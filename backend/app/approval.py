from uuid import uuid4

from backend.app.models import ApprovalRequest, UserContext


def build_approval_request(
    user: UserContext,
    case_id: str,
    action_type: str,
    payload: dict,
) -> ApprovalRequest:
    return ApprovalRequest(
        action_id=f"apr-{uuid4().hex[:10]}",
        action_type=action_type,
        case_id=case_id,
        requested_by=user.user_id,
        required_role="supervisor",
        payload=payload,
    )
