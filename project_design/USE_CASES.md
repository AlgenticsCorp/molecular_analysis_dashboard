# Use Cases

This document captures the core use cases for the Molecular Analysis Dashboard across the defined user types (Root, Admin, Standard). Each use case specifies actors, preconditions, main success scenario, key variations, and error cases.

## Legend
- Actor: R = Root, A = Admin, S = Standard
- Data domains: Metadata DB (shared), Results DB (per org), Storage (per org)

---

## UC-001: Login and Session Management (R, A, S)
- Preconditions: User exists and is enabled; has valid roles in their org (except Root who is global).
- Main Flow:
  1. User submits credentials (or SSO) and org selection (if multi-org membership).
  2. System issues JWT (access/refresh) with `sub`, `org_id`, `roles`.
  3. Client stores token and uses it for subsequent requests.
- Errors: Invalid credentials, disabled user, expired token.

## UC-002: Admin Defines a Pipeline (A, R)
- Description: Create/edit an interactive pipeline composed of tasks/jobs with defined inputs/outputs.
- Preconditions: Admin or Root role; org context.
- Main Flow:
  1. Admin creates pipeline with metadata (name, version, visibility, description).
  2. Admin defines tasks (e.g., prepare ligand, prepare protein, docking, post-processing) with typed I/O schemas.
  3. Admin specifies execution adapters (e.g., Vina, Smina, Gnina, script, container) and parameters.
  4. System validates schema compatibility and persists in Metadata DB.
- Variations: Import/export pipeline spec as YAML/JSON; clone/branch pipeline versions.
- Errors: Schema mismatch, missing adapters, permission denied.

## UC-003: Admin Manages Pipeline Versions (A, R)
- Description: Version existing pipelines; deprecate or publish versions for users.
- Preconditions: Pipeline exists; Admin or Root.
- Main Flow: Create new version from base; edit tasks and parameters; publish; optionally deprecate older versions.
- Errors: Version conflicts; immutable published versions.

## UC-004: Standard Runs a Predefined Pipeline (S, A, R)
- Description: Execute a published pipeline by providing inputs and parameters.
- Preconditions: Published pipeline; user has `job.create` and access to required inputs.
- Main Flow:
  1. User selects pipeline version and uploads or selects existing molecules/inputs.
  2. System validates inputs against task I/O schemas.
  3. System computes an `input_signature` and checks cache (if enabled). If cache hit with sufficient confidence, return canonical job; else create a Job (PENDING) in Results DB and enqueue Celery task(s).
  4. Worker executes tasks (selected docking engine), stores artifacts in org storage, updates job status.
  5. User polls or subscribes; system returns results (scores, poses, links to artifacts).
- Variations: Batch runs; scheduled runs; priority queues.
- Errors: Validation failure, resource limits, adapter execution errors.

## UC-005: View Job Status and Results (S, A, R)
- Preconditions: Job exists in user’s org (or Root).
- Main Flow: Query by job_id; return status, events timeline, logs (via `logs_uri`), metrics, per-task results (JSONB) with confidence scores, and artifact URLs; render interactive 3D view.
- Variations: Filter/sort by pipeline, date, status.
- Errors: Permission denied, missing artifacts.

## UC-006: Manage Users and Roles (A, R)
- Description: Admin assigns roles and permissions within the organization; Root can manage across orgs.
- Main Flow: Invite/create users; assign roles; disable/reactivate accounts; audit changes.
- Errors: Permission denied; role conflicts.

## UC-007: Org Provisioning (R)
- Description: Root provisions a new organization.
- Main Flow: Create org record (Metadata DB); create per-org Results DB and Storage namespace/bucket; issue initial Admin account; set quotas and policies.
- Errors: Provisioning failures (DB/storage), quota conflicts.

## UC-008: Artifact Management (S, A, R)
- Description: Upload/download molecules and artifacts via Storage Adapter.
- Main Flow: Put/Get files; list artifacts by job; generate pre-signed URLs for downloads.
- Errors: Size limits, unsupported formats, permission denied.

## UC-009: Pipeline Catalog & Discovery (S, A)
- Description: Browse available pipelines; filter by category, tags, org visibility.
- Main Flow: Read from Metadata DB; return published pipelines and versions.

## UC-010: Auditing & Compliance (A, R)
- Description: View audit logs for security events and pipeline changes.

## UC-011: Cache Management (A, R)
- Description: Inspect and manage cache entries for pipelines/tasks.
- Main Flow: List cache entries; view `confidence_score`, `hit_count`, `last_used_at`; invalidate or pin canonical entries; adjust TTL.
- Errors: Permission denied.

## UC-012: External Authentication (R)
- Description: Integrate external identity providers (Microsoft/Google/SSO) and link user identities.
- Main Flow: Configure providers; link accounts on first login; enforce RBAC via memberships/roles.
- Errors: Misconfiguration, provider errors.
---

## Schemas & Contracts (High Level)

- Pipeline Spec
  - id, org_id, name, version, visibility
  - tasks: [ { id, name, adapter, inputs: schema, outputs: schema, params } ]
- Job
  - id, org_id, pipeline_id, version, status, created_at, updated_at
  - inputs (URIs), outputs (URIs), metrics, logs
- Artifact
  - uri, content_type, size, checksum, created_by, created_at

---

## Non-Functional Requirements (per Use Case)

- Security: org isolation via `org_id`, RBAC checks at endpoints
- Reliability: retries for external adapters; idempotent task design
- Performance: async I/O; background processing; pagination for listings
- Observability: structured logs with `job_id`, metrics for queue depth/latency
- Compliance: audit trails for critical operations
