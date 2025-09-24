"""
Task management API routes for molecular analysis dashboard.

This module defines FastAPI routes for task management operations, providing
RESTful endpoints to list, retrieve, and filter tasks from the database.
Supports multi-tenant organization filtering and graceful fallback handling.

Responsibilities:
- Provide REST API endpoints for task operations
- Handle organization-scoped filtering for multi-tenant support
- Transform database objects to API responses
- Provide proper error handling and HTTP status codes

Dependencies:
- fastapi: For HTTP routing and dependency injection
- sqlalchemy: For database queries and session management
- ..schemas.tasks: For response schemas
- ..services.task_transformer: For data transformation
- ....infrastructure.database: For database session management

Assumptions:
- Database models are available in database/models/metadata
- Organization filtering is required for production environments
- TaskDefinition model has org_id, task_id, task_metadata, and is_active fields
- Graceful fallback when database is unavailable
"""

import os

# Import database models
import sys
from typing import List, Optional, Sequence
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....adapters.external.ligand_prep_adapter import RDKitLigandPrepAdapter
from ....adapters.external.neurosnap_adapter import NeuroSnapAdapter
from ....domain.entities.docking_job import MolecularStructure
from ....infrastructure.database import get_metadata_session
from ....use_cases.commands.execute_docking_task import (
    DockingTaskExecution,
    DockingTaskRequest,
    ExecuteDockingTaskUseCase,
)
from ..schemas.task_execution import (
    DockingPoseSchema,
    DockingResultsSchema,
    JobStatusSchema,
    TaskExecutionRequest,
    TaskExecutionResponse,
    TaskExecutionStatusResponse,
)
from ..schemas.tasks import ErrorResponse, TaskDetailResponse, TaskListResponse
from ..services.task_transformer import (
    extract_api_specification,
    extract_service_configuration,
    transform_task_definition_to_template,
    transform_task_definitions_to_templates,
)

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "database")
)

try:
    from models.metadata import TaskDefinition
except ImportError:
    # Fallback for when database models aren't available
    TaskDefinition = None

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get(
    "",
    response_model=TaskListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="List all tasks",
    description="Get a list of all available tasks for the organization",
)
async def list_tasks(
    org_id: Optional[str] = Query(None, description="Organization ID (required for production)"),
    category: Optional[str] = Query(None, description="Filter by task category"),
    active_only: bool = Query(True, description="Return only active tasks"),
    db: AsyncSession = Depends(get_metadata_session),
) -> TaskListResponse:
    """List all available tasks for an organization.

    Retrieves tasks from the database with optional filtering by category and
    organization. Supports multi-tenant access control and graceful fallback
    when database is unavailable.

    Args:
        org_id (Optional[str]): Organization UUID for multi-tenant filtering.
            Required in production environments. Defaults to None for demo mode.
        category (Optional[str]): Filter tasks by category (autodock_vina,
            autodock4, schrodinger, custom). Defaults to None (all categories).
        active_only (bool): Whether to return only active tasks. Defaults to True.
        db (AsyncSession): Database session dependency injected by FastAPI.

    Returns:
        TaskListResponse: Response containing:
            - tasks: List of TaskTemplate objects with frontend-compatible format
            - total_count: Total number of tasks returned
            - organization_id: Organization identifier used for filtering

    Raises:
        HTTPException: 500 if database models unavailable or query fails

    Example:
        GET /api/v1/tasks?org_id=123e4567-e89b-12d3-a456-426614174000&category=autodock_vina

        Response:
        {
            "tasks": [...],
            "total_count": 5,
            "organization_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    """

    if TaskDefinition is None:
        # SECURITY: Fallback response when database is not available
        # NOTE: This prevents API failures during database maintenance
        raise HTTPException(
            status_code=500,
            detail="Database models not available. Please ensure database is properly configured.",
        )

    try:
        # Build query
        query = select(TaskDefinition)

        # Add organization filter (required for production)
        if org_id:
            query = query.where(TaskDefinition.org_id == UUID(org_id))

        # Add category filter
        if category:
            query = query.where(TaskDefinition.task_metadata["category"].astext == category)

        # Add active filter
        if active_only:
            query = query.where(TaskDefinition.is_active == True)

        # Order by name
        query = query.order_by(TaskDefinition.task_metadata["name"].astext)

        # Execute query
        result = await db.execute(query)
        task_definitions: Sequence = result.scalars().all()

        # RATIONALE: Convert Sequence to List for transformer compatibility
        task_list = list(task_definitions)

        # Transform to frontend format
        tasks = transform_task_definitions_to_templates(task_list)

        # Use first task's org_id or provided org_id or default
        response_org_id = org_id or (
            str(task_definitions[0].org_id) if task_definitions else "demo-org"
        )

        return TaskListResponse(
            tasks=tasks, total_count=len(tasks), organization_id=response_org_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")


@router.get(
    "/{task_id}",
    response_model=TaskDetailResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get task details",
    description="Get detailed information about a specific task including API specification",
)
async def get_task_detail(
    task_id: str,
    org_id: Optional[str] = Query(None, description="Organization ID"),
    db: AsyncSession = Depends(get_metadata_session),
) -> TaskDetailResponse:
    """Get detailed information about a specific task.

    Retrieves comprehensive task information including metadata, API specification,
    and service configuration. Supports organization filtering for multi-tenant access.

    Args:
        task_id (str): Unique task identifier (e.g., 'molecular-docking-basic')
        org_id (Optional[str]): Organization UUID for access control.
            Defaults to None for demo mode.
        db (AsyncSession): Database session dependency injected by FastAPI.

    Returns:
        TaskDetailResponse: Detailed task information containing:
            - task: Complete TaskTemplate with all metadata and parameters
            - api_specification: OpenAPI 3.0 spec for task execution endpoints
            - service_configuration: Deployment config (engine, timeout, etc.)

    Raises:
        HTTPException: 404 if task not found, 500 if database unavailable

    Example:
        GET /api/v1/tasks/molecular-docking-basic?org_id=123e4567-e89b-12d3-a456-426614174000

        Response:
        {
            "task": {"id": "molecular-docking-basic", ...},
            "api_specification": {"openapi": "3.0.0", ...},
            "service_configuration": {"engine": "vina", "timeout": 3600}
        }
    """

    if TaskDefinition is None:
        raise HTTPException(
            status_code=500,
            detail="Database models not available. Please ensure database is properly configured.",
        )

    try:
        # Build query
        query = select(TaskDefinition).where(TaskDefinition.task_id == task_id)

        # Add organization filter if provided
        if org_id:
            query = query.where(TaskDefinition.org_id == UUID(org_id))

        # Execute query
        result = await db.execute(query)
        task_definition = result.scalar_one_or_none()

        if not task_definition:
            raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

        # Transform to frontend format
        task = transform_task_definition_to_template(task_definition)
        api_spec = extract_api_specification(task_definition)
        service_config = extract_service_configuration(task_definition)

        return TaskDetailResponse(
            task=task, api_specification=api_spec, service_configuration=service_config
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task details: {str(e)}")


@router.get(
    "/categories",
    response_model=List[str],
    summary="List task categories",
    description="Get a list of all available task categories",
)
async def list_task_categories(
    org_id: Optional[str] = Query(None, description="Organization ID"),
    db: AsyncSession = Depends(get_metadata_session),
) -> List[str]:
    """List all available task categories.

    Retrieves distinct task categories from the database, optionally filtered
    by organization. Provides fallback categories when database is unavailable.

    Args:
        org_id (Optional[str]): Organization UUID for filtering categories.
            Defaults to None for all organizations.
        db (AsyncSession): Database session dependency injected by FastAPI.

    Returns:
        List[str]: List of available category identifiers:
            - autodock_vina: AutoDock Vina molecular docking
            - autodock4: AutoDock 4 legacy molecular docking
            - schrodinger: Schrödinger suite integration
            - custom: User-defined custom tasks

    Raises:
        Never raises - provides graceful fallback to default categories

    Example:
        GET /api/v1/tasks/categories

        Response:
        ["autodock_vina", "autodock4", "schrodinger", "custom"]
    """

    # NOTE: Always provide fallback categories for graceful degradation
    default_categories = ["autodock_vina", "autodock4", "schrodinger", "custom"]

    if TaskDefinition is None:
        return default_categories

    try:
        # Build query to get distinct categories
        query = select(TaskDefinition.task_metadata["category"].astext.distinct())

        # Add organization filter if provided
        if org_id:
            query = query.where(TaskDefinition.org_id == UUID(org_id))

        # Add active filter
        query = query.where(TaskDefinition.is_active == True)

        # Execute query
        result = await db.execute(query)
        categories = [row[0] for row in result.fetchall() if row[0]]

        return categories or default_categories

    except Exception:
        # SECURITY: Never expose database errors to API consumers
        # NOTE: Return default categories on any error for reliability
        return default_categories


# Task Execution Endpoints


@router.post(
    "/{task_id}/execute",
    response_model=TaskExecutionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Execute a molecular task",
    description="Submit a molecular task for execution (GNINA docking, analysis, etc.)",
)
async def execute_task(
    task_id: str,
    request: TaskExecutionRequest = Body(...),
    org_id: Optional[str] = Query(None, description="Organization ID"),
) -> TaskExecutionResponse:
    """Execute a molecular analysis task.

    Submits a molecular task for execution using the appropriate engine
    (GNINA for molecular docking). Supports both immediate and asynchronous
    execution depending on the task type and complexity.

    Args:
        task_id: Task identifier (e.g., 'gnina-molecular-docking')
        request: Task execution parameters and configuration
        org_id: Organization ID for multi-tenant access control

    Returns:
        TaskExecutionResponse: Execution tracking information with job ID

    Raises:
        HTTPException: 400 for invalid parameters, 404 for unknown task, 500 for execution errors

    Example:
        POST /api/v1/tasks/gnina-molecular-docking/execute
        {
            "receptor": {"name": "EGFR", "format": "pdb", "data": "HEADER..."},
            "ligand": "osimertinib",
            "binding_site": {"center_x": 25.5, "center_y": 10.2, "center_z": 15.8, ...}
        }
    """
    try:
        # Validate task exists and is supported
        if task_id not in ["gnina-molecular-docking", "molecular-docking", "docking"]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "TASK_NOT_FOUND",
                        "message": f"Task '{task_id}' not found or not supported",
                        "details": {
                            "supported_tasks": ["gnina-molecular-docking", "molecular-docking"],
                            "requested_task": task_id,
                        },
                    }
                },
            )

        # Convert request to use case format
        # Handle receptor conversion
        if isinstance(request.receptor, dict):
            receptor_structure = MolecularStructure(
                name=request.receptor.get("name", "receptor"),
                format=request.receptor.get("format", "pdb"),
                data=request.receptor.get("data", ""),
            )
        else:
            # Convert Pydantic model to domain entity
            receptor_structure = MolecularStructure(
                name=request.receptor.name,
                format=request.receptor.format,
                data=request.receptor.data,
                properties=request.receptor.properties or {},
            )

        # Handle ligand conversion
        ligand_input = request.ligand
        if isinstance(request.ligand, str):
            # String (drug name) - pass as is
            ligand_input = request.ligand
        elif isinstance(request.ligand, dict):
            # Dictionary - convert to domain entity
            ligand_input = MolecularStructure(
                name=request.ligand.get("name", "ligand"),
                format=request.ligand.get("format", "sdf"),
                data=request.ligand.get("data", ""),
                properties=request.ligand.get("properties", {}),
            )
        else:
            # Pydantic model - convert to domain entity
            ligand_input = MolecularStructure(
                name=request.ligand.name,
                format=request.ligand.format,
                data=request.ligand.data,
                properties=request.ligand.properties or {},
            )

        # Create use case request
        use_case_request = DockingTaskRequest(
            receptor=receptor_structure,
            ligand=ligand_input,
            binding_site=request.binding_site.dict() if request.binding_site else None,
            job_note=request.job_note,
            max_poses=request.max_poses,
            energy_range=request.energy_range,
            exhaustiveness=request.exhaustiveness,
            timeout_minutes=request.timeout_minutes,
            organization_id=org_id or request.organization_id,
            user_id=request.user_id,
            task_metadata=request.task_metadata or {},
        )

        # Initialize adapters (in production, these would be injected as dependencies)
        api_key = os.getenv("NEUROSNAP_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "CONFIGURATION_ERROR",
                        "message": "NeuroSnap API key not configured",
                        "details": {"required_env_var": "NEUROSNAP_API_KEY"},
                    }
                },
            )

        neurosnap_adapter = NeuroSnapAdapter(api_key=api_key)
        ligand_prep_adapter = RDKitLigandPrepAdapter()

        # Initialize and execute use case
        use_case = ExecuteDockingTaskUseCase(
            docking_adapter=neurosnap_adapter,
            ligand_prep_adapter=ligand_prep_adapter,
            neurosnap_adapter=neurosnap_adapter,
        )

        # Execute the task
        execution = await use_case.execute(use_case_request)

        # Convert results to API format
        results_schema = None
        if execution.results:
            poses = [
                DockingPoseSchema(
                    rank=pose.rank,
                    affinity=pose.affinity,
                    rmsd_lb=pose.rmsd_lb,
                    rmsd_ub=pose.rmsd_ub,
                    confidence_score=pose.confidence_score,
                    pose_data=pose.pose_data,
                )
                for pose in execution.results.poses
            ]

            best_pose_schema = None
            if execution.results.best_pose:
                best_pose_schema = DockingPoseSchema(
                    rank=execution.results.best_pose.rank,
                    affinity=execution.results.best_pose.affinity,
                    rmsd_lb=execution.results.best_pose.rmsd_lb,
                    rmsd_ub=execution.results.best_pose.rmsd_ub,
                    confidence_score=execution.results.best_pose.confidence_score,
                    pose_data=execution.results.best_pose.pose_data,
                )

            results_schema = DockingResultsSchema(
                poses=poses,
                best_pose=best_pose_schema,
                execution_time=execution.results.execution_time,
                engine_version=execution.results.engine_version,
                parameters=execution.results.parameters,
                metadata=execution.results.metadata,
            )

        # Calculate progress percentage
        progress = 0.0
        current_step = "pending"
        if execution.status == JobStatusSchema.RUNNING:
            progress = 50.0
            current_step = "running"
        elif execution.status == JobStatusSchema.COMPLETED:
            progress = 100.0
            current_step = "completed"
        elif execution.status == JobStatusSchema.FAILED:
            progress = 0.0
            current_step = "failed"

        response = TaskExecutionResponse(
            execution_id=execution.execution_id,
            job_id=execution.job_id,
            status=JobStatusSchema(execution.status.value),
            task_id=task_id,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            estimated_completion=execution.estimated_completion,
            results=results_schema,
            error_message=execution.error_message,
            retry_count=execution.retry_count,
            progress_percentage=progress,
            current_step=current_step,
            organization_id=org_id or request.organization_id,
            user_id=request.user_id,
        )

        # Clean up adapter connections
        await neurosnap_adapter.close()

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": f"Failed to execute task: {str(e)}",
                    "details": {"task_id": task_id},
                }
            },
        )


@router.get(
    "/executions/{execution_id}/status",
    response_model=TaskExecutionStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Execution not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get execution status",
    description="Get the current status of a task execution",
)
async def get_execution_status(
    execution_id: UUID,
    org_id: Optional[str] = Query(None, description="Organization ID"),
) -> TaskExecutionStatusResponse:
    """Get current status of a task execution.

    Retrieves the current status and progress information for a specific
    task execution. Useful for monitoring long-running tasks.

    Args:
        execution_id: Unique execution identifier
        org_id: Organization ID for access control

    Returns:
        TaskExecutionStatusResponse: Current execution status and progress

    Raises:
        HTTPException: 404 if execution not found, 500 for system errors
    """
    # TODO: Implement execution status retrieval from persistent storage
    # For now, return a placeholder response
    raise HTTPException(
        status_code=404,
        detail={
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "Execution status tracking not yet implemented",
                "details": {
                    "execution_id": str(execution_id),
                    "note": "Status persistence will be added in next implementation phase",
                },
            }
        },
    )
