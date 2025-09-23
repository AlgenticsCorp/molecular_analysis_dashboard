# 🏗️ Architecture Overview for New Developers

This guide provides a developer-friendly introduction to the Molecular Analysis Dashboard's architecture, designed to help you understand the system design and start contributing effectively.

## 🎯 **What You'll Learn**

- **Clean Architecture principles** and how we implement them
- **System boundaries** and how components interact
- **Key design patterns** used throughout the codebase
- **Multi-tenant architecture** for organization isolation
- **Technology choices** and why we made them

---

## 🏛️ **Clean Architecture Overview**

We follow **Clean Architecture** (also known as Hexagonal Architecture or Ports & Adapters) to create maintainable, testable, and flexible code.

### **The Big Picture**

```
🌐 External World
    ↕️
🚪 Presentation Layer     (FastAPI routes, React components)
    ↕️
🎯 Use Cases Layer       (Business logic orchestration)
    ↕️
💎 Domain Layer          (Pure business rules and entities)
    ↕️
🔌 Ports Layer          (Abstract interfaces)
    ↕️
🔧 Adapters Layer       (Database, external APIs, file system)
    ↕️
🏗️ Infrastructure Layer  (Configuration, dependency injection)
```

### **Key Principle: Dependency Rule**

**Dependencies point inward** - outer layers depend on inner layers, never the reverse.

```python
# ✅ Good: Use case depends on domain and ports (abstractions)
class ProcessMoleculeUseCase:
    def __init__(self, repository: MoleculeRepositoryPort):
        self._repository = repository  # Depends on interface

# ❌ Bad: Use case depends on adapter (implementation)
class ProcessMoleculeUseCase:
    def __init__(self, repository: PostgreSQLRepository):
        self._repository = repository  # Depends on implementation
```

---

## 📁 **Code Structure Walkthrough**

### **Domain Layer** (`src/molecular_analysis_dashboard/domain/`)

**Pure business logic** - no external dependencies

```python
# domain/entities/molecule.py
@dataclass
class Molecule:
    """Core business entity representing a molecular structure."""
    id: Optional[str]
    name: str
    smiles: Optional[str]  # SMILES notation

    def validate_structure(self) -> bool:
        """Business rule: molecule must have valid structure."""
        return bool(self.smiles and len(self.smiles) > 0)

    def calculate_molecular_weight(self) -> float:
        """Domain service: calculate properties."""
        # Pure calculation - no external dependencies
        pass
```

**What goes here:**
- Business entities (Molecule, DockingJob, Pipeline)
- Value objects (MolecularWeight, BindingSite)
- Domain services (calculations, validations)
- Business rules and invariants

**What doesn't:**
- Database code
- HTTP requests
- File I/O
- Framework dependencies

### **Use Cases Layer** (`src/molecular_analysis_dashboard/use_cases/`)

**Application orchestration** - coordinates domain objects

```python
# use_cases/commands/create_docking_job.py
class CreateDockingJobUseCase:
    def __init__(
        self,
        job_repository: JobRepositoryPort,  # Abstract interface
        molecule_repository: MoleculeRepositoryPort,  # Abstract interface
        docking_engine: DockingEnginePort  # Abstract interface
    ):
        self._job_repo = job_repository
        self._molecule_repo = molecule_repository
        self._engine = docking_engine

    async def execute(self, command: CreateDockingJobCommand) -> DockingJob:
        # 1. Get domain objects via ports
        molecule = await self._molecule_repo.get_by_id(command.molecule_id)
        if not molecule:
            raise MoleculeNotFoundError()

        # 2. Apply business rules
        if not molecule.validate_structure():
            raise InvalidMoleculeError("Molecule structure is invalid")

        # 3. Create domain entity
        job = DockingJob.create(
            molecule=molecule,
            target=command.target,
            parameters=command.parameters
        )

        # 4. Persist and execute via ports
        job = await self._job_repo.save(job)
        await self._engine.submit_job(job)

        return job
```

**Characteristics:**
- Orchestrates multiple domain objects
- Depends only on domain and ports (abstractions)
- Contains application-specific business rules
- Framework-agnostic

### **Ports Layer** (`src/molecular_analysis_dashboard/ports/`)

**Abstract interfaces** - define contracts between layers

```python
# ports/repository/job_repository_port.py
from abc import ABC, abstractmethod

class JobRepositoryPort(ABC):
    """Contract for job persistence."""

    @abstractmethod
    async def save(self, job: DockingJob) -> DockingJob:
        """Save job to storage."""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[DockingJob]:
        """Retrieve job by ID."""
        pass

    @abstractmethod
    async def list_by_organization(self, org_id: str) -> List[DockingJob]:
        """List jobs for organization."""
        pass

# ports/external/docking_engine_port.py
class DockingEnginePort(ABC):
    """Contract for molecular docking engines."""

    @abstractmethod
    async def submit_job(self, job: DockingJob) -> str:
        """Submit job to docking engine."""
        pass

    @abstractmethod
    async def get_results(self, job_id: str) -> DockingResult:
        """Get docking results."""
        pass
```

**Benefits:**
- Enable dependency inversion
- Allow easy testing with mocks
- Support multiple implementations
- Define stable contracts

### **Adapters Layer** (`src/molecular_analysis_dashboard/adapters/`)

**Concrete implementations** - handle external systems

```python
# adapters/database/postgresql_job_repository.py
class PostgreSQLJobRepository(JobRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, job: DockingJob) -> DockingJob:
        # Map domain entity to SQLAlchemy model
        model = JobModel.from_entity(job)
        self._session.add(model)
        await self._session.commit()

        # Map back to domain entity
        return model.to_entity()

# adapters/external/autodock_vina_adapter.py
class AutoDockVinaAdapter(DockingEnginePort):
    async def submit_job(self, job: DockingJob) -> str:
        # Execute AutoDock Vina as subprocess
        # Handle file I/O, parsing results
        # Return job execution ID
        pass
```

**Responsibilities:**
- Implement port interfaces
- Handle framework-specific code
- Map between domain and external representations
- Deal with I/O, networking, file systems

### **Infrastructure Layer** (`src/molecular_analysis_dashboard/infrastructure/`)

**System configuration** - wires everything together

```python
# infrastructure/dependency_injection.py
from fastapi import Depends

def get_job_repository(
    session: AsyncSession = Depends(get_async_session)
) -> JobRepositoryPort:
    return PostgreSQLJobRepository(session)

def get_docking_engine() -> DockingEnginePort:
    return AutoDockVinaAdapter()

def get_create_job_use_case(
    job_repo: JobRepositoryPort = Depends(get_job_repository),
    engine: DockingEnginePort = Depends(get_docking_engine)
) -> CreateDockingJobUseCase:
    return CreateDockingJobUseCase(job_repo, engine)
```

### **Presentation Layer** (`src/molecular_analysis_dashboard/presentation/`)

**External interfaces** - HTTP API, CLI, etc.

```python
# presentation/api/routes/jobs.py
@router.post("/jobs", response_model=JobResponse)
async def create_job(
    request: CreateJobRequest,
    use_case: CreateDockingJobUseCase = Depends(get_create_job_use_case)
) -> JobResponse:
    # Convert HTTP request to use case command
    command = CreateDockingJobCommand(
        molecule_id=request.molecule_id,
        target=request.target,
        parameters=request.parameters
    )

    # Execute business logic
    job = await use_case.execute(command)

    # Convert domain entity to HTTP response
    return JobResponse.from_entity(job)
```

---

## 🏢 **Multi-Tenant Architecture**

### **Organization-Based Isolation**

Every piece of data belongs to an organization:

```python
# All domain entities have organization context
@dataclass
class DockingJob:
    id: str
    org_id: str  # Organization isolation
    molecule: Molecule
    status: JobStatus

# Repository queries are org-scoped
class PostgreSQLJobRepository(JobRepositoryPort):
    async def list_by_organization(self, org_id: str) -> List[DockingJob]:
        query = select(JobModel).where(JobModel.org_id == org_id)
        # This ensures data isolation
```

### **Database Strategy**

We use a **hybrid approach**:

```
Metadata DB (Shared)          Results DBs (Per-Org)
┌─────────────────────┐      ┌─────────────────────┐
│ organizations       │      │ jobs (org_a)        │
│ users               │      │ executions          │
│ task_definitions    │      │ docking_results     │
│ pipeline_templates  │      │ job_events          │
└─────────────────────┘      └─────────────────────┘
                             ┌─────────────────────┐
                             │ jobs (org_b)        │
                             │ executions          │
                             │ docking_results     │
                             │ job_events          │
                             └─────────────────────┘
```

**Benefits:**
- Complete data isolation between organizations
- Independent scaling per tenant
- Separate backup and retention policies
- Compliance with data residency requirements

---

## 🔄 **Request Flow Example**

Let's trace a docking job creation request:

```
1. HTTP Request arrives
   POST /api/v1/jobs
   {
     "molecule_id": "mol123",
     "target": "protein.pdb",
     "parameters": {...}
   }

2. Presentation Layer
   ├─ Validate JWT token
   ├─ Extract org_id from JWT
   ├─ Validate request schema
   └─ Convert to CreateJobCommand

3. Use Case Layer
   ├─ Get molecule via MoleculeRepositoryPort
   ├─ Validate business rules
   ├─ Create DockingJob entity
   ├─ Save via JobRepositoryPort
   └─ Submit via DockingEnginePort

4. Adapter Layer
   ├─ PostgreSQL: Save job to database
   ├─ AutoDock: Start docking process
   └─ FileSystem: Store input files

5. Response
   └─ Return job details to client
```

### **Key Observations**

- **JWT contains org_id** - used for multi-tenant isolation
- **Use cases are pure orchestration** - no I/O or framework code
- **Adapters handle all external communication**
- **Domain entities remain framework-agnostic**

---

## 🛠️ **Technology Stack Decisions**

### **Backend Technology Choices**

| Technology | Why We Chose It |
|------------|-----------------|
| **FastAPI** | Modern async Python framework, automatic OpenAPI generation |
| **SQLAlchemy 2.0** | Mature ORM with excellent async support |
| **PostgreSQL** | Robust relational database with JSON support |
| **Celery** | Proven distributed task processing |
| **Redis** | Fast message broker and caching |
| **Docker** | Consistent development and deployment |

### **Frontend Technology Choices**

| Technology | Why We Chose It |
|------------|-----------------|
| **React 18** | Component-based UI with excellent ecosystem |
| **TypeScript** | Type safety for large codebases |
| **Material-UI** | Professional component library |
| **React Query** | Excellent server state management |
| **Vite** | Fast build tool and dev server |

### **Architecture Pattern Choices**

| Pattern | Why We Use It |
|---------|---------------|
| **Clean Architecture** | Maintainable, testable, framework-independent |
| **Domain-Driven Design** | Models complex molecular analysis domain |
| **CQRS (light)** | Separate read/write operations for performance |
| **Multi-tenancy** | Secure organization data isolation |
| **Async/Await** | Handle I/O efficiently |

---

## 🔍 **Key Design Patterns**

### **Repository Pattern**
Abstracts data access behind interfaces:
```python
# Port (abstraction)
class MoleculeRepositoryPort(ABC):
    async def save(self, molecule: Molecule) -> Molecule: ...

# Adapter (implementation)
class PostgreSQLMoleculeRepository(MoleculeRepositoryPort):
    async def save(self, molecule: Molecule) -> Molecule:
        # PostgreSQL-specific implementation
```

### **Command Pattern**
Encapsulates requests as objects:
```python
@dataclass
class CreateDockingJobCommand:
    molecule_id: str
    target: str
    parameters: DockingParameters

class CreateDockingJobUseCase:
    async def execute(self, command: CreateDockingJobCommand) -> DockingJob:
        # Handle command
```

### **Factory Pattern**
Creates complex objects:
```python
class DockingJobFactory:
    @staticmethod
    def create_from_request(request: CreateJobRequest, org_id: str) -> DockingJob:
        return DockingJob(
            id=generate_id(),
            org_id=org_id,
            # ... other properties
        )
```

### **Adapter Pattern**
Allows incompatible interfaces to work together:
```python
# External docking engines have different interfaces
class VinaEngineAdapter(DockingEnginePort):
    # Adapts Vina's interface to our standard port

class SminaEngineAdapter(DockingEnginePort):
    # Adapts Smina's interface to our standard port
```

---

## 🧪 **Testing Strategy**

### **Test Pyramid**

```
        🔺 E2E Tests (Few)
       /   \  Full workflows
      /     \  Real services
     /       \
    🔺 Integration Tests (Some)
   /   \      Database & external services
  /     \     Real adapters
 /       \
🔺 Unit Tests (Many)
   Domain logic & use cases
   Fast, isolated, mocked dependencies
```

### **Testing at Each Layer**

```python
# Unit test - Domain layer
def test_molecule_validation():
    molecule = Molecule(name="aspirin", smiles="CC(=O)OC1=CC=CC=C1C(=O)O")
    assert molecule.validate_structure() == True

# Unit test - Use case layer (with mocks)
async def test_create_job_use_case():
    mock_repo = Mock(spec=JobRepositoryPort)
    use_case = CreateDockingJobUseCase(mock_repo)

    job = await use_case.execute(command)

    mock_repo.save.assert_called_once()

# Integration test - Adapter layer
async def test_postgresql_job_repository():
    async with test_session() as session:
        repo = PostgreSQLJobRepository(session)
        job = create_test_job()

        saved = await repo.save(job)
        retrieved = await repo.get_by_id(saved.id)

        assert retrieved == saved

# E2E test - Full workflow
async def test_job_creation_workflow(api_client):
    response = await api_client.post("/api/v1/jobs", json=job_data)
    assert response.status_code == 201

    job_id = response.json()["job_id"]
    # Wait for completion and verify results
```

---

## 🎯 **Domain-Driven Design Concepts**

### **Ubiquitous Language**

We use domain terminology consistently throughout:

- **Molecule**: Chemical compound to be analyzed
- **Docking**: Process of predicting molecular binding
- **Pose**: Predicted binding configuration
- **Affinity**: Strength of molecular binding
- **Pipeline**: Sequence of analysis tasks
- **Execution**: Running instance of a task

### **Bounded Contexts**

Our system has several bounded contexts:

```
┌─────────────────────┐  ┌─────────────────────┐
│   User Management   │  │  Molecular Analysis │
│                     │  │                     │
│ • Organizations     │  │ • Molecules         │
│ • Users             │  │ • Docking Jobs      │
│ • Roles             │  │ • Results           │
│ • Permissions       │  │ • Pipelines         │
└─────────────────────┘  └─────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐
│   Task Management   │  │   File Management   │
│                     │  │                     │
│ • Task Definitions  │  │ • File Storage      │
│ • Executions        │  │ • Upload/Download   │
│ • Service Registry  │  │ • Format Conversion │
│ • Resource Quotas   │  │ • Artifact Tracking │
└─────────────────────┘  └─────────────────────┘
```

### **Aggregates**

Domain entities are grouped into aggregates:

```python
# DockingJob is an aggregate root
class DockingJob:
    def __init__(self):
        self._executions: List[TaskExecution] = []  # Aggregate members
        self._results: List[DockingResult] = []     # Aggregate members

    def add_execution(self, execution: TaskExecution):
        # Business rule: maintain consistency within aggregate
        if execution.job_id != self.id:
            raise ValueError("Execution belongs to different job")
        self._executions.append(execution)
```

---

## 🔄 **Development Workflow Integration**

### **How Architecture Guides Development**

1. **Start with Domain**: Define entities and business rules
2. **Create Use Cases**: Orchestrate domain objects
3. **Define Ports**: Abstract external dependencies
4. **Implement Adapters**: Connect to real systems
5. **Wire Infrastructure**: Configure dependency injection
6. **Add Presentation**: Create API endpoints/UI

### **Adding a New Feature Example**

**Scenario**: Add molecular property calculation

```python
# 1. Domain - Add business logic
class Molecule:
    def calculate_properties(self) -> MolecularProperties:
        # Pure calculation logic

# 2. Use Case - Orchestrate the workflow
class CalculatePropertiesUseCase:
    async def execute(self, molecule_id: str) -> MolecularProperties:
        molecule = await self._molecule_repo.get_by_id(molecule_id)
        properties = molecule.calculate_properties()
        await self._properties_repo.save(properties)
        return properties

# 3. Port - Define storage contract
class PropertiesRepositoryPort(ABC):
    async def save(self, properties: MolecularProperties): ...

# 4. Adapter - Implement storage
class PostgreSQLPropertiesRepository(PropertiesRepositoryPort):
    async def save(self, properties: MolecularProperties):
        # Database-specific implementation

# 5. Infrastructure - Wire dependencies
def get_calculate_properties_use_case(...) -> CalculatePropertiesUseCase:
    return CalculatePropertiesUseCase(...)

# 6. Presentation - Add HTTP endpoint
@router.post("/molecules/{id}/properties")
async def calculate_properties(id: str, use_case = Depends(...)):
    return await use_case.execute(id)
```

---

## 📚 **Further Reading**

### **Architecture Resources**
- [Clean Architecture (Uncle Bob)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

### **Implementation Examples**
- Browse `src/molecular_analysis_dashboard/domain/` for business entities
- Check `src/molecular_analysis_dashboard/use_cases/` for application logic
- Examine `tests/unit/domain/` for domain testing examples
- Review `src/molecular_analysis_dashboard/adapters/` for external integrations

### **Next Steps**
1. **Explore the codebase** following the architecture layers
2. **Try the [First Contribution](first-contribution.md)** guide
3. **Read existing tests** to understand behavior
4. **Join discussions** about architectural decisions

---

## 🎯 **Key Takeaways**

1. **Clean Architecture** keeps business logic separate from frameworks
2. **Dependency inversion** allows easy testing and flexibility
3. **Multi-tenancy** ensures secure organization data isolation
4. **Domain-driven design** models complex molecular analysis workflows
5. **Testing strategy** validates behavior at each architectural layer
6. **Consistent patterns** make the codebase predictable and maintainable

Understanding these architectural principles will help you navigate the codebase, make effective changes, and contribute high-quality code that fits well with the existing system design.

Ready to dive deeper? Check out the [First Contribution](first-contribution.md) guide to start making changes! 🚀
