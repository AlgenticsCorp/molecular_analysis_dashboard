# Database Management Documentation

*Database administration, operations, performance optimization, and maintenance procedures.*

## Overview

This section covers comprehensive database management including setup procedures, migration management, performance optimization, data seeding strategies, and operational maintenance for the PostgreSQL-based molecular analysis system.

## Management Components

### **[Database Setup](database-setup.md)**
Complete database setup and configuration procedures
- PostgreSQL installation and configuration
- Docker-based database deployment
- Environment-specific setup procedures
- Initial database configuration and optimization

### **[Migration Management](migrations.md)**
Alembic-based database migration strategies and procedures
- Migration creation and versioning
- Migration execution and rollback procedures
- Schema evolution best practices
- Migration testing and validation

### **[Performance Optimization](performance.md)**
Database performance tuning and optimization strategies
- Query optimization and index management
- Connection pooling and resource management
- Monitoring and performance analysis
- Scaling strategies for high-load scenarios

### **[Data Seeding](data-seeding.md)**
Test data generation and database seeding strategies
- Development data seeding procedures
- Test fixture creation and management
- Production data migration strategies
- Data anonymization and privacy protection

## Database Operations

### PostgreSQL Configuration
```bash
# Docker-based PostgreSQL setup
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: molecular_dashboard
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    command: >
      postgres
      -c shared_preload_libraries=pg_stat_statements
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=4MB
      -c maintenance_work_mem=64MB
```

### Connection Management
```python
# SQLAlchemy async engine configuration
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Production-optimized connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False  # Set to True for debugging
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Migration Management
```bash
# Alembic migration workflow
# 1. Generate new migration
alembic revision --autogenerate -m "Add molecular_weight column"

# 2. Review generated migration
# Edit alembic/versions/xxx_add_molecular_weight.py

# 3. Test migration in development
alembic upgrade head

# 4. Validate migration results
psql molecular_dashboard -c "\d molecules"

# 5. Apply to staging/production
docker compose exec postgres alembic upgrade head
```

## Performance Management

### Query Optimization
```sql
-- Enable query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Monitor slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC
LIMIT 10;

-- Analyze query plans
EXPLAIN (ANALYZE, BUFFERS)
SELECT m.*, j.status
FROM molecules m
JOIN docking_jobs j ON m.id = j.molecule_id
WHERE m.organization_id = $1;
```

### Index Management
```sql
-- Monitor index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_tup_read = 0;

-- Create performance-critical indexes
CREATE INDEX CONCURRENTLY idx_molecules_org_created
ON molecules(organization_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_jobs_status_priority
ON docking_jobs(status, priority DESC)
WHERE status IN ('pending', 'running');
```

### Monitoring and Maintenance
```bash
# Database health monitoring script
#!/bin/bash
# scripts/db-health-check.sh

DB_NAME="molecular_dashboard"
ALERT_THRESHOLD=80

# Check connection count
CONNECTIONS=$(psql -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='$DB_NAME';")
MAX_CONNECTIONS=$(psql -t -c "SHOW max_connections;")
CONNECTION_PCT=$((CONNECTIONS * 100 / MAX_CONNECTIONS))

if [ $CONNECTION_PCT -gt $ALERT_THRESHOLD ]; then
    echo "ALERT: High connection usage: ${CONNECTION_PCT}%"
fi

# Check database size
DB_SIZE=$(psql -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));")
echo "Database size: $DB_SIZE"

# Check for long-running queries
LONG_QUERIES=$(psql -t -c "
SELECT count(*)
FROM pg_stat_activity
WHERE state = 'active'
AND query_start < NOW() - INTERVAL '5 minutes';")

if [ $LONG_QUERIES -gt 0 ]; then
    echo "ALERT: $LONG_QUERIES long-running queries detected"
fi

# Check replication lag (if applicable)
# Check for bloated tables
# Check for missing indexes
```

## Backup and Recovery

### Automated Backup Strategy
```bash
# Backup script with retention
#!/bin/bash
# scripts/backup-database.sh

BACKUP_DIR="/backups/postgresql"
RETENTION_DAYS=30
DB_NAME="molecular_dashboard"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -h postgres -U admin -d $DB_NAME | gzip > \
    "$BACKUP_DIR/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"

# Organization-specific backups for multi-tenancy
for org_id in $(psql -t -c "SELECT id FROM organizations;"); do
    pg_dump -h postgres -U admin -d $DB_NAME \
        --where="organization_id='$org_id'" \
        --data-only | gzip > \
        "$BACKUP_DIR/org_backup_${org_id}_${TIMESTAMP}.sql.gz"
done

# Clean old backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "org_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
```

### Point-in-Time Recovery
```bash
# Enable continuous archiving
# In postgresql.conf:
archive_mode = on
archive_command = 'cp %p /archive/%f'
wal_level = replica

# Create base backup
pg_basebackup -D /backup/base -Ft -z -P

# Recovery from backup
# 1. Stop PostgreSQL
# 2. Restore base backup
# 3. Create recovery.conf
# 4. Start PostgreSQL in recovery mode
```

## Data Management

### Data Seeding for Development
```python
# Development data seeding
from faker import Faker
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

fake = Faker()

async def seed_development_data(session: AsyncSession):
    """Seed database with realistic development data"""

    # Create test organizations
    organizations = []
    for i in range(3):
        org = Organization(
            name=fake.company(),
            created_at=fake.date_time_this_year()
        )
        session.add(org)
        organizations.append(org)

    await session.commit()

    # Create test users for each organization
    for org in organizations:
        for j in range(fake.random_int(5, 15)):
            user = User(
                email=fake.email(),
                organization_id=org.id,
                role=fake.random_element(['user', 'admin']),
                created_at=fake.date_time_this_year()
            )
            session.add(user)

    await session.commit()

    # Create test molecules
    molecules = []
    for org in organizations:
        for k in range(fake.random_int(50, 200)):
            molecule = Molecule(
                name=fake.word().title() + fake.random_element(['ine', 'ol', 'ate']),
                smiles=generate_random_smiles(),
                organization_id=org.id,
                molecular_weight=fake.random.uniform(100.0, 800.0),
                created_at=fake.date_time_this_year()
            )
            session.add(molecule)
            molecules.append(molecule)

    await session.commit()

def generate_random_smiles() -> str:
    """Generate realistic SMILES strings for testing"""
    # Implementation for generating valid SMILES
    pass
```

### Data Migration and ETL
```python
# Data migration utilities
import pandas as pd
from sqlalchemy import text

async def migrate_legacy_data(session: AsyncSession, csv_file: str):
    """Migrate data from legacy CSV format"""

    df = pd.read_csv(csv_file)

    # Validate and clean data
    df = df.dropna(subset=['name', 'smiles'])
    df['molecular_weight'] = pd.to_numeric(df['molecular_weight'], errors='coerce')

    # Batch insert for performance
    batch_size = 1000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]

        values = []
        for _, row in batch.iterrows():
            values.append({
                'name': row['name'],
                'smiles': row['smiles'],
                'molecular_weight': row['molecular_weight'],
                'organization_id': row['organization_id']
            })

        await session.execute(
            text("""
                INSERT INTO molecules (name, smiles, molecular_weight, organization_id)
                VALUES (:name, :smiles, :molecular_weight, :organization_id)
            """),
            values
        )

        await session.commit()
        print(f"Migrated batch {i//batch_size + 1}")
```

## Multi-Tenant Management

### Organization Database Isolation
```python
# Per-organization database connections
class MultiTenantDatabaseManager:
    def __init__(self):
        self.engines = {}
        self.sessions = {}

    async def get_org_session(self, org_id: str) -> AsyncSession:
        """Get database session for specific organization"""
        if org_id not in self.engines:
            # Create dedicated engine for large organizations
            if await self.is_large_organization(org_id):
                engine = create_async_engine(
                    f"postgresql+asyncpg://user:pass@db/{org_id}_results"
                )
                self.engines[org_id] = engine
            else:
                # Use shared engine with row-level security
                self.engines[org_id] = shared_engine

        session = AsyncSession(self.engines[org_id])

        # Set organization context for row-level security
        await session.execute(
            text("SET app.current_org_id = :org_id"),
            {"org_id": org_id}
        )

        return session
```

### Data Partitioning Strategy
```sql
-- Partition large tables by organization
CREATE TABLE job_results_partitioned (
    id UUID DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    job_id UUID NOT NULL,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (organization_id);

-- Create partitions for each organization
CREATE TABLE job_results_org_1 PARTITION OF job_results_partitioned
FOR VALUES WITH (modulus 4, remainder 0);

CREATE TABLE job_results_org_2 PARTITION OF job_results_partitioned
FOR VALUES WITH (modulus 4, remainder 1);
```

## Troubleshooting

### Common Database Issues
```bash
# Check database locks
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

# Kill long-running queries
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
AND query_start < NOW() - INTERVAL '10 minutes';

# Check table bloat
SELECT
    schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Related Documentation

- **[Database Design](../design/README.md)** - Schema and data model documentation
- **[Connection Routing](../connection-routing/README.md)** - Multi-tenant connection patterns
- **[Database Testing](../testing/README.md)** - Testing strategies and procedures
- **[System Architecture](../../architecture/system-design/README.md)** - Overall system context
- **[Deployment Configuration](../../deployment/README.md)** - Database deployment procedures
