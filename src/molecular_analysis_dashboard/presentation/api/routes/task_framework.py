"""
Task Framework Integration Endpoints.

These endpoints demonstrate the task framework approach where tasks are
executed through provider adapters that bridge to specific provider endpoints.
"""

from typing import Dict, Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException, File, Form, UploadFile

from ....adapters.providers.neurosnap_task_adapter import TaskExecution, TaskExecutionService

# Create a separate router for task framework endpoints
task_framework_router = APIRouter(
    prefix="/api/v1/task-framework",
    tags=["🔄 Task Framework"],
    responses={
        401: {"description": "Authentication failed"},
        404: {"description": "Task not found"},
        500: {"description": "Internal server error"},
    },
)

# Initialize task execution service
_task_execution_service = TaskExecutionService()


@task_framework_router.post("/{task_id}/execute")
async def execute_task_via_framework(
    task_id: str,
    receptor_file: UploadFile = File(..., description="Protein receptor in PDB format"),
    ligand_file: UploadFile = File(..., description="Ligand molecule in SDF format"),
    job_name: str = Form(default="Task Framework Execution", description="Job name"),
    note: str = Form(default="Executed via task framework", description="Job notes"),
) -> Dict[str, Any]:
    """Execute a molecular task using the task framework.
    
    This endpoint demonstrates the task framework approach where tasks are
    executed through provider adapters that bridge to specific endpoints.
    
    The flow is:
    1. Create TaskExecution with uploaded files
    2. Use TaskExecutionService to find appropriate adapter
    3. Adapter translates task to provider-specific API call
    4. Return external job ID for tracking
    """
    
    if task_id != "gnina-molecular-docking":
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    try:
        # Generate execution ID
        execution_id = str(uuid4())
        
        # Prepare parameters from uploaded files
        receptor_content = await receptor_file.read()
        ligand_content = await ligand_file.read()
        
        parameters = {
            "receptor_file": {
                "content": receptor_content,
                "filename": receptor_file.filename
            },
            "ligand_file": {
                "content": ligand_content,
                "filename": ligand_file.filename
            },
            "job_name": job_name,
            "note": note
        }
        
        # Create task execution
        execution = TaskExecution(
            execution_id=execution_id,
            task_id=task_id,
            parameters=parameters
        )
        
        # Execute task using provider adapter
        external_job_id = await _task_execution_service.execute_task(
            task_id=task_id,
            execution=execution,
            task_definition={}  # Would be loaded from database in full implementation
        )
        
        return {
            "execution_id": execution_id,
            "external_job_id": external_job_id,
            "status": "submitted",
            "task_id": task_id,
            "message": f"Task {task_id} executed successfully via task framework. External job ID: {external_job_id}",
            "approach": "task_framework_with_provider_adapter",
            "provider_endpoint": "/api/v1/providers/neurosnap/docking/submit",
            "tracking_endpoints": {
                "status": f"/api/v1/task-framework/{task_id}/status/{external_job_id}",
                "results": f"/api/v1/task-framework/{task_id}/results/{external_job_id}"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Task framework execution failed: {str(e)}"
        )


@task_framework_router.get("/{task_id}/status/{external_job_id}")
async def get_task_framework_status(task_id: str, external_job_id: str) -> Dict[str, Any]:
    """Get status of a task execution via the task framework."""
    
    try:
        status = await _task_execution_service.get_execution_status(task_id, external_job_id)
        return {
            "task_id": task_id,
            "external_job_id": external_job_id,
            "status": status,
            "approach": "task_framework_with_provider_adapter"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@task_framework_router.get("/{task_id}/results/{external_job_id}")
async def get_task_framework_results(task_id: str, external_job_id: str) -> Dict[str, Any]:
    """Get results of a task execution via the task framework."""
    
    try:
        results = await _task_execution_service.get_execution_results(task_id, external_job_id)
        return {
            "task_id": task_id,
            "external_job_id": external_job_id,
            "results": results,
            "approach": "task_framework_with_provider_adapter"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task results: {str(e)}"
        )


@task_framework_router.get("/tasks/available")
async def list_available_framework_tasks() -> Dict[str, Any]:
    """List all available tasks in the task framework."""
    
    tasks = [
        {
            "task_id": "gnina-molecular-docking",
            "name": "GNINA Molecular Docking", 
            "description": "Neural network-guided molecular docking via NeuroSnap API",
            "category": "molecular_docking",
            "provider": "neurosnap",
            "status": "available",
            "parameters": {
                "receptor_file": {"type": "file", "format": "pdb", "required": True},
                "ligand_file": {"type": "file", "format": "sdf", "required": True},
                "job_name": {"type": "string", "required": False},
                "note": {"type": "string", "required": False}
            },
            "endpoints": {
                "execute": "/api/v1/task-framework/gnina-molecular-docking/execute",
                "status": "/api/v1/task-framework/gnina-molecular-docking/status/{job_id}",
                "results": "/api/v1/task-framework/gnina-molecular-docking/results/{job_id}"
            }
        }
    ]
    
    return {
        "tasks": tasks,
        "total_count": len(tasks),
        "approach": "task_framework_with_provider_adapter"
    }