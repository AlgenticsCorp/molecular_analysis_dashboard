"""Execute docking task use case for molecular analysis dashboard.

This module implements the core business logic for executing molecular docking tasks
using the GNINA docking engine via NeuroSnap API. It orchestrates the complete workflow
from input validation through result retrieval while maintaining clean architecture principles.

Responsibilities:
- Validate task parameters against task definition schema
- Prepare ligands when needed (drug names, SMILES, etc.)
- Submit docking jobs to NeuroSnap via GNINA adapter
- Monitor job execution status with proper retry logic
- Retrieve and validate docking results
- Handle errors and provide meaningful feedback

Dependencies:
- Domain entities: GninaDockingJob, MolecularStructure, DockingResults
- Ports: DockingEnginePort, MolecularPreparationPort, NeuroSnapApiPort
- Use case base classes and validation utilities

Architecture:
- Clean Architecture Use Case layer
- Depends on abstract ports, not concrete adapters
- Pure business logic with no framework dependencies
- Comprehensive error handling and logging
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from ...domain.entities.docking_job import (
    DockingEngine,
    DockingResults,
    GninaDockingJob,
    JobStatus,
    MolecularStructure,
)
from ...ports.external.docking_engine_port import DockingEnginePort
from ...ports.external.molecular_prep_port import MolecularPreparationPort
from ...ports.external.neurosnap_api_port import NeuroSnapApiPort

logger = logging.getLogger(__name__)


@dataclass
class DockingTaskRequest:
    """Request parameters for docking task execution."""

    # Required inputs
    receptor: Union[MolecularStructure, Dict[str, Any]]
    ligand: Union[MolecularStructure, Dict[str, Any], str]  # Can be structure or drug name

    # Optional parameters
    binding_site: Optional[Dict[str, float]] = (
        None  # center_x, center_y, center_z, size_x, size_y, size_z
    )
    job_note: Optional[str] = None
    max_poses: int = 9
    energy_range: float = 3.0
    exhaustiveness: int = 8

    # Execution control
    timeout_minutes: int = 30
    retry_attempts: int = 3

    # Metadata
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    task_metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Initialize default values after dataclass creation."""
        if self.task_metadata is None:
            self.task_metadata = {}


@dataclass
class DockingTaskExecution:
    """Execution tracking information for docking task."""

    execution_id: UUID
    job_id: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[DockingResults] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    estimated_completion: Optional[datetime] = None


class DockingTaskExecutionError(Exception):
    """Base exception for docking task execution errors."""

    def __init__(
        self, message: str, execution_id: Optional[UUID] = None, job_id: Optional[str] = None
    ):
        super().__init__(message)
        self.execution_id = execution_id
        self.job_id = job_id


class DockingParameterValidationError(DockingTaskExecutionError):
    """Exception raised when task parameters are invalid."""

    pass


class LigandPreparationError(DockingTaskExecutionError):
    """Exception raised when ligand preparation fails."""

    pass


class DockingSubmissionError(DockingTaskExecutionError):
    """Exception raised when job submission fails."""

    pass


class DockingExecutionTimeoutError(DockingTaskExecutionError):
    """Exception raised when docking execution times out."""

    pass


class ExecuteDockingTaskUseCase:
    """Use case for executing molecular docking tasks via GNINA/NeuroSnap.

    This use case orchestrates the complete molecular docking workflow:
    1. Validate input parameters
    2. Prepare ligand if needed (drug name -> structure)
    3. Submit docking job to NeuroSnap
    4. Monitor execution with status polling
    5. Retrieve and validate results
    6. Handle errors with proper retry logic

    Attributes:
        docking_adapter: Adapter for GNINA docking engine operations
        ligand_prep_adapter: Adapter for ligand preparation operations
        neurosnap_adapter: Adapter for NeuroSnap API operations
    """

    def __init__(
        self,
        docking_adapter: DockingEnginePort,
        ligand_prep_adapter: MolecularPreparationPort,
        neurosnap_adapter: NeuroSnapApiPort,
    ):
        """Initialize use case with required adapters.

        Args:
            docking_adapter: Port for docking engine operations
            ligand_prep_adapter: Port for molecular preparation operations
            neurosnap_adapter: Port for NeuroSnap API operations
        """
        self.docking_adapter = docking_adapter
        self.ligand_prep_adapter = ligand_prep_adapter
        self.neurosnap_adapter = neurosnap_adapter

    async def execute(self, request: DockingTaskRequest) -> DockingTaskExecution:
        """Execute complete molecular docking workflow.

        Orchestrates the full docking pipeline from parameter validation through
        result retrieval. Handles errors gracefully and provides comprehensive
        execution tracking.

        Args:
            request: Docking task parameters and configuration

        Returns:
            DockingTaskExecution: Execution tracking with results or error info

        Raises:
            DockingTaskExecutionError: For various execution failures
        """
        execution = DockingTaskExecution(
            execution_id=uuid4(),
            started_at=datetime.utcnow(),
            estimated_completion=datetime.utcnow() + timedelta(minutes=request.timeout_minutes),
        )

        logger.info(f"Starting docking task execution {execution.execution_id}")

        try:
            # Step 1: Validate parameters
            await self._validate_parameters(request, execution)

            # Step 2: Prepare ligand if needed
            ligand_structure = await self._prepare_ligand(request, execution)

            # Step 3: Prepare receptor
            receptor_structure = await self._prepare_receptor(request, execution)

            # Step 4: Submit docking job
            await self._submit_docking_job(request, execution, receptor_structure, ligand_structure)

            # Step 5: Monitor execution
            await self._monitor_execution(request, execution)

            # Step 6: Retrieve results
            await self._retrieve_results(execution)

            execution.status = JobStatus.COMPLETED
            execution.completed_at = datetime.utcnow()

            logger.info(f"Docking task {execution.execution_id} completed successfully")
            return execution

        except Exception as e:
            execution.status = JobStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error_message = str(e)

            logger.error(f"Docking task {execution.execution_id} failed: {e}")
            raise

    async def _validate_parameters(
        self, request: DockingTaskRequest, execution: DockingTaskExecution
    ) -> None:
        """Validate docking task parameters.

        Args:
            request: Task request to validate
            execution: Execution context for error tracking

        Raises:
            DockingParameterValidationError: If parameters are invalid
        """
        logger.debug(f"Validating parameters for execution {execution.execution_id}")

        # Validate receptor
        if not request.receptor:
            raise DockingParameterValidationError("Receptor is required", execution.execution_id)

        # Validate ligand
        if not request.ligand:
            raise DockingParameterValidationError("Ligand is required", execution.execution_id)

        # Validate binding site if provided
        if request.binding_site:
            required_keys = ["center_x", "center_y", "center_z", "size_x", "size_y", "size_z"]
            missing_keys = [key for key in required_keys if key not in request.binding_site]
            if missing_keys:
                raise DockingParameterValidationError(
                    f"Binding site missing required keys: {missing_keys}", execution.execution_id
                )

        # Validate numeric parameters
        if request.max_poses < 1 or request.max_poses > 20:
            raise DockingParameterValidationError(
                "max_poses must be between 1 and 20", execution.execution_id
            )

        if request.energy_range < 0.5 or request.energy_range > 10.0:
            raise DockingParameterValidationError(
                "energy_range must be between 0.5 and 10.0", execution.execution_id
            )

    async def _prepare_ligand(
        self, request: DockingTaskRequest, execution: DockingTaskExecution
    ) -> MolecularStructure:
        """Prepare ligand structure for docking.

        Args:
            request: Task request containing ligand information
            execution: Execution context for error tracking

        Returns:
            MolecularStructure: Prepared ligand ready for docking

        Raises:
            LigandPreparationError: If ligand preparation fails
        """
        logger.debug(f"Preparing ligand for execution {execution.execution_id}")

        try:
            # If ligand is already a MolecularStructure, return it
            if isinstance(request.ligand, MolecularStructure):
                return request.ligand

            # If ligand is a dictionary with structure data, convert it
            if isinstance(request.ligand, dict):
                if "data" in request.ligand and "format" in request.ligand:
                    return MolecularStructure(
                        data=request.ligand["data"],
                        format=request.ligand["format"],
                        name=request.ligand.get("name", "ligand"),
                    )

            # If ligand is a drug name string, prepare it via drug name lookup
            if isinstance(request.ligand, str):
                return await self.ligand_prep_adapter.prepare_ligand_from_drug_name(request.ligand)

            raise LigandPreparationError(
                f"Unsupported ligand type: {type(request.ligand)}", execution.execution_id
            )

        except Exception as e:
            raise LigandPreparationError(
                f"Failed to prepare ligand: {str(e)}", execution.execution_id
            ) from e

    async def _prepare_receptor(
        self, request: DockingTaskRequest, execution: DockingTaskExecution
    ) -> MolecularStructure:
        """Prepare receptor structure for docking.

        Args:
            request: Task request containing receptor information
            execution: Execution context for error tracking

        Returns:
            MolecularStructure: Prepared receptor ready for docking

        Raises:
            DockingParameterValidationError: If receptor preparation fails
        """
        logger.debug(f"Preparing receptor for execution {execution.execution_id}")

        try:
            # If receptor is already a MolecularStructure, return it
            if isinstance(request.receptor, MolecularStructure):
                return request.receptor

            # If receptor is a dictionary with structure data, convert it
            if isinstance(request.receptor, dict):
                if "data" in request.receptor and "format" in request.receptor:
                    return MolecularStructure(
                        data=request.receptor["data"],
                        format=request.receptor["format"],
                        name=request.receptor.get("name", "receptor"),
                    )

            raise DockingParameterValidationError(
                f"Unsupported receptor type: {type(request.receptor)}", execution.execution_id
            )

        except Exception as e:
            raise DockingParameterValidationError(
                f"Failed to prepare receptor: {str(e)}", execution.execution_id
            ) from e

    async def _submit_docking_job(
        self,
        request: DockingTaskRequest,
        execution: DockingTaskExecution,
        receptor: MolecularStructure,
        ligand: MolecularStructure,
    ) -> None:
        """Submit docking job to NeuroSnap.

        Args:
            request: Task request with docking parameters
            execution: Execution context for job tracking
            receptor: Prepared receptor structure
            ligand: Prepared ligand structure

        Raises:
            DockingSubmissionError: If job submission fails
        """
        logger.debug(f"Submitting docking job for execution {execution.execution_id}")

        try:
            # Create docking parameters dictionary
            docking_parameters = {
                "binding_site": request.binding_site,
                "max_poses": request.max_poses,
                "energy_range": request.energy_range,
                "exhaustiveness": request.exhaustiveness,
            }

            # Submit via docking engine adapter (passing structures and parameters separately)
            execution.job_id = await self.docking_adapter.submit_docking_job(
                receptor=receptor,
                ligand=ligand,
                job_note=request.job_note or f"Execution {execution.execution_id}",
                parameters=docking_parameters,
            )
            execution.status = JobStatus.RUNNING

            logger.info(
                f"Docking job {execution.job_id} submitted for execution {execution.execution_id}"
            )

        except Exception as e:
            raise DockingSubmissionError(
                f"Failed to submit docking job: {str(e)}", execution.execution_id
            ) from e

    async def _monitor_execution(
        self, request: DockingTaskRequest, execution: DockingTaskExecution
    ) -> None:
        """Monitor docking job execution with polling.

        Args:
            request: Task request with timeout configuration
            execution: Execution context with job ID

        Raises:
            DockingExecutionTimeoutError: If execution times out
        """
        logger.debug(f"Monitoring execution {execution.execution_id}, job {execution.job_id}")

        timeout_at = datetime.utcnow() + timedelta(minutes=request.timeout_minutes)
        poll_interval = 10  # seconds

        while datetime.utcnow() < timeout_at:
            try:
                if not execution.job_id:
                    raise DockingSubmissionError(
                        "No job ID available for status monitoring", execution.execution_id
                    )

                status = await self.docking_adapter.get_job_status(execution.job_id)

                if status == JobStatus.COMPLETED:
                    logger.info(f"Job {execution.job_id} completed successfully")
                    return

                elif status == JobStatus.FAILED:
                    raise DockingSubmissionError(
                        f"Docking job {execution.job_id} failed",
                        execution.execution_id,
                        execution.job_id,
                    )

                elif status == JobStatus.CANCELED:
                    raise DockingSubmissionError(
                        f"Docking job {execution.job_id} was canceled",
                        execution.execution_id,
                        execution.job_id,
                    )

                # Job still running, wait and poll again
                await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"Error polling job status: {e}")
                await asyncio.sleep(poll_interval)

        # Timeout reached
        raise DockingExecutionTimeoutError(
            f"Docking job {execution.job_id} timed out after {request.timeout_minutes} minutes",
            execution.execution_id,
            execution.job_id,
        )

    async def _retrieve_results(self, execution: DockingTaskExecution) -> None:
        """Retrieve and validate docking results.

        Args:
            execution: Execution context to store results

        Raises:
            DockingSubmissionError: If result retrieval fails
        """
        logger.debug(
            f"Retrieving results for execution {execution.execution_id}, job {execution.job_id}"
        )

        try:
            if not execution.job_id:
                raise DockingSubmissionError(
                    "No job ID available for result retrieval", execution.execution_id
                )

            execution.results = await self.docking_adapter.retrieve_results(execution.job_id)

            # Validate results
            if not execution.results or not execution.results.poses:
                raise DockingSubmissionError(
                    f"No valid docking poses returned for job {execution.job_id}",
                    execution.execution_id,
                    execution.job_id,
                )

            logger.info(
                f"Retrieved {len(execution.results.poses)} poses for execution {execution.execution_id}"
            )

        except Exception as e:
            raise DockingSubmissionError(
                f"Failed to retrieve docking results: {str(e)}",
                execution.execution_id,
                execution.job_id,
            ) from e

    async def get_execution_status(self, execution_id: UUID) -> Optional[DockingTaskExecution]:
        """Get current status of a docking execution.

        Args:
            execution_id: Unique execution identifier

        Returns:
            DockingTaskExecution: Current execution state or None if not found

        Note:
            In a full implementation, this would query a repository/database
            to retrieve persistent execution state. For now, returns None.
        """
        # TODO: Implement execution state persistence and retrieval
        logger.warning(f"Execution status retrieval not implemented for {execution_id}")
        return None

    async def cancel_execution(self, execution_id: UUID) -> bool:
        """Cancel a running docking execution.

        Args:
            execution_id: Unique execution identifier

        Returns:
            bool: True if cancellation successful, False otherwise

        Note:
            In a full implementation, this would cancel the NeuroSnap job
            and update execution state. For now, returns False.
        """
        # TODO: Implement execution cancellation
        logger.warning(f"Execution cancellation not implemented for {execution_id}")
        return False
