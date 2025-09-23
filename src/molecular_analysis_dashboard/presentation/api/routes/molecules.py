"""API routes for molecule upload and storage operations."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ....adapters.storage.file_storage import FileStorageAdapter
from ....ports.storage import StorageError
from ....use_cases.molecules import (
    GeneratePresignedUrlUseCase,
    GetFileInfoUseCase,
    GetMoleculeFileUseCase,
    UploadMoleculeUseCase,
)
from ..schemas.molecules import (
    ErrorResponse,
    FileInfoResponse,
    MoleculeUploadResponse,
    PresignedUrlResponse,
    StorageHealthResponse,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/molecules", tags=["molecules"])

# Initialize storage adapter and use cases
storage_adapter = FileStorageAdapter()
upload_use_case = UploadMoleculeUseCase(storage_adapter)
get_file_use_case = GetMoleculeFileUseCase(storage_adapter)
presigned_url_use_case = GeneratePresignedUrlUseCase(storage_adapter)
file_info_use_case = GetFileInfoUseCase(storage_adapter)


# Dependency for getting current user (placeholder)
async def get_current_user():
    """Get current authenticated user (placeholder implementation)."""
    # TODO: Implement proper JWT authentication
    return {
        "user_id": UUID("12345678-1234-5678-1234-123456789012"),
        "org_id": UUID("87654321-4321-8765-4321-210987654321"),
    }


@router.post(
    "/upload",
    response_model=MoleculeUploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or parameters"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Storage error"},
    },
)
async def upload_molecule(
    file: UploadFile = File(..., description="Molecular structure file"),
    name: str = Form(..., description="Molecule name"),
    format: str = Form(..., description="File format (pdb, sdf, mol2, etc.)"),
    properties: Optional[str] = Form(None, description="JSON string of properties"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    visibility: str = Form("private", description="Visibility (private, org, public)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a molecular structure file.

    This endpoint accepts molecular structure files in various formats
    and stores them with associated metadata.
    """
    try:
        # Validate file size (100MB limit)
        if file.size and file.size > 100 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB.")

        # Parse properties and tags
        molecule_properties = {}
        if properties:
            import json

            try:
                molecule_properties = json.loads(properties)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format for properties")

        molecule_tags = []
        if tags:
            molecule_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Upload molecule using use case
        molecule = await upload_use_case.execute(
            file_content=file.file,
            file_name=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            organization_id=current_user["org_id"],
            uploaded_by=current_user["user_id"],
            molecule_name=name,
            file_format=format,
            properties=molecule_properties,
            tags=molecule_tags,
            visibility=visibility,
        )

        # Convert to response model
        response = MoleculeUploadResponse(
            molecule_id=molecule.molecule_id,
            name=molecule.name,
            format=molecule.format,
            uri=molecule.uri,
            size_bytes=molecule.size_bytes,
            checksum=molecule.checksum,
            properties=molecule.properties,
            tags=molecule.tags,
            visibility=molecule.visibility,
            uploaded_by=molecule.uploaded_by,
            created_at=molecule.created_at,
        )

        logger.info(f"Successfully uploaded molecule: {name} for user {current_user['user_id']}")

        return response

    except ValueError as e:
        logger.warning(f"Validation error during upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        logger.error(f"Storage error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/download/{file_uri:path}",
    responses={
        200: {"description": "File content"},
        404: {"model": ErrorResponse, "description": "File not found"},
        500: {"model": ErrorResponse, "description": "Storage error"},
    },
)
async def download_molecule_file(file_uri: str, current_user: dict = Depends(get_current_user)):
    """
    Download a molecular structure file by its storage URI.

    Returns the file content as a streaming response.
    """
    try:
        # Construct full storage URI
        storage_uri = f"storage://{file_uri}"

        # Get file using use case
        file_content = await get_file_use_case.execute(storage_uri)

        if file_content is None:
            raise HTTPException(status_code=404, detail="File not found")

        # Get file info for proper headers
        file_info = await file_info_use_case.execute(storage_uri)

        def file_generator():
            try:
                while chunk := file_content.read(8192):
                    yield chunk
            finally:
                file_content.close()

        headers = {
            "Content-Disposition": (
                f"attachment; filename={file_info['name']}" if file_info else "attachment"
            )
        }

        media_type = (
            file_info.get("mime_type", "application/octet-stream")
            if file_info
            else "application/octet-stream"
        )

        return StreamingResponse(file_generator(), media_type=media_type, headers=headers)

    except StorageError as e:
        logger.error(f"Storage error during download: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/presigned-url/{file_uri:path}",
    response_model=PresignedUrlResponse,
    responses={
        404: {"model": ErrorResponse, "description": "File not found"},
        500: {"model": ErrorResponse, "description": "Storage error"},
    },
)
async def get_presigned_url(
    file_uri: str, expiration: int = 3600, current_user: dict = Depends(get_current_user)
):
    """
    Generate a presigned URL for accessing a molecular structure file.

    The URL will be valid for the specified expiration time.
    """
    try:
        # Construct full storage URI
        storage_uri = f"storage://{file_uri}"

        # Generate presigned URL using use case
        presigned_url = await presigned_url_use_case.execute(storage_uri, expiration)

        if presigned_url is None:
            raise HTTPException(status_code=404, detail="File not found")

        return PresignedUrlResponse(url=presigned_url, expires_in=expiration)

    except StorageError as e:
        logger.error(f"Storage error during URL generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during URL generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/info/{file_uri:path}",
    response_model=FileInfoResponse,
    responses={
        404: {"model": ErrorResponse, "description": "File not found"},
        500: {"model": ErrorResponse, "description": "Storage error"},
    },
)
async def get_file_info(file_uri: str, current_user: dict = Depends(get_current_user)):
    """
    Get metadata information about a molecular structure file.

    Returns file size, creation time, MIME type, and other metadata.
    """
    try:
        # Construct full storage URI
        storage_uri = f"storage://{file_uri}"

        # Get file info using use case
        file_info = await file_info_use_case.execute(storage_uri)

        if file_info is None:
            raise HTTPException(status_code=404, detail="File not found")

        return FileInfoResponse(**file_info)

    except StorageError as e:
        logger.error(f"Storage error during file info retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during file info retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/storage/health",
    response_model=StorageHealthResponse,
    responses={500: {"model": ErrorResponse, "description": "Storage service unavailable"}},
)
async def get_storage_health():
    """
    Check storage service health and availability.

    Returns storage status and available space information.
    """
    try:
        import shutil

        # Check storage root directory
        storage_root = storage_adapter.storage_root
        available_space = shutil.disk_usage(storage_root).free

        return StorageHealthResponse(
            status="healthy",
            service="storage",
            storage_root=str(storage_root),
            available_space=available_space,
        )

    except Exception as e:
        logger.error(f"Storage health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Storage service unavailable: {str(e)}")
