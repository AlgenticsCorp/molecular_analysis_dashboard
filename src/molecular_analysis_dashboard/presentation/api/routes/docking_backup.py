"""Simple and clean docking API with NeuroSnap integration."""

import json
import logging
import os
from datetime import datetime
from typing import List, Optional

import requests
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import Field
from requests_toolbelt.multipart.encoder import MultipartEncoder

from ....adapters.http.neurosnap_client import NeuroSnapClient
from ....domain.entities.docking_job import JobStatus
from ....domain.exceptions import (
    FileDownloadError,
    FileListingError,
    JobNotCompleteError,
    StatusCheckError,
)
from ..schemas.docking import (
    DirectJobSubmissionResponse,
    DockingPoseSchema,
    DockingResultsResponse,
    ErrorResponse,
    JobFilterParams,
    JobListResponse,
    JobStatusEnum,
    JobStatusResponse,
    JobSummary,
    MolecularFileInfo,
)

# Setup
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/docking",
    tags=["Molecular Docking"],
    responses={
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    },
)


def get_api_key() -> str:
    """Get NeuroSnap API key."""
    key = os.getenv("NEUROSNAP_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return key


def get_neurosnap_client() -> NeuroSnapClient:
    """Create NeuroSnap client instance."""
    return NeuroSnapClient(api_key=get_api_key())


def map_job_status(status: JobStatus) -> JobStatusEnum:
    """Map domain JobStatus to API JobStatusEnum."""
    mapping = {
        JobStatus.PENDING: JobStatusEnum.PENDING,
        JobStatus.RUNNING: JobStatusEnum.RUNNING,
        JobStatus.COMPLETED: JobStatusEnum.COMPLETED,
        JobStatus.FAILED: JobStatusEnum.FAILED,
        JobStatus.CANCELED: JobStatusEnum.CANCELED,
    }
    return mapping.get(status, JobStatusEnum.PENDING)


async def call_neurosnap(receptor_file: UploadFile, ligand_file: UploadFile, note: str) -> str:
    """Call NeuroSnap API using the correct working format."""

    # Read receptor as binary (like the working example)
    receptor_content = await receptor_file.read()
    ligand_content = await ligand_file.read()

    # Decode ligand as text for JSON
    try:
        ligand_data = ligand_content.decode("utf-8")
    except UnicodeDecodeError:
        ligand_data = ligand_content.decode("latin-1")

    print(f"DEBUG: Using correct GNINA format")
    print(f"DEBUG: Receptor size: {len(receptor_content)} bytes")
    print(f"DEBUG: Ligand size: {len(ligand_data)} chars")

    # Use the EXACT format from the working example
    fields = {
        # Receptor: tuple format (filename, binary_data) like working example
        "Input Receptor": (receptor_file.filename or "structure.pdb", receptor_content),
        # Ligand: JSON format with data first, then type (like working example)
        "Input Ligand": json.dumps([{"data": ligand_data, "type": "sdf"}]),
    }

    print(f"DEBUG: Field structure:")
    print(f"  Input Receptor: tuple with filename '{fields['Input Receptor'][0]}'")
    print(f"  Input Ligand: JSON array format")

    # Submit to NeuroSnap
    multipart_data = MultipartEncoder(fields=fields)

    print(f"DEBUG: Submitting to GNINA with correct format")

    response = requests.post(
        f"https://neurosnap.ai/api/job/submit/GNINA?note={note}",
        headers={"X-API-KEY": get_api_key(), "Content-Type": multipart_data.content_type},
        data=multipart_data,
        timeout=30,
    )

    print(f"DEBUG: NeuroSnap response status: {response.status_code}")
    print(f"DEBUG: NeuroSnap response: {response.text}")

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"NeuroSnap API error: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=502, detail=f"NeuroSnap error: {response.status_code} - {response.text}"
        )


@router.post(
    "/submit",
    response_model=DirectJobSubmissionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file format or missing files"},
        500: {"model": ErrorResponse, "description": "Job submission failed"},
        502: {"model": ErrorResponse, "description": "NeuroSnap API error"},
    },
    summary="Submit Docking Job",
    description="""
    Submit a molecular docking job to NeuroSnap's GNINA engine.

    **Required Files:**
    - **Receptor**: PDB format protein structure file
    - **Ligand**: SDF format small molecule file

    **Workflow:**
    1. Upload receptor (PDB) and ligand (SDF) files
    2. Job is submitted to NeuroSnap GNINA service
    3. Returns job ID for status monitoring
    4. Use `/status/{job_id}` to monitor progress
    5. Use `/results/{job_id}` to retrieve completed results

    **Typical Processing Time:** 15-30 minutes depending on system complexity.
    """,
    tags=["Molecular Docking"],
)
async def submit_job(
    receptor_file: UploadFile = File(
        ...,
        description="Protein receptor structure in PDB format",
        media_type="chemical/x-pdb",
    ),
    ligand_file: UploadFile = File(
        ...,
        description="Ligand molecule structure in SDF format",
        media_type="chemical/x-sdf",
    ),
    job_name: str = Form(
        default="GNINA Docking",
        description="Human-readable name for the docking job",
    ),
    note: str = Form(
        default="Docking analysis",
        description="Additional notes or description for the job",
    ),
):
    """Submit docking job to NeuroSnap."""

    # Validate files
    if not receptor_file.filename or not receptor_file.filename.endswith(".pdb"):
        raise HTTPException(status_code=400, detail="Receptor must be PDB file")
    if not ligand_file.filename or not ligand_file.filename.endswith(".sdf"):
        raise HTTPException(status_code=400, detail="Ligand must be SDF file")

    try:
        # Calculate file sizes
        receptor_content = await receptor_file.read()
        ligand_content = await ligand_file.read()

        # Reset file pointers for later use
        receptor_file.file.seek(0)
        ligand_file.file.seek(0)

        # Submit to NeuroSnap
        job_id = await call_neurosnap(receptor_file, ligand_file, f"{job_name}: {note}")

        return DirectJobSubmissionResponse(
            job_id=job_id,
            status=JobStatusEnum.PENDING,
            message=f"Job submitted to NeuroSnap (ID: {job_id})",
            receptor_info=MolecularFileInfo(
                filename=receptor_file.filename, format="pdb", size_bytes=len(receptor_content)
            ),
            ligand_info=MolecularFileInfo(
                filename=ligand_file.filename, format="sdf", size_bytes=len(ligand_content)
            ),
            job_name=job_name,
            estimated_runtime="15-30 minutes",
            submitted_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Job submission failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit job")


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Status check failed"},
    },
    summary="Get Job Status",
    description="""Check the current status and progress of a docking job.

    **Status Values:**
    - `pending`: Job submitted but not started
    - `running`: Job is currently executing
    - `completed`: Job finished successfully
    - `failed`: Job failed with error
    - `canceled`: Job was canceled by user

    **Progress Information:**
    - Progress percentage (0-100%)
    - Estimated time remaining
    - Detailed status message
    """,
    tags=["Job Management"],
)
async def get_job_status(
    job_id: str,
    client: NeuroSnapClient = Depends(get_neurosnap_client),
) -> JobStatusResponse:
    """Get current status of a docking job.

    Args:
        job_id: NeuroSnap job ID from job submission
        client: Injected NeuroSnap client

    Returns:
        Current job status with progress information

    Raises:
        HTTPException: If job not found or status check fails
    """
    try:
        async with client:
            # Get status from NeuroSnap
            status = await client.get_job_status(job_id)

            # Calculate progress percentage based on status
            progress_map = {
                JobStatus.PENDING: 0.0,
                JobStatus.RUNNING: 50.0,  # Could be enhanced with actual progress
                JobStatus.COMPLETED: 100.0,
                JobStatus.FAILED: 0.0,
                JobStatus.CANCELED: 0.0,
            }

            # Estimate remaining time based on status
            time_remaining_map = {
                JobStatus.PENDING: "10-30 minutes",
                JobStatus.RUNNING: "5-15 minutes",
                JobStatus.COMPLETED: None,
                JobStatus.FAILED: None,
                JobStatus.CANCELED: None,
            }

            return JobStatusResponse(
                job_id=job_id,
                status=map_job_status(status),
                progress_percentage=progress_map.get(status, 0.0),
                estimated_time_remaining=time_remaining_map.get(status),
                status_message=f"Job is {status.value}",
                started_at=None,  # Could be extracted from NeuroSnap if available
                updated_at=datetime.utcnow(),
            )

    except StatusCheckError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "JOB_NOT_FOUND",
                        "message": f"Job '{job_id}' not found or not accessible",
                    }
                },
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "STATUS_CHECK_FAILED",
                        "message": f"Failed to check job status: {str(e)}",
                    }
                },
            )
    except Exception as e:
        logger.error(f"Unexpected error checking job status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error checking job status",
                }
            },
        )


@router.get(
    "/results/{job_id}",
    response_model=DockingResultsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found or not completed"},
        425: {"model": ErrorResponse, "description": "Job not completed yet"},
        500: {"model": ErrorResponse, "description": "Results retrieval failed"},
    },
    summary="Get Job Results",
    description="""Retrieve complete docking results for a completed job including all poses and binding scores.

    **Results Include:**
    - All docking poses ranked by binding affinity
    - Best scoring pose details
    - Binding scores and confidence values
    - Download URLs for result files
    - Execution metadata

    **Requirements:**
    - Job must have `completed` status
    - Results are only available for successful jobs

    **File Formats:**
    - SDF files with molecular coordinates
    - Log files with detailed analysis
    """,
    tags=["Results Retrieval"],
)
async def get_job_results(
    job_id: str,
    client: NeuroSnapClient = Depends(get_neurosnap_client),
) -> DockingResultsResponse:
    """Get complete docking results for a completed job.

    Args:
        job_id: NeuroSnap job ID from job submission
        client: Injected NeuroSnap client

    Returns:
        Complete docking results with poses and binding scores

    Raises:
        HTTPException: If job not found, not completed, or results retrieval fails
    """
    try:
        async with client:
            # First check if job is completed
            status = await client.get_job_status(job_id)

            if status != JobStatus.COMPLETED:
                raise HTTPException(
                    status_code=425,
                    detail={
                        "error": {
                            "code": "JOB_NOT_COMPLETED",
                            "message": f"Job '{job_id}' is not completed (status: {status.value})",
                            "current_status": status.value,
                        }
                    },
                )

            # List available output files
            output_files = await client.list_job_files(job_id, file_type="out")
            logger.info(f"Found {len(output_files)} output files for job {job_id}")

            # Look for main result files (SDF with docking poses)
            poses = []
            best_pose = None

            # Download and parse SDF files for poses
            for filename in output_files:
                if filename.endswith(".sdf") and "pose" in filename.lower():
                    try:
                        file_content = await client.download_job_file(job_id, filename)
                        # Parse SDF content for docking poses
                        parsed_poses = parse_sdf_poses(file_content.decode("utf-8"))
                        poses.extend(parsed_poses)
                    except Exception as e:
                        logger.warning(f"Failed to parse {filename}: {e}")
                        continue

            # Sort poses by affinity (best first)
            poses.sort(key=lambda p: p.affinity)

            # Set ranks
            for i, pose in enumerate(poses, 1):
                pose.rank = i

            # Best pose is the first (lowest affinity)
            if poses:
                best_pose = poses[0]

            return DockingResultsResponse(
                job_id=job_id,
                status=JobStatusEnum.COMPLETED,
                poses=poses,
                best_pose=best_pose,
                execution_time=None,  # Could be extracted from log files
                engine_version="GNINA",
                parameters=None,  # Could be extracted from job submission data
                completed_at=datetime.utcnow(),
                download_urls={
                    f: f"https://neurosnap.ai/api/job/download/{job_id}/out/{f}"
                    for f in output_files
                },
            )

    except HTTPException:
        raise
    except (StatusCheckError, FileListingError, FileDownloadError) as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "JOB_NOT_FOUND",
                        "message": f"Job '{job_id}' not found or results not available",
                    }
                },
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "RESULTS_RETRIEVAL_FAILED",
                        "message": f"Failed to retrieve results: {str(e)}",
                    }
                },
            )
    except Exception as e:
        logger.error(f"Unexpected error retrieving results: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error retrieving results",
                }
            },
        )


@router.get(
    "/jobs",
    response_model=JobListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Job listing failed"},
    },
    summary="List Jobs",
    description="""List all docking jobs for the current user with optional filtering by status and date range.

    **Filtering Options:**
    - Filter by job status (pending, running, completed, failed)
    - Filter by submission date range
    - Search by job name substring

    **Pagination:**
    - Results are paginated for performance
    - Default page size: 20 jobs
    - Maximum page size: 100 jobs

    **Note:** Full job listing requires additional implementation for job persistence.
    Currently returns placeholder response due to NeuroSnap API limitations.
    """,
    tags=["Job Management"],
)
async def list_jobs(
    status: Optional[JobStatusEnum] = Query(None, description="Filter by job status"),
    start_date: Optional[datetime] = Query(
        None, description="Filter jobs submitted after this date"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter jobs submitted before this date"
    ),
    job_name_contains: Optional[str] = Query(None, description="Filter by job name substring"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of jobs per page"),
    client: NeuroSnapClient = Depends(get_neurosnap_client),
) -> JobListResponse:
    """List all docking jobs for the current user.

    Args:
        status: Optional status filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        job_name_contains: Optional job name substring filter
        page: Page number for pagination
        page_size: Number of jobs per page
        client: Injected NeuroSnap client

    Returns:
        Paginated list of user's docking jobs

    Raises:
        HTTPException: If job listing fails
    """
    try:
        async with client:
            # Note: NeuroSnap doesn't have a direct list_user_jobs method
            # This would need to be implemented or we'd need to maintain our own job registry
            # For now, return a placeholder response
            logger.warning("Job listing not fully implemented - NeuroSnap API limitation")

            return JobListResponse(
                jobs=[],  # Empty for now - would need job database or NeuroSnap enhancement
                total_count=0,
                page=page,
                page_size=page_size,
                filters=(
                    {
                        "status": status,
                        "start_date": start_date,
                        "end_date": end_date,
                        "job_name_contains": job_name_contains,
                    }
                    if any([status, start_date, end_date, job_name_contains])
                    else None
                ),
            )

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "JOB_LISTING_FAILED",
                    "message": f"Failed to retrieve job list: {str(e)}",
                }
            },
        )


def parse_sdf_poses(sdf_content: str) -> List[DockingPoseSchema]:
    """Parse SDF file content to extract docking poses.

    Args:
        sdf_content: Raw SDF file content

    Returns:
        List of parsed docking poses
    """
    poses = []

    try:
        # Split SDF into individual molecule blocks
        molecule_blocks = sdf_content.split("$$$$")

        for i, block in enumerate(molecule_blocks):
            if not block.strip():
                continue

            # Extract binding affinity from SDF properties
            affinity = None
            confidence = None

            lines = block.strip().split("\n")
            for line in lines:
                if "minimizedAffinity" in line:
                    try:
                        affinity = float(line.split()[-1])
                    except (ValueError, IndexError):
                        pass
                elif "CNNscore" in line or "confidence" in line:
                    try:
                        confidence = float(line.split()[-1])
                    except (ValueError, IndexError):
                        pass

            if affinity is not None:
                poses.append(
                    DockingPoseSchema(
                        rank=i + 1,  # Will be updated later when sorted
                        affinity=affinity,
                        rmsd_lb=None,  # Would need to be extracted from SDF properties
                        rmsd_ub=None,  # Would need to be extracted from SDF properties
                        confidence_score=confidence,
                        coordinates_sdf=block.strip(),
                    )
                )

    except Exception as e:
        logger.warning(f"Failed to parse SDF poses: {e}")

    return poses
