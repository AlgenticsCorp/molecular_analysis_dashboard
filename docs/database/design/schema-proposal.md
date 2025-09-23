# Schema Proposal (PostgreSQL)

This document provides concrete PostgreSQL DDL (first pass) for both databases:
- Metadata DB (shared across all orgs)
- Results DB (one per organization)

Assumptions
- UUIDs as primary keys (Postgres `gen_random_uuid()` from `pgcrypto` or via application).
- Timestamps in UTC (`TIMESTAMPTZ`) with server default `now()`.
- JSONB for flexible specs/metadata.
- Multi-tenancy: Metadata DB includes `org_id` where applicable; Results DB is per-org, so `org_id` is not repeated there.
- Status fields use Postgres ENUMs for clarity and integrity.

Note: This is a developer-friendly starting point; refine during implementation and migrations.

---

## 0) Extensions (enable once per DB)

```sql
-- UUID generation if you want DB-side defaults (optional)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Case-insensitive text (optional for emails)
CREATE EXTENSION IF NOT EXISTS citext;
```

---

## 1) Metadata DB (shared)

### 1.1 Enums
```sql
CREATE TYPE visibility AS ENUM ('private', 'org', 'public');
CREATE TYPE job_status AS ENUM ('PENDING','RUNNING','COMPLETED','FAILED','CANCELED');
CREATE TYPE health_status AS ENUM ('healthy', 'unhealthy', 'starting', 'unknown');
```

### 1.2 Dynamic Task System Tables
```sql
-- Task definitions with OpenAPI specifications
CREATE TABLE task_definitions (
  task_definition_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id              UUID NOT NULL REFERENCES organizations(org_id),
  task_id             VARCHAR(100) NOT NULL,
  version             VARCHAR(20) NOT NULL DEFAULT '1.0.0',
  metadata            JSONB NOT NULL DEFAULT '{}', -- title, description, category, tags
  interface_spec      JSONB NOT NULL, -- OpenAPI 3.0 specification
  service_config      JSONB NOT NULL DEFAULT '{}', -- Docker image, resources, env
  is_active           BOOLEAN NOT NULL DEFAULT true,
  is_system           BOOLEAN NOT NULL DEFAULT false,
  created_by          UUID REFERENCES users(user_id),
  created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(org_id, task_id, version)
);

-- Running task service instances
CREATE TABLE task_services (
  service_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_definition_id  UUID NOT NULL REFERENCES task_definitions(task_definition_id),
  service_url         VARCHAR(500) NOT NULL,
  pod_name            VARCHAR(200),
  node_name           VARCHAR(200),
  health_status       health_status NOT NULL DEFAULT 'unknown',
  last_health_check   TIMESTAMPTZ,
  resources_used      JSONB DEFAULT '{}',
  started_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(task_definition_id, service_url)
);

-- Pipeline templates for composable workflows
CREATE TABLE pipeline_templates (
  template_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id              UUID NOT NULL REFERENCES organizations(org_id),
  name                VARCHAR(100) NOT NULL,
  display_name        VARCHAR(100) NOT NULL,
  description         TEXT,
  category            VARCHAR(50) NOT NULL,
  workflow_definition JSONB NOT NULL, -- DAG specification
  default_parameters  JSONB DEFAULT '{}',
  is_public           BOOLEAN NOT NULL DEFAULT false,
  is_system           BOOLEAN NOT NULL DEFAULT false,
  version             VARCHAR(20) NOT NULL DEFAULT '1.0.0',
  created_by          UUID REFERENCES users(user_id),
  created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(org_id, name, version)
);

-- Pipeline task composition
CREATE TABLE pipeline_task_steps (
  step_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id         UUID NOT NULL REFERENCES pipeline_templates(template_id) ON DELETE CASCADE,
  task_definition_id  UUID NOT NULL REFERENCES task_definitions(task_definition_id),
  step_name           VARCHAR(100) NOT NULL,
  step_order          INTEGER NOT NULL,
  depends_on          JSONB DEFAULT '[]', -- Array of prerequisite step IDs
  parameter_overrides JSONB DEFAULT '{}',
  created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### 1.3 Identity & Access
```sql
CREATE TABLE organizations (
  org_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name           TEXT NOT NULL UNIQUE,
  status         TEXT NOT NULL DEFAULT 'active',
  quotas         JSONB NOT NULL DEFAULT '{}',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
  user_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email          CITEXT NOT NULL UNIQUE,
  hashed_password TEXT NOT NULL,
  enabled        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE roles (
  role_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id         UUID REFERENCES organizations(org_id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  -- Either keep permissions in JSONB or normalize; here we normalize via role_permissions
  UNIQUE (org_id, name)
);

CREATE TABLE role_permissions (
  role_id        UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
  permission     TEXT NOT NULL,
  PRIMARY KEY (role_id, permission)
);

CREATE TABLE memberships (
  user_id        UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  org_id         UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, org_id)
);

CREATE TABLE membership_roles (
  user_id        UUID NOT NULL,
  org_id         UUID NOT NULL,
  role_id        UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, org_id, role_id),
  FOREIGN KEY (user_id, org_id) REFERENCES memberships(user_id, org_id) ON DELETE CASCADE
);

CREATE TABLE audit_logs (
  audit_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id         UUID NULL REFERENCES organizations(org_id) ON DELETE SET NULL,
  user_id        UUID NULL REFERENCES users(user_id) ON DELETE SET NULL,
  action         TEXT NOT NULL,
  entity_type    TEXT NOT NULL,
  entity_id      TEXT NULL,
  metadata       JSONB NOT NULL DEFAULT '{}',
  ts             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_logs_org_ts ON audit_logs(org_id, ts DESC);
```

### 1.3 Catalog
```sql
CREATE TABLE pipelines (
  pipeline_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id         UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  description    TEXT NOT NULL DEFAULT '',
  latest_version TEXT NULL,
  visibility     visibility NOT NULL DEFAULT 'org',
  created_by     UUID NULL REFERENCES users(user_id) ON DELETE SET NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (org_id, name)
);

CREATE TABLE pipeline_versions (
  pipeline_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pipeline_id    UUID NOT NULL REFERENCES pipelines(pipeline_id) ON DELETE CASCADE,
  version        TEXT NOT NULL,
  spec           JSONB NOT NULL, -- task graph, I/O schemas, params
  published      BOOLEAN NOT NULL DEFAULT FALSE,
  created_by     UUID NULL REFERENCES users(user_id) ON DELETE SET NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (pipeline_id, version)
);
```

### 1.4 Data Catalog (Molecules & Artifacts)
```sql
CREATE TABLE molecules (
  molecule_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id         UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  format         TEXT NOT NULL,   -- pdb/sdf/pdbqt
  uri            TEXT NOT NULL,   -- mad:// or s3:// or file://
  size_bytes     BIGINT NULL,
  checksum       TEXT NULL,
  created_by     UUID NULL REFERENCES users(user_id) ON DELETE SET NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_molecules_org_name ON molecules(org_id, name);

-- Optional generic artifact registry (inputs/outputs). Can be omitted if all outputs live only in Results DB.
CREATE TABLE artifacts (
  artifact_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id         UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
  purpose        TEXT NOT NULL,        -- input/output/log/etc.
  content_type   TEXT NULL,
  uri            TEXT NOT NULL,
  size_bytes     BIGINT NULL,
  checksum       TEXT NULL,
  created_by     UUID NULL REFERENCES users(user_id) ON DELETE SET NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 1.4a External Identity & Org Settings
```sql
CREATE TABLE identity_providers (
  provider_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  kind          TEXT NOT NULL,       -- 'azure_ad', 'google', 'saml', etc.
  config        JSONB NOT NULL DEFAULT '{}' -- client_id, tenant, endpoints, etc.
);

CREATE TABLE identities (
  identity_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  provider_id   UUID NOT NULL REFERENCES identity_providers(provider_id) ON DELETE CASCADE,
  subject       TEXT NOT NULL,       -- stable external subject identifier
  email         TEXT NULL,
  linked_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (provider_id, subject)
);

CREATE TABLE org_settings (
  org_id        UUID PRIMARY KEY REFERENCES organizations(org_id) ON DELETE CASCADE,
  storage_bucket TEXT NULL,
  storage_prefix TEXT NULL,
  logs_backend   TEXT NULL,          -- e.g., 'loki', 'opensearch', 's3'
  config         JSONB NOT NULL DEFAULT '{}'
);
```

### 1.5 Jobs (Lightweight Meta for Global Queries)
```sql
CREATE TABLE jobs_meta (
  job_id         UUID PRIMARY KEY,           -- mirrors Results DB job_id
  org_id         UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
  pipeline_id    UUID NOT NULL REFERENCES pipelines(pipeline_id) ON DELETE RESTRICT,
  pipeline_version_id UUID NOT NULL REFERENCES pipeline_versions(pipeline_version_id) ON DELETE RESTRICT,
  submitted_by   UUID NULL REFERENCES users(user_id) ON DELETE SET NULL,
  status         job_status NOT NULL DEFAULT 'PENDING',
  priority       INT NOT NULL DEFAULT 0,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_jobs_meta_org_status_created ON jobs_meta(org_id, status, created_at DESC);
CREATE INDEX idx_jobs_meta_org_created ON jobs_meta(org_id, created_at DESC);
```

### 1.6 Tokens (Optional)
```sql
CREATE TABLE tokens (
  token_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  org_id         UUID NULL REFERENCES organizations(org_id) ON DELETE SET NULL,
  kind           TEXT NOT NULL, -- refresh, api_key, etc.
  expires_at     TIMESTAMPTZ NOT NULL,
  revoked        BOOLEAN NOT NULL DEFAULT FALSE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 2) Results DB (per organization)

### 2.1 Enums (repeat in each Results DB)
```sql
CREATE TYPE job_status AS ENUM ('PENDING','RUNNING','COMPLETED','FAILED','CANCELED');
```

### 2.2 Core Job Tables
```sql
CREATE TABLE jobs (
  job_id         UUID PRIMARY KEY,
  pipeline_version TEXT NOT NULL,
  status         job_status NOT NULL DEFAULT 'PENDING',
  input_signature TEXT NULL,            -- deterministic hash of normalized inputs/params
  params         JSONB NOT NULL DEFAULT '{}',
  timings        JSONB NOT NULL DEFAULT '{}',   -- queued/started/ended
  metrics        JSONB NOT NULL DEFAULT '{}',
  error          JSONB NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_jobs_status_updated ON jobs(status, updated_at DESC);
CREATE INDEX idx_jobs_input_signature ON jobs(input_signature);

CREATE TABLE job_inputs (
  job_id         UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
  key            TEXT NOT NULL,    -- e.g., ligand_uri, protein_uri
  uri            TEXT NOT NULL,
  content_type   TEXT NULL,
  size_bytes     BIGINT NULL,
  checksum       TEXT NULL,
  PRIMARY KEY (job_id, key)
);

CREATE TABLE job_outputs (
  job_id         UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
  key            TEXT NOT NULL,    -- e.g., ligand_pdbqt, log
  uri            TEXT NOT NULL,
  content_type   TEXT NULL,
  size_bytes     BIGINT NULL,
  checksum       TEXT NULL,
  PRIMARY KEY (job_id, key)
);

CREATE TABLE docking_results (
  job_id         UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
  pose_rank      INT NOT NULL,
  affinity       DOUBLE PRECISION NOT NULL,
  rmsd           DOUBLE PRECISION NULL,
  metadata       JSONB NOT NULL DEFAULT '{}',
  PRIMARY KEY (job_id, pose_rank)
);
CREATE INDEX idx_docking_results_affinity ON docking_results(affinity);
```

### 2.3 Task Execution & Logs (optional but useful)
```sql
CREATE TABLE task_executions (
  exec_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id         UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
  task_name      TEXT NOT NULL,
  status         job_status NOT NULL DEFAULT 'PENDING',
  started_at     TIMESTAMPTZ NULL,
  ended_at       TIMESTAMPTZ NULL,
  retries        INT NOT NULL DEFAULT 0,
  logs_uri       TEXT NULL
);

CREATE TABLE task_logs (
  job_id         UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
  line_no        BIGINT NOT NULL,
  ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
  level          TEXT NOT NULL DEFAULT 'INFO',
  message        TEXT NOT NULL,
  PRIMARY KEY (job_id, line_no)
);
```

### 2.4 Task-level Results and Caching
```sql
-- Generic task-level results (service-specific schema via JSONB) and confidence scoring
CREATE TABLE task_results (
  job_id         UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
  task_name      TEXT NOT NULL,
  service_name   TEXT NULL,                 -- e.g., 'vina', 'prep_ligand'
  schema_version TEXT NULL,
  confidence_score DOUBLE PRECISION NULL,   -- for cache/replacement policies
  result_data    JSONB NOT NULL DEFAULT '{}',
  PRIMARY KEY (job_id, task_name)
);

-- Result cache to reuse outputs for repeated inputs
CREATE TABLE result_cache (
  cache_key      TEXT PRIMARY KEY,          -- hash of normalized inputs + pipeline/task
  pipeline_version TEXT NOT NULL,
  task_name      TEXT NOT NULL,
  canonical_job_id UUID NOT NULL,
  confidence_score DOUBLE PRECISION NULL,
  artifact_map   JSONB NOT NULL DEFAULT '{}',  -- keys -> URIs
  metrics_summary JSONB NOT NULL DEFAULT '{}',
  hit_count      INT NOT NULL DEFAULT 0,
  last_used_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at     TIMESTAMPTZ NULL
);

-- Job event timeline (append-only)
CREATE TABLE job_events (
  job_id       UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
  seq_no       BIGINT NOT NULL,
  ts           TIMESTAMPTZ NOT NULL DEFAULT now(),
  event        TEXT NOT NULL,      -- e.g., QUEUED, STARTED, TASK_COMPLETED
  detail       TEXT NULL,
  metadata     JSONB NOT NULL DEFAULT '{}',
  PRIMARY KEY (job_id, seq_no)
);
```

---

## 3) Conventions & Migrations

- Naming: `snake_case` for tables/columns; PK as `<name>_id` where applicable.
- Foreign keys: Use `ON DELETE CASCADE` for dependent records (e.g., job_* tables), and `RESTRICT` where you need integrity (pipeline references).
- Indexes: Favor composite indexes for common filters (e.g., `(org_id, status, created_at)` in metadata `jobs_meta`).
- Timestamps: Maintain `updated_at` in app or via triggers (optional).
- Alembic: Use consistent revision messages (e.g., `feat(db): add jobs_meta`); consider separate migration contexts for Metadata DB and each Results DB.
- Types: Reuse ENUM names across DBs; define in each Results DB during provisioning.

## 4) Provisioning Flow (Org Lifecycle)

1. Create `organizations` row in Metadata DB.
2. Provision a new Results DB for the org (or a schema/namespace), apply this Results DDL.
3. Create a storage bucket/prefix for the org.
4. Seed initial `roles` and an `admin` membership for the org.

## 5) Notes & Variations

- Artifacts registry in Metadata DB is optional; many systems store only inputs there and keep outputs/logs referenced in Results DB.
- You may embed task graph in `pipeline_versions.spec` or normalize with `tasks` and `task_edges` tables if you need cross-version analytics.
- If you prefer not to use Postgres ENUMs, replace with `TEXT` plus a CHECK constraint (or use application-level validation).

---

This proposal aligns with the entities in `USE_CASES.md`, tenancy model in `DATABASES.md`, and API flows in `API_CONTRACT.md`. Refine during Sprint 2 as repositories and migrations are implemented.
