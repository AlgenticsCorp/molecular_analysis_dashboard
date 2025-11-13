"""Celery tasks for background job processing."""

from __future__ import annotations

import logging
import os
from typing import Any

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="mad.ping")
def ping() -> str:
    """Return a simple ping response for health checks."""
    return "pong"


@celery_app.task(name="mad.poll_job_status", bind=True, max_retries=3)
def poll_job_status(self, execution_id: str, external_job_id: str, task_id: str) -> dict[str, Any]:
    """Poll internal API for job status and check if polling should continue.
    
    This task polls the internal unified task API which handles the middleware
    translation between internal execution IDs and external job IDs.
    
    Args:
        execution_id: UUID of the task_framework_executions record
        external_job_id: Job ID from external service (for logging/reference)
        task_id: Task identifier (e.g., 'gnina-molecular-docking')
    
    Returns:
        dict with status update results
    """
    import httpx
    
    logger.info(f"Polling status for execution {execution_id}")
    
    # Get API base URL from environment
    api_url = os.getenv("API_URL", "http://api:8000")
    
    try:
        # Poll internal API endpoint
        response = httpx.get(
            f"{api_url}/api/v1/tasks-unified/executions/{execution_id}/status",
            timeout=30.0
        )
        response.raise_for_status()
        status_data = response.json()
        
        current_status = status_data.get("status", "unknown")
        logger.info(f"Execution {execution_id} status: {current_status}")
        
        # Non-terminal states (keep polling): pending, running
        # Terminal states (stop polling): completed, failed, cancelled
        if current_status in ("pending", "running"):
            # Schedule next poll in 10 seconds
            poll_job_status.apply_async(
                args=[execution_id, external_job_id, task_id],
                countdown=10
            )
            logger.info(f"Status is {current_status}, next poll in 10s")
            return {
                "status": "polling",
                "current_status": current_status,
                "next_poll_scheduled": True
            }
        else:
            # Terminal state reached
            logger.info(f"Terminal status reached: {current_status}")
            return {
                "status": current_status,
                "next_poll_scheduled": False,
                "error_message": status_data.get("error_message")
            }
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(f"Execution {execution_id} not found")
            return {
                "status": "error",
                "message": "Execution not found",
                "next_poll_scheduled": False
            }
        # Other HTTP errors - retry
        logger.error(f"HTTP error polling status: {e}")
        raise self.retry(countdown=60, exc=e)
    except httpx.HTTPError as e:
        # Network/timeout errors - retry
        logger.error(f"Network error polling status: {e}")
        raise self.retry(countdown=60, exc=e)
    except Exception as e:
        logger.error(f"Error polling job status: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
