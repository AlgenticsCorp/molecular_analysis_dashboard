"""
Professional molecular docking API routes with file upload integration.

This module provides NeuroSnap-style REST endpoints for molecular docking
operations, including file upload, job submission, and result management.
Based on patterns learned from NeuroSnap API tutorial.

Responsibilities:
- Professional file upload endpoints for PDB/SDF files
- Job submission using uploaded files (not JSON strings)
- Job monitoring and result retrieval
- SwaggerUI-testable endpoints with proper OpenAPI schemas

API Structure (following NeuroSnap patterns):
- POST /api/v1/docking/upload/receptor - Upload PDB files
- POST /api/v1/docking/upload/ligand - Upload SDF files
- POST /api/v1/docking/submit - Submit docking job with file_ids
- GET /api/v1/docking/jobs - List user's docking jobs
- GET /api/v1/docking/jobs/{job_id}/status - Poll job status
- GET /api/v1/docking/jobs/{job_id}/results - Download results
"""

import logging
from io import BytesIO
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ....adapters.external.neurosnap_adapter import NeuroSnapAdapter
from ....adapters.storage.file_storage import FileStorageAdapter
from ....domain.entities.docking_job import JobStatus, MolecularStructure
from ....ports.storage import StorageError
from ....use_cases.commands.execute_docking_task import (
    DockingTaskRequest,
    ExecuteDockingTaskUseCase,
)
from ..schemas.docking import (
    DockingResultsResponse,
    FileUploadResponse,
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
    UserJobsResponse,
)

logger = logging.getLogger(__name__)

# Initialize router with professional endpoint structure
router = APIRouter(prefix="/api/v1/docking", tags=["molecular-docking"])

# Initialize storage and adapters
storage_adapter = FileStorageAdapter()


# Dependency for authentication (placeholder - using same as molecules)
async def get_current_user():
    """Get current authenticated user."""
    # TODO: Implement proper JWT authentication
    return {
        "user_id": UUID("12345678-1234-5678-1234-123456789012"),
        "org_id": UUID("87654321-4321-8765-4321-210987654321"),
    }


def validate_pdb_file(content: bytes) -> Dict[str, Any]:
    """
    Validate PDB file format and extract basic information.

    Args:
        content: Raw PDB file content

    Returns:
        Dict with validation results and file info

    Raises:
        ValueError: If file is not valid PDB format
    """
    try:
        pdb_text = content.decode("utf-8")
        lines = pdb_text.strip().split("\n")

        atom_count = 0
        has_coordinates = False

        for line in lines:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                atom_count += 1
                # Check if coordinates are present (positions 30-54)
                if len(line) >= 54:
                    try:
                        x = float(line[30:38].strip())
                        y = float(line[38:46].strip())
                        z = float(line[46:54].strip())
                        has_coordinates = True
                    except ValueError:
                        continue

        if atom_count == 0:
            raise ValueError("No ATOM records found in PDB file")

        if not has_coordinates:
            raise ValueError("No valid coordinates found in PDB file")

        return {
            "format": "pdb",
            "atom_count": atom_count,
            "has_coordinates": has_coordinates,
            "file_size": len(content),
        }

    except UnicodeDecodeError:
        raise ValueError("File is not valid text format")
    except Exception as e:
        raise ValueError(f"Invalid PDB file: {str(e)}")


def validate_sdf_file(content: bytes) -> Dict[str, Any]:
    """
    Validate SDF file format and extract basic information.

    Args:
        content: Raw SDF file content

    Returns:
        Dict with validation results and file info

    Raises:
        ValueError: If file is not valid SDF format
    """
    try:
        sdf_text = content.decode("utf-8")
        lines = sdf_text.strip().split("\n")

        if len(lines) < 4:
            raise ValueError("SDF file too short")

        # Check for molecule count line (line 3)
        try:
            mol_line = lines[3].strip()
            if len(mol_line) >= 6:
                atom_count = int(mol_line[:3].strip())
                bond_count = int(mol_line[3:6].strip())
            else:
                raise ValueError("Invalid molecule count line")
        except (ValueError, IndexError):
            raise ValueError("Invalid SDF format - cannot parse molecule counts")

        if atom_count == 0:
            raise ValueError("No atoms found in SDF file")

        # Look for $$$$ delimiter
        has_delimiter = any(line.strip() == "$$$$" for line in lines)

        return {
            "format": "sdf",
            "atom_count": atom_count,
            "bond_count": bond_count,
            "has_delimiter": has_delimiter,
            "file_size": len(content),
        }

    except UnicodeDecodeError:
        raise ValueError("File is not valid text format")
    except Exception as e:
        raise ValueError(f"Invalid SDF file: {str(e)}")


@router.post(
    "/upload/receptor",
    response_model=FileUploadResponse,
    summary="Upload receptor protein structure (PDB)",
    description="Upload a PDB file containing the receptor protein structure for molecular docking. File will be validated and stored for use in docking jobs.",
    responses={
        400: {"description": "Invalid PDB file format"},
        413: {"description": "File too large (max 100MB)"},
        500: {"description": "Storage error"},
    },
)
async def upload_receptor(
    file: UploadFile = File(
        ...,
        description="PDB file containing receptor protein structure",
        media_type="chemical/x-pdb",
    ),
    name: Optional[str] = Form(None, description="Optional name for the receptor"),
    current_user: dict = Depends(get_current_user),
) -> FileUploadResponse:
    """
    Upload a receptor PDB file for molecular docking.

    This endpoint accepts PDB files and validates them for proper format,
    including ATOM records and 3D coordinates. Files are stored and
    assigned a file_id for use in job submission.
    """
    try:
        # Check file size (100MB limit)
        if file.size and file.size > 100 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB")

        # Read and validate file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Validate PDB format
        try:
            validation_info = validate_pdb_file(content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid PDB file: {str(e)}")

        # Generate file ID and storage path
        file_id = str(uuid4())
        storage_path = f"docking/receptors/{current_user['org_id']}/{file_id}.pdb"

        # Store file
        try:
            # Create file-like object for storage
            file_obj = BytesIO(content)
            await storage_adapter.store_file(
                file_obj,
                storage_path,
                content_type="chemical/x-pdb",
                organization_id=current_user["org_id"],
            )
        except Exception as e:
            logger.error(f"Storage error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to store file")

        response = FileUploadResponse(
            file_id=file_id,
            filename=file.filename or f"receptor_{file_id}.pdb",
            format="pdb",
            file_type="receptor",
            size_bytes=len(content),
            validation_info=validation_info,
            storage_path=storage_path,
            name=name or file.filename or f"Receptor {file_id[:8]}",
        )

        logger.info(
            f"Uploaded receptor PDB: {file.filename} ({validation_info['atom_count']} atoms)"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in receptor upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/upload/ligand",
    response_model=FileUploadResponse,
    summary="Upload ligand molecule structure (SDF)",
    description="Upload an SDF file containing the ligand molecule structure for molecular docking. File will be validated and stored for use in docking jobs.",
    responses={
        400: {"description": "Invalid SDF file format"},
        413: {"description": "File too large (max 100MB)"},
        500: {"description": "Storage error"},
    },
)
async def upload_ligand(
    file: UploadFile = File(
        ...,
        description="SDF file containing ligand molecule structure",
        media_type="chemical/x-mdl-sdfile",
    ),
    name: Optional[str] = Form(None, description="Optional name for the ligand"),
    current_user: dict = Depends(get_current_user),
) -> FileUploadResponse:
    """
    Upload a ligand SDF file for molecular docking.

    This endpoint accepts SDF files and validates them for proper format,
    including molecule blocks and atom/bond information. Files are stored
    and assigned a file_id for use in job submission.
    """
    try:
        # Check file size (100MB limit)
        if file.size and file.size > 100 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB")

        # Read and validate file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Validate SDF format
        try:
            validation_info = validate_sdf_file(content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid SDF file: {str(e)}")

        # Generate file ID and storage path
        file_id = str(uuid4())
        storage_path = f"docking/ligands/{current_user['org_id']}/{file_id}.sdf"

        # Store file
        try:
            # Create file-like object for storage
            file_obj = BytesIO(content)
            await storage_adapter.store_file(
                file_obj,
                storage_path,
                content_type="chemical/x-mdl-sdfile",
                organization_id=current_user["org_id"],
            )
        except Exception as e:
            logger.error(f"Storage error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to store file")

        response = FileUploadResponse(
            file_id=file_id,
            filename=file.filename or f"ligand_{file_id}.sdf",
            format="sdf",
            file_type="ligand",
            size_bytes=len(content),
            validation_info=validation_info,
            storage_path=storage_path,
            name=name or file.filename or f"Ligand {file_id[:8]}",
        )

        logger.info(f"Uploaded ligand SDF: {file.filename} ({validation_info['atom_count']} atoms)")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ligand upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/submit",
    response_model=JobSubmissionResponse,
    summary="Submit molecular docking job",
    description="Submit a GNINA molecular docking job using previously uploaded receptor and ligand files. Job will be queued and executed asynchronously.",
    responses={
        400: {"description": "Invalid file IDs or parameters"},
        404: {"description": "Uploaded files not found"},
        500: {"description": "Job submission failed"},
    },
)
async def submit_docking_job(
    request: JobSubmissionRequest, current_user: dict = Depends(get_current_user)
) -> JobSubmissionResponse:
    """
    Submit a molecular docking job using uploaded files.

    This endpoint accepts file_ids from previously uploaded receptor and ligand
    files and submits them to the GNINA docking engine via NeuroSnap API.
    """
    try:
        # TODO: Implement actual job submission in Phase 2
        # For now, return a placeholder response

        job_id = str(uuid4())

        # Placeholder response - will be replaced with real implementation
        response = JobSubmissionResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Job submitted successfully (placeholder implementation)",
            receptor_file_id=request.receptor_file_id,
            ligand_file_id=request.ligand_file_id,
            parameters=request.parameters,
            estimated_runtime="5-10 minutes",
        )

        logger.info(f"Submitted docking job {job_id} (placeholder)")
        return response

    except Exception as e:
        logger.error(f"Job submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit job")


@router.get(
    "/jobs",
    response_model=UserJobsResponse,
    summary="List user's docking jobs",
    description="List all molecular docking jobs submitted by the current user, including status and basic information.",
)
async def list_user_jobs(current_user: dict = Depends(get_current_user)) -> UserJobsResponse:
    """
    List all docking jobs for the current user.

    Returns a list of jobs with their current status, submission time,
    and basic parameters.
    """
    try:
        # TODO: Implement actual job listing in Phase 3
        # For now, return placeholder data

        jobs = []  # Placeholder - will query actual jobs from database/NeuroSnap

        return UserJobsResponse(jobs=jobs, total_jobs=len(jobs))

    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jobs")


@router.get(
    "/jobs/{job_id}/status",
    response_model=JobStatusResponse,
    summary="Get docking job status",
    description="Get the current status of a molecular docking job, including progress and estimated completion time.",
)
async def get_job_status(
    job_id: str, current_user: dict = Depends(get_current_user)
) -> JobStatusResponse:
    """
    Get the status of a specific docking job.

    Returns current job status, progress information, and estimated
    completion time if available.
    """
    try:
        # TODO: Implement actual status checking in Phase 3
        # For now, return placeholder status

        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            progress=0.0,
            message="Job status checking not yet implemented",
            created_at="2025-09-26T19:00:00Z",
            started_at=None,
            completed_at=None,
            estimated_completion="2025-09-26T19:10:00Z",
        )

    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job status")


@router.get(
    "/jobs/{job_id}/results",
    response_model=DockingResultsResponse,
    summary="Download docking job results",
    description="Download the results of a completed molecular docking job, including poses and binding affinities.",
)
async def get_job_results(
    job_id: str, current_user: dict = Depends(get_current_user)
) -> DockingResultsResponse:
    """
    Get the results of a completed docking job.

    Returns docking poses, binding affinities, and other analysis results
    for completed jobs.
    """
    try:
        # TODO: Implement actual result retrieval in Phase 3
        # For now, return placeholder results

        return DockingResultsResponse(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            results_available=False,
            message="Result download not yet implemented",
            download_urls={},
            summary=None,
        )

    except Exception as e:
        logger.error(f"Error getting job results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job results")
