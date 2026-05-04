# Workflow Design

The assistant uses LangGraph `StateGraph` for orchestration. Business logic is
kept in small node functions, and LangGraph owns the conditional routing.

## Main Path

```text
extract_case_id
authorize_read
load_case
retrieve_policy
decide_action
compose_response
finalize
```

## State

The workflow state carries:

- original user question
- user context
- case id
- case record
- citations
- approval request
- answer text
- audit metadata

Each node reads and updates the state. The response contract remains stable
because the final node converts the workflow state into `AssistantResponse`.

## Early Exits

The workflow exits early for:

- missing case id
- unauthorized read
- case not found

These paths still finalize with an audit event, which makes failures observable
and reviewable.

## LangGraph Implementation

The graph is built in `backend/app/workflow.py` with:

- `START -> extract_case_id`
- conditional edge to `missing_case_id_response` or `authorize_read`
- conditional edge to `finalize` or `load_case`
- conditional edge to `case_not_found_response` or `retrieve_policy`
- main path through `decide_action`, `compose_response`, and `finalize`

Future production additions can use LangGraph checkpointers, retries, interrupts
for human approval, and LangSmith tracing.
