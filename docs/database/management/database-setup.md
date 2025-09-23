# Database Management for Molecular Analysis Dashboard

This directory contains a **complete, self-contained database deployment system** for the Molecular Analysis Dashboard. Designed for easy deployment, maintenance, and external hosting.

## 🏗️ Architecture Overview

The database system uses a **multi-tenant architecture** with:
- **Metadata Database**: Shared organizational data (users, tasks, templates)
- **Results Databases**: Per-organization data isolation (jobs, results, artifacts)
- **Redis**: Caching and job queuing
- **Clean Architecture**: Domain-driven design with ports & adapters

## 📁 Directory Structure

```
database/
├── README.md                   # Complete deployment documentation
├── requirements.txt            # Python dependencies for database operations
├── docker-compose.db.yml       # Database services orchestration
├── Dockerfile.db               # Multi-stage container for DB operations
├── Makefile                    # Management commands (make help)
├── alembic.ini                 # Alembic migration configuration
├── alembic/                    # Migration environment
│   ├── env.py                  # Multi-database migration support
│   ├── script.py.mako          # Migration template
│   └── versions/               # Version-controlled migration files
│       ├── metadata/           # Shared metadata DB migrations
│       └── results/            # Per-org results DB migrations
├── models/                     # SQLAlchemy domain models
│   ├── __init__.py             # Model exports
│   ├── base.py                 # Database configuration & session management
│   ├── metadata.py             # Metadata entities (Org, User, Task, etc.)
│   └── results.py              # Results entities (Job, Execution, etc.)
├── seeds/                      # Data seeding system
│   ├── __init__.py
│   ├── system_tasks.py         # System task definitions
│   ├── organizations.py        # Default organizations and users
│   └── data/                   # JSON seed data
│       ├── system_tasks.json
│       └── pipeline_templates.json
└── scripts/                    # Database utilities with Rich CLI
    ├── migrate.py              # Migration runner (metadata & results)
    ├── seed.py                 # Data seeder with validation
    ├── backup.py               # Database backup utility
    ├── restore.py              # Database restore utility
    └── health_check.py         # Comprehensive health monitoring
```

## 🚀 Quick Start Deployment

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM available
- Ports 5432 (PostgreSQL) and 6379 (Redis) available

### Option 1: Docker Deployment (Recommended)

```bash
# 1. Navigate to database directory
cd /path/to/molecular_analysis_dashboard/database

# 2. Start all database services
make up
# OR: docker compose -f docker-compose.db.yml up -d

# 3. Run database migrations
make migrate
# Creates 22+ tables in PostgreSQL

# 4. Seed initial data (optional)
make seed
# Adds system tasks, default org, sample data

# 5. Verify deployment
make health
# Tests PostgreSQL, Redis connectivity

# 6. Check status
docker compose -f docker-compose.db.yml ps
```

### Option 2: External Database Deployment

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
export REDIS_URL="redis://host:6379/0"
export RESULTS_DB_TEMPLATE="postgresql+asyncpg://user:pass@host:5432/results_{org_id}"

# 3. Run migrations
python scripts/migrate.py --branch metadata

# 4. Seed data
python scripts/seed.py --force

# 5. Health check
python scripts/health_check.py
```

### Option 3: Local Development

```bash
# Start only database services
make up

# Use local Python environment
source venv/bin/activate  # or conda activate
pip install -r requirements.txt

# Run migrations locally
make local-migrate

# Seed local database
make local-seed

# Monitor health continuously
make health-continuous
```

## 🛠️ Management Commands

The database includes a comprehensive Makefile with all operations:

```bash
# Core Operations
make help                 # Show all available commands
make up                   # Start database services (PostgreSQL + Redis)
make down                 # Stop all database services
make restart              # Restart all services
make logs                 # Show service logs
make clean                # Remove containers and volumes

# Database Operations
make migrate              # Run metadata database migrations
make migrate-results      # Run results database migrations for org
make migrate-status       # Show current migration version
make migrate-history      # Show migration history
make migrate-down         # Downgrade one migration
make seed                 # Seed database with initial data
make seed-force           # Force reseed (replaces existing data)

# Maintenance
make health               # Run health check once
make health-continuous    # Continuous monitoring (30s intervals)
make shell                # Open PostgreSQL shell
make backup               # Backup database to file
make restore              # Restore database from backup
make reset                # Complete reset (development only)
make quick-reset          # Quick reset for development

# Development
make dev-setup            # Complete development setup
make test-migrations      # Test migration up/down cycles
make docs                 # Generate database documentation

# Local Operations (no Docker)
make local-migrate        # Run migrations on local PostgreSQL
make local-seed           # Seed local database
make local-health         # Check local database health
```

## 🔧 Configuration & Environment Variables

### Required Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DATABASE_URL` | Primary database connection | `postgresql+asyncpg://mad:mad_password@postgres:5432/mad` | `postgresql+asyncpg://user:pass@host:5432/mad_prod` |
| `REDIS_URL` | Redis connection for caching | `redis://redis:6379/0` | `redis://host:6379/1` |
| `RESULTS_DB_TEMPLATE` | Results DB template with {org_id} | `postgresql+asyncpg://mad:mad_password@postgres:5432/mad_results_{org_id}` | `postgresql+asyncpg://user:pass@host:5432/results_{org_id}` |

### Optional Configuration

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `POSTGRES_USER` | Database username | `mad` | Any valid username |
| `POSTGRES_PASSWORD` | Database password | `mad_password` | Strong password |
| `POSTGRES_DB` | Database name | `mad` | Database identifier |
| `DB_POOL_SIZE` | Connection pool size | `10` | 5-50 depending on load |
| `DB_ECHO` | SQL query logging | `false` | `true`/`false` |
| `ALEMBIC_BRANCH` | Migration branch | `metadata` | `metadata`/`results` |

### Docker Compose Configuration

**docker-compose.db.yml** includes:
- **PostgreSQL 16**: Primary database with health checks
- **Redis 7**: Caching and job queues
- **Migration Service**: Automatic schema management
- **Health Check Service**: Continuous monitoring
- **Seed Service**: Initial data population

```yaml
# Example production override
environment:
  DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:5432/${DB_NAME}
  REDIS_URL: redis://${REDIS_HOST}:6379/0
  DB_POOL_SIZE: 20
  DB_ECHO: false
```

## 🗄️ Database Schema Overview

### Metadata Database (Shared)
**22 Tables Created**

#### Core Entities
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `organizations` | Multi-tenant root entities | `org_id`, `name`, `status`, `quotas` |
| `users` | User accounts across orgs | `user_id`, `email`, `username`, `auth_data` |
| `memberships` | User-organization relationships | `user_id`, `org_id`, `role`, `permissions` |
| `roles` | Permission-based access control | `role_id`, `name`, `permissions`, `org_id` |

#### Molecular Analysis Workflow
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `task_definitions` | Reusable analysis tasks | `task_id`, `name`, `task_type`, `config` |
| `pipeline_templates` | Workflow templates | `template_id`, `name`, `steps`, `org_id` |
| `molecules` | Molecular structure metadata | `molecule_id`, `name`, `formula`, `org_id` |

#### System Management
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `audit_logs` | All system activities | `log_id`, `action`, `user_id`, `timestamp` |
| `task_services` | External service integrations | `service_id`, `name`, `config`, `status` |

### Results Database (Per-Organization)
**Dynamic per `org_id`**

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `jobs` | Docking job executions | `job_id`, `status`, `pipeline_id`, `metadata` |
| `task_executions` | Individual task runs | `execution_id`, `job_id`, `task_id`, `status` |
| `task_results` | Task execution outputs | `result_id`, `execution_id`, `data`, `confidence` |
| `job_events` | Job lifecycle tracking | `job_id`, `event`, `timestamp`, `details` |
| `docking_results` | Molecular docking outputs | `result_id`, `molecule_id`, `score`, `poses` |

## 🔄 Multi-Tenant Database Strategy

The system implements a **hybrid multi-tenant architecture**:

### Shared Metadata Database
```
mad (PostgreSQL)
├── organizations        # Tenant definitions
├── users               # Cross-tenant users
├── task_definitions    # Shared workflows
├── pipeline_templates  # Reusable pipelines
└── audit_logs         # System-wide logging
```

### Per-Organization Results Databases
```
mad_results_{org_id} (PostgreSQL)
├── jobs               # Organization-specific jobs
├── task_executions    # Private execution history
├── docking_results    # Confidential molecular data
└── job_events        # Private audit trail
```

### Benefits of This Approach
- ✅ **Complete Data Isolation**: No cross-tenant data leakage
- ✅ **Performance**: Avoid N+1 queries across organizations
- ✅ **Compliance**: Per-org data residency and retention policies
- ✅ **Scalability**: Independent scaling and backup per tenant
- ✅ **Security**: Database-level access control per organization

## ⚡ Performance & Scaling

### Connection Management
```python
# Async connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,           # Base connections
    max_overflow=20,        # Burst capacity
    pool_pre_ping=True,     # Health checks
    pool_recycle=3600       # 1-hour refresh
)
```

### Database Optimization
- **Indexes**: Primary keys, foreign keys, and query-specific indexes
- **JSONB**: Efficient storage for metadata and configuration
- **Partitioning**: Results tables partitioned by time (future)
- **Async Operations**: Non-blocking database I/O throughout

### Monitoring Queries
```sql
-- Check connection usage
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';

-- Monitor slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC;

-- Table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🛡️ Security & Safety Features

### Access Control
- **Database-Level**: PostgreSQL role-based access control
- **Application-Level**: SQLAlchemy query filtering by `org_id`
- **Connection Security**: SSL/TLS for production connections
- **Credential Management**: Environment variable configuration

### Data Protection
```python
# All queries automatically filter by organization
@org_scoped
def get_jobs(org_id: UUID) -> List[Job]:
    return session.query(Job).filter(Job.org_id == org_id).all()

# Prevents cross-tenant data access
def get_results(org_id: UUID, job_id: UUID) -> Results:
    results_db = get_results_database(org_id)  # org-specific DB
    return results_db.query(Results).filter(Results.job_id == job_id).first()
```

### Backup & Recovery
```bash
# Automated backups
make backup                    # Full database backup
make backup ORG_ID=uuid       # Organization-specific backup

# Point-in-time recovery
make restore BACKUP_FILE=backup.sql

# Migration rollback
make migrate-down             # Rollback one migration
make migrate-down STEPS=3     # Rollback 3 migrations
```

### Health Monitoring
```python
# Comprehensive health checks
- PostgreSQL connectivity and response time
- Redis connectivity and memory usage
- Database table counts and sizes
- Migration version consistency
- Connection pool utilization
- Disk space and performance metrics
```

## 🚀 Production Deployment

### Cloud Provider Deployment

#### AWS RDS + ElastiCache
```bash
# 1. Create RDS PostgreSQL instance
aws rds create-db-instance \
    --db-instance-identifier mad-prod \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --master-username maduser \
    --master-user-password "${DB_PASSWORD}" \
    --allocated-storage 100

# 2. Create ElastiCache Redis
aws elasticache create-cache-cluster \
    --cache-cluster-id mad-redis \
    --engine redis \
    --cache-node-type cache.t3.micro

# 3. Deploy database schema
export DATABASE_URL="postgresql+asyncpg://maduser:${DB_PASSWORD}@mad-prod.region.rds.amazonaws.com:5432/mad"
export REDIS_URL="redis://mad-redis.cache.amazonaws.com:6379/0"
make migrate
make seed
```

#### Google Cloud SQL + Memorystore
```bash
# 1. Create Cloud SQL instance
gcloud sql instances create mad-prod \
    --database-version=POSTGRES_16 \
    --tier=db-custom-2-4096 \
    --region=us-central1

# 2. Create Redis instance
gcloud redis instances create mad-redis \
    --size=1 \
    --region=us-central1

# 3. Deploy schema
export DATABASE_URL="postgresql+asyncpg://postgres:${DB_PASSWORD}@${SQL_IP}:5432/mad"
make migrate
```

#### Azure Database + Redis Cache
```bash
# 1. Create PostgreSQL server
az postgres server create \
    --resource-group mad-rg \
    --name mad-prod \
    --sku-name GP_Gen5_2 \
    --admin-user maduser \
    --admin-password "${DB_PASSWORD}"

# 2. Create Redis Cache
az redis create \
    --resource-group mad-rg \
    --name mad-redis \
    --location westus2 \
    --sku Basic \
    --vm-size c0

# 3. Deploy
export DATABASE_URL="postgresql+asyncpg://maduser@mad-prod:${DB_PASSWORD}@mad-prod.postgres.database.azure.com:5432/mad"
make migrate
```

### Container Orchestration

#### Docker Swarm
```yaml
# docker-stack.yml
version: '3.8'
services:
  database:
    image: mad-database:latest
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@external-db:5432/mad
      REDIS_URL: redis://external-redis:6379/0
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure

  migrate:
    image: mad-database:latest
    command: ["python", "scripts/migrate.py"]
    deploy:
      restart_policy:
        condition: none
```

#### Kubernetes
```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Job
metadata:
  name: database-migrate
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: mad-database:latest
        command: ["python", "scripts/migrate.py"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: database-url
      restartPolicy: OnFailure
```

### CI/CD Integration

#### GitHub Actions
```yaml
# .github/workflows/database.yml
name: Database Deployment
on:
  push:
    paths: ['database/**']

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run Database Migrations
      run: |
        cd database
        docker compose -f docker-compose.db.yml run --rm migrate
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
        REDIS_URL: ${{ secrets.REDIS_URL }}
```

#### GitLab CI
```yaml
# .gitlab-ci.yml
database_migrate:
  stage: deploy
  image: docker:latest
  script:
    - cd database
    - docker compose -f docker-compose.db.yml run --rm migrate
  only:
    - main
  environment:
    name: production
```

## 🔍 Testing & Validation

### Migration Testing
```bash
# Test migration up/down cycles
make test-migrations

# Manual migration testing
make migrate-down STEPS=1    # Rollback
make migrate                 # Apply again
make migrate-status          # Verify state
```

### Load Testing
```python
# scripts/load_test.py
import asyncio
import asyncpg
from concurrent.futures import ThreadPoolExecutor

async def connection_test():
    """Test database under load"""
    async def run_query():
        conn = await asyncpg.connect(DATABASE_URL)
        result = await conn.fetchval("SELECT COUNT(*) FROM organizations")
        await conn.close()
        return result

    # Simulate 100 concurrent connections
    tasks = [run_query() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    print(f"Handled {len(results)} concurrent queries")

# Run load test
python scripts/load_test.py
```

### Data Validation
```bash
# Validate data integrity
make health                           # Basic connectivity
docker exec mad-postgres psql -U mad -d mad -c "
SELECT
    schemaname,
    tablename,
    attname as column,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;
"

# Check foreign key constraints
docker exec mad-postgres psql -U mad -d mad -c "
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
"
```

## 🚨 Troubleshooting Guide

### Common Issues

#### Connection Problems
```bash
# Check if services are running
make status                    # Show service status
docker compose -f docker-compose.db.yml logs postgres
docker compose -f docker-compose.db.yml logs redis

# Test connectivity manually
docker run --rm --network database_database postgres:16 \
    psql -h postgres -U mad -d mad -c "SELECT version();"
```

#### Migration Failures
```bash
# Check migration status
make migrate-status

# View migration history
make migrate-history

# Manual migration recovery
docker compose -f docker-compose.db.yml run --rm migrate \
    alembic --config alembic.ini current --verbose

# Reset migrations (DANGER - only for development)
make reset
```

#### Performance Issues
```bash
# Check connection pool usage
docker exec mad-postgres psql -U mad -d mad -c "
SELECT
    state,
    count(*) as connections
FROM pg_stat_activity
GROUP BY state;
"

# Analyze slow queries
docker exec mad-postgres psql -U mad -d mad -c "
SELECT
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"

# Check table sizes
docker exec mad-postgres psql -U mad -d mad -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

#### Redis Issues
```bash
# Check Redis memory usage
docker exec mad-redis redis-cli info memory

# Monitor Redis operations
docker exec mad-redis redis-cli monitor

# Clear Redis cache if needed
docker exec mad-redis redis-cli flushdb
```

### Emergency Procedures

#### Database Recovery
```bash
# 1. Stop all applications first
make down

# 2. Backup current state
make backup BACKUP_FILE="emergency_backup_$(date +%Y%m%d_%H%M%S).sql"

# 3. Reset to last known good state
make restore BACKUP_FILE="last_good_backup.sql"

# 4. Restart services
make up
make health
```

#### Data Corruption Recovery
```bash
# 1. Identify corruption
docker exec mad-postgres psql -U mad -d mad -c "
SELECT schemaname, tablename
FROM pg_tables
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = tablename
);"

# 2. Rebuild affected tables
make migrate-down STEPS=5    # Rollback to before corruption
make migrate                 # Reapply migrations
make seed-force             # Restore seed data
```

## 📊 Monitoring & Observability

### Health Check Dashboard
```python
# scripts/monitoring.py - Production monitoring
import asyncio
from rich.live import Live
from rich.table import Table
from rich.console import Console

async def health_dashboard():
    """Real-time health monitoring dashboard"""
    console = Console()

    while True:
        table = Table(title="Database Health Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Response Time", justify="right")
        table.add_column("Details")

        # Check PostgreSQL
        pg_status = await check_postgres()
        table.add_row("PostgreSQL", pg_status['status'],
                     f"{pg_status['response_time']}ms",
                     f"Connections: {pg_status['connections']}")

        # Check Redis
        redis_status = await check_redis()
        table.add_row("Redis", redis_status['status'],
                     f"{redis_status['response_time']}ms",
                     f"Memory: {redis_status['memory']}")

        console.clear()
        console.print(table)
        await asyncio.sleep(5)

# Run monitoring
python scripts/monitoring.py
```

### Log Aggregation
```bash
# Centralized logging for production
docker compose -f docker-compose.db.yml logs --follow | \
    tee /var/log/mad/database.log

# Log rotation
logrotate -f /etc/logrotate.d/mad-database
```

### Metrics Collection
```python
# Integration with Prometheus/Grafana
# Add to health_check.py
def export_metrics():
    """Export database metrics for monitoring"""
    return {
        'database_connections_active': get_active_connections(),
        'database_size_bytes': get_database_size(),
        'query_response_time_ms': get_avg_response_time(),
        'redis_memory_usage_bytes': get_redis_memory(),
        'migration_version': get_current_migration(),
    }
```

## 📚 External Resources & Integration

### Compatible with:
- **ORMs**: SQLAlchemy (used), Django ORM, Prisma
- **Migration Tools**: Alembic (used), Flyway, Liquibase
- **Monitoring**: Prometheus, Grafana, DataDog, New Relic
- **Cloud Services**: AWS RDS, Google Cloud SQL, Azure Database
- **Container Platforms**: Docker, Kubernetes, OpenShift

### Integration Examples:
- **FastAPI**: Direct SQLAlchemy async session integration
- **Django**: Custom database router for multi-tenant
- **Celery**: Redis broker configuration included
- **GraphQL**: Schema introspection for auto-generated APIs
