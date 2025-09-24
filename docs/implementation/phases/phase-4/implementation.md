# Phase 4: Task Integration & Advanced Features - Implementation Guide

**Phase:** 4 - Task Integration & Advanced Features
**Implementation Period:** April 1 - May 31, 2025
**Prerequisites:** Phase 3B Service Implementation Complete

---

## 🎯 **Implementation Overview**

This guide provides step-by-step implementation instructions for Phase 4, focusing on the dynamic task system, molecular docking engine integration, and advanced pipeline capabilities.

**Implementation Strategy:**
- **Sequential Sub-Phases**: 4A → 4B → 4C with clear dependencies
- **Clean Architecture Compliance**: Strict layering and dependency management
- **Test-Driven Development**: Comprehensive testing at each layer
- **Incremental Delivery**: Functional increments with validation gates

---

## 📋 **Phase 4A: Task Integration Implementation**

### **Step 1: Domain Layer - Task Entities**

**1.1 Create Task Domain Entity**
```python
# src/molecular_analysis_dashboard/domain/entities/task.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid
from datetime import datetime

class TaskStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"

class TaskCategory(Enum):
    DOCKING = "docking"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    OPTIMIZATION = "optimization"

@dataclass
class TaskDefinition:
    """Dynamic task definition with OpenAPI specification."""

    task_id: str
    name: str
    version: str
    category: TaskCategory
    description: str
    interface_spec: Dict[str, Any]  # OpenAPI 3.0 specification
    service_config: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @classmethod
    def create(cls, task_id: str, name: str, version: str,
               category: TaskCategory, interface_spec: Dict[str, Any],
               **kwargs) -> 'TaskDefinition':
        """Factory method for creating new task definitions."""
        # Validate OpenAPI spec structure
        if not cls._validate_openapi_spec(interface_spec):
            raise ValueError("Invalid OpenAPI specification")

        return cls(
            task_id=task_id,
            name=name,
            version=version,
            category=category,
            interface_spec=interface_spec,
            **kwargs
        )

    @staticmethod
    def _validate_openapi_spec(spec: Dict[str, Any]) -> bool:
        """Validate that interface_spec is a valid OpenAPI 3.0 specification."""
        required_fields = ['openapi', 'info', 'paths']
        return all(field in spec for field in required_fields)

    def get_execution_endpoint(self) -> str:
        """Get the execution endpoint path from OpenAPI spec."""
        paths = self.interface_spec.get('paths', {})
        for path, methods in paths.items():
            if 'post' in methods:
                return path
        raise ValueError("No POST endpoint found in task specification")
```

**1.2 Create Task Execution Entity**
```python
# src/molecular_analysis_dashboard/domain/entities/task_execution.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import uuid
from datetime import datetime

class ExecutionStatus(Enum):
    SUBMITTED = "submitted"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskExecution:
    """Task execution with status tracking and results."""

    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    org_id: str = ""
    job_id: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.SUBMITTED
    parameters: Dict[str, Any] = field(default_factory=dict)
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_metrics: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    @classmethod
    def create(cls, task_id: str, org_id: str, parameters: Dict[str, Any],
               job_id: Optional[str] = None) -> 'TaskExecution':
        """Factory method for creating new task execution."""
        return cls(
            task_id=task_id,
            org_id=org_id,
            job_id=job_id,
            parameters=parameters
        )

    def start_execution(self) -> None:
        """Mark execution as started."""
        if self.status not in [ExecutionStatus.SUBMITTED, ExecutionStatus.QUEUED]:
            raise ValueError(f"Cannot start execution from status: {self.status}")
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete_execution(self, results: Dict[str, Any],
                          metrics: Optional[Dict[str, Any]] = None) -> None:
        """Mark execution as completed with results."""
        if self.status != ExecutionStatus.RUNNING:
            raise ValueError(f"Cannot complete execution from status: {self.status}")
        self.status = ExecutionStatus.COMPLETED
        self.results = results
        self.execution_metrics = metrics
        self.completed_at = datetime.utcnow()

    def fail_execution(self, error_message: str) -> None:
        """Mark execution as failed with error message."""
        if self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED]:
            raise ValueError(f"Cannot fail execution from status: {self.status}")
        self.status = ExecutionStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
```

### **Step 2: Use Cases Layer - Task Operations**

**2.1 Register Task Use Case**
```python
# src/molecular_analysis_dashboard/use_cases/commands/register_task.py
from dataclasses import dataclass
from typing import Dict, Any, List
from ..ports.task_registry_port import TaskRegistryPort
from ..ports.service_discovery_port import ServiceDiscoveryPort
from ..domain.entities.task import TaskDefinition, TaskCategory

@dataclass
class RegisterTaskCommand:
    """Command to register a new dynamic task."""
    task_id: str
    name: str
    version: str
    category: str
    description: str
    interface_spec: Dict[str, Any]
    service_config: Dict[str, Any]
    tags: List[str] = None

class RegisterTaskUseCase:
    """Use case for registering dynamic tasks."""

    def __init__(self,
                 task_registry: TaskRegistryPort,
                 service_discovery: ServiceDiscoveryPort):
        self._task_registry = task_registry
        self._service_discovery = service_discovery

    async def execute(self, command: RegisterTaskCommand) -> TaskDefinition:
        """Register a new task definition."""

        # Validate category
        try:
            category = TaskCategory(command.category)
        except ValueError:
            raise ValueError(f"Invalid task category: {command.category}")

        # Create task definition
        task = TaskDefinition.create(
            task_id=command.task_id,
            name=command.name,
            version=command.version,
            category=category,
            interface_spec=command.interface_spec,
            service_config=command.service_config,
            description=command.description,
            tags=command.tags or []
        )

        # Check if task already exists
        existing_task = await self._task_registry.get_by_id(task.task_id)
        if existing_task:
            raise ValueError(f"Task with ID {task.task_id} already exists")

        # Save task definition
        saved_task = await self._task_registry.save(task)

        # Register with service discovery if service_config provided
        if task.service_config and 'service_url' in task.service_config:
            await self._service_discovery.register_service(
                service_id=f"task-{task.task_id}",
                task_id=task.task_id,
                service_url=task.service_config['service_url'],
                health_check_url=task.service_config.get('health_check_url'),
                capabilities=task.service_config.get('capabilities', {})
            )

        return saved_task
```

**2.2 Execute Task Use Case**
```python
# src/molecular_analysis_dashboard/use_cases/commands/execute_task.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
from ..ports.task_registry_port import TaskRegistryPort
from ..ports.task_executor_port import TaskExecutorPort
from ..ports.job_repository_port import JobRepositoryPort
from ..domain.entities.task_execution import TaskExecution

@dataclass
class ExecuteTaskCommand:
    """Command to execute a dynamic task."""
    task_id: str
    org_id: str
    parameters: Dict[str, Any]
    job_id: Optional[str] = None

class ExecuteTaskUseCase:
    """Use case for executing dynamic tasks."""

    def __init__(self,
                 task_registry: TaskRegistryPort,
                 task_executor: TaskExecutorPort,
                 job_repository: JobRepositoryPort):
        self._task_registry = task_registry
        self._task_executor = task_executor
        self._job_repository = job_repository

    async def execute(self, command: ExecuteTaskCommand) -> TaskExecution:
        """Execute a task with given parameters."""

        # Get task definition
        task = await self._task_registry.get_by_id(command.task_id)
        if not task:
            raise ValueError(f"Task not found: {command.task_id}")

        if task.status != "active":
            raise ValueError(f"Task {command.task_id} is not active")

        # Validate parameters against OpenAPI spec
        validation_errors = await self._validate_parameters(
            task.interface_spec, command.parameters
        )
        if validation_errors:
            raise ValueError(f"Parameter validation failed: {validation_errors}")

        # Create task execution
        execution = TaskExecution.create(
            task_id=command.task_id,
            org_id=command.org_id,
            parameters=command.parameters,
            job_id=command.job_id
        )

        # Save execution record
        execution = await self._job_repository.save_task_execution(execution)

        # Submit for async execution
        await self._task_executor.submit_task(execution, task)

        return execution

    async def _validate_parameters(self, interface_spec: Dict[str, Any],
                                 parameters: Dict[str, Any]) -> List[str]:
        """Validate parameters against OpenAPI specification."""
        # Implementation would use OpenAPI schema validation
        # For now, return empty list (no errors)
        return []
```

### **Step 3: Ports Layer - Abstract Interfaces**

**3.1 Task Registry Port**
```python
# src/molecular_analysis_dashboard/ports/task_registry_port.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain.entities.task import TaskDefinition, TaskCategory

class TaskRegistryPort(ABC):
    """Port for task registry operations."""

    @abstractmethod
    async def save(self, task: TaskDefinition) -> TaskDefinition:
        """Save a task definition."""
        pass

    @abstractmethod
    async def get_by_id(self, task_id: str) -> Optional[TaskDefinition]:
        """Get task by ID."""
        pass

    @abstractmethod
    async def list_by_category(self, category: TaskCategory) -> List[TaskDefinition]:
        """List tasks by category."""
        pass

    @abstractmethod
    async def list_active(self) -> List[TaskDefinition]:
        """List all active tasks."""
        pass

    @abstractmethod
    async def update(self, task: TaskDefinition) -> TaskDefinition:
        """Update existing task definition."""
        pass

    @abstractmethod
    async def delete(self, task_id: str) -> bool:
        """Delete task definition."""
        pass
```

**3.2 Task Executor Port**
```python
# src/molecular_analysis_dashboard/ports/task_executor_port.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..domain.entities.task import TaskDefinition
from ..domain.entities.task_execution import TaskExecution

class TaskExecutorPort(ABC):
    """Port for task execution operations."""

    @abstractmethod
    async def submit_task(self, execution: TaskExecution,
                         task_definition: TaskDefinition) -> None:
        """Submit task for async execution."""
        pass

    @abstractmethod
    async def get_execution_status(self, execution_id: str) -> TaskExecution:
        """Get current execution status."""
        pass

    @abstractmethod
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel running execution."""
        pass

    @abstractmethod
    async def get_execution_logs(self, execution_id: str) -> List[str]:
        """Get execution logs."""
        pass
```

**3.3 Service Discovery Port**
```python
# src/molecular_analysis_dashboard/ports/service_discovery_port.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ServiceRegistration:
    """Service registration information."""
    service_id: str
    task_id: str
    service_url: str
    health_check_url: Optional[str]
    status: str  # healthy, unhealthy, unknown
    capabilities: Dict[str, Any]
    last_health_check: Optional[datetime]

class ServiceDiscoveryPort(ABC):
    """Port for service discovery operations."""

    @abstractmethod
    async def register_service(self, service_id: str, task_id: str,
                              service_url: str, health_check_url: Optional[str] = None,
                              capabilities: Optional[Dict[str, Any]] = None) -> ServiceRegistration:
        """Register a new service."""
        pass

    @abstractmethod
    async def get_service(self, service_id: str) -> Optional[ServiceRegistration]:
        """Get service by ID."""
        pass

    @abstractmethod
    async def list_services_for_task(self, task_id: str) -> List[ServiceRegistration]:
        """List all services for a task."""
        pass

    @abstractmethod
    async def update_service_health(self, service_id: str,
                                   status: str) -> ServiceRegistration:
        """Update service health status."""
        pass

    @abstractmethod
    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service."""
        pass
```

### **Step 4: Adapters Layer - Implementations**

**4.1 Database Task Registry Adapter**
```python
# src/molecular_analysis_dashboard/adapters/database/task_registry_adapter.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from ...ports.task_registry_port import TaskRegistryPort
from ...domain.entities.task import TaskDefinition, TaskCategory, TaskStatus
from .models.task_models import TaskDefinitionModel

class DatabaseTaskRegistryAdapter(TaskRegistryPort):
    """Database implementation of task registry port."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def save(self, task: TaskDefinition) -> TaskDefinition:
        """Save task definition to database."""
        async with self._session_factory() as session:
            # Convert domain entity to database model
            task_model = TaskDefinitionModel(
                task_id=task.task_id,
                name=task.name,
                version=task.version,
                category=task.category.value,
                description=task.description,
                interface_spec=task.interface_spec,
                service_config=task.service_config,
                status=task.status.value,
                tags=task.tags,
                created_at=task.created_at,
                updated_at=task.updated_at
            )

            session.add(task_model)
            await session.commit()
            await session.refresh(task_model)

            # Convert back to domain entity
            return self._model_to_entity(task_model)

    async def get_by_id(self, task_id: str) -> Optional[TaskDefinition]:
        """Get task by ID."""
        async with self._session_factory() as session:
            stmt = select(TaskDefinitionModel).where(
                TaskDefinitionModel.task_id == task_id
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()

            return self._model_to_entity(model) if model else None

    async def list_by_category(self, category: TaskCategory) -> List[TaskDefinition]:
        """List tasks by category."""
        async with self._session_factory() as session:
            stmt = select(TaskDefinitionModel).where(
                TaskDefinitionModel.category == category.value
            )
            result = await session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]

    async def list_active(self) -> List[TaskDefinition]:
        """List all active tasks."""
        async with self._session_factory() as session:
            stmt = select(TaskDefinitionModel).where(
                TaskDefinitionModel.status == TaskStatus.ACTIVE.value
            )
            result = await session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]

    def _model_to_entity(self, model: TaskDefinitionModel) -> TaskDefinition:
        """Convert database model to domain entity."""
        return TaskDefinition(
            task_id=model.task_id,
            name=model.name,
            version=model.version,
            category=TaskCategory(model.category),
            description=model.description,
            interface_spec=model.interface_spec,
            service_config=model.service_config,
            status=TaskStatus(model.status),
            tags=model.tags,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
```

**4.2 Celery Task Executor Adapter**
```python
# src/molecular_analysis_dashboard/adapters/messaging/celery_task_executor.py
from typing import Dict, Any, List
from celery import Celery
from ...ports.task_executor_port import TaskExecutorPort
from ...domain.entities.task import TaskDefinition
from ...domain.entities.task_execution import TaskExecution
from ...infrastructure.celery_app import celery_app

class CeleryTaskExecutorAdapter(TaskExecutorPort):
    """Celery implementation of task executor port."""

    def __init__(self, celery_app: Celery, job_repository):
        self._celery = celery_app
        self._job_repository = job_repository

    async def submit_task(self, execution: TaskExecution,
                         task_definition: TaskDefinition) -> None:
        """Submit task for async execution via Celery."""

        # Create Celery task
        task_name = f"execute_dynamic_task"
        task_args = {
            'execution_id': execution.execution_id,
            'task_id': task_definition.task_id,
            'org_id': execution.org_id,
            'parameters': execution.parameters,
            'service_config': task_definition.service_config,
            'interface_spec': task_definition.interface_spec
        }

        # Submit to appropriate queue based on task category
        queue_name = self._get_queue_for_category(task_definition.category)

        # Send Celery task
        self._celery.send_task(
            task_name,
            kwargs=task_args,
            queue=queue_name,
            task_id=execution.execution_id
        )

        # Update execution status
        execution.status = "queued"
        await self._job_repository.update_task_execution(execution)

    async def get_execution_status(self, execution_id: str) -> TaskExecution:
        """Get execution status from database."""
        return await self._job_repository.get_task_execution(execution_id)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel Celery task execution."""
        try:
            self._celery.control.revoke(execution_id, terminate=True)

            # Update execution status in database
            execution = await self._job_repository.get_task_execution(execution_id)
            if execution:
                execution.status = "cancelled"
                await self._job_repository.update_task_execution(execution)

            return True
        except Exception:
            return False

    def _get_queue_for_category(self, category) -> str:
        """Get Celery queue name for task category."""
        queue_mapping = {
            "docking": "docking.standard",
            "analysis": "analysis.standard",
            "visualization": "visualization.standard",
            "optimization": "optimization.high_priority"
        }
        return queue_mapping.get(category.value, "tasks.default")
```

### **Step 5: Infrastructure Layer - Celery Tasks**

**5.1 Dynamic Task Execution**
```python
# src/molecular_analysis_dashboard/infrastructure/tasks.py
from celery import Celery
from typing import Dict, Any
import httpx
import asyncio
from ..domain.entities.task_execution import ExecutionStatus
from ..adapters.database.job_repository_adapter import DatabaseJobRepositoryAdapter

@celery_app.task(bind=True)
def execute_dynamic_task(self, execution_id: str, task_id: str, org_id: str,
                        parameters: Dict[str, Any], service_config: Dict[str, Any],
                        interface_spec: Dict[str, Any]):
    """Execute a dynamic task via HTTP service call."""

    try:
        # Run async execution in event loop
        return asyncio.run(_execute_task_async(
            execution_id, task_id, org_id, parameters,
            service_config, interface_spec
        ))
    except Exception as e:
        # Update execution with error
        asyncio.run(_handle_execution_error(execution_id, str(e)))
        raise

async def _execute_task_async(execution_id: str, task_id: str, org_id: str,
                             parameters: Dict[str, Any], service_config: Dict[str, Any],
                             interface_spec: Dict[str, Any]):
    """Async implementation of dynamic task execution."""

    # Get database session and repository
    job_repo = DatabaseJobRepositoryAdapter(get_async_session)

    # Update execution status to running
    execution = await job_repo.get_task_execution(execution_id)
    execution.start_execution()
    await job_repo.update_task_execution(execution)

    # Get service endpoint
    service_url = service_config.get('service_url')
    if not service_url:
        raise ValueError("No service_url found in task configuration")

    # Get execution endpoint from OpenAPI spec
    endpoint_path = _get_execution_path(interface_spec)
    full_url = f"{service_url.rstrip('/')}{endpoint_path}"

    # Execute HTTP request to task service
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            full_url,
            json=parameters,
            headers={
                'Content-Type': 'application/json',
                'X-Org-ID': org_id,
                'X-Execution-ID': execution_id
            }
        )

        if response.status_code == 200:
            results = response.json()

            # Update execution with results
            execution.complete_execution(
                results=results,
                metrics={'http_status': response.status_code}
            )
            await job_repo.update_task_execution(execution)

            return results
        else:
            error_msg = f"Task service returned {response.status_code}: {response.text}"
            execution.fail_execution(error_msg)
            await job_repo.update_task_execution(execution)
            raise Exception(error_msg)

def _get_execution_path(interface_spec: Dict[str, Any]) -> str:
    """Extract execution endpoint path from OpenAPI spec."""
    paths = interface_spec.get('paths', {})
    for path, methods in paths.items():
        if 'post' in methods:
            return path
    return '/execute'  # Default fallback

async def _handle_execution_error(execution_id: str, error_message: str):
    """Handle execution error by updating database."""
    job_repo = DatabaseJobRepositoryAdapter(get_async_session)
    execution = await job_repo.get_task_execution(execution_id)
    if execution:
        execution.fail_execution(error_message)
        await job_repo.update_task_execution(execution)
```

### **Step 6: Presentation Layer - API Routes**

**6.1 Task Registry API**
```python
# src/molecular_analysis_dashboard/presentation/api/routes/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ...use_cases.commands.register_task import RegisterTaskUseCase, RegisterTaskCommand
from ...use_cases.commands.execute_task import ExecuteTaskUseCase, ExecuteTaskCommand
from ...use_cases.queries.get_tasks import GetTasksUseCase
from ..schemas.task_schemas import (
    TaskDefinitionResponse, TaskListResponse, TaskExecutionResponse,
    RegisterTaskRequest, ExecuteTaskRequest
)
from ..dependencies import get_current_organization

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

@router.post("/", response_model=TaskDefinitionResponse)
async def register_task(
    request: RegisterTaskRequest,
    org_id: str = Depends(get_current_organization),
    register_use_case: RegisterTaskUseCase = Depends()
):
    """Register a new dynamic task definition."""

    command = RegisterTaskCommand(
        task_id=request.task_id,
        name=request.name,
        version=request.version,
        category=request.category,
        description=request.description,
        interface_spec=request.interface_spec,
        service_config=request.service_config,
        tags=request.tags
    )

    try:
        task = await register_use_case.execute(command)
        return TaskDefinitionResponse.from_entity(task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    category: Optional[str] = Query(None),
    get_tasks_use_case: GetTasksUseCase = Depends()
):
    """List available tasks, optionally filtered by category."""

    tasks = await get_tasks_use_case.execute(category=category)
    return TaskListResponse(
        tasks=[TaskDefinitionResponse.from_entity(task) for task in tasks]
    )

@router.get("/{task_id}", response_model=TaskDefinitionResponse)
async def get_task_detail(
    task_id: str,
    get_tasks_use_case: GetTasksUseCase = Depends()
):
    """Get detailed information about a specific task."""

    task = await get_tasks_use_case.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskDefinitionResponse.from_entity(task)

@router.post("/{task_id}/execute", response_model=TaskExecutionResponse)
async def execute_task(
    task_id: str,
    request: ExecuteTaskRequest,
    org_id: str = Depends(get_current_organization),
    execute_use_case: ExecuteTaskUseCase = Depends()
):
    """Execute a dynamic task with provided parameters."""

    command = ExecuteTaskCommand(
        task_id=task_id,
        org_id=org_id,
        parameters=request.parameters,
        job_id=request.job_id
    )

    try:
        execution = await execute_use_case.execute(command)
        return TaskExecutionResponse.from_entity(execution)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/executions/{execution_id}", response_model=TaskExecutionResponse)
async def get_execution_status(
    execution_id: str,
    org_id: str = Depends(get_current_organization),
    execute_use_case: ExecuteTaskUseCase = Depends()
):
    """Get status of a task execution."""

    execution = await execute_use_case.get_execution_status(execution_id)
    if not execution or execution.org_id != org_id:
        raise HTTPException(status_code=404, detail="Execution not found")

    return TaskExecutionResponse.from_entity(execution)
```

---

## 📋 **Phase 4B: Docking Engines Implementation**

### **Step 1: Enhanced Docking Engine Adapters**

**1.1 AutoDock Vina Enhanced Adapter**
```python
# src/molecular_analysis_dashboard/adapters/external/enhanced_vina_adapter.py
from pathlib import Path
from typing import Dict, Any, List
import asyncio
import subprocess
import json
from ...ports.docking_engine_port import DockingEnginePort, DockingInput, DockingResult
from ...domain.entities.task_execution import ExecutionStatus

class EnhancedVinaAdapter(DockingEnginePort):
    """Enhanced AutoDock Vina adapter with containerization support."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.use_containers = config.get('use_containers', True)
        self.container_image = config.get('container_image', 'docking/vina:latest')
        self.executable_path = config.get('executable_path', '/usr/local/bin/vina')
        self.max_concurrent = config.get('max_concurrent_jobs', 5)
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

    async def execute_docking(self, docking_input: DockingInput) -> DockingResult:
        """Execute AutoDock Vina with enhanced configuration."""

        async with self._semaphore:  # Limit concurrent executions
            if self.use_containers:
                return await self._execute_containerized(docking_input)
            else:
                return await self._execute_binary(docking_input)

    async def _execute_containerized(self, docking_input: DockingInput) -> DockingResult:
        """Execute Vina in Docker container."""

        # Prepare container volumes
        container_workdir = "/app/work"
        volumes = {
            str(docking_input.receptor_file.parent): {"bind": f"{container_workdir}/input", "mode": "ro"},
            str(docking_input.output_dir): {"bind": f"{container_workdir}/output", "mode": "rw"}
        }

        # Build Vina command
        vina_cmd = self._build_vina_command(docking_input, container_workdir)

        # Docker run command
        docker_cmd = [
            "docker", "run", "--rm",
            "--memory", "2g",
            "--cpus", "2.0",
            "-v", f"{docking_input.receptor_file.parent}:{container_workdir}/input:ro",
            "-v", f"{docking_input.output_dir}:{container_workdir}/output:rw",
            self.container_image
        ] + vina_cmd

        try:
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=docking_input.timeout_seconds
            )

            if process.returncode == 0:
                return await self._parse_vina_results(docking_input, stdout.decode())
            else:
                return DockingResult(
                    success=False,
                    error_message=f"Vina execution failed: {stderr.decode()}",
                    output_files=[],
                    scores=[],
                    poses=0
                )

        except asyncio.TimeoutError:
            return DockingResult(
                success=False,
                error_message=f"Vina execution timed out after {docking_input.timeout_seconds}s",
                output_files=[],
                scores=[],
                poses=0
            )

    def _build_vina_command(self, docking_input: DockingInput, workdir: str) -> List[str]:
        """Build Vina command line arguments."""

        receptor_filename = docking_input.receptor_file.name
        ligand_filename = docking_input.ligand_file.name
        output_filename = f"{docking_input.job_id}_output.pdbqt"

        cmd = [
            "vina",
            "--receptor", f"{workdir}/input/{receptor_filename}",
            "--ligand", f"{workdir}/input/{ligand_filename}",
            "--out", f"{workdir}/output/{output_filename}",
            "--log", f"{workdir}/output/{docking_input.job_id}_log.txt"
        ]

        # Add binding site parameters
        if docking_input.binding_site:
            site = docking_input.binding_site
            cmd.extend([
                "--center_x", str(site.get('center_x', 0)),
                "--center_y", str(site.get('center_y', 0)),
                "--center_z", str(site.get('center_z', 0)),
                "--size_x", str(site.get('size_x', 20)),
                "--size_y", str(site.get('size_y', 20)),
                "--size_z", str(site.get('size_z', 20))
            ])

        # Add engine-specific parameters
        if docking_input.engine_params:
            for key, value in docking_input.engine_params.items():
                cmd.extend([f"--{key}", str(value)])

        return cmd

    async def _parse_vina_results(self, docking_input: DockingInput,
                                 stdout: str) -> DockingResult:
        """Parse Vina execution results."""

        output_files = []
        scores = []
        poses = 0

        # Look for output files
        output_pdbqt = docking_input.output_dir / f"{docking_input.job_id}_output.pdbqt"
        log_file = docking_input.output_dir / f"{docking_input.job_id}_log.txt"

        if output_pdbqt.exists():
            output_files.append(output_pdbqt)
            poses = self._count_poses_in_pdbqt(output_pdbqt)

        if log_file.exists():
            output_files.append(log_file)
            scores = self._extract_scores_from_log(log_file)

        return DockingResult(
            success=True,
            output_files=output_files,
            scores=scores,
            poses=poses,
            execution_time_seconds=0,  # Would be calculated in wrapper
            engine_version=await self._get_vina_version(),
            command_executed=" ".join(self._build_vina_command(docking_input, "/app/work"))
        )

    def _count_poses_in_pdbqt(self, pdbqt_file: Path) -> int:
        """Count number of poses in PDBQT output file."""
        pose_count = 0
        try:
            with open(pdbqt_file, 'r') as f:
                for line in f:
                    if line.startswith('MODEL'):
                        pose_count += 1
        except Exception:
            pass
        return pose_count

    def _extract_scores_from_log(self, log_file: Path) -> List[float]:
        """Extract binding affinity scores from Vina log."""
        scores = []
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                # Parse Vina output format for binding affinities
                # This would contain regex parsing for score extraction
                pass
        except Exception:
            pass
        return scores

    async def _get_vina_version(self) -> str:
        """Get Vina version information."""
        try:
            if self.use_containers:
                cmd = ["docker", "run", "--rm", self.container_image, "vina", "--version"]
            else:
                cmd = [self.executable_path, "--version"]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return stdout.decode().strip()
        except Exception:
            return "unknown"

    async def health_check(self) -> bool:
        """Check if Vina engine is available."""
        try:
            version = await self._get_vina_version()
            return version != "unknown"
        except Exception:
            return False
```

**1.2 Smina Adapter Implementation**
```python
# src/molecular_analysis_dashboard/adapters/external/smina_adapter.py
from pathlib import Path
from typing import Dict, Any, List
import asyncio
from .enhanced_vina_adapter import EnhancedVinaAdapter

class SminaAdapter(EnhancedVinaAdapter):
    """Smina docking engine adapter (inherits from Vina with modifications)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.container_image = config.get('container_image', 'docking/smina:latest')
        self.executable_path = config.get('executable_path', '/usr/local/bin/smina')

    def _build_vina_command(self, docking_input: DockingInput, workdir: str) -> List[str]:
        """Build Smina command (similar to Vina but with Smina binary)."""

        receptor_filename = docking_input.receptor_file.name
        ligand_filename = docking_input.ligand_file.name
        output_filename = f"{docking_input.job_id}_output.pdbqt"

        cmd = [
            "smina",  # Use smina instead of vina
            "--receptor", f"{workdir}/input/{receptor_filename}",
            "--ligand", f"{workdir}/input/{ligand_filename}",
            "--out", f"{workdir}/output/{output_filename}",
            "--log", f"{workdir}/output/{docking_input.job_id}_log.txt"
        ]

        # Add Smina-specific parameters
        cmd.extend([
            "--scoring", "vinardo",  # Smina default scoring function
            "--minimize"  # Energy minimization
        ])

        # Add binding site and other parameters (same as Vina)
        if docking_input.binding_site:
            site = docking_input.binding_site
            cmd.extend([
                "--center_x", str(site.get('center_x', 0)),
                "--center_y", str(site.get('center_y', 0)),
                "--center_z", str(site.get('center_z', 0)),
                "--size_x", str(site.get('size_x', 20)),
                "--size_y", str(site.get('size_y', 20)),
                "--size_z", str(site.get('size_z', 20))
            ])

        return cmd
```

**1.3 Gnina Adapter Implementation**
```python
# src/molecular_analysis_dashboard/adapters/external/gnina_adapter.py
from pathlib import Path
from typing import Dict, Any, List
import asyncio
from .enhanced_vina_adapter import EnhancedVinaAdapter

class GninaAdapter(EnhancedVinaAdapter):
    """Gnina docking engine adapter with CNN scoring."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.container_image = config.get('container_image', 'docking/gnina:latest')
        self.executable_path = config.get('executable_path', '/usr/local/bin/gnina')
        self.use_cnn = config.get('use_cnn_scoring', True)

    def _build_vina_command(self, docking_input: DockingInput, workdir: str) -> List[str]:
        """Build Gnina command with CNN scoring options."""

        receptor_filename = docking_input.receptor_file.name
        ligand_filename = docking_input.ligand_file.name
        output_filename = f"{docking_input.job_id}_output.sdf"

        cmd = [
            "gnina",
            "--receptor", f"{workdir}/input/{receptor_filename}",
            "--ligand", f"{workdir}/input/{ligand_filename}",
            "--out", f"{workdir}/output/{output_filename}",
            "--log", f"{workdir}/output/{docking_input.job_id}_log.txt"
        ]

        # Add Gnina-specific CNN scoring
        if self.use_cnn:
            cmd.extend([
                "--cnn_scoring", "rescore",
                "--cnn", "dense",  # Use dense CNN model
                "--cnn_model", "/models/dense_ensemble.caffemodel"
            ])

        # Add binding site parameters
        if docking_input.binding_site:
            site = docking_input.binding_site
            cmd.extend([
                "--center_x", str(site.get('center_x', 0)),
                "--center_y", str(site.get('center_y', 0)),
                "--center_z", str(site.get('center_z', 0)),
                "--size_x", str(site.get('size_x', 20)),
                "--size_y", str(site.get('size_y', 20)),
                "--size_z", str(site.get('size_z', 20))
            ])

        # Gnina-specific parameters
        cmd.extend([
            "--exhaustiveness", "16",  # Higher search exhaustiveness
            "--num_modes", "20"        # More output poses
        ])

        return cmd

    async def _parse_vina_results(self, docking_input: DockingInput,
                                 stdout: str) -> DockingResult:
        """Parse Gnina results (SDF format with CNN scores)."""

        output_files = []
        scores = []
        poses = 0

        # Gnina outputs SDF files instead of PDBQT
        output_sdf = docking_input.output_dir / f"{docking_input.job_id}_output.sdf"
        log_file = docking_input.output_dir / f"{docking_input.job_id}_log.txt"

        if output_sdf.exists():
            output_files.append(output_sdf)
            poses, scores = self._parse_sdf_results(output_sdf)

        if log_file.exists():
            output_files.append(log_file)

        return DockingResult(
            success=True,
            output_files=output_files,
            scores=scores,
            poses=poses,
            execution_time_seconds=0,
            engine_version=await self._get_gnina_version(),
            command_executed=" ".join(self._build_vina_command(docking_input, "/app/work"))
        )

    def _parse_sdf_results(self, sdf_file: Path) -> tuple[int, List[float]]:
        """Parse SDF file to extract poses and CNN scores."""
        poses = 0
        scores = []

        try:
            with open(sdf_file, 'r') as f:
                content = f.read()
                # Count molecules (poses) in SDF
                poses = content.count('$$$$')

                # Extract CNN scores from SDF properties
                # This would contain SDF parsing logic to extract
                # the CNN affinity scores from molecule properties

        except Exception:
            pass

        return poses, scores

    async def _get_gnina_version(self) -> str:
        """Get Gnina version information."""
        try:
            if self.use_containers:
                cmd = ["docker", "run", "--rm", self.container_image, "gnina", "--version"]
            else:
                cmd = [self.executable_path, "--version"]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return stdout.decode().strip()
        except Exception:
            return "unknown"
```

---

## 📋 **Phase 4C: Advanced Pipelines Implementation**

### **Step 1: Enhanced Pipeline Domain Entity**

```python
# src/molecular_analysis_dashboard/domain/entities/enhanced_pipeline.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from datetime import datetime

class PipelineExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    OPTIMIZED = "optimized"

class StepCondition(Enum):
    ALWAYS = "always"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    CONDITIONAL = "conditional"

@dataclass
class PipelineStep:
    """Individual step in pipeline execution."""
    step_id: str
    task_id: str
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: StepCondition = StepCondition.ALWAYS
    conditional_logic: Optional[Dict[str, Any]] = None
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: int = 3600
    retry_count: int = 0

    def should_execute(self, previous_results: Dict[str, Any]) -> bool:
        """Determine if step should execute based on conditions."""
        if self.condition == StepCondition.ALWAYS:
            return True
        elif self.condition == StepCondition.CONDITIONAL and self.conditional_logic:
            return self._evaluate_conditional_logic(previous_results)
        else:
            # Check dependency results for ON_SUCCESS/ON_FAILURE
            return self._check_dependency_conditions(previous_results)

    def _evaluate_conditional_logic(self, results: Dict[str, Any]) -> bool:
        """Evaluate conditional logic expression."""
        # Implementation would include expression evaluation
        # For now, return True as placeholder
        return True

    def _check_dependency_conditions(self, results: Dict[str, Any]) -> bool:
        """Check if dependencies meet condition requirements."""
        for dep_step_id in self.depends_on:
            dep_result = results.get(dep_step_id)
            if not dep_result:
                return False

            if self.condition == StepCondition.ON_SUCCESS:
                if not dep_result.get('success', False):
                    return False
            elif self.condition == StepCondition.ON_FAILURE:
                if dep_result.get('success', True):
                    return False

        return True

@dataclass
class ParameterOptimization:
    """Parameter optimization configuration."""
    enabled: bool = False
    method: str = "grid_search"  # grid_search, random_search, bayesian
    parameters: Dict[str, Any] = field(default_factory=dict)
    optimization_metric: str = "binding_affinity"
    max_iterations: int = 10
    target_value: Optional[float] = None

@dataclass
class EnhancedPipeline:
    """Advanced pipeline with conditional execution and optimization."""

    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    org_id: str = ""
    steps: List[PipelineStep] = field(default_factory=list)
    execution_mode: PipelineExecutionMode = PipelineExecutionMode.SEQUENTIAL
    parameter_optimization: Optional[ParameterOptimization] = None
    global_parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    is_template: bool = False
    version: str = "1.0.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @classmethod
    def create(cls, name: str, description: str, org_id: str,
               steps: List[PipelineStep], **kwargs) -> 'EnhancedPipeline':
        """Factory method for creating enhanced pipelines."""

        # Validate step dependencies
        cls._validate_step_dependencies(steps)

        return cls(
            name=name,
            description=description,
            org_id=org_id,
            steps=steps,
            **kwargs
        )

    @staticmethod
    def _validate_step_dependencies(steps: List[PipelineStep]) -> None:
        """Validate that step dependencies are valid."""
        step_ids = {step.step_id for step in steps}

        for step in steps:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    raise ValueError(f"Step {step.step_id} depends on non-existent step {dep_id}")

    def get_execution_order(self) -> List[List[str]]:
        """Get step execution order considering dependencies."""
        if self.execution_mode == PipelineExecutionMode.SEQUENTIAL:
            return [[step.step_id] for step in self.steps]
        elif self.execution_mode == PipelineExecutionMode.PARALLEL:
            return [step.step_id for step in self.steps if not step.depends_on], \
                   [step.step_id for step in self.steps if step.depends_on]
        else:  # OPTIMIZED
            return self._calculate_optimal_execution_order()

    def _calculate_optimal_execution_order(self) -> List[List[str]]:
        """Calculate optimal execution order based on dependencies."""
        # Implementation would use topological sort
        # For now, return sequential order
        return [[step.step_id] for step in self.steps]

    def should_optimize_parameters(self) -> bool:
        """Check if parameter optimization is enabled."""
        return (self.parameter_optimization is not None and
                self.parameter_optimization.enabled)
```

---

## 🧪 **Testing Implementation Guide**

### **Unit Test Examples**

```python
# tests/unit/domain/entities/test_task_definition.py
import pytest
from src.molecular_analysis_dashboard.domain.entities.task import TaskDefinition, TaskCategory

def test_task_definition_creation():
    """Test creating a valid task definition."""
    interface_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test Task", "version": "1.0.0"},
        "paths": {
            "/execute": {
                "post": {
                    "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}}
                }
            }
        }
    }

    task = TaskDefinition.create(
        task_id="test-task",
        name="Test Task",
        version="1.0.0",
        category=TaskCategory.DOCKING,
        interface_spec=interface_spec
    )

    assert task.task_id == "test-task"
    assert task.category == TaskCategory.DOCKING
    assert task.get_execution_endpoint() == "/execute"

def test_invalid_openapi_spec():
    """Test that invalid OpenAPI spec raises error."""
    invalid_spec = {"invalid": "spec"}

    with pytest.raises(ValueError, match="Invalid OpenAPI specification"):
        TaskDefinition.create(
            task_id="test-task",
            name="Test Task",
            version="1.0.0",
            category=TaskCategory.DOCKING,
            interface_spec=invalid_spec
        )
```

### **Integration Test Examples**

```python
# tests/integration/test_task_execution_flow.py
import pytest
from unittest.mock import Mock, AsyncMock
import asyncio

@pytest.mark.asyncio
async def test_complete_task_execution_flow():
    """Test complete task execution from registration to results."""

    # Setup test data
    task_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Molecular Docking", "version": "1.0.0"},
        "paths": {"/execute": {"post": {"responses": {"200": {"description": "Success"}}}}}
    }

    # Mock dependencies
    task_registry = Mock()
    task_executor = Mock()
    job_repository = Mock()

    # Setup async methods
    task_registry.get_by_id = AsyncMock(return_value=TaskDefinition.create(
        task_id="molecular-docking",
        name="Molecular Docking",
        version="1.0.0",
        category=TaskCategory.DOCKING,
        interface_spec=task_spec
    ))

    job_repository.save_task_execution = AsyncMock()
    task_executor.submit_task = AsyncMock()

    # Execute use case
    execute_use_case = ExecuteTaskUseCase(task_registry, task_executor, job_repository)

    command = ExecuteTaskCommand(
        task_id="molecular-docking",
        org_id="test-org",
        parameters={"receptor_file": "protein.pdb", "ligand_file": "ligand.sdf"}
    )

    result = await execute_use_case.execute(command)

    # Verify results
    assert result.task_id == "molecular-docking"
    assert result.org_id == "test-org"
    assert result.status == ExecutionStatus.SUBMITTED

    # Verify interactions
    task_registry.get_by_id.assert_called_once_with("molecular-docking")
    job_repository.save_task_execution.assert_called_once()
    task_executor.submit_task.assert_called_once()
```

---

## 📈 **Performance Optimization Guidelines**

### **Database Optimization**
```sql
-- Create indexes for task execution queries
CREATE INDEX CONCURRENTLY idx_task_executions_org_status
ON task_executions (org_id, status) WHERE status != 'completed';

CREATE INDEX CONCURRENTLY idx_task_executions_task_created
ON task_executions (task_id, created_at DESC);

-- Partition large tables by org_id or date
CREATE TABLE task_executions_partitioned (
    LIKE task_executions INCLUDING ALL
) PARTITION BY HASH (org_id);
```

### **Caching Strategy**
```python
# Use Redis for caching task definitions and frequent queries
from redis.asyncio import Redis
from typing import Optional

class CachedTaskRegistryAdapter(TaskRegistryPort):
    """Task registry with Redis caching."""

    def __init__(self, base_adapter: TaskRegistryPort, redis: Redis):
        self._base = base_adapter
        self._redis = redis
        self._cache_ttl = 300  # 5 minutes

    async def get_by_id(self, task_id: str) -> Optional[TaskDefinition]:
        # Try cache first
        cache_key = f"task:{task_id}"
        cached = await self._redis.get(cache_key)

        if cached:
            return TaskDefinition(**json.loads(cached))

        # Fallback to database
        task = await self._base.get_by_id(task_id)

        if task:
            # Cache the result
            await self._redis.setex(
                cache_key,
                self._cache_ttl,
                json.dumps(asdict(task), default=str)
            )

        return task
```

---

## 🚀 **Deployment Instructions**

### **Container Configuration**
```yaml
# docker-compose.phase4.yml
version: '3.8'
services:
  # Enhanced API with task system
  api-enhanced:
    build:
      context: .
      dockerfile: docker/Dockerfile.api-enhanced
    environment:
      - TASK_REGISTRY_ENABLED=true
      - DOCKING_ENGINES=vina,smina,gnina
      - PIPELINE_OPTIMIZATION_ENABLED=true
    depends_on:
      - postgres
      - redis
      - task-registry

  # Task registry service
  task-registry:
    build:
      context: .
      dockerfile: docker/Dockerfile.task-registry
    environment:
      - DATABASE_URL=${METADATA_DATABASE_URL}
      - REDIS_URL=${REDIS_URL}

  # Enhanced workers with all docking engines
  worker-docking-all:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker-docking-all
    environment:
      - CELERY_QUEUES=docking.vina,docking.smina,docking.gnina
      - DOCKING_CONTAINER_REGISTRY=${CONTAINER_REGISTRY}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - docking_data:/app/data
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '6.0'
          memory: 12G
```

### **Environment Variables**
```bash
# Phase 4 Configuration
TASK_SYSTEM_ENABLED=true
DYNAMIC_TASK_DISCOVERY=true
PIPELINE_OPTIMIZATION_ENABLED=true

# Docking Engine Configuration
DOCKING_ENGINES=vina,smina,gnina
DOCKING_CONTAINER_REGISTRY=localhost:5000
DOCKING_MAX_CONCURRENT_JOBS=20

# Service Discovery
SERVICE_DISCOVERY_ENABLED=true
SERVICE_HEALTH_CHECK_INTERVAL=30

# Performance Settings
TASK_EXECUTION_TIMEOUT=7200
PIPELINE_MAX_STEPS=50
PARAMETER_OPTIMIZATION_MAX_ITERATIONS=100
```

---

This comprehensive implementation guide provides detailed step-by-step instructions for implementing Phase 4, maintaining alignment with Clean Architecture principles and existing system documentation. Each component builds on the established patterns while adding the advanced capabilities needed for the dynamic task system and molecular docking integration.

*Continue to Part 2 for frontend implementation, WebSocket integration, and 3D visualization components...*
