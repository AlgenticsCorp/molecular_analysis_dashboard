# In-House GNINA Service Integration Plan

This document captures the end-to-end plan for the internal GNINA-based docking service **and** documents the
implementation that shipped on December 4, 2025. It now acts as the integration playbook for any future
in-house computational services: architectural context, deployment requirements, API wiring, verification
checklist, and lessons learned are all consolidated here.

> **Status snapshot – 2025-12-04**
>
> - GNINA microservice (FastAPI) is live in local Compose with `/healthz`, `/info`, and job lifecycle routes under
>   `/api/v1/gnina/*`.
> - Dashboard backend exposes the task through `GninaServiceAdapter`, and Celery workers can poll/collect results.
> - Frontend uses the unified task form to submit GNINA jobs; documentation and tests cover submit/poll/download.
> - The remaining roadmap items focus on observability, GPU enablement, and production deployment patterns.

## 1. Objectives & Scope

- Provide a self-hosted docking service powered by GNINA packaged as a separate container.
- Allow remote deployments (on-prem or cloud) with secure API access from the Molecular Analysis Dashboard.
- Integrate the service into Swagger, backend task framework, and frontend dashboard.
- Establish reusable patterns so future home-grown services can use the same integration path.

### Out of Scope

- Replacing existing NeuroSnap integrations (they remain available).
- Implementing GPU scheduling or autoscaling (documented as future enhancements).
- Delivering production infrastructure (Helm charts, Terraform) beyond the docker-compose templates described.

## 2. Architecture Alignment

- Fits within Ports & Adapters design: the GNINA executor becomes another provider adapter.
- App Layer updates: `TaskExecutionService` dispatches to `GninaLocalAdapter` when configured.
- Infrastructure updates: new container image registered behind the API gateway with health checks.
- Database: reuse `TaskFrameworkExecution` records (no new tables) but store provider metadata (e.g., `engine_version`).
- Celery Worker: reuses existing polling/refresh mechanism, optionally adds GNINA-specific tasks for long jobs.

## 3. Service Design

### Containerized API

- Python (FastAPI) service exposing:
  - `GET /healthz` – liveness probe used by Compose/Kubernetes.
  - `GET /info` – returns build metadata (GNINA version, storage root, simulated runtime when in demo mode).
  - `POST /api/v1/gnina/jobs` – accepts receptor & ligand uploads plus form parameters (e.g., `exhaustiveness`).
    Advanced GNINA CLI flags can be tunneled via `advanced_parameters` (JSON object) which is stored with the job and
    forwarded by the adapter when the real CLI integration is enabled.
  - `GET /api/v1/gnina/jobs/{job_id}` – polling endpoint for status/progress messages.
  - `GET /api/v1/gnina/jobs/{job_id}/results` – final binding affinity + pose metadata.
  - `GET /api/v1/gnina/jobs/{job_id}/files/{filename}` – download persisted artifacts (docked pose, log, etc.).
- Service writes output to a dedicated storage directory (default `/storage`). The path is configurable and
  mounted via Docker volume so API + worker can share artifacts.
- Configurable via environment variables:
  - `GNINA_SERVICE_STORAGE_DIR` (defaults to `/storage`)
  - `GNINA_SIMULATED_RUNTIME_SECONDS` & `GNINA_SIMULATED_PROGRESS_INTERVAL` (demo defaults; replace when wiring
    real GNINA binary)
  - `GNINA_SERVICE_PORT` (Compose published port)
  - `LOG_LEVEL`

### Docker Artifacts

- `docker/Dockerfile.gnina` builds the FastAPI service (currently using a simulated GNINA loop while GPU support
  is validated). The file installs the project in editable mode, creates a non-root user, and runs Uvicorn.
- `docker-compose.yml` defines the `gnina-service` container with health checks, exposed port `8080` (published as
  `${GNINA_SERVICE_PORT:-8085}`), and a dedicated `gnina_storage` volume. The API and worker mount the shared
  storage volume via `/storage/results` and `/storage/uploads` for cross-service file access.
- `.env.example` includes the keys required by the backend to call the service: `GNINA_SERVICE_URL`,
  `GNINA_SERVICE_API_KEY`, and tunables for simulated runtime. Future GPU integration will extend this list with
  CUDA device configuration.

### Deployment Modes

1. **Local Development** (current): Compose stack runs GNINA service alongside API. `GNINA_SERVICE_URL` defaults to
  `http://gnina-service:8080/api/v1/gnina` inside the network, and to `http://localhost:8085/api/v1/gnina` for
  host-based curl tests.
2. **Remote Deployment** (beta): Run GNINA service on a separate host/cluster; set `GNINA_SERVICE_URL` to the remote
  base URL. Ensure network ACLs and API key enforcement (once enabled) are in place.
3. **Hybrid / Multi-instance** (future): Multiple GNINA services registered in Consul or the API gateway, with
  routing logic to pick a target based on queue depth or available GPU resources.

## 4. Backend Integration

### Task Configuration

- `config/tasks/gnina-molecular-docking.json` registers the task, parameter schema, and adapter reference. The
  provider is set to `internal`, enabling the dashboard UI to tag it as a first-party service.
- `TaskRegistry` loads the config at startup, exposing metadata through `/api/v1/tasks-unified/available` and
  ensuring validation (file presence, allowed extensions, numeric range checks) happens before job submission.

### Adapter Implementation

- `GninaServiceAdapter` (in `adapters/providers/gnina_service_adapter.py`) handles uploads, submits multipart
  form data to the microservice, and registers the returned job for polling.
- File validation enforces expected MIME types and non-empty payloads before hitting the service.
- Result handling maps the docked pose and metadata into the unified execution model so downstream systems (file
  service, result viewers) behave consistently with other providers.

### Storage Integration Pattern

- The unified task service now persists both input and output artifacts via `ExecutionFileService`, using the same
  abstraction that powers NeuroSnap downloads. This ensures GNINA jobs surface downloadable files under
  `/api/v1/tasks-unified/files/{file_id}/download` without bespoke wiring.
- Providers should return a `download_urls` mapping keyed by semantic parameter name; during completion the service
  dereferences each URL, streams the payload into the shared storage volume, and records hashes plus metadata in
  `execution_files`.
- Storage paths follow the convention `/uploads/{organization_id or 0000...}/{execution_id}/{filename}`, enabling
  multi-tenant isolation and reuse of retention policies. Future first-party services can plug in by delivering
  stable download endpoints and optional MIME type hints.
- When new services require cloud-backed storage, implement an adapter for `ExecutionFileService` instead of
  bypassing the abstraction so the dashboard UI gains downloads, previews, and audit logs for free.

### Execution Flow

1. User uploads receptor (`.pdbqt`/`.pdb`) and ligand (`.sdf`/`.pdbqt`) through the unified task API/UI.
2. Adapter persists raw files, then POSTs to `GNINA_SERVICE_URL + "/jobs"`.
3. GNINA service immediately enqueues work and responds with `{job_id, status, queued_at, parameters}`.
4. Celery worker runs `poll_gnina_job` (new task) which queries `/jobs/{job_id}` until status is terminal, updating
  dashboard execution state.
5. On success, worker fetches `/jobs/{job_id}/results` and `/jobs/{job_id}/files/*`; the unified task service streams
  artifacts into `/storage/uploads/...`, records file metadata (hashes, content type) via `ExecutionFileService`, and
  updates the execution record with binding affinity metrics so downstream consumers inherit consistent storage
  semantics.

### Configuration

- Introduce `GNINA_SERVICE_URL`, `GNINA_SERVICE_API_KEY`, `GNINA_DEFAULT_TIMEOUT` env vars.
- Update `settings.py` to load GNINA config and expose to adapter/service.

## 5. API & Swagger

- GNINA task surfaces through the existing unified task endpoints, so Swagger auto-generates request/response
  models (`/api/v1/tasks-unified/execute`). Example payloads are in `docs/api/examples/gnina-docking.http`.
- Dedicated GNINA microservice routes (`/api/v1/gnina/jobs/*`) are documented in `docs/deployment/docker/setup.md`
  and linked from the API operations section for operators who need to run health checks outside the dashboard.
- The backend also exposes `GET /api/v1/gnina/proxy/health` (internal) which forwards to the service—useful for
  platform monitoring without exposing the service publicly.

## 6. Frontend & Dashboard

- GNINA card appears in the task library when `GNINA_SERVICE_ENABLED` flag is on.
- Task form reuses the file upload components; configured to require receptor + ligand and optional `exhaustiveness`.
- Execution detail view includes binding affinity and download buttons (pose + raw log). Future iteration will add
  inline pose visualization once 3D viewer component is ready.
- Dashboard filters now include “Internal Services” to quickly locate GNINA and similar in-house providers.

## 7. Monitoring & Observability

- GNINA service emits structured logs (JSON) including `job_id`, `execution_id`, and timing details. Ensure log
  forwarders include the service in their allowlists.
- Flower dashboard (`http://localhost:5555`) shows Celery tasks polling GNINA jobs; it is the quickest way to
  inspect queue health locally.
- Health endpoints: `docker compose ps` highlights container health state; `curl http://localhost:8085/healthz`
  verifies service reachability from host.
- Future work: add Prometheus `/metrics` endpoint and integrate with Grafana dashboards; add OpenTelemetry spans
  linking dashboard requests to GNINA job executions.

## 8. Testing Strategy

### Unit Tests

- Adapter tests cover payload construction, validation errors (empty files, missing params), and job submission
  response parsing.
- `tests/unit/gnina_service/test_job_manager.py` ensures the microservice manager handles lifecycle transitions.
- `tests/unit/gnina_service/test_routes.py` runs against the FastAPI router using `httpx.ASGITransport` to verify
  submission, polling, and artifact download routes.

### Integration Tests

- HTTPX mocking (planned) will let us simulate slow/success/failure cases without spinning up the container.
- Backend integration tests (future) should assert Celery polling logic stores results correctly in storage service.

### End-to-End

- Local Compose validation: `docker compose up gnina-service api worker gateway frontend` then submit a docking job
  through the UI or via `curl`. Sample command using repository fixtures:

  ```bash
  curl -f -X POST http://localhost:8085/api/v1/gnina/jobs \
    -F "receptor_file=@EGFR_KD_L858R_T790M_model_1.pdb;type=chemical/x-pdb" \
    -F "ligand_file=@erlotinib.sdf;type=chemical/x-mdl-sdfile" \
    -F exhaustiveness=4 \
    -F job_name="local-cli-test"
  ```

- Monitor progress with:

  ```bash
  watch -n 2 "curl -s http://localhost:8085/api/v1/gnina/jobs/<job_id> | jq '.status,.message'"
  ```

- Retrieve results once `status == "succeeded"`:

  ```bash
  curl -f http://localhost:8085/api/v1/gnina/jobs/<job_id>/results | jq
  curl -f http://localhost:8085/api/v1/gnina/jobs/<job_id>/files/docked_pose.pdbqt -o docked_pose.pdbqt
  ```

## 9. Rollout Plan

1. ✅ Implement microservice, adapter, task config, and unit tests behind `GNINA_SERVICE_ENABLED` flag.
2. ✅ Build GNINA service image and include it in local Compose; verify job submission using repository sample files.
3. 🔃 Update remaining documentation touchpoints (`docs/integration/provider-examples/gnina.md`, frontend playbook)
  to reference the shipping endpoints.
4. 🔜 Deploy to staging with remote GNINA instance; configure gateway routing and API key enforcement.
5. 🔜 Flip feature flag for select users, monitor Celery/Flower metrics, and gather UX feedback.
6. 🔜 Iterate on GPU support, observability, and dashboard visualization enhancements before general availability.

## 10. Future Enhancements

- GPU scheduling integration (Kubernetes device plugins).
- Auto-scaling GNINA service based on queue depth.
- Multi-tenancy isolation for GNINA workloads (dedicated storage buckets).
- Advanced analytics: scoring distributions, heatmaps.

---

_Revision history_: original plan (2025-12-04 AM); implementation details + instructions updated (2025-12-04 PM).
