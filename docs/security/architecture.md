# Security Architecture

This document summarizes the key security controls, assumptions, and patterns for the Molecular Analysis Dashboard.

Threat Model (high level)
- Actors: Users (Standard/Admin), Root, Service Accounts; API; Workers; External services (Postgres, Redis, Object Storage).
- Assets: Credentials/secrets, job results, molecular artifacts, user accounts, audit logs.
- Risks: Cross-tenant data exposure; credential leakage; improper authorization; tampering with artifacts; weak transport security.

---

AuthN/AuthZ
- Authentication: JWT (access & refresh). Signed with `SECRET_KEY` (dev) or external KMS/HSM (prod).
- Claims: `sub`, `org_id`, `roles`, optional `scopes`, `iat`, `exp`, `aud`, `iss`.
- Authorization: RBAC at API boundary; org isolation enforced in repositories (every query filters by `org_id`).
- Token Rotation: Short-lived access tokens; refresh tokens with rotation and revocation list (DB-backed or cache-backed).

Transport & Storage Security
- TLS termination at reverse proxy/LB in production.
- Postgres connections use TLS where available; credentials not baked into images.
- Secrets (DB, JWT, S3) provided via environment or secret manager (K8s Secrets/ASM/Vault); never in VCS.
- Artifacts stored with per-org prefixes/buckets; server-side encryption when using S3/MinIO.

Multi-Tenancy Isolation
- JWT `org_id` claim maps to tenant context.
- Repository layer enforces `org_id` on all CRUD.
- Storage adapter prefixes paths with `org_id/` or uses per-org buckets.
- Optional: database-level RLS policies when feasible.

Workers & Task Queue
- Use `acks_late=true` and `prefetch=1` for fair scheduling and resilience to worker restarts.
- Idempotent task design: task retries won’t duplicate side effects (check existing artifacts/DB state).
- Limit command execution scope in engine adapters (sanitize inputs, restrict paths).

Auditing & Observability
- Log security events: logins, role changes, org provisioning, job lifecycle.
- Include `org_id`, `user_id`, `job_id`, and timestamps.
- Consider metrics for auth failures, queue depths, and job error rates.

Operational Guidance
- Rotate `SECRET_KEY` and database credentials regularly; automate via secret manager.
- Keep base images patched; rebuild regularly.
- Implement backup/restore tests for DBs and storage.

References
- Users & Roles: `USERS_AND_ROLES.md`
- Databases & Tenancy: `DATABASES.md`
- API Contract: `API_CONTRACT.md`
