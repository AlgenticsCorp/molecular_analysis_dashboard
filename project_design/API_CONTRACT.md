# API Contract (Initial)

This document defines the initial REST API surface planned for the Molecular Analysis Dashboard. It focuses on core endpoints for health/readiness, authentication, molecule uploads, and job lifecycle.

Notes:
- All endpoints return JSON unless serving files.
- Authentication: Bearer JWT, except for `/health`, `/ready`, and auth endpoints.
- Multi-tenancy: All authenticated requests include `org_id` in JWT; server enforces org scoping.
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
  - 200: `{ "status": "ready" , "checks": { "db": "ok", "broker": "ok" } }`
  - 503: `{ "status": "not_ready", "checks": { ... } }`
  - Purpose: Readiness probe (DB + broker connectivity).

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

## Error Codes (Indicative)

- `AUTH_INVALID_CREDENTIALS`
- `AUTH_UNAUTHORIZED`
- `ORG_FORBIDDEN`
- `PIPELINE_NOT_FOUND`
- `VALIDATION_FAILED`
- `JOB_NOT_FOUND`
- `ARTIFACT_NOT_FOUND`
- `INTERNAL_ERROR`

---

## OpenAPI

- The FastAPI app will expose an OpenAPI schema at `/openapi.json` and interactive docs at `/docs`.
- Keep Pydantic models in `presentation` layer for request/response contracts.
