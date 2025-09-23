# Database Testing Documentation

*Comprehensive testing strategies for the molecular analysis platform database layer.*

## Overview

This section provides complete testing methodologies for database operations, ensuring data integrity, performance, and multi-tenant security across the molecular analysis dashboard.

## Testing Components

### **[Integration Tests](integration.md)**
Database integration testing strategies and implementation
- Repository layer testing with real database connections
- Multi-tenant data isolation verification
- Transaction management and rollback testing
- Database constraint and validation testing
- Cross-service data consistency verification

### **[Performance Tests](performance.md)**
Database performance testing and optimization validation
- Load testing for concurrent molecular analysis workflows
- Query performance benchmarking and optimization
- Connection pool stress testing
- Multi-tenant performance isolation verification
- Storage and indexing performance validation

### **[Unit Tests](unit.md)**
Database unit testing patterns and mock strategies
- Repository interface mocking and testing
- Domain entity persistence testing
- Database adapter unit testing
- Query builder and ORM testing
- Migration testing strategies

## Database Testing Architecture

### Test Database Management
```python
# Test database lifecycle management
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

class DatabaseTestManager:
    def __init__(self):
        self.test_db_url = "postgresql+asyncpg://test:test@localhost/test_molecular_db"
        self.engine = create_async_engine(self.test_db_url, echo=True)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def setup_test_database(self):
        """Create and migrate test database"""
        # Run Alembic migrations
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", self.test_db_url)
        command.upgrade(alembic_cfg, "head")

        # Seed test data
        await self.seed_test_data()

    async def cleanup_test_database(self):
        """Clean up test database after tests"""
        async with self.engine.begin() as conn:
            # Drop all test data
            await conn.execute(text("TRUNCATE TABLE molecules CASCADE"))
            await conn.execute(text("TRUNCATE TABLE docking_jobs CASCADE"))
            await conn.execute(text("TRUNCATE TABLE organizations CASCADE"))

    async def seed_test_data(self):
        """Seed essential test data"""
        async with self.session_factory() as session:
            # Create test organizations
            test_orgs = [
                Organization(id=uuid4(), name="Test Org 1"),
                Organization(id=uuid4(), name="Test Org 2"),
                Organization(id=uuid4(), name="Large Org", tier="enterprise")
            ]

            for org in test_orgs:
                session.add(org)

            await session.commit()

@pytest.fixture(scope="session")
async def test_db_manager():
    """Provide test database manager for entire test session"""
    manager = DatabaseTestManager()
    await manager.setup_test_database()
    yield manager
    await manager.cleanup_test_database()

@pytest.fixture
async def db_session(test_db_manager):
    """Provide clean database session for each test"""
    async with test_db_manager.session_factory() as session:
        transaction = session.begin()
        yield session
        await transaction.rollback()
```

### Multi-Tenant Testing Framework
```python
# Multi-tenant testing utilities
class MultiTenantTestCase:
    """Base class for multi-tenant database tests"""

    def __init__(self):
        self.test_org_ids = [uuid4() for _ in range(3)]
        self.router = DatabaseRouter()

    async def setup_tenant_isolation_test(self, db_session):
        """Set up test data across multiple tenants"""

        # Create molecules for each organization
        for i, org_id in enumerate(self.test_org_ids):
            molecule = Molecule(
                id=uuid4(),
                organization_id=org_id,
                name=f"Test Molecule {i}",
                smiles=f"CCO{i}"
            )
            db_session.add(molecule)

        await db_session.commit()

    async def verify_tenant_isolation(self, db_session, org_id: UUID):
        """Verify that queries return only data for specified org"""

        # Set tenant context
        await db_session.execute(
            text("SET app.current_org_id = :org_id"),
            {"org_id": str(org_id)}
        )

        # Query molecules - should only return this org's data
        result = await db_session.execute(
            select(Molecule).where(Molecule.organization_id == org_id)
        )
        molecules = result.scalars().all()

        # Verify all results belong to the correct organization
        for molecule in molecules:
            assert molecule.organization_id == org_id

        return len(molecules)

class TestMultiTenantIsolation(MultiTenantTestCase):
    async def test_row_level_security_enforcement(self, db_session):
        """Test that RLS prevents cross-tenant data access"""

        await self.setup_tenant_isolation_test(db_session)

        for org_id in self.test_org_ids:
            count = await self.verify_tenant_isolation(db_session, org_id)
            assert count == 1  # Should only see own data

    async def test_admin_bypass_policy(self, db_session):
        """Test that admin role can access all tenant data"""

        await self.setup_tenant_isolation_test(db_session)

        # Set admin role context
        await db_session.execute(text("SET ROLE admin_role"))

        # Admin should see all molecules
        result = await db_session.execute(select(Molecule))
        molecules = result.scalars().all()

        assert len(molecules) == len(self.test_org_ids)

    async def test_tenant_data_cleanup(self, db_session):
        """Test proper tenant data deletion"""

        await self.setup_tenant_isolation_test(db_session)
        org_to_delete = self.test_org_ids[0]

        # Delete all data for one organization
        await db_session.execute(
            delete(Molecule).where(Molecule.organization_id == org_to_delete)
        )
        await db_session.commit()

        # Verify data is gone for deleted org
        result = await db_session.execute(
            select(Molecule).where(Molecule.organization_id == org_to_delete)
        )
        assert len(result.scalars().all()) == 0

        # Verify other orgs' data is intact
        for org_id in self.test_org_ids[1:]:
            result = await db_session.execute(
                select(Molecule).where(Molecule.organization_id == org_id)
            )
            assert len(result.scalars().all()) == 1
```

### Repository Testing Patterns
```python
# Repository layer testing
class TestMoleculeRepository:
    """Test cases for molecule repository implementation"""

    @pytest.fixture
    async def molecule_repo(self, db_session):
        return PostgreSQLMoleculeRepository(db_session)

    @pytest.fixture
    async def test_organization(self, db_session):
        org = Organization(id=uuid4(), name="Test Org")
        db_session.add(org)
        await db_session.commit()
        return org

    async def test_create_molecule(self, molecule_repo, test_organization):
        """Test creating a new molecule"""

        molecule_data = {
            'name': 'Aspirin',
            'smiles': 'CC(=O)OC1=CC=CC=C1C(=O)O',
            'molecular_weight': 180.16,
            'organization_id': test_organization.id
        }

        molecule = await molecule_repo.create(molecule_data)

        assert molecule.id is not None
        assert molecule.name == 'Aspirin'
        assert molecule.organization_id == test_organization.id

    async def test_find_molecules_by_organization(self, molecule_repo, test_organization):
        """Test finding molecules by organization"""

        # Create test molecules
        molecules_data = [
            {'name': 'Molecule 1', 'smiles': 'CCO', 'organization_id': test_organization.id},
            {'name': 'Molecule 2', 'smiles': 'CCC', 'organization_id': test_organization.id}
        ]

        for data in molecules_data:
            await molecule_repo.create(data)

        # Find molecules for organization
        found_molecules = await molecule_repo.find_by_organization(test_organization.id)

        assert len(found_molecules) == 2
        for molecule in found_molecules:
            assert molecule.organization_id == test_organization.id

    async def test_update_molecule(self, molecule_repo, test_organization):
        """Test updating molecule data"""

        # Create molecule
        molecule_data = {
            'name': 'Original Name',
            'smiles': 'CCO',
            'organization_id': test_organization.id
        }
        molecule = await molecule_repo.create(molecule_data)

        # Update molecule
        updated_data = {'name': 'Updated Name'}
        updated_molecule = await molecule_repo.update(molecule.id, updated_data)

        assert updated_molecule.name == 'Updated Name'
        assert updated_molecule.smiles == 'CCO'  # Unchanged

    async def test_delete_molecule(self, molecule_repo, test_organization):
        """Test deleting a molecule"""

        molecule_data = {
            'name': 'To Delete',
            'smiles': 'CCO',
            'organization_id': test_organization.id
        }
        molecule = await molecule_repo.create(molecule_data)

        # Delete molecule
        await molecule_repo.delete(molecule.id)

        # Verify deletion
        deleted_molecule = await molecule_repo.find_by_id(molecule.id)
        assert deleted_molecule is None
```

### Performance Testing Framework
```python
# Database performance testing
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor

class DatabasePerformanceTest:
    """Performance testing utilities for database operations"""

    def __init__(self, db_session):
        self.db_session = db_session
        self.results = []

    async def measure_query_performance(self, query_func, iterations=100):
        """Measure average query execution time"""

        times = []

        for _ in range(iterations):
            start_time = time.perf_counter()
            await query_func()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        return {
            'avg_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }

    async def test_concurrent_access(self, query_func, concurrent_users=10):
        """Test database performance under concurrent load"""

        async def run_user_queries():
            """Simulate user query pattern"""
            for _ in range(10):  # 10 queries per user
                await query_func()
                await asyncio.sleep(0.1)  # Brief pause between queries

        # Run concurrent user sessions
        start_time = time.perf_counter()

        tasks = [run_user_queries() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)

        end_time = time.perf_counter()

        total_time = end_time - start_time
        total_queries = concurrent_users * 10

        return {
            'total_time': total_time,
            'queries_per_second': total_queries / total_time,
            'concurrent_users': concurrent_users
        }

class TestDatabasePerformance:
    """Performance test cases"""

    async def test_molecule_search_performance(self, db_session):
        """Test performance of molecule search queries"""

        perf_test = DatabasePerformanceTest(db_session)

        # Create test data
        await self.create_performance_test_data(db_session, 1000)

        async def search_molecules():
            return await db_session.execute(
                select(Molecule).where(
                    Molecule.name.ilike('%test%')
                ).limit(10)
            )

        results = await perf_test.measure_query_performance(search_molecules)

        # Assert performance requirements
        assert results['avg_time'] < 0.1  # Less than 100ms average
        assert results['max_time'] < 0.5   # No query over 500ms

    async def test_docking_job_creation_performance(self, db_session):
        """Test performance of job creation under load"""

        perf_test = DatabasePerformanceTest(db_session)

        async def create_docking_job():
            job_data = {
                'name': f'Performance Test Job {uuid4()}',
                'status': 'pending',
                'organization_id': uuid4()
            }
            job = DockingJob(**job_data)
            db_session.add(job)
            await db_session.commit()

        results = await perf_test.test_concurrent_access(
            create_docking_job,
            concurrent_users=5
        )

        # Assert throughput requirements
        assert results['queries_per_second'] > 10  # At least 10 jobs/second

    async def create_performance_test_data(self, db_session, count):
        """Create large dataset for performance testing"""

        molecules = []
        for i in range(count):
            molecule = Molecule(
                id=uuid4(),
                name=f'Test Molecule {i}',
                smiles=f'CC(O){i}',
                organization_id=uuid4()
            )
            molecules.append(molecule)

        db_session.add_all(molecules)
        await db_session.commit()
```

## Testing Configuration

### Test Environment Setup
```yaml
# pytest.ini configuration
[tool:pytest]
asyncio_mode = auto
testpaths = tests
addopts =
    --verbose
    --cov=src/molecular_analysis_dashboard
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
    multi_tenant: Multi-tenant isolation tests

# Test database configuration
DATABASE_TEST_URL = "postgresql+asyncpg://test:test@localhost/test_molecular_db"
TEST_DATABASE_NAME = "test_molecular_db"
TEST_ISOLATION_LEVEL = "SERIALIZABLE"
```

### Continuous Integration Testing
```yaml
# .github/workflows/database-tests.yml
name: Database Tests

on: [push, pull_request]

jobs:
  database-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_USER: test
          POSTGRES_DB: test_molecular_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run database migrations
      run: |
        alembic upgrade head
      env:
        DATABASE_URL: postgresql://test:test@localhost/test_molecular_db

    - name: Run unit tests
      run: pytest tests/unit/database/ -v

    - name: Run integration tests
      run: pytest tests/integration/database/ -v

    - name: Run performance tests
      run: pytest tests/performance/database/ -v -m "not slow"

    - name: Run multi-tenant tests
      run: pytest tests/integration/database/ -v -m multi_tenant
```

## Best Practices

### Test Organization
- **Separation**: Keep unit, integration, and performance tests separate
- **Fixtures**: Use pytest fixtures for database setup and teardown
- **Isolation**: Ensure tests don't interfere with each other
- **Cleanup**: Always clean up test data after test completion
- **Mocking**: Mock external dependencies appropriately

### Performance Testing
- **Baseline**: Establish performance baselines for regression detection
- **Load Testing**: Test under realistic concurrent load
- **Monitoring**: Monitor database metrics during tests
- **Bottleneck Identification**: Profile queries to identify bottlenecks
- **Resource Usage**: Monitor memory and CPU usage during tests

### Multi-Tenant Testing
- **Isolation Verification**: Always test tenant data isolation
- **RLS Testing**: Comprehensive row-level security testing
- **Cross-Tenant**: Verify no cross-tenant data leakage
- **Admin Access**: Test admin bypass capabilities
- **Performance**: Test multi-tenant performance under load

## Related Documentation

- **[Database Design](../design/README.md)** - Schema and data model documentation
- **[Database Management](../management/README.md)** - Administration procedures
- **[Connection Routing](../connection-routing/README.md)** - Multi-tenant connection patterns
- **[Architecture Testing](../../architecture/README.md)** - Architectural testing strategies
- **[Integration Testing](../../development/guides/README.md)** - Cross-service integration testing
