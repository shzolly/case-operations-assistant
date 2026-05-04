# NJ Judiciary Agentic Case Operations Assistant

Production-style MVP for practicing end-to-end AI engineering patterns:
RAG, agent workflows, tool usage, role-based access control, human approval,
containers, CI/CD, testing, and observability.

## MVP Story

A court staff user asks:

> What should I do next for case FM-2026-001?

The assistant:

1. Identifies the case and user role.
2. Retrieves relevant internal procedure guidance.
3. Calls a mock legacy case-management API.
4. Applies permission and approval rules.
5. Returns a cited recommendation.
6. Creates an approval request for sensitive actions.

## Repository Layout

```text
backend/             Python assistant service and orchestration logic
frontend/            React staff UI scaffold
mock-legacy-api/     Mock case-management service data and API contract
docs/                Architecture, roadmap, policies, and runbooks
knowledge/           Markdown procedure documents used by retrieval
infra/               Deployment notes and future IaC placeholders
tests/               Dependency-light verification scripts
```

## First Local Verification

This first slice can be verified without installing external packages:

```powershell
.venv\Scripts\python.exe tests\smoke_test.py
.venv\Scripts\python.exe tests\storage_lifecycle_test.py
.venv\Scripts\python.exe tests\http_smoke_test.py
.venv\Scripts\python.exe tests\frontend_contract_test.py
```

Expected result: the assistant returns a grounded recommendation with citations,
case context, and a pending approval action.

## Run the Clickable MVP

This no-build server uses Python's standard library and serves both the local UI
and the assistant API:

```powershell
.venv\Scripts\python.exe run_local_server.py
```

Open:

```text
http://127.0.0.1:8000
```

The server writes local demo runtime data to `data/`, which is ignored by
git.

## Planned Runtime Stack

- Frontend: React, TypeScript, Vite
- Backend: Python, FastAPI, LangChain, LangGraph
- Retrieval: OpenAI `text-embedding-3-small` with PostgreSQL/pgvector
- Deployment: Docker, AWS ECS Fargate, API Gateway, Secrets Manager, VPC
- Observability: structured logs, OpenTelemetry, CloudWatch, agent traces

## FastAPI Runtime

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.venv\Scripts\python.exe -m uvicorn backend.app.api:app --reload --port 8000
```

Run the production-shaped API tests:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_api_contract.py
```

## Retrieval Corpus

Policy and procedure sources live in `knowledge/policies`. The backend ingests
those Markdown files, chunks them, builds a local hybrid lexical/vector index,
and returns chunk-level citations such as `SOP-FM-001#1`.

See `docs/rag-design.md` for the retrieval design and upgrade path.
See `docs/pgvector-rag.md` for the production pgvector setup.

## Workflow Orchestration

The assistant workflow is implemented as explicit nodes in
`backend/app/workflow.py`. This mirrors the LangGraph model while keeping the
current MVP dependency-light:

```text
extract_case_id -> authorize_read -> load_case -> retrieve_policy
-> decide_action -> compose_response -> finalize
```

## Frontend

The local no-build UI is served from `frontend/static` by `run_local_server.py`.
The React implementation in `frontend/src` mirrors the same workflow and is ready
for the Vite runtime once Node/npm is available.

See `docs/frontend-design.md` for the staff workflow demo path.
