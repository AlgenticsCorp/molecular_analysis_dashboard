"""Pydantic schemas for task execution API endpoints.

This module defines the request and response schemas for molecular task
execution endpoints, providing comprehensive validation and documentation
for the task execution API.

Responsibilities:
- Define request schemas for task execution with proper validation
- Define response schemas for execution tracking and results
- Provide OpenAPI documentation through Pydantic models
- Enable type-safe API interactions with comprehensive examples

Dependencies:
- pydantic: For data validation and serialization
- typing: For type hints and validation
- datetime: For timestamp handling
- uuid: For unique identifier handling

Schemas:
- TaskExecutionRequest: Parameters for executing a molecular task
- MolecularStructureSchema: Molecular structure data representation
- BindingSiteSchema: Binding site configuration for docking
- TaskExecutionResponse: Execution tracking and status information
- DockingResultsSchema: Complete docking analysis results
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator


class JobStatusSchema(str, Enum):
    """Job execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class MolecularStructureSchema(BaseModel):
    """Molecular structure data schema."""

    name: str = Field(..., description="Human-readable name for the structure")
    format: str = Field(..., description="Structure format (pdb, sdf, mol2, pdbqt)")
    data: str = Field(..., description="Structure file content or data URI")
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional structure properties and metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "EGFR Kinase Domain",
                "format": "pdb",
                "data": "HEADER    TRANSFERASE...",
                "properties": {"resolution": 2.4, "method": "X-RAY DIFFRACTION"},
            }
        }


class BindingSiteSchema(BaseModel):
    """Binding site configuration for molecular docking."""

    center_x: float = Field(..., description="X-coordinate of binding site center (Å)")
    center_y: float = Field(..., description="Y-coordinate of binding site center (Å)")
    center_z: float = Field(..., description="Z-coordinate of binding site center (Å)")
    size_x: float = Field(..., description="X-dimension of search box (Å)")
    size_y: float = Field(..., description="Y-dimension of search box (Å)")
    size_z: float = Field(..., description="Z-dimension of search box (Å)")

    @validator("center_x", "center_y", "center_z")
    def validate_coordinates(cls, v):
        if not -1000 <= v <= 1000:
            raise ValueError("Coordinates must be between -1000 and 1000 Å")
        return v

    @validator("size_x", "size_y", "size_z")
    def validate_dimensions(cls, v):
        if not 5.0 <= v <= 50.0:
            raise ValueError("Box dimensions must be between 5.0 and 50.0 Å")
        return v

    class Config:
        schema_extra = {
            "example": {
                "center_x": 25.5,
                "center_y": 10.2,
                "center_z": 15.8,
                "size_x": 20.0,
                "size_y": 20.0,
                "size_z": 20.0,
            }
        }


class TaskExecutionRequest(BaseModel):
    """Request schema for executing a molecular task."""

    # Required inputs
    receptor: Union[MolecularStructureSchema, Dict[str, Any]] = Field(
        ..., description="Protein/receptor structure data"
    )
    ligand: Union[MolecularStructureSchema, Dict[str, Any], str] = Field(
        ..., description="Ligand structure data or drug name for auto-preparation"
    )

    # Optional docking parameters
    binding_site: Optional[BindingSiteSchema] = Field(
        None,
        description="Binding site configuration (optional - will use automatic detection if not provided)",
    )
    job_note: Optional[str] = Field(
        None, max_length=500, description="Human-readable description of the docking job"
    )
    max_poses: int = Field(
        default=9, ge=1, le=20, description="Maximum number of binding poses to generate"
    )
    energy_range: float = Field(
        default=3.0, ge=0.5, le=10.0, description="Energy range for pose selection (kcal/mol)"
    )
    exhaustiveness: int = Field(
        default=8, ge=1, le=32, description="Exhaustiveness of the global search"
    )

    # Execution control
    timeout_minutes: int = Field(
        default=30, ge=5, le=120, description="Maximum execution time in minutes"
    )

    # Metadata
    organization_id: Optional[str] = Field(
        None, description="Organization ID for multi-tenant access control"
    )
    user_id: Optional[str] = Field(None, description="User ID for audit logging")
    task_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional task-specific metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "receptor": {
                    "name": "EGFR T790M",
                    "format": "pdb",
                    "data": "HEADER    TRANSFERASE...",
                },
                "ligand": "osimertinib",
                "binding_site": {
                    "center_x": 25.5,
                    "center_y": 10.2,
                    "center_z": 15.8,
                    "size_x": 20.0,
                    "size_y": 20.0,
                    "size_z": 20.0,
                },
                "job_note": "EGFR resistance mutation analysis",
                "max_poses": 9,
                "energy_range": 3.0,
                "exhaustiveness": 8,
                "timeout_minutes": 30,
            }
        }


class DockingPoseSchema(BaseModel):
    """Individual docking pose result schema."""

    rank: int = Field(..., description="Pose ranking by binding affinity")
    affinity: float = Field(..., description="Binding affinity in kcal/mol")
    rmsd_lb: Optional[float] = Field(None, description="RMSD lower bound")
    rmsd_ub: Optional[float] = Field(None, description="RMSD upper bound")
    confidence_score: Optional[float] = Field(None, description="Neural network confidence score")
    pose_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional pose-specific data"
    )


class DockingResultsSchema(BaseModel):
    """Complete docking analysis results schema."""

    poses: List[DockingPoseSchema] = Field(..., description="All generated binding poses")
    best_pose: Optional[DockingPoseSchema] = Field(
        None, description="Best binding pose by affinity"
    )
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    engine_version: Optional[str] = Field(None, description="Docking engine version used")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Parameters used for docking"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional analysis metadata"
    )


class TaskExecutionResponse(BaseModel):
    """Response schema for task execution tracking."""

    execution_id: UUID = Field(..., description="Unique execution identifier")
    job_id: Optional[str] = Field(None, description="External provider job identifier")
    status: JobStatusSchema = Field(..., description="Current execution status")
    task_id: str = Field(..., description="Task type identifier")

    # Timestamps
    started_at: Optional[datetime] = Field(None, description="Execution start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Execution completion timestamp")
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated completion timestamp"
    )

    # Results and errors
    results: Optional[DockingResultsSchema] = Field(
        None, description="Execution results if completed"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retry attempts made")

    # Progress tracking
    progress_percentage: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Execution progress percentage"
    )
    current_step: Optional[str] = Field(None, description="Current execution step")

    # Metadata
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    user_id: Optional[str] = Field(None, description="User identifier")

    class Config:
        schema_extra = {
            "example": {
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "job_id": "gnina_12345",
                "status": "completed",
                "task_id": "gnina-molecular-docking",
                "started_at": "2025-09-24T10:00:00Z",
                "completed_at": "2025-09-24T10:15:00Z",
                "estimated_completion": "2025-09-24T10:30:00Z",
                "results": {
                    "poses": [{"rank": 1, "affinity": -8.2, "confidence_score": 0.85}],
                    "best_pose": {"rank": 1, "affinity": -8.2, "confidence_score": 0.85},
                },
                "retry_count": 0,
                "progress_percentage": 100.0,
                "current_step": "completed",
            }
        }


class TaskExecutionStatusResponse(BaseModel):
    """Response schema for execution status queries."""

    execution_id: UUID = Field(..., description="Unique execution identifier")
    status: JobStatusSchema = Field(..., description="Current execution status")
    progress_percentage: Optional[float] = Field(None, description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current step description")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: Dict[str, Any] = Field(..., description="Error information")

    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid binding site coordinates",
                    "details": {
                        "field": "binding_site.center_x",
                        "value": 2000.0,
                        "constraint": "must be between -1000 and 1000",
                    },
                }
            }
        }
