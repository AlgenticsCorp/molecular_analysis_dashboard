# API Contract (Enhanced)

This document defines the REST API surface for the Molecular Analysis Dashboard, including **dynamic task management** and traditional molecular analysis endpoints.

Notes:
- All endpoints return JSON unless serving files.
- Authentication: Bearer JWT, except for `/health`, `/ready`, and auth endpoints.
- Multi-tenancy: All authenticated requests include `org_id` in JWT; server enforces org scoping.
- **Dynamic Tasks**: Task definitions and interfaces are loaded from database with OpenAPI 3.0 specifications.
- Error format (standardized):
  ```json
  { "error": { "code": "<STRING>", "message": "<HUMAN_READABLE>", "details": { /* optional */ } } }
  ```

---

## Health & Readiness

- GET `/health`
  - Auth: none
  - 200: `{ "status": "ok" }`
  - Purpose: Liveness probe only (process up).

- GET `/ready`
  - Auth: none
  - 200: `{ "status": "ready" , "checks": { "db": "ok", "broker": "ok", "task_registry": "ok" } }`
  - 503: `{ "status": "not_ready", "checks": { ... } }`
  - Purpose: Readiness probe (DB + broker + task registry connectivity).

---

## Dynamic Task Registry

- GET `/api/v1/task-registry/tasks`
  - Auth: Bearer; Roles: `standard`+
  - Query Params: `category` (optional), `is_active` (optional), `search` (optional)
  - 200:
    ```json
    {
      "tasks": [
        {
          "task_definition_id": "uuid",
          "task_id": "molecular-docking",
          "version": "1.0.0",
          "metadata": {
            "title": "Molecular Docking",
            "description": "Protein-ligand docking using various engines",
            "category": "Analysis",
            "tags": ["docking", "protein", "ligand"],
            "icon": "fas fa-molecule"
          },
          "interface_spec": { /* OpenAPI 3.0 specification */ },
          "service_config": { "docker_image": "...", "resources": {...} },
          "is_active": true,
          "is_system": false
        }
      ],
      "categories": ["Analysis", "Visualization", "Processing"],
      "total_count": 25
    }
    ```

- GET `/api/v1/task-registry/tasks/{task_id}/versions/{version}/interface`
  - Auth: Bearer; org-scoped
  - 200: OpenAPI 3.0 specification for task interface
  - 404: task/version not found

- POST `/api/v1/task-registry/tasks`
  - Auth: Bearer; Roles: `admin`+ (custom task creation)
  - Body:
    ```json
    {
      "task_id": "custom-analysis",
      "version": "1.0.0",
      "metadata": { "title": "...", "description": "...", "category": "..." },
      "interface_spec": { /* OpenAPI 3.0 specification */ },
      "service_config": { "docker_image": "...", "resources": {...} }
    }
    ```
  - 201: Task definition created
  - 400: validation error (invalid OpenAPI spec)

- GET `/api/v1/task-registry/tasks/{task_id}/services`
  - Auth: Bearer; org-scoped
  - 200:
    ```json
    {
      "services": [
        {
          "service_id": "uuid",
          "service_url": "http://task-docking-v1:8080",
          "health_status": "healthy",
          "resources_used": { "cpu": "500m", "memory": "1Gi" },
          "last_health_check": "iso"
        }
      ]
    }
    ```

---

## Dynamic Task Execution

- POST `/api/v1/tasks/{task_id}/execute`
  - Auth: Bearer; Roles: `standard`+
  - Query Params: `version` (optional, defaults to latest)
  - Body: Dynamic based on task's OpenAPI specification
  - 202:
    ```json
    {
      "execution_id": "uuid",
      "task_id": "molecular-docking",
      "version": "1.0.0",
      "status": "SUBMITTED",
      "service_url": "http://task-docking-v1:8080",
      "estimated_duration": 300
    }
    ```
  - 400: parameter validation error
  - 404: task not found
  - 503: no healthy services available

- GET `/api/v1/executions/{execution_id}/status`
  - Auth: Bearer; org-scoped
  - 200:
    ```json
    {
      "execution_id": "uuid",
      "status": "PENDING|RUNNING|COMPLETED|FAILED",
      "progress": 0.75,
      "started_at": "iso",
      "updated_at": "iso",
      "estimated_completion": "iso"
    }
    ```

- GET `/api/v1/executions/{execution_id}/results`
  - Auth: Bearer; org-scoped
  - 200: Dynamic response based on task's OpenAPI output specification
  - 202: task not yet completed

---

## Pipeline Templates

- GET `/api/v1/pipeline-templates`
  - Auth: Bearer; org-scoped
  - Query Params: `category` (optional), `is_public` (optional)
  - 200:
    ```json
    {
      "templates": [
        {
          "template_id": "uuid",
          "name": "protein-ligand-screening",
          "display_name": "Protein-Ligand Screening Pipeline",
          "description": "Multi-step docking and analysis workflow",
          "category": "Screening",
          "workflow_definition": { /* DAG specification */ },
          "is_public": false,
          "version": "1.0.0"
        }
      ]
    }
    ```

- POST `/api/v1/pipeline-templates/{template_id}/instantiate`
  - Auth: Bearer; org-scoped
  - Body:
    ```json
    {
      "name": "My Screening Job",
      "parameters": { /* template-specific parameters */ },
      "molecule_ids": ["uuid1", "uuid2"]
    }
    ```
  - 202: Pipeline instance created and queued for execution

---

## Auth

- POST `/api/v1/auth/register`
  - Auth: none (may be restricted to Root/Admin depending on policy)
  - Body:
    ```json
    { "email": "user@example.com", "password": "string", "org_id": "uuid" }
    ```
  - 201: `{ "user_id": "uuid", "email": "...", "org_id": "uuid" }`
  - 409: user exists

- POST `/api/v1/auth/token`
  - Auth: none
  - Body (form or JSON): `{ "email": "...", "password": "...", "org_id": "uuid" }`
  - 200: `{ "access_token": "jwt", "refresh_token": "jwt", "token_type": "bearer" }`
  - 401: invalid credentials

---

## Molecules & Artifacts

- POST `/api/v1/molecules/upload`
  - Auth: Bearer; Roles: `standard`+ (org-scoped)
  - Content-Type: `multipart/form-data`
    - Fields: `file` (binary), `name` (string), `format` (e.g., `pdb`, `sdf`, `pdbqt`)
  - 201:
    ```json
    { "molecule_id": "uuid", "name": "...", "format": "pdb", "uri": "mad://org/<org_id>/molecules/<id>.<ext>" }
    ```
  - 400: unsupported format or size exceeded

- GET `/api/v1/artifacts/{uri}` (optional if serving via pre-signed URLs)
  - Auth: Bearer; org-scoped access check
  - 302/200: file stream or redirect to pre-signed URL

---

## Pipelines & Jobs

- POST `/api/v1/pipelines/{pipeline_id}/jobs`
  - Auth: Bearer; Roles: `standard`+ with `job.create`
  - Query Params (optional): `use_cache=true|false` (default: `true`)
  - Body:
    ```json
    {
      "pipeline_version": "1.0.0",
      "inputs": { "ligand_uri": "...", "protein_uri": "..." },
      "params": { /* engine-specific params */ }
    }
    ```
  - 202:
    ```json
    { "job_id": "uuid", "status": "PENDING", "cache": { "hit": false } }
    ```
  - 200 (cache hit):
    ```json
    { "job_id": "uuid", "status": "COMPLETED", "cache": { "hit": true, "canonical_job_id": "uuid", "confidence_score": 0.92 } }
    ```
  - 400: validation error (I/O schema mismatch)
  - 404: pipeline/version not found

- GET `/api/v1/jobs/{job_id}/status`
  - Auth: Bearer; org-scoped
  - 200:
    ```json
    { "job_id": "uuid", "status": "PENDING|RUNNING|COMPLETED|FAILED", "started_at": "iso", "updated_at": "iso" }
    ```

- GET `/api/v1/jobs/{job_id}/results`
  - Auth: Bearer; org-scoped
  - 200:
    ```json
    {
      "job_id": "uuid",
      "scores": [ { "pose": 1, "affinity": -7.4, "confidence_score": 0.92 } ],
      "artifacts": {
        "ligand_pdbqt": "mad://org/<org_id>/jobs/<job_id>/ligand_out.pdbqt",
        "log": "mad://org/<org_id>/jobs/<job_id>/<engine>.log"
      },
      "task_results": [ { "task_name": "dock", "service_name": "vina|smina|gnina|<custom>", "schema_version": "1", "confidence_score": 0.92, "result_data": { /* engine-specific */ } } ]
    }
    ```

- GET `/api/v1/jobs/{job_id}/files/{filename}` (optional direct serve)
  - Auth: Bearer; org-scoped
  - 200: file stream

- GET `/api/v1/jobs/{job_id}/events`
  - Auth: Bearer; org-scoped
  - 200:
    ```json
    [
      { "seq": 1, "ts": "iso", "event": "QUEUED" },
      { "seq": 2, "ts": "iso", "event": "STARTED" },
      { "seq": 3, "ts": "iso", "event": "TASK_COMPLETED", "detail": "dock" }
    ]
    ```

- GET `/api/v1/jobs/{job_id}/logs` (optional)
  - Auth: Bearer; org-scoped
  - 302/200: redirect or signed URL to logs in the configured logs backend or object storage

---

## Permissions & Tenancy (Summary)

- JWT claims: `sub`, `org_id`, `roles`, optional `scopes`, `exp`.
- Org isolation: every read/write is filtered by `org_id` at repository layer.
- Roles:
  - standard: run jobs, view own results
  - admin: manage users/roles/pipelines in org
  - root: cross-org provisioning/visibility

---

## Error Codes (Enhanced)

- `AUTH_INVALID_CREDENTIALS`
- `AUTH_UNAUTHORIZED`
- `ORG_FORBIDDEN`
- `PIPELINE_NOT_FOUND`
- `VALIDATION_FAILED`
- `JOB_NOT_FOUND`
- `ARTIFACT_NOT_FOUND`
- `TASK_NOT_FOUND`
- `TASK_VALIDATION_FAILED`
- `SERVICE_UNAVAILABLE`
- `EXECUTION_FAILED`
- `INTERNAL_ERROR`

---

## OpenAPI & Dynamic Interface Generation

- The FastAPI app will expose an OpenAPI schema at `/openapi.json` and interactive docs at `/docs`.
- **Dynamic Task Interfaces**: Each task's OpenAPI specification is stored in the database and loaded dynamically.
- **Frontend Integration**: Frontend automatically generates forms and interfaces based on task OpenAPI specifications.
- Keep Pydantic models in `presentation` layer for core API contracts, while task-specific schemas are loaded dynamically.
