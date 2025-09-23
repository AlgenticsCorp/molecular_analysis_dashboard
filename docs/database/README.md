# 🗄️ Database Documentation

This section contains comprehensive documentation for the Molecular Analysis Dashboard database architecture, implementing a multi-tenant system with clean separation between shared metadata and organization-specific results.

## 🏗️ **Database Architecture Overview**

The system implements a **hybrid multi-tenant architecture** with:
- **Metadata Database**: Shared organizational data (users, tasks, templates)
- **Results Databases**: Per-organization data isolation (jobs, results, artifacts)
- **Redis**: Caching and job queuing
- **Clean Architecture**: Domain-driven design with ports & adapters

```
Metadata DB (Shared)     Results DBs (Per-Org)
┌─────────────────┐    ┌─────────────────┐
│ organizations    │    │ jobs (org_a)     │
│ users            │    │ executions       │
│ task_definitions │    │ docking_results  │
│ pipelines        │    │ job_events       │
│ audit_logs       │    └─────────────────┘
└─────────────────┘    ┌─────────────────┐
                     │ jobs (org_b)     │
                     │ executions       │
                     │ docking_results  │
                     │ job_events       │
                     └─────────────────┘
```

## 🗂️ **Database Sections**

### **[Design](design/README.md)**
Database schema, ERD, and architectural patterns
- **[Schema Overview](design/schema.md)** - Complete database schema with ERD diagrams
- **[Multi-Tenant Design](design/multi-tenant.md)** - Hybrid multi-tenancy implementation
- **[Performance Design](design/performance.md)** - Indexing, partitioning, and optimization
- **[Data Types](design/data-types.md)** - Custom types, constraints, and validation

### **[Management](management/README.md)**
Database operations, migrations, and maintenance
- **[Migration Guide](management/migrations.md)** - Alembic migrations for multi-database setup
- **[Seeding Data](management/seeding.md)** - Initial data population and fixtures
- **[Backup & Recovery](management/backup-recovery.md)** - Database backup strategies
- **[Monitoring](management/monitoring.md)** - Health checks and performance monitoring

### **[Connection Routing](connection-routing/README.md)**
Multi-tenant database routing and connection management
- **[Router Architecture](connection-routing/router.md)** - Database connection routing system
- **[Session Management](connection-routing/sessions.md)** - Async session handling
- **[Organization Isolation](connection-routing/isolation.md)** - Data isolation strategies
- **[Performance Tuning](connection-routing/performance.md)** - Connection pooling and optimization

### **[Testing](testing/README.md)**
Database testing strategies and utilities
- **[Test Database Setup](testing/setup.md)** - Isolated test database configuration
- **[Migration Testing](testing/migrations.md)** - Migration up/down cycle testing
- **[Load Testing](testing/load-testing.md)** - Database performance under load
- **[Data Integrity](testing/integrity.md)** - Constraint and consistency testing

---

## 🚀 **Quick Start**

### **Deploy Database System**
```bash
# Navigate to database directory
cd database/

# Start all database services
make up

# Run migrations (creates 22+ tables)
make migrate

# Seed initial data
make seed

# Verify health
make health
```

### **Connect to Database**
```python
# Multi-database connection example
from database.router import DatabaseRouter

# Initialize router
db_router = DatabaseRouter()

# Metadata operations
async with db_router.get_metadata_session() as session:
    orgs = await session.execute(
        select(Organization).where(Organization.status == 'active')
    )

# Organization-specific operations
async with db_router.get_results_session(org_id) as session:
    jobs = await session.execute(
        select(Job).where(Job.status == 'completed')
    )
```

## 📋 **Database Statistics**

### **Schema Summary**
- **Metadata Tables**: 22 shared tables across organizations
- **Results Tables**: 8 tables per organization (dynamically created)
- **Custom Types**: 3 PostgreSQL enums for data consistency
- **Indexes**: 15+ performance-optimized indexes
- **Constraints**: 25+ data validation constraints

### **Key Features**
- ✅ **Complete Data Isolation**: Per-organization results databases
- ✅ **Async Operations**: Non-blocking database I/O throughout
- ✅ **Performance Optimized**: Strategic indexing and connection pooling
- ✅ **Migration Management**: Alembic-based versioning for multi-database
- ✅ **Backup Strategy**: Automated backup for metadata and per-org results
- ✅ **Security**: Row-level security and data classification

## 🔄 **Common Operations**

### **Multi-Tenant Queries**
```sql
-- Get organization summary with job counts
SELECT
    o.name as org_name,
    COUNT(jm.job_id) as total_jobs,
    o.quotas->>'max_concurrent_jobs' as job_limit
FROM organizations o
LEFT JOIN jobs_meta jm ON o.org_id = jm.org_id
GROUP BY o.org_id, o.name, o.quotas;

-- Cross-database job analysis (requires application logic)
-- 1. Get job metadata from shared DB
-- 2. Get job details from org-specific results DB
-- 3. Combine results in application layer
```

### **Performance Monitoring**
```sql
-- Monitor connection usage
SELECT
    datname,
    state,
    count(*) as connections
FROM pg_stat_activity
WHERE datname LIKE 'mad%'
GROUP BY datname, state;

-- Check database sizes
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datname LIKE 'mad%'
ORDER BY pg_database_size(datname) DESC;
```

## 🔐 **Security Features**

### **Access Control**
- **Database-Level**: PostgreSQL role-based access control
- **Application-Level**: SQLAlchemy query filtering by `org_id`
- **Row-Level Security**: Automatic org-scoped data access
- **Connection Security**: SSL/TLS for production connections

### **Data Protection**
- **Multi-Tenant Isolation**: Complete database separation per organization
- **Audit Logging**: Comprehensive activity tracking
- **Sensitive Data**: Proper classification and handling
- **Backup Encryption**: Encrypted backups for sensitive data

## 🛠️ **Management Tools**

### **Available Commands**
```bash
# Database lifecycle
make up                    # Start database services
make down                  # Stop database services
make migrate              # Run metadata migrations
make migrate-results      # Run results migrations
make seed                 # Populate initial data
make health               # Check database health

# Maintenance operations
make backup               # Backup all databases
make restore              # Restore from backup
make shell                # Open PostgreSQL shell
make reset                # Complete reset (dev only)

# Monitoring
make health-continuous    # Continuous health monitoring
make logs                 # View service logs
```

### **Health Monitoring**
```bash
# Real-time health dashboard
make health-continuous

# Example output:
# ┌──────────────────────────────┐
# │      Database Health Status     │
# ├──────────────────────────────┤
# │ PostgreSQL   ✅ Healthy  8ms   │
# │ Redis        ✅ Healthy  2ms   │
# │ Metadata DB  ✅ Ready    12ms  │
# │ Results DBs  ✅ Ready    15ms  │
# └──────────────────────────────┘
```

## 🔗 **Related Documentation**

- [System Architecture](../architecture/README.md) - Overall system design
- [API Contracts](../api/README.md) - Database-API integration patterns
- [Deployment Guide](../deployment/README.md) - Production database deployment
- [Development Setup](../development/README.md) - Local database development

## 📚 **External Resources**

### **Technologies Used**
- **PostgreSQL 16**: Primary relational database
- **Redis 7**: Caching and job queuing
- **SQLAlchemy 2.0**: Python ORM with async support
- **Alembic**: Database migration management
- **Docker**: Containerized database services

### **Learning Resources**
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Async Tutorial](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Multi-Tenant Database Patterns](https://docs.microsoft.com/en-us/azure/sql-database/saas-tenancy-app-design-patterns)
- [Database Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

---

For questions about database operations or architecture, refer to the specific documentation sections above or the [troubleshooting guide](management/troubleshooting.md).
