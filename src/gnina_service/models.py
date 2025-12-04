"""Models used by the GNINA microservice."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class JobStatus(str, Enum):
    """Enumerates the lifecycle states of a GNINA job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class GninaJob:
    """Represents a docking request managed by the microservice."""

    job_id: str
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Optional[float] = None
    message: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    storage_path: Path = field(default_factory=Path)
    result_payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_status_payload(self) -> Dict[str, Any]:
        """Expose status information in a serialisable structure."""

        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        data.pop("storage_path", None)
        data.pop("result_payload", None)
        data.pop("error", None)
        return data

    def to_result_payload(self) -> Dict[str, Any]:
        """Expose final outputs with additional metadata."""

        base = {
            "job_id": self.job_id,
            "status": self.status.value,
            "metadata": {"parameters": self.parameters},
        }
        if self.result_payload:
            base.update(self.result_payload)
        if self.error:
            base["error"] = self.error
        base["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        return base

    def mark_running(self) -> None:
        self.status = JobStatus.RUNNING
        now = datetime.now(timezone.utc)
        self.started_at = now
        self.updated_at = now
        self.progress = 0.0

    def mark_progress(self, fraction: float, message: Optional[str] = None) -> None:
        self.progress = max(0.0, min(1.0, fraction))
        self.message = message
        self.updated_at = datetime.now(timezone.utc)

    def mark_success(self, payload: Dict[str, Any]) -> None:
        self.status = JobStatus.SUCCEEDED
        self.result_payload = payload
        now = datetime.now(timezone.utc)
        self.updated_at = now
        self.completed_at = now
        self.progress = 1.0
        self.message = "Job completed successfully"

    def mark_failure(self, error_message: str) -> None:
        self.status = JobStatus.FAILED
        self.error = error_message
        now = datetime.now(timezone.utc)
        self.updated_at = now
        self.completed_at = now
        self.message = error_message
        self.progress = None
