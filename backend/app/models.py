from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class UserContext:
    user_id: str
    role: str
    courthouse: str


@dataclass(frozen=True)
class Citation:
    source_id: str
    title: str
    excerpt: str


@dataclass(frozen=True)
class CaseRecord:
    case_id: str
    case_type: str
    status: str
    assigned_unit: str
    last_event: str
    days_since_last_event: int
    flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ApprovalRequest:
    action_id: str
    action_type: str
    case_id: str
    requested_by: str
    required_role: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class AssistantResponse:
    answer: str
    case: CaseRecord | None
    citations: list[Citation]
    approval_request: ApprovalRequest | None
    audit: dict[str, Any]

