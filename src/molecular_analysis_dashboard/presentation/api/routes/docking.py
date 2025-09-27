"""Simple and clean docking API with NeuroSnap integration."""

import json
import logging
import os

import requests
from fastapi import APIRouter, File, HTTPException, UploadFile
from requests_toolbelt.multipart.encoder import MultipartEncoder

from ....domain.entities.docking_job import JobStatus
from ..schemas.docking import DirectJobSubmissionResponse

# Setup
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/docking", tags=["docking"])


def get_api_key() -> str:
    """Get NeuroSnap API key."""
    key = os.getenv("NEUROSNAP_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return key


async def call_neurosnap(receptor_file: UploadFile, ligand_file: UploadFile, note: str) -> str:
    """Call NeuroSnap API exactly like the working script."""

    # Read files
    receptor_data = (await receptor_file.read()).decode("utf-8")
    ligand_data = (await ligand_file.read()).decode("utf-8")

    # Prepare data exactly like working script
    fields = {
        "Input Receptor": json.dumps(
            [
                {
                    "type": "pdb",
                    "name": (
                        receptor_file.filename.split(".")[0]
                        if receptor_file.filename
                        else "receptor"
                    ),
                    "data": receptor_data,
                }
            ]
        ),
        "Input Ligand": json.dumps([{"type": "sdf", "data": ligand_data}]),
    }

    # Submit to NeuroSnap
    multipart_data = MultipartEncoder(fields=fields)
    response = requests.post(
        f"https://neurosnap.ai/api/job/submit/GNINA?note={note}",
        headers={"X-API-KEY": get_api_key(), "Content-Type": multipart_data.content_type},
        data=multipart_data,
        timeout=30,
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(
            status_code=502, detail=f"NeuroSnap error: {response.status_code} - {response.text}"
        )


@router.post("/submit", response_model=DirectJobSubmissionResponse)
async def submit_job(
    receptor_file: UploadFile = File(...),
    ligand_file: UploadFile = File(...),
    job_name: str = "GNINA Docking",
    note: str = "Docking analysis",
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

        return DirectJobSubmissionResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message=f"Job submitted to NeuroSnap (ID: {job_id})",
            receptor_info={"filename": receptor_file.filename, "format": "pdb"},
            ligand_info={"filename": ligand_file.filename, "format": "sdf"},
            job_name=job_name,
            estimated_runtime="15-30 minutes",
        )

    except Exception as e:
        logger.error(f"Job submission failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit job")
