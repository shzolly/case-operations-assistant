# Frontend Design

The staff UI is designed as an operational workspace rather than a marketing
page. The first screen supports the actual case-assistant workflow:

- role and user context
- quick demo prompts
- natural-language request composer
- assistant recommendation
- workflow trace
- case context
- citation excerpts
- approval lifecycle
- admin-only audit event view

## Demo Flow

1. Use clerk role.
2. Ask: `What should I do next for case FM-2026-001?`
3. Review recommendation, citations, workflow trace, and pending approval.
4. Switch to supervisor role.
5. Approve or reject the pending action.
6. Switch to admin role.
7. Review audit events.

## Implementation Paths

The local no-build UI lives in `frontend/static` and is served by
`run_local_server.py`.

The React implementation lives in `frontend/src` and mirrors the same user
experience for the Vite runtime.

