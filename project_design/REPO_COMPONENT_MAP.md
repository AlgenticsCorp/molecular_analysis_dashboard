# Repository & Container Component Map

Purpose: Provide a clear, single reference mapping between runtime components (containers), Docker images, and source code folders, and show where documentation lives.

Assumptions
- Target package path is `src/molecular_analysis_dashboard/` per design. If the code skeleton still uses `src/yourpkg/`, plan to rename during Sprint 1.
- Workdir inside containers is `/app`.

---

## Documentation Layout

- Root docs (overview & process)
  - `README.md` — project overview, quick start
  - `SETUP.md` — single source of truth for installation
  - `DEVELOPER_GUIDE.md`, `CONTRIBUTING.md`, `GITHUB_WORKFLOW.md`, `TROUBLESHOOTING.md`
- Design docs (human-authored)
  - `project_design/ARCHITECTURE.md` — layers and responsibilities
  - `project_design/FRAMEWORK_DESIGN.md` — diagrams (component/sequence/deployment/class)
  - `project_design/TOOLS_AND_WORKFLOW.md` — tech stack & E2E flow
  - `project_design/IMPLEMENTATION_PLAN.md` — phased execution (sprints)
  - `project_design/USE_CASES.md`, `project_design/USERS_AND_ROLES.md`, `project_design/DATABASES.md`
  - `project_design/API_CONTRACT.md` — endpoint contracts
  - `project_design/REPO_COMPONENT_MAP.md` — this file
- Generated docs & artifacts
  - `docs/atlas/*` — import/call graphs (generated)
  - `docs/schema.json` — code schema (generated)

---

## Runtime Components → Docker Images → Compose Services

- API (FastAPI + Gunicorn/Uvicorn)
  - Image: built from `docker/Dockerfile.api`
  - Service: `api` (in `docker-compose.yml`)
  - Ports: `8000:8000`
  - Healthcheck: `GET /health`

- Worker (Celery)
  - Image: built from `docker/Dockerfile.worker`
  - Service: `worker`
  - Consumes: Redis broker, Postgres DB

- Migrate (Alembic one-shot)
  - Image: same as API image (`docker/Dockerfile.api`)
  - Service: `migrate`
  - Command: `alembic upgrade head`

- Flower (Celery monitoring)
  - Image: `mher/flower`
  - Service: `flower`
  - Port: `5555:5555`

- Infrastructure dependencies
  - Postgres: `postgres:16` (service `postgres`)
  - Redis: `redis:7-alpine` (service `redis`)

---

## Source Code Folders → Component Responsibilities

Target layout under `src/molecular_analysis_dashboard/`:

- Presentation (API)
  - `presentation/api/` — FastAPI app & routers, Pydantic schemas, health/ready endpoints
- Use Cases (application services)
  - `use_cases/commands/`, `use_cases/queries/` — orchestration logic
- Ports (interfaces)
  - `ports/repository/`, `ports/external/` — Protocols/ABCs for DB, engines, storage
- Adapters (implementations)
  - `adapters/database/` — SQLAlchemy repositories (PostgreSQL)
  - `adapters/external/` — docking engine adapters (Vina/Smina/Gnina), RDKit helpers
  - `adapters/messaging/` — Celery task implementations (if separated)
- Infrastructure (wiring/config)
  - `infrastructure/config.py` — Pydantic settings
  - `infrastructure/database.py` — SQLAlchemy engine/session
  - `infrastructure/security.py` — JWT/password
  - `infrastructure/celery_app.py` — Celery instance & routes
- Domain (pure business)
  - `domain/entities/`, `domain/services/`
- Shared (cross-cutting)
  - `shared/` — utilities, constants, helpers
- Tasks (if applicable)
  - `tasks/` — Celery task entrypoints (can live under adapters/messaging too)

Note: During Sprint 1, some folders may be created as stubs.

---

## Container Files & Configuration

- Docker files
  - `docker/Dockerfile.api` — API image build
  - `docker/Dockerfile.worker` — Celery worker image build
  - `docker/gunicorn_conf.py` — Gunicorn settings
- Compose & environment
  - `docker-compose.yml` — service topology
  - `.env.example` → copy to `.env`
  - Key envs (shared via `x-common-env`): `DATABASE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `RESULTS_DIR`, `UPLOADS_DIR`, `SECRET_KEY`, `LOG_LEVEL`
- Volumes
  - `results:` → mounted at `$RESULTS_DIR` (default `/data/results`)
  - `uploads:` → mounted at `$UPLOADS_DIR` (default `/data/uploads`)

---

## Quick Commands

- Build all
  ```bash
  docker compose build
  ```
- Start infra then app
  ```bash
  docker compose up -d postgres redis
  docker compose run --rm migrate
  docker compose up -d api worker
  ```
- Healthcheck
  ```bash
  curl -f http://localhost:8000/health
  ```
- Scale
  ```bash
  docker compose up -d --scale api=2 --scale worker=3
  ```

---

## Traceability (Design → Code → Runtime)

- Use Cases → `use_cases/*` → invoked by API routers → may enqueue Celery tasks
- Ports → `ports/*` → implemented by `adapters/*` → swap adapters without changing core
- Storage adapter → `adapters/external/*` or `adapters/storage/*` → LocalFS in dev, S3/MinIO in prod
- Readiness → `presentation/api/*` + `infrastructure/*` check DB & broker

For diagrams of interactions and deployment topology, see `FRAMEWORK_DESIGN.md`.
