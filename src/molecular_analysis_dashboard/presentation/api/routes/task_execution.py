"""
Simple task execution API routes for immediate GNINA integration.

This module provides a minimal implementation of task execution endpoints
that bypasses database dependencies and directly integrates with the GNINA
adapters. This allows immediate testing of the GNINA integration via Swagger UI.

Responsibilities:
- Provide immediate /api/v1/tasks/{task_id}/execute endpoint
- Direct integration with GNINA use case
- Swagger UI documentation for molecular docking
- Production-ready error handling

Dependencies:
- fastapi: For HTTP routing and validation
- pydantic: For request/response schemas
- GNINA adapters: Direct integration without database layer

Architecture:
- Simplified for immediate integration testing
- Will be replaced with full database integration in next phase
"""

import os
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from ....adapters.external.ligand_prep_adapter import RDKitLigandPrepAdapter
from ....adapters.external.neurosnap_adapter import NeuroSnapAdapter
from ....domain.entities.docking_job import MolecularStructure

# Use case and adapters
from ....use_cases.commands.execute_docking_task import (
    DockingTaskRequest,
    ExecuteDockingTaskUseCase,
)

# Task execution schemas (simplified)
from ..schemas.task_execution import (
    DockingPoseSchema,
    DockingResultsSchema,
    JobStatusSchema,
    TaskExecutionRequest,
    TaskExecutionResponse,
)

# Create router
router = APIRouter(prefix="/api/v1/tasks", tags=["task-execution"])


# Available tasks response
class AvailableTasksResponse(BaseModel):
    """Available molecular tasks response."""

    tasks: list[Dict[str, Any]] = Field(..., description="List of available tasks")
    total_count: int = Field(..., description="Total number of tasks")


@router.get(
    "",
    response_model=AvailableTasksResponse,
    summary="List available tasks",
    description="Get list of available molecular analysis tasks",
)
async def list_available_tasks() -> AvailableTasksResponse:
    """List available molecular analysis tasks.

    Returns a list of currently supported molecular analysis tasks,
    including GNINA molecular docking and future task types.

    Returns:
        AvailableTasksResponse: List of available tasks with metadata
    """
    available_tasks = [
        {
            "task_id": "gnina-molecular-docking",
            "name": "GNINA Molecular Docking",
            "description": "Neural network-guided molecular docking via NeuroSnap API",
            "category": "molecular_docking",
            "engine": "gnina",
            "provider": "neurosnap",
            "status": "available",
            "parameters": {
                "receptor": {"type": "molecular_structure", "required": True},
                "ligand": {"type": "molecular_structure_or_drug_name", "required": True},
                "binding_site": {"type": "binding_site_coordinates", "required": False},
                "max_poses": {"type": "integer", "default": 9, "range": [1, 20]},
                "energy_range": {"type": "float", "default": 3.0, "range": [0.5, 10.0]},
                "exhaustiveness": {"type": "integer", "default": 8, "range": [1, 32]},
            },
        },
        {
            "task_id": "molecular-docking",
            "name": "Molecular Docking (Alias)",
            "description": "Alias for GNINA molecular docking",
            "category": "molecular_docking",
            "engine": "gnina",
            "provider": "neurosnap",
            "status": "available",
            "alias_for": "gnina-molecular-docking",
        },
    ]

    return AvailableTasksResponse(tasks=available_tasks, total_count=len(available_tasks))


@router.post(
    "/{task_id}/execute",
    response_model=TaskExecutionResponse,
    responses={
        400: {"description": "Invalid request parameters"},
        404: {"description": "Task not found"},
        500: {"description": "Internal server error"},
    },
    summary="Execute molecular task",
    description="Execute a molecular analysis task (GNINA docking, etc.)",
)
async def execute_molecular_task(
    task_id: str,
    request: TaskExecutionRequest = Body(...),
    org_id: Optional[str] = Query(None, description="Organization ID"),
) -> TaskExecutionResponse:
    """Execute a molecular analysis task.

    Submits a molecular task for execution using the appropriate engine.
    Currently supports GNINA molecular docking via NeuroSnap API.

    Args:
        task_id: Task identifier (gnina-molecular-docking, molecular-docking, docking)
        request: Task execution parameters and configuration
        org_id: Organization ID for multi-tenant access control

    Returns:
        TaskExecutionResponse: Execution tracking information with results

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
        supported_tasks = ["gnina-molecular-docking", "molecular-docking", "docking"]
        if task_id not in supported_tasks:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "TASK_NOT_FOUND",
                        "message": f"Task '{task_id}' not found or not supported",
                        "details": {"supported_tasks": supported_tasks, "requested_task": task_id},
                    }
                },
            )

        # Convert Pydantic request to domain objects
        # Handle receptor conversion
        if isinstance(request.receptor, dict):
            receptor_structure = MolecularStructure(
                name=request.receptor.get("name", "receptor"),
                format=request.receptor.get("format", "pdb"),
                data=request.receptor.get("data", ""),
                properties=request.receptor.get("properties", {}),
            )
        else:
            # Pydantic model to domain entity
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

        # Check for NeuroSnap API key
        api_key = os.getenv("NEUROSNAP_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "CONFIGURATION_ERROR",
                        "message": "NeuroSnap API key not configured",
                        "details": {
                            "required_env_var": "NEUROSNAP_API_KEY",
                            "help": "Set NEUROSNAP_API_KEY environment variable with your API key",
                        },
                    }
                },
            )

        # Initialize adapters
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
                    pose_data=pose.pose_data or {},
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
                    pose_data=execution.results.best_pose.pose_data or {},
                )

            results_schema = DockingResultsSchema(
                poses=poses,
                best_pose=best_pose_schema,
                execution_time=execution.results.execution_time,
                engine_version=execution.results.engine_version,
                parameters=execution.results.parameters or {},
                metadata=execution.results.metadata or {},
            )

        # Calculate progress and status
        progress = 0.0
        current_step = "pending"
        if execution.status.value == "running":
            progress = 50.0
            current_step = "running"
        elif execution.status.value == "completed":
            progress = 100.0
            current_step = "completed"
        elif execution.status.value == "failed":
            progress = 0.0
            current_step = "failed"

        # Create response
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
                    "details": {"task_id": task_id, "exception_type": type(e).__name__},
                }
            },
        )
