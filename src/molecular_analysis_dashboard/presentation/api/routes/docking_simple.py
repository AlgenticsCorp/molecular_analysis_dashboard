"""Simplified docking routes for initial testing - without storage dependencies."""

import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ..schemas.docking import (
    DockingResultsResponse,
    FileUploadResponse,
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
    UserJobsResponse,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/docking", tags=["docking"])

# Simple in-memory storage for testing
uploaded_files: Dict[str, Dict[str, Any]] = {}
submitted_jobs: Dict[str, Dict[str, Any]] = {}


def validate_pdb_file(content: bytes) -> Dict[str, Any]:
    """Basic PDB file validation."""
    try:
        content_str = content.decode("utf-8")
        lines = content_str.split("\n")

        atom_count = sum(1 for line in lines if line.startswith("ATOM"))
        has_coordinates = any("ATOM" in line and len(line.split()) >= 8 for line in lines[:50])

        return {"atom_count": atom_count, "has_coordinates": has_coordinates, "format": "pdb"}
    except Exception as e:
        raise ValueError(f"Invalid PDB format: {str(e)}")


def validate_sdf_file(content: bytes) -> Dict[str, Any]:
    """Basic SDF file validation."""
    try:
        content_str = content.decode("utf-8")

        # Check for SDF structure markers
        has_mol_block = "$$$$" in content_str
        has_atom_count = any(
            line.strip() and line.strip().split()[0].isdigit()
            for line in content_str.split("\n")[3:4]
        )

        return {"format": "sdf", "has_mol_block": has_mol_block, "has_atom_count": has_atom_count}
    except Exception as e:
        raise ValueError(f"Invalid SDF format: {str(e)}")


@router.post("/upload/receptor", response_model=FileUploadResponse)
async def upload_receptor(file: UploadFile = File(...), name: str = "Uploaded Receptor"):
    """Upload and validate a protein receptor file (PDB format)."""

    if not file.filename.lower().endswith(".pdb"):
        raise HTTPException(status_code=400, detail="Only PDB files are supported for receptors")

    try:
        # Read file content
        content = await file.read()

        # Validate PDB file
        validation_info = validate_pdb_file(content)

        # Generate file ID and store (in memory for testing)
        file_id = str(uuid.uuid4())
        uploaded_files[file_id] = {
            "filename": file.filename,
            "content": content,
            "file_type": "receptor",
            "format": "pdb",
            "validation_info": validation_info,
            "name": name,
        }

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            format="pdb",
            file_type="receptor",
            size_bytes=len(content),
            validation_info=validation_info,
            storage_path=f"memory://receptors/{file_id}",
            name=name,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading receptor: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file upload")


@router.post("/upload/ligand", response_model=FileUploadResponse)
async def upload_ligand(file: UploadFile = File(...), name: str = "Uploaded Ligand"):
    """Upload and validate a ligand file (SDF format)."""

    if not file.filename.lower().endswith(".sdf"):
        raise HTTPException(status_code=400, detail="Only SDF files are supported for ligands")

    try:
        # Read file content
        content = await file.read()

        # Validate SDF file
        validation_info = validate_sdf_file(content)

        # Generate file ID and store (in memory for testing)
        file_id = str(uuid.uuid4())
        uploaded_files[file_id] = {
            "filename": file.filename,
            "content": content,
            "file_type": "ligand",
            "format": "sdf",
            "validation_info": validation_info,
            "name": name,
        }

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            format="sdf",
            file_type="ligand",
            size_bytes=len(content),
            validation_info=validation_info,
            storage_path=f"memory://ligands/{file_id}",
            name=name,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading ligand: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file upload")


@router.post("/jobs", response_model=JobSubmissionResponse)
async def submit_docking_job(request: JobSubmissionRequest):
    """Submit a new docking job using uploaded files."""

    # Validate that files exist
    if request.receptor_file_id not in uploaded_files:
        raise HTTPException(status_code=400, detail="Receptor file not found")

    if request.ligand_file_id not in uploaded_files:
        raise HTTPException(status_code=400, detail="Ligand file not found")

    # Create job
    job_id = str(uuid.uuid4())
    submitted_jobs[job_id] = {
        "job_id": job_id,
        "receptor_file_id": request.receptor_file_id,
        "ligand_file_id": request.ligand_file_id,
        "job_note": request.job_note,
        "status": "pending",
        "created_at": "2024-09-26T22:49:00Z",
    }

    return JobSubmissionResponse(
        job_id=job_id,
        status="pending",
        message="Docking job submitted successfully",
        estimated_completion_time="2024-09-26T23:19:00Z",
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a specific docking job."""

    if job_id not in submitted_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = submitted_jobs[job_id]

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress_percentage=25.0,
        current_step="Preprocessing receptor file",
        created_at=job["created_at"],
        estimated_completion="2024-09-26T23:19:00Z",
    )


@router.get("/jobs", response_model=UserJobsResponse)
async def get_user_jobs():
    """Get all docking jobs for the current user."""

    jobs = []
    for job_id, job_data in submitted_jobs.items():
        jobs.append(
            {
                "job_id": job_id,
                "status": job_data["status"],
                "created_at": job_data["created_at"],
                "job_note": job_data.get("job_note", ""),
            }
        )

    return UserJobsResponse(jobs=jobs, total_count=len(jobs))


@router.get("/jobs/{job_id}/results", response_model=DockingResultsResponse)
async def get_job_results(job_id: str):
    """Get the results of a completed docking job."""

    if job_id not in submitted_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = submitted_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")

    # Mock results for testing
    return DockingResultsResponse(
        job_id=job_id,
        status="completed",
        results={
            "poses": [
                {
                    "rank": 1,
                    "affinity": -8.5,
                    "rmsd_lb": 0.0,
                    "rmsd_ub": 0.0,
                    "confidence_score": 0.95,
                }
            ],
            "best_pose": {"rank": 1, "affinity": -8.5, "confidence_score": 0.95},
        },
        download_url="http://localhost:8000/api/v1/docking/jobs/123/download",
        metadata={"execution_time": 1800, "engine_version": "gnina-1.0", "total_poses": 9},
    )
