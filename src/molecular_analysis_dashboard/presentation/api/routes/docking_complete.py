"""Complete docking API with NeuroSnap integration and job lifecycle management."""

import json
import logging
import os
from datetime import datetime
from typing import List, Optional

import requests
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from requests_toolbelt.multipart.encoder import MultipartEncoder

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

from typing import Any, Dict

# Response models for basic types (avoiding complex schemas for now)
from pydantic import BaseModel


class BasicJobResponse(BaseModel):
    """Basic job response model."""

    job_id: str
    status: str
    message: str


class BasicStatusResponse(BaseModel):
    """Basic status response model."""

    job_id: str
    status: str
    progress_percentage: Optional[float] = None
    estimated_time_remaining: Optional[str] = None
    updated_at: datetime


class BasicResultsResponse(BaseModel):
    """Basic results response model."""

    job_id: str
    status: str
    files: List[str]
    download_urls: Dict[str, str]


def get_api_key() -> str:
    """Get NeuroSnap API key."""
    key = os.getenv("NEUROSNAP_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return key


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
    response_model=BasicJobResponse,
    summary="Submit Docking Job",
    description="Submit a molecular docking job to NeuroSnap's GNINA engine.",
)
async def submit_job(
    receptor_file: UploadFile = File(..., description="Protein receptor structure in PDB format"),
    ligand_file: UploadFile = File(..., description="Ligand molecule structure in SDF format"),
    job_name: str = Form(
        default="GNINA Docking", description="Human-readable name for the docking job"
    ),
    note: str = Form(default="Docking analysis", description="Additional notes for the job"),
):
    """Submit docking job to NeuroSnap."""

    # Validate files
    if not receptor_file.filename or not receptor_file.filename.endswith(".pdb"):
        raise HTTPException(status_code=400, detail="Receptor must be PDB file")
    if not ligand_file.filename or not ligand_file.filename.endswith(".sdf"):
        raise HTTPException(status_code=400, detail="Ligand must be SDF file")

    try:
        # Submit to NeuroSnap
        job_id = await call_neurosnap(receptor_file, ligand_file, f"{job_name}: {note}")

        return BasicJobResponse(
            job_id=job_id,
            status="pending",
            message=f"Job submitted to NeuroSnap (ID: {job_id})",
        )

    except Exception as e:
        logger.error(f"Job submission failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit job")


@router.get(
    "/status/{job_id}",
    response_model=BasicStatusResponse,
    summary="Get Job Status",
    description="Check the current status and progress of a docking job.",
)
async def get_job_status(job_id: str):
    """Get current status of a docking job."""

    try:
        # Call NeuroSnap status API
        response = requests.get(
            f"https://neurosnap.ai/api/job/status/{job_id}",
            headers={"X-API-KEY": get_api_key()},
            timeout=30,
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"NeuroSnap error: {response.status_code}")

        # Parse status response
        status_data = response.json()
        status = (
            status_data if isinstance(status_data, str) else status_data.get("status", "unknown")
        )

        # Calculate progress based on status
        progress_map = {
            "pending": 0.0,
            "running": 50.0,
            "completed": 100.0,
            "failed": 0.0,
        }

        time_remaining_map = {
            "pending": "10-30 minutes",
            "running": "5-15 minutes",
            "completed": None,
            "failed": None,
        }

        return BasicStatusResponse(
            job_id=job_id,
            status=status,
            progress_percentage=progress_map.get(status, 0.0),
            estimated_time_remaining=time_remaining_map.get(status),
            updated_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check job status")


@router.get(
    "/results/{job_id}",
    response_model=BasicResultsResponse,
    summary="Get Job Results",
    description="Retrieve results for a completed docking job.",
)
async def get_job_results(job_id: str):
    """Get results for a completed docking job."""

    try:
        # First check if job is completed
        status_response = requests.get(
            f"https://neurosnap.ai/api/job/status/{job_id}",
            headers={"X-API-KEY": get_api_key()},
            timeout=30,
        )

        if status_response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        status_data = status_response.json()
        status = (
            status_data if isinstance(status_data, str) else status_data.get("status", "unknown")
        )

        if status != "completed":
            raise HTTPException(
                status_code=425, detail=f"Job '{job_id}' is not completed (status: {status})"
            )

        # List output files
        files_response = requests.get(
            f"https://neurosnap.ai/api/job/files/{job_id}/out",
            headers={"X-API-KEY": get_api_key()},
            timeout=30,
        )

        if files_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to list result files")

        files = files_response.json()

        # Generate download URLs
        download_urls = {
            filename: f"https://neurosnap.ai/api/job/file/{job_id}/out/{filename}"
            for filename in files
        }

        return BasicResultsResponse(
            job_id=job_id,
            status=status,
            files=files,
            download_urls=download_urls,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Results retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve results")


@router.get(
    "/download/{job_id}/{filename}",
    summary="Download Result File",
    description="Download a specific result file from a completed job.",
)
async def download_result_file(job_id: str, filename: str):
    """Download a specific result file."""

    try:
        # Download file from NeuroSnap
        response = requests.get(
            f"https://neurosnap.ai/api/job/file/{job_id}/out/{filename}",
            headers={"X-API-KEY": get_api_key()},
            timeout=60,
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to download file")

        # Return file content with appropriate headers
        from fastapi.responses import Response

        return Response(
            content=response.content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")
