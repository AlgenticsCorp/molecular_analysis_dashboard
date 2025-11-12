"""
Unified Task API Router - combines database tasks with task framework
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from uuid import UUID
import json
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.task_execution import TaskFrameworkExecution
from ....services.unified_task_service import unified_task_service
from ....infrastructure.database import get_metadata_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks-unified", tags=["unified-tasks"])


# Placeholder auth functions - matching existing pattern
def get_current_org_id() -> Optional[UUID]:
    """Get current organization ID (placeholder implementation)."""
    return None


def get_current_user_id() -> Optional[UUID]:
    """Get current user ID (placeholder implementation)."""
    return None


@router.get("/", response_model=List[Dict[str, Any]])
async def list_all_tasks(
    org_id: Optional[UUID] = Depends(get_current_org_id)
):
    """List all available tasks from both database and framework"""
    try:
        tasks = await unified_task_service.get_all_tasks(org_id)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")


@router.get("/available")
async def get_available_tasks():
    """Get available tasks for task library (simplified endpoint)"""
    try:
        tasks = await unified_task_service.get_all_tasks()
        
        # Simplify response for frontend
        simplified_tasks = []
        for task in tasks:
            simplified_task = {
                "id": task["id"],
                "name": task["name"],
                "description": task["description"],
                "category": task.get("category", "general"),
                "tags": task.get("tags", []),
                "execution_time_estimate": task.get("execution_time_estimate", 300),
                "resource_requirements": task.get("resource_requirements", {}),
                "parameters": task.get("parameters", []),
                "source": task.get("source", "unknown")
            }
            simplified_tasks.append(simplified_task)
        
        return {"tasks": simplified_tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch available tasks: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for task service"""
    try:
        # Check if we can list tasks
        tasks = await unified_task_service.get_all_tasks()
        return {
            "status": "healthy",
            "tasks_available": len(tasks),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/executions")
async def list_user_executions(
    limit: int = 50,
    user_id: Optional[UUID] = Depends(get_current_user_id),
    org_id: Optional[UUID] = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_metadata_session)
):
    """List user's task executions"""
    try:
        # For development: If no user_id (not authenticated), return all executions
        if not user_id:
            query = select(TaskFrameworkExecution).order_by(TaskFrameworkExecution.created_at.desc()).limit(limit)
            result = await db.execute(query)
            executions = result.scalars().all()
            
            return {"executions": [execution.to_dict() for execution in executions]}
        
        # Otherwise, use the service method for authenticated users
        executions = await unified_task_service.list_user_executions(
            user_id=user_id,
            org_id=org_id,
            limit=limit
        )
        return {"executions": executions}
    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch executions: {str(e)}")


@router.get("/executions/{execution_id}/status")
async def get_execution_status(execution_id: str):
    """Get status of a task execution"""
    try:
        status = await unified_task_service.get_execution_status(execution_id)
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch status: {str(e)}")


@router.get("/executions/{execution_id}/results")
async def get_execution_results(execution_id: str):
    """Get results of a completed execution"""
    try:
        results = await unified_task_service.get_execution_results(execution_id)
        if not results:
            raise HTTPException(status_code=404, detail="Results not found or execution not completed")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch results: {str(e)}")


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task_details(
    task_id: str,
    org_id: Optional[UUID] = Depends(get_current_org_id)
):
    """Get detailed information about a specific task"""
    try:
        task = await unified_task_service.get_task_by_id(task_id, org_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str,
    receptor_file: Optional[UploadFile] = File(None),
    ligand_file: Optional[UploadFile] = File(None),
    job_name: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    parameters: Optional[str] = Form("{}"),  # JSON string of additional parameters
    org_id: Optional[UUID] = Depends(get_current_org_id),
    user_id: Optional[UUID] = Depends(get_current_user_id)
):
    """Execute a task with provided parameters and files"""
    try:
        # Parse parameters
        try:
            params = json.loads(parameters) if parameters else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid parameters JSON")
        
        # Add form fields to parameters
        if job_name:
            params["job_name"] = job_name
        if note:
            params["note"] = note
        
        # Prepare files
        files = {}
        if receptor_file:
            files["receptor_file"] = {
                "filename": receptor_file.filename,
                "content": await receptor_file.read(),
                "content_type": receptor_file.content_type
            }
        
        if ligand_file:
            files["ligand_file"] = {
                "filename": ligand_file.filename,
                "content": await ligand_file.read(),
                "content_type": ligand_file.content_type
            }
        
        # Execute task
        result = await unified_task_service.execute_task(
            task_id=task_id,
            parameters=params,
            files=files if files else None,
            org_id=org_id,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")