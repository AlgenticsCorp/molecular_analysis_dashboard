# Multi-Tenant Connection Routing Documentation

*Database connection management and routing strategies for multi-tenant molecular analysis platform.*

## Overview

This section documents the multi-tenant connection routing architecture that enables organization-based data isolation while maintaining performance and security across the molecular analysis dashboard.

## Connection Routing Components

### **[Multi-Tenant Architecture](multi-tenant.md)**
Comprehensive multi-tenant database connection and data isolation strategies
- Organization-based connection routing patterns
- Row-level security implementation
- Database per-tenant vs shared database strategies
- Connection pooling for multi-tenant scenarios
- Performance optimization for tenant isolation

## Multi-Tenant Patterns

### Hybrid Multi-Tenancy Model
```
┌─────────────────────────────────────┐
│          Shared Metadata           │ ← Users, orgs, system config
│        (Single Database)           │
├─────────────────────────────────────┤
│      Medium Organizations          │ ← Row-level security
│     (Shared with RLS)             │   (10-1000 users per org)
├─────────────────────────────────────┤
│      Large Organizations           │ ← Dedicated databases
│   (Dedicated Databases)           │   (1000+ users per org)
└─────────────────────────────────────┘
```

### Connection Routing Architecture
```python
# Dynamic connection routing based on organization
class DatabaseRouter:
    def __init__(self):
        self.shared_engine = create_async_engine(SHARED_DB_URL)
        self.dedicated_engines = {}

    async def get_connection(self, org_id: str) -> AsyncEngine:
        org_config = await self.get_org_config(org_id)

        if org_config.has_dedicated_db:
            return await self.get_dedicated_engine(org_id)
        else:
            return self.shared_engine

    async def execute_with_tenant_context(self, org_id: str, query: str):
        engine = await self.get_connection(org_id)

        async with engine.begin() as conn:
            # Set tenant context for row-level security
            await conn.execute(text("SET app.current_org_id = :org_id"),
                             {"org_id": org_id})

            result = await conn.execute(text(query))
            return result
```

### Row-Level Security Implementation
```sql
-- Enable RLS for multi-tenant tables
ALTER TABLE molecules ENABLE ROW LEVEL SECURITY;
ALTER TABLE docking_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_results ENABLE ROW LEVEL SECURITY;

-- Create tenant isolation policies
CREATE POLICY tenant_isolation_molecules ON molecules
FOR ALL TO app_role
USING (organization_id = current_setting('app.current_org_id')::uuid);

CREATE POLICY tenant_isolation_jobs ON docking_jobs
FOR ALL TO app_role
USING (organization_id = current_setting('app.current_org_id')::uuid);

-- Admin bypass policy for system operations
CREATE POLICY admin_bypass_molecules ON molecules
FOR ALL TO admin_role
USING (true);
```

## Performance Optimization

### Connection Pool Management
```python
# Tenant-aware connection pooling
from sqlalchemy.pool import QueuePool
import asyncio

class TenantConnectionPoolManager:
    def __init__(self):
        self.pools = {}
        self.pool_configs = {
            'small_tenant': {'pool_size': 5, 'max_overflow': 10},
            'medium_tenant': {'pool_size': 10, 'max_overflow': 20},
            'large_tenant': {'pool_size': 20, 'max_overflow': 40}
        }

    async def get_pool(self, org_id: str) -> QueuePool:
        if org_id not in self.pools:
            org_size = await self.get_org_size(org_id)
            config = self.pool_configs.get(org_size, self.pool_configs['small_tenant'])

            self.pools[org_id] = create_async_engine(
                await self.get_db_url(org_id),
                poolclass=QueuePool,
                **config
            )

        return self.pools[org_id]
```

### Query Optimization for Multi-Tenancy
```sql
-- Optimized indexes for tenant queries
CREATE INDEX idx_molecules_org_id_created ON molecules(organization_id, created_at DESC);
CREATE INDEX idx_jobs_org_id_status ON docking_jobs(organization_id, status);

-- Partial indexes for active data
CREATE INDEX idx_active_jobs_org ON docking_jobs(organization_id, created_at)
WHERE status IN ('pending', 'running');

-- Covering indexes for common queries
CREATE INDEX idx_molecules_org_covering ON molecules(organization_id, id, name, created_at);
```

## Security and Isolation

### Data Isolation Verification
```python
# Automated testing of tenant isolation
import pytest
from sqlalchemy import text

class TestTenantIsolation:
    async def test_row_level_security(self, db_session):
        """Verify RLS prevents cross-tenant data access"""

        # Create test data for two organizations
        org1_id = uuid4()
        org2_id = uuid4()

        # Set context for org1
        await db_session.execute(
            text("SET app.current_org_id = :org_id"),
            {"org_id": str(org1_id)}
        )

        # Query should only return org1 data
        result = await db_session.execute(text("SELECT * FROM molecules"))
        molecules = result.fetchall()

        for molecule in molecules:
            assert molecule.organization_id == org1_id

    async def test_connection_routing(self):
        """Verify correct database routing per tenant"""
        router = DatabaseRouter()

        # Small org should use shared database
        small_org_engine = await router.get_connection("small-org-id")
        assert small_org_engine == router.shared_engine

        # Large org should use dedicated database
        large_org_engine = await router.get_connection("large-org-id")
        assert large_org_engine != router.shared_engine
```

### Audit and Compliance
```sql
-- Tenant access logging
CREATE TABLE tenant_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    user_id UUID NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    row_count INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Trigger function for automatic logging
CREATE OR REPLACE FUNCTION log_tenant_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO tenant_access_log (
        organization_id, user_id, table_name, operation, row_count
    ) VALUES (
        current_setting('app.current_org_id')::uuid,
        current_setting('app.current_user_id')::uuid,
        TG_TABLE_NAME,
        TG_OP,
        CASE WHEN TG_OP = 'SELECT' THEN NEW.row_count ELSE 1 END
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
```

## Migration and Maintenance

### Tenant Migration Strategies
```python
# Migrate tenant from shared to dedicated database
async def migrate_tenant_to_dedicated_db(org_id: str):
    """Migrate large tenant to dedicated database"""

    # 1. Create new dedicated database
    dedicated_db_url = f"postgresql://user:pass@host/{org_id}_db"
    dedicated_engine = create_async_engine(dedicated_db_url)

    # 2. Run schema migrations on new database
    await run_alembic_migrations(dedicated_engine)

    # 3. Copy tenant data from shared database
    await copy_tenant_data(org_id, dedicated_engine)

    # 4. Update tenant configuration
    await update_tenant_config(org_id, has_dedicated_db=True)

    # 5. Verify data integrity
    await verify_migration_integrity(org_id, dedicated_engine)

    # 6. Clean up shared database (optional)
    await cleanup_shared_tenant_data(org_id)

async def copy_tenant_data(org_id: str, target_engine: AsyncEngine):
    """Copy all tenant data to dedicated database"""

    tables = ['molecules', 'docking_jobs', 'job_results', 'pipelines']

    for table in tables:
        # Export from shared database
        query = f"""
        COPY (SELECT * FROM {table} WHERE organization_id = '{org_id}')
        TO '/tmp/{table}_{org_id}.csv' CSV HEADER
        """
        await shared_engine.execute(text(query))

        # Import to dedicated database
        query = f"""
        COPY {table} FROM '/tmp/{table}_{org_id}.csv' CSV HEADER
        """
        await target_engine.execute(text(query))
```

### Monitoring and Alerting
```python
# Tenant-specific monitoring
class TenantMonitor:
    async def check_tenant_performance(self, org_id: str):
        """Monitor tenant-specific performance metrics"""

        engine = await self.router.get_connection(org_id)

        metrics = {
            'connection_count': await self.get_connection_count(engine),
            'query_performance': await self.get_avg_query_time(engine, org_id),
            'storage_usage': await self.get_storage_usage(engine, org_id),
            'active_jobs': await self.get_active_job_count(engine, org_id)
        }

        # Check thresholds and alert if needed
        if metrics['connection_count'] > self.thresholds['max_connections']:
            await self.send_alert(f"High connection usage for org {org_id}")

        return metrics
```

## Best Practices

### Connection Management
- **Pool Sizing**: Size connection pools based on tenant activity
- **Connection Lifecycle**: Implement proper connection cleanup
- **Failover**: Configure automatic failover for dedicated databases
- **Monitoring**: Monitor connection usage per tenant
- **Resource Limits**: Set appropriate resource limits per tenant

### Security Considerations
- **RLS Enforcement**: Always enable row-level security for shared tables
- **Context Setting**: Ensure tenant context is set for every query
- **Access Logging**: Log all tenant data access for compliance
- **Encryption**: Enable encryption in transit and at rest
- **Backup Isolation**: Separate backup strategies per tenant

### Performance Optimization
- **Index Strategy**: Create tenant-aware indexes
- **Query Planning**: Optimize queries for multi-tenant scenarios
- **Cache Partitioning**: Partition cache by tenant
- **Resource Allocation**: Allocate resources based on tenant size
- **Monitoring**: Implement tenant-specific performance monitoring

## Related Documentation

- **[Database Design](../design/README.md)** - Schema and data model documentation
- **[Database Management](../management/README.md)** - Administration procedures
- **[Database Testing](../testing/README.md)** - Testing multi-tenant scenarios
- **[Security Architecture](../../security/README.md)** - Security policies and implementation
- **[API Authentication](../../api/README.md)** - API-level tenant isolation
