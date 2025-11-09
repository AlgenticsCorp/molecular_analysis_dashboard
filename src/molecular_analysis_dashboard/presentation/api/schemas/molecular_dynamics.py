"""Pydantic schemas for molecular dynamics API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AMBERRelaxationJobStatus(str, Enum):
    """AMBER relaxation job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class AMBERRelaxationRequest(BaseModel):
    """Request schema for AMBER relaxation job submission."""

    job_name: str = Field(default="AMBER Relaxation", description="Human-readable job name")
    max_iterations: int = Field(
        default=2500, ge=100, le=10000, description="Maximum number of relaxation iterations"
    )
    tolerance: float = Field(
        default=1.0, ge=0.1, le=10.0, description="Energy convergence tolerance"
    )
    note: str = Field(
        default="Molecular dynamics relaxation analysis", description="Additional notes"
    )


class MolecularDynamicsJobResponse(BaseModel):
    """Response from molecular dynamics job submission."""

    job_id: str = Field(description="NeuroSnap job ID")
    status: str = Field(description="Initial job status")
    message: str = Field(description="Submission status message")
    job_name: str = Field(description="User-provided job name")
    max_iterations: int = Field(description="Maximum iterations configured")
    tolerance: float = Field(description="Convergence tolerance configured")
    estimated_runtime: str = Field(description="Estimated completion time")
    submitted_at: Optional[datetime] = Field(description="Submission timestamp")
