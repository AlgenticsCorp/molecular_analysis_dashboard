"""Pydantic schemas for docking API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ....domain.entities.docking_job import JobStatus


class JobStatusEnum(str, Enum):
    """Job status enumeration for API responses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class MolecularFileInfo(BaseModel):
    """Information about an uploaded molecular file."""

    filename: str = Field(..., description="Original filename")
    format: str = Field(..., description="File format (pdb, sdf, mol2, etc.)")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")

    class Config:
        schema_extra = {
            "example": {"filename": "1HTM_receptor.pdb", "format": "pdb", "size_bytes": 245631}
        }


class DirectJobSubmissionResponse(BaseModel):
    """Response from direct job submission to NeuroSnap."""

    job_id: str = Field(..., description="NeuroSnap job ID")
    status: JobStatusEnum = Field(..., description="Initial job status")
    message: str = Field(..., description="Submission status message")
    receptor_info: MolecularFileInfo = Field(..., description="Uploaded receptor information")
    ligand_info: MolecularFileInfo = Field(..., description="Uploaded ligand information")
    job_name: str = Field(..., description="User-provided job name")
    estimated_runtime: str = Field(..., description="Estimated completion time")
    submitted_at: Optional[datetime] = Field(default=None, description="Submission timestamp")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "68d8615c545d2bb25a34dc95",
                "status": "pending",
                "message": "Job submitted to NeuroSnap successfully",
                "receptor_info": {
                    "filename": "1HTM_receptor.pdb",
                    "format": "pdb",
                    "size_bytes": 245631,
                },
                "ligand_info": {"filename": "erlotinib.sdf", "format": "sdf", "size_bytes": 3421},
                "job_name": "EGFR-Erlotinib Docking",
                "estimated_runtime": "15-30 minutes",
                "submitted_at": "2025-09-27T10:30:00Z",
            }
        }


class JobStatusResponse(BaseModel):
    """Response for job status queries."""

    job_id: str = Field(..., description="NeuroSnap job ID")
    status: JobStatusEnum = Field(..., description="Current job status")
    progress_percentage: Optional[float] = Field(
        None, description="Job progress (0-100)", ge=0, le=100
    )
    estimated_time_remaining: Optional[str] = Field(
        None, description="Estimated time to completion"
    )
    status_message: Optional[str] = Field(None, description="Detailed status message")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last status update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "68d8615c545d2bb25a34dc95",
                "status": "running",
                "progress_percentage": 75.0,
                "estimated_time_remaining": "5-8 minutes",
                "status_message": "Processing docking poses...",
                "started_at": "2025-09-27T10:32:15Z",
                "updated_at": "2025-09-27T10:45:30Z",
            }
        }


class DockingPoseSchema(BaseModel):
    """Individual docking pose result."""

    rank: int = Field(..., description="Pose ranking (1 = best)")
    affinity: float = Field(..., description="Binding affinity (kcal/mol)")
    rmsd_lb: Optional[float] = Field(None, description="RMSD lower bound")
    rmsd_ub: Optional[float] = Field(None, description="RMSD upper bound")
    confidence_score: Optional[float] = Field(None, description="CNN confidence score", ge=0, le=1)
    coordinates_sdf: Optional[str] = Field(None, description="SDF format coordinates")

    class Config:
        schema_extra = {
            "example": {
                "rank": 1,
                "affinity": -8.7,
                "rmsd_lb": 0.0,
                "rmsd_ub": 2.1,
                "confidence_score": 0.92,
                "coordinates_sdf": "...\nSDF coordinate data\n...",
            }
        }


class DockingResultsResponse(BaseModel):
    """Complete docking results for a completed job."""

    job_id: str = Field(..., description="NeuroSnap job ID")
    status: JobStatusEnum = Field(..., description="Final job status")
    poses: List[DockingPoseSchema] = Field(..., description="All docking poses ranked by affinity")
    best_pose: Optional[DockingPoseSchema] = Field(None, description="Best scoring pose")
    execution_time: Optional[float] = Field(None, description="Total execution time in seconds")
    engine_version: Optional[str] = Field(None, description="Docking engine version used")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Docking parameters used")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    download_urls: Optional[Dict[str, str]] = Field(
        None, description="URLs for downloading result files"
    )

    class Config:
        schema_extra = {
            "example": {
                "job_id": "68d8615c545d2bb25a34dc95",
                "status": "completed",
                "poses": [
                    {
                        "rank": 1,
                        "affinity": -8.7,
                        "rmsd_lb": 0.0,
                        "rmsd_ub": 2.1,
                        "confidence_score": 0.92,
                    },
                    {
                        "rank": 2,
                        "affinity": -8.2,
                        "rmsd_lb": 0.5,
                        "rmsd_ub": 2.8,
                        "confidence_score": 0.87,
                    },
                ],
                "best_pose": {
                    "rank": 1,
                    "affinity": -8.7,
                    "rmsd_lb": 0.0,
                    "rmsd_ub": 2.1,
                    "confidence_score": 0.92,
                },
                "execution_time": 1247.5,
                "engine_version": "GNINA v1.0",
                "completed_at": "2025-09-27T11:02:45Z",
                "download_urls": {
                    "results_sdf": "https://neurosnap.ai/download/...",
                    "log_file": "https://neurosnap.ai/download/...",
                },
            }
        }


class JobSummary(BaseModel):
    """Summary information for a docking job."""

    job_id: str = Field(..., description="NeuroSnap job ID")
    job_name: str = Field(..., description="User-provided job name")
    status: JobStatusEnum = Field(..., description="Current job status")
    receptor_filename: str = Field(..., description="Receptor filename")
    ligand_filename: str = Field(..., description="Ligand filename")
    submitted_at: datetime = Field(..., description="Job submission timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    best_affinity: Optional[float] = Field(None, description="Best binding affinity if completed")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "68d8615c545d2bb25a34dc95",
                "job_name": "EGFR-Erlotinib Docking",
                "status": "completed",
                "receptor_filename": "1HTM_receptor.pdb",
                "ligand_filename": "erlotinib.sdf",
                "submitted_at": "2025-09-27T10:30:00Z",
                "completed_at": "2025-09-27T11:02:45Z",
                "best_affinity": -8.7,
            }
        }


class JobListResponse(BaseModel):
    """Response for listing user's docking jobs."""

    jobs: List[JobSummary] = Field(..., description="List of user's docking jobs")
    total_count: int = Field(..., description="Total number of jobs")
    page: int = Field(default=1, description="Current page number", ge=1)
    page_size: int = Field(default=20, description="Number of jobs per page", ge=1, le=100)
    filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters")

    class Config:
        schema_extra = {
            "example": {
                "jobs": [
                    {
                        "job_id": "68d8615c545d2bb25a34dc95",
                        "job_name": "EGFR-Erlotinib Docking",
                        "status": "completed",
                        "receptor_filename": "1HTM_receptor.pdb",
                        "ligand_filename": "erlotinib.sdf",
                        "submitted_at": "2025-09-27T10:30:00Z",
                        "completed_at": "2025-09-27T11:02:45Z",
                        "best_affinity": -8.7,
                    }
                ],
                "total_count": 1,
                "page": 1,
                "page_size": 20,
                "filters": {"status": "completed"},
            }
        }


class JobFilterParams(BaseModel):
    """Parameters for filtering job lists."""

    status: Optional[JobStatusEnum] = Field(None, description="Filter by job status")
    start_date: Optional[datetime] = Field(
        None, description="Filter jobs submitted after this date"
    )
    end_date: Optional[datetime] = Field(None, description="Filter jobs submitted before this date")
    job_name_contains: Optional[str] = Field(None, description="Filter by job name substring")
    page: int = Field(default=1, description="Page number", ge=1)
    page_size: int = Field(default=20, description="Number of jobs per page", ge=1, le=100)

    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "start_date": "2025-09-01T00:00:00Z",
                "end_date": "2025-09-30T23:59:59Z",
                "job_name_contains": "EGFR",
                "page": 1,
                "page_size": 20,
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: Dict[str, Any] = Field(..., description="Error details")

    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": "Job 'invalid-id' not found or not accessible",
                    "details": {"job_id": "invalid-id", "timestamp": "2025-09-27T12:00:00Z"},
                }
            }
        }
