"""
Pydantic schemas for molecular docking API endpoints.

This module defines request/response schemas for the professional docking API,
following NeuroSnap-style patterns with proper OpenAPI documentation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ....domain.entities.docking_job import JobStatus


class FileUploadResponse(BaseModel):
    """Response schema for file upload endpoints."""

    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    filename: str = Field(..., description="Original filename")
    format: str = Field(..., description="File format (pdb, sdf, mol2)")
    file_type: str = Field(..., description="File type (receptor, ligand)")
    size_bytes: int = Field(..., description="File size in bytes")
    validation_info: Dict[str, Any] = Field(..., description="File validation results")
    storage_path: str = Field(..., description="Internal storage path")
    name: str = Field(..., description="Display name for the file")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "12345678-1234-5678-1234-123456789012",
                "filename": "protein.pdb",
                "format": "pdb",
                "file_type": "receptor",
                "size_bytes": 125432,
                "validation_info": {"atom_count": 2456, "has_coordinates": True, "format": "pdb"},
                "storage_path": "docking/receptors/org-id/file-id.pdb",
                "name": "EGFR Kinase Domain",
            }
        }


class JobSubmissionRequest(BaseModel):
    """Request schema for submitting docking jobs."""

    receptor_file_id: str = Field(..., description="File ID of uploaded receptor PDB")
    ligand_file_id: str = Field(..., description="File ID of uploaded ligand SDF")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional GNINA parameters (exhaustiveness, num_modes, etc.)"
    )
    job_name: Optional[str] = Field(None, description="Optional name for the job")
    note: Optional[str] = Field(None, description="Optional job description/note")

    class Config:
        schema_extra = {
            "example": {
                "receptor_file_id": "12345678-1234-5678-1234-123456789012",
                "ligand_file_id": "87654321-4321-8765-4321-210987654321",
                "parameters": {"exhaustiveness": 8, "num_modes": 9, "energy_range": 3},
                "job_name": "EGFR-Osimertinib Docking",
                "note": "Testing drug resistance mutations",
            }
        }


class DirectJobSubmissionResponse(BaseModel):
    """Response schema for direct job submission with file uploads."""

    job_id: str = Field(..., description="Unique identifier for the submitted job")
    status: JobStatus = Field(..., description="Initial job status")
    message: str = Field(..., description="Submission confirmation message")
    receptor_info: Dict[str, Any] = Field(..., description="Uploaded receptor file information")
    ligand_info: Dict[str, Any] = Field(..., description="Uploaded ligand file information")
    job_name: str = Field(..., description="User-provided job name")
    estimated_runtime: Optional[str] = Field(None, description="Estimated completion time")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job-12345678-1234-5678-1234-123456789012",
                "status": "pending",
                "message": "GNINA docking job submitted successfully with uploaded files",
                "receptor_info": {
                    "filename": "egfr_kinase.pdb",
                    "format": "pdb",
                    "atom_count": 2456,
                    "size_bytes": 125432,
                },
                "ligand_info": {"filename": "osimertinib.sdf", "format": "sdf", "size_bytes": 3421},
                "job_name": "EGFR-Osimertinib Docking",
                "estimated_runtime": "15-30 minutes",
            }
        }


class JobSubmissionResponse(BaseModel):
    """Response schema for job submission."""

    job_id: str = Field(..., description="Unique identifier for the submitted job")
    status: JobStatus = Field(..., description="Initial job status")
    message: str = Field(..., description="Submission confirmation message")
    receptor_file_id: str = Field(..., description="Receptor file ID used")
    ligand_file_id: str = Field(..., description="Ligand file ID used")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Job parameters")
    estimated_runtime: Optional[str] = Field(None, description="Estimated completion time")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "job-12345678-1234-5678-1234-123456789012",
                "status": "pending",
                "message": "Job submitted successfully to GNINA queue",
                "receptor_file_id": "12345678-1234-5678-1234-123456789012",
                "ligand_file_id": "87654321-4321-8765-4321-210987654321",
                "parameters": {"exhaustiveness": 8, "num_modes": 9},
                "estimated_runtime": "5-10 minutes",
            }
        }


class JobStatusResponse(BaseModel):
    """Response schema for job status queries."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress: float = Field(..., description="Job progress (0.0 to 1.0)")
    message: str = Field(..., description="Status message or error details")
    created_at: str = Field(..., description="Job creation timestamp (ISO format)")
    started_at: Optional[str] = Field(None, description="Job start timestamp")
    completed_at: Optional[str] = Field(None, description="Job completion timestamp")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "job-12345678-1234-5678-1234-123456789012",
                "status": "running",
                "progress": 0.65,
                "message": "Docking in progress - evaluating poses",
                "created_at": "2025-09-26T19:00:00Z",
                "started_at": "2025-09-26T19:01:30Z",
                "completed_at": None,
                "estimated_completion": "2025-09-26T19:08:00Z",
            }
        }


class DockingJobInfo(BaseModel):
    """Information about a single docking job."""

    job_id: str = Field(..., description="Job identifier")
    job_name: Optional[str] = Field(None, description="User-provided job name")
    status: JobStatus = Field(..., description="Current job status")
    receptor_name: str = Field(..., description="Receptor file name")
    ligand_name: str = Field(..., description="Ligand file name")
    created_at: str = Field(..., description="Job creation timestamp")
    completed_at: Optional[str] = Field(None, description="Job completion timestamp")
    runtime: Optional[str] = Field(None, description="Job runtime duration")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "job-12345678-1234-5678-1234-123456789012",
                "job_name": "EGFR-Osimertinib Docking",
                "status": "completed",
                "receptor_name": "EGFR Kinase Domain",
                "ligand_name": "Osimertinib",
                "created_at": "2025-09-26T19:00:00Z",
                "completed_at": "2025-09-26T19:07:45Z",
                "runtime": "7m 45s",
            }
        }


class UserJobsResponse(BaseModel):
    """Response schema for listing user jobs."""

    jobs: List[DockingJobInfo] = Field(..., description="List of user's docking jobs")
    total_jobs: int = Field(..., description="Total number of jobs")

    class Config:
        schema_extra = {
            "example": {
                "jobs": [
                    {
                        "job_id": "job-12345678-1234-5678-1234-123456789012",
                        "job_name": "EGFR-Osimertinib Docking",
                        "status": "completed",
                        "receptor_name": "EGFR Kinase Domain",
                        "ligand_name": "Osimertinib",
                        "created_at": "2025-09-26T19:00:00Z",
                        "completed_at": "2025-09-26T19:07:45Z",
                        "runtime": "7m 45s",
                    }
                ],
                "total_jobs": 1,
            }
        }


class DockingResultsResponse(BaseModel):
    """Response schema for job results."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Job status")
    results_available: bool = Field(..., description="Whether results are ready for download")
    message: str = Field(..., description="Results status message")
    download_urls: Dict[str, str] = Field(..., description="URLs for downloading result files")
    summary: Optional[Dict[str, Any]] = Field(None, description="Result summary statistics")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "job-12345678-1234-5678-1234-123456789012",
                "status": "completed",
                "results_available": True,
                "message": "Results ready for download",
                "download_urls": {
                    "poses_sdf": "/api/v1/docking/jobs/job-123/files/poses.sdf",
                    "scores_csv": "/api/v1/docking/jobs/job-123/files/scores.csv",
                    "summary_json": "/api/v1/docking/jobs/job-123/files/summary.json",
                },
                "summary": {"best_affinity": -9.2, "num_poses": 9, "runtime": "7m 45s"},
            }
        }
