READ_CASE = "read_case"
DRAFT_TASK = "draft_task"
APPROVE_SENSITIVE_ACTION = "approve_sensitive_action"
REVIEW_AUDIT = "review_audit"


ROLE_PERMISSIONS = {
    "clerk": {READ_CASE, DRAFT_TASK},
    "supervisor": {READ_CASE, DRAFT_TASK, APPROVE_SENSITIVE_ACTION},
    "admin": {READ_CASE, DRAFT_TASK, APPROVE_SENSITIVE_ACTION, REVIEW_AUDIT},
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())

