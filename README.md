# Molecular Analysis Dashboard

[![CI](https://github.com/AlgenticsCorp/molecular_analysis_dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/AlgenticsCorp/molecular_analysis_dashboard/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/AlgenticsCorp/molecular_analysis_dashboard/branch/main/graph/badge.svg)](https://codecov.io/gh/AlgenticsCorp/molecular_analysis_dashboard)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive web-based platform for molecular analysis and computational chemistry workflows. Built with modern architecture patterns, this dashboard provides researchers and scientists with tools to manage molecular docking pipelines, visualize results, and orchestrate complex computational workflows.

## 🎯 Key Features

### 🧬 Molecular Analysis Capabilities
- **Multi-Engine Docking**: Support for AutoDock Vina, Smina, and **Gnina (✅ LIVE)** via NeuroSnap cloud API
- **3D Molecular Visualization**: Interactive molecule viewing with 3Dmol.js
- **Cheminformatics Integration**: RDKit-powered molecular processing
- **Pipeline Management**: Create and manage complex analysis workflows
- **Real-time Job Monitoring**: Live updates on running computations
- **🆕 GNINA Cloud Integration**: Production-ready molecular docking via NeuroSnap API with comprehensive workflow orchestration

### 🎨 Modern Web Interface
- **React TypeScript Frontend**: Type-safe, responsive user interface
- **Material-UI Components**: Professional, consistent design system
- **Multi-step Wizards**: Intuitive task configuration and execution
- **Real-time Updates**: WebSocket integration for live job status
- **Mobile-Friendly**: Responsive design for all devices

### 🏗️ Enterprise Architecture
- **Clean Architecture**: SOLID principles with Hexagonal/Ports & Adapters pattern
- **API Gateway**: OpenResty-based intelligent routing with security and observability
- **Microservice Ready**: FastAPI backend with containerized deployment
- **Scalable Computing**: Celery-based distributed task processing
- **Multi-tenant**: Organization-based data isolation
- **Security First**: JWT authentication with role-based access control

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### 1. Clone and Setup
```bash
git clone https://github.com/AlgenticsCorp/molecular_analysis_dashboard.git
cd molecular_analysis_dashboard
cp .env.example .env
```

### 2. Start Backend Services
```bash
# Start infrastructure services
docker compose up -d postgres redis

# Run database migrations
docker compose run --rm migrate

# Configure NeuroSnap API integration
echo "NEUROSNAP_API_KEY=your_api_key_here" >> .env

# Start all services including gateway
docker compose up -d
```

### 3. Access the Application
- **Dashboard**: http://localhost (gateway routes to frontend)
- **API Documentation**: http://localhost/api/docs
- **GNINA Docking API**: http://localhost/api/v1/tasks/gnina-molecular-docking/execute
- **API Health Check**: http://localhost/health
- **System Status**: http://localhost/api/v1/health

> **🧬 GNINA Integration**: Complete molecular docking workflow now available via NeuroSnap cloud API with interactive Swagger UI testing.

## 📱 Application Overview

### Dashboard Features
The molecular analysis dashboard provides eight main interfaces:

1. **📊 Platform Dashboard**
   - Real-time job statistics and system metrics
   - Recent job history with status tracking
   - Quick access to common actions
   - System health monitoring

2. **📚 Task Library**
   - Browse available molecular analysis tasks
   - Task templates and configurations
   - Custom task creation and management
   - Version control for analysis protocols

3. **⚡ Execute Tasks**
   - Multi-step wizard for job configuration
   - Molecule upload and validation
   - Parameter optimization settings
   - Batch job submission

4. **🔄 Pipelines**
   - Visual pipeline builder
   - Workflow orchestration
   - Dependency management
   - Pipeline templates and sharing

5. **👔 Job Manager**
   - Real-time job monitoring
   - Resource usage tracking
   - Log streaming and error handling
   - Job scheduling and prioritization

6. **📁 File Manager**
   - Molecular structure file organization
   - Bulk upload and validation
   - File format conversion
   - Storage quota management

7. **⚙️ Admin Panel**
   - User and organization management
   - System configuration
   - Resource allocation
   - Security settings

8. **🔧 Settings**
   - User preferences and profiles
   - API key management
   - Notification settings
   - Integration configurations

## 🛠️ Technology Stack

### Backend Architecture
```
├── FastAPI (Web Framework)
├── SQLAlchemy (ORM)
├── PostgreSQL (Database)
├── Redis (Cache & Message Broker)
├── Celery (Distributed Tasks)
├── Docker (Containerization)
└── JWT (Authentication)
```

### Frontend Architecture
```
├── React 18 + TypeScript
├── Material-UI (Design System)
├── React Query (State Management)
├── React Router (Navigation)
├── React Hook Form + Zod (Forms)
├── 3Dmol.js (Molecular Visualization)
├── WebSocket (Real-time Updates)
└── Vite (Build Tool)
```

### Molecular Computing
```
├── AutoDock Vina (Molecular Docking)
├── Smina (Enhanced Docking)
├── ✅ Gnina (Deep Learning Docking) - LIVE via NeuroSnap Cloud API
├── RDKit (Cheminformatics)
├── OpenBabel (Format Conversion)
└── ChemAxon (Enterprise Tools)
```

**🆕 GNINA Integration Status:**
- ✅ **Production Ready**: Complete Clean Architecture implementation
- ✅ **Cloud Integration**: NeuroSnap API with async workflow orchestration
- ✅ **API Endpoints**: Full FastAPI REST interface with OpenAPI documentation
- ✅ **Comprehensive Testing**: Unit, integration, and E2E test suites (>80% coverage)
- ✅ **Interactive Testing**: Live Swagger UI at http://localhost:8000/docs

## 🏗️ Architecture Patterns

This project implements **Clean Architecture** with clear separation of concerns:

```
src/molecular_analysis_dashboard/
├── domain/          # Business entities (Molecule, Job, Pipeline)
├── use_cases/       # Application services (CreateJob, RunDocking)
├── ports/           # Abstract interfaces (Repository, DockingEngine)
├── adapters/        # Concrete implementations (PostgreSQL, Vina)
├── infrastructure/  # Framework setup (Celery, FastAPI, Config)
├── presentation/    # API routes and schemas
└── shared/          # Cross-cutting utilities
```

Key architectural benefits:
- **Testability**: Business logic isolated from frameworks
- **Flexibility**: Easy to swap implementations
- **Maintainability**: Clear dependencies and responsibilities
- **Scalability**: Horizontally scalable with Docker Compose

## 🧪 Development Workflow

### Quality Gates
Every commit is protected by automated checks:
- **Type Safety**: mypy strict mode
- **Code Formatting**: Black + isort
- **Linting**: flake8, pylint
- **Security**: bandit scanning
- **Testing**: pytest with 80%+ coverage
- **Documentation**: Comprehensive docstrings

### Running Tests
```bash
# Backend tests
pytest tests/ --cov=src

# Frontend tests
cd frontend && npm test

# Integration tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Development Environment
```bash
# Backend development
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install

# Frontend development
cd frontend
npm install
npm run dev

# API documentation
mkdocs serve
```

## 🚀 Deployment

### 🐳 Containerized Deployment (Recommended)

The molecular analysis dashboard is fully containerized for easy deployment across environments. All services run as secure, isolated containers with proper health checks and networking.

#### Prerequisites
- Docker 20.10+ with Docker Compose
- 4GB+ RAM available for containers
- 10GB+ disk space for images and data

#### Complete Stack Deployment

```bash
# 1. Clone and configure
git clone https://github.com/AlgenticsCorp/molecular_analysis_dashboard.git
cd molecular_analysis_dashboard
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Run database migrations
docker compose run --rm migrate

# 4. Verify deployment
curl http://localhost:3000/health
```

**Service Access:**
- **🌐 Frontend Application**: http://localhost:3000
- **📊 API Documentation**: http://localhost:3000/api/docs (proxied)
- **🔍 Health Check**: http://localhost:3000/health
- **📈 Worker Monitoring**: http://localhost:5555 (Flower UI)

#### Individual Service Management

```bash
# Scale services independently
docker compose up -d --scale api=3 --scale worker=5

# Monitor service logs
docker compose logs -f frontend api worker

# Restart specific services
docker compose restart frontend api

# View service status
docker compose ps
```

#### Container Architecture

```
                        ┌─────────────────┐
                        │   API Gateway   │ ← NEW: Phase 3A Complete
                        │  (OpenResty)    │   • JWT Authentication
                        │   Port: 80/443  │   • Rate Limiting
                        └─────────────────┘   • Service Routing
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │      API        │    │     Worker      │
│   (React/Nginx) │    │   (FastAPI)     │    │   (Celery)      │
│   Port: 3000    │    │   Port: 8000    │    │   Background    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐               │
         │──────────────│    Storage      │───────────────│
                        │   (Nginx)       │
                        │   Port: 8080    │
                        └─────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐
         │   PostgreSQL    │    │     Redis       │
         │   Port: 5432    │    │   Port: 6379    │
         └─────────────────┘    └─────────────────┘
```

#### 📁 Storage Service Container

The storage service is a dedicated Nginx-based container that handles all molecular file operations with enhanced security and performance.

**🔧 Key Features:**
- **Dedicated file server**: Isolated container for molecular file management
- **Volume management**: Persistent storage with organized directory structure
- **Security hardening**: Non-root execution, CORS handling, content validation
- **Health monitoring**: Built-in health checks and monitoring endpoints
- **Organization isolation**: Secure per-organization file separation
- **Format support**: PDB, SDF, MOL2, and other molecular formats

**📂 Storage Structure:**
```
/storage/
├── uploads/          # User-uploaded molecular files
│   └── {org-id}/     # Per-organization isolation
│       └── molecules/# Organized by type
├── results/          # Docking computation results
│   └── {org-id}/     # Per-organization results
│       └── jobs/     # Job-specific outputs
└── temp/             # Temporary processing files
    └── {session-id}/ # Session-based cleanup
```

**🚀 Storage Service Management:**

```bash
# Check storage service status
docker compose ps storage
docker compose logs storage

# Monitor storage usage
docker compose exec storage df -h /storage
docker compose exec storage du -sh /storage/*

# Access storage endpoints
curl http://localhost:8080/health              # Health check
curl http://localhost:8080/uploads/            # Browse uploads
curl http://localhost:8080/results/            # Browse results

# Storage service configuration
docker compose exec storage cat /etc/nginx/conf.d/default.conf
```

**🔒 Security Features:**

- **Non-root execution**: Runs as nginx user (UID 101)
- **Read-only filesystem**: Only storage volumes are writable
- **CORS configuration**: Proper cross-origin request handling
- **Content-Type validation**: Strict MIME type enforcement
- **Directory traversal protection**: Path sanitization and validation
- **Access logging**: Comprehensive request logging

**⚡ Performance Optimization:**

```bash
# Scale storage for high I/O workloads
docker compose up -d --scale storage=2

# Monitor storage performance
docker stats storage
docker compose exec storage iostat -x 1

# Optimize for large files
# Edit docker-compose.yml:
services:
  storage:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

**🛠️ File Upload API Integration:**

The storage service integrates with the FastAPI backend for seamless molecular file operations:

```bash
# Upload molecule via API (proxied through frontend)
curl -X POST http://localhost:3000/api/v1/molecules/upload \
  -F "file=@molecule.pdb" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Direct storage access (for debugging)
curl -X PUT http://localhost:8080/uploads/org-123/molecules/test.pdb \
  --data-binary @molecule.pdb \
  -H "Content-Type: chemical/x-pdb"
```

**🔍 Storage Health Monitoring:**

```bash
# Comprehensive health check
curl -s http://localhost:8080/health | jq '.'
{
  "status": "healthy",
  "service": "storage",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}

# Monitor storage metrics
docker compose exec storage cat /var/log/nginx/access.log
docker compose exec storage cat /var/log/nginx/error.log
```

**🐛 Storage Service Troubleshooting:**

1. **Permission Issues:**
   ```bash
   # Fix volume permissions
   docker compose exec storage chown -R nginx:nginx /storage
   docker compose restart storage
   ```

2. **Upload Failures:**
   ```bash
   # Check upload directory permissions
   docker compose exec storage ls -la /storage/uploads/

   # Verify CORS headers
   curl -I -X OPTIONS http://localhost:8080/uploads/
   ```

3. **File Not Found Errors:**
   ```bash
   # Check file organization
   docker compose exec storage find /storage -name "*.pdb" -ls

   # Verify API connectivity
   docker compose exec frontend nslookup storage
   ```

4. **Performance Issues:**
   ```bash
   # Monitor I/O usage
   docker stats --format "table {{.Container}}\t{{.BlockIO}}"

   # Check storage volume usage
   docker volume inspect molecular_analysis_dashboard_uploads
   ```

#### Security Features

- **🔒 Non-root containers**: All services run with minimal privileges
- **🛡️ Network isolation**: Services communicate via internal networks only
- **🚪 Single entry point**: Frontend acts as reverse proxy for all traffic
- **📋 Health monitoring**: Comprehensive health checks for all containers
- **🔧 Resource limits**: Configurable CPU and memory constraints

#### Environment Configuration

**Development Environment:**
```bash
# Start with development overrides
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Enable hot reloading for frontend development
cd frontend && npm run dev  # Runs outside container for faster iteration
```

**Production Environment:**
```bash
# Use production optimizations
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Enable SSL/TLS with reverse proxy
# See project_design/DEPLOYMENT_DOCKER.md for HTTPS setup
```

#### Volume Management

```bash
# Persistent data volumes
docker volume ls | grep molecular_analysis

# Backup database
docker compose exec postgres pg_dump -U user molecular_db > backup.sql

# Backup uploaded files
docker compose exec frontend tar -czf /tmp/uploads.tar.gz /usr/share/nginx/html/uploads

# View storage usage
docker system df
docker compose exec frontend df -h /usr/share/nginx/html
```

#### Performance Tuning

**Horizontal Scaling:**
```bash
# Scale API for high traffic
docker compose up -d --scale api=5

# Scale workers for computational load
docker compose up -d --scale worker=10

# Monitor resource usage
docker stats
```

**Resource Allocation:**
```yaml
# Add to docker-compose.override.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
  worker:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

#### Troubleshooting

**Common Issues:**

1. **Frontend not accessible**: Check container health and port mapping
   ```bash
   docker compose ps frontend
   docker compose logs frontend
   curl -I http://localhost:3000
   ```

2. **API proxy errors**: Verify network connectivity between containers
   ```bash
   docker compose exec frontend nslookup api
   docker compose logs api
   ```

3. **Build failures**: Clear Docker cache and rebuild
   ```bash
   docker compose down
   docker system prune -f
   docker compose build --no-cache
   docker compose up -d
   ```

4. **Performance issues**: Monitor resource usage and scale appropriately
   ```bash
   docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
   ```

**Health Check Debugging:**
```bash
# Check all service health
docker compose ps

# View health check logs
docker inspect $(docker compose ps -q frontend) | jq '.[0].State.Health'

# Manual health check
docker compose exec frontend curl -f http://localhost:3000/health
```

#### CI/CD Integration

**GitHub Actions Example:**
```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
          docker compose run --rm migrate
```

**Rolling Updates:**
```bash
# Zero-downtime frontend updates
docker compose build frontend
docker compose up -d --no-deps frontend

# Blue-green API deployment
docker compose up -d --scale api=6  # Start new instances
# Wait for health checks to pass
docker compose up -d --scale api=3  # Remove old instances
```

### 🌩️ Cloud Deployment

#### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml molecular-dashboard

# Scale services
docker service scale molecular-dashboard_api=3
```

#### Kubernetes
```bash
# Using provided manifests
kubectl apply -f k8s/

# Using Helm chart
helm install molecular-dashboard ./helm/molecular-dashboard
```

#### Cloud Platforms

**AWS ECS:**
- Task definitions provided in `deploy/aws/`
- ALB configuration for load balancing
- RDS for managed PostgreSQL
- ElastiCache for managed Redis

**Google Cloud Run:**
- Cloud Build configuration
- Managed database integration
- Auto-scaling based on traffic

**Azure Container Instances:**
- ARM templates for infrastructure
- Container groups for service orchestration
- Managed PostgreSQL integration

### 📊 Monitoring and Observability

#### Application Metrics
```bash
# View service metrics
docker compose exec frontend curl http://localhost:3000/metrics

# API performance metrics
docker compose exec api curl http://localhost:8000/metrics

# Worker queue metrics
docker compose exec flower curl http://localhost:5555/api/workers
```

#### Log Aggregation
```bash
# Centralized logging
docker compose logs -f --tail=100

# Service-specific logs
docker compose logs -f frontend
docker compose logs -f api --since=1h
```

#### Health Monitoring
```bash
# Continuous health monitoring
watch -n 5 'docker compose ps'

# Automated health checks
# See monitoring/healthcheck.sh for automated monitoring script
```

For detailed cloud deployment guides, see `project_design/DEPLOYMENT_DOCKER.md` and platform-specific documentation in the `deploy/` directory.

## 📊 Monitoring and Observability

### Metrics
- **Application Metrics**: Job completion rates, error rates
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: User engagement, computation hours

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Log Aggregation**: Centralized logging with ELK stack
- **Error Tracking**: Sentry integration for error monitoring

### Health Checks
- **API Health**: `/health` endpoint
- **Database Connectivity**: Connection pool monitoring
- **Worker Health**: Celery worker status
- **External Services**: Docking engine availability

## 🔐 Security

### Authentication & Authorization
- **JWT Tokens**: Secure API authentication
- **Role-Based Access**: User, Admin, Super Admin roles
- **Organization Isolation**: Multi-tenant data security
- **API Rate Limiting**: Prevent abuse and ensure fair usage

### Data Protection
- **Encryption at Rest**: Database and file storage encryption
- **Encryption in Transit**: TLS/SSL for all communications
- **Input Validation**: Comprehensive request validation
- **Audit Logging**: Complete audit trail for compliance

## 📚 Documentation

### User Documentation
- [User Guide](docs/USER_GUIDE.md) - Complete user manual
- [API Reference](http://localhost:8000/docs) - Interactive API docs
- [Tutorial](docs/TUTORIAL.md) - Step-by-step getting started

### Developer Documentation
- [Architecture Guide](project_design/ARCHITECTURE.md) - System design overview
- [API Design](project_design/API_CONTRACT.md) - API specifications
- [Database Schema](project_design/ERD.md) - Data model documentation
- [Deployment Guide](project_design/DEPLOYMENT_DOCKER.md) - Production deployment

### Design Documentation
- [Frontend Architecture](project_design/FRONTEND_ARCHITECTURE.md) - UI/UX design patterns
- [Framework Design](project_design/FRAMEWORK_DESIGN.md) - System diagrams
- [Implementation Plan](project_design/IMPLEMENTATION_PLAN.md) - Development roadmap

## 🤝 Contributing

We welcome contributions from the molecular analysis and software development communities!

### Getting Started
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow our [Contributing Guidelines](CONTRIBUTING.md)
4. Ensure all tests pass: `pytest && npm test`
5. Submit a pull request

### Areas for Contribution
- **New Docking Engines**: Add support for additional molecular docking tools
- **Visualization Features**: Enhance 3D molecular visualization capabilities
- **Analysis Tools**: Implement new computational chemistry algorithms
- **UI/UX Improvements**: Enhance user experience and accessibility
- **Performance Optimization**: Improve computation and rendering performance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Scientific Community
- **AutoDock Team**: For the Vina docking engine
- **RDKit Contributors**: For cheminformatics tools
- **3Dmol.js Team**: For molecular visualization

### Technical Community
- **FastAPI**: For the excellent web framework
- **React Team**: For the robust frontend framework
- **Material-UI**: For the comprehensive design system

## 📞 Support

- **Documentation**: [User Guide](docs/USER_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/AlgenticsCorp/molecular_analysis_dashboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AlgenticsCorp/molecular_analysis_dashboard/discussions)
- **Email**: support@algentics.com

---

Built with ❤️ by the Algentics team for the molecular analysis community.
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

### Areas for Contribution
- **New Docking Engines**: Add support for additional molecular docking tools
- **Visualization Features**: Enhance 3D molecular visualization capabilities
- **Analysis Tools**: Implement new computational chemistry algorithms
- **UI/UX Improvements**: Enhance user experience and accessibility
- **Performance Optimization**: Improve computation and rendering performance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Scientific Community
- **AutoDock Team**: For the Vina docking engine
- **RDKit Contributors**: For cheminformatics tools
- **3Dmol.js Team**: For molecular visualization

### Technical Community
- **FastAPI**: For the excellent web framework
- **React Team**: For the robust frontend framework
- **Material-UI**: For the comprehensive design system

## 📞 Support

- **Documentation**: [User Guide](docs/USER_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/AlgenticsCorp/molecular_analysis_dashboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AlgenticsCorp/molecular_analysis_dashboard/discussions)
- **Email**: support@algentics.com

---

Built with ❤️ by the Algentics team for the molecular analysis community.

## 🗂️ Project Structure & Component Location Guide

This repository follows Clean Architecture principles with clear component organization. Here's where to find and how to document each type of component:

### 📁 **Repository Layout**
```
molecular_analysis_dashboard/
├── 📚 docs/                          # ✨ ALL DOCUMENTATION LIVES HERE
│   ├── 🏗️ architecture/             # System design & patterns
│   │   ├── system-design/           # Core architecture docs
│   │   ├── backend/                 # Backend architecture
│   │   ├── frontend/                # UI/UX architecture
│   │   └── integration/             # Service integration
│   ├── 🗄️ database/                # Database design & management
│   │   ├── design/                  # Schema, ERD, data models
│   │   ├── management/              # Migrations, performance
│   │   ├── connection-routing/      # Multi-tenant patterns
│   │   └── testing/                 # Database testing strategies
│   ├── 🔗 api/                     # API documentation
│   │   ├── contracts/               # REST API specifications
│   │   ├── gateway/                 # API gateway documentation
│   │   └── schemas/                 # Data schemas
│   ├── 🚀 deployment/              # Deployment guides
│   │   ├── environments/            # Environment configurations
│   │   ├── docker/                  # Container orchestration
│   │   └── cloud/                   # Cloud deployment strategies
│   ├── 👩‍💻 development/             # Developer resources
│   │   ├── getting-started/         # Onboarding guides
│   │   ├── guides/                  # Development guides
│   │   ├── workflows/               # Git, CI/CD, testing workflows
│   │   └── tools/                   # Development tools
│   ├── 🚀 implementation/          # Implementation tracking
│   │   └── phases/                  # Phase-based development progress
│   ├── 🔒 security/                # Security documentation
│   └── ⚙️ operations/              # Operational procedures
├── 🎨 frontend/                     # React TypeScript Application
│   ├── src/
│   │   ├── components/              # Reusable UI components
│   │   ├── pages/                   # Application pages/routes
│   │   ├── services/                # API client services
│   │   ├── types/                   # TypeScript definitions
│   │   └── utils/                   # Utility functions
│   ├── package.json                # Frontend dependencies
│   └── vite.config.ts              # Build configuration
├── 🔧 src/molecular_analysis_dashboard/  # Backend Clean Architecture
│   ├── 🏛️ domain/                  # Business entities & domain services
│   │   ├── entities/                # Core business objects (Molecule, Job)
│   │   ├── services/                # Domain business logic
│   │   └── exceptions/              # Domain-specific exceptions
│   ├── 💼 use_cases/               # Application services (business workflows)
│   │   ├── commands/                # Write operations (CreateJob, StartPipeline)
│   │   └── queries/                 # Read operations (GetMolecule, ListJobs)
│   ├── 🔌 ports/                   # Abstract interfaces (dependency inversion)
│   │   ├── repository/              # Data persistence abstractions
│   │   ├── external/                # External service interfaces
│   │   └── messaging/               # Message queue abstractions
│   ├── 🔧 adapters/                # Concrete implementations
│   │   ├── database/                # PostgreSQL, SQLAlchemy implementations
│   │   ├── external/                # Docking engines (Vina, Smina, Gnina)
│   │   ├── messaging/               # Celery, Redis implementations
│   │   └── storage/                 # File storage implementations
│   ├── 🏗️ infrastructure/          # Framework & configuration
│   │   ├── database/                # DB session management
│   │   ├── messaging/               # Celery configuration
│   │   ├── security/                # JWT, authentication
│   │   └── config/                  # Application settings
│   ├── 🌐 presentation/            # Web layer (FastAPI)
│   │   ├── api/                     # REST endpoints
│   │   ├── schemas/                 # Request/response models
│   │   └── middleware/              # HTTP middleware
│   └── 🔄 shared/                  # Cross-cutting utilities
│       ├── utils/                   # Common utilities
│       ├── constants/               # Application constants
│       └── exceptions/              # Shared exceptions
├── 🧪 tests/                       # Test Suite
│   ├── unit/                        # Fast, isolated business logic tests
│   ├── integration/                 # Service integration tests
│   └── e2e/                        # Full system end-to-end tests
├── 🐳 docker/                      # Container configurations
│   ├── Dockerfile.api              # Backend API container
│   ├── Dockerfile.frontend         # Frontend container
│   ├── Dockerfile.worker           # Celery worker container
│   └── nginx.conf                  # Nginx configuration
├── 📊 database/                    # Database operations
│   ├── alembic/                    # Database migrations
│   ├── models/                     # SQLAlchemy models
│   ├── scripts/                    # Database utility scripts
│   └── seeds/                      # Test data seeding
├── 🔧 tools/                       # Development & build tools
│   ├── extract_schema.py           # API schema extraction
│   ├── health_check.py             # System health verification
│   └── render_graphs.py            # Dependency visualization
├── 📋 project_management/          # Project tracking (if needed)
├── 🐳 docker-compose.yml           # Local development environment
├── ⚙️ pyproject.toml               # Python project configuration
└── 📖 README.md                    # This guide
```

### 🎯 **Where to Add New Components**

| **Component Type** | **Location** | **Documentation** |
|-------------------|-------------|------------------|
| **New Business Entity** | `src/domain/entities/` | `docs/architecture/system-design/` |
| **New Use Case** | `src/use_cases/commands/` or `queries/` | `docs/architecture/system-design/use-cases.md` |
| **New Docking Engine** | `src/adapters/external/` | `docs/architecture/backend/docking-engines.md` |
| **New API Endpoint** | `src/presentation/api/` | `docs/api/contracts/rest-api.md` |
| **New Database Table** | `database/alembic/versions/` | `docs/database/design/schema.md` |
| **New Frontend Page** | `frontend/src/pages/` | `docs/architecture/frontend/` |
| **New React Component** | `frontend/src/components/` | Component-level JSDoc comments |
| **New Storage Adapter** | `src/adapters/storage/` | `docs/architecture/backend/storage-adapters.md` |
| **New Authentication Method** | `src/infrastructure/security/` | `docs/security/architecture.md` |
| **New Deployment Environment** | `docker/` + docs | `docs/deployment/environments/` |
| **New Database Migration** | `database/alembic/versions/` | `docs/database/management/migrations.md` |
| **New Test Suite** | `tests/unit/`, `integration/`, `e2e/` | `docs/development/workflows/testing-workflows.md` |

## 📚 Comprehensive Documentation

> **🎯 All documentation is centrally organized in the [`docs/`](docs/) directory.** Start with the [**Documentation Hub**](docs/README.md) for complete navigation.

### 🚀 **Quick Access by Role**

| **Role** | **Start Here** | **Key Documents** |
|----------|---------------|------------------|
| **🆕 New Developer** | [Getting Started](docs/development/getting-started/setup.md) | Setup → Architecture → Workflow |
| **🏗️ System Architect** | [Architecture Hub](docs/architecture/README.md) | System Design → Clean Architecture → Patterns |
| **🎨 Frontend Developer** | [Frontend Architecture](docs/architecture/frontend/architecture.md) | React Patterns → Components → UI/UX |
| **⚙️ Backend Developer** | [Backend Architecture](docs/architecture/backend/docking-engines.md) | APIs → Domain Logic → Integrations |
| **🗄️ Database Developer** | [Database Design](docs/database/README.md) | Schema → Migrations → Multi-tenancy |
| **🚀 DevOps Engineer** | [Deployment Guides](docs/deployment/docker/setup.md) | Docker → CI/CD → Cloud Deployment |
| **📊 Project Manager** | [Implementation Status](docs/implementation/README.md) | Phase Progress → Planning → Roadmap |
| **🔒 Security Engineer** | [Security Architecture](docs/security/architecture.md) | Auth → Data Protection → Compliance |

### 📋 **Documentation Categories**

#### 🏗️ **[Architecture & Design](docs/architecture/README.md)**
- **[System Overview](docs/architecture/system-design/overview.md)** - High-level architecture
- **[Clean Architecture](docs/architecture/system-design/clean-architecture.md)** - SOLID principles implementation
- **[API Gateway Design](docs/architecture/integration/gateway.md)** - Service integration patterns
- **[Domain Model](docs/architecture/system-design/use-cases.md)** - Business logic organization
- **[Docking Engines](docs/architecture/backend/docking-engines.md)** - Molecular computation integration

#### 👩‍💻 **[Development Resources](docs/development/README.md)**
- **[Setup Guide](docs/development/getting-started/setup.md)** - Environment setup and first steps
- **[Developer Guide](docs/development/guides/developer-guide.md)** - Comprehensive development handbook
- **[Git Workflow](docs/development/workflows/git-workflow.md)** - Branching strategy and commit standards
- **[Testing Workflows](docs/development/workflows/testing-workflows.md)** - Testing strategies and automation
- **[CI/CD Pipeline](docs/development/workflows/cicd-pipeline.md)** - Automated quality gates and deployment

#### 🗄️ **[Database Documentation](docs/database/README.md)**
- **[Schema Design](docs/database/design/schema.md)** - Data models and relationships
- **[Multi-tenant Architecture](docs/database/connection-routing/multi-tenant.md)** - Organization-based isolation
- **[Migration Strategy](docs/database/management/migrations.md)** - Database evolution patterns
- **[Performance Optimization](docs/database/management/performance.md)** - Query optimization and scaling

#### 🔗 **[API Documentation](docs/api/README.md)**
- **[REST API Contracts](docs/api/contracts/rest-api.md)** - Complete endpoint specifications
- **[Interactive API Docs](http://localhost:8000/docs)** - Swagger/OpenAPI interface (when running)
- **[Authentication Flows](docs/security/architecture.md)** - JWT and authorization patterns

#### 🚀 **[Deployment & Operations](docs/deployment/docker/setup.md)**
- **[Docker Setup](docs/deployment/docker/setup.md)** - Containerized deployment guide
- **[Environment Configuration](docs/deployment/environments/configuration.md)** - Settings and environment variables
- **[Cloud Deployment](docs/deployment/cloud/production.md)** - Production deployment strategies
- **[Operations Runbook](docs/operations/runbook.md)** - Troubleshooting and maintenance

### 📖 **Documentation Standards & How to Document New Components**

#### ✍️ **When Adding New Components**

1. **📍 Choose the Right Location** (see Component Location Guide above)
2. **📝 Write Component Documentation** following these standards:
   - **Business Logic**: Document in relevant `docs/architecture/` section
   - **API Changes**: Update `docs/api/contracts/rest-api.md`
   - **Database Changes**: Update `docs/database/design/schema.md` + create migration docs
   - **Deployment Changes**: Update relevant `docs/deployment/` guides

#### 📐 **Documentation Format Standards**

```markdown
# Component Name

*Brief description of purpose and role in system*

## Overview
[What this component does and why it exists]

## Architecture
[How it fits into the Clean Architecture]

## Implementation
[Key implementation details and patterns]

## Usage Examples
[Code examples and common use cases]

## Testing
[How to test this component]

## Related Components
- [Link to related documentation]
- [Cross-references to dependent components]
```

#### 🔄 **Keeping Documentation Updated**

- **Before Code Changes**: Read relevant docs to understand current design
- **During Development**: Update documentation as you implement
- **Pull Request Reviews**: Documentation updates are required for architectural changes
- **Cross-References**: Always update related documentation sections

#### 🎯 **Documentation Quality Gates**

- ✅ **New APIs**: Must update API contracts and provide examples
- ✅ **New Database Tables**: Must update schema docs and provide migration guide
- ✅ **New Components**: Must document architecture integration and testing approach
- ✅ **Breaking Changes**: Must provide migration guide and update all affected docs

**📖 See the [Contributing Guide](docs/development/guides/contributing.md) for detailed documentation requirements.**

## 🧪 Testing Strategy

### Test Organization
```
tests/
├── unit/           # Fast, isolated tests for business logic
├── integration/    # Service integration tests
└── e2e/           # Full system tests with Docker
```

### Running Tests
```bash
# Backend tests
pytest tests/ --cov=src/molecular_analysis_dashboard

# Frontend tests
cd frontend && npm test

# Integration tests with Docker
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Specific test types
pytest -m unit
pytest -m integration
pytest -m e2e
```

## 🔄 Continuous Integration

GitHub Actions workflow includes:
- **Multi-Python versions**: 3.9, 3.10, 3.11, 3.12
- **Cross-platform**: Linux, macOS, Windows
- **Quality gates**: All linting and testing
- **Security scanning**: Bandit, safety
- **Documentation**: Auto-build and deploy
- **Coverage reporting**: Codecov integration

## 🔧 Configuration

### Environment Variables
Key configuration options in `.env`:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/molecular_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Molecular Engines
VINA_PATH=/usr/local/bin/vina
SMINA_PATH=/usr/local/bin/smina

# Security
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# File Storage
STORAGE_TYPE=local  # or s3
STORAGE_PATH=/app/data
```

### Docker Configuration
The application uses Docker Compose for orchestration:
- **API Service**: FastAPI application server
- **Worker Service**: Celery task workers for molecular computations
- **PostgreSQL**: Primary database for application data
- **Redis**: Message broker and caching layer

## 🎯 Use Cases

### Research Scientists
- Upload molecular structures for analysis
- Configure docking parameters and constraints
- Monitor long-running computational jobs
- Visualize and analyze docking results
- Export results for publication

### Computational Chemists
- Create custom analysis pipelines
- Batch process large molecular libraries
- Optimize docking parameters
- Compare results across different engines
- Integrate with existing computational workflows

### Laboratory Managers
- Manage user access and permissions
- Monitor system resource usage
- Configure organizational settings
- Generate usage reports and analytics
- Ensure data security and compliance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please follow our comprehensive contribution guidelines:

### 🚀 **Quick Start for Contributors**
1. **📚 Read First**: [Contributing Guide](docs/development/guides/contributing.md) - Complete process and standards
2. **🏗️ Understand Architecture**: [Architecture Overview](docs/architecture/system-design/overview.md)
3. **⚙️ Setup Environment**: [Development Setup](docs/development/getting-started/setup.md)
4. **🌿 Follow Workflow**: [Git Workflow](docs/development/workflows/git-workflow.md)

### 📋 **Contribution Process**
1. **Fork & Branch**: `git checkout -b feature/amazing-feature`
2. **Follow Patterns**: Use existing architectural patterns (see [Clean Architecture Guide](docs/architecture/system-design/clean-architecture.md))
3. **Quality Gates**: `pre-commit run --all-files` (see [Testing Workflows](docs/development/workflows/testing-workflows.md))
4. **Documentation**: Update relevant docs using our [Documentation Standards](#-documentation-standards--how-to-document-new-components)
5. **Testing**: Add tests following [Testing Guidelines](docs/development/workflows/testing-workflows.md)
6. **Pull Request**: Follow [PR Process](docs/development/workflows/pull-request-process.md)

### 🎯 **Areas for Contribution**
- **🧬 New Docking Engines**: Add support for additional molecular docking tools ([Backend Architecture](docs/architecture/backend/docking-engines.md))
- **📊 Visualization Features**: Enhance 3D molecular visualization ([Frontend Architecture](docs/architecture/frontend/architecture.md))
- **🔬 Analysis Tools**: Implement new computational chemistry algorithms ([Use Cases](docs/architecture/system-design/use-cases.md))
- **🎨 UI/UX Improvements**: Enhance user experience and accessibility ([Frontend Guides](docs/architecture/frontend/))
- **⚡ Performance Optimization**: Improve computation and rendering performance ([Performance Docs](docs/database/management/performance.md))

**💡 Before starting major work, please create an issue to discuss the approach and ensure alignment with project goals.**

## 🙏 Acknowledgments

- **Clean Architecture**: Robert C. Martin
- **Ports & Adapters**: Alistair Cockburn
- **SOLID Principles**: Robert C. Martin
- **Python Tooling**: Black, isort, mypy, pytest, and the amazing Python community
