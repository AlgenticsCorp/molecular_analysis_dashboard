# Molecular Analysis Dashboard

[![CI](https://github.com/AlgenticsCorp/molecular_analysis_dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/AlgenticsCorp/molecular_analysis_dashboard/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/AlgenticsCorp/molecular_analysis_dashboard/branch/main/graph/badge.svg)](https://codecov.io/gh/AlgenticsCorp/molecular_analysis_dashboard)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end platform for running and managing molecular docking pipelines. The system follows **Clean Architecture** (Hexagonal/Ports & Adapters), exposes a FastAPI backend, offloads long-running compute to Celery workers, persists state in PostgreSQL, uses Redis as a broker, and stores artifacts on local filesystem (dev) or S3/MinIO (prod). The repo is fully containerized for easy local runs and ready to scale out in orchestrators.

> Governance and Policies: see `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, and `CHANGELOG.md`.

## 🔗 Quick Links

- Architecture Overview: [project_design/ARCHITECTURE.md](project_design/ARCHITECTURE.md)
- Frontend Architecture: [project_design/FRONTEND_ARCHITECTURE.md](project_design/FRONTEND_ARCHITECTURE.md)
- Framework Design & Diagrams: [project_design/FRAMEWORK_DESIGN.md](project_design/FRAMEWORK_DESIGN.md)
- Tools & Workflow: [project_design/TOOLS_AND_WORKFLOW.md](project_design/TOOLS_AND_WORKFLOW.md)
- Docker Deployment & Scaling: [project_design/DEPLOYMENT_DOCKER.md](project_design/DEPLOYMENT_DOCKER.md)
- Agile Implementation Plan: [project_design/IMPLEMENTATION_PLAN.md](project_design/IMPLEMENTATION_PLAN.md)
- Users & Roles: [project_design/USERS_AND_ROLES.md](project_design/USERS_AND_ROLES.md)
- Use Cases: [project_design/USE_CASES.md](project_design/USE_CASES.md)
- Databases & Tenancy: [project_design/DATABASES.md](project_design/DATABASES.md)

For initial setup details and development environment guidelines, see [SETUP.md](SETUP.md) and [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).
## 🏗️ Architecture

This project implements **SOLID** and **Clean Architecture** patterns. See `project_design/ARCHITECTURE.md` for details and `project_design/FRAMEWORK_DESIGN.md` for Mermaid diagrams.

## 🛠️ Technology Stack

### **Backend**
- **Python 3.11+** with FastAPI, Celery, SQLAlchemy
- **PostgreSQL** for data persistence with multi-tenant architecture
- **Redis** for task queuing and caching
- **Docker** for containerization and local development

### **Frontend**
- **React 18+** with TypeScript for type-safe UI development
- **Material-UI (MUI)** for consistent design system
- **React Query** for server state management and caching
- **Vite** for fast development and optimized builds
- **3Dmol.js** for interactive molecular visualization

### **Molecular Computing**
- **AutoDock Vina, Smina, Gnina** via pluggable engine adapters
- **RDKit** for cheminformatics and molecular processing

```
src/molecular_analysis_dashboard/
├── domain/          # Business entities and domain services
├── use_cases/       # Application services (business logic)
├── ports/           # Abstract interfaces (dependency inversion)
├── adapters/        # Concrete implementations (DB, external engines, storage)
├── infrastructure/  # Celery, DB session, config, security
├── presentation/    # FastAPI routers, schemas, templates
└── shared/          # Cross-cutting utilities
```

## 🚀 Quick Start

### Option A: Full Stack Development (Backend + Frontend)

```bash
# Backend setup
cp .env.example .env
docker compose build
docker compose up -d postgres redis
docker compose run --rm migrate   # after Alembic is configured
docker compose up -d api worker

# Frontend setup (in new terminal)
cd frontend
npm install
npm run dev

# Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option B: Backend Only (API development)

```bash
cp .env.example .env
docker compose build
docker compose up -d postgres redis
docker compose run --rm migrate   # after Alembic is configured
docker compose up -d api worker
curl -f http://localhost:8000/health
```

Scale horizontally:

```bash
docker compose up -d --scale api=2 --scale worker=3
```

See `project_design/DEPLOYMENT_DOCKER.md` for details.

### Option B: Run via virtualenv (for contributors)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs,tools]"
pre-commit install
pytest
```

## 🛠️ Development Workflow

### Code Quality Gates

Every commit is protected by:

- **Code formatting**: Black, isort
- **Type checking**: mypy with strict settings
- **Linting**: flake8, pylint, bandit
- **Docstring enforcement**: pydocstyle, flake8-docstrings
- **Complexity analysis**: radon (cyclomatic & maintainability)
- **Security scanning**: bandit
- **Test coverage**: pytest-cov (≥80% required)

### Documentation Standards

**Mandatory docstrings** for all public APIs using Google style:

```python
def process_order(order_id: str, user_id: str) -> OrderResult:
    """
    Process a customer order through the fulfillment pipeline.

    Args:
        order_id: Unique identifier for the order.
        user_id: Customer's user identifier.

    Returns:
        OrderResult containing processing status and details.

    Raises:
        OrderNotFoundError: If order_id doesn't exist.
        InsufficientInventoryError: If items are out of stock.

    Example:
        >>> result = process_order("ORD-123", "USR-456")
        >>> result.status
        'completed'
    """
```

### Automated Code Atlas

The project automatically generates:

- **Schema extraction** (`docs/schema.json`): Machine-readable API documentation
- **Call graphs** (`docs/atlas/calls.svg`): Function-level dependency visualization
- **Import graphs** (`docs/atlas/imports.svg`): Module dependency visualization
- **Interactive docs** (`mkdocs serve`): Browsable API documentation

## 📊 Quality Metrics

### Complexity Thresholds

- **Cyclomatic Complexity**: ≤ 10 per function
- **Maintainability Index**: ≥ B grade
- **Max function length**: ≤ 60 statements
- **Max function args**: ≤ 6 parameters

### Test Coverage

- **Minimum coverage**: 80%
- **Test types**: Unit, Integration, E2E
- **Test organization**: Mirror `src/` structure in `tests/`

## 🤖 AI Agent Integration

This project is optimized for AI-assisted development:

### For LLM Agents

1. **Read** `DEVELOPER_GUIDE.md` for architecture patterns
2. **Analyze** `docs/schema.json` for current API surface
3. **Review** `docs/atlas/*.svg` for dependency relationships
4. **Follow** docstring templates for consistent documentation
5. **Validate** changes with `pre-commit run --all-files`

### Agent-Friendly Features

- **Single source of truth**: Code generates all documentation
- **Clear contracts**: Comprehensive type hints and docstrings
- **Dependency visualization**: Understand impact of changes
- **Automated validation**: Immediate feedback on code quality
- **Standardized structure**: Predictable file organization

## 🔧 Project Customization

### 1. Update Project Metadata

Edit `pyproject.toml`:
```toml
[project]
name = "your-actual-package-name"
description = "Your project description"
authors = [{name = "Your Name", email = "your.email@domain.com"}]
```

### 2. Rename Package Directory

```bash
mv src/yourpkg src/molecular_analysis_dashboard
# Update imports throughout codebase
```

### 3. Configure Repository URLs

Update in `pyproject.toml` and CI workflows:
```toml
[project.urls]
Homepage = "https://github.com/AlgenticsCorp/molecular_analysis_dashboard"
Repository = "https://github.com/AlgenticsCorp/molecular_analysis_dashboard"
```

## 📁 Project Structure

```
project-root/
├── .github/workflows/           # CI/CD pipelines
├── .vscode/                    # VS Code configuration
├── docs/                       # Generated docs
│   ├── atlas/                  # Generated graphs
│   ├── schema.json            # API schema
│   └── *.md                   # Manual documentation
├── src/molecular_analysis_dashboard/  # Source code
│   ├── domain/                # Business logic
│   ├── use_cases/             # Application services
│   ├── ports/                 # Interfaces
│   ├── adapters/              # Implementations
│   ├── infrastructure/        # Configuration & DI
│   ├── presentation/          # Controllers & CLI
│   └── shared/                # Utilities
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
├── tools/                     # Development tools
├── bootstrap.sh               # Project setup script
├── pyproject.toml             # Project configuration
├── project_design/             # Design and plans
│   ├── ARCHITECTURE.md
│   ├── FRAMEWORK_DESIGN.md
│   ├── TOOLS_AND_WORKFLOW.md
│   ├── DEPLOYMENT_DOCKER.md
│   └── implementation_plan.md
└── DEVELOPER_GUIDE.md         # Engineering guide
```

## 📚 Documentation

- Architecture Overview: `project_design/ARCHITECTURE.md`
- Framework Design & Diagrams: `project_design/FRAMEWORK_DESIGN.md`
- Tools & Workflow: `project_design/TOOLS_AND_WORKFLOW.md`
- Deployment & Scaling: `project_design/DEPLOYMENT_DOCKER.md`
- Implementation Plan: `project_design/IMPLEMENTATION_PLAN.md`
- Users & Roles: `project_design/USERS_AND_ROLES.md`
- Use Cases: `project_design/USE_CASES.md`
- Databases & Tenancy: `project_design/DATABASES.md`
- API Contract: `project_design/API_CONTRACT.md`
- Component Map (Repo ↔ Containers): `project_design/REPO_COMPONENT_MAP.md`
- Configuration Reference: `project_design/CONFIGURATION.md`
- Security Architecture: `project_design/SECURITY_ARCH.md`
- Operations Runbook: `project_design/RUNBOOK.md`
- Task Queue Design: `project_design/QUEUE_DESIGN.md`
- Data Model ERD: `project_design/ERD.md`
- Schema Proposal (DDL): `project_design/SCHEMA_PROPOSAL.md`
- Developer Guide: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- API Docs (local): `mkdocs serve`
- Code Atlas: `docs/atlas/` (dependency graphs)
- API Schema: `docs/schema.json` (machine-readable)

## 🧪 Testing Strategy

### Test Organization
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Service integration tests
└── e2e/           # Full system tests
```

### Running Tests
```bash
# All tests
pytest

# Specific test types
pytest -m unit
pytest -m integration
pytest -m e2e

# With coverage
pytest --cov=src/molecular_analysis_dashboard --cov-report=html
```

## 🔄 Continuous Integration

GitHub Actions workflow includes:

- **Multi-Python versions**: 3.9, 3.10, 3.11, 3.12
- **Cross-platform**: Linux, macOS, Windows
- **Quality gates**: All linting and testing
- **Security scanning**: Bandit, safety
- **Documentation**: Auto-build and deploy
- **Atlas generation**: Dependency graphs
- **Coverage reporting**: Codecov integration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the established patterns
4. Ensure all quality gates pass: `pre-commit run --all-files`
5. Add/update tests and documentation
6. Submit a pull request

## 🙏 Acknowledgments

- **Clean Architecture**: Robert C. Martin
- **Ports & Adapters**: Alistair Cockburn
- **SOLID Principles**: Robert C. Martin
- **Python Tooling**: Black, isort, mypy, pytest, and the amazing Python community
