# Developer Guide: Architecture, Standards & Workflow

This comprehensive guide covers architecture patterns, quality standards, and development workflows for the Molecular Analysis Dashboard. Designed for clarity, safe changes, and productivity.

## 🏗️ **Architecture Overview**

### **Clean Architecture (Ports & Adapters)**

We use a strict **Ports & Adapters** structure for maintainability and testability:

```
src/molecular_analysis_dashboard/
├── domain/          # Pure business logic (entities, domain services)
├── use_cases/       # Application services (orchestration)
├── ports/           # Abstract interfaces (contracts)
├── adapters/        # Implementations (database, external APIs)
├── infrastructure/  # Dependency injection, configuration
├── presentation/    # HTTP routes, CLI, workers (thin I/O)
└── shared/          # Small cross-cutting utilities
```

### **Layer Responsibilities**

#### **Domain Layer** (`domain/`)
```python
# domain/entities/molecule.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Molecule:
    """Core business entity representing a molecular structure."""
    id: Optional[str]
    name: str
    smiles: Optional[str]
    mol_block: Optional[str]

    def validate_structure(self) -> bool:
        """Domain rule: validate molecular structure."""
        return bool(self.smiles or self.mol_block)
```

**Rules**:
- ✅ Pure Python objects with no external dependencies
- ✅ Contains business rules and invariants
- ✅ Framework-agnostic entities and value objects

#### **Use Cases Layer** (`use_cases/`)
```python
# use_cases/commands/create_docking_job.py
from domain.entities import DockingJob
from ports.repository import JobRepositoryPort

class CreateDockingJobUseCase:
    def __init__(self, job_repository: JobRepositoryPort):
        self._job_repository = job_repository

    async def execute(self, command: CreateDockingJobCommand) -> DockingJob:
        # 1. Validate business rules
        if not command.molecule.validate_structure():
            raise InvalidMoleculeError("Invalid molecular structure")

        # 2. Create domain entity
        job = DockingJob.create(
            molecule=command.molecule,
            target=command.target
        )

        # 3. Persist via port
        return await self._job_repository.save(job)
```

**Rules**:
- ✅ Orchestrates domain entities
- ✅ Depends only on domain and ports (abstractions)
- ✅ Contains application-specific business rules
- ❌ No knowledge of frameworks or external systems

#### **Ports Layer** (`ports/`)
```python
# ports/repository/job_repository_port.py
from abc import ABC, abstractmethod
from typing import Optional
from domain.entities import DockingJob

class JobRepositoryPort(ABC):
    """Port defining contract for job persistence."""

    @abstractmethod
    async def save(self, job: DockingJob) -> DockingJob:
        """Persist a docking job."""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[DockingJob]:
        """Retrieve job by ID."""
        pass
```

**Rules**:
- ✅ Abstract Base Classes or Protocols
- ✅ Define stable contracts between layers
- ✅ Enable dependency inversion
- ✅ Support testing with mocks

#### **Adapters Layer** (`adapters/`)
```python
# adapters/database/postgresql_job_repository.py
from ports.repository import JobRepositoryPort
from domain.entities import DockingJob

class PostgreSQLJobRepository(JobRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, job: DockingJob) -> DockingJob:
        # Map domain entity to SQLAlchemy model
        model = JobModel.from_entity(job)
        self._session.add(model)
        await self._session.commit()
        return model.to_entity()
```

**Rules**:
- ✅ Implements port interfaces
- ✅ Contains framework-specific code
- ✅ Maps between domain and external representations
- ✅ Can be swapped without affecting business logic

## 📏 **Code Quality Standards**

### **SOLID Principles**

We enforce **SOLID principles** for maintainable code:

- **S**ingle Responsibility: Each class has one reason to change
- **O**pen/Closed: Open for extension, closed for modification
- **L**iskov Substitution: Subtypes must be substitutable for base types
- **I**nterface Segregation: Clients shouldn't depend on unused interfaces
- **D**ependency Inversion: Depend on abstractions, not concretions

### **Documentation Requirements**

All public APIs **must** have comprehensive docstrings:

#### **Module Documentation** (top of file):
```python
"""
Molecular docking job management.

This module provides use cases for creating, executing, and monitoring
molecular docking jobs using various computational engines.

Dependencies:
- Domain entities (Molecule, DockingJob)
- Repository ports for persistence
- External docking engine adapters

Limitations:
- Currently supports only single-target docking
- Requires pre-processed molecular structures
"""
```

#### **Class Documentation**:
```python
class DockingJobProcessor:
    """
    Application service for processing molecular docking jobs.

    This class orchestrates the complete docking workflow from job submission
    to result processing, handling engine selection, parameter validation,
    and result caching.

    Attributes:
        repository: Job persistence interface.
        engine_adapter: Docking engine communication interface.
        cache: Result caching interface.

    Example:
        >>> processor = DockingJobProcessor(repo, engine, cache)
        >>> job = await processor.process_job(job_request)
        >>> print(f"Job completed with affinity: {job.best_affinity}")
    """
```

#### **Function Documentation** (Google Style):
```python
def calculate_binding_affinity(
    poses: List[MolecularPose],
    scoring_function: str = "vina"
) -> BindingAffinityResult:
    """
    Calculate binding affinity scores for molecular poses.

    This function evaluates the binding strength between a ligand and target
    protein using the specified scoring function. Supports multiple poses
    and returns ranked results.

    Args:
        poses: List of molecular poses to evaluate. Each pose must contain
            valid 3D coordinates and atom types.
        scoring_function: Scoring method to use. Supported values are
            'vina' (AutoDock Vina), 'smina' (Smina), or 'custom'.

    Returns:
        BindingAffinityResult containing:
        - ranked_poses: Poses sorted by affinity (best first)
        - best_affinity: Lowest (most favorable) binding energy
        - confidence_scores: Reliability metrics for each pose

    Raises:
        InvalidPoseError: If poses contain invalid molecular data.
        UnsupportedScoringError: If scoring_function is not supported.
        ComputationError: If scoring calculation fails.

    Example:
        >>> poses = [pose1, pose2, pose3]
        >>> result = calculate_binding_affinity(poses, "vina")
        >>> print(f"Best affinity: {result.best_affinity} kcal/mol")
        >>> for pose in result.ranked_poses:
        ...     print(f"Pose {pose.id}: {pose.affinity}")
    """
```

### **Code Commenting Guidelines**

**Purpose**: Make intent obvious, capture the "why," reduce cognitive load.

#### **Comment Types and Schema**:

**Block Comments** (above code):
```python
# RATIONALE: Batching reduces DB round-trips from O(n) to O(1)
# for large molecule collections, improving performance by 10x.
batch_insert_molecules(molecules)

# INVARIANT: All molecules in batch must belong to same organization
# to maintain data isolation and security constraints.
assert all(mol.org_id == batch_org_id for mol in molecules)
```

**Inline Comments** (end of line):
```python
result = engine.dock(ligand, protein)  # May take 5-30 minutes
if result.poses > MAX_POSES:  # Prevent memory exhaustion
    result = result.top_k(MAX_POSES)
```

**Decision/TODO/Security Tags**:
```python
# TODO(#456) [@molecular-team] 2025-09-23: Replace O(n²) loop with bulk upsert
# FIXME: Incorrect timezone handling around DST transitions (issue #789)
# NOTE: This is idempotent by design; safe to retry on failure
# SECURITY: Tokens are redacted in logs; never log raw JWT content
```

**Code Snippet Comments** (required in docs):
```python
# Submit docking job and monitor progress (simplified workflow)
client = DockingClient(api_key="your-key")

# Upload molecular structures
protein = client.upload_molecule("protein.pdb")  # Target protein
ligand = client.upload_molecule("ligand.sdf")    # Small molecule

# Configure docking parameters
params = DockingParams(
    binding_site=BindingSite(x=25, y=10, z=15, radius=10),
    exhaustiveness=8  # Higher values = more thorough search
)

# Submit job and wait for completion
job = client.submit_docking_job(protein, ligand, params)
result = job.wait_for_completion()  # Polls every 30 seconds

print(f"Best binding affinity: {result.best_affinity} kcal/mol")
```

## 🧪 **Testing Strategy**

### **Test Structure**

Mirror the `src/` structure in `tests/`:

```
tests/
├── unit/           # Fast, isolated tests (no I/O)
│   ├── domain/     # Pure business logic
│   ├── use_cases/  # Application services (with mocks)
│   └── shared/     # Utility functions
├── integration/    # Service integration tests
│   ├── adapters/   # Database, external APIs
│   └── end_to_end/ # Full workflow tests
└── performance/    # Load and stress tests
```

### **Test Categories and Markers**

```python
import pytest

@pytest.mark.unit
def test_molecule_validation():
    """Test pure domain logic - no external dependencies."""
    molecule = Molecule(name="aspirin", smiles="CC(=O)OC1=CC=CC=C1C(=O)O")
    assert molecule.validate_structure() is True

@pytest.mark.integration
@pytest.mark.asyncio
async def test_job_repository_persistence():
    """Test database integration with real PostgreSQL."""
    async with test_database() as session:
        repository = PostgreSQLJobRepository(session)

        job = DockingJob.create(
            molecule=test_molecule(),
            target=test_target()
        )

        saved_job = await repository.save(job)
        retrieved_job = await repository.get_by_id(saved_job.id)

        assert retrieved_job == saved_job

@pytest.mark.e2e
@pytest.mark.slow
async def test_complete_docking_workflow():
    """Test entire workflow from molecule upload to results."""
    # This test runs against real services and may take minutes
    pass
```

### **Testing Commands**

```bash
# Run specific test categories
pytest -m unit                    # Fast unit tests only
pytest -m integration             # Integration tests
pytest -m "not slow"             # Skip time-consuming tests

# Coverage reporting
pytest --cov=src/molecular_analysis_dashboard --cov-report=html
open htmlcov/index.html

# Parallel execution
pytest -n auto                    # Use all CPU cores
```

### **Mock and Fixture Patterns**

```python
# conftest.py - Shared fixtures
@pytest.fixture
def mock_job_repository():
    """Mock repository for unit testing use cases."""
    repo = Mock(spec=JobRepositoryPort)
    repo.save = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
async def test_database():
    """Isolated test database for integration tests."""
    # Create clean test database
    engine = create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

## 🛠️ **Development Environment Setup**

### **Virtual Environment & Dependencies**

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# Windows: .venv\Scripts\Activate.ps1

# Install project in development mode
python -m pip install --upgrade pip
pip install -e ".[dev,docs,tools]"
```

### **Pre-commit Hooks Setup**

Automatic code quality enforcement:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files
pre-commit run --all-files
```

**Configured hooks**:
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **flake8**: Linting with plugins
- **bandit**: Security scanning
- **pydocstyle**: Docstring compliance
- **radon**: Complexity analysis

### **Configuration Files**

**.flake8**:
```ini
[flake8]
max-line-length = 100
extend-ignore = E203,W503
docstring-convention = google
extend-select = D
ignore = D401
exclude = .venv,build,dist,migrations
```

**pyproject.toml** (mypy config):
```toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
exclude = [
    "tests/",
    "migrations/"
]
```

## 🔄 **Development Workflow**

### **Feature Development Process**

1. **Before Coding**:
   - Read relevant docstrings and understand dependencies
   - Review architecture diagrams and existing tests
   - Plan the change within clean architecture boundaries

2. **During Development**:
   - Write tests first (TDD approach)
   - Implement feature following existing patterns
   - Add comprehensive docstrings
   - Run quality checks frequently

3. **Before Committing**:
   - Run full test suite: `pytest`
   - Check code quality: `pre-commit run --all-files`
   - Update documentation if needed
   - Commit with conventional commit message

### **Adding New Features**

**Start with Domain**:
```python
# 1. Define domain entity
class NewEntity:
    """New business concept with clear responsibilities."""
    pass

# 2. Add business rules as methods
def validate_business_rule(self) -> bool:
    """Check business invariant."""
    pass
```

**Create Use Case**:
```python
# 3. Define application service
class NewFeatureUseCase:
    def __init__(self, repository: NewEntityRepositoryPort):
        self._repository = repository

    async def execute(self, command: NewFeatureCommand) -> NewEntity:
        # Business logic orchestration
        pass
```

**Define Port**:
```python
# 4. Abstract interface for external dependencies
class NewEntityRepositoryPort(ABC):
    @abstractmethod
    async def save(self, entity: NewEntity) -> NewEntity:
        pass
```

**Implement Adapter**:
```python
# 5. Concrete implementation
class PostgreSQLNewEntityRepository(NewEntityRepositoryPort):
    async def save(self, entity: NewEntity) -> NewEntity:
        # Database-specific implementation
        pass
```

**Wire in Infrastructure**:
```python
# 6. Configure dependency injection
def get_new_feature_use_case(
    repository: NewEntityRepositoryPort = Depends(get_repository)
) -> NewFeatureUseCase:
    return NewFeatureUseCase(repository)
```

**Add Presentation**:
```python
# 7. HTTP endpoint
@router.post("/new-feature", response_model=NewEntityResponse)
async def create_new_entity(
    request: NewEntityRequest,
    use_case: NewFeatureUseCase = Depends(get_new_feature_use_case)
) -> NewEntityResponse:
    command = request.to_command()
    entity = await use_case.execute(command)
    return NewEntityResponse.from_entity(entity)
```

## 📊 **Code Quality Metrics**

### **Complexity Limits**

- **Cyclomatic Complexity**: ≤ 10 per function
- **Maintainability Index**: ≥ 70
- **Lines per Function**: ≤ 50
- **Parameters per Function**: ≤ 6

### **Coverage Requirements**

- **Unit Test Coverage**: ≥ 80%
- **Integration Test Coverage**: ≥ 60%
- **Critical Path Coverage**: 100%

### **Performance Guidelines**

- **API Response Time**: < 200ms (95th percentile)
- **Database Query Time**: < 100ms average
- **Memory Usage**: < 512MB per worker process
- **CPU Usage**: < 70% sustained load

## 🚨 **Troubleshooting**

### **Common Development Issues**

**Import Errors**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

**Database Connection Issues**:
```bash
# Check PostgreSQL service
docker ps | grep postgres

# Reset database
cd database
make reset
make migrate
```

**Test Failures**:
```bash
# Run specific failing test with verbose output
pytest tests/path/to/test.py::test_name -v -s

# Clear pytest cache
rm -rf .pytest_cache

# Check test database isolation
pytest tests/integration/ --create-db
```

### **Debugging Strategies**

**Use debugger with pytest**:
```python
import pytest

def test_complex_logic():
    # Set breakpoint
    pytest.set_trace()

    # Your test code here
    result = complex_function()
    assert result.is_valid
```

**Async debugging**:
```python
import asyncio
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Use asyncio debug mode
asyncio.run(main(), debug=True)
```

## 📈 **Performance Optimization**

### **Database Performance**

```python
# Use async database operations
async def get_jobs_with_results(org_id: UUID) -> List[JobWithResults]:
    # Efficient eager loading
    query = (
        select(JobModel)
        .options(selectinload(JobModel.results))
        .where(JobModel.org_id == org_id)
    )

    result = await session.execute(query)
    return [job.to_domain() for job in result.scalars()]

# Use database-level pagination
async def get_jobs_paginated(
    org_id: UUID, page: int, size: int
) -> PaginatedResponse[Job]:
    offset = (page - 1) * size

    query = (
        select(JobModel)
        .where(JobModel.org_id == org_id)
        .offset(offset)
        .limit(size)
    )

    # Count query for total
    count_query = (
        select(func.count(JobModel.id))
        .where(JobModel.org_id == org_id)
    )

    # Execute both queries concurrently
    jobs_result, count_result = await asyncio.gather(
        session.execute(query),
        session.execute(count_query)
    )

    jobs = [job.to_domain() for job in jobs_result.scalars()]
    total_count = count_result.scalar()

    return PaginatedResponse(
        items=jobs,
        total_count=total_count,
        page=page,
        size=size
    )
```

### **Caching Strategies**

```python
from functools import lru_cache
from typing import Dict, Any

# In-memory caching for expensive computations
@lru_cache(maxsize=1000)
def calculate_molecular_properties(smiles: str) -> Dict[str, Any]:
    """Cache molecular property calculations."""
    # Expensive RDKit computations
    pass

# Redis caching for database queries
class CachedJobRepository:
    def __init__(self, repository: JobRepositoryPort, cache: RedisCache):
        self._repository = repository
        self._cache = cache

    async def get_by_id(self, job_id: str) -> Optional[Job]:
        # Check cache first
        cached = await self._cache.get(f"job:{job_id}")
        if cached:
            return Job.from_json(cached)

        # Fallback to database
        job = await self._repository.get_by_id(job_id)
        if job:
            await self._cache.set(
                f"job:{job_id}",
                job.to_json(),
                expire=3600  # 1 hour
            )

        return job
```

## 🎯 **Daily Development Commands**

```bash
# Environment setup
source .venv/bin/activate         # Activate virtual environment

# Code quality
pre-commit run --all-files        # Format, lint, type check
black src/ tests/                 # Format code
isort src/ tests/                 # Sort imports
mypy src/                         # Type checking

# Testing
pytest -x                         # Stop on first failure
pytest --lf                       # Run last failed tests only
pytest -k "test_name"            # Run specific test pattern

# Development server
uvicorn src.molecular_analysis_dashboard.presentation.main:app --reload

# Database operations
cd database && make migrate       # Run migrations
cd database && make seed          # Seed test data
cd database && make health        # Check database health

# Documentation
mkdocs serve                      # Preview documentation
```

---

## Summary

This guide establishes:

- **Clean Architecture** compliance with strict layering
- **Comprehensive documentation** requirements (Google-style docstrings)
- **Quality automation** via pre-commit hooks and CI
- **Testing strategy** with proper isolation and coverage
- **Performance guidelines** for database and async operations
- **Troubleshooting** procedures for common issues

Following these practices ensures code quality, maintainability, and team productivity. For specific implementation patterns, refer to existing code in the repository or ask for guidance during code review.
