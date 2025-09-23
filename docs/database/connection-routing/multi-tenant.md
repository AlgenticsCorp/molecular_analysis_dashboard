# Database Connection Management

## Overview

The application uses a **dual-database strategy** with automatic per-organization database provisioning and intelligent connection routing.

## Database Architecture

```
┌─────────────────┐    ┌─────────────────────────────────┐
│   Metadata DB   │    │        Results Databases        │
│   (Shared)      │    │        (Per-Organization)       │
├─────────────────┤    ├─────────────────────────────────┤
│ • Organizations │    │ mad_results_org1:               │
│ • Users         │    │ • docking_jobs                  │
│ • Identities    │    │ • task_results                  │
│ • Settings      │    │ • artifacts                     │
│ • Audit Logs    │    │ • input_signatures (cache)     │
│                 │    │                                 │
│                 │    │ mad_results_org2:               │
│                 │    │ • docking_jobs                  │
│                 │    │ • task_results                  │
│                 │    │ • ...                           │
└─────────────────┘    └─────────────────────────────────┘
```

## Connection Manager Implementation

### Core Connection Router

```python
# infrastructure/database.py
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """
    Manages connections to metadata DB and per-org results databases.

    Features:
    - Automatic org database creation
    - Connection pooling per database
    - Health checking and failover
    - Schema migration coordination
    """

    def __init__(self, metadata_dsn: str, results_dsn_template: str):
        self.metadata_dsn = metadata_dsn
        self.results_dsn_template = results_dsn_template

        # Engine registry: {database_name: AsyncEngine}
        self._engines: Dict[str, AsyncEngine] = {}

        # Session makers: {database_name: sessionmaker}
        self._session_makers: Dict[str, sessionmaker] = {}

        # Initialize metadata database
        self._initialize_metadata_db()

    def _initialize_metadata_db(self):
        """Initialize the shared metadata database connection."""
        # RATIONALE: metadata DB uses larger pool since it's shared across all requests
        self._engines['metadata'] = create_async_engine(
            self.metadata_dsn,
            pool_size=20,           # Higher for shared DB
            max_overflow=30,
            pool_pre_ping=True,     # Health check connections
            echo=False              # Set to True for SQL debugging
        )

        self._session_makers['metadata'] = sessionmaker(
            self._engines['metadata'],
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def get_org_engine(self, org_id: str) -> AsyncEngine:
        """
        Get or create database engine for organization.

        Args:
            org_id: Organization identifier

        Returns:
            AsyncEngine configured for the org's results database

        Raises:
            DatabaseProvisioningError: If org DB creation fails
        """
        db_key = f"results_{org_id}"

        if db_key not in self._engines:
            await self._provision_org_database(org_id)

        return self._engines[db_key]

    async def _provision_org_database(self, org_id: str):
        """
        Create and configure per-org results database.

        SECURITY: org_id is validated upstream to prevent SQL injection
        INVARIANT: each org gets isolated database with identical schema
        """
        db_name = f"mad_results_{org_id}"
        db_key = f"results_{org_id}"

        # Generate DSN for this org's database
        org_dsn = self.results_dsn_template.format(org_id=org_id)

        try:
            # Create database if it doesn't exist
            await self._create_database_if_not_exists(db_name)

            # RATIONALE: smaller pool per org since they're isolated
            self._engines[db_key] = create_async_engine(
                org_dsn,
                pool_size=5,            # Smaller per-org pools
                max_overflow=10,
                pool_pre_ping=True,
                echo=False
            )

            self._session_makers[db_key] = sessionmaker(
                self._engines[db_key],
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Run schema migrations for new org database
            await self._migrate_org_database(org_id)

            logger.info(f"Provisioned database for org {org_id}: {db_name}")

        except Exception as e:
            logger.error(f"Failed to provision database for org {org_id}: {e}")
            raise DatabaseProvisioningError(f"Cannot create database for org {org_id}") from e

    async def _create_database_if_not_exists(self, db_name: str):
        """Create PostgreSQL database if it doesn't exist."""
        # NOTE: Uses admin connection to create database
        admin_dsn = self.metadata_dsn.rsplit('/', 1)[0] + '/postgres'  # Connect to 'postgres' DB
        admin_engine = create_async_engine(admin_dsn, isolation_level="AUTOCOMMIT")

        try:
            async with admin_engine.begin() as conn:
                # Check if database exists
                result = await conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": db_name}
                )

                if not result.fetchone():
                    # Create database
                    await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                    logger.info(f"Created database: {db_name}")
        finally:
            await admin_engine.dispose()

    async def _migrate_org_database(self, org_id: str):
        """Run Alembic migrations on org's results database."""
        # TODO(#456) [@data-eng] 2025-09-10: integrate with Alembic for org DB migrations
        # For now, this is a placeholder that will run the results schema DDL
        pass

    def get_metadata_session(self) -> AsyncSession:
        """Get session for shared metadata database."""
        return self._session_makers['metadata']()

    async def get_org_session(self, org_id: str) -> AsyncSession:
        """Get session for organization's results database."""
        await self.get_org_engine(org_id)  # Ensure database exists
        db_key = f"results_{org_id}"
        return self._session_makers[db_key]()

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections."""
        health_status = {}

        # Check metadata DB
        try:
            async with self._engines['metadata'].begin() as conn:
                await conn.execute(text("SELECT 1"))
            health_status['metadata'] = True
        except Exception:
            health_status['metadata'] = False

        # Check org databases
        for db_key, engine in self._engines.items():
            if db_key.startswith('results_'):
                try:
                    async with engine.begin() as conn:
                        await conn.execute(text("SELECT 1"))
                    health_status[db_key] = True
                except Exception:
                    health_status[db_key] = False

        return health_status

    async def close_all(self):
        """Close all database connections."""
        for engine in self._engines.values():
            await engine.dispose()

        self._engines.clear()
        self._session_makers.clear()

# Custom exceptions
class DatabaseProvisioningError(Exception):
    """Raised when org database provisioning fails."""
    pass
```

### Dependency Injection Setup

```python
# infrastructure/database.py (continued)
from infrastructure.config import get_database_settings

# Global connection manager instance
_connection_manager: Optional[DatabaseConnectionManager] = None

def get_connection_manager() -> DatabaseConnectionManager:
    """Get singleton database connection manager."""
    global _connection_manager

    if _connection_manager is None:
        db_settings = get_database_settings()
        _connection_manager = DatabaseConnectionManager(
            metadata_dsn=db_settings.database_url,
            results_dsn_template=db_settings.results_db_template
        )

    return _connection_manager

# FastAPI dependency functions
async def get_metadata_session() -> AsyncSession:
    """FastAPI dependency for metadata database session."""
    manager = get_connection_manager()
    session = manager.get_metadata_session()
    try:
        yield session
    finally:
        await session.close()

async def get_org_session(org_id: str) -> AsyncSession:
    """FastAPI dependency factory for org database session."""
    manager = get_connection_manager()
    session = await manager.get_org_session(org_id)
    try:
        yield session
    finally:
        await session.close()
```

## Usage in Repository Layer

### Metadata Repository

```python
# adapters/database/metadata_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database import get_metadata_session

class OrganizationRepository:
    """Repository for organization metadata (shared database)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        """Fetch organization from metadata database."""
        # Implementation using self.session...
        pass

# Usage in API endpoint
@router.get("/organizations/{org_id}")
async def get_organization(
    org_id: str,
    metadata_session: AsyncSession = Depends(get_metadata_session)
):
    """Get organization details from metadata database."""
    repo = OrganizationRepository(metadata_session)
    org = await repo.get_by_id(org_id)
    # ... rest of endpoint logic
```

### Results Repository

```python
# adapters/database/results_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database import get_org_session

class DockingJobRepository:
    """Repository for docking jobs (per-org database)."""

    def __init__(self, session: AsyncSession, org_id: str):
        self.session = session
        self.org_id = org_id

    async def create_job(self, job_data: dict) -> DockingJob:
        """Create job in org's results database."""
        # Implementation using self.session...
        pass

# Usage in API endpoint
@router.post("/organizations/{org_id}/jobs")
async def create_docking_job(
    org_id: str,
    job_request: JobCreateRequest,
    results_session: AsyncSession = Depends(lambda: get_org_session(org_id))
):
    """Create docking job in org's dedicated database."""
    repo = DockingJobRepository(results_session, org_id)
    job = await repo.create_job(job_request.dict())
    # ... rest of endpoint logic
```

## Connection Routing Strategy

### Request-Level Routing

```python
# presentation/api/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from infrastructure.database import get_connection_manager

class DatabaseRoutingMiddleware(BaseHTTPMiddleware):
    """Middleware to set up database routing for each request."""

    async def dispatch(self, request, call_next):
        # Extract org_id from request (path param, JWT token, header, etc.)
        org_id = self._extract_org_id(request)

        if org_id:
            # Pre-warm org database connection
            manager = get_connection_manager()
            await manager.get_org_engine(org_id)  # Ensures DB exists

        response = await call_next(request)
        return response

    def _extract_org_id(self, request) -> Optional[str]:
        """Extract organization ID from request context."""
        # Check path parameters first
        if hasattr(request, 'path_params') and 'org_id' in request.path_params:
            return request.path_params['org_id']

        # Check JWT token claims
        if hasattr(request.state, 'current_user'):
            return getattr(request.state.current_user, 'org_id', None)

        return None
```

## Database Schema Migration Strategy

### Alembic Configuration

```python
# alembic/env.py (enhanced for multi-database)
from alembic import context
from infrastructure.database import get_connection_manager
from infrastructure.config import get_database_settings

def run_migrations_metadata():
    """Run migrations for shared metadata database."""
    db_settings = get_database_settings()

    with context.configure(
        url=db_settings.database_url,
        target_metadata=metadata_models.metadata,  # Metadata schema
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    ):
        with context.begin_transaction():
            context.run_migrations()

def run_migrations_results_template():
    """Run migrations for results database template."""
    # This creates the "template" that will be applied to all org databases
    db_settings = get_database_settings()
    template_url = db_settings.results_db_template.format(org_id='template')

    with context.configure(
        url=template_url,
        target_metadata=results_models.metadata,  # Results schema
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    ):
        with context.begin_transaction():
            context.run_migrations()

# Migration commands:
# alembic -n metadata upgrade head     # Migrate shared metadata DB
# alembic -n results upgrade head      # Migrate results template
```

## Health Checks Integration

```python
# presentation/api/health.py
from infrastructure.database import get_connection_manager

@router.get("/ready")
async def readiness_check():
    """Enhanced readiness check with database health."""
    manager = get_connection_manager()
    health_status = await manager.health_check()

    all_healthy = all(health_status.values())

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": {
            "databases": health_status,
            "metadata_db": health_status.get('metadata', False),
            "org_databases": {
                k: v for k, v in health_status.items()
                if k.startswith('results_')
            }
        }
    }
```

## Configuration Integration

Add to `.env`:

```bash
# Database Connection Management
DB_DATABASE_URL=postgresql+asyncpg://mad:password@postgres:5432/mad
DB_RESULTS_DB_TEMPLATE=postgresql+asyncpg://mad:password@postgres:5432/mad_results_{org_id}
DB_AUTO_CREATE_ORG_DBS=true
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_ORG_POOL_SIZE=5
DB_ORG_MAX_OVERFLOW=10
```

## Error Handling

```python
# domain/exceptions.py
class DatabaseError(Exception):
    """Base database error."""
    pass

class DatabaseProvisioningError(DatabaseError):
    """Organization database provisioning failed."""
    pass

class DatabaseConnectionError(DatabaseError):
    """Database connection failed."""
    pass

class OrganizationNotFoundError(DatabaseError):
    """Organization database not found."""
    pass
```

## Testing Strategy

```python
# tests/integration/test_database_routing.py
import pytest
from infrastructure.database import DatabaseConnectionManager

@pytest.mark.integration
async def test_org_database_provisioning():
    """Test automatic org database creation."""
    manager = DatabaseConnectionManager(
        metadata_dsn="postgresql+asyncpg://test:test@localhost/test_metadata",
        results_dsn_template="postgresql+asyncpg://test:test@localhost/test_results_{org_id}"
    )

    # Should create database automatically
    engine = await manager.get_org_engine("test_org")
    assert engine is not None

    # Should reuse existing connection
    engine2 = await manager.get_org_engine("test_org")
    assert engine is engine2

@pytest.mark.integration
async def test_connection_health_check():
    """Test database health checking."""
    manager = get_connection_manager()
    health = await manager.health_check()

    assert 'metadata' in health
    assert health['metadata'] is True
```

## Performance Considerations

1. **Connection Pooling**: Separate pools for metadata (shared, larger) vs org databases (isolated, smaller)
2. **Lazy Loading**: Org databases are created only when first accessed
3. **Health Monitoring**: Regular health checks prevent stale connections
4. **Resource Limits**: Configurable pool sizes prevent resource exhaustion
5. **Connection Reuse**: Same org_id always routes to same connection pool

## Security Considerations

1. **SQL Injection**: org_id validation prevents malicious database names
2. **Isolation**: Each org gets completely separate database
3. **Access Control**: Database-level permissions can be set per org
4. **Audit Trail**: All database operations are logged with org context
