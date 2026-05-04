from backend.app.models import UserContext
from backend.app.storage import clear_runtime_data, list_audit_events
from backend.app.workflow import run_case_workflow


def test_follow_up_workflow_records_expected_node_path() -> None:
    clear_runtime_data()
    user = UserContext(user_id="demo.clerk", role="clerk", courthouse="Mercer")

    response = run_case_workflow("What should I do next for case FM-2026-001?", user)

    assert response.case is not None
    assert response.approval_request is not None
    assert response.audit["nodes"] == [
        "extract_case_id",
        "authorize_read",
        "load_case",
        "retrieve_policy",
        "decide_action",
        "compose_response",
        "finalize",
    ]
    assert response.audit["decision"]["needs_follow_up"] is True


def test_missing_case_id_exits_before_case_tool_call() -> None:
    clear_runtime_data()
    user = UserContext(user_id="demo.clerk", role="clerk", courthouse="Mercer")

    response = run_case_workflow("What should I do next?", user)

    assert response.case is None
    assert response.approval_request is None
    assert response.audit["tool_calls"] == []
    assert response.audit["nodes"] == [
        "extract_case_id",
        "missing_case_id_response",
        "finalize",
    ]


def test_unauthorized_user_exits_before_case_lookup() -> None:
    clear_runtime_data()
    user = UserContext(user_id="demo.viewer", role="viewer", courthouse="Mercer")

    response = run_case_workflow("What should I do next for case FM-2026-001?", user)

    assert response.case is None
    assert response.audit["authorization"] == "denied:read_case"
    assert response.audit["tool_calls"] == []
    assert response.audit["nodes"] == [
        "extract_case_id",
        "authorize_read",
        "finalize",
    ]


def test_case_not_found_path_is_audited() -> None:
    clear_runtime_data()
    user = UserContext(user_id="demo.clerk", role="clerk", courthouse="Mercer")

    response = run_case_workflow("What should I do next for case FM-2026-999?", user)

    assert response.case is None
    assert "could not find case" in response.answer
    assert response.audit["nodes"] == [
        "extract_case_id",
        "authorize_read",
        "load_case",
        "case_not_found_response",
        "finalize",
    ]
    assert any(event["event"] == "case_not_found" for event in list_audit_events())

