"""Shared NeuroSnap service for common operations across all engines."""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests
from fastapi import HTTPException
from fastapi.responses import Response

logger = logging.getLogger(__name__)


def get_api_key() -> str:
    """Get NeuroSnap API key."""
    key = os.getenv("NEUROSNAP_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return key


async def get_job_status(job_id: str) -> Dict:
    """Get status for any NeuroSnap job regardless of engine type."""
    try:
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

        return {"job_id": job_id, "status": status, "raw_response": status_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check job status")


async def get_job_results(job_id: str) -> Dict:
    """Get results for any completed NeuroSnap job regardless of engine type."""
    try:
        # First check if job is completed
        status_info = await get_job_status(job_id)
        status = status_info["status"]

        if status != "completed":
            raise HTTPException(
                status_code=425, detail=f"Job '{job_id}' is not completed (status: {status})"
            )

        # Get job data (files and config) from NeuroSnap
        data_response = requests.get(
            f"https://neurosnap.ai/api/job/data/{job_id}/",
            headers={"X-API-KEY": get_api_key()},
            timeout=30,
        )

        if data_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to retrieve job data")

        data = data_response.json()
        logger.info(f"NeuroSnap job {job_id} data response: {data}")

        # Extract output files
        if isinstance(data, dict) and "out" in data:
            files = [file_info[0] for file_info in data["out"] if isinstance(file_info, list)]
        else:
            files = []

        # Generate download URLs
        download_urls = {
            filename: f"https://neurosnap.ai/api/job/file/{job_id}/out/{filename}"
            for filename in files
        }

        return {
            "job_id": job_id,
            "status": status,
            "files": files,
            "download_urls": download_urls,
            "raw_data": data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Results retrieval failed: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")


async def download_job_file(job_id: str, filename: str) -> Response:
    """Download a specific result file from any NeuroSnap job."""
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

        # Determine content type based on file extension
        content_type = "application/octet-stream"
        if filename.endswith(".pdb"):
            content_type = "text/plain"
        elif filename.endswith(".sdf"):
            content_type = "chemical/x-mdl-sdfile"
        elif filename.endswith(".json"):
            content_type = "application/json"
        elif filename.endswith(".log") or filename.endswith(".txt"):
            content_type = "text/plain"
        elif filename.endswith(".csv"):
            content_type = "text/csv"

        return Response(
            content=response.content,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")


def get_progress_estimates(status: str, engine_type: str = "docking") -> Dict:
    """Get progress estimates based on engine type and status."""

    # Different engines have different typical runtimes
    if engine_type == "docking":
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
    elif engine_type == "folding":
        progress_map = {
            "pending": 0.0,
            "running": 60.0,  # Folding takes longer
            "completed": 100.0,
            "failed": 0.0,
        }
        time_remaining_map = {
            "pending": "30-60 minutes",
            "running": "15-30 minutes",
            "completed": None,
            "failed": None,
        }
    else:
        # Default estimates
        progress_map = {
            "pending": 0.0,
            "running": 50.0,
            "completed": 100.0,
            "failed": 0.0,
        }
        time_remaining_map = {
            "pending": "15-45 minutes",
            "running": "10-20 minutes",
            "completed": None,
            "failed": None,
        }

    return {
        "progress_percentage": progress_map.get(status, 0.0),
        "estimated_time_remaining": time_remaining_map.get(status),
    }


def determine_engine_type(job_id: str) -> str:
    """Determine engine type from job ID or other heuristics."""
    # This is a simple heuristic - in a real system you might store this info
    # or query the NeuroSnap API for job details

    # For now, we can make reasonable guesses based on job patterns
    # or always return "unknown" and let callers specify
    return "unknown"
