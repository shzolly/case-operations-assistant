from dataclasses import asdict

from fastapi import FastAPI, Header, HTTPException

from backend.app.models import UserContext
from backend.app.orchestrator import answer_case_question
from backend.app.schemas import ApprovalDecisionRequest, ApprovalListResponse, AuditListResponse, ChatRequest
from backend.app.security import APPROVE_SENSITIVE_ACTION, REVIEW_AUDIT, has_permission
from backend.app.storage import decide_approval_request, list_approval_requests, list_audit_events


app = FastAPI(title="NJ Judiciary AI Assistant")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
def chat(
    request: ChatRequest,
    x_user_id: str = Header(default="demo.clerk"),
    x_user_role: str = Header(default="clerk"),
    x_courthouse: str = Header(default="Mercer"),
) -> dict:
    user = UserContext(
        user_id=x_user_id,
        role=x_user_role,
        courthouse=x_courthouse,
    )
    response = answer_case_question(request.message, user)
    return asdict(response)


@app.get("/api/approvals", response_model=ApprovalListResponse)
def approvals() -> dict:
    return {"approvals": list_approval_requests()}


@app.post("/api/approvals/{action_id}/approve")
def approve(
    action_id: str,
    request: ApprovalDecisionRequest,
    x_user_id: str = Header(default="demo.supervisor"),
    x_user_role: str = Header(default="supervisor"),
) -> dict:
    if not has_permission(x_user_role, APPROVE_SENSITIVE_ACTION):
        raise HTTPException(status_code=403, detail="Role cannot approve sensitive actions")
    updated = decide_approval_request(action_id, "approved", x_user_id, request.reason)
    if updated is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return {"approval": updated}


@app.post("/api/approvals/{action_id}/reject")
def reject(
    action_id: str,
    request: ApprovalDecisionRequest,
    x_user_id: str = Header(default="demo.supervisor"),
    x_user_role: str = Header(default="supervisor"),
) -> dict:
    if not has_permission(x_user_role, APPROVE_SENSITIVE_ACTION):
        raise HTTPException(status_code=403, detail="Role cannot reject sensitive actions")
    updated = decide_approval_request(action_id, "rejected", x_user_id, request.reason)
    if updated is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return {"approval": updated}


@app.get("/api/audit", response_model=AuditListResponse)
def audit(
    limit: int = 100,
    x_user_role: str = Header(default="admin"),
) -> dict:
    if not has_permission(x_user_role, REVIEW_AUDIT):
        raise HTTPException(status_code=403, detail="Role cannot review audit trail")
    return {"events": list_audit_events(limit=limit)}
