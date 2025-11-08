"""Complete structure folding API with NeuroSnap IntelliFold (AlphaFold3) integration."""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests
from fastapi import APIRouter, File, HTTPException, UploadFile
from requests_toolbelt.multipart.encoder import MultipartEncoder

from ..schemas.folding import FoldingJobRequest, FoldingJobResponse, SequenceInput

# Setup
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/folding",
    tags=["Structure Folding"],
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


async def call_neurosnap_intellifold(
    folding_request: FoldingJobRequest,
    msa_file: Optional[UploadFile] = None,
    molecule_files: Optional[List[UploadFile]] = None,
) -> str:
    """Call NeuroSnap IntelliFold API using the correct format."""

    # Prepare input sequences in the required format
    sequences_dict = {}
    for seq in folding_request.sequences:
        if seq.type.value not in sequences_dict:
            sequences_dict[seq.type.value] = {}
        sequences_dict[seq.type.value][seq.name] = seq.sequence

    print(f"DEBUG: Prepared sequences: {sequences_dict}")

    # Prepare input molecules (from request + uploaded files)
    molecules_list = []

    # Add molecules from request
    if folding_request.molecules:
        for mol in folding_request.molecules:
            molecules_list.append({"data": mol.data, "type": mol.type})

    # Add uploaded molecule files
    if molecule_files:
        for mol_file in molecule_files:
            content = await mol_file.read()
            try:
                mol_data = content.decode("utf-8")
            except UnicodeDecodeError:
                mol_data = content.decode("latin-1")

            # Determine file type from extension
            filename = mol_file.filename or "unknown"
            if filename.endswith(".sdf"):
                file_type = "sdf"
            elif filename.endswith(".mol"):
                file_type = "mol"
            elif filename.endswith(".pdb"):
                file_type = "pdb"
            else:
                file_type = "sdf"  # default

            molecules_list.append({"data": mol_data, "type": file_type})

    print(f"DEBUG: Prepared molecules: {len(molecules_list)} molecules")

    # Prepare fields for multipart request
    fields = {
        # Mandatory field - sequences
        "Input Sequences": json.dumps(sequences_dict),
    }

    # Optional fields
    if molecules_list:
        fields["Input Molecules"] = json.dumps(molecules_list)

    if folding_request.residue_modifications:
        fields["Residue Modifications"] = folding_request.residue_modifications

    fields["MSA Mode"] = folding_request.msa_mode.value

    # Custom MSA file if provided
    if msa_file:
        msa_content = await msa_file.read()
        fields["Custom MSA"] = (msa_file.filename or "custom_msa.txt", msa_content, "text/plain")

    fields["Number Recycles"] = str(folding_request.number_recycles)
    fields["Sampling Steps"] = str(folding_request.sampling_steps)
    fields["Diffusion Samples"] = str(folding_request.diffusion_samples)

    print(f"DEBUG: Final fields prepared:")
    for key, value in fields.items():
        if key == "Custom MSA":
            print(f"  {key}: MSA file uploaded")
        elif isinstance(value, str) and len(value) > 100:
            print(f"  {key}: {value[:100]}...")
        else:
            print(f"  {key}: {value}")

    # Create multipart encoder
    multipart_data = MultipartEncoder(fields=fields)

    # Submit to NeuroSnap IntelliFold API
    url = (
        f"https://neurosnap.ai/api/job/submit/IntelliFold (AlphaFold3)?note={folding_request.note}"
    )

    print(f"DEBUG: Submitting to IntelliFold: {url}")

    response = requests.post(
        url,
        headers={
            "X-API-KEY": get_api_key(),
            "Content-Type": multipart_data.content_type,
        },
        data=multipart_data,
        timeout=60,
    )

    print(f"DEBUG: NeuroSnap response status: {response.status_code}")
    print(f"DEBUG: NeuroSnap response: {response.text}")

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"NeuroSnap IntelliFold API error: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=502,
            detail=f"NeuroSnap IntelliFold error: {response.status_code} - {response.text}",
        )


@router.post(
    "/submit",
    response_model=FoldingJobResponse,
    summary="Submit Structure Folding Job",
    description="Submit a protein structure folding job to NeuroSnap's IntelliFold (AlphaFold3) engine.",
)
async def submit_folding_job(
    folding_request: FoldingJobRequest,
    msa_file: Optional[UploadFile] = File(None, description="Optional custom MSA file"),
    molecule_files: Optional[List[UploadFile]] = File(
        None, description="Optional additional molecule files (SDF/MOL/PDB)"
    ),
):
    """Submit structure folding job to NeuroSnap IntelliFold."""

    # Validation
    if not folding_request.sequences:
        raise HTTPException(status_code=400, detail="At least one sequence is required")

    # Validate sequence formats
    for seq in folding_request.sequences:
        if not seq.sequence or len(seq.sequence.strip()) == 0:
            raise HTTPException(status_code=400, detail=f"Empty sequence provided for {seq.name}")

        # Basic validation for sequence types
        if seq.type.value == "aa":
            # Basic amino acid validation
            valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
            invalid_chars = set(seq.sequence.upper()) - valid_aa
            if invalid_chars:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid amino acid characters in {seq.name}: {invalid_chars}",
                )
        elif seq.type.value == "dna":
            # Basic DNA validation
            valid_dna = set("ATCG")
            invalid_chars = set(seq.sequence.upper()) - valid_dna
            if invalid_chars:
                raise HTTPException(
                    status_code=400, detail=f"Invalid DNA characters in {seq.name}: {invalid_chars}"
                )
        elif seq.type.value == "rna":
            # Basic RNA validation
            valid_rna = set("AUCG")
            invalid_chars = set(seq.sequence.upper()) - valid_rna
            if invalid_chars:
                raise HTTPException(
                    status_code=400, detail=f"Invalid RNA characters in {seq.name}: {invalid_chars}"
                )

    try:
        # Submit to NeuroSnap IntelliFold
        job_id = await call_neurosnap_intellifold(folding_request, msa_file, molecule_files)

        # Count molecules
        molecule_count = 0
        if folding_request.molecules:
            molecule_count += len(folding_request.molecules)
        if molecule_files and len(molecule_files) > 0:
            molecule_count += len(molecule_files)

        return FoldingJobResponse(
            job_id=job_id,
            status="pending",
            message=f"Structure folding job submitted to NeuroSnap IntelliFold (ID: {job_id})",
            job_name=folding_request.job_name,
            sequences_count=len(folding_request.sequences),
            molecules_count=molecule_count,
            estimated_runtime="30-60 minutes",
            submitted_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Folding job submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit folding job: {str(e)}")


# Status endpoint moved to /api/v1/neurosnap/status/{job_id} (unified)


# Results endpoint moved to /api/v1/neurosnap/results/{job_id} (unified)


# Download endpoint moved to /api/v1/neurosnap/download/{job_id}/{filename} (unified)


@router.post(
    "/submit-simple",
    response_model=FoldingJobResponse,
    summary="Submit Simple Folding Job",
    description="Submit a simple protein folding job with just sequences (no file uploads).",
)
async def submit_simple_folding_job(
    sequences: List[SequenceInput], job_name: str = "Simple Folding"
):
    """Submit a simple folding job with just sequences."""

    # Create a basic folding request
    folding_request = FoldingJobRequest(
        job_name=job_name,
        sequences=sequences,
        molecules=None,
        note="Simple protein structure prediction",
    )

    # Use the main submission function with no file uploads
    return await submit_folding_job(folding_request, None, None)
