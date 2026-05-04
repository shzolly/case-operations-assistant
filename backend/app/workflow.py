import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable

from langgraph.graph import END, START, StateGraph

from backend.app.approval import build_approval_request
from backend.app.legacy_client import get_case
from backend.app.models import ApprovalRequest, AssistantResponse, CaseRecord, Citation, UserContext
from backend.app.policies import retrieve_policy
from backend.app.security import DRAFT_TASK, READ_CASE, has_permission
from backend.app.storage import append_audit_event, save_approval_request


CASE_ID_PATTERN = re.compile(r"\b[A-Z]{2}-\d{4}-\d{3}\b", re.IGNORECASE)


@dataclass
class WorkflowState:
    question: str
    user: UserContext
    audit: dict
    case_id: str | None = None
    case: CaseRecord | None = None
    citations: list[Citation] = field(default_factory=list)
    approval_request: ApprovalRequest | None = None
    answer: str = ""
    terminal_event: str = "assistant_response"


WorkflowNode = Callable[[WorkflowState], WorkflowState]


def build_initial_state(question: str, user: UserContext) -> WorkflowState:
    return WorkflowState(
        question=question,
        user=user,
        audit={
            "request_time": datetime.now(timezone.utc).isoformat(),
            "user_id": user.user_id,
            "role": user.role,
            "workflow": "case_next_step",
            "tool_calls": [],
            "nodes": [],
        },
    )


def record_node(state: WorkflowState, node_name: str) -> None:
    state.audit["nodes"].append(node_name)


def extract_case_id_node(state: WorkflowState) -> WorkflowState:
    record_node(state, "extract_case_id")
    match = CASE_ID_PATTERN.search(state.question)
    if match:
        state.case_id = match.group(0).upper()
    return state


def missing_case_id_node(state: WorkflowState) -> WorkflowState:
    record_node(state, "missing_case_id_response")
    state.citations = retrieve_policy(state.question)
    state.answer = "Please include a case id like FM-2026-001 so I can check the case context."
    state.terminal_event = "assistant_response"
    return state


def authorize_read_node(state: WorkflowState) -> WorkflowState:
    record_node(state, "authorize_read")
    if not has_permission(state.user.role, READ_CASE):
        state.audit["authorization"] = "denied:read_case"
        state.citations = retrieve_policy(state.question)
        state.answer = "You are not authorized to read case information for this request."
        state.terminal_event = "authorization_denied"
    else:
        state.audit["authorization"] = "allowed:read_case"
    return state


def load_case_node(state: WorkflowState) -> WorkflowState:
    record_node(state, "load_case")
    if state.case_id is None:
        return state
    state.case = get_case(state.case_id)
    state.audit["tool_calls"].append({"tool": "get_case", "case_id": state.case_id})
    return state


def case_not_found_node(state: WorkflowState) -> WorkflowState:
    record_node(state, "case_not_found_response")
    state.citations = retrieve_policy(state.question)
    state.answer = f"I could not find case {state.case_id} in the mock case system."
    state.terminal_event = "case_not_found"
    return state


def retrieve_policy_node(state: WorkflowState) -> WorkflowState:
    record_node(state, "retrieve_policy")
    if state.case is None:
        state.citations = retrieve_policy(state.question)
        return state

    retrieval_query = " ".join(
        [
            state.question,
            state.case.case_type,
            state.case.status,
            state.case.assigned_unit,
            state.case.last_event,
            " ".join(state.case.flags),
        ]
    )
    state.citations = retrieve_policy(retrieval_query)
    state.audit["retrieval"] = {
        "query_strategy": "question_plus_case_context",
        "citation_ids": [citation.source_id for citation in state.citations],
    }
    return state


def decide_action_node(state: WorkflowState) -> WorkflowState:
    record_node(state, "decide_action")
    if state.case is None:
        return state

    needs_follow_up = state.case.days_since_last_event > 14 or "follow-up-due" in state.case.flags
    state.audit["decision"] = {
        "needs_follow_up": needs_follow_up,
        "reason": "idle_days_or_follow_up_flag" if needs_follow_up else "within_normal_window",
    }

    if needs_follow_up and has_permission(state.user.role, DRAFT_TASK):
        state.approval_request = build_approval_request(
            user=state.user,
            case_id=state.case.case_id,
            action_type="create_internal_follow_up_task",
            payload={
                "assigned_unit": state.case.assigned_unit,
                "reason": "No docket activity for more than 14 days.",
                "last_event": state.case.last_event,
            },
        )
        state.audit["approval"] = asdict(state.approval_request)
        save_approval_request(state.approval_request)
    return state


def compose_response_node(state: WorkflowState) -> WorkflowState:
    record_node(state, "compose_response")
    if state.case is None:
        return state

    needs_follow_up = bool(state.audit.get("decision", {}).get("needs_follow_up"))
    if needs_follow_up:
        state.answer = (
            f"Case {state.case.case_id} is {state.case.status} and has had no activity for "
            f"{state.case.days_since_last_event} days. Recommended next step: verify "
            "the latest filing status, review whether documents are missing, and "
            "prepare an internal follow-up task for the assigned unit. Because "
            "this affects case workflow, I created a pending approval item for a "
            "supervisor before execution."
        )
    else:
        state.answer = (
            f"Case {state.case.case_id} is {state.case.status}. Based on the current mock "
            "record, no overdue follow-up action is required. Continue monitoring "
            "according to normal unit procedure."
        )
    state.terminal_event = "assistant_response"
    return state


def finalize_node(state: WorkflowState) -> WorkflowState:
    record_node(state, "finalize")
    event = {
        "event": state.terminal_event,
        "approval_required": state.approval_request is not None,
        "audit": state.audit,
    }
    if state.case is not None:
        event["case_id"] = state.case.case_id
    append_audit_event(event)
    return state


def route_after_extract(state: WorkflowState) -> str:
    return "missing_case_id_response" if state.case_id is None else "authorize_read"


def route_after_authorize(state: WorkflowState) -> str:
    return "finalize" if state.answer else "load_case"


def route_after_load_case(state: WorkflowState) -> str:
    return "case_not_found_response" if state.case is None else "retrieve_policy"


def build_case_workflow_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("extract_case_id", extract_case_id_node)
    graph.add_node("missing_case_id_response", missing_case_id_node)
    graph.add_node("authorize_read", authorize_read_node)
    graph.add_node("load_case", load_case_node)
    graph.add_node("case_not_found_response", case_not_found_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)
    graph.add_node("decide_action", decide_action_node)
    graph.add_node("compose_response", compose_response_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "extract_case_id")
    graph.add_conditional_edges(
        "extract_case_id",
        route_after_extract,
        {
            "missing_case_id_response": "missing_case_id_response",
            "authorize_read": "authorize_read",
        },
    )
    graph.add_edge("missing_case_id_response", "finalize")
    graph.add_conditional_edges(
        "authorize_read",
        route_after_authorize,
        {
            "finalize": "finalize",
            "load_case": "load_case",
        },
    )
    graph.add_conditional_edges(
        "load_case",
        route_after_load_case,
        {
            "case_not_found_response": "case_not_found_response",
            "retrieve_policy": "retrieve_policy",
        },
    )
    graph.add_edge("case_not_found_response", "finalize")
    graph.add_edge("retrieve_policy", "decide_action")
    graph.add_edge("decide_action", "compose_response")
    graph.add_edge("compose_response", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


CASE_WORKFLOW_GRAPH = build_case_workflow_graph()


def run_case_workflow(question: str, user: UserContext) -> AssistantResponse:
    state = build_initial_state(question, user)
    final_state = CASE_WORKFLOW_GRAPH.invoke(state)
    return to_response(final_state)


def to_response(state: WorkflowState) -> AssistantResponse:
    if isinstance(state, dict):
        return AssistantResponse(
            answer=state["answer"],
            case=state["case"],
            citations=state["citations"],
            approval_request=state["approval_request"],
            audit=state["audit"],
        )
    return AssistantResponse(
        answer=state.answer,
        case=state.case,
        citations=state.citations,
        approval_request=state.approval_request,
        audit=state.audit,
    )
