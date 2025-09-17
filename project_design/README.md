# Project Design Overview

This page is the entry point for all system design documents. It summarizes the architecture, data model, APIs, security, deployment, and implementation plan, and links to detailed references in this folder.

---

## Executive Summary
- Domain: Molecular analysis with pluggable docking engines (Vina/Smina/Gnina/custom) and 3D visualization.
- Architecture: Clean Architecture (Ports & Adapters), FastAPI, Celery, PostgreSQL, Redis, object storage.
- Data: Metadata DB (shared), per-org Results DB, logs in separate backend, JSONB for flexible task results.
- Key features: Caching via `input_signature`, job events, external auth (OIDC) with local RBAC, object-store artifacts.
- Delivery: Incremental, always-running stages with per-stage local/cloud deployment plans.

---

## Architecture at a Glance
- Layers: Presentation (API), Use Cases, Ports, Adapters (DB/Engines/Storage), Infrastructure, Domain.
- Execution path: API validates → Use Case → Ports → Adapters → DB/Worker/Storage.
- Async work: Celery workers consume from Redis; engines run via subprocess or container.
- Gateway-ready: FastAPI app supports `ROOT_PATH`, proxy headers, trusted hosts, CORS, and request ID.

References:
- Architecture overview: [ARCHITECTURE.md](./ARCHITECTURE.md)
- Framework design & diagrams: [FRAMEWORK_DESIGN.md](./FRAMEWORK_DESIGN.md)
- Tools & workflow (E2E flow): [TOOLS_AND_WORKFLOW.md](./TOOLS_AND_WORKFLOW.md)
- Code structure (folders): [CODE_STRUCTURE.md](./CODE_STRUCTURE.md)
- Repo → container map: [REPO_COMPONENT_MAP.md](./REPO_COMPONENT_MAP.md)
- API Gateway guide: [API_GATEWAY.md](./API_GATEWAY.md)

---

## Data Model & Storage
- Metadata DB (shared): organizations, users, roles, pipelines, tokens, etc.
- Results DB (per org): jobs, task results (JSONB + confidence), result cache, job events.
- Logs: stored in a logs backend or object storage; only `logs_uri` in DB.
- Artifacts: stored in LocalFS (dev) or S3/MinIO (prod); URIs in DB.

References:
- ERD (Mermaid): [ERD.md](./ERD.md)
- Schema proposal (DDL): [SCHEMA_PROPOSAL.md](./SCHEMA_PROPOSAL.md)
- Databases & storage strategy: [DATABASES.md](./DATABASES.md)

---

## API & Use Cases
- REST API with JWT auth; org isolation via `org_id` claim.
- Pipelines & jobs with cache-aware submission and confidence-based reuse.
- Results include per-task `result_data` (engine-specific), `confidence_score`, artifacts, and events/logs.

References:
- API contract: [API_CONTRACT.md](./API_CONTRACT.md)
- Use cases (UC-001 .. UC-012): [USE_CASES.md](./USE_CASES.md)

---

## Security & Tenancy
- External auth (OIDC: Microsoft/Google/SSO) mapped to local users/roles.
- RBAC within orgs; Root role for cross-org operations.
- Secrets via env; prefer secret managers in production.

Reference: [ARCHITECTURE.md](./ARCHITECTURE.md) (Security), [API_GATEWAY.md](./API_GATEWAY.md)

---

## Deployment & Operations
- Local: Docker Compose with services for API, Worker, Postgres, Redis, Migrate, Flower.
- Cloud: Managed Postgres/Redis, object storage, gateway/WAF, per-queue worker scaling.
- Observability: structured logs with request IDs, optional metrics/tracing.

References:
- Local (per stage): [DEPLOYMENT_PLAN_LOCAL.md](./DEPLOYMENT_PLAN_LOCAL.md)
- Cloud (per stage): [DEPLOYMENT_PLAN_CLOUD.md](./DEPLOYMENT_PLAN_CLOUD.md)

---

## Implementation Plan (Always-Running Stages)
- Stages 0–9: Each ends in a runnable system (health → DB → uploads → jobs → engines → cache → events/logs → external auth → hardening).
- Quality gates: Build/lint/tests, smoke endpoints, migrations, and observability checks per stage.

Reference: [implementation_plan.md](./implementation_plan.md)

---

## Extensibility: Engines & Adapters
- Docking engines are pluggable behind `DockingEnginePort`.
- Add adapters (e.g., Vina/Smina/Gnina/custom container) without changing core use cases.
- Route per engine via queue, settings, or pipeline spec.

References: [FRAMEWORK_DESIGN.md](./FRAMEWORK_DESIGN.md), [TOOLS_AND_WORKFLOW.md](./TOOLS_AND_WORKFLOW.md)

---

## For First-Time Developers
1. Quick start: run API/Worker locally → see [docs/getting-started/quick-start.md](../docs/getting-started/quick-start.md)
2. Read: [ARCHITECTURE.md](./ARCHITECTURE.md) → [FRAMEWORK_DESIGN.md](./FRAMEWORK_DESIGN.md) → [API_CONTRACT.md](./API_CONTRACT.md)
3. Implement by stages: [implementation_plan.md](./implementation_plan.md)
4. Deploy per stage: [DEPLOYMENT_PLAN_LOCAL.md](./DEPLOYMENT_PLAN_LOCAL.md), [DEPLOYMENT_PLAN_CLOUD.md](./DEPLOYMENT_PLAN_CLOUD.md)

---

## Conventions & Notes
- JSONB for flexible task results; keep schemas versioned (`schema_version`).
- Store only URIs in DB for files/logs; use pre-signed URLs for downloads.
- Cache canonicalization via `input_signature`; TTL and confidence thresholds configurable.

---

## Change Log & Traceability
- High-level changes: [CHANGELOG.md](../CHANGELOG.md)
- Design ↔ Code: Ports in `src/molecular_analysis_dashboard/ports/` implemented by `adapters/*`; use cases orchestrate via ports.
