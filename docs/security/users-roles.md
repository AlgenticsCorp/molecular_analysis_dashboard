# Users and Roles

This document defines the user types, role model, and permissions for the Molecular Analysis Dashboard, including multi-tenant boundaries and governance.

## User Types (Actors)

- Root
  - Superuser independent of any organization. Global visibility and control.
- Admin
  - Organization-scoped administrator. Manages users, roles, pipelines, and resources for their organization.
- Standard
  - Organization-scoped end user. Runs pipelines, views statuses and results, manages their data within org constraints.
- (Optional) Service Account
  - Non-interactive principal for automation/integration.

## Role-Based Access Control (RBAC)

- Roles are sets of permissions. Users can have multiple roles within an organization. The Root user is outside org scope and has full permissions.
- Recommended built-in roles per organization:
  - `admin`: Full org administration (users, roles, pipelines, quotas)
  - `operator` (optional): Can run pipelines and manage jobs, but cannot change org settings
  - `standard`: Can run predefined pipelines and view job results
  - `viewer` (optional): Read-only access to job results and metadata

### Core Permission Scopes

- Organization Management
  - `org.view`, `org.update`, `org.quota.update`
- User & Role Management
  - `user.create`, `user.update`, `user.disable`, `role.assign`, `role.manage`
- Pipeline Lifecycle
  - `pipeline.create`, `pipeline.update`, `pipeline.delete`, `pipeline.view`
  - `task.define`, `task.update`, `task.delete`, `task.view`
- Job Execution
  - `job.create` (run pipeline), `job.cancel`, `job.view`, `job.results.view`
- Storage Access
  - `storage.put`, `storage.get`, `artifact.list`, `artifact.delete`
- Security & Audit
  - `audit.view`, `policy.update`, `secrets.manage`

### Example Permission Matrix (Summary)

| Capability | Root | Admin | Standard |
|---|---|---|---|
| Manage organizations | ✅ | ❌ | ❌ |
| Manage users/roles (org) | ✅ | ✅ | ❌ |
| Create/update pipelines | ✅ | ✅ | ❌ |
| Run pipelines (jobs) | ✅ | ✅ | ✅ |
| View all org results | ✅ | ✅ | ✅ (own + allowed) |
| Cross-org visibility | ✅ | ❌ | ❌ |

Notes:
- Admin and Standard are organization-scoped. Root is global.
- Cross-organization data access is prohibited except for Root.

## Multi-Tenancy Model

- Organizations (tenants) logically isolate compute and data access.
- Metadata database is shared across all organizations (users, roles, pipelines, job metadata).
- Each organization has:
  - A separate results database (for heavy/large results tables)
  - A separate storage bucket or namespace for artifacts (inputs/outputs/logs)
- Within an organization, users share the same results DB and storage bucket.
- Isolation boundaries are enforced by:
  - JWT claims: `sub`, `org_id`, `roles`, optional `scopes`
  - Repository layer: every query filters by `org_id`
  - Storage adapter: prefixes paths with `org_id/` or maps to per-org buckets

## Authentication and Authorization

- Auth: JWT-based (access/refresh) with signed tokens.
- Claims include: `sub` (user id), `org_id`, `roles`, optional `scopes`, `exp`.
- Authorization is enforced at the API boundary via role/permission checks and propagated to use cases.

## Auditing and Compliance

- Audit trails for: logins, role changes, pipeline updates, job lifecycle, artifact access.
- Include `org_id`, `user_id`, `job_id`, `pipeline_id`, and timestamp in audit events.

## Administrative Responsibilities

- Root: Onboards organizations, sets global policies, configures shared services, monitors quotas and health.
- Admin: Manages org users/roles, defines pipelines, monitors jobs, handles data governance in their org.
