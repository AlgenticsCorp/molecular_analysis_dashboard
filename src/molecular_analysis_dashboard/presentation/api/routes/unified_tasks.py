"""
Unified Task API Router - combines database tasks with task framework
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from typing import Dict, List, Any, Optional
from uuid import UUID
import json
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from pathlib import Path
import os

from database.models.task_execution import TaskFrameworkExecution
from ....services.unified_task_service import unified_task_service
from ....services.execution_file_service import ExecutionFileService
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


@router.get("/executions/{execution_id}/files")
async def list_execution_files(
    execution_id: str,
    file_type: Optional[str] = None
):
    """
    List all files associated with a specific execution.
    
    Args:
        execution_id: The ID of the task execution
        file_type: Optional filter - 'input' or 'output'
    
    Returns:
        List of file metadata including file_id, filename, size, etc.
    """
    try:
        file_service = ExecutionFileService()
        files = await file_service.get_execution_files(
            execution_id=UUID(execution_id),
            file_type=file_type
        )
        
        return {
            "execution_id": execution_id,
            "total_files": len(files),
            "files": files
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid execution ID format")
    except Exception as e:
        logger.error(f"Error listing files for execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


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


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str
):
    """
    Download a file by its file_id.
    Handles both local storage files and external URLs (NeuroSnap).
    """
    try:
        # Get file metadata from database
        file_service = ExecutionFileService()
        file_metadata = await file_service.get_file(file_id)
        
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Handle external URLs (NeuroSnap) - redirect to external URL
        if file_metadata.get("storage_backend") == "neurosnap_cloud":
            download_url = file_metadata.get("download_url")
            if not download_url:
                raise HTTPException(status_code=404, detail="Download URL not available")
            return RedirectResponse(url=download_url)
        
        # Handle local storage files
        storage_path = file_metadata.get("storage_path")
        if not storage_path:
            raise HTTPException(status_code=404, detail="File path not available")
        
        # Construct full file path
        # Storage path is relative like: /uploads/system/{execution_id}/{filename}
        # We need to serve from the storage volume mounted at /storage
        full_path = Path("/storage") / storage_path.lstrip("/")
        
        if not full_path.exists():
            logger.error(f"File not found at path: {full_path}")
            raise HTTPException(status_code=404, detail="File not found on storage")
        
        # Read and stream the file
        def iter_file():
            with open(full_path, "rb") as f:
                yield from f
        
        # Determine content type
        content_type = file_metadata.get("content_type", "application/octet-stream")
        filename = file_metadata.get("filename", "download")
        
        return StreamingResponse(
            iter_file(),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(full_path.stat().st_size)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")


@router.get("/executions/{execution_id}/files/{file_type}/{parameter_name}/download")
async def download_execution_file(
    execution_id: str,
    file_type: str,
    parameter_name: str
):
    """
    Download a specific file from an execution by parameter name.
    file_type: 'input' or 'output'
    parameter_name: e.g., 'receptor_file', 'ligand_file', 'output_csv'
    """
    try:
        file_service = ExecutionFileService()
        file_metadata = await file_service.get_file_by_execution_and_param(
            execution_id, parameter_name, file_type
        )
        
        if not file_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_type}/{parameter_name} for execution {execution_id}"
            )
        
        # Use the same download logic
        file_id = file_metadata.get("file_id")
        if not file_id:
            raise HTTPException(status_code=500, detail="Invalid file metadata")
        
        # Redirect to the main download endpoint
        return await download_file(file_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execution file download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")