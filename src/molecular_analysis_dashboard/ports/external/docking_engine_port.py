"""Abstract port for molecular docking engines."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...domain.entities.docking_job import (
    DockingResults,
    GninaDockingJob,
    JobStatus,
    MolecularStructure,
)


class DockingEnginePort(ABC):
    """Abstract interface for molecular docking engines.

    This port defines the contract for interacting with molecular docking
    engines (GNINA, Vina, Smina) either locally or via external APIs.
    """

    @abstractmethod
    async def submit_docking_job(
        self,
        receptor: MolecularStructure,
        ligand: Optional[MolecularStructure] = None,
        job_note: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submit a molecular docking job.

        Args:
            receptor: Protein/receptor structure data
            ligand: Ligand structure data (optional for some workflows)
            job_note: Human-readable job description
            parameters: Engine-specific docking parameters

        Returns:
            External job ID for tracking

        Raises:
            DockingSubmissionError: If job submission fails
        """
        pass

    @abstractmethod
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get the current status of a docking job.

        Args:
            job_id: Job ID from the docking engine

        Returns:
            Current job status

        Raises:
            DockingStatusError: If status check fails
        """
        pass

    @abstractmethod
    async def retrieve_results(self, job_id: str) -> DockingResults:
        """Retrieve completed docking results.

        Args:
            job_id: Job ID from the docking engine

        Returns:
            Complete docking analysis results

        Raises:
            DockingResultsError: If result retrieval fails
            JobNotCompleteError: If job hasn't finished yet
        """
        pass

    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running docking job.

        Args:
            job_id: Job ID from the docking engine

        Returns:
            True if cancellation was successful

        Raises:
            DockingCancellationError: If cancellation fails
        """
        pass

    @abstractmethod
    async def list_available_services(self) -> List[Dict[str, Any]]:
        """List available docking services and their capabilities.

        Returns:
            List of available services with metadata

        Raises:
            ServiceDiscoveryError: If service listing fails
        """
        pass

    @abstractmethod
    async def validate_input_structure(self, structure: MolecularStructure) -> bool:
        """Validate molecular structure for compatibility.

        Args:
            structure: Molecular structure to validate

        Returns:
            True if structure is valid for this engine

        Raises:
            StructureValidationError: If validation fails
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported molecular formats.

        Returns:
            Dict mapping structure types to supported formats
            e.g., {'receptor': ['pdb'], 'ligand': ['sdf', 'mol2']}
        """
        pass

    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default docking parameters for this engine.

        Returns:
            Default parameter configuration
        """
        pass
