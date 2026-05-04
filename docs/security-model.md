# Security Model

## Roles

| Role | Capabilities |
| --- | --- |
| clerk | Read case status, retrieve guidance, draft follow-up task |
| supervisor | Clerk permissions plus approval of sensitive actions |
| admin | Configuration and audit review |

## Rules

- Every tool call receives a user context.
- Every action is checked against role permissions.
- Read actions may run immediately when authorized.
- Write actions are never executed directly by the model.
- Sensitive writes become pending approval requests.
- Audit logs must not contain unnecessary PII.

## Sensitive Actions

- Create official notice.
- Update case disposition.
- Route filing for judicial review.
- Close or reopen a case.
- Send external communication.

