"""Unified NeuroSnap operations router for common endpoints across all engines."""

import logging
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Path

from ..services.neurosnap_service import (
    download_job_file,
    get_job_results,
    get_job_status,
    get_progress_estimates,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/neurosnap",
    tags=["NeuroSnap Unified"],
    responses={
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    },
)


class UnifiedStatusResponse:
    """Unified status response that works for any engine type."""

    def __init__(self, job_id: str, status: str, engine_type: str = "unknown"):
        estimates = get_progress_estimates(status, engine_type)

        self.job_id = job_id
        self.status = status
        self.progress_percentage = estimates["progress_percentage"]
        self.estimated_time_remaining = estimates["estimated_time_remaining"]
        self.updated_at = datetime.utcnow()

        # Simplified status messages
        self.status_message = f"Job {status}"
        self.current_step = "Processing in progress" if status == "running" else None


class UnifiedResultsResponse:
    """Unified results response that works for any engine type."""

    def __init__(
        self,
        job_id: str,
        status: str,
        files: List[str],
        download_urls: Dict[str, str],
        raw_data: Dict = None,
    ):
        self.job_id = job_id
        self.status = status
        self.files = files
        self.download_urls = download_urls
        self.raw_data = raw_data


@router.get(
    "/status/{job_id}",
    summary="Get Job Status (Any Engine)",
    description="Check the current status of any NeuroSnap job (GNINA, IntelliFold, etc.).",
)
async def get_unified_job_status(job_id: str = Path(..., description="NeuroSnap job ID")):
    """Get current status of any NeuroSnap job."""

    # Get status from shared service
    status_info = await get_job_status(job_id)

    # Create unified response with default engine type
    response = UnifiedStatusResponse(job_id, status_info["status"], "unknown")

    return {
        "job_id": response.job_id,
        "status": response.status,
        "progress_percentage": response.progress_percentage,
        "estimated_time_remaining": response.estimated_time_remaining,
        "status_message": response.status_message,
        "current_step": response.current_step,
        "updated_at": response.updated_at.isoformat(),
    }


@router.get(
    "/results/{job_id}",
    summary="Get Job Results (Any Engine)",
    description="Retrieve results for any completed NeuroSnap job.",
)
async def get_unified_job_results(job_id: str = Path(..., description="NeuroSnap job ID")):
    """Get results for any completed NeuroSnap job."""

    # Get results from shared service
    results_info = await get_job_results(job_id)

    # Create unified response
    response = UnifiedResultsResponse(
        job_id=results_info["job_id"],
        status=results_info["status"],
        files=results_info["files"],
        download_urls=results_info["download_urls"],
        raw_data=results_info["raw_data"],
    )

    return {
        "job_id": response.job_id,
        "status": response.status,
        "files": response.files,
        "download_urls": response.download_urls,
        "file_count": len(response.files),
        "raw_data": response.raw_data,
    }


@router.get(
    "/download/{job_id}/{filename}",
    summary="Download Job Result File (Any Engine)",
    description="Download a specific result file from any NeuroSnap job.",
)
async def download_unified_job_file(
    job_id: str = Path(..., description="NeuroSnap job ID"),
    filename: str = Path(..., description="Name of the file to download"),
):
    """Download a specific result file from any NeuroSnap job."""

    return await download_job_file(job_id, filename)


@router.get(
    "/jobs/{job_id}",
    summary="Get Complete Job Information",
    description="Get comprehensive job information including status, results, and metadata.",
)
async def get_complete_job_info(job_id: str = Path(..., description="NeuroSnap job ID")):
    """Get complete job information including status and results if available."""

    # Get status first
    status_info = await get_job_status(job_id)
    status = status_info["status"]

    # Create base response
    response = {
        "job_id": job_id,
        "status": status,
        "status_info": status_info,
    }

    # If completed, also get results
    if status == "completed":
        try:
            results_info = await get_job_results(job_id)
            response["results"] = results_info
            response["has_results"] = True
        except Exception as e:
            logger.warning(f"Could not fetch results for completed job {job_id}: {e}")
            response["has_results"] = False
            response["results_error"] = str(e)
    else:
        response["has_results"] = False
        response["results"] = None

    # Add progress estimates
    estimates = get_progress_estimates(status, "unknown")
    response.update(estimates)

    return response
