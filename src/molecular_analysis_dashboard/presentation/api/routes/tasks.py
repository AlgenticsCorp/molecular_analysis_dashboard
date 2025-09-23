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
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....infrastructure.database import get_metadata_session
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
