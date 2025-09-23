# Deployment Plan (Local - Docker Compose)

This guide provides per-stage steps to run the system locally using Docker Compose. Ensure you have Docker Desktop installed.

Prereqs
- Copy `.env.example` to `.env` and adjust values as needed.

---

## Stage 0: Bootstrap API Health
- Build and run API only:
```bash
docker compose build api
docker compose up -d api
curl -f http://localhost:8000/health
```

## Stage 1: Metadata DB + Alembic Baseline
- Start Postgres:
```bash
docker compose up -d postgres
```
- Run migrations:
```bash
docker compose run --rm migrate
```
- Start API and check readiness:
```bash
docker compose up -d api
curl -f http://localhost:8000/ready
```

## Stage 2: Molecules & Artifacts + Storage Adapter
- Ensure storage volumes exist (Compose sets up `uploads` and `results`).
- Start services:
```bash
docker compose up -d postgres api
```
- Test upload:
```bash
# Example using HTTPie
http -f POST :8000/api/v1/molecules/upload \
  Authorization:"Bearer $TOKEN" \
  name=ligand_1 format=pdbqt file@path/to/ligand.pdbqt
```

## Stage 3: Results DB + Jobs Meta
- Start infra:
```bash
docker compose up -d postgres
```
- Run metadata migrations if updated:
```bash
docker compose run --rm migrate
```
- Start API:
```bash
docker compose up -d api
```
- Create job and poll status:
```bash
http POST :8000/api/v1/pipelines/<id>/jobs Authorization:"Bearer $TOKEN" \
  pipeline_version=1.0.0 inputs:='{"ligand_uri":"...","protein_uri":"..."}'
http :8000/api/v1/jobs/<job_id>/status Authorization:"Bearer $TOKEN"
```

## Stage 4: Async Pipeline (Worker, No Engine)
- Start Redis and Worker:
```bash
docker compose up -d redis worker
```
- Submit job and watch status:
```bash
http POST :8000/api/v1/pipelines/<id>/jobs Authorization:"Bearer $TOKEN"
docker compose logs -f worker
```

## Stage 5: Docking Engine(s)
- Ensure the selected engine binary/runtime is available in the worker image (e.g., Vina/Smina/Gnina). See `Dockerfile.worker` notes.
- Start full stack:
```bash
docker compose up -d postgres redis api worker
```
- Run job and fetch results:
```bash
http POST :8000/api/v1/pipelines/<id>/jobs Authorization:"Bearer $TOKEN" \
  pipeline_version=1.0.0 inputs:='{"ligand_uri":"...","protein_uri":"..."}'
http :8000/api/v1/jobs/<job_id>/results Authorization:"Bearer $TOKEN"
```

## Stage 6: Caching & Confidence
- Submit same inputs twice; expect cache hit on second submission.

## Stage 7: Logs & Events
- Fetch events and logs URL:
```bash
http :8000/api/v1/jobs/<job_id>/events Authorization:"Bearer $TOKEN"
http :8000/api/v1/jobs/<job_id>/logs Authorization:"Bearer $TOKEN"
```

## Stage 8: External Auth
- Configure IdP settings in DB or env; restart API.

## Stage 9: Hardening
- Enable metrics/tracing; confirm via `/metrics` if implemented.

Notes
- Use `docker compose logs -f <service>` for troubleshooting.
- Use `docker compose down -v` to reset local volumes.
