"""Integration tests for GNINA docking task execution API endpoints.

This module contains integration tests for the task execution API endpoints,
testing the complete integration between presentation, use cases, and adapters.

Test Coverage Requirements:
- ≥70% integration test coverage (repository requirement)
- Test complete request/response workflows
- Mock external APIs (NeuroSnap) but test real integrations
- Follow repository API testing patterns
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import json

from molecular_analysis_dashboard.presentation.api.main import app
from molecular_analysis_dashboard.domain.entities.docking_job import (
    MolecularStructure,
    DockingResults,
    DockingPose,
    JobStatus
)


class TestTaskExecutionAPI:
    """Integration tests for task execution API endpoints."""

    @pytest.fixture
    async def client(self):
        """Create async HTTP client for API testing."""
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def valid_execution_request(self):
        """Create valid task execution request payload."""
        return {
            "receptor": {
                "name": "EGFR Test",
                "format": "pdb",
                "data": "HEADER    TRANSFERASE TEST"
            },
            "ligand": "osimertinib",
            "binding_site": {
                "center_x": 25.5,
                "center_y": 10.2,
                "center_z": 15.8,
                "size_x": 20.0,
                "size_y": 20.0,
                "size_z": 20.0
            },
            "job_note": "Integration test",
            "max_poses": 5,
            "timeout_minutes": 10
        }

    @pytest.mark.asyncio
    async def test_list_available_tasks(self, client):
        """Test GET /api/v1/tasks endpoint returns available tasks."""
        # Act
        response = await client.get("/api/v1/tasks")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "tasks" in data
        assert "total_count" in data
        assert data["total_count"] >= 1

        # Check GNINA task is available
        gnina_tasks = [task for task in data["tasks"]
                      if task["task_id"] == "gnina-molecular-docking"]
        assert len(gnina_tasks) == 1

        gnina_task = gnina_tasks[0]
        assert gnina_task["name"] == "GNINA Molecular Docking"
        assert gnina_task["engine"] == "gnina"
        assert gnina_task["provider"] == "neurosnap"
        assert gnina_task["status"] == "available"

    @pytest.mark.asyncio
    async def test_execute_task_missing_api_key(self, client, valid_execution_request):
        """Test task execution fails gracefully when API key is missing."""
        # Arrange - Ensure no API key is set
        with patch.dict('os.environ', {}, clear=True):
            # Act
            response = await client.post(
                "/api/v1/tasks/gnina-molecular-docking/execute",
                json=valid_execution_request
            )

        # Assert
        assert response.status_code == 500
        error_data = response.json()

        assert "error" in error_data["detail"]
        assert error_data["detail"]["error"]["code"] == "CONFIGURATION_ERROR"
        assert "NeuroSnap API key not configured" in error_data["detail"]["error"]["message"]

    @pytest.mark.asyncio
    async def test_execute_task_invalid_task_id(self, client, valid_execution_request):
        """Test task execution with invalid task ID returns 404."""
        # Act
        response = await client.post(
            "/api/v1/tasks/invalid-task/execute",
            json=valid_execution_request
        )

        # Assert
        assert response.status_code == 404
        error_data = response.json()

        assert error_data["detail"]["error"]["code"] == "TASK_NOT_FOUND"
        assert "invalid-task" in error_data["detail"]["error"]["message"]
        assert "supported_tasks" in error_data["detail"]["error"]["details"]

    @pytest.mark.asyncio
    async def test_execute_task_invalid_binding_site(self, client, valid_execution_request):
        """Test task execution with invalid binding site parameters."""
        # Arrange
        valid_execution_request["binding_site"]["center_x"] = 2000.0  # Invalid coordinate

        # Act
        response = await client.post(
            "/api/v1/tasks/gnina-molecular-docking/execute",
            json=valid_execution_request
        )

        # Assert
        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_execute_task_successful_with_mocked_adapters(self, client, valid_execution_request):
        """Test successful task execution with mocked external dependencies."""
        # Arrange - Mock the adapters to avoid real API calls
        mock_results = DockingResults(
            poses=[
                DockingPose(rank=1, affinity=-8.2, confidence_score=0.85),
                DockingPose(rank=2, affinity=-7.5, confidence_score=0.78)
            ],
            execution_time=120.5,
            engine_version="gnina-1.0"
        )
        mock_results.best_pose = mock_results.poses[0]

        with patch('os.environ.get') as mock_env:
            mock_env.return_value = "test-api-key"

            with patch('molecular_analysis_dashboard.adapters.external.neurosnap_adapter.NeuroSnapAdapter') as mock_adapter_class:
                mock_adapter = AsyncMock()
                mock_adapter_class.return_value = mock_adapter

                # Mock the use case execution
                with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.ExecuteDockingTaskUseCase') as mock_use_case_class:
                    mock_use_case = AsyncMock()
                    mock_use_case_class.return_value = mock_use_case

                    mock_execution = AsyncMock()
                    mock_execution.execution_id = "test-exec-123"
                    mock_execution.job_id = "test-job-456"
                    mock_execution.status = JobStatus.COMPLETED
                    mock_execution.results = mock_results
                    mock_execution.error_message = None
                    mock_execution.retry_count = 0
                    mock_execution.started_at = "2025-09-24T10:00:00Z"
                    mock_execution.completed_at = "2025-09-24T10:02:00Z"
                    mock_execution.estimated_completion = "2025-09-24T10:10:00Z"

                    mock_use_case.execute.return_value = mock_execution

                    # Act
                    response = await client.post(
                        "/api/v1/tasks/gnina-molecular-docking/execute",
                        json=valid_execution_request
                    )

        # Assert
        assert response.status_code == 200
        result_data = response.json()

        assert result_data["execution_id"] == "test-exec-123"
        assert result_data["job_id"] == "test-job-456"
        assert result_data["status"] == "completed"
        assert result_data["task_id"] == "gnina-molecular-docking"
        assert result_data["progress_percentage"] == 100.0
        assert result_data["current_step"] == "completed"

        # Check results structure
        assert result_data["results"] is not None
        assert len(result_data["results"]["poses"]) == 2
        assert result_data["results"]["best_pose"]["affinity"] == -8.2
        assert result_data["results"]["execution_time"] == 120.5

    @pytest.mark.asyncio
    async def test_execute_task_with_drug_name_ligand(self, client):
        """Test task execution with drug name as ligand input."""
        # Arrange
        request_data = {
            "receptor": {
                "name": "EGFR",
                "format": "pdb",
                "data": "HEADER TEST"
            },
            "ligand": "aspirin",  # Drug name instead of structure
            "job_note": "Drug name test"
        }

        with patch('os.environ.get', return_value="test-key"):
            with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.ExecuteDockingTaskUseCase') as mock_use_case_class:
                mock_use_case = AsyncMock()
                mock_use_case_class.return_value = mock_use_case
                mock_use_case.execute.side_effect = Exception("Ligand preparation test")

                # Act
                response = await client.post(
                    "/api/v1/tasks/gnina-molecular-docking/execute",
                    json=request_data
                )

        # Assert
        assert response.status_code == 500
        # The request was properly formatted and reached the use case

    @pytest.mark.asyncio
    async def test_execute_task_with_molecular_structure_ligand(self, client):
        """Test task execution with molecular structure as ligand input."""
        # Arrange
        request_data = {
            "receptor": {
                "name": "EGFR",
                "format": "pdb",
                "data": "HEADER TEST"
            },
            "ligand": {
                "name": "Custom Ligand",
                "format": "sdf",
                "data": "mock sdf data"
            },
            "job_note": "Structure ligand test"
        }

        with patch('os.environ.get', return_value="test-key"):
            with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.ExecuteDockingTaskUseCase') as mock_use_case_class:
                mock_use_case = AsyncMock()
                mock_use_case_class.return_value = mock_use_case
                mock_use_case.execute.side_effect = Exception("Structure test")

                # Act
                response = await client.post(
                    "/api/v1/tasks/gnina-molecular-docking/execute",
                    json=request_data
                )

        # Assert
        assert response.status_code == 500
        # The request was properly formatted and reached the use case

    @pytest.mark.asyncio
    async def test_execute_task_parameter_validation(self, client):
        """Test comprehensive parameter validation."""
        test_cases = [
            # Missing receptor
            ({
                "ligand": "aspirin"
            }, 422),

            # Missing ligand
            ({
                "receptor": {"name": "test", "format": "pdb", "data": "test"}
            }, 422),

            # Invalid max_poses
            ({
                "receptor": {"name": "test", "format": "pdb", "data": "test"},
                "ligand": "aspirin",
                "max_poses": 25
            }, 422),

            # Invalid energy_range
            ({
                "receptor": {"name": "test", "format": "pdb", "data": "test"},
                "ligand": "aspirin",
                "energy_range": 15.0
            }, 422),
        ]

        for request_data, expected_status in test_cases:
            # Act
            response = await client.post(
                "/api/v1/tasks/gnina-molecular-docking/execute",
                json=request_data
            )

            # Assert
            assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_api_response_schema_compliance(self, client, valid_execution_request):
        """Test that API responses comply with OpenAPI schema."""
        with patch('os.environ.get', return_value="test-key"):
            with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.ExecuteDockingTaskUseCase') as mock_use_case_class:
                mock_use_case = AsyncMock()
                mock_use_case_class.return_value = mock_use_case

                mock_execution = AsyncMock()
                mock_execution.execution_id = "test-id"
                mock_execution.job_id = "job-123"
                mock_execution.status = JobStatus.COMPLETED
                mock_execution.results = None  # No results case
                mock_execution.error_message = None
                mock_execution.retry_count = 0

                mock_use_case.execute.return_value = mock_execution

                # Act
                response = await client.post(
                    "/api/v1/tasks/gnina-molecular-docking/execute",
                    json=valid_execution_request
                )

        # Assert response structure matches TaskExecutionResponse schema
        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "execution_id", "job_id", "status", "task_id",
            "retry_count", "progress_percentage", "current_step"
        ]

        for field in required_fields:
            assert field in data

    @pytest.mark.asyncio
    async def test_health_and_ready_endpoints(self, client):
        """Test basic health and readiness endpoints."""
        # Test health endpoint
        health_response = await client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "ok"

        # Test ready endpoint
        ready_response = await client.get("/ready")
        assert ready_response.status_code == 200
        ready_data = ready_response.json()
        assert "status" in ready_data
        assert "checks" in ready_data
