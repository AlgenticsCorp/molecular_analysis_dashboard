# Implementation Plan (Incremental, Always-Running Stages)

This plan ensures the system is runnable at the end of every stage. Each stage defines a small goal, strict scope, quality gates, and rollback. Deployment steps per stage live in:
- Local (Compose): `project_design/DEPLOYMENT_PLAN_LOCAL.md`
- Cloud (VM/Kubernetes outline): `project_design/DEPLOYMENT_PLAN_CLOUD.md`

References: `ARCHITECTURE.md`, `FRAMEWORK_DESIGN.md`, `API_CONTRACT.md`, `ERD.md`, `SCHEMA_PROPOSAL.md`, `DATABASES.md`.

---

## Stage 0: Bootstrap API Health
Goal: Minimal FastAPI app with `/health`. No DB, no broker.

- Scope
    - Skeleton package at `src/molecular_analysis_dashboard/`
    - Endpoint: `GET /health` -> `{ "status": "ok" }`
- Quality gates
    - Build/lint pass (pre-commit if configured)
    - `curl http://localhost:8000/health` returns 200
- Rollback
    - Revert app init; keep only health check

## Stage 1: Metadata DB + Alembic Baseline
Goal: Add Postgres connectivity and migrations with core identity/RBAC.

- Scope
    - Async SQLAlchemy engine/session; Alembic configured
    - Migrations create: `organizations`, `users`, `roles`, `role_permissions`, `memberships`, `membership_roles`, `tokens`
    - Endpoint: `GET /ready` -> DB connectivity check
- Quality gates
    - Alembic upgrade/downgrade succeed locally
    - `/ready` returns `ready` when DB up
- Rollback
    - Downgrade migration; disable DB wiring

## Stage 2: Molecules & Artifacts + Storage Adapter
Goal: Upload molecules; persist metadata and file URIs.

- Scope
    - Tables: `molecules`, optional `artifacts`
    - Storage adapter: LocalFS (dev) with configurable root; presigned URL stub
    - Endpoints: `POST /api/v1/molecules/upload`, optional `GET /api/v1/artifacts/{uri}`
- Quality gates
    - Upload small file -> DB row exists; file present at storage path; downloadable via URL/presign
- Rollback
    - Revert endpoints; keep schema (non-breaking)

## Stage 3: Results DB Provisioning + Jobs Meta
Goal: Establish per-org Results DB and global jobs index.

- Scope
    - Provision Results DB (or schema) for an org and apply initial DDL: `jobs`, `job_inputs`, `job_outputs`
    - Metadata DB: add `jobs_meta`
    - Endpoints: `POST /api/v1/pipelines/{pipeline_id}/jobs` (create PENDING only), `GET /api/v1/jobs/{job_id}/status`
- Quality gates
    - Job creation writes to both DBs idempotently; status is retrievable
- Rollback
    - Drop org results DB (dev only); disable job creation path

## Stage 4: Async Pipeline (Worker, No Engine)
Goal: Wire Celery worker and Redis; simulate execution.

- Scope
    - Celery app + worker; Redis as broker
    - Task flips job status `PENDING -> RUNNING -> COMPLETED`; writes dummy outputs
    - Results API returns dummy artifact URIs
- Quality gates
    - Submit job -> observe state transitions; artifacts recorded
- Rollback
    - Stop worker; API path falls back to PENDING only

## Stage 5: Docking Engine(s) + Domain Results
Goal: Execute real docking and persist scores/poses.

- Scope
    - Adapters: one or more engine adapters (e.g., `AutoDockVinaAdapter`, `SminaAdapter`, `GninaAdapter`) behind `DockingEnginePort` with timeouts and error mapping
    - Results DB: add `docking_results`; `task_executions` with `logs_uri`
    - Endpoint: `GET /api/v1/jobs/{job_id}/results` -> scores + artifact links
- Quality gates
    - Known test ligand/protein produce deterministic outputs; results visible via API
- Rollback
    - Fallback to Stage 4 task; keep schema (non-breaking)

## Stage 6: Caching & Confidence
Goal: Reuse results for equivalent inputs; track confidence.

- Scope
    - Compute `input_signature` (normalized inputs + params) for `jobs`
    - Tables: `task_results` (JSONB + `confidence_score`), `result_cache` (canonical job, TTL, counts)
    - Job creation supports `use_cache`; cache hits may return 200 immediately
- Quality gates
    - Submitting same inputs twice yields cache hit; TTL/threshold honored
- Rollback
    - Disable cache check; continue persisting signatures

## Stage 7: Logs Separation + Job Events
Goal: Remove log lines from DB; add event timeline.

- Scope
    - Logs stored in object storage/log backend; keep `logs_uri` only
    - Table: `job_events` (append-only timeline)
    - Endpoints: `/api/v1/jobs/{job_id}/events`, `/api/v1/jobs/{job_id}/logs` (redirect/presign)
- Quality gates
    - Events populate; logs downloadable via signed link
- Rollback
    - Continue writing logs to object storage only; endpoints remain

## Stage 8: External Auth (Microsoft/Google) + RBAC
Goal: Use external IdP for auth, maintain local RBAC.

- Scope
    - Tables: `identity_providers`, `identities`
    - OIDC login flow maps identities to users; enforce `memberships`/`roles`
- Quality gates
    - IdP login on test tenant; RBAC enforced on routes
- Rollback
    - Fall back to local email/password (if enabled); keep identity tables

## Stage 9: Hardening & Observability
Goal: Production readiness.

- Scope
    - Metrics, tracing, structured logging; retries/backoff
    - Indexes/partitioning; backups/retention; CI/CD pipeline
- Quality gates
    - Baseline load test; dashboards show golden signals; backup/restore tested
- Rollback
    - Disable optional collectors; revert partitioning with migrations

---

## Per-Stage Deliverables (Summary)
- Stage 0: FastAPI app, `/health`
- Stage 1: DB engine, Alembic, `/ready`, identity/RBAC tables
- Stage 2: `molecules`/`artifacts`, storage adapter, upload endpoint
- Stage 3: Results DB provisioning, `jobs_meta`, job create/status
- Stage 4: Celery/Redis, async task, dummy results
- Stage 5: Docking engine adapter(s), `docking_results`, `task_executions`, results API
- Stage 6: `jobs.input_signature`, `task_results`, `result_cache`, cache-aware submit
- Stage 7: `job_events`, logs backend integration, events/logs endpoints
- Stage 8: `identity_providers`, `identities`, OIDC integration
- Stage 9: metrics/tracing/alerts, backups, CI/CD

## Minimal Test Matrix
- 0: `/health` 200
- 1: `/ready` 200 with DB; migrations ok
- 2: molecule upload persists row + file; presign valid
- 3: job rows created in both DBs; status PENDING reads back
- 4: status transitions via worker; dummy artifacts present
- 5: docking scores persisted; results API returns expected fields
- 6: cache hit on repeated inputs; TTL/threshold honored
- 7: events listed; `/logs` returns signed URL
- 8: IdP login maps to user; RBAC enforced
- 9: metrics live; backup/restore verified
