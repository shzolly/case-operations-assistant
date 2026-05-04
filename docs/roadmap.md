# Phased MVP Roadmap

## Phase 0 - Project Foundation

Outcome: a repo you can explain clearly in an interview.

- Define architecture, domain story, and security model.
- Seed sample procedure documents and case records.
- Add dependency-light assistant core with smoke tests.
- Add API and frontend scaffolds.

## Phase 1 - Vertical Slice

Outcome: one complete workflow from user question to recommended action.

- Staff asks a natural-language question.
- Assistant retrieves relevant procedure guidance.
- Assistant calls case lookup tool.
- RBAC validates the user's allowed actions.
- Sensitive action is routed to a human approval queue.
- Response includes citations and audit metadata.

## Phase 2 - Real API Service

Outcome: FastAPI service that exposes the assistant workflow.

- Add `/api/chat`, `/api/cases/{case_id}`, `/api/approvals`.
- Add request/response schemas.
- Add structured application logs.
- Add automated tests around core workflow and API boundaries.

## Phase 3 - React Staff UI

Outcome: usable staff-facing interface.

- Chat panel.
- Case context sidebar.
- Source citation panel.
- Pending approval banner.
- Role switcher for demo purposes.

## Phase 4 - RAG Upgrade

Outcome: retrieval pipeline closer to production.

- Add document ingestion. Completed for Markdown policy files.
- Add lexical retrieval quality tests. Completed for the local MVP.
- Add local embedding abstraction and hybrid vector scoring. Completed for MVP.
- Store vectors in pgvector or OpenSearch. Deferred to production hardening.
- Add hallucination/citation evaluation cases. Seeded retrieval evals completed.

## Phase 5 - Agentic Orchestration

Outcome: LangGraph workflow with visible state transitions.

- Replace simple orchestrator with LangGraph. Completed.
- Add explicit nodes for classify, retrieve, authorize, act, approve, answer. Completed with deterministic case workflow nodes.
- Add retry/error paths.
- Add deterministic tool contracts.

## Phase 6 - Production Hardening

Outcome: deployment-ready project story.

- Dockerize all services. Completed for backend, frontend, and pgvector Postgres.
- Add GitHub Actions CI. Completed for backend tests, smoke scripts, frontend build, and image build.
- Add container scanning. Completed with Trivy workflow.
- Add ECS Fargate deployment notes or Terraform/CDK. ECS task definition scaffold and runbook added.
- Add Secrets Manager integration. ECS task definition uses Secrets Manager references.
- Add OpenTelemetry traces and CloudWatch dashboards. CloudWatch logging scaffold added; tracing/dashboard work remains.

## Interview Narrative

The existing court system is treated as a legacy monolith. The AI assistant is a
separate Python microservice so the team can improve staff efficiency without
destabilizing core case-management workflows. The assistant is grounded by RAG,
constrained by RBAC, monitored through observability, and blocked from sensitive
write actions unless a human approves them.
