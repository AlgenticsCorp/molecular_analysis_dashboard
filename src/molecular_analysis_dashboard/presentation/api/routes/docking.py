"""Complete docking API with NeuroSnap integration and job lifecycle management."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from requests_toolbelt.multipart.encoder import MultipartEncoder

from ..services.neurosnap_service import (
    download_job_file,
    get_api_key,
    get_job_results,
    get_job_status,
    get_progress_estimates,
)

# Setup
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/docking",
    tags=["🎯 Molecular Docking", "☁️ NeuroSnap Cloud"],
    responses={
        401: {"description": "Authentication failed"},
        402: {"description": "NeuroSnap API credits exhausted"},
        500: {"description": "Internal server error"},
    },
)


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


# Status endpoint moved to /api/v1/neurosnap/status/{job_id} (unified)


# Results endpoint moved to /api/v1/neurosnap/results/{job_id} (unified)


# Download endpoint moved to /api/v1/neurosnap/download/{job_id}/{filename} (unified)
