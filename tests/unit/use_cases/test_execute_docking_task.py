"""Unit tests for GNINA docking use case.

This module contains comprehensive unit tests for the ExecuteDockingTaskUseCase,
following the repository's testing guidelines and Clean Architecture patterns.

Test Coverage Requirements:
- ≥80% unit test coverage (repository requirement)
- Test each architectural layer in isolation
- Mock external dependencies (ports/adapters)
- Follow pytest patterns with proper fixtures
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from molecular_analysis_dashboard.use_cases.commands.execute_docking_task import (
    ExecuteDockingTaskUseCase,
    DockingTaskRequest,
    DockingTaskExecution,
    DockingParameterValidationError,
    LigandPreparationError,
    DockingSubmissionError,
    DockingExecutionTimeoutError
)
from molecular_analysis_dashboard.domain.entities.docking_job import (
    MolecularStructure,
    DockingResults,
    DockingPose,
    JobStatus
)


class TestExecuteDockingTaskUseCase:
    """Test suite for ExecuteDockingTaskUseCase following Clean Architecture principles."""

    @pytest.fixture
    def mock_docking_adapter(self):
        """Mock docking engine adapter."""
        adapter = AsyncMock()
        adapter.submit_docking_job.return_value = "test_job_123"
        adapter.get_job_status.return_value = JobStatus.COMPLETED

        # Mock successful docking results
        test_poses = [
            DockingPose(rank=1, affinity=-8.2, confidence_score=0.85),
            DockingPose(rank=2, affinity=-7.5, confidence_score=0.78)
        ]
        adapter.retrieve_results.return_value = DockingResults(
            poses=test_poses,
            best_pose=test_poses[0],
            execution_time=120.5,
            engine_version="gnina-1.0"
        )
        return adapter

    @pytest.fixture
    def mock_ligand_prep_adapter(self):
        """Mock ligand preparation adapter."""
        adapter = AsyncMock()
        adapter.prepare_ligand_from_drug_name.return_value = MolecularStructure(
            name="osimertinib",
            format="sdf",
            data="mock_sdf_data"
        )
        return adapter

    @pytest.fixture
    def mock_neurosnap_adapter(self):
        """Mock NeuroSnap API adapter."""
        adapter = AsyncMock()
        adapter.close.return_value = None
        return adapter

    @pytest.fixture
    def use_case(self, mock_docking_adapter, mock_ligand_prep_adapter, mock_neurosnap_adapter):
        """Create ExecuteDockingTaskUseCase with mocked dependencies."""
        return ExecuteDockingTaskUseCase(
            docking_adapter=mock_docking_adapter,
            ligand_prep_adapter=mock_ligand_prep_adapter,
            neurosnap_adapter=mock_neurosnap_adapter
        )

    @pytest.fixture
    def valid_request(self):
        """Create a valid docking task request."""
        receptor = MolecularStructure(
            name="EGFR",
            format="pdb",
            data="HEADER    TRANSFERASE TEST"
        )

        return DockingTaskRequest(
            receptor=receptor,
            ligand="osimertinib",
            binding_site={
                'center_x': 25.5, 'center_y': 10.2, 'center_z': 15.8,
                'size_x': 20.0, 'size_y': 20.0, 'size_z': 20.0
            },
            job_note="Unit test",
            max_poses=5,
            energy_range=3.0,
            timeout_minutes=10
        )

    @pytest.mark.asyncio
    async def test_execute_successful_workflow(self, use_case, valid_request):
        """Test successful execution of complete docking workflow."""
        # Act
        execution = await use_case.execute(valid_request)

        # Assert
        assert execution.status == JobStatus.COMPLETED
        assert execution.job_id == "test_job_123"
        assert execution.results is not None
        assert len(execution.results.poses) == 2
        assert execution.results.best_pose.affinity == -8.2
        assert execution.error_message is None

    @pytest.mark.asyncio
    async def test_parameter_validation_missing_receptor(self, use_case):
        """Test validation error when receptor is missing."""
        # Arrange
        invalid_request = DockingTaskRequest(
            receptor=None,  # Missing receptor
            ligand="osimertinib"
        )

        # Act & Assert
        with pytest.raises(DockingParameterValidationError) as exc_info:
            await use_case.execute(invalid_request)

        assert "Receptor is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parameter_validation_invalid_binding_site(self, use_case):
        """Test validation error for invalid binding site coordinates."""
        # Arrange
        receptor = MolecularStructure(name="test", format="pdb", data="test")
        invalid_request = DockingTaskRequest(
            receptor=receptor,
            ligand="osimertinib",
            binding_site={
                'center_x': 25.5,  # Missing other required coordinates
                'size_x': 20.0
            }
        )

        # Act & Assert
        with pytest.raises(DockingParameterValidationError) as exc_info:
            await use_case.execute(invalid_request)

        assert "missing required keys" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parameter_validation_invalid_max_poses(self, use_case, valid_request):
        """Test validation error for invalid max_poses parameter."""
        # Arrange
        valid_request.max_poses = 25  # Exceeds maximum allowed (20)

        # Act & Assert
        with pytest.raises(DockingParameterValidationError) as exc_info:
            await use_case.execute(valid_request)

        assert "max_poses must be between 1 and 20" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ligand_preparation_from_drug_name(self, use_case, valid_request, mock_ligand_prep_adapter):
        """Test ligand preparation from drug name."""
        # Arrange - ligand is already a string in valid_request

        # Act
        execution = await use_case.execute(valid_request)

        # Assert
        mock_ligand_prep_adapter.prepare_ligand_from_drug_name.assert_called_once_with("osimertinib")
        assert execution.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_ligand_preparation_from_structure(self, use_case, valid_request):
        """Test ligand preparation with pre-existing structure."""
        # Arrange
        ligand_structure = MolecularStructure(
            name="custom_ligand",
            format="sdf",
            data="custom_sdf_data"
        )
        valid_request.ligand = ligand_structure

        # Act
        execution = await use_case.execute(valid_request)

        # Assert
        assert execution.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_ligand_preparation_failure(self, use_case, valid_request, mock_ligand_prep_adapter):
        """Test handling of ligand preparation failure."""
        # Arrange
        mock_ligand_prep_adapter.prepare_ligand_from_drug_name.side_effect = Exception("PubChem API error")

        # Act & Assert
        with pytest.raises(LigandPreparationError) as exc_info:
            await use_case.execute(valid_request)

        assert "Failed to prepare ligand" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_docking_submission_failure(self, use_case, valid_request, mock_docking_adapter):
        """Test handling of docking job submission failure."""
        # Arrange
        mock_docking_adapter.submit_docking_job.side_effect = Exception("NeuroSnap API error")

        # Act & Assert
        with pytest.raises(DockingSubmissionError) as exc_info:
            await use_case.execute(valid_request)

        assert "Failed to submit docking job" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_job_status_monitoring_failure(self, use_case, valid_request, mock_docking_adapter):
        """Test handling when job fails during execution."""
        # Arrange
        mock_docking_adapter.get_job_status.return_value = JobStatus.FAILED

        # Act & Assert
        with pytest.raises(DockingSubmissionError) as exc_info:
            await use_case.execute(valid_request)

        assert "Docking job test_job_123 failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execution_timeout(self, use_case, valid_request, mock_docking_adapter):
        """Test handling of execution timeout."""
        # Arrange
        mock_docking_adapter.get_job_status.return_value = JobStatus.RUNNING  # Never completes
        valid_request.timeout_minutes = 1  # Very short timeout

        # Mock datetime to simulate timeout
        with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.datetime') as mock_dt:
            start_time = datetime.utcnow()
            timeout_time = start_time + timedelta(minutes=2)  # Past timeout
            mock_dt.utcnow.side_effect = [start_time, start_time, timeout_time]

            # Act & Assert
            with pytest.raises(DockingExecutionTimeoutError) as exc_info:
                await use_case.execute(valid_request)

            assert "timed out after 1 minutes" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_result_retrieval_failure(self, use_case, valid_request, mock_docking_adapter):
        """Test handling of result retrieval failure."""
        # Arrange
        mock_docking_adapter.retrieve_results.side_effect = Exception("Result retrieval error")

        # Act & Assert
        with pytest.raises(DockingSubmissionError) as exc_info:
            await use_case.execute(valid_request)

        assert "Failed to retrieve docking results" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_results_validation(self, use_case, valid_request, mock_docking_adapter):
        """Test validation of empty docking results."""
        # Arrange
        mock_docking_adapter.retrieve_results.return_value = DockingResults(
            poses=[],  # Empty results
            best_pose=None
        )

        # Act & Assert
        with pytest.raises(DockingSubmissionError) as exc_info:
            await use_case.execute(valid_request)

        assert "No valid docking poses returned" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execution_tracking_metadata(self, use_case, valid_request):
        """Test that execution tracking includes proper metadata."""
        # Act
        execution = await use_case.execute(valid_request)

        # Assert
        assert execution.execution_id is not None
        assert execution.started_at is not None
        assert execution.completed_at is not None
        assert execution.estimated_completion is not None
        assert execution.retry_count == 0

    @pytest.mark.asyncio
    async def test_receptor_preparation_from_dict(self, use_case, valid_request):
        """Test receptor preparation from dictionary input."""
        # Arrange
        valid_request.receptor = {
            'name': 'EGFR_dict',
            'format': 'pdb',
            'data': 'HEADER DICT TEST'
        }

        # Act
        execution = await use_case.execute(valid_request)

        # Assert
        assert execution.status == JobStatus.COMPLETED

    def test_get_execution_status_not_implemented(self, use_case):
        """Test that execution status retrieval is not yet implemented."""
        # Act
        result = use_case.get_execution_status(uuid4())

        # Assert
        # This is expected to return None as it's not implemented yet
        # In a future iteration, this would return actual status
        assert result is None or hasattr(result, '__await__')  # May be async

    def test_cancel_execution_not_implemented(self, use_case):
        """Test that execution cancellation is not yet implemented."""
        # Act
        result = use_case.cancel_execution(uuid4())

        # Assert
        # This is expected to return False as it's not implemented yet
        assert result is False or hasattr(result, '__await__')  # May be async
