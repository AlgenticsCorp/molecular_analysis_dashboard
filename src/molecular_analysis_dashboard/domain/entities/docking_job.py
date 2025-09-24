"""Docking job domain entities for molecular analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class JobStatus(Enum):
    """Job execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class DockingEngine(Enum):
    """Supported docking engines."""

    GNINA = "gnina"
    VINA = "vina"
    SMINA = "smina"


@dataclass
class DockingPose:
    """Individual docking pose result."""

    rank: int
    affinity: float  # Binding affinity in kcal/mol
    rmsd_lb: Optional[float] = None  # RMSD lower bound
    rmsd_ub: Optional[float] = None  # RMSD upper bound
    confidence_score: Optional[float] = None
    pose_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DockingResults:
    """Complete docking analysis results."""

    poses: List[DockingPose]
    best_pose: Optional[DockingPose] = None
    execution_time: Optional[float] = None
    engine_version: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set best pose after initialization."""
        if self.poses and not self.best_pose:
            self.best_pose = min(self.poses, key=lambda p: p.affinity)

    def get_top_poses(self, n: int = 5) -> List[DockingPose]:
        """Get top N poses by binding affinity."""
        return sorted(self.poses, key=lambda p: p.affinity)[:n]


@dataclass
class MolecularStructure:
    """Molecular structure data container."""

    name: str
    format: str  # pdb, sdf, mol2, pdbqt, etc.
    data: str  # File content or URI
    properties: Dict[str, Any] = field(default_factory=dict)

    def is_file_path(self) -> bool:
        """Check if data represents a file path."""
        return not self.data.startswith(("HEADER", "MOLECULE", "@<TRIPOS>"))


@dataclass
class GninaDockingJob:
    """GNINA-specific docking job entity."""

    job_id: UUID
    org_id: UUID
    task_definition_id: str
    receptor: MolecularStructure
    ligand: Optional[MolecularStructure]
    status: JobStatus
    submitted_by: UUID
    created_at: datetime
    job_note: Optional[str] = None
    neurosnap_job_id: Optional[str] = None  # External provider job ID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[DockingResults] = None
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    execution_metadata: Dict[str, Any] = field(default_factory=dict)

    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == JobStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if job completed successfully."""
        return self.status == JobStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.status == JobStatus.FAILED

    def get_execution_time(self) -> Optional[float]:
        """Get job execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def get_best_affinity(self) -> Optional[float]:
        """Get best binding affinity score."""
        if self.results and self.results.best_pose:
            return self.results.best_pose.affinity
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": str(self.job_id),
            "org_id": str(self.org_id),
            "task_definition_id": self.task_definition_id,
            "receptor": {
                "name": self.receptor.name,
                "format": self.receptor.format,
                "properties": self.receptor.properties,
            },
            "ligand": (
                {
                    "name": self.ligand.name if self.ligand else None,
                    "format": self.ligand.format if self.ligand else None,
                    "properties": self.ligand.properties if self.ligand else {},
                }
                if self.ligand
                else None
            ),
            "status": self.status.value,
            "job_note": self.job_note,
            "neurosnap_job_id": self.neurosnap_job_id,
            "submitted_by": str(self.submitted_by),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time": self.get_execution_time(),
            "best_affinity": self.get_best_affinity(),
            "error_message": self.error_message,
            "results_summary": {
                "pose_count": len(self.results.poses) if self.results else 0,
                "best_affinity": self.get_best_affinity(),
                "top_poses": (
                    [
                        {"rank": p.rank, "affinity": p.affinity, "confidence": p.confidence_score}
                        for p in self.results.get_top_poses(3)
                    ]
                    if self.results
                    else []
                ),
            },
        }
