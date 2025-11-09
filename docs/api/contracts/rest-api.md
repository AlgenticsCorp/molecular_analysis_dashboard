# API Contract (Comprehensive Molecular Analysis Platform)

This document defines the REST API surface for the **Molecular Analysis Dashboard**, a comprehensive computational biology platform with **5 integrated molecular analysis services** through NeuroSnap cloud APIs.

## 🧬 **Platform Overview**
- **Structure Folding**: IntelliFold & Boltz-2 (AlphaFold3) protein structure prediction
- **Molecular Dynamics**: AMBER relaxation and optimization
- **Molecular Docking**: GNINA neural network-guided binding analysis
- **Task Execution Framework**: Generic computational workflow interface
- **Unified Management**: Centralized job tracking and results retrieval

Notes:
- All endpoints return JSON unless serving files.
- Authentication: Bearer JWT, except for `/health`, `/ready`, and auth endpoints.
- Multi-tenancy: All authenticated requests include `org_id` in JWT; server enforces org scoping.
- **Multi-Service Integration**: All services integrate with NeuroSnap cloud APIs for computational execution.
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
  - 200: 
    ```json
    {
      "status": "ready",
      "checks": {
        "task_execution_api": "ready",
        "docking_api": "ready",
        "folding_api": "ready",
        "molecular_dynamics_api": "ready",
        "neurosnap_unified_api": "ready",
        "database": "ok",
        "cache": "ok"
      }
    }
    ```
  - 503: `{ "status": "not_ready", "checks": { ... } }`
  - Purpose: Readiness probe (DB + cache + all molecular analysis services connectivity).

---

## 🚀 **Task Execution Framework**

- GET `/api/v1/tasks`
  - Auth: Bearer; Roles: `standard`+
  - Query Params: None
  - 200:
    ```json
    {
      "tasks": [
        {
          "task_id": "gnina-molecular-docking",
          "name": "GNINA Molecular Docking",
          "description": "Neural network-guided molecular docking via NeuroSnap API",
          "category": "molecular_docking",
          "engine": "gnina",
          "provider": "neurosnap",
          "status": "available",
          "parameters": {
            "receptor": {"type": "molecular_structure", "required": true},
            "ligand": {"type": "molecular_structure_or_drug_name", "required": true},
            "binding_site": {"type": "binding_site_coordinates", "required": false}
          }
        }
      ],
      "total_count": 1
    }
    ```
  - Purpose: List available molecular analysis tasks

- POST `/api/v1/tasks/{task_id}/execute`
  - Auth: Bearer; Roles: `standard`+
  - Path: `task_id` (string) - Task identifier (e.g., "gnina-molecular-docking")
  - Body:
    ```json
    {
      "receptor": {
        "name": "EGFR Kinase Domain",
        "format": "pdb",
        "data": "HEADER    TRANSFERASE..."
      },
      "ligand": "osimertinib",
      "binding_site": {
        "center_x": 25.5, "center_y": 10.2, "center_z": 15.8,
        "size_x": 20.0, "size_y": 20.0, "size_z": 20.0
      },
      "max_poses": 9,
      "energy_range": 3.0,
      "exhaustiveness": 8,
      "timeout_minutes": 30
    }
    ```
  - 200:
    ```json
    {
      "execution_id": "123e4567-e89b-12d3-a456-426614174000",
      "job_id": "gnina_12345",
      "status": "completed",
      "task_id": "gnina-molecular-docking",
      "results": {
        "poses": [
          {"rank": 1, "affinity": -8.2, "confidence_score": 0.85}
        ],
        "best_pose": {"rank": 1, "affinity": -8.2, "confidence_score": 0.85}
      }
    }
    ```
  - Purpose: Execute molecular analysis tasks with standardized interface

---

## 🧬 **Structure Folding Services (IntelliFold & Boltz-2)**

- POST `/api/v1/folding/submit`
  - Auth: Bearer; Roles: `standard`+
  - Body:
    ```json
    {
      "job_name": "Protein Structure Prediction",
      "sequences": [
        {
          "name": "protein1",
          "type": "aa",
          "sequence": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAV..."
        }
      ],
      "molecules": [
        {
          "name": "ligand1",
          "type": "sdf",
          "data": "\n  Mrv2014 11090825392D\n\n  6  6  0  0  0  0..."
        }
      ],
      "msa_mode": "mmseqs2_uniref_env",
      "number_recycles": 3,
      "sampling_steps": 200,
      "diffusion_samples": 5,
      "note": "Structure prediction with small molecule"
    }
    ```
  - File Upload: `msa_file` (optional), `molecule_files[]` (optional)
  - 200:
    ```json
    {
      "job_id": "intellifold_20231109_143022",
      "status": "pending",
      "message": "Structure folding job submitted to NeuroSnap IntelliFold",
      "job_name": "Protein Structure Prediction",
      "sequences_count": 1,
      "molecules_count": 1,
      "estimated_runtime": "30-60 minutes"
    }
    ```
  - Purpose: Submit protein structure folding jobs to IntelliFold (AlphaFold3)

- POST `/api/v1/folding/submit-boltz2`
  - Auth: Bearer; Roles: `standard`+
  - Body: Form data with JSON `folding_request` + optional file uploads
  - Additional Parameters:
    - `cyclic_biopolymers` (optional): Cyclic structure specifications
    - `use_inference_time_potentials` (boolean): Advanced potential functions
    - `molecular_weight_correction` (boolean): MW-based corrections
    - `sampling_steps_affinity` (int): Affinity sampling steps (default: 200)
  - 200: Same format as IntelliFold response
  - Purpose: Submit advanced protein folding jobs to Boltz-2 with enhanced parameters

- POST `/api/v1/folding/submit-simple`
  - Auth: Bearer; Roles: `standard`+
  - Body:
    ```json
    [
      {
        "name": "protein1",
        "type": "aa",
        "sequence": "MKTAYIAKQRQISFV..."
      }
    ]
    ```
  - 200: Same format as IntelliFold response
  - Purpose: Simple protein folding with sequences only

---

## ⚗️ **Molecular Dynamics Services (AMBER)**

- POST `/api/v1/molecular-dynamics/amber-relaxation/submit`
  - Auth: Bearer; Roles: `standard`+
  - Body: Form data
    - `structure_file` (required): PDB/PDBQT protein structure file
    - `max_iterations` (optional): Maximum optimization iterations (100-10000, default: 2500)
    - `tolerance` (optional): Energy convergence tolerance (0.1-10.0, default: 1.0)
    - `job_name` (optional): Human-readable job name
    - `note` (optional): Job description
  - 200:
    ```json
    {
      "job_id": "amber_20231109_143045",
      "status": "pending",
      "message": "AMBER relaxation job submitted to NeuroSnap",
      "job_name": "AMBER Relaxation",
      "max_iterations": 2500,
      "tolerance": 1.0,
      "estimated_runtime": "15-45 minutes"
    }
    ```
  - Purpose: Submit molecular dynamics relaxation jobs using AMBER force fields

- POST `/api/v1/molecular-dynamics/amber-relaxation/submit-simple`
  - Auth: Bearer; Roles: `standard`+
  - Body: Form data with `structure_file` and `job_name` only
  - 200: Same format as full AMBER response
  - Purpose: Simple AMBER relaxation with default parameters

---

## 🔬 **Molecular Docking Services (GNINA)**

- POST `/api/v1/docking/submit`
  - Auth: Bearer; Roles: `standard`+
  - Body: Form data or JSON
    - `receptor_file` or `receptor`: Protein structure (PDB format)
    - `ligand_file` or `ligand`: Ligand structure (SDF) or drug name
    - `binding_site` (optional): Binding site coordinates
    - `job_name`: Human-readable job identifier
  - 200:
    ```json
    {
      "job_id": "gnina_20231109_143067",
      "status": "pending",
      "message": "Molecular docking job submitted",
      "receptor_name": "EGFR",
      "ligand_name": "osimertinib",
      "estimated_runtime": "10-30 minutes"
    }
    ```
  - Purpose: Submit molecular docking analysis using GNINA engine

---

## 🌐 **Unified NeuroSnap Job Management**

- GET `/api/v1/neurosnap/status/{job_id}`
  - Auth: Bearer; Roles: `standard`+
  - Path: `job_id` (string) - NeuroSnap job identifier
  - 200:
    ```json
    {
      "job_id": "gnina_12345",
      "status": "completed",
      "progress_percentage": 100,
      "current_step": "Analysis complete",
      "estimated_completion": null,
      "runtime_seconds": 1247
    }
    ```
  - Purpose: Universal status checking for all NeuroSnap computational jobs

- GET `/api/v1/neurosnap/results/{job_id}`
  - Auth: Bearer; Roles: `standard`+
  - Path: `job_id` (string) - NeuroSnap job identifier
  - 200:
    ```json
    {
      "job_id": "gnina_12345",
      "status": "completed",
      "files": [
        "output.csv",
        "output.sdf",
        "binding_poses.pdb"
      ],
      "download_urls": {
        "output.csv": "/api/v1/neurosnap/download/gnina_12345/output.csv",
        "output.sdf": "/api/v1/neurosnap/download/gnina_12345/output.sdf"
      }
    }
    ```
  - Purpose: Universal results retrieval for all computational services

- GET `/api/v1/neurosnap/download/{job_id}/{filename}`
  - Auth: Bearer; Roles: `standard`+
  - Path: `job_id` (string), `filename` (string)
  - 200: Binary file content with appropriate Content-Type headers
  - Purpose: Universal file download for all analysis results
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
