# Operations Runbook (Local & Prod-Ready Notes)

Purpose: Give developers and operators the essentials to run, check, scale, and troubleshoot the system.

---

## Bring-up (Local Compose)

```bash
cp .env.example .env
# Build images
docker compose build
# Start infra
docker compose up -d postgres redis
# Run DB migrations
docker compose run --rm migrate
# Start API and workers
docker compose up -d api worker
# Health checks
curl -f http://localhost:8000/health
```

## Health & Readiness
- Liveness: `GET /health` (API process up)
- Readiness: `GET /ready` (checks DB + broker): returns `ready/not_ready` and components
- Logs: `docker compose logs -f api worker`

## Scaling
```bash
docker compose up -d --scale api=2 --scale worker=3
```
- Tune with env vars: `WEB_CONCURRENCY`, `CELERY_WORKER_CONCURRENCY`, `CELERY_PREFETCH_MULTIPLIER=1`, `CELERY_ACKS_LATE=true`

## Backups (Indicative)
- Metadata DB: daily backups / PITR if managed service
- Results DBs (per org): per-tenant retention policies
- Storage: lifecycle policies (S3) or snapshot volumes (local dev)

## Secrets & Rotations
- Never commit secrets. Provide via `.env` (dev) or secret manager (prod).
- Rotate `SECRET_KEY` and DB creds; restart API/worker.

## Common Issues
- API not ready: check Postgres/Redis health, `DATABASE_URL`, broker URLs.
- Worker not consuming: verify broker URL, queue names/routes, and Celery logs.
- File permissions: ensure volumes are writable by non-root `appuser`.

## Migrations
- Apply: `docker compose run --rm migrate`
- If Alembic errors: check revision history; resolve conflicts; re-run

## Observability (optional)
- Metrics: expose `/metrics` if enabled; scrape with Prometheus
- Tracing: OpenTelemetry instrumentation for API and Celery

## Disaster Recovery Drills (recommended)
- Restore a backup to a staging environment
- Verify job submission and result retrieval

References
- Deployment: `DEPLOYMENT_DOCKER.md`
- Component Map: `REPO_COMPONENT_MAP.md`
- Configuration: `CONFIGURATION.md`
- Security: `SECURITY_ARCH.md`
