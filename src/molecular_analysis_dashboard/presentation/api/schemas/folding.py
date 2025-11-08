"""Pydantic schemas for structure folding API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ....domain.entities.docking_job import JobStatus


class FoldingJobStatus(str, Enum):
    """Folding job status enumeration for API responses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class SequenceType(str, Enum):
    """Sequence type enumeration."""

    PROTEIN = "aa"
    DNA = "dna"
    RNA = "rna"


class MSAMode(str, Enum):
    """MSA mode enumeration."""

    MMSEQS2_UNIREF_ENV = "mmseqs2_uniref_env"
    CUSTOM = "custom"


class SequenceInput(BaseModel):
    """Individual sequence input for folding."""

    name: str = Field(..., description="Sequence name/identifier")
    sequence: str = Field(..., description="Amino acid, DNA, or RNA sequence")
    type: SequenceType = Field(..., description="Sequence type")

    class Config:
        schema_extra = {
            "example": {"name": "prot1", "sequence": "LCLYTHIGRNIYYGSYLYSETWN", "type": "aa"}
        }


class MoleculeInput(BaseModel):
    """Individual molecule input for folding."""

    data: str = Field(..., description="Molecule data (SDF format or SMILES string)")
    type: str = Field(..., description="Molecule format (sdf or smiles)")

    class Config:
        schema_extra = {"example": {"data": "C=C=C", "type": "smiles"}}


class FoldingJobRequest(BaseModel):
    """Request schema for structure folding job submission."""

    job_name: str = Field(default="AlphaFold3 Folding", description="Human-readable job name")
    sequences: List[SequenceInput] = Field(..., description="Input sequences for folding")
    molecules: Optional[List[MoleculeInput]] = Field(default=None, description="Optional molecules")
    residue_modifications: Optional[str] = Field(
        default=None, description="Residue modifications (e.g., protein_1:102:MLY)"
    )
    msa_mode: MSAMode = Field(default=MSAMode.MMSEQS2_UNIREF_ENV, description="MSA mode")
    number_recycles: int = Field(
        default=6, description="Number of recycling iterations", ge=1, le=20
    )
    sampling_steps: int = Field(default=200, description="Number of sampling steps", ge=1, le=1000)
    diffusion_samples: int = Field(
        default=5, description="Number of diffusion samples", ge=1, le=50
    )
    note: str = Field(default="Structure prediction analysis", description="Additional notes")

    class Config:
        schema_extra = {
            "example": {
                "job_name": "Multi-domain Protein Folding",
                "sequences": [
                    {"name": "prot1", "sequence": "LCLYTHIGRNIYYGSYLYSETWN", "type": "aa"},
                    {"name": "dna1", "sequence": "CGTGCTGGCGACTAAGTC", "type": "dna"},
                ],
                "molecules": [{"data": "C=C=C", "type": "smiles"}],
                "residue_modifications": "protein_1:102:MLY",
                "msa_mode": "mmseqs2_uniref_env",
                "number_recycles": 6,
                "sampling_steps": 200,
                "diffusion_samples": 5,
                "note": "Complex protein-DNA-ligand structure prediction",
            }
        }


class FoldingJobResponse(BaseModel):
    """Response from folding job submission."""

    job_id: str = Field(..., description="NeuroSnap job ID")
    status: FoldingJobStatus = Field(..., description="Initial job status")
    message: str = Field(..., description="Submission status message")
    job_name: str = Field(..., description="User-provided job name")
    sequences_count: int = Field(..., description="Number of input sequences")
    molecules_count: int = Field(default=0, description="Number of input molecules")
    estimated_runtime: str = Field(..., description="Estimated completion time")
    submitted_at: Optional[datetime] = Field(default=None, description="Submission timestamp")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "af3_68d8615c545d2bb25a34dc95",
                "status": "pending",
                "message": "Structure folding job submitted to NeuroSnap successfully",
                "job_name": "Multi-domain Protein Folding",
                "sequences_count": 2,
                "molecules_count": 1,
                "estimated_runtime": "30-60 minutes",
                "submitted_at": "2025-11-08T10:30:00Z",
            }
        }


class FoldingStatusResponse(BaseModel):
    """Response for folding job status queries."""

    job_id: str = Field(..., description="NeuroSnap job ID")
    status: FoldingJobStatus = Field(..., description="Current job status")
    progress_percentage: Optional[float] = Field(
        None, description="Job progress (0-100)", ge=0, le=100
    )
    estimated_time_remaining: Optional[str] = Field(
        None, description="Estimated time to completion"
    )
    status_message: Optional[str] = Field(None, description="Detailed status message")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last status update timestamp")
    current_step: Optional[str] = Field(None, description="Current processing step")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "af3_68d8615c545d2bb25a34dc95",
                "status": "running",
                "progress_percentage": 65.0,
                "estimated_time_remaining": "15-25 minutes",
                "status_message": "Processing protein structure prediction...",
                "current_step": "Diffusion sampling",
                "started_at": "2025-11-08T10:32:15Z",
                "updated_at": "2025-11-08T10:45:30Z",
            }
        }


class StructurePrediction(BaseModel):
    """Individual structure prediction result."""

    model_rank: int = Field(..., description="Model ranking (1 = best)")
    confidence_score: float = Field(..., description="Overall confidence score", ge=0, le=1)
    plddt_score: Optional[float] = Field(None, description="pLDDT confidence score", ge=0, le=100)
    pae_score: Optional[float] = Field(None, description="Predicted Aligned Error score")
    structure_pdb: Optional[str] = Field(None, description="PDB format structure")
    chain_count: Optional[int] = Field(None, description="Number of chains in structure")
    residue_count: Optional[int] = Field(None, description="Total number of residues")

    class Config:
        schema_extra = {
            "example": {
                "model_rank": 1,
                "confidence_score": 0.87,
                "plddt_score": 78.5,
                "pae_score": 3.2,
                "chain_count": 2,
                "residue_count": 245,
            }
        }


class FoldingResultsResponse(BaseModel):
    """Complete folding results for a completed job."""

    job_id: str = Field(..., description="NeuroSnap job ID")
    status: FoldingJobStatus = Field(..., description="Final job status")
    predictions: List[StructurePrediction] = Field(
        ..., description="All structure predictions ranked by confidence"
    )
    best_prediction: Optional[StructurePrediction] = Field(
        None, description="Best confidence prediction"
    )
    execution_time: Optional[float] = Field(None, description="Total execution time in seconds")
    engine_version: Optional[str] = Field(None, description="AlphaFold3 engine version used")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Folding parameters used")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    download_urls: Optional[Dict[str, str]] = Field(
        None, description="URLs for downloading result files"
    )
    quality_metrics: Optional[Dict[str, float]] = Field(
        None, description="Structure quality metrics"
    )

    class Config:
        schema_extra = {
            "example": {
                "job_id": "af3_68d8615c545d2bb25a34dc95",
                "status": "completed",
                "predictions": [
                    {
                        "model_rank": 1,
                        "confidence_score": 0.87,
                        "plddt_score": 78.5,
                        "pae_score": 3.2,
                        "chain_count": 2,
                        "residue_count": 245,
                    },
                    {
                        "model_rank": 2,
                        "confidence_score": 0.82,
                        "plddt_score": 75.1,
                        "pae_score": 4.1,
                        "chain_count": 2,
                        "residue_count": 245,
                    },
                ],
                "best_prediction": {
                    "model_rank": 1,
                    "confidence_score": 0.87,
                    "plddt_score": 78.5,
                    "pae_score": 3.2,
                    "chain_count": 2,
                    "residue_count": 245,
                },
                "execution_time": 2347.5,
                "engine_version": "AlphaFold3 v1.0",
                "completed_at": "2025-11-08T11:32:45Z",
                "download_urls": {
                    "structure_pdb": "https://neurosnap.ai/download/...",
                    "confidence_json": "https://neurosnap.ai/download/...",
                    "log_file": "https://neurosnap.ai/download/...",
                },
                "quality_metrics": {
                    "average_plddt": 78.5,
                    "average_pae": 3.2,
                    "structure_completeness": 0.95,
                },
            }
        }


class FoldingJobSummary(BaseModel):
    """Summary information for a folding job."""

    job_id: str = Field(..., description="NeuroSnap job ID")
    job_name: str = Field(..., description="User-provided job name")
    status: FoldingJobStatus = Field(..., description="Current job status")
    sequences_count: int = Field(..., description="Number of input sequences")
    molecules_count: int = Field(default=0, description="Number of input molecules")
    submitted_at: datetime = Field(..., description="Job submission timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    best_confidence: Optional[float] = Field(None, description="Best confidence score if completed")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "af3_68d8615c545d2bb25a34dc95",
                "job_name": "Multi-domain Protein Folding",
                "status": "completed",
                "sequences_count": 2,
                "molecules_count": 1,
                "submitted_at": "2025-11-08T10:30:00Z",
                "completed_at": "2025-11-08T11:32:45Z",
                "best_confidence": 0.87,
            }
        }


class FoldingJobListResponse(BaseModel):
    """Response for listing user's folding jobs."""

    jobs: List[FoldingJobSummary] = Field(..., description="List of user's folding jobs")
    total_count: int = Field(..., description="Total number of jobs")
    page: int = Field(default=1, description="Current page number", ge=1)
    page_size: int = Field(default=20, description="Number of jobs per page", ge=1, le=100)
    filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters")

    class Config:
        schema_extra = {
            "example": {
                "jobs": [
                    {
                        "job_id": "af3_68d8615c545d2bb25a34dc95",
                        "job_name": "Multi-domain Protein Folding",
                        "status": "completed",
                        "sequences_count": 2,
                        "molecules_count": 1,
                        "submitted_at": "2025-11-08T10:30:00Z",
                        "completed_at": "2025-11-08T11:32:45Z",
                        "best_confidence": 0.87,
                    }
                ],
                "total_count": 1,
                "page": 1,
                "page_size": 20,
                "filters": {"status": "completed"},
            }
        }


class FoldingErrorResponse(BaseModel):
    """Standard error response format for folding endpoints."""

    error: Dict[str, Any] = Field(..., description="Error details")

    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "FOLDING_JOB_NOT_FOUND",
                    "message": "Folding job 'invalid-id' not found or not accessible",
                    "details": {"job_id": "invalid-id", "timestamp": "2025-11-08T12:00:00Z"},
                }
            }
        }
