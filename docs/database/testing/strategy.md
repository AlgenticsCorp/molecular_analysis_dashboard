# Database Testing Strategy

## Overview

This document outlines the comprehensive database testing strategy for the Molecular Analysis Dashboard, focusing on **multi-tenant data isolation**, **dynamic task system validation**, and **database migration testing** across different environments.

## Testing Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Database Testing Strategy                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │ Unit Tests      │    │      Integration Tests             │  │
│  │                 │    │                                     │  │
│  │ • Repository    │    │ • Multi-tenant Isolation           │  │
│  │   Logic         │    │ • Cross-database Operations        │  │
│  │ • Entity        │    │ • Task Registry Workflows          │  │
│  │   Validation    │    │ • Pipeline Composition             │  │
│  │ • Adapter       │    │ • Service Discovery                │  │
│  │   Behavior      │    │                                     │  │
│  └─────────────────┘    └─────────────────────────────────────┘  │
│           │                            │                        │
│           ▼                            ▼                        │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │ Migration Tests │    │      Performance Tests             │  │
│  │                 │    │                                     │  │
│  │ • Schema        │    │ • Query Performance                │  │
│  │   Evolution     │    │ • Connection Pool Stress           │  │
│  │ • Data          │    │ • Concurrent Access                │  │
│  │   Migration     │    │ • Load Testing                     │  │
│  │ • Rollback      │    │                                     │  │
│  │   Safety        │    │                                     │  │
│  └─────────────────┘    └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Test Environment Setup

### 1. Test Database Configuration

**Docker Compose for Testing:**
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  postgres_test:
    image: postgres:15
    environment:
      POSTGRES_DB: mad_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    volumes:
      - postgres_test_data:/var/lib/postgresql/data
      - ./tests/fixtures/sql:/docker-entrypoint-initdb.d
    tmpfs:
      - /tmp
    command: >
      postgres
        -c shared_preload_libraries=pg_stat_statements
        -c pg_stat_statements.track=all
        -c log_statement=all
        -c log_duration=on

  redis_test:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    tmpfs:
      - /data

volumes:
  postgres_test_data:
```

**Test Database Manager:**
```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from src.molecular_analysis_dashboard.infrastructure.database import Base

class TestDatabaseManager:
    """Manages test database lifecycle."""

    def __init__(self):
        self.postgres_container = None
        self.redis_container = None
        self.metadata_engine = None
        self.results_engines = {}

    async def setup(self):
        """Setup test database containers."""
        # Start PostgreSQL container
        self.postgres_container = PostgresContainer("postgres:15")
        self.postgres_container.start()

        # Start Redis container
        self.redis_container = RedisContainer("redis:7-alpine")
        self.redis_container.start()

        # Create database engines
        postgres_url = self.postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
        self.metadata_engine = create_async_engine(postgres_url + "_metadata")

        # Create database schemas
        await self._create_test_databases()

    async def teardown(self):
        """Cleanup test resources."""
        if self.metadata_engine:
            await self.metadata_engine.dispose()

        for engine in self.results_engines.values():
            await engine.dispose()

        if self.postgres_container:
            self.postgres_container.stop()

        if self.redis_container:
            self.redis_container.stop()

    async def _create_test_databases(self):
        """Create test database schemas."""
        # Create metadata database schema
        async with self.metadata_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def create_org_database(self, org_id: str):
        """Create organization-specific test database."""
        postgres_url = self.postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
        org_engine = create_async_engine(f"{postgres_url}_results_{org_id}")

        # Create results schema
        async with org_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.results_engines[org_id] = org_engine
        return org_engine

@pytest.fixture(scope="session")
async def test_db_manager():
    """Provide test database manager."""
    manager = TestDatabaseManager()
    await manager.setup()
    yield manager
    await manager.teardown()

@pytest.fixture
async def metadata_session(test_db_manager):
    """Provide metadata database session."""
    async_session = sessionmaker(
        test_db_manager.metadata_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def results_session(test_db_manager, test_org_id):
    """Provide results database session."""
    org_engine = await test_db_manager.create_org_database(test_org_id)
    async_session = sessionmaker(
        org_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()
```

## Unit Testing Strategy

### 1. Repository Layer Tests

**Task Registry Repository Tests:**
```python
# tests/unit/adapters/database/test_task_registry.py
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.molecular_analysis_dashboard.domain.entities.task_definition import TaskDefinition
from src.molecular_analysis_dashboard.adapters.database.task_registry import TaskRegistryAdapter

class TestTaskRegistryAdapter:
    """Test task registry database operations."""

    @pytest.fixture
    async def task_registry(self, metadata_session: AsyncSession):
        """Provide task registry adapter."""
        return TaskRegistryAdapter(metadata_session)

    @pytest.fixture
    def sample_task_definition(self, test_org_id: str):
        """Provide sample task definition."""
        return TaskDefinition(
            org_id=test_org_id,
            task_id="test-docking",
            version="1.0.0",
            metadata={
                "title": "Test Docking",
                "description": "Test molecular docking task",
                "category": "Analysis"
            },
            interface_spec={
                "openapi": "3.0.0",
                "paths": {
                    "/execute": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "protein_file": {"type": "string"},
                                                "ligand_file": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            service_config={
                "docker_image": "test/docking:v1.0.0",
                "resources": {"cpu": "1000m", "memory": "2Gi"}
            },
            is_system=False,
            is_active=True
        )

    async def test_create_task_definition(
        self,
        task_registry: TaskRegistryAdapter,
        sample_task_definition: TaskDefinition
    ):
        """Test creating a task definition."""
        # Act
        created_task = await task_registry.create_task_definition(sample_task_definition)

        # Assert
        assert created_task.task_definition_id is not None
        assert created_task.task_id == "test-docking"
        assert created_task.version == "1.0.0"
        assert created_task.metadata["title"] == "Test Docking"

    async def test_get_task_definition(
        self,
        task_registry: TaskRegistryAdapter,
        sample_task_definition: TaskDefinition
    ):
        """Test retrieving a task definition."""
        # Arrange
        created_task = await task_registry.create_task_definition(sample_task_definition)

        # Act
        retrieved_task = await task_registry.get_task_definition(
            created_task.org_id,
            created_task.task_id,
            created_task.version
        )

        # Assert
        assert retrieved_task is not None
        assert retrieved_task.task_definition_id == created_task.task_definition_id
        assert retrieved_task.interface_spec == created_task.interface_spec

    async def test_get_task_library_with_filters(
        self,
        task_registry: TaskRegistryAdapter,
        test_org_id: str
    ):
        """Test getting task library with category filter."""
        # Arrange - Create multiple tasks
        tasks = [
            TaskDefinition(
                org_id=test_org_id,
                task_id=f"task-{i}",
                version="1.0.0",
                metadata={"title": f"Task {i}", "category": category},
                interface_spec={"openapi": "3.0.0"},
                service_config={},
                is_active=True
            )
            for i, category in enumerate(["Analysis", "Analysis", "Visualization"])
        ]

        for task in tasks:
            await task_registry.create_task_definition(task)

        # Act
        analysis_tasks = await task_registry.get_task_library(
            test_org_id,
            filters={"category": "Analysis"}
        )

        # Assert
        assert len(analysis_tasks) == 2
        for task in analysis_tasks:
            assert task.metadata["category"] == "Analysis"

    async def test_multi_tenant_isolation(
        self,
        task_registry: TaskRegistryAdapter
    ):
        """Test that task definitions are isolated by organization."""
        # Arrange
        org1_id = str(uuid4())
        org2_id = str(uuid4())

        task1 = TaskDefinition(
            org_id=org1_id,
            task_id="shared-task",
            version="1.0.0",
            metadata={"title": "Org 1 Task"},
            interface_spec={"openapi": "3.0.0"},
            service_config={},
            is_active=True
        )

        task2 = TaskDefinition(
            org_id=org2_id,
            task_id="shared-task",
            version="1.0.0",
            metadata={"title": "Org 2 Task"},
            interface_spec={"openapi": "3.0.0"},
            service_config={},
            is_active=True
        )

        await task_registry.create_task_definition(task1)
        await task_registry.create_task_definition(task2)

        # Act
        org1_tasks = await task_registry.get_task_library(org1_id)
        org2_tasks = await task_registry.get_task_library(org2_id)

        # Assert
        assert len(org1_tasks) == 1
        assert len(org2_tasks) == 1
        assert org1_tasks[0].metadata["title"] == "Org 1 Task"
        assert org2_tasks[0].metadata["title"] == "Org 2 Task"
```

### 2. Entity Validation Tests

**Task Definition Entity Tests:**
```python
# tests/unit/domain/entities/test_task_definition.py
import pytest
from pydantic import ValidationError

from src.molecular_analysis_dashboard.domain.entities.task_definition import TaskDefinition

class TestTaskDefinition:
    """Test task definition entity validation."""

    def test_valid_task_definition(self):
        """Test creating a valid task definition."""
        task = TaskDefinition(
            org_id="org-123",
            task_id="valid-task",
            version="1.0.0",
            metadata={"title": "Valid Task"},
            interface_spec={"openapi": "3.0.0"},
            service_config={"docker_image": "test:v1.0.0"},
            is_active=True
        )

        assert task.task_id == "valid-task"
        assert task.is_active is True

    def test_invalid_task_id_format(self):
        """Test task ID validation."""
        with pytest.raises(ValidationError) as exc_info:
            TaskDefinition(
                org_id="org-123",
                task_id="Invalid Task ID!",  # Invalid characters
                version="1.0.0",
                metadata={"title": "Task"},
                interface_spec={"openapi": "3.0.0"},
                service_config={},
                is_active=True
            )

        assert "task_id" in str(exc_info.value)

    def test_openapi_spec_validation(self):
        """Test OpenAPI specification validation."""
        with pytest.raises(ValidationError):
            TaskDefinition(
                org_id="org-123",
                task_id="test-task",
                version="1.0.0",
                metadata={"title": "Task"},
                interface_spec={},  # Missing required OpenAPI fields
                service_config={},
                is_active=True
            )

    def test_version_format_validation(self):
        """Test semantic version validation."""
        valid_versions = ["1.0.0", "2.1.3", "0.0.1-alpha"]
        invalid_versions = ["1.0", "v1.0.0", "1.0.0.0", "invalid"]

        for version in valid_versions:
            task = TaskDefinition(
                org_id="org-123",
                task_id="test-task",
                version=version,
                metadata={"title": "Task"},
                interface_spec={"openapi": "3.0.0"},
                service_config={},
                is_active=True
            )
            assert task.version == version

        for version in invalid_versions:
            with pytest.raises(ValidationError):
                TaskDefinition(
                    org_id="org-123",
                    task_id="test-task",
                    version=version,
                    metadata={"title": "Task"},
                    interface_spec={"openapi": "3.0.0"},
                    service_config={},
                    is_active=True
                )
```

## Integration Testing Strategy

### 1. Multi-Tenant Isolation Tests

**Cross-Organization Data Access Tests:**
```python
# tests/integration/test_multi_tenant_isolation.py
import pytest
from uuid import uuid4

from src.molecular_analysis_dashboard.adapters.database.task_registry import TaskRegistryAdapter
from src.molecular_analysis_dashboard.adapters.database.organization import OrganizationAdapter

class TestMultiTenantIsolation:
    """Test multi-tenant data isolation."""

    @pytest.fixture
    async def organizations(self, metadata_session):
        """Create test organizations."""
        org_adapter = OrganizationAdapter(metadata_session)

        org1 = await org_adapter.create_organization({
            "name": "Organization 1",
            "status": "active"
        })

        org2 = await org_adapter.create_organization({
            "name": "Organization 2",
            "status": "active"
        })

        return org1, org2

    async def test_task_definition_isolation(
        self,
        metadata_session,
        organizations
    ):
        """Test that task definitions are isolated between organizations."""
        org1, org2 = organizations
        task_registry = TaskRegistryAdapter(metadata_session)

        # Create task in org1
        org1_task = await task_registry.create_task_definition(TaskDefinition(
            org_id=org1.org_id,
            task_id="shared-name",
            version="1.0.0",
            metadata={"title": "Org 1 Task"},
            interface_spec={"openapi": "3.0.0"},
            service_config={},
            is_active=True
        ))

        # Create task with same ID in org2
        org2_task = await task_registry.create_task_definition(TaskDefinition(
            org_id=org2.org_id,
            task_id="shared-name",
            version="1.0.0",
            metadata={"title": "Org 2 Task"},
            interface_spec={"openapi": "3.0.0"},
            service_config={},
            is_active=True
        ))

        # Verify isolation
        org1_tasks = await task_registry.get_task_library(org1.org_id)
        org2_tasks = await task_registry.get_task_library(org2.org_id)

        assert len(org1_tasks) == 1
        assert len(org2_tasks) == 1
        assert org1_tasks[0].metadata["title"] == "Org 1 Task"
        assert org2_tasks[0].metadata["title"] == "Org 2 Task"

        # Verify cross-org access fails
        org1_task_from_org2 = await task_registry.get_task_definition(
            org2.org_id, "shared-name", "1.0.0"
        )
        assert org1_task_from_org2.metadata["title"] == "Org 2 Task"  # Not org1's task

    async def test_results_database_isolation(
        self,
        organizations,
        test_db_manager
    ):
        """Test that results databases are isolated between organizations."""
        org1, org2 = organizations

        # Create separate results databases
        org1_engine = await test_db_manager.create_org_database(org1.org_id)
        org2_engine = await test_db_manager.create_org_database(org2.org_id)

        # Create sessions for each org
        from sqlalchemy.orm import sessionmaker
        Session1 = sessionmaker(org1_engine, class_=AsyncSession)
        Session2 = sessionmaker(org2_engine, class_=AsyncSession)

        # Test that databases are separate
        async with Session1() as session1, Session2() as session2:
            # Insert data in org1 database
            await session1.execute(text("""
                INSERT INTO jobs (job_id, pipeline_version, status)
                VALUES ('job1', '1.0.0', 'COMPLETED')
            """))
            await session1.commit()

            # Verify data exists in org1 but not org2
            org1_result = await session1.execute(text("SELECT COUNT(*) FROM jobs"))
            org2_result = await session2.execute(text("SELECT COUNT(*) FROM jobs"))

            assert org1_result.scalar() == 1
            assert org2_result.scalar() == 0
```

### 2. Pipeline Composition Tests

**Task Dependency Resolution Tests:**
```python
# tests/integration/test_pipeline_composition.py
import pytest

from src.molecular_analysis_dashboard.adapters.database.pipeline_template import PipelineTemplateAdapter
from src.molecular_analysis_dashboard.use_cases.pipeline.compose_pipeline import ComposePipelineUseCase

class TestPipelineComposition:
    """Test pipeline composition with dynamic tasks."""

    async def test_pipeline_task_dependency_resolution(
        self,
        metadata_session,
        test_org_id
    ):
        """Test that pipeline task dependencies are resolved correctly."""
        # Create pipeline template adapter
        pipeline_adapter = PipelineTemplateAdapter(metadata_session)

        # Create pipeline template with task dependencies
        pipeline_template = await pipeline_adapter.create_pipeline_template({
            "org_id": test_org_id,
            "name": "protein-analysis-pipeline",
            "description": "Multi-step protein analysis",
            "category": "Analysis",
            "workflow_definition": {
                "type": "DAG",
                "steps": [
                    {
                        "id": "step1",
                        "task_id": "file-converter",
                        "depends_on": []
                    },
                    {
                        "id": "step2",
                        "task_id": "molecular-docking",
                        "depends_on": ["step1"]
                    },
                    {
                        "id": "step3",
                        "task_id": "molecular-visualization",
                        "depends_on": ["step2"]
                    }
                ]
            }
        })

        # Test dependency resolution
        compose_use_case = ComposePipelineUseCase(pipeline_adapter)
        resolved_pipeline = await compose_use_case.resolve_pipeline_dependencies(
            pipeline_template.template_id
        )

        # Verify dependency order
        assert len(resolved_pipeline.execution_order) == 3
        assert resolved_pipeline.execution_order[0].task_id == "file-converter"
        assert resolved_pipeline.execution_order[1].task_id == "molecular-docking"
        assert resolved_pipeline.execution_order[2].task_id == "molecular-visualization"

    async def test_circular_dependency_detection(
        self,
        metadata_session,
        test_org_id
    ):
        """Test that circular dependencies are detected and rejected."""
        pipeline_adapter = PipelineTemplateAdapter(metadata_session)

        # Create pipeline with circular dependency
        with pytest.raises(ValueError, match="Circular dependency detected"):
            await pipeline_adapter.create_pipeline_template({
                "org_id": test_org_id,
                "name": "circular-pipeline",
                "description": "Pipeline with circular dependency",
                "category": "Analysis",
                "workflow_definition": {
                    "type": "DAG",
                    "steps": [
                        {
                            "id": "step1",
                            "task_id": "task-a",
                            "depends_on": ["step2"]  # Circular dependency
                        },
                        {
                            "id": "step2",
                            "task_id": "task-b",
                            "depends_on": ["step1"]  # Circular dependency
                        }
                    ]
                }
            })
```

## Migration Testing Strategy

### 1. Migration Validation Tests

**Schema Migration Tests:**
```python
# tests/integration/test_migrations.py
import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

class TestMigrations:
    """Test database migration functionality."""

    @pytest.fixture
    def alembic_config(self, test_db_manager):
        """Provide Alembic configuration for testing."""
        config = Config()
        config.set_main_option("script_location", "alembic")
        config.set_main_option(
            "sqlalchemy.url",
            test_db_manager.metadata_engine.url
        )
        return config

    async def test_migration_upgrade_downgrade(self, alembic_config):
        """Test migration upgrade and downgrade operations."""
        # Get migration scripts
        script_dir = ScriptDirectory.from_config(alembic_config)
        revisions = list(script_dir.walk_revisions())

        # Test each migration
        for revision in reversed(revisions):  # Start from first migration
            # Upgrade to this revision
            command.upgrade(alembic_config, revision.revision)

            # Verify migration was applied
            current_revision = command.current(alembic_config)
            assert current_revision == revision.revision

            # Test downgrade (if has down_revision)
            if revision.down_revision:
                command.downgrade(alembic_config, revision.down_revision)
                current_revision = command.current(alembic_config)
                assert current_revision == revision.down_revision

                # Upgrade back for next test
                command.upgrade(alembic_config, revision.revision)

    async def test_migration_data_preservation(
        self,
        alembic_config,
        metadata_session
    ):
        """Test that migrations preserve existing data."""
        # Insert test data before migration
        await metadata_session.execute(text("""
            INSERT INTO organizations (org_id, name, status)
            VALUES ('test-org', 'Test Org', 'active')
        """))
        await metadata_session.commit()

        # Run migration
        command.upgrade(alembic_config, "head")

        # Verify data still exists
        result = await metadata_session.execute(text("""
            SELECT name FROM organizations WHERE org_id = 'test-org'
        """))

        assert result.scalar() == "Test Org"

    async def test_concurrent_migration_safety(self, alembic_config):
        """Test that migrations are safe under concurrent access."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_migration():
            try:
                command.upgrade(alembic_config, "head")
                return True
            except Exception as e:
                return str(e)

        # Run multiple concurrent migrations
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(run_migration)
                for _ in range(3)
            ]

            results = [future.result() for future in futures]

        # At least one should succeed, others should handle gracefully
        successes = sum(1 for result in results if result is True)
        assert successes >= 1
```

### 2. Data Migration Tests

**System Task Seeding Tests:**
```python
# tests/integration/test_data_seeding.py
import pytest

from scripts.seeders.system_tasks import SystemTaskSeeder
from src.molecular_analysis_dashboard.adapters.database.task_registry import TaskRegistryAdapter

class TestDataSeeding:
    """Test data seeding operations."""

    async def test_system_task_seeding(
        self,
        metadata_session,
        test_org_id
    ):
        """Test that system tasks are seeded correctly."""
        task_registry = TaskRegistryAdapter(metadata_session)
        seeder = SystemTaskSeeder(metadata_session)

        # Run seeding
        await seeder.seed_system_tasks(test_org_id)

        # Verify system tasks were created
        tasks = await task_registry.get_task_library(test_org_id)
        system_tasks = [t for t in tasks if t.is_system]

        assert len(system_tasks) >= 3  # Minimum expected system tasks

        # Verify specific system tasks
        task_ids = {t.task_id for t in system_tasks}
        assert "molecular-docking" in task_ids
        assert "molecular-visualization" in task_ids

        # Verify task specifications are valid
        docking_task = next(t for t in system_tasks if t.task_id == "molecular-docking")
        assert "openapi" in docking_task.interface_spec
        assert "docker_image" in docking_task.service_config

    async def test_seeding_idempotency(
        self,
        metadata_session,
        test_org_id
    ):
        """Test that seeding can be run multiple times safely."""
        task_registry = TaskRegistryAdapter(metadata_session)
        seeder = SystemTaskSeeder(metadata_session)

        # Run seeding twice
        await seeder.seed_system_tasks(test_org_id)
        initial_count = len(await task_registry.get_task_library(test_org_id))

        await seeder.seed_system_tasks(test_org_id)  # Run again
        final_count = len(await task_registry.get_task_library(test_org_id))

        # Should not create duplicates
        assert initial_count == final_count
```

## Performance Testing Strategy

### 1. Load Testing

**Database Load Tests:**
```python
# tests/performance/test_database_load.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestDatabaseLoad:
    """Test database performance under load."""

    async def test_concurrent_task_library_queries(
        self,
        metadata_session,
        test_org_id
    ):
        """Test concurrent access to task library."""
        task_registry = TaskRegistryAdapter(metadata_session)

        async def query_task_library():
            start_time = time.time()
            tasks = await task_registry.get_task_library(test_org_id)
            duration = time.time() - start_time
            return len(tasks), duration

        # Run 50 concurrent queries
        tasks = [query_task_library() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        # Verify all queries succeeded
        assert len(results) == 50

        # Check performance metrics
        durations = [duration for _, duration in results]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        assert avg_duration < 0.5  # Average under 500ms
        assert max_duration < 2.0  # Max under 2 seconds

    async def test_connection_pool_stress(self, test_db_manager):
        """Test connection pool under stress."""
        async def create_session_and_query():
            async with test_db_manager.metadata_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar()

        # Create more concurrent requests than pool size
        tasks = [create_session_and_query() for _ in range(100)]
        start_time = time.time()

        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify all queries succeeded
        assert all(result == 1 for result in results)
        assert total_time < 10.0  # Should complete within 10 seconds
```

## Test Data Management

### 1. Test Fixtures

**Comprehensive Test Data Setup:**
```python
# tests/fixtures/test_data.py
import pytest
from uuid import uuid4

@pytest.fixture
def test_org_id():
    """Provide consistent test organization ID."""
    return str(uuid4())

@pytest.fixture
async def test_organization(metadata_session, test_org_id):
    """Create test organization."""
    from src.molecular_analysis_dashboard.adapters.database.organization import OrganizationAdapter

    org_adapter = OrganizationAdapter(metadata_session)
    return await org_adapter.create_organization({
        "org_id": test_org_id,
        "name": "Test Organization",
        "status": "active",
        "quotas": {
            "max_jobs_per_month": 1000,
            "max_storage_gb": 100
        }
    })

@pytest.fixture
async def test_user(metadata_session, test_org_id):
    """Create test user."""
    from src.molecular_analysis_dashboard.adapters.database.user import UserAdapter

    user_adapter = UserAdapter(metadata_session)
    return await user_adapter.create_user({
        "email": "test@example.com",
        "org_id": test_org_id,
        "enabled": True
    })

@pytest.fixture
async def test_tasks(metadata_session, test_org_id):
    """Create test task definitions."""
    from scripts.seeders.system_tasks import SystemTaskSeeder

    seeder = SystemTaskSeeder(metadata_session)
    await seeder.seed_system_tasks(test_org_id)

    task_registry = TaskRegistryAdapter(metadata_session)
    return await task_registry.get_task_library(test_org_id)
```

### 2. Test Data Cleanup

**Automatic Test Cleanup:**
```python
# tests/conftest.py
@pytest.fixture(autouse=True)
async def cleanup_test_data(metadata_session):
    """Automatically cleanup test data after each test."""
    yield  # Run the test

    # Cleanup in reverse dependency order
    await metadata_session.execute(text("DELETE FROM pipeline_task_steps"))
    await metadata_session.execute(text("DELETE FROM pipeline_templates"))
    await metadata_session.execute(text("DELETE FROM task_services"))
    await metadata_session.execute(text("DELETE FROM task_definitions"))
    await metadata_session.execute(text("DELETE FROM membership_roles"))
    await metadata_session.execute(text("DELETE FROM memberships"))
    await metadata_session.execute(text("DELETE FROM users"))
    await metadata_session.execute(text("DELETE FROM organizations"))

    await metadata_session.commit()
```

This comprehensive database testing strategy ensures:

1. **Multi-tenant data isolation** is properly validated
2. **Dynamic task system** functions correctly across scenarios
3. **Database migrations** are safe and preserve data
4. **Performance requirements** are met under load
5. **Test data management** is automated and consistent
6. **Integration testing** covers cross-database operations

The strategy provides confidence that the database layer will perform reliably in production environments.
