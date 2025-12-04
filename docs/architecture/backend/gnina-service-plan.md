# In-House GNINA Service Integration Plan

This document outlines the end-to-end plan for delivering an internal GNINA-based docking service. It covers
architectural context, deployment requirements, API integration, and dashboard wiring so future services can
follow the same approach.

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

- Python (FastAPI) service exposing `/health`, `/info`, and `/dock` endpoints.
- `/dock` accepts receptor & ligand files plus optional parameters; returns job ID + polling URL.
- Service writes output to shared volume or object storage (MinIO/S3-compatible) and reports metadata.
- Configurable via env vars: `GNINA_EXEC_PATH`, GPU toggle, queue depth, storage credentials.

### Docker Artifacts

- `docker/Dockerfile.gnina-service`: builds GNINA binary + FastAPI service.
- `docker-compose.yml` additions: new `gnina-service` service with volume mounts, optional GPU device requests.
- `.env.example` keys: `GNINA_SERVICE_URL`, `GNINA_SERVICE_API_KEY`, storage credentials for remote deployments.

### Deployment Modes

1. **Local Development**: Compose stack runs GNINA service alongside API; API points to `http://gnina-service:8080`.
2. **Remote Deployment**: GNINA service runs in separate environment; API gateway routes to external URL set via env vars.
3. **Hybrid**: multiple GNINA instances registered; future load balancing handled by gateway rules.

## 4. Backend Integration

### Task Configuration

- Add `config/tasks/gnina-local-docking.json` describing parameters, validation (PDBQT, SDF, etc.), and metadata.
- Extend `TaskRegistry` to load the GNINA adapter and expose via `/api/v1/tasks-unified/available`.

### Adapter Implementation

- Create `GninaLocalAdapter` (in `adapters/providers`):
  - Validates receptor/ligand extensions.
  - Calls GNINA API with multipart form data.
  - Parses job ID and registers for polling.
- Reuse `_download_output_files` with new mapping for GNINA’s output names (poses, log).

### Execution Flow

1. Upload receptor/ligand via dashboard or Swagger.
2. Submit task with `task_id = gnina-local-docking`.
3. Adapter stores files, POSTs to GNINA service.
4. Celery polls `/status/{job_id}` on GNINA API, updates execution status.
5. When completed, fetch result metadata and store output files.

### Configuration

- Introduce `GNINA_SERVICE_URL`, `GNINA_SERVICE_API_KEY`, `GNINA_DEFAULT_TIMEOUT` env vars.
- Update `settings.py` to load GNINA config and expose to adapter/service.

## 5. API & Swagger

- Auto-registered in Swagger via unified task endpoints.
- Provide example request/response in `docs/api/examples/gnina-docking.http`.
- Optionally add dedicated `/api/v1/gnina/health` endpoint for operational checks.

## 6. Frontend & Dashboard

- Add GNINA task card with icon and description in task library.
- Ensure task form renderer respects spec (file inputs, numeric fields, optional JSON parameters).
- Update execution result UI to display GNINA-specific metadata (e.g., binding affinity, log file link).
- Add filter option to view only in-house services.

## 7. Monitoring & Observability

- Expose Prometheus metrics (`/metrics`) from GNINA service: job durations, failures, queue depth.
- Integrate with structured logging (correlation IDs, execution_id).
- Add health check entry to dashboard status page.
- Document log shipping or remote monitoring options.

## 8. Testing Strategy

### Unit Tests

- Validate adapter payload construction and error handling.
- Ensure task registry loads GNINA config and enforces file validation.

### Integration Tests

- Use HTTPX mock server to emulate GNINA service.
- Test full submit → poll → download workflow storing output files.

### End-to-End

- Compose scenario running GNINA container; execute sample docking; verify dashboard displays results.

## 9. Rollout Plan

1. Implement adapter + config + tests; merge behind feature flag (`GNINA_SERVICE_ENABLED`).
2. Build GNINA service image, run locally via compose.
3. Update documentation (`docs/integration/provider-examples/gnina.md`).
4. Deploy to staging environment with remote GNINA service; perform smoke tests.
5. Enable dashboard feature flag for GNINA tasks; monitor usage.
6. Collect feedback, iterate on performance/UX.

## 10. Future Enhancements

- GPU scheduling integration (Kubernetes device plugins).
- Auto-scaling GNINA service based on queue depth.
- Multi-tenancy isolation for GNINA workloads (dedicated storage buckets).
- Advanced analytics: scoring distributions, heatmaps.

---

_Revision history: initial draft, December 4, 2025._
