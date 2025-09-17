# Data Model ERD (Indicative)

A high-level entity relationship description for both the shared Metadata DB and per-org Results DBs.

Metadata DB (shared)
- organizations (org_id PK) 1—* user_org_memberships (*, org_id FK)
- users (user_id PK) 1—* user_org_memberships (*, user_id FK)
- roles (role_id PK, org_id FK) — many-to-many via role assignments (simplified as permissions[] here)
- pipelines (pipeline_id PK, org_id FK) 1—* pipeline_versions (pipeline_version_id PK)
- jobs_meta (job_id PK, org_id FK, pipeline_id FK, pipeline_version_id FK)
- audits (...)

Results DB (per org)
- jobs (job_id PK, pipeline_version_id, status, timings)
- job_inputs (job_id FK, key, uri, content_type)
- job_outputs (job_id FK, key, uri, content_type)
- docking_results (job_id FK, pose_rank, score, metadata)
- logs (job_id FK, ts, message)

Notes
- `org_id` present in all metadata tables to enforce tenant scoping.
- Artifacts referenced by URI; storage backend provides pre-signed access where applicable.
- Consider DB-level RLS in addition to repository filtering if supported.

See `DATABASES.md` for tenancy strategy and `USERS_AND_ROLES.md` for RBAC.

---

## ER Diagrams (Mermaid)

### Metadata DB (Shared)

```mermaid
erDiagram
	ORGANIZATIONS ||--o{ MEMBERSHIPS : "has"
	USERS ||--o{ MEMBERSHIPS : "joins"
	MEMBERSHIPS ||--o{ MEMBERSHIP_ROLES : "grants"
	ROLES ||--o{ MEMBERSHIP_ROLES : "assigned"
	ROLES ||--o{ ROLE_PERMISSIONS : "defines"

	ORGANIZATIONS ||--o{ PIPELINES : "owns"
	PIPELINES ||--o{ PIPELINE_VERSIONS : "versions"

	ORGANIZATIONS ||--o{ MOLECULES : "owns"
	ORGANIZATIONS ||--o{ ARTIFACTS : "owns"

	ORGANIZATIONS ||--o{ AUDIT_LOGS : "scopes"
	USERS ||--o{ AUDIT_LOGS : "performs"
	USERS ||--o{ TOKENS : "has"
	ORGANIZATIONS ||--o{ TOKENS : "scopes"
	IDENTITY_PROVIDERS ||--o{ IDENTITIES : "issues"
	USERS ||--o{ IDENTITIES : "linked"
	ORGANIZATIONS ||--o{ ORG_SETTINGS : "has"

	ORGANIZATIONS ||--o{ JOBS_META : "owns"
	PIPELINES ||--o{ JOBS_META : "referenced"
	PIPELINE_VERSIONS ||--o{ JOBS_META : "referenced"
	USERS ||--o{ JOBS_META : "submitted_by"

	ORGANIZATIONS {
		uuid org_id PK
		text name
		text status
		jsonb quotas
		timestamptz created_at
	}
	USERS {
		uuid user_id PK
		citext email
		text hashed_password
		bool enabled
		timestamptz created_at
	}
	ROLES {
		uuid role_id PK
		uuid org_id FK
		text name
	}
	ROLE_PERMISSIONS {
		uuid role_id FK
		text permission
	}
	MEMBERSHIPS {
		uuid user_id FK
		uuid org_id FK
		timestamptz created_at
	}
	MEMBERSHIP_ROLES {
		uuid user_id FK
		uuid org_id FK
		uuid role_id FK
	}
	PIPELINES {
		uuid pipeline_id PK
		uuid org_id FK
		text name
		text description
		text latest_version
		visibility visibility
		uuid created_by FK
		timestamptz created_at
	}
	PIPELINE_VERSIONS {
		uuid pipeline_version_id PK
		uuid pipeline_id FK
		text version
		jsonb spec
		bool published
		uuid created_by FK
		timestamptz created_at
	}
	MOLECULES {
		uuid molecule_id PK
		uuid org_id FK
		text name
		text format
		text uri
		bigint size_bytes
		text checksum
		uuid created_by FK
		timestamptz created_at
	}
	IDENTITY_PROVIDERS {
		uuid provider_id PK
		text name
		text kind
		text config
	}
	IDENTITIES {
		uuid identity_id PK
		uuid user_id FK
		uuid provider_id FK
		text subject
		text email
		timestamptz linked_at
	}
	ORG_SETTINGS {
		uuid org_id PK
		text storage_bucket
		text storage_prefix
		text logs_backend
		jsonb config
	}
	ARTIFACTS {
		uuid artifact_id PK
		uuid org_id FK
		text purpose
		text content_type
		text uri
		bigint size_bytes
		text checksum
		uuid created_by FK
		timestamptz created_at
	}
	AUDIT_LOGS {
		uuid audit_id PK
		uuid org_id FK
		uuid user_id FK
		text action
		text entity_type
		text entity_id
		jsonb metadata
		timestamptz ts
	}
	JOBS_META {
		uuid job_id PK
		uuid org_id FK
		uuid pipeline_id FK
		uuid pipeline_version_id FK
		uuid submitted_by FK
		job_status status
		int priority
		timestamptz created_at
		timestamptz updated_at
	}
	TOKENS {
		uuid token_id PK
		uuid user_id FK
		uuid org_id FK
		text kind
		timestamptz expires_at
		bool revoked
		timestamptz created_at
	}
```

### Results DB (Per Organization)

```mermaid
erDiagram
	JOBS ||--o{ JOB_INPUTS : "has"
	JOBS ||--o{ JOB_OUTPUTS : "produces"
	JOBS ||--o{ DOCKING_RESULTS : "has"
	JOBS ||--o{ TASK_EXECUTIONS : "composed_of"
	JOBS ||--o{ TASK_RESULTS : "task_results"
	JOBS ||--o{ JOB_EVENTS : "events"
	JOBS ||--o{ RESULT_CACHE : "canonical_for"

	JOBS {
		uuid job_id PK
		text pipeline_version
		job_status status
		text input_signature
		jsonb params
		jsonb timings
		jsonb metrics
		jsonb error
		timestamptz created_at
		timestamptz updated_at
	}
	JOB_INPUTS {
		uuid job_id FK
		text key
		text uri
		text content_type
		bigint size_bytes
		text checksum
	}
	JOB_OUTPUTS {
		uuid job_id FK
		text key
		text uri
		text content_type
		bigint size_bytes
		text checksum
	}
	DOCKING_RESULTS {
		uuid job_id FK
		int pose_rank
		float affinity
		float rmsd
		jsonb metadata
	}
	TASK_RESULTS {
		uuid job_id FK
		text task_name
		text service_name
		text schema_version
		float confidence_score
		jsonb result_data
	}
	TASK_EXECUTIONS {
		uuid exec_id PK
		uuid job_id FK
		text task_name
		job_status status
		timestamptz started_at
		timestamptz ended_at
		int retries
		text logs_uri
	}
	JOB_EVENTS {
		uuid job_id FK
		bigint seq_no
		timestamptz ts
		text event
		text detail
		jsonb metadata
	}
	RESULT_CACHE {
		text cache_key PK
		text pipeline_version
		text task_name
		uuid canonical_job_id
		float confidence_score
		jsonb artifact_map
		jsonb metrics_summary
		int hit_count
		timestamptz last_used_at
		timestamptz created_at
		timestamptz expires_at
	}
```

### Logs DB (Separate)

While `TASK_EXECUTIONS.logs_uri` points to logs in object storage or a log backend, high-volume log lines should be stored in a separate logging database.

```mermaid
erDiagram
	LOG_STREAMS ||--o{ LOG_ENTRIES : "contains"

	LOG_STREAMS {
		text stream_id PK
		uuid org_id
		uuid job_id
		text task_name
		text source
	}
	LOG_ENTRIES {
		text stream_id FK
		bigint seq_no
		timestamptz ts
		text level
		jsonb fields
		text message
	}
```

Recommendation: Use a dedicated log store (e.g., Loki, OpenSearch) and keep only `logs_uri` pointers in relational DBs.

---

## Storage Modality Guidance

- Relational (Postgres)
  - Metadata DB: organizations, users, roles, role_permissions, memberships, membership_roles, pipelines, pipeline_versions, molecules, artifacts, audit_logs, tokens, identities, identity_providers, org_settings, jobs_meta
  - Results DB (per org): jobs (with input_signature, params, timings, metrics), job_inputs, job_outputs, docking_results, task_executions, task_results, result_cache
- Non-relational / external
  - Object storage: all file bodies (inputs/outputs/log archives), large result matrices; referenced via `uri`
  - Logs database: log lines (LOG_ENTRIES) retained outside Postgres; keep pointers only in Postgres
  - Search index (optional): for rich text/facet search over pipelines/molecules/tags when needed

---

## Potential Entities to Add (Optional/Future)

These are common additions that can enhance functionality; adopt incrementally as needed.

- Pipeline modeling (Metadata DB)
	- `TASKS`, `TASK_EDGES`: Normalize pipeline DAG inside a version for cross-version analytics and validation beyond the JSON `spec`.
	- `ADAPTERS`/`EXECUTION_PROFILES`: Catalog of execution backends and resource presets.
- Tagging & discovery (Metadata DB)
	- `TAGS`, `PIPELINE_TAGS`, `MOLECULE_TAGS`: Faceted search and organization of pipelines/molecules.
- Org configuration (Metadata DB)
	- `ORG_SETTINGS` or `ORG_INTEGRATIONS`: Per-org configuration like storage bucket/prefix, webhook endpoints, SSO provider configs.
- Identity & invitations (Metadata DB)
	- `INVITATIONS` (email, org, role, token, expiry), `PASSWORD_RESETS`, `IDENTITIES` (SSO subject mapping), `IDENTITY_PROVIDERS`.
- Notifications & webhooks (Metadata DB)
	- `WEBHOOKS` (subscriptions), `WEBHOOK_DELIVERIES` (attempts, status), `NOTIFICATIONS` (in-app).
- Service accounts & automation (Metadata DB)
	- `SERVICE_ACCOUNTS` (non-human principals) and role assignments.
- Results DB augmentations (per org)
	- `JOBS.params` (added above) to persist engine parameters.
	- `JOB_EVENTS` (timeline) for a compact status history.
	- `STRUCTURE_PROPERTIES` or `MOLECULE_PROPERTIES` (computed descriptors) if you compute/query them frequently.
