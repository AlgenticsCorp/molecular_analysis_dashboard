# Database Performance Strategy

## Overview

This document outlines the database performance optimization strategy for the Molecular Analysis Dashboard, focusing on **efficient querying of the dynamic task registry**, **multi-tenant data isolation performance**, and **scalable database design patterns**.

## Performance Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Database Performance Strategy                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │ Query           │    │      Indexing Strategy             │  │
│  │ Optimization    │    │                                     │  │
│  │                 │    │ • Composite Indexes                │  │
│  │ • Query Plans   │    │ • JSONB GIN Indexes                │  │
│  │ • Index Usage   │    │ • Partial Indexes                  │  │
│  │ • Partitioning  │    │ • Expression Indexes               │  │
│  │ • Connection    │    │ • Foreign Key Indexes              │  │
│  │   Pooling       │    │                                     │  │
│  └─────────────────┘    └─────────────────────────────────────┘  │
│           │                            │                        │
│           ▼                            ▼                        │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │   Monitoring    │    │       Caching Strategy             │  │
│  │                 │    │                                     │  │
│  │ • Slow Queries  │    │ • Query Result Cache               │  │
│  │ • Index Usage   │    │ • Connection Pool Cache            │  │
│  │ • Lock Analysis │    │ • Prepared Statement Cache         │  │
│  │ • Performance   │    │ • Application-Level Cache          │  │
│  │   Metrics       │    │                                     │  │
│  └─────────────────┘    └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Indexing Strategy

### 1. Task Registry Performance Indexes

**Critical indexes for dynamic task system:**

```sql
-- Task registry performance indexes
CREATE INDEX CONCURRENTLY idx_task_definitions_org_active
ON task_definitions(org_id, is_active)
WHERE is_active = true;

CREATE INDEX CONCURRENTLY idx_task_definitions_category
ON task_definitions(org_id, (metadata->>'category'))
WHERE is_active = true;

CREATE INDEX CONCURRENTLY idx_task_definitions_search
ON task_definitions USING GIN((
    setweight(to_tsvector('english', metadata->>'title'), 'A') ||
    setweight(to_tsvector('english', metadata->>'description'), 'B') ||
    setweight(to_tsvector('english', array_to_string(ARRAY(SELECT jsonb_array_elements_text(metadata->'tags')), ' ')), 'C')
));

-- JSONB indexes for flexible metadata queries
CREATE INDEX CONCURRENTLY idx_task_definitions_metadata_gin
ON task_definitions USING GIN(metadata);

CREATE INDEX CONCURRENTLY idx_task_definitions_interface_gin
ON task_definitions USING GIN(interface_spec);

-- Service discovery performance
CREATE INDEX CONCURRENTLY idx_task_services_health_url
ON task_services(task_definition_id, health_status, service_url)
WHERE health_status = 'healthy';

CREATE INDEX CONCURRENTLY idx_task_services_last_check
ON task_services(last_health_check)
WHERE health_status IN ('healthy', 'starting');

-- Pipeline template performance
CREATE INDEX CONCURRENTLY idx_pipeline_templates_org_public
ON pipeline_templates(org_id, is_public, category)
WHERE is_active = true;

CREATE INDEX CONCURRENTLY idx_pipeline_steps_template_order
ON pipeline_task_steps(template_id, step_order);
```

### 2. Multi-Tenant Performance Indexes

**Optimized for organization-scoped queries:**

```sql
-- Core identity performance
CREATE INDEX CONCURRENTLY idx_users_email_enabled
ON users(email) WHERE enabled = true;

CREATE INDEX CONCURRENTLY idx_memberships_user_org
ON memberships(user_id, org_id);

CREATE INDEX CONCURRENTLY idx_membership_roles_org_user
ON membership_roles(org_id, user_id);

-- Job metadata performance (frequently queried)
CREATE INDEX CONCURRENTLY idx_jobs_meta_org_status_created
ON jobs_meta(org_id, status, created_at DESC);

CREATE INDEX CONCURRENTLY idx_jobs_meta_user_created
ON jobs_meta(submitted_by, created_at DESC);

CREATE INDEX CONCURRENTLY idx_jobs_meta_pipeline_created
ON jobs_meta(pipeline_id, created_at DESC);

-- Molecule management performance
CREATE INDEX CONCURRENTLY idx_molecules_org_created
ON molecules(org_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_molecules_org_format
ON molecules(org_id, format) WHERE format IS NOT NULL;

-- Audit log performance (write-heavy table)
CREATE INDEX CONCURRENTLY idx_audit_logs_org_ts
ON audit_logs(org_id, ts DESC);

CREATE INDEX CONCURRENTLY idx_audit_logs_user_ts
ON audit_logs(user_id, ts DESC);

CREATE INDEX CONCURRENTLY idx_audit_logs_entity
ON audit_logs(entity_type, entity_id, ts DESC);
```

### 3. Results Database Indexes (Per-Organization)

**Optimized for job execution and result queries:**

```sql
-- Job execution performance
CREATE INDEX CONCURRENTLY idx_jobs_status_created
ON jobs(status, created_at DESC);

CREATE INDEX CONCURRENTLY idx_jobs_input_signature
ON jobs(input_signature) WHERE input_signature IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_jobs_pipeline_version
ON jobs(pipeline_version, created_at DESC);

-- Task execution tracking
CREATE INDEX CONCURRENTLY idx_task_executions_job_status
ON task_executions(job_id, status);

CREATE INDEX CONCURRENTLY idx_task_executions_task_definition
ON task_executions(task_definition_id, status);

CREATE INDEX CONCURRENTLY idx_task_executions_service_url
ON task_executions(service_url, started_at DESC);

-- Dynamic task results performance
CREATE INDEX CONCURRENTLY idx_dynamic_task_results_exec
ON dynamic_task_results(exec_id);

CREATE INDEX CONCURRENTLY idx_dynamic_task_results_confidence
ON dynamic_task_results(confidence_score DESC)
WHERE confidence_score IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_dynamic_task_results_data_gin
ON dynamic_task_results USING GIN(result_data);

-- Caching performance
CREATE INDEX CONCURRENTLY idx_result_cache_pipeline_task
ON result_cache(pipeline_version, task_name, cache_key);

CREATE INDEX CONCURRENTLY idx_result_cache_expires
ON result_cache(expires_at) WHERE expires_at IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_result_cache_hit_count
ON result_cache(hit_count DESC, last_used_at DESC);

-- Job events (time-series data)
CREATE INDEX CONCURRENTLY idx_job_events_job_ts
ON job_events(job_id, ts DESC);

CREATE INDEX CONCURRENTLY idx_job_events_event_ts
ON job_events(event, ts DESC);
```

## Query Optimization Patterns

### 1. Task Registry Queries

**Optimized task discovery query:**
```sql
-- Efficient task library loading with filtering
SELECT
    td.task_definition_id,
    td.task_id,
    td.version,
    td.metadata,
    td.is_active,
    ts.service_count,
    ts.healthy_services
FROM task_definitions td
LEFT JOIN (
    SELECT
        task_definition_id,
        COUNT(*) as service_count,
        COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy_services
    FROM task_services
    GROUP BY task_definition_id
) ts ON td.task_definition_id = ts.task_definition_id
WHERE td.org_id = $1
    AND td.is_active = true
    AND ($2::text IS NULL OR td.metadata->>'category' = $2)
ORDER BY td.metadata->>'title';
```

**Task search with full-text search:**
```sql
-- Full-text search across task metadata
SELECT
    task_definition_id,
    task_id,
    metadata,
    ts_rank(search_vector, query) as rank
FROM (
    SELECT *,
        setweight(to_tsvector('english', metadata->>'title'), 'A') ||
        setweight(to_tsvector('english', metadata->>'description'), 'B') ||
        setweight(to_tsvector('english', array_to_string(ARRAY(SELECT jsonb_array_elements_text(metadata->'tags')), ' ')), 'C') as search_vector
    FROM task_definitions
    WHERE org_id = $1 AND is_active = true
) t, plainto_tsquery('english', $2) query
WHERE search_vector @@ query
ORDER BY rank DESC, metadata->>'title';
```

### 2. Service Discovery Queries

**Healthy service discovery:**
```sql
-- Find healthy service for task execution
SELECT
    ts.service_id,
    ts.service_url,
    ts.pod_name,
    ts.resources_used,
    ts.last_health_check
FROM task_services ts
JOIN task_definitions td ON ts.task_definition_id = td.task_definition_id
WHERE td.org_id = $1
    AND td.task_id = $2
    AND td.version = $3
    AND ts.health_status = 'healthy'
    AND ts.last_health_check > NOW() - INTERVAL '2 minutes'
ORDER BY (ts.resources_used->>'cpu')::numeric ASC  -- Load balancing
LIMIT 1;
```

### 3. Pipeline Composition Queries

**Pipeline template with task details:**
```sql
-- Load pipeline template with full task information
WITH pipeline_steps AS (
    SELECT
        pts.template_id,
        pts.step_order,
        pts.step_name,
        pts.depends_on,
        pts.parameter_overrides,
        td.task_id,
        td.metadata,
        td.interface_spec
    FROM pipeline_task_steps pts
    JOIN task_definitions td ON pts.task_definition_id = td.task_definition_id
    WHERE pts.template_id = $1
    ORDER BY pts.step_order
)
SELECT
    pt.template_id,
    pt.name,
    pt.description,
    pt.workflow_definition,
    pt.default_parameters,
    jsonb_agg(
        jsonb_build_object(
            'step_order', ps.step_order,
            'step_name', ps.step_name,
            'task_id', ps.task_id,
            'task_metadata', ps.metadata,
            'depends_on', ps.depends_on,
            'parameter_overrides', ps.parameter_overrides
        ) ORDER BY ps.step_order
    ) as steps
FROM pipeline_templates pt
LEFT JOIN pipeline_steps ps ON pt.template_id = ps.template_id
WHERE pt.template_id = $1 AND pt.org_id = $2
GROUP BY pt.template_id, pt.name, pt.description, pt.workflow_definition, pt.default_parameters;
```

## Connection Management

### 1. Connection Pooling Configuration

**AsyncPG Pool Settings:**
```python
# infrastructure/database.py
DATABASE_POOL_CONFIG = {
    # Connection pool sizing
    "min_size": 5,          # Minimum connections in pool
    "max_size": 20,         # Maximum connections in pool (per database)

    # Connection timeouts
    "timeout": 30,          # Connection acquisition timeout (seconds)
    "command_timeout": 60,  # Individual query timeout (seconds)
    "server_settings": {
        "jit": "off",                    # Disable JIT for faster connection
        "application_name": "mad_api"    # Application identifier
    },

    # Connection lifecycle
    "max_lifetime": 3600,   # Max connection lifetime (1 hour)
    "max_idle": 600,        # Max idle time before closure (10 minutes)

    # Performance tuning
    "record_class": Record,  # Use optimized record class
    "loop": None,           # Use current event loop
}

# Multi-database connection management
class DatabaseManager:
    def __init__(self):
        self.metadata_pool = None
        self.results_pools = {}  # org_id -> connection pool

    async def get_metadata_connection(self):
        """Get connection to shared metadata database."""
        if not self.metadata_pool:
            self.metadata_pool = await create_pool(
                METADATA_DATABASE_URL,
                **DATABASE_POOL_CONFIG
            )
        return await self.metadata_pool.acquire()

    async def get_results_connection(self, org_id: str):
        """Get connection to organization results database."""
        if org_id not in self.results_pools:
            results_url = RESULTS_DATABASE_URL.format(org_id=org_id)
            self.results_pools[org_id] = await create_pool(
                results_url,
                **DATABASE_POOL_CONFIG
            )
        return await self.results_pools[org_id].acquire()
```

### 2. Query Performance Monitoring

**Query performance tracking:**
```python
# adapters/database/performance_monitor.py
import time
import logging
from typing import Dict, Any
from functools import wraps

class QueryPerformanceMonitor:
    """Monitor database query performance."""

    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 second

    def monitor_query(self, query_name: str):
        """Decorator to monitor query performance."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Log slow queries
                    if execution_time > self.slow_query_threshold:
                        logging.warning(
                            f"Slow query detected: {query_name} took {execution_time:.2f}s"
                        )

                    # Update query statistics
                    self._update_stats(query_name, execution_time)

                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logging.error(
                        f"Query failed: {query_name} after {execution_time:.2f}s - {e}"
                    )
                    raise

            return wrapper
        return decorator

    def _update_stats(self, query_name: str, execution_time: float):
        """Update query performance statistics."""
        if query_name not in self.query_stats:
            self.query_stats[query_name] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "max_time": 0
            }

        stats = self.query_stats[query_name]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["max_time"] = max(stats["max_time"], execution_time)

# Usage in repository adapters
monitor = QueryPerformanceMonitor()

class TaskRegistryAdapter:
    @monitor.monitor_query("get_task_library")
    async def get_task_library(self, org_id: str, filters: Dict[str, Any]) -> List[TaskDefinition]:
        # Query implementation with monitoring
        pass
```

## Caching Strategy

### 1. Application-Level Caching

**Redis-based query result caching:**
```python
# infrastructure/cache.py
import json
import hashlib
from typing import Optional, Any, Dict
from redis.asyncio import Redis

class QueryCache:
    """Redis-based query result caching."""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes

    async def get_cached_result(
        self,
        cache_key: str,
        query_func,
        *args,
        ttl: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Get cached result or execute query and cache result."""
        # Try to get from cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Execute query and cache result
        result = await query_func(*args, **kwargs)
        await self.redis.setex(
            cache_key,
            ttl or self.default_ttl,
            json.dumps(result, default=str)
        )
        return result

    def generate_cache_key(self, prefix: str, **params) -> str:
        """Generate deterministic cache key from parameters."""
        key_data = f"{prefix}:{json.dumps(params, sort_keys=True)}"
        return f"query:{hashlib.md5(key_data.encode()).hexdigest()}"

# Usage in adapters
class TaskRegistryAdapter:
    def __init__(self, session: AsyncSession, cache: QueryCache):
        self.session = session
        self.cache = cache

    async def get_task_library(self, org_id: str, filters: Dict[str, Any]) -> List[TaskDefinition]:
        """Get task library with caching."""
        cache_key = self.cache.generate_cache_key(
            "task_library",
            org_id=org_id,
            **filters
        )

        return await self.cache.get_cached_result(
            cache_key,
            self._fetch_task_library,
            org_id,
            filters,
            ttl=600  # 10 minutes for task library
        )
```

### 2. Database-Level Optimizations

**Prepared statement caching:**
```python
# infrastructure/prepared_statements.py
class PreparedStatementManager:
    """Manage prepared statements for frequently used queries."""

    def __init__(self):
        self.statements = {}

    async def prepare_common_statements(self, connection):
        """Prepare frequently used statements."""
        # Task library query
        self.statements["task_library"] = await connection.prepare("""
            SELECT task_definition_id, task_id, version, metadata, is_active
            FROM task_definitions
            WHERE org_id = $1 AND is_active = true
            ORDER BY metadata->>'title'
        """)

        # Service discovery query
        self.statements["healthy_services"] = await connection.prepare("""
            SELECT service_url, resources_used
            FROM task_services ts
            JOIN task_definitions td ON ts.task_definition_id = td.task_definition_id
            WHERE td.org_id = $1 AND td.task_id = $2
                AND ts.health_status = 'healthy'
            ORDER BY (ts.resources_used->>'cpu')::numeric
        """)

        # Job status query
        self.statements["job_status"] = await connection.prepare("""
            SELECT job_id, status, created_at, updated_at
            FROM jobs
            WHERE job_id = $1
        """)
```

## Performance Monitoring

### 1. Database Metrics Collection

**PostgreSQL performance monitoring:**
```sql
-- Query to monitor slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE mean_time > 100  -- Queries taking more than 100ms on average
ORDER BY mean_time DESC
LIMIT 20;

-- Index usage monitoring
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan < 10  -- Potentially unused indexes
ORDER BY idx_scan;

-- Table size monitoring
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY bytes DESC;
```

### 2. Application Metrics

**Performance metrics collection:**
```python
# infrastructure/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Database metrics
DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_name', 'database']
)

DB_CONNECTION_POOL_SIZE = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    ['database', 'status']  # status: active, idle
)

DB_QUERY_ERRORS = Counter(
    'db_query_errors_total',
    'Database query errors',
    ['query_name', 'error_type']
)

# Task registry metrics
TASK_REGISTRY_QUERIES = Counter(
    'task_registry_queries_total',
    'Task registry query count',
    ['operation', 'org_id']
)

TASK_EXECUTION_REQUESTS = Counter(
    'task_execution_requests_total',
    'Task execution request count',
    ['task_id', 'org_id', 'status']
)

# Cache metrics
CACHE_HITS = Counter(
    'cache_hits_total',
    'Cache hit count',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Cache miss count',
    ['cache_type']
)
```

## Optimization Recommendations

### 1. Query Optimization Checklist

**Pre-deployment checklist:**
- [ ] All frequently used queries have appropriate indexes
- [ ] JSONB queries use GIN indexes where appropriate
- [ ] Multi-tenant queries include org_id in WHERE clause
- [ ] Pagination implemented for large result sets
- [ ] Query plans analyzed for efficiency
- [ ] Connection pooling configured appropriately
- [ ] Slow query monitoring enabled
- [ ] Cache strategy implemented for frequent queries

### 2. Performance Testing Strategy

**Load testing scenarios:**
```python
# tests/performance/task_registry_load_test.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def load_test_task_library():
    """Load test task library endpoint."""
    url = "http://localhost:8000/api/v1/task-registry/tasks"
    headers = {"Authorization": "Bearer <test-token>"}

    async with aiohttp.ClientSession() as session:
        tasks = []
        start_time = time.time()

        # Simulate 100 concurrent requests
        for i in range(100):
            task = session.get(url, headers=headers)
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        print(f"100 requests completed in {duration:.2f} seconds")
        print(f"Average response time: {duration/100:.3f} seconds")

        # Verify all responses are successful
        for resp in responses:
            assert resp.status == 200

if __name__ == "__main__":
    asyncio.run(load_test_task_library())
```

This comprehensive database performance strategy ensures:

1. **Efficient task registry queries** with proper indexing
2. **Optimized multi-tenant data access** patterns
3. **Scalable connection management** across databases
4. **Comprehensive performance monitoring** and alerting
5. **Effective caching strategies** for frequent operations
6. **Load testing frameworks** for performance validation

The strategy provides a solid foundation for high-performance operation of the dynamic task system at scale.
