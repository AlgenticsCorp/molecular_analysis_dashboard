# Deployment Plan (Cloud)

This guide outlines a pragmatic path to deploy each stage to a cloud environment. Choose your stack (VMs with Docker or Kubernetes). Examples assume:
- Container Registry available (e.g., GHCR, ECR, GCR)
- Managed Postgres (e.g., RDS, Cloud SQL)
- Managed Redis (e.g., ElastiCache, Memorystore) or self-hosted
- Object Storage (e.g., S3, GCS, MinIO)
- Optional Logs backend (e.g., Loki, OpenSearch)

---

## Global Prereqs
- Create secrets: `JWT_SECRET`, DB URL(s), Redis URL, object storage credentials.
- Configure networking and security groups/firewalls.
- Set up Container Registry and CI to push images per stage.

## Stage 0: API Health on a VM
- Build and push image `api:stage0`.
- Provision a VM; install Docker; run:
```bash
docker run -d --name api -p 80:8000 \
  -e LOG_LEVEL=info \
  ghcr.io/yourorg/mad-api:stage0
curl -f http://<vm-ip>/health
```

## Stage 1: Metadata DB + Migrations
- Provision Managed Postgres and create DB.
- Store `DATABASE_URL` in a secret store (e.g., SSM/Secrets Manager).
- Run migrations job once:
  - VM: `docker run --rm -e DATABASE_URL=... ghcr.io/.../migrate:stage1`
  - K8s: `kubectl apply -f k8s/job-migrate.yaml`
- Deploy API with env `DATABASE_URL` and health probes.

## Stage 2: Storage Adapter
- Create S3/GCS bucket and IAM policy with least privilege.
- Set env: `STORAGE_BACKEND=s3`, `S3_BUCKET=...`, `AWS_*` credentials.
- Re-deploy API.

## Stage 3: Results DB + Jobs Meta
- If using per-org DBs, provision template and automate schema creation.
- Add `RESULTS_DATABASE_URL` (or DSN per org) and rotate secrets.
- Re-run migrations if needed.

## Stage 4: Async Pipeline
- Provision Redis. Set `REDIS_URL` env.
- Deploy Worker with same image tag as API; add queues via config.
- Add probes: liveness (process running), readiness (Redis reachable).

## Stage 5: Docking Engine(s)
- Ensure the worker base image contains the chosen engine(s) (e.g., Vina/Smina/Gnina) and RDKit with CPU libs.
- Grant Worker access to object storage.
- Run an end-to-end job; verify artifacts and results URIs resolve.

## Stage 6: Cache & Confidence
- Ensure `RESULT_CACHE_TTL` env configured; add index migrations applied.
- Validate cache hits through logs and API responses.

## Stage 7: Logs & Events
- Stand up Loki/OpenSearch or use vendor logging.
- Configure API to emit structured logs; expose `/jobs/{id}/logs` to return signed URLs or redirects.

## Stage 8: External Auth
- Configure IdP (Azure AD/Google): client ID/secret, redirect URIs.
- Map identities to local users/roles; test RBAC on endpoints.

## Stage 9: Hardening
- Enable metrics/tracing (OTLP endpoint), WAF, rate limits.
- Backups for Postgres and object storage lifecycle policies.
- Blue/green rollout with health checks.

Kubernetes Notes
- Use `Deployment` for API/Worker, `Job` for migrations.
- Add `PodDisruptionBudget`, `HPA` on CPU and queue depth.
- Configure `Ingress` + TLS; set proper `readinessProbe` and `livenessProbe`.

Observability Checklist
- Metrics: request rate/latency, queue depth, worker success/failure.
- Tracing: job lifecycle spans across API and worker.
- Logs: structured JSON, correlation IDs.
