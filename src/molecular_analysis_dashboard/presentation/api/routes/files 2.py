"""
File management API routes.

This module provides REST API endpoints for managing user-uploaded molecular
structure files independently of task executions.

Endpoints:
- POST /api/v1/files - Upload a new file
- GET /api/v1/files - List files with filtering and pagination
- GET /api/v1/files/{file_id} - Get file metadata
- PATCH /api/v1/files/{file_id} - Update file metadata
- DELETE /api/v1/files/{file_id} - Delete a file
- POST /api/v1/files/bulk-delete - Delete multiple files
- GET /api/v1/files/stats - Get storage statistics
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ....services.user_file_service import UserFileService

logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = "Internal server error"
ERROR_NOT_FOUND = "not found"
ERROR_ACCESS_DENIED = "access denied"

# Create router
router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.post("", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    category: str = Form("molecular_structure"),
    user_id: Optional[str] = Form(None),  # For future auth integration
    created_by: Optional[str] = Form(None),
):
    """
    Upload a new molecular structure file.
    
    Supported formats: PDB, PDBQT, SDF, MOL2, XYZ
    
    Args:
        file: File to upload
        name: Custom display name (optional, defaults to filename)
        description: File description (optional)
        tags: Comma-separated tags (optional)
        category: File category (default: molecular_structure)
        user_id: User ID (optional, for multi-user support)
        created_by: Email/username of uploader (optional)
        
    Returns:
        File metadata including file_id, validation results, and checksums
        
    Raises:
        400: Invalid file format or validation failed
        413: File too large
        500: Internal server error
    """
    service = UserFileService()
    
    try:
        # Parse tags from comma-separated string
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        
        # Parse user_id
        user_uuid = UUID(user_id) if user_id else None
        
        # Upload file
        result = await service.upload_file(
            file=file,
            user_id=user_uuid,
            name=name,
            description=description,
            tags=tag_list,
            category=category,
            created_by=created_by,
        )
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "File uploaded successfully",
                "file": result,
            },
        )
        
    except ValueError as e:
        logger.warning(f"File upload validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except IOError as e:
        logger.error(f"File upload storage error: {e}")
        raise HTTPException(status_code=500, detail="Failed to store file")
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
    raise HTTPException(status_code=500, detail=INTERNAL_ERROR_MESSAGE)


@router.get("")
async def list_files(
    user_id: Optional[str] = None,
    format: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    sort_by: str = "uploaded_at",
    order: str = "desc",
    page: int = 1,
    limit: int = 50,
):
    """
    List files with filtering, sorting, and pagination.
    
    Args:
        user_id: Filter by user ID
        format: Filter by format (pdb, sdf, pdbqt, mol2, xyz)
        category: Filter by category
        search: Search in filename or description
        tags: Comma-separated tags (files must have ALL tags)
        sort_by: Sort field (uploaded_at, filename, size_bytes)
        order: Sort order (asc, desc)
        page: Page number (1-indexed)
        limit: Items per page (max 200)
        
    Returns:
        Paginated list of files with metadata
    """
    service = UserFileService()
    
    try:
        # Parse tags from comma-separated string
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        
        # Parse user_id
        user_uuid = UUID(user_id) if user_id else None
        
        result = await service.list_files(
            user_id=user_uuid,
            file_format=format,
            category=category,
            search=search,
            tags=tag_list,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")


@router.get("/stats")
async def get_storage_stats(user_id: Optional[str] = None):
    """
    Get storage usage statistics.
    
    Args:
        user_id: User ID to get stats for (optional, None for global stats)
        
    Returns:
        Storage statistics including file counts and sizes by format
    """
    service = UserFileService()
    
    try:
        user_uuid = UUID(user_id) if user_id else None
        
        result = await service.get_storage_stats(user_uuid)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR_MESSAGE)


@router.get("/{file_id}")
async def get_file_metadata(file_id: str, user_id: Optional[str] = None):
    """
    Get detailed metadata for a specific file.
    
    Args:
        file_id: File ID (UUID)
        user_id: Optional user ID for ownership verification
        
    Returns:
        File metadata including checksums, tags, and storage info
        
    Raises:
        404: File not found
        403: Access denied
    """
    service = UserFileService()
    
    try:
        file_uuid = UUID(file_id)
        user_uuid = UUID(user_id) if user_id else None
        
        result = await service.get_file_metadata(file_uuid, user_uuid)
        
        return JSONResponse(content=result)
        
    except ValueError as e:
        error_text = str(e).lower()
        if ERROR_NOT_FOUND in error_text:
            raise HTTPException(status_code=404, detail=str(e))
        elif ERROR_ACCESS_DENIED in error_text:
            raise HTTPException(status_code=403, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting file metadata: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR_MESSAGE)


@router.patch("/{file_id}")
async def update_file_metadata(
    file_id: str,
    filename: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    user_id: Optional[str] = None,
):
    """
    Update file metadata (not the file content).
    
    Args:
        file_id: File ID (UUID)
        filename: New filename (optional)
        description: New description (optional)
        tags: New comma-separated tags (optional)
        category: New category (optional)
        is_public: Public flag (optional)
        user_id: User ID for ownership verification (optional)
        
    Returns:
        Updated file metadata
        
    Raises:
        404: File not found
        403: Access denied
    """
    service = UserFileService()
    
    try:
        file_uuid = UUID(file_id)
        user_uuid = UUID(user_id) if user_id else None
        
        # Parse tags from comma-separated string
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        
        result = await service.update_file_metadata(
            file_id=file_uuid,
            user_id=user_uuid,
            filename=filename,
            description=description,
            tags=tag_list,
            category=category,
            is_public=is_public,
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "File metadata updated successfully",
            "file": result,
        })
        
    except ValueError as e:
        error_text = str(e).lower()
        if ERROR_NOT_FOUND in error_text:
            raise HTTPException(status_code=404, detail=str(e))
        elif ERROR_ACCESS_DENIED in error_text:
            raise HTTPException(status_code=403, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating file metadata: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR_MESSAGE)


@router.delete("/{file_id}", status_code=204)
async def delete_file(file_id: str, user_id: Optional[str] = None):
    """
    Delete a file and its database record.
    
    Args:
        file_id: File ID (UUID)
        user_id: User ID for ownership verification (optional)
        
    Returns:
        204 No Content on success
        
    Raises:
        404: File not found
        403: Access denied
        409: File is in use by active executions
    """
    service = UserFileService()
    
    try:
        file_uuid = UUID(file_id)
        user_uuid = UUID(user_id) if user_id else None
        
        await service.delete_file(file_uuid, user_uuid)
        
        return JSONResponse(status_code=204, content=None)
        
    except ValueError as e:
        error_msg = str(e).lower()
        if ERROR_NOT_FOUND in error_msg:
            raise HTTPException(status_code=404, detail=str(e))
        elif ERROR_ACCESS_DENIED in error_msg:
            raise HTTPException(status_code=403, detail=str(e))
        elif "in use" in error_msg or "referenced" in error_msg:
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR_MESSAGE)


@router.post("/bulk-delete")
async def bulk_delete_files(
    file_ids: List[str],
    user_id: Optional[str] = None,
):
    """
    Delete multiple files in a single operation.
    
    Args:
        file_ids: List of file IDs (UUIDs)
        user_id: User ID for ownership verification (optional)
        
    Returns:
        Summary of deletion results including errors
    """
    service = UserFileService()
    
    try:
        file_uuids = [UUID(fid) for fid in file_ids]
        user_uuid = UUID(user_id) if user_id else None
        
        result = await service.bulk_delete(file_uuids, user_uuid)
        
        return JSONResponse(content={
            "success": result["failed"] == 0,
            "message": f"Deleted {result['deleted']} file(s), {result['failed']} failed",
            "deleted": result["deleted"],
            "failed": result["failed"],
            "errors": result["errors"],
        })
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR_MESSAGE)
