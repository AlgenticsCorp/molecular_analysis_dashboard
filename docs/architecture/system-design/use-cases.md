# Use Cases (Enhanced with Dynamic Task System)

This document captures the core use cases for the Molecular Analysis Dashboard across the defined user types (Root, Admin, Standard). Enhanced to include **dynamic task management** capabilities.

## Legend
- Actor: R = Root, A = Admin, S = Standard
- Data domains: Metadata DB (shared), Results DB (per org), Storage (per org), **Task Registry (database)**

---

## UC-001: Login and Session Management (R, A, S)
- Preconditions: User exists and is enabled; has valid roles in their org (except Root who is global).
- Main Flow:
  1. User submits credentials (or SSO) and org selection (if multi-org membership).
  2. System issues JWT (access/refresh) with `sub`, `org_id`, `roles`, **task permissions**.
  3. Client stores token and uses it for subsequent requests.
- Errors: Invalid credentials, disabled user, expired token.

## UC-002: Admin Defines Custom Tasks (A, R) **[NEW - Dynamic Task System]**
- Description: Create custom computational tasks with OpenAPI specifications stored in database.
- Preconditions: Admin or Root role; org context; task creation permissions.
- Main Flow:
  1. Admin defines task metadata (name, description, category, version).
  2. Admin specifies OpenAPI 3.0 interface specification (inputs, outputs, parameters).
  3. Admin configures service deployment (Docker image, resources, environment).
  4. System validates OpenAPI specification and stores in task registry database.
  5. Task becomes available for pipeline composition and direct execution.
- Variations: Clone existing tasks; version management; import/export task definitions.
- Errors: Invalid OpenAPI specification, resource constraint violations, permission denied.

## UC-003: Admin Defines a Pipeline (A, R)
- Description: Create/edit an interactive pipeline composed of **database-defined tasks** with defined inputs/outputs.
- Preconditions: Admin or Root role; org context; available tasks in registry.
- Main Flow:
  1. Admin creates pipeline with metadata (name, version, visibility, description).
  2. Admin selects tasks from **dynamic task registry** and defines task composition (DAG).
  3. Admin configures task parameters and data flow between tasks.
  4. System validates task compatibility and data flow schemas from **database task definitions**.
  5. Pipeline template stored with references to task definition IDs.
- Variations: Visual pipeline builder; template sharing; pipeline marketplace.
- Errors: Task compatibility issues, circular dependencies, missing task definitions.

## UC-003: Admin Manages Pipeline Versions (A, R)
- Description: Version existing pipelines; deprecate or publish versions for users.
- Preconditions: Pipeline exists; Admin or Root.
- Main Flow: Create new version from base; edit tasks and parameters; publish; optionally deprecate older versions.
- Errors: Version conflicts; immutable published versions.

## UC-004: Standard Executes Dynamic Tasks (S, A, R) **[NEW - Dynamic Task System]**
- Description: Execute individual tasks defined in database with auto-generated interfaces.
- Preconditions: Active task definitions in registry; user has task execution permissions.
- Main Flow:
  1. User browses **dynamic task library** loaded from database.
  2. System **auto-generates form interface** from task's OpenAPI specification.
  3. User fills parameters; system validates against **database-stored schema**.
  4. System discovers healthy task service instances via service discovery.
  5. Task executed via **HTTP call to containerized service**; execution tracked in database.
  6. Results returned according to task's OpenAPI response specification.
- Variations: Batch task execution; task chaining; real-time parameter validation.
- Errors: Service unavailable, parameter validation failure, task execution timeout.

## UC-005: Standard Runs a Predefined Pipeline (S, A, R)
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
