from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ApprovalDecisionRequest(BaseModel):
    reason: str | None = None


class ApprovalRecord(BaseModel):
    action_id: str
    action_type: str
    case_id: str
    requested_by: str
    required_role: str
    payload: dict[str, Any]
    status: Literal["pending", "approved", "rejected"]
    decided_by: str | None = None
    decided_at: str | None = None
    decision_reason: str | None = None


class ApprovalListResponse(BaseModel):
    approvals: list[ApprovalRecord]


class AuditListResponse(BaseModel):
    events: list[dict[str, Any]]

