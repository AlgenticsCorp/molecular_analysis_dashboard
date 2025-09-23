# Databases and Tenancy Model

This document defines the database layout and multi-tenancy strategy for the Molecular Analysis Dashboard.

## Overview

- Shared Metadata Database (global): Users, roles, organizations (tenants), pipelines, pipeline versions, and lightweight job metadata.
- Per-Organization Results Database: Heavy job results, result tables, and performance-sensitive data are isolated per org to reduce contention and enable per-tenant scaling and retention policies.
- Storage: Per-organization bucket/namespace for artifacts (inputs, outputs, logs) managed via the Storage Adapter; dev can use local filesystem.
 - Logs Database (separate): High-volume log lines are stored in a log backend (e.g., Loki/OpenSearch). Postgres holds only pointers (e.g., `logs_uri`).

## Logical Databases

1) Metadata DB (shared)
- Tables (indicative):
  - organizations (org_id, name, created_at, status, quotas)
  - users (user_id, email, hashed_password, enabled, created_at)
  - user_org_memberships (user_id, org_id, roles[])
  - roles (role_id, org_id, name, permissions[])
  - pipelines (pipeline_id, org_id, name, description, latest_version)
  - pipeline_versions (pipeline_version_id, pipeline_id, version, spec, published)
  - jobs_meta (job_id, org_id, pipeline_id, pipeline_version_id, created_by, status, created_at, updated_at)
  - audits (...)

2) Results DB (per org)
- Tables (indicative):
  - jobs (job_id, pipeline_version_id, status, timings, metrics)
  - job_inputs (job_id, key, uri, content_type)
  - job_outputs (job_id, key, uri, content_type)
  - docking_results (job_id, score, pose_rank, metadata)
  - logs (job_id, line_no, ts, message)

## Isolation & Routing

- API requests carry `org_id` in JWT; repositories filter by `org_id`.
- Results DB routing by `org_id`:
  - Connection management layer maps `org_id` -> DSN for that org’s results DB.
  - New org provisioning creates a new results DB and applies migrations.
- Storage paths/buckets are prefixed or separated per `org_id` to avoid cross-tenant leakage.

## Performance & Scaling

- Metadata DB: add PgBouncer, read replicas (for browsing pipelines), and indexes on `(org_id, status, created_at)`.
- Results DB: sharding by org; can scale vertically per heavy tenants; allows per-tenant retention and backup strategies.
- Migrations: Alembic per DB with version tables; run `migrate` job once per DB change.

## Consistency & Transactions

- Job creation spans Metadata DB (job record) and Results DB (job payload); use transactional boundaries with outbox/inbox pattern or idempotent retries.
- Artifacts are referenced by URI; ensure writes to storage happen before DB commit or use two-phase commit patterns if needed (usually overkill; prefer idempotency).

## Security & Compliance

- Enforce RLS (Row Level Security) style filtering in repositories; consider DB-enforced RLS if supported.
- Encrypt data at rest and in transit; rotate credentials per org where feasible.
- Audit tables in Metadata DB capture critical actions with `org_id`, `user_id`, `pipeline_id`, `job_id`.

## Backup & Retention

- Metadata DB: Daily backups, PITR if supported by managed service.
- Results DB: Per-tenant retention policies; larger tenants can have more frequent backups.
- Storage: Lifecycle policies for cold artifacts; versioning for critical datasets.

---

## Logs Database (Separate)

- Rationale: Task and service logs can be very high volume and are optimized for time-series search and retention in a dedicated system (e.g., Loki with S3, or OpenSearch/Elasticsearch).
- In Postgres: keep `task_executions.logs_uri` or a `job_outputs` entry pointing to the log archive; avoid row-per-log-line tables for scale.
- Benefits: Fast log search, cheaper storage at scale, independent retention policies.

## Caching Strategy

- Goal: Reuse results for identical or equivalent inputs to save compute.
- Input signature: Compute a deterministic `input_signature` from normalized inputs and parameters; store in Results DB `jobs.input_signature`.
- Cache index: Maintain `result_cache` table keyed by `cache_key` (derived from signature + pipeline/task) with pointers to canonical job/artifacts and a `confidence_score`.
- Retrieval: On new job creation, check `result_cache`. If found and confidence is high enough, link artifacts and metrics; else run and update cache.
- Replacement: If a new result has a better `confidence_score`, update `result_cache` to point to the new canonical job.
- TTL: Use `expires_at` and `last_used_at` to age out entries.

## Storage Modality (Relational vs Non-Relational)

- Relational (Postgres)
  - Metadata DB: identity/RBAC (`users`, `roles`, `memberships`, `tokens`), orgs (`organizations`, `org_settings`), catalogs (`pipelines`, `pipeline_versions`, `molecules`, `artifacts`), auditing (`audit_logs`), external auth mapping (`identity_providers`, `identities`), global queries (`jobs_meta`).
  - Results DB: `jobs` (status, params, input_signature, timings, metrics), `job_inputs`, `job_outputs`, `docking_results`, `task_executions`, `task_results`, `result_cache`.
- Non-Relational / External
  - Object storage: all artifacts and logs bodies referenced by `uri`.
  - Logs backend: per-line logs for search/retention.
  - Optional search index: for faceted search across pipelines/molecules when needed.
