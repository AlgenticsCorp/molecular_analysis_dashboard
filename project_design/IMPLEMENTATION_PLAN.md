# Implementation Plan (Enhanced with Dynamic Task System)

This plan ensures the system is runnable at the end of every stage. Each stage defines a small goal, strict scope, quality gates, and rollback. **Enhanced to include dynamic task system for scalable computational workflows.**

Deployment steps per stage live in:
- Local (Compose): `project_design/DEPLOYMENT_PLAN_LOCAL.md`
- Cloud (VM/Kubernetes outline): `project_design/DEPLOYMENT_PLAN_CLOUD.md`

References: `ARCHITECTURE.md`, `FRAMEWORK_DESIGN.md`, `API_CONTRACT.md`, `ERD.md`, `SCHEMA_PROPOSAL.md`, `DATABASES.md`.

---

## Stage 0: Bootstrap API Health
Goal: Minimal FastAPI app with `/health`. No DB, no broker.

- Scope
    - Skeleton package at `src/molecular_analysis_dashboard/`
    - Endpoint: `GET /health` -> `{ "status": "ok" }`
- Quality gates
    - Build/lint pass (pre-commit if configured)
    - `curl http://localhost:8000/health` returns 200
- Rollback
    - Revert app init; keep only health check

## Stage 1: Metadata DB + Alembic Baseline + Task Registry Foundation
Goal: Add PostgreSQL connectivity, migrations with core identity/RBAC, and dynamic task system foundation.

- Scope
    - Async SQLAlchemy engine/session; Alembic configured
    - Migrations create: `organizations`, `users`, `roles`, `role_permissions`, `memberships`, `membership_roles`, `tokens`
    - **Dynamic Task Tables**: `task_definitions`, `task_services`, `pipeline_templates`, `pipeline_task_steps`
    - Endpoint: `GET /ready` -> DB connectivity check + task registry connectivity
- Quality gates
    - Alembic upgrade/downgrade succeed locally
    - `/ready` returns `ready` when DB up and task registry accessible
    - **Task definition CRUD operations work via database**
- Rollback
    - Downgrade migration; disable DB wiring
    - Fall back to static task definitions if needed

## Stage 2: Dynamic Task Registry + Basic Task Management
Goal: Database-driven task definitions with OpenAPI specifications.

- Scope
    - **Task Registry API**: `GET /api/v1/task-registry/tasks`, `POST /api/v1/task-registry/tasks`
    - **OpenAPI Interface Loading**: Task definitions include full OpenAPI 3.0 specifications
    - **System Task Seeding**: Insert built-in molecular docking tasks into database
    - **Basic Service Discovery**: Track running task services in `task_services` table
- Quality gates
    - **Tasks can be defined in database without code changes**
    - **Frontend can load task list from API dynamically**
    - **OpenAPI specifications validate correctly**
- Rollback
    - Fall back to hardcoded task definitions; keep schema (non-breaking)

## Stage 2: Dynamic Task Registry + Basic Task Management
Goal: Database-driven task definitions with OpenAPI specifications.

- Scope
    - **Task Registry API**: `GET /api/v1/task-registry/tasks`, `POST /api/v1/task-registry/tasks`
    - **OpenAPI Interface Loading**: Task definitions include full OpenAPI 3.0 specifications
    - **System Task Seeding**: Insert built-in molecular docking tasks into database
    - **Basic Service Discovery**: Track running task services in `task_services` table
- Quality gates
    - **Tasks can be defined in database without code changes**
    - **Frontend can load task list from API dynamically**
    - **OpenAPI specifications validate correctly**
- Rollback
    - Fall back to hardcoded task definitions; keep schema (non-breaking)

## Stage 3: Molecules & Artifacts + Storage Adapter
Goal: Upload molecules; persist metadata and file URIs.

- Scope
    - Tables: `molecules`, optional `artifacts`
    - Storage adapter: LocalFS (dev) with configurable root; presigned URL stub
    - Endpoints: `POST /api/v1/molecules/upload`, optional `GET /api/v1/artifacts/{uri}`
- Quality gates
    - Upload small file -> DB row exists; file present at storage path; downloadable via URL/presign
- Rollback
    - Revert endpoints; keep schema (non-breaking)

## Stage 4: Dynamic Task Execution + Service Orchestration
Goal: Execute tasks defined in database via containerized services.

- Scope
    - **Dynamic Task Execution API**: `POST /api/v1/tasks/{task_id}/execute`, `GET /api/v1/executions/{execution_id}/status`
    - **Service Discovery Integration**: Find and route to healthy task service instances
    - **HTTP-based Task Adapters**: Communication with containerized task services via OpenAPI
    - **Enhanced Task Executions**: Track execution metadata including service URL and task definition ID
- Quality gates
    - **Tasks execute via HTTP calls to containerized services**
    - **Task parameters validate against database-stored OpenAPI schemas**
    - **Service discovery routes requests to healthy instances**
- Rollback
    - Fall back to hardcoded task execution; keep enhanced tracking tables

## Stage 5: Results DB Provisioning + Pipeline Templates
Goal: Establish per-org Results DB and pipeline composition system.

- Scope
    - Provision Results DB (or schema) for an org and apply initial DDL: `jobs`, `job_inputs`, `job_outputs`, `dynamic_task_results`
    - Metadata DB: add `jobs_meta`
    - **Pipeline Templates**: `GET /api/v1/pipeline-templates`, `POST /api/v1/pipeline-templates/{template_id}/instantiate`
    - **Composable Workflows**: Define pipelines as DAG of database tasks
- Quality gates
    - Job creation writes to both DBs idempotently; status is retrievable
    - **Pipeline templates can be composed from available tasks**
    - **Pipeline instantiation creates executable workflow**
- Rollback
    - Drop org results DB (dev only); disable pipeline composition

## Stage 6: Frontend Dynamic Interface Generation
Goal: Auto-generate task forms and interfaces from database specifications.

- Scope
    - **Dynamic Form Generation**: Frontend generates forms from OpenAPI specifications loaded from database
    - **Real-time Task Interface**: Forms adapt automatically when task definitions change
    - **Task Execution UI**: Submit and monitor dynamic task executions
    - **Pipeline Builder**: Visual interface for composing pipelines from available tasks
- Quality gates
    - **Frontend loads and renders new tasks without code deployment**
    - **Form validation follows OpenAPI schema from database**
    - **Task execution status updates in real-time**
- Rollback
    - Fall back to static task forms; keep API integration

## Stage 7: Async Pipeline Orchestration + Task Services
Goal: Wire Celery worker coordination with containerized task services.

- Scope
    - Celery app + worker for workflow orchestration; Redis as broker
    - **Task Service Management**: Auto-scaling and health monitoring of containerized task services
    - **Workflow Coordination**: Execute pipeline DAGs with task dependencies
    - **Service Load Balancing**: Distribute task executions across available service instances
- Quality gates
    - **Pipeline workflows execute with proper task dependency resolution**
    - **Task services scale based on demand**
    - **Failed task services are detected and replaced**
- Rollback
    - Stop worker; API path falls back to single-task execution

## Stage 8: Enhanced Docking Engines + Legacy Integration
Goal: Integrate traditional docking engines with dynamic task system.

- Scope
    - **Legacy Engine Adapters**: Wrap AutoDock Vina, Smina, Gnina as database-defined tasks
    - **Engine-Specific Services**: Containerized docking engines with standardized OpenAPI interfaces
    - Results DB: enhanced `docking_results` with confidence scoring
    - **Molecular Analysis Tools**: Additional computational chemistry tasks as database entries
- Quality gates
    - Known test ligand/protein produce deterministic outputs via dynamic task system
    - **Legacy engines work seamlessly through database-defined interfaces**
    - **Results visible via enhanced API with confidence tracking**
- Rollback
    - Fall back to direct engine adapters; keep dynamic task capability

## Stage 9: Advanced Caching + Result Intelligence
Goal: Intelligent result reuse and confidence-based optimization.

- Scope
    - Compute `input_signature` (normalized inputs + params) for `jobs`
    - Tables: enhanced `task_results` (JSONB + `confidence_score`), `result_cache` with task-aware caching
    - **Intelligent Cache Keys**: Cache results per task type and version
    - **Confidence-Based Reuse**: Reuse results based on confidence scores and similarity
- Quality gates
    - **Submitting same inputs twice yields cache hit across different task versions**
    - **Confidence scoring influences cache reuse decisions**
    - TTL/threshold honored per task type
- Rollback
    - Disable intelligent caching; continue basic cache functionality

## Stage 10: Logs Separation + Enhanced Event Tracking
Goal: Comprehensive event tracking for dynamic task executions.

- Scope
    - Logs stored in object storage/log backend; keep `logs_uri` only
    - Table: enhanced `job_events` with task-specific event types
    - **Task Service Logs**: Centralized logging from containerized task services
    - Endpoints: `/api/v1/jobs/{job_id}/events`, `/api/v1/executions/{execution_id}/logs`
- Quality gates
    - **Events populate with task-specific context**
    - **Task service logs aggregated and accessible**
    - Logs downloadable via signed link
- Rollback
    - Continue basic event logging; keep enhanced schema

## Stage 11: External Auth + Dynamic Task Permissions
Goal: Fine-grained permissions for custom task creation and execution.

- Scope
    - Tables: `identity_providers`, `identities`
    - **Task-Level Permissions**: RBAC for task creation, execution, and management
    - **Organization Task Scoping**: Custom tasks scoped to organizations
    - OIDC login flow with task-aware permissions
- Quality gates
    - **IdP login with task-specific role enforcement**
    - **Organization admins can create custom tasks**
    - **Standard users can execute permitted tasks only**
- Rollback
    - Fall back to basic RBAC; keep enhanced permission schema

## Stage 12: Production Hardening + Task Service Infrastructure
Goal: Production-ready dynamic task system with comprehensive monitoring.

- Scope
    - **Task Service Orchestration**: Kubernetes-based task service deployment and scaling
    - **Service Health Monitoring**: Comprehensive health checks and auto-recovery
    - **Task Performance Analytics**: Track task execution performance and resource usage
    - **Resource Quotas**: Per-organization limits on task execution resources
    - Enhanced metrics, tracing, structured logging for task services
- Quality gates
    - **Task services auto-scale based on demand**
    - **Performance bottlenecks detected and reported**
    - **Resource quotas enforced per organization**
    - Comprehensive monitoring dashboards operational
- Rollback
    - Disable auto-scaling; revert to basic service management

---

## Per-Stage Deliverables (Enhanced Summary)
- Stage 0: FastAPI app, `/health`
- Stage 1: DB engine, Alembic, `/ready`, identity/RBAC tables, **task registry foundation**
- Stage 2: **Dynamic task registry API**, **OpenAPI-based task definitions**, system task seeding
- Stage 3: `molecules`/`artifacts`, storage adapter, upload endpoint
- Stage 4: **Dynamic task execution API**, **service discovery integration**, HTTP-based task adapters
- Stage 5: Results DB provisioning, **pipeline templates**, composable workflows
- Stage 6: **Dynamic frontend interfaces**, **auto-generated forms**, real-time task UI
- Stage 7: Celery/Redis coordination, **task service orchestration**, workflow execution
- Stage 8: **Legacy engine integration**, enhanced docking results, molecular analysis tools
- Stage 9: **Intelligent caching**, confidence-based result reuse, task-aware optimization
- Stage 10: Enhanced event tracking, **task service logging**, centralized log aggregation
- Stage 11: **Task-level permissions**, organization task scoping, enhanced RBAC
- Stage 12: **Production task infrastructure**, auto-scaling, performance analytics, resource quotas

## Enhanced Test Matrix
- 0: `/health` 200
- 1: `/ready` 200 with DB + task registry; migrations ok
- 2: **Tasks definable in database; OpenAPI specs validate; frontend loads dynamically**
- 3: molecule upload persists row + file; presign valid
- 4: **Dynamic task execution via HTTP; service discovery routing; parameter validation**
- 5: **Pipeline templates compose tasks; workflow instantiation works**
- 6: **Frontend generates forms from database specs; real-time task monitoring**
- 7: **Pipeline workflows execute with dependencies; task services scale on demand**
- 8: **Legacy engines accessible as database tasks; enhanced result tracking**
- 9: **Intelligent cache hits across task versions; confidence-based decisions**
- 10: **Task service logs aggregated; enhanced event context tracking**
- 11: **Task permissions enforced; organization custom task scoping**
- 12: **Auto-scaling operational; performance monitoring active; quotas enforced**
