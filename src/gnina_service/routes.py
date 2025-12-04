"""FastAPI routes for the GNINA docking microservice."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from .job_manager import GninaJobManager, job_manager
from .models import JobStatus

logger = logging.getLogger(__name__)

JOB_NOT_FOUND_DETAIL = "Job not found"

router = APIRouter(prefix="/api/v1/gnina", tags=["GNINA"])


def get_job_manager() -> GninaJobManager:
    return job_manager


def _parse_optional_int(value: Optional[str], field: str) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError as exc:  # noqa: FBT001 - user supplied value needs validation
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid integer for {field}") from exc


def _parse_optional_float(value: Optional[str], field: str) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError as exc:  # noqa: FBT001
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid float for {field}") from exc


def _parse_optional_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _clean_parameters(raw: Dict[str, Optional[Any]]) -> Dict[str, Any]:
    parameters: Dict[str, Any] = {}
    for key, value in raw.items():
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        parameters[key] = value
    return parameters


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def submit_job(  # noqa: PLR0913 - FastAPI form signature wrapper
    receptor_file: UploadFile = File(...),
    ligand_file: UploadFile = File(...),
    job_name: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    exhaustiveness: Optional[str] = Form(None),
    num_modes: Optional[str] = Form(None),
    energy_range: Optional[str] = Form(None),
    seed: Optional[str] = Form(None),
    cnn_scoring: Optional[str] = Form(None),
    scoring: Optional[str] = Form(None),
    advanced_parameters: Optional[str] = Form(None),
    manager: GninaJobManager = Depends(get_job_manager),
) -> Dict[str, object]:
    receptor_bytes = await receptor_file.read()
    ligand_bytes = await ligand_file.read()
    if not receptor_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Receptor file is empty")
    if not ligand_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Ligand file is empty")
    files_payload = {
        "receptor_file": (receptor_file.filename or "receptor.pdbqt", receptor_bytes),
        "ligand_file": (ligand_file.filename or "ligand.pdbqt", ligand_bytes),
    }
    await receptor_file.close()
    await ligand_file.close()

    advanced_payload: Optional[Dict[str, Any]] = None
    if advanced_parameters:
        try:
            loaded = json.loads(advanced_parameters)
        except json.JSONDecodeError as exc:  # noqa: FBT001 - user supplied data must be valid JSON
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="advanced_parameters must be a JSON object",
            ) from exc
        if not isinstance(loaded, dict):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="advanced_parameters must be a JSON object",
            )
        advanced_payload = loaded

    parameters = _clean_parameters(
        {
            "job_name": _parse_optional_str(job_name),
            "note": _parse_optional_str(note),
            "exhaustiveness": _parse_optional_int(exhaustiveness, "exhaustiveness"),
            "num_modes": _parse_optional_int(num_modes, "num_modes"),
            "energy_range": _parse_optional_float(energy_range, "energy_range"),
            "seed": _parse_optional_int(seed, "seed"),
            "cnn_scoring": _parse_optional_str(cnn_scoring),
            "scoring": _parse_optional_str(scoring),
            "advanced_parameters": advanced_payload,
            "receptor_file_name": _parse_optional_str(receptor_file.filename),
            "ligand_file_name": _parse_optional_str(ligand_file.filename),
        }
    )

    job = await manager.submit_job(parameters=parameters, files=files_payload)
    payload = {
        "job_id": job.job_id,
        "status": job.status.value,
        "queued_at": job.created_at.isoformat(),
    }
    if job.parameters:
        payload["parameters"] = job.parameters
    return payload


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, manager: GninaJobManager = Depends(get_job_manager)) -> Dict[str, object]:
    job = await manager.get_job(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=JOB_NOT_FOUND_DETAIL)
    payload = job.to_status_payload()
    if job.status == JobStatus.FAILED and job.error:
        payload["error"] = job.error
    return payload


@router.get("/jobs/{job_id}/results")
async def get_job_results(job_id: str, manager: GninaJobManager = Depends(get_job_manager)) -> Dict[str, object]:
    job = await manager.get_job(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=JOB_NOT_FOUND_DETAIL)
    if job.status == JobStatus.SUCCEEDED:
        return job.to_result_payload()
    if job.status == JobStatus.FAILED:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"job_id": job.job_id, "status": job.status.value, "error": job.error},
        )
    raise HTTPException(status.HTTP_409_CONFLICT, detail="Job results are not ready")


@router.get("/jobs/{job_id}/files/{file_name}")
async def download_job_file(
    job_id: str,
    file_name: str,
    manager: GninaJobManager = Depends(get_job_manager),
) -> FileResponse:
    job = await manager.get_job(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=JOB_NOT_FOUND_DETAIL)
    safe_name = Path(file_name).name
    target_path = job.storage_path / "results" / safe_name
    if not target_path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not available")
    logger.debug("Serving GNINA result file %s for job %s", safe_name, job_id)
    return FileResponse(target_path, media_type="text/plain", filename=safe_name)
