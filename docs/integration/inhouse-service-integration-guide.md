# In-House Service Integration Guide

This guide distills the GNINA docking rollout into a reusable playbook for shipping additional in-house
computational services. Follow these steps end to end to containerize your service, expose a dedicated task API,
wire it through the unified task framework, persist artifacts with the storage service, and surface it in the
frontend task library.

---

## 1. Define Service Contract & Dependencies

- Document the job lifecycle: submission payload, status polling response, result fields, and downloadable assets.
- Capture compute requirements (CPU, RAM, GPU) and any external binaries the container must install.
- Decide whether jobs are short-lived HTTP requests or long-running background tasks that require polling.

## 2. Dockerize the Service

1. Create `docker/Dockerfile.<service>` that installs dependencies, copies source, and launches your API server.
   - Run as a non-root user.
   - Expose a configurable port via `ENV SERVICE_PORT=8080` and `CMD uvicorn ... --port ${SERVICE_PORT}` (or similar).
2. Add a Compose profile entry in `docker-compose.yml`:
   - Define container name, build context, shared volumes (e.g., `/storage`), health check, and environment vars.
   - Reuse the `gnina_storage` style pattern: a dedicated volume for outputs plus shared mounts for API/worker access.
3. Extend `.env.example` with service-specific variables: `SERVICE_URL`, optional API key, simulated runtime toggles.
4. Update `docs/deployment/docker/setup.md` with bring-up instructions so developers can run `docker compose up <service>`.

## 3. Expose a Service API

Implement a FastAPI (or compatible) surface with the following routes:

- `GET /healthz` and `GET /info` for health monitoring and metadata.
- `POST /api/v1/<service>/jobs` to accept uploads/parameters and return `{job_id, status, parameters}`.
- `GET /api/v1/<service>/jobs/{job_id}` for status polling (include progress, message, timestamps).
- `GET /api/v1/<service>/jobs/{job_id}/results` containing final scores/metrics and a `download_urls` object.
- `GET /api/v1/<service>/jobs/{job_id}/files/{filename}` streaming stored artifacts (pose, log, etc.).

Ensure the service writes to the shared storage mount (default `/storage`) using predictable directory structure
(e.g., `/storage/jobs/<job_id>/`).

## 4. Register the Task Definition

1. Add a config file under `config/tasks/<service-task-id>.json`.
   - Define `id`, `name`, `description`, `parameters`, allowed extensions, and default values.
   - Set `provider` to `internal` so the dashboard tags it as a first-party service.
2. Update `TaskRegistry` if new validation helpers are required for custom parameter types.
3. Confirm the new task appears via `GET /api/v1/tasks-unified/`.

## 5. Implement the Provider Adapter

1. Create `src/molecular_analysis_dashboard/adapters/providers/<service>_adapter.py`.
   - Validate incoming files and scalar parameters.
   - POST multipart form data to `SERVICE_URL + "/jobs"` using `httpx`.
   - Record `job_id` and provider metadata in the execution record.
2. Register the adapter within `TaskExecutionService` or the provider registry so the unified task service can
   instantiate it by task ID.
3. Add unit tests covering submission payload construction, error handling, and polling conversions.

## 6. Orchestrate Through Unified Task Service

- Ensure `UnifiedTaskService` knows how to:
  - Submit executions via the adapter.
  - Poll the provider for status (Celery task or async loop).
  - Normalize provider statuses to `queued/running/completed/failed` using the existing alias map.
  - Capture provider metadata (`binding_affinity`, `engine_version`, etc.) on completion.
- Reuse `_resolve_download_url` to handle absolute vs. relative provider URLs.

## 7. Persist Files with ExecutionFileService

1. During completion, iterate over provider `download_urls` and stream each asset into storage:
   - Use `ExecutionFileService.store_file_from_url(...)` (or equivalent helper) so hashes, content type, and
     storage path metadata are captured automatically.
   - Follow the shared layout `/uploads/{organization_id or 0000...}/{execution_id}/{filename}`.
2. Verify `GET /api/v1/tasks-unified/executions/{execution_id}/results` lists both `input_files` and `output_files`
   with populated `url` fields.
3. Confirm the download endpoint `/api/v1/tasks-unified/files/{file_id}/download` streams the artifact end-to-end.

## 8. API Gateway & Routing

- Add reverse-proxy entries (nginx/gateway) so `/api/v1/<service>/...` routes to the container internally.
- If the service should be accessible only via backend, keep the route private and rely on the adapter’s internal URL.
- Update `docs/architecture/backend/docking-engines.md` (or relevant architecture doc) with the new routing diagram.

## 9. Frontend Integration

1. Enable the task in the frontend task library by ensuring `TaskLibraryService` fetches the new task metadata.
2. Update `frontend/src/features/tasks/config.ts` (or relevant config) if manual whitelisting is required.
3. Build a task form schema reflecting the parameter definitions (file pickers, numeric inputs, toggles).
4. Update the execution detail page to display service-specific metrics (e.g., binding affinity) and download links.
5. Add documentation links/tooltips referencing the new service.

## 10. Verification Checklist

- [ ] `docker compose up <service> api worker` runs without errors; health checks pass.
- [ ] `curl -F ...` job submission returns `200` with a job ID.
- [ ] Polling transitions through `queued → running → completed`.
- [ ] `GET /executions/{id}/results` exposes metadata and files.
- [ ] Download endpoint returns byte-identical files (md5/sha256 stored in DB).
- [ ] Frontend task card submits jobs and displays results in QA build.
- [ ] Observability: logs include `job_id`, metrics exported if needed.

## 11. Roll Forward / Roll Back

- Feature flag each new service (`SERVICE_ENABLED`) so you can dark launch in staging.
- Maintain migration guide in `docs/architecture/backend/<service>-service-plan.md` capturing lessons learned.
- Rollback plan: disable the flag, remove task definition from registry, and stop the container.

---

_Revision history_: created December 4, 2025 based on GNINA integration lessons.
