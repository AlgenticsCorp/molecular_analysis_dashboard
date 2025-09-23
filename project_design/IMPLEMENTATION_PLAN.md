# Implementation Plan (Enhanced with Dynamic Task System)

This plan ensures the system is runnable at the end of every stage. Each stage defines a small goal, strict scope, quality gates, and rollback. **Enhanced to include dynamic task system for scalable computational workflows.**

Deployment steps per stage live in:
- Local (Compose): `project_design/DEPLOYMENT_PLAN_LOCAL.md`
- Cloud (VM/Kubernetes outline): `project_design/DEPLOYMENT_PLAN_CLOUD.md`

References: `ARCHITECTURE.md`, `FRAMEWORK_DESIGN.md`, `API_CONTRACT.md`, `ERD.md`, `SCHEMA_PROPOSAL.md`, `DATABASES.md`.

---

## Stage 0: Bootstrap API Health ✅ COMPLETED
Goal: Minimal FastAPI app with `/health`. No DB, no broker.

- Scope
    - Skeleton package at `src/molecular_analysis_dashboard/`
    - Endpoint: `GET /health` -> `{ "status": "ok" }`
- Quality gates
    - Build/lint pass (pre-commit if configured)
    - `curl http://localhost:8000/health` returns 200
- **Status: COMPLETED** - Health endpoint functional and accessible
- Rollback
    - Revert app init; keep only health check

## Stage 1: Metadata DB + Alembic Baseline + Task Registry Foundation ✅ COMPLETED
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
- **Status: COMPLETED** - Database schema established, migrations functional, ready endpoint operational
- Rollback
    - Downgrade migration; disable DB wiring
    - Fall back to static task definitions if needed

## Stage 2: Dynamic Task Registry + Basic Task Management ✅ COMPLETED
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
- **Status: COMPLETED** - Task registry API implemented with:
    - FastAPI endpoints with Pydantic schemas (`/api/v1/tasks`)
    - Task transformer services for data conversion
    - Frontend TaskService with API client and fallback mechanism
    - Static task data fallback for high availability
    - Feature flag system for controlled rollout
    - React hooks integration (useTasks, useTaskDetail, useTaskCategories)
    - Comprehensive test coverage (30 unit tests, 17 integration tests, 74% coverage)
- Rollback
    - Fall back to hardcoded task definitions; keep schema (non-breaking)

## Stage 3: Complete Containerization + Molecules & Artifacts ✅ COMPLETED
Goal: Deploy each system component as separate secure containers; implement molecule upload functionality.

### Phase 1: Frontend & Storage Containerization ✅ COMPLETED
- **Frontend Service**: React/Vite container with Nginx production serving
- **Storage Service**: Dedicated file storage container with volume management
- **Molecule Management**: Upload/download API with organization isolation
- **Security Hardening**: Non-root containers, input validation, CORS

### Phase 2: Storage Service Integration ✅ COMPLETED
- **File Storage Adapter**: Complete FileStorageAdapter implementation
- **API Integration**: Molecule upload endpoints with validation
- **Volume Management**: Persistent storage with organized directory structure
- **Comprehensive Testing**: 50+ tests (unit, integration, API, E2E)

### Phase 3: Gateway Service & Security 🔄 IN PROGRESS
- **API Gateway**: Centralized routing and load balancing
- **Service Mesh**: Enhanced inter-service communication
- **Advanced Security**: JWT validation, rate limiting, RBAC integration
- **SSL/TLS Termination**: Production-ready HTTPS configuration

### Phase 4: Integration & Testing 🔄 PENDING
- **End-to-End Integration**: Full workflow validation
- **Performance Testing**: Load testing and optimization
- **Production Hardening**: Monitoring, alerting, and observability
- **Deployment Automation**: CI/CD pipeline integration

- **Current Status: Phases 1-2 COMPLETED** - Core containerization functional:
    - All services containerized with health checks
    - Storage service operational with comprehensive testing
    - Molecule upload/download workflows working
    - Production documentation and troubleshooting guides
- **Next: Phase 3 (Gateway Service) & Phase 4 (Integration Testing)**
- Rollback
    - Revert new containers; keep existing containerized services; disable new endpoints (non-breaking)

## Stage 4: Dynamic Task Execution + Service Orchestration ⏳ PENDING
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
- **Status: READY TO START** - Prerequisites completed:
    - Task definitions ready (Stage 2)
    - Container infrastructure operational (Stage 3 Phases 1-2)
    - Storage system functional for task inputs/outputs
    - Will leverage gateway service from Stage 3 Phase 3
- Rollback
    - Fall back to hardcoded task execution; keep enhanced tracking tables

## Stage 5: Results DB Provisioning + Pipeline Templates ⏳ PENDING
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
- **Status: PENDING** - Foundation ready, pipeline composition needs implementation
- Rollback
    - Drop org results DB (dev only); disable pipeline composition

## Stage 6: Frontend Dynamic Interface Generation 🔄 PARTIALLY COMPLETED
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
- **Status: PARTIALLY COMPLETED** - TaskLibrary component dynamically loads tasks from API with fallback, but form generation needs implementation
- **Pending: Dynamic form generation, task execution UI, pipeline builder**
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
- Stage 0: FastAPI app, `/health` ✅ **COMPLETED**
- Stage 1: DB engine, Alembic, `/ready`, identity/RBAC tables, **task registry foundation** ✅ **COMPLETED**
- Stage 2: **Dynamic task registry API**, **OpenAPI-based task definitions**, system task seeding ✅ **COMPLETED**
- Stage 3: **Complete containerization**, `molecules`/`artifacts`, storage adapter, upload endpoint ✅ **COMPLETED**
- Stage 4: **Dynamic task execution API**, **service discovery integration**, HTTP-based task adapters ⏳ **PENDING**
- Stage 5: Results DB provisioning, **pipeline templates**, composable workflows ⏳ **PENDING**
- Stage 6: **Dynamic frontend interfaces**, **auto-generated forms**, real-time task UI 🔄 **PARTIALLY COMPLETED**
- Stage 7: Celery/Redis coordination, **task service orchestration**, workflow execution ⏳ **PENDING**
- Stage 8: **Legacy engine integration**, enhanced docking results, molecular analysis tools ⏳ **PENDING**
- Stage 9: **Intelligent caching**, confidence-based result reuse, task-aware optimization ⏳ **PENDING**
- Stage 10: Enhanced event tracking, **task service logging**, centralized log aggregation ⏳ **PENDING**
- Stage 11: **Task-level permissions**, organization task scoping, enhanced RBAC ⏳ **PENDING**
- Stage 12: **Production task infrastructure**, auto-scaling, performance analytics, resource quotas ⏳ **PENDING**

## Enhanced Test Matrix
- 0: `/health` 200 ✅ **PASSING**
- 1: `/ready` 200 with DB + task registry; migrations ok ✅ **PASSING**
- 2: **Tasks definable in database; OpenAPI specs validate; frontend loads dynamically** ✅ **PASSING**
- 3: **All services containerized and scalable; molecule upload persists row + file; presign valid** ✅ **PASSING**
- 4: **Dynamic task execution via HTTP; service discovery routing; parameter validation** ⏳ **PENDING**
- 5: **Pipeline templates compose tasks; workflow instantiation works** ⏳ **PENDING**
- 6: **Frontend generates forms from database specs; real-time task monitoring** 🔄 **PARTIAL - TaskLibrary loads dynamically**
- 7: **Pipeline workflows execute with dependencies; task services scale on demand** ⏳ **PENDING**
- 8: **Legacy engines accessible as database tasks; enhanced result tracking** ⏳ **PENDING**
- 9: **Intelligent cache hits across task versions; confidence-based decisions** ⏳ **PENDING**
- 10: **Task service logs aggregated; enhanced event context tracking** ⏳ **PENDING**
- 11: **Task permissions enforced; organization custom task scoping** ⏳ **PENDING**
- 12: **Auto-scaling operational; performance monitoring active; quotas enforced** ⏳ **PENDING**

---

## Current Implementation Status (Updated September 23, 2025)

### ✅ COMPLETED FEATURES
1. **Task Registry API with Frontend Integration**
   - FastAPI endpoints: `GET /api/v1/tasks`, `GET /api/v1/tasks/{task_id}`, `GET /api/v1/tasks/categories`
   - Pydantic schemas for type-safe task definitions
   - Task transformer services for data conversion between database and API formats
   - Frontend TaskService with HTTP client, retry logic, and 5-minute caching
   - Automatic fallback to static data when API unavailable
   - Feature flag system for controlled rollout (API vs static data)
   - React hooks integration: `useTasks`, `useTaskDetail`, `useTaskCategories`
   - Performance optimizations: memoized parameters, infinite re-render loop fixes
   - Comprehensive test coverage: 30 unit tests, 17 integration tests, 74% coverage

2. **Frontend Task Library**
   - TaskLibrary component dynamically loads tasks from API
   - Graceful degradation to static task data (3 comprehensive task templates)
   - Search and filtering capabilities
   - Loading states, error handling, and user feedback
   - Feature flag debugging interface
   - API health monitoring with status indicators

3. **Infrastructure Foundation**
   - Database schema with task_definitions, task_services, pipeline_templates
   - Alembic migrations for version control
   - Health (`/health`) and readiness (`/ready`) endpoints
   - Clean Architecture compliance with proper separation of concerns

3. **Complete Storage Containerization (Stage 3 Extension)**
   - Frontend container: Multi-stage React/Vite build with Nginx production serving
   - Storage service: Dedicated Nginx-based file server with security hardening
   - Volume management: Persistent storage with organized directory structure
   - Molecule upload API: Complete file validation, organization isolation, presigned URLs
   - Comprehensive testing: 50+ tests across unit, integration, API, and E2E levels
   - Production documentation: Deployment guides, troubleshooting, performance optimization

### 🔄 PARTIALLY COMPLETED
1. **Stage 6**: Task loading is dynamic but form generation needs implementation

### ⏳ NEXT PRIORITIES
1. **Stage 3 - Phase 3**: Gateway Service & Security (API Gateway, advanced security)
2. **Stage 3 - Phase 4**: Integration & Testing (E2E validation, performance testing)
3. **Stage 4**: Dynamic task execution API with containerized service communication
4. **Stage 6**: Auto-generated forms from OpenAPI specifications

---

## 🚀 NEXT PHASES: Complete Containerization + Task Execution

**Two-Track Approach**: Complete containerization infrastructure while preparing task execution.

### **Track A: Complete Stage 3 Containerization** (Immediate Priority)

#### **Stage 3 - Phase 3: Gateway Service & Security**
- **API Gateway**: Centralized routing with Nginx/Traefik
- **Service Mesh**: Enhanced inter-service communication
- **Advanced Security**: JWT validation, rate limiting, RBAC integration
- **SSL/TLS Termination**: Production HTTPS configuration
- **Load Balancing**: Intelligent request distribution

#### **Stage 3 - Phase 4: Integration & Testing**
- **End-to-End Integration**: Full workflow validation
- **Performance Testing**: Load testing and bottleneck identification
- **Production Hardening**: Monitoring, alerting, observability
- **CI/CD Integration**: Automated deployment pipelines

### **Track B: Prepare Stage 4 Task Execution** (Parallel Development)

#### **Stage 4 - Phase A: Task Execution Infrastructure**
- **Task Execution API**: `POST /api/v1/tasks/{task_id}/execute`
- **Execution Status API**: `GET /api/v1/executions/{execution_id}/status`
- **Execution Results API**: `GET /api/v1/executions/{execution_id}/results`
- **Database Schema**: Enhanced `task_executions` table with service routing

#### **Stage 4 - Phase B: Service Discovery & Communication**
- **Service Registry**: Track healthy task service instances
- **HTTP Task Adapters**: OpenAPI-based service communication
- **Health Monitoring**: Automatic failover and recovery
- **Parameter Validation**: Schema validation from database specs

### **Technical Foundation Already In Place**:
✅ **Database Schema**: `task_definitions`, `task_services`, `pipeline_templates` ready
✅ **Container Infrastructure**: All services containerized with health checks
✅ **Storage System**: File upload/download for task inputs and results
✅ **API Framework**: FastAPI with comprehensive error handling and validation
✅ **Frontend Integration**: Dynamic task loading with React hooks

### **Key Deliverables for Stage 4**:
1. **Containerized Task Services**: Sample docking services as containers
2. **Service Orchestration**: Discovery and routing of task execution requests
3. **Real-time Execution**: Live status updates and result streaming
4. **OpenAPI Integration**: Full schema validation from database specifications
5. **Production Testing**: Comprehensive test coverage for execution workflows

### **Success Metrics**:
- ✅ Tasks execute via HTTP calls to containerized services
- ✅ Parameters validate against database-stored OpenAPI schemas
- ✅ Service discovery routes to healthy instances automatically
- ✅ Real-time execution status updates work correctly
- ✅ Task results persist and are accessible via API

### **Estimated Effort**: 2-3 weeks
- Week 1: Task execution API and database integration
- Week 2: Service discovery and HTTP communication
- Week 3: Testing, optimization, and documentation
