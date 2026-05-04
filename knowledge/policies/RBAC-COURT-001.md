# Court Staff Role Permissions

Source ID: RBAC-COURT-001
Domain: Security

Clerks may read case status, retrieve procedural guidance, and draft internal
follow-up tasks.

Supervisors may approve or reject sensitive actions after reviewing the case
context and supporting rationale.

Administrative users may review audit trails and configuration.

Every tool call must receive the user role and must check authorization before
reading case information or mutating workflow state.

