"""Complete molecular dynamics API with NeuroSnap AMBER Relaxation integration."""

import json
import logging
import os
from datetime import datetime
from typing import Optional

import requests
from fastapi import APIRouter, File, HTTPException, UploadFile
from requests_toolbelt.multipart.encoder import MultipartEncoder

from ..schemas.molecular_dynamics import AMBERRelaxationRequest, MolecularDynamicsJobResponse

# Setup
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/providers/neurosnap/molecular-dynamics",
    tags=["🔬 Molecular Dynamics", "☁️ NeuroSnap Cloud"],
    responses={
        401: {"description": "Authentication failed"},
        402: {"description": "NeuroSnap API credits exhausted"},
        500: {"description": "Internal server error"},
    },
)


def get_api_key() -> str:
    """Get NeuroSnap API key from environment."""
    api_key = os.getenv("NEUROSNAP_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NeuroSnap API key not configured")
    return api_key


async def call_neurosnap_amber_relaxation(
    structure_file: UploadFile,
    relaxation_request: AMBERRelaxationRequest,
) -> str:
    """Call NeuroSnap AMBER Relaxation API using the correct format."""

    # Read the structure file
    structure_content = await structure_file.read()

    # Prepare fields for multipart upload
    fields = {}

    # Mandatory fields
    fields["Input Structure"] = (
        structure_file.filename or "structure.pdb",
        structure_content,
        "application/octet-stream",
    )

    # Optional fields
    fields["Max Iterations"] = str(relaxation_request.max_iterations)
    fields["Tolerance"] = str(relaxation_request.tolerance)

    print(f"DEBUG: Final fields prepared:")
    for key, value in fields.items():
        if key == "Input Structure":
            print(f"  {key}: Structure file uploaded ({len(structure_content)} bytes)")
        else:
            print(f"  {key}: {value}")

    # Create multipart encoder
    multipart_data = MultipartEncoder(fields=fields)

    # Submit to NeuroSnap AMBER Relaxation API
    url = f"https://neurosnap.ai/api/job/submit/AMBER Relaxation?note={relaxation_request.note}"

    print(f"DEBUG: Submitting to AMBER Relaxation: {url}")

    response = requests.post(
        url,
        headers={
            "X-API-KEY": get_api_key(),
            "Content-Type": multipart_data.content_type,
        },
        data=multipart_data,
        timeout=60,
    )

    print(f"DEBUG: NeuroSnap AMBER response status: {response.status_code}")
    print(f"DEBUG: NeuroSnap AMBER response: {response.text}")

    if response.status_code == 200:
        result = response.json()
        if isinstance(result, dict) and "job_id" in result:
            return result["job_id"]
        else:
            # Handle case where response is just the job ID string
            return result
    else:
        logger.error(f"NeuroSnap AMBER API error: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=502,
            detail=f"NeuroSnap AMBER error: {response.status_code} - {response.text}",
        )


@router.post(
    "/amber-relaxation/submit",
    response_model=MolecularDynamicsJobResponse,
    summary="Submit AMBER Relaxation Job",
    description="Submit a molecular dynamics relaxation job to NeuroSnap's AMBER engine.",
)
async def submit_amber_relaxation_job(
    structure_file: UploadFile = File(..., description="Input protein structure in PDB format"),
    max_iterations: int = 2500,
    tolerance: float = 1.0,
    job_name: str = "AMBER Relaxation",
    note: str = "Molecular dynamics relaxation analysis",
):
    """Submit AMBER relaxation job to NeuroSnap."""

    # Validation
    if not structure_file.filename:
        raise HTTPException(status_code=400, detail="Structure file is required")

    # Check file format
    if not structure_file.filename.lower().endswith((".pdb", ".pdbqt")):
        raise HTTPException(
            status_code=400, detail="Structure file must be in PDB format (.pdb or .pdbqt)"
        )

    # Validate parameters
    if max_iterations < 100 or max_iterations > 10000:
        raise HTTPException(status_code=400, detail="Max iterations must be between 100 and 10000")

    if tolerance < 0.1 or tolerance > 10.0:
        raise HTTPException(status_code=400, detail="Tolerance must be between 0.1 and 10.0")

    # Create relaxation request
    relaxation_request = AMBERRelaxationRequest(
        job_name=job_name,
        max_iterations=max_iterations,
        tolerance=tolerance,
        note=note,
    )

    try:
        # Submit to NeuroSnap AMBER
        job_id = await call_neurosnap_amber_relaxation(structure_file, relaxation_request)

        return MolecularDynamicsJobResponse(
            job_id=job_id,
            status="pending",
            message=f"AMBER relaxation job submitted to NeuroSnap (ID: {job_id})",
            job_name=relaxation_request.job_name,
            max_iterations=relaxation_request.max_iterations,
            tolerance=relaxation_request.tolerance,
            estimated_runtime="15-45 minutes",
            submitted_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"AMBER relaxation job submission failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit AMBER relaxation job: {str(e)}"
        )


@router.post(
    "/amber-relaxation/submit-simple",
    response_model=MolecularDynamicsJobResponse,
    summary="Submit AMBER Relaxation Simple Job",
    description="Submit a simple AMBER relaxation job with default parameters.",
)
async def submit_simple_amber_relaxation_job(
    structure_file: UploadFile = File(..., description="Input protein structure in PDB format"),
    job_name: str = "Simple AMBER Relaxation",
):
    """Submit a simple AMBER relaxation job with default parameters."""

    return await submit_amber_relaxation_job(
        structure_file=structure_file,
        max_iterations=2500,
        tolerance=1.0,
        job_name=job_name,
        note="Simple molecular dynamics relaxation with default parameters",
    )
