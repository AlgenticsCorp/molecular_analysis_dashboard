# Task Queue Design (Celery)

Purpose: Document Celery routing, concurrency, retries, and idempotency expectations.

Queues & Routing (initial)
- Default queue: `docking` — CPU-bound docking tasks
- Routing key example: `tasks.docking.execute`
- Future: add `postprocess`, `notifications` queues if needed

Worker Settings
- `--concurrency=${CELERY_WORKER_CONCURRENCY:-2}` — tune per host CPU
- `--prefetch-multiplier=1` — fair scheduling, prevents long-running task starvation
- `acks_late=true` — acknowledge after processing to tolerate worker restarts

Retries & Backoff
- Use Celery retries (or Tenacity) with exponential backoff for transient errors (DB/network/object store)
- Max retries: 3–5 (tune by failure mode)
- Idempotency: Check for existing artifacts/DB rows before writing; use unique constraints where applicable

Serialization & Timeouts
- JSON serializer for tasks/results
- Soft/hard timeouts per task (e.g., soft=30m, hard=45m for docking)

Observability
- Use Flower (`:5555`) locally to monitor queues and tasks
- Log structured context: `job_id`, `org_id`, `pipeline_id`

Security Considerations
- Validate and sanitize any file paths/inputs used by engine adapters
- Avoid passing secrets in task args; read from environment/secret manager

References
- Framework design & sequence: `FRAMEWORK_DESIGN.md`
- API contract (job lifecycle): `API_CONTRACT.md`
