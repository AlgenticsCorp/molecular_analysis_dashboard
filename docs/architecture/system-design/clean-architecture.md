# Clean Architecture Implementation

This document details how the Molecular Analysis Dashboard implements Clean Architecture (Ports & Adapters) principles to ensure maintainability, testability, and adaptability.

## 🏗️ **Clean Architecture Principles**

### **The Dependency Rule**
Source code dependencies can only point inwards. Nothing in an inner circle can know anything about something in an outer circle.

```
┌─────────────────┐
│   Frameworks    │  ← Infrastructure (FastAPI, SQLAlchemy, Celery)
│   & Drivers     │
├─────────────────┤
│  Adapters       │  ← Interface Implementations (PostgreSQL, Redis)
│                 │
├─────────────────┤
│  Use Cases      │  ← Application Business Rules
│                 │
├─────────────────┤
│   Entities      │  ← Enterprise Business Rules (Domain)
│                 │
└─────────────────┘
```

### **Core Benefits**
- **Framework Independence**: Business logic doesn't depend on frameworks
- **Database Independence**: Can swap databases without changing business rules
- **UI Independence**: Business rules don't know about the UI
- **External Agency Independence**: Business rules don't know about external services
- **Testability**: Business rules can be tested without external elements

## 📁 **Layer Organization**

### **Domain Layer** (`domain/`)
**Purpose**: Contains enterprise-wide business rules and entities

```python
# domain/entities/molecule.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Molecule:
    """Core business entity representing a molecular structure."""
    id: Optional[str]
    name: str
    smiles: Optional[str]
    mol_block: Optional[str]
    properties: dict

    def validate_structure(self) -> bool:
        """Domain rule: validate molecular structure."""
        return bool(self.smiles or self.mol_block)

    def calculate_molecular_weight(self) -> float:
        """Domain service: calculate molecular properties."""
        # Pure business logic - no external dependencies
        pass
```

**Key Characteristics**:
- ✅ Pure Python objects
- ✅ No external dependencies
- ✅ Contains business rules and invariants
- ✅ Framework-agnostic

### **Use Cases Layer** (`use_cases/`)
**Purpose**: Application-specific business rules and orchestration

```python
# use_cases/commands/create_docking_job.py
from abc import ABC, abstractmethod
from domain.entities import DockingJob, Molecule
from ports.repository import DockingJobRepositoryPort
from ports.external import DockingEnginePort

class CreateDockingJobUseCase:
    def __init__(
        self,
        job_repository: DockingJobRepositoryPort,
        docking_engine: DockingEnginePort
    ):
        self._job_repository = job_repository
        self._docking_engine = docking_engine

    async def execute(self, command: CreateDockingJobCommand) -> DockingJob:
        # 1. Validate business rules
        if not command.molecule.validate_structure():
            raise InvalidMoleculeError("Invalid molecular structure")

        # 2. Create domain entity
        job = DockingJob.create(
            molecule=command.molecule,
            target=command.target,
            parameters=command.parameters
        )

        # 3. Persist via port
        job = await self._job_repository.save(job)

        # 4. Trigger execution via port
        await self._docking_engine.submit_job(job)

        return job
```

**Key Characteristics**:
- ✅ Orchestrates domain entities
- ✅ Depends only on ports (abstractions)
- ✅ Contains application-specific business rules
- ✅ No knowledge of frameworks or external systems

### **Ports Layer** (`ports/`)
**Purpose**: Abstract interfaces that define contracts

```python
# ports/repository/docking_job_repository_port.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import DockingJob

class DockingJobRepositoryPort(ABC):
    """Port defining contract for docking job persistence."""

    @abstractmethod
    async def save(self, job: DockingJob) -> DockingJob:
        """Persist a docking job."""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[DockingJob]:
        """Retrieve job by ID."""
        pass

    @abstractmethod
    async def list_by_organization(self, org_id: str) -> List[DockingJob]:
        """List jobs for organization."""
        pass
```

**Key Characteristics**:
- ✅ Abstract Base Classes or Protocols
- ✅ Define stable contracts
- ✅ Enable dependency inversion
- ✅ Support testing with mocks

### **Adapters Layer** (`adapters/`)
**Purpose**: Concrete implementations of ports

```python
# adapters/database/postgresql_docking_job_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from ports.repository import DockingJobRepositoryPort
from domain.entities import DockingJob

class PostgreSQLDockingJobRepository(DockingJobRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, job: DockingJob) -> DockingJob:
        # Map domain entity to SQLAlchemy model
        model = DockingJobModel.from_entity(job)
        self._session.add(model)
        await self._session.commit()

        # Map back to domain entity
        return model.to_entity()

    async def get_by_id(self, job_id: str) -> Optional[DockingJob]:
        model = await self._session.get(DockingJobModel, job_id)
        return model.to_entity() if model else None
```

**Key Characteristics**:
- ✅ Implements port interfaces
- ✅ Contains framework-specific code
- ✅ Maps between domain entities and external representations
- ✅ Can be swapped without affecting business logic

### **Infrastructure Layer** (`infrastructure/`)
**Purpose**: Framework setup and dependency wiring

```python
# infrastructure/dependency_injection.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from adapters.database import PostgreSQLDockingJobRepository
from adapters.external import AutoDockVinaAdapter
from use_cases.commands import CreateDockingJobUseCase

def get_docking_job_repository(
    session: AsyncSession = Depends(get_async_session)
) -> DockingJobRepositoryPort:
    return PostgreSQLDockingJobRepository(session)

def get_docking_engine() -> DockingEnginePort:
    return AutoDockVinaAdapter()

def get_create_docking_job_use_case(
    repository: DockingJobRepositoryPort = Depends(get_docking_job_repository),
    engine: DockingEnginePort = Depends(get_docking_engine)
) -> CreateDockingJobUseCase:
    return CreateDockingJobUseCase(repository, engine)
```

**Key Characteristics**:
- ✅ Wires dependencies together
- ✅ Framework-specific configuration
- ✅ Database connection setup
- ✅ Service registration and discovery

### **Presentation Layer** (`presentation/`)
**Purpose**: External interface (API routes, schemas)

```python
# presentation/api/routes/docking_jobs.py
from fastapi import APIRouter, Depends
from presentation.api.schemas import CreateDockingJobRequest, DockingJobResponse
from use_cases.commands import CreateDockingJobUseCase

router = APIRouter()

@router.post("/jobs", response_model=DockingJobResponse)
async def create_docking_job(
    request: CreateDockingJobRequest,
    use_case: CreateDockingJobUseCase = Depends(get_create_docking_job_use_case)
) -> DockingJobResponse:
    # Convert request to use case command
    command = request.to_command()

    # Execute use case
    job = await use_case.execute(command)

    # Convert domain entity to response
    return DockingJobResponse.from_entity(job)
```

**Key Characteristics**:
- ✅ Handles external communication
- ✅ Input/output validation
- ✅ Maps between external formats and domain
- ✅ Depends only on use cases

## 🔄 **Dependency Flow**

```
Presentation → Use Cases → Domain
     ↓           ↓
Infrastructure  Ports ← Adapters
```

### **Dependency Injection Example**

```python
# Fast API dependency injection following clean architecture

# Infrastructure provides concrete implementations
api_dependencies = {
    DockingJobRepositoryPort: PostgreSQLDockingJobRepository,
    DockingEnginePort: AutoDockVinaAdapter,
    StoragePort: S3StorageAdapter,
}

# Use cases depend on ports (abstractions)
use_case = CreateDockingJobUseCase(
    job_repository=container[DockingJobRepositoryPort],
    docking_engine=container[DockingEnginePort],
    storage=container[StoragePort]
)

# Presentation depends on use cases
@router.post("/jobs")
async def create_job(
    request: CreateJobRequest,
    use_case: CreateDockingJobUseCase = Depends(get_use_case)
):
    return await use_case.execute(request.to_command())
```

## 🧪 **Testing Benefits**

### **Unit Testing Domain Logic**
```python
def test_molecule_validation():
    # Test pure domain logic - no external dependencies
    molecule = Molecule(name="test", smiles="CCO")
    assert molecule.validate_structure() == True

    invalid_molecule = Molecule(name="test")
    assert invalid_molecule.validate_structure() == False
```

### **Use Case Testing with Mocks**
```python
@pytest.mark.asyncio
async def test_create_docking_job_use_case():
    # Mock ports (interfaces)
    mock_repository = Mock(spec=DockingJobRepositoryPort)
    mock_engine = Mock(spec=DockingEnginePort)

    # Test use case in isolation
    use_case = CreateDockingJobUseCase(mock_repository, mock_engine)

    command = CreateDockingJobCommand(...)
    result = await use_case.execute(command)

    # Verify interactions with ports
    mock_repository.save.assert_called_once()
    mock_engine.submit_job.assert_called_once()
```

### **Integration Testing Adapters**
```python
@pytest.mark.asyncio
async def test_postgresql_repository_integration():
    # Test adapter with real database
    repository = PostgreSQLDockingJobRepository(test_session)

    job = DockingJob(...)
    saved_job = await repository.save(job)

    retrieved_job = await repository.get_by_id(saved_job.id)
    assert retrieved_job == saved_job
```

## 🔄 **Dynamic Task System Integration**

The dynamic task system extends clean architecture principles:

### **Task Definition Entity**
```python
# domain/entities/task_definition.py
@dataclass
class TaskDefinition:
    """Domain entity for dynamic task definitions."""
    id: str
    name: str
    version: str
    openapi_spec: dict
    organization_id: str

    def validate_spec(self) -> bool:
        """Validate OpenAPI specification."""
        # Domain rule for task spec validation
        pass
```

### **Task Registry Port**
```python
# ports/repository/task_registry_port.py
class TaskRegistryPort(ABC):
    @abstractmethod
    async def register_task(self, task_def: TaskDefinition) -> None:
        pass

    @abstractmethod
    async def discover_tasks(self, org_id: str) -> List[TaskDefinition]:
        pass
```

### **Service Discovery Adapter**
```python
# adapters/external/kubernetes_service_discovery.py
class KubernetesServiceDiscoveryAdapter(ServiceDiscoveryPort):
    async def register_service(self, service_info: ServiceInfo) -> None:
        # Register task service with Kubernetes API
        pass

    async def discover_services(self, task_type: str) -> List[ServiceInfo]:
        # Discover running task services
        pass
```

## ✅ **Clean Architecture Compliance Checklist**

### **Domain Layer**
- [ ] No external dependencies (no imports from other layers)
- [ ] Pure business logic only
- [ ] Framework-agnostic entities
- [ ] Domain services for complex business rules

### **Use Cases Layer**
- [ ] Depends only on domain and ports
- [ ] No framework dependencies
- [ ] Orchestrates business workflows
- [ ] Input/output through commands and queries

### **Ports Layer**
- [ ] Abstract interfaces only
- [ ] No implementation details
- [ ] Stable contracts
- [ ] Enable dependency inversion

### **Adapters Layer**
- [ ] Implements port interfaces
- [ ] Contains framework-specific code
- [ ] Maps between domain and external systems
- [ ] Can be swapped independently

### **Infrastructure Layer**
- [ ] Wires dependencies together
- [ ] Framework configuration
- [ ] No business logic
- [ ] Service registration

### **Presentation Layer**
- [ ] Depends only on use cases
- [ ] Input/output validation
- [ ] Maps external formats to domain
- [ ] Framework-specific interface code

## 🎯 **Best Practices**

1. **Keep Domain Pure**: No external dependencies in domain layer
2. **Use Dependency Injection**: Wire adapters through infrastructure
3. **Test at Right Level**: Unit test domain, integration test adapters
4. **Stable Ports**: Design interfaces that don't change frequently
5. **Single Responsibility**: Each layer and component has one reason to change
6. **Explicit Dependencies**: Make dependencies visible through constructor injection

For more details on specific implementations:
- [Domain Model](domain-model.md) - Detailed domain entities and rules
- [Service Layer](service-layer.md) - Use case implementations
- [Integration Patterns](../integration/gateway.md) - Adapter implementations
