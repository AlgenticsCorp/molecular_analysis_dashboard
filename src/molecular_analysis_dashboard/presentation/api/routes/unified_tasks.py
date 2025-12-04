"""
Unified Task API Router - combines database tasks with task framework
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from starlette.datastructures import UploadFile, FormData
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
import json
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from pathlib import Path
import os
from math import ceil

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


FORM_TRUE_VALUES = {"true", "1", "yes", "on"}
FORM_FALSE_VALUES = {"false", "0", "no", "off"}
DEFAULT_BINARY_CONTENT_TYPE = "application/octet-stream"
def _normalize_extension(ext: str) -> str:
    normalized = ext.lower().strip()
    if not normalized:
        return ""
    if not normalized.startswith("."):
        normalized = f".{normalized}" if normalized else normalized
    return normalized


def _validate_file_upload(
    parameter_name: str,
    upload: UploadFile,
    content: bytes,
    spec: Optional[Dict[str, Any]] = None,
) -> None:
    """Validate uploaded files against parameter specification."""

    if not spec:
        return

    validation = spec.get("validation", {}) or {}

    allowed_extensions = validation.get("file_types") or []
    if allowed_extensions:
        normalized_allowed = {
            _normalize_extension(ext)
            for ext in allowed_extensions
            if isinstance(ext, str)
        }
        filename = upload.filename or ""
        extension = _normalize_extension(Path(filename).suffix)
        if not extension or extension not in normalized_allowed:
            allowed_display = ", ".join(sorted(normalized_allowed))
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Parameter '{parameter_name}' must use one of the supported file extensions: "
                    f"{allowed_display or 'unspecified'}"
                ),
            )

    max_size_mb = validation.get("max_size_mb")
    if max_size_mb is not None:
        try:
            max_size_bytes = int(float(max_size_mb) * 1024 * 1024)
        except (TypeError, ValueError):
            max_size_bytes = None
        if max_size_bytes is not None and len(content) > max_size_bytes:
            actual_mb = ceil(len(content) / (1024 * 1024))
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Parameter '{parameter_name}' exceeds the maximum allowed size of {max_size_mb} MB "
                    f"(received ~{actual_mb} MB)."
                ),
            )


def _coerce_form_value(value: str, spec: Dict[str, Any]) -> Any:
    """Convert raw string values from multipart forms into typed parameter values."""

    if value == "" and not spec.get("required"):
        return None

    param_type = spec.get("type", "string")
    try:
        if param_type == "integer":
            return int(value)
        if param_type == "number":
            return float(value)
        if param_type == "boolean":
            lowered = value.lower()
            if lowered in FORM_TRUE_VALUES:
                return True
            if lowered in FORM_FALSE_VALUES:
                return False
            raise ValueError("Invalid boolean value")
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid value for parameter '{spec.get('name', 'unknown')}'",
        ) from exc

    return value


def _validate_allowed_value(value: Any, spec: Dict[str, Any]) -> None:
    allowed = spec.get("validation", {}).get("allowed_values")
    if allowed and value not in allowed:
        allowed_csv = ", ".join(str(v) for v in allowed)
        raise HTTPException(
            status_code=400,
            detail=f"Value for parameter '{spec.get('name', 'unknown')}' must be one of: {allowed_csv}",
        )


def _load_json_parameters(form: FormData) -> Dict[str, Any]:
    """Load optional JSON payload embedded in the multipart request."""

    raw_parameters = form.get("parameters")
    if not raw_parameters:
        return {}

    if isinstance(raw_parameters, UploadFile):
        raise HTTPException(status_code=400, detail="parameters field must be JSON")

    try:
        parsed = json.loads(raw_parameters)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid parameters JSON") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="parameters JSON must be an object")

    return parsed


async def _handle_form_item(
    key: str,
    value: Any,
    spec: Optional[Dict[str, Any]],
    params: Dict[str, Any],
    files: Dict[str, Dict[str, Any]],
) -> None:
    """Process a single multipart form entry."""

    if isinstance(value, UploadFile):
        content = await value.read()
        await value.close()

        _validate_file_upload(key, value, content, spec)

        files[key] = {
            "filename": value.filename,
            "content": content,
            "content_type": value.content_type or DEFAULT_BINARY_CONTENT_TYPE,
        }
        return

    if spec:
        coerced = _coerce_form_value(value, spec)
        if coerced is None and value == "":
            return
        _validate_allowed_value(coerced, spec)
        params[key] = coerced
        return

    params[key] = value


async def _parse_task_form_data(
    form: FormData,
    parameter_specs: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Parse multipart form data into structured parameters and file payloads."""

    params = _load_json_parameters(form)
    files: Dict[str, Dict[str, Any]] = {}

    for key, value in form.multi_items():
        if key == "parameters":
            continue

        spec = parameter_specs.get(key)
        await _handle_form_item(key, value, spec, params, files)

    missing_files = [
        name
        for name, spec in parameter_specs.items()
        if spec.get("type") == "file" and spec.get("required") and name not in files
    ]
    if missing_files:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required file parameters: {', '.join(missing_files)}",
        )

    return params, files


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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch results: {str(e)}")


@router.delete("/executions/{execution_id}", status_code=204)
async def delete_execution(execution_id: str, purge_files: bool = True):
    """Delete an execution and optionally purge its stored files."""

    try:
        deleted = await unified_task_service.delete_execution(
            execution_id,
            delete_files=purge_files,
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Execution not found")
        return Response(status_code=204)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid execution ID format")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to delete execution %s: %s", execution_id, exc)
        raise HTTPException(status_code=500, detail=f"Failed to delete execution: {exc}")


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
    request: Request,
    org_id: Optional[UUID] = Depends(get_current_org_id),
    user_id: Optional[UUID] = Depends(get_current_user_id),
):
    """Execute a task with dynamically parsed parameters and files."""

    try:
        task_definition = await unified_task_service.get_task_by_id(task_id, org_id)
        if not task_definition:
            raise HTTPException(status_code=404, detail="Task not found")

        parameter_specs = {
            param.get("name"): param for param in task_definition.get("parameters", [])
        }

        form = await request.form()
        params, files = await _parse_task_form_data(form, parameter_specs)

        result = await unified_task_service.execute_task(
            task_id=task_id,
            parameters=params,
            files=files if files else None,
            org_id=org_id,
            user_id=user_id,
        )

        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(exc)}") from exc


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
        content_type = file_metadata.get("content_type", DEFAULT_BINARY_CONTENT_TYPE)
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