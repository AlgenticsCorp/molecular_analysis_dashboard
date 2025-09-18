# Molecular Analysis Dashboard - AI Coding Agent Instructions

This is a **molecular analysis platform** built with **Clean Architecture** (Ports & Adapters), supporting pluggable docking engines (Vina/Smina/Gnina) with React TypeScript frontend and FastAPI backend.

## 🔄 Terminal & Process Management
- **Reuse the last active integrated terminal** for commands
- **Only open a new terminal** if the last active terminal is running a long-lived process (e.g., dev server, tail, watch). Detect by checking recent process output or known start commands (npm run dev, vite, uvicorn, flask, next dev, etc.)
- When opening a new terminal, **name it** with the task (e.g., `build`, `tests`, `lint`) and reuse it thereafter
- **Environment activation**: Before running any commands, ensure the correct environment is active:
  - Backend: Check for virtual environment (`venv`, `conda`, `poetry`) activation
  - Frontend: Ensure correct Node.js version if using version managers
  - Docker: Verify services are running before executing dependent commands

## 🛡️ Change Safety & Approvals
- **Do not modify or write code** unless the user has explicitly asked for an update, modification, or implementation
- Before any change:
  1) **Read** all `.md` guidance in the repo (project_design/*.md, README.md, CONTRIBUTING.md, etc.) and **map** the repo structure to decide correct locations
  2) **Propose a short plan** (files to touch, functions to add/change, tests to run). **Ask for approval** before editing
- When a task is done:
  - **Run** the solution end-to-end, **read console output**, and summarize results and any errors
  - **Ask for approval** to mark the task complete

## 🐛 Debugging Discipline
- During debugging, you may insert **temporary diagnostics** (logs, asserts, feature flags) but **remove all debug code** once fixed
- Apply the **final fix in place** in the canonical file(s) (no duplicate/new versions unless explicitly requested)

## 🗑️ Dependency & Deletion Safety
- Before removing any file or symbol, **analyze references** (imports, exports, runtime use) to ensure it isn't depended on. Propose the removal plan and get approval

## ✅ Testing & Validation
- After completing a task or fix, **run the relevant tests/linters** and **execute** the app/command needed to prove it works. Summarize console output and status

## 📝 Git & CI
- In GitHub repos: after successful local validation, **ask for approval** before `git commit` / `git push` / PR creation
- Use descriptive commit messages; if creating a PR, include a summary of changes, tests run, and risk notes

## 🔁 Interaction Loop (applies after *every* user request)
1) Clarify intent if ambiguous
2) If the user did **not** ask for changes → provide analysis/plan only; **do not edit**
3) If changes are requested → read guidelines, propose plan → **wait for approval**
4) Implement approved plan; reuse terminals; respect env activation
5) Test, run, read console; **ask for approval** to finish
6) If GitHub: ask approval to commit/push/PR after tests pass

## 🧬 Domain Knowledge

**Core Entities**: `Molecule`, `DockingJob`, `Pipeline`, `Organization` - molecular structures undergo docking analysis via computational engines
**Key Workflows**: Upload molecules → Configure pipeline parameters → Submit docking jobs → Monitor execution → Visualize 3D results
**Multi-tenant**: Organization-based data isolation with per-org results databases
**Async Processing**: Long-running molecular docking via Celery workers (separate from API)

## 🏗️ Clean Architecture Pattern

**STRICT layering** - dependencies point inward only:

```
src/molecular_analysis_dashboard/
├── domain/          # Pure business logic (Molecule, DockingJob entities)
├── use_cases/       # Application services (CreateDockingJobUseCase)
├── ports/           # Abstract interfaces (DockingEnginePort, RepositoryPort)
├── adapters/        # Implementations (PostgreSQLRepository, VinaAdapter)
├── infrastructure/  # Framework setup (Celery, FastAPI, DB sessions)
├── presentation/    # API routes and Pydantic schemas
└── shared/          # Cross-cutting utilities
```

**Adding features**: Start with `domain/` entities → `use_cases/` orchestration → `ports/` interfaces → `adapters/` implementations → wire in `infrastructure/`

## 🛠️ Development Patterns

### Docker-First Development
```bash
# Backend services (always start with this)
docker compose up -d postgres redis
docker compose run --rm migrate  # Run migrations first
docker compose up -d api worker

# Frontend (separate terminal)
cd frontend && npm run dev

# Scale workers independently
docker compose up -d --scale worker=3
```

### Testing Strategy
- **Unit tests**: `pytest tests/unit/` - fast, isolated business logic
- **Integration**: `pytest tests/integration/` - database and service integration
- **E2E**: `docker compose -f docker-compose.test.yml up --abort-on-container-exit`
- **Frontend**: `cd frontend && npm test`

### Code Quality (MANDATORY)
```bash
# Backend - all must pass
pre-commit run --all-files  # Black, isort, flake8, mypy, bandit
pytest --cov=src/molecular_analysis_dashboard --cov-fail-under=80

# Frontend
npm run type-check && npm run lint && npm test
```

## 🔌 Key Integration Patterns

### Docking Engine Adapters
- **Pluggable engines**: Implement `DockingEnginePort` for new engines (Vina/Smina/Gnina/custom)
- **Subprocess execution**: Engines run as external processes, results parsed from output files
- **Error handling**: Map engine-specific errors to domain exceptions

### Database Patterns
- **Multi-tenant**: Shared metadata DB + per-org results DBs (dynamic connection routing)
- **Async SQLAlchemy**: All DB operations use `async`/`await` with connection pooling
- **Alembic migrations**: Always run `docker compose run --rm migrate` after schema changes

### File Storage
- **Development**: Local filesystem (`STORAGE_TYPE=local`)
- **Production**: S3/MinIO (`STORAGE_TYPE=s3`) - same adapter interface
- **Artifacts**: Store URIs in DB, not file contents

## 📁 File Placement Rules

**Domain Logic** → `domain/entities/`, `domain/services/`
**Business Workflows** → `use_cases/commands/`, `use_cases/queries/`
**External Contracts** → `ports/repository/`, `ports/external/`
**Database/Engine/API** → `adapters/database/`, `adapters/messaging/`
**Config/DI/Security** → `infrastructure/`
**HTTP API** → `presentation/api/`
**React Components** → `frontend/src/components/`, `frontend/src/pages/`

## 🎯 API & Frontend Patterns

### FastAPI Conventions
- **JWT auth**: All endpoints require org-scoped JWT tokens
- **Pydantic schemas**: Strict input/output validation
- **Health checks**: `/health` (liveness), `/ready` (dependencies)
- **API versioning**: `/api/v1/` prefix

### React TypeScript Patterns
- **Material-UI**: Consistent design system with theme
- **React Query**: Server state management for API calls
- **3Dmol.js**: Molecular visualization in browser
- **Form handling**: React Hook Form + Zod validation
- **Type safety**: Shared TypeScript interfaces between frontend/backend

## ⚡ Performance & Scaling

**API**: Stateless FastAPI - scale horizontally (`--scale api=N`)
**Workers**: CPU-bound Celery workers - tune concurrency per queue
**Database**: Connection pooling, read replicas for large datasets
**Storage**: Object storage (S3/MinIO) for large molecular files
**Caching**: Redis for job queues and result caching via `input_signature`

## 🔄 Common Workflows

### Adding New Docking Engine
1. Implement `DockingEnginePort` in `adapters/external/`
2. Add engine config to `infrastructure/settings.py`
3. Register in dependency injection
4. Add engine option to pipeline creation UI

### Database Schema Changes
1. Create Alembic migration: `alembic revision --autogenerate -m "description"`
2. Test migration: `docker compose run --rm migrate`
3. Update repository adapters and domain entities
4. Run tests to verify data flow

### New API Endpoints
1. Define Pydantic schemas in `presentation/api/schemas/`
2. Create use case in `use_cases/` (business logic)
3. Add FastAPI router in `presentation/api/routes/`
4. Update frontend API client in `frontend/src/services/`

## 🚨 Critical Conventions

- **Never bypass the adapter pattern** - don't import SQLAlchemy models in use cases
- **Async everywhere** - all database and HTTP operations use async/await
- **Multi-tenant aware** - all queries must filter by `org_id`
- **Type safety** - use mypy strict mode, comprehensive docstrings
- **Docker-first** - local development uses containers, not local Python installs
- **Test coverage** - maintain 80%+ coverage, test at correct architectural layers

## 📚 Key Reference Files

- Architecture: `project_design/ARCHITECTURE.md`, `project_design/FRAMEWORK_DESIGN.md`
- API contracts: `project_design/API_CONTRACT.md`
- Database schema: `project_design/ERD.md`
- Deployment: `project_design/DEPLOYMENT_DOCKER.md`
- Implementation stages: `project_design/IMPLEMENTATION_PLAN.md`

---

## 🚨 CRITICAL: Follow the Interaction Loop

**Every request must follow this sequence:**
1. **Clarify** if intent is ambiguous
2. **Analyze** before acting - read relevant docs and understand the change
3. **Propose** a plan and wait for approval if making changes
4. **Implement** using proper terminals and environments
5. **Test** and validate the solution works
6. **Report** results and ask for approval to complete
