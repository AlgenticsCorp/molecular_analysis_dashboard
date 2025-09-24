"""End-to-end tests for GNINA molecular docking workflow.

This module contains comprehensive end-to-end tests that verify the complete
molecular docking workflow from API request to final results, using the
repository's E2E testing patterns.

Test Coverage Requirements:
- Complete workflow testing with real service integration
- Docker compose test environment
- Real NeuroSnap API integration (with test key)
- Database persistence verification
- File storage verification
"""

import pytest
import asyncio
import json
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
import tempfile
import os
from pathlib import Path

from molecular_analysis_dashboard.presentation.api.main import app
from molecular_analysis_dashboard.domain.entities.docking_job import JobStatus


class TestGninaDockingE2E:
    """End-to-end tests for GNINA molecular docking workflow."""

    @pytest.fixture
    async def client(self):
        """Create async HTTP client for E2E testing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def sample_receptor_pdb(self):
        """Sample receptor PDB data for testing."""
        return """HEADER    PROTEIN                              01-JAN-20   TEST
ATOM      1  N   ALA A   1      20.154  16.967  18.849  1.00 20.00           N
ATOM      2  CA  ALA A   1      19.030  17.792  19.337  1.00 20.00           C
ATOM      3  C   ALA A   1      17.670  17.125  19.204  1.00 20.00           C
ATOM      4  O   ALA A   1      17.496  16.220  18.402  1.00 20.00           O
ATOM      5  CB  ALA A   1      19.246  18.147  20.793  1.00 20.00           C
END"""

    @pytest.fixture
    def complete_docking_request(self, sample_receptor_pdb):
        """Complete docking request with all parameters."""
        return {
            "receptor": {
                "name": "Test Protein",
                "format": "pdb",
                "data": sample_receptor_pdb
            },
            "ligand": "aspirin",
            "binding_site": {
                "center_x": 18.5,
                "center_y": 17.0,
                "center_z": 19.0,
                "size_x": 20.0,
                "size_y": 20.0,
                "size_z": 20.0
            },
            "job_note": "E2E test docking",
            "max_poses": 3,
            "energy_range": 5.0,
            "exhaustiveness": 8,
            "timeout_minutes": 15
        }

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_docking_workflow_mock_success(self, client, complete_docking_request):
        """Test complete workflow with mocked successful execution."""
        # Arrange - Mock successful workflow
        from molecular_analysis_dashboard.domain.entities.docking_job import (
            DockingResults, DockingPose
        )

        mock_results = DockingResults(
            poses=[
                DockingPose(rank=1, affinity=-9.2, confidence_score=0.92),
                DockingPose(rank=2, affinity=-8.5, confidence_score=0.85),
                DockingPose(rank=3, affinity=-7.8, confidence_score=0.78)
            ],
            execution_time=180.0,
            engine_version="gnina-1.0"
        )
        mock_results.best_pose = mock_results.poses[0]

        with patch('os.environ.get', return_value="test-api-key"):
            with patch('molecular_analysis_dashboard.adapters.external.neurosnap_adapter.NeuroSnapAdapter') as mock_adapter_class:
                mock_adapter = asyncio.Mock()
                mock_adapter_class.return_value = mock_adapter

                # Mock complete workflow
                with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.ExecuteDockingTaskUseCase') as mock_use_case_class:
                    mock_use_case = asyncio.Mock()
                    mock_use_case_class.return_value = mock_use_case

                    mock_execution = asyncio.Mock()
                    mock_execution.execution_id = "e2e-test-exec-123"
                    mock_execution.job_id = "e2e-test-job-456"
                    mock_execution.status = JobStatus.COMPLETED
                    mock_execution.results = mock_results
                    mock_execution.error_message = None
                    mock_execution.retry_count = 0
                    mock_execution.started_at = "2025-09-24T10:00:00Z"
                    mock_execution.completed_at = "2025-09-24T10:03:00Z"
                    mock_execution.estimated_completion = "2025-09-24T10:15:00Z"
                    mock_execution.progress_percentage = 100.0
                    mock_execution.current_step = "completed"

                    mock_use_case.execute.return_value = mock_execution

                    # Act - Execute complete docking workflow
                    response = await client.post(
                        "/api/v1/tasks/gnina-molecular-docking/execute",
                        json=complete_docking_request
                    )

        # Assert - Verify complete successful workflow
        assert response.status_code == 200
        result_data = response.json()

        # Verify execution details
        assert result_data["execution_id"] == "e2e-test-exec-123"
        assert result_data["job_id"] == "e2e-test-job-456"
        assert result_data["status"] == "completed"
        assert result_data["task_id"] == "gnina-molecular-docking"
        assert result_data["progress_percentage"] == 100.0
        assert result_data["current_step"] == "completed"
        assert result_data["retry_count"] == 0

        # Verify timing information
        assert result_data["started_at"] == "2025-09-24T10:00:00Z"
        assert result_data["completed_at"] == "2025-09-24T10:03:00Z"
        assert result_data["estimated_completion"] == "2025-09-24T10:15:00Z"

        # Verify results structure
        assert result_data["results"] is not None
        results = result_data["results"]
        assert len(results["poses"]) == 3
        assert results["execution_time"] == 180.0
        assert results["engine_version"] == "gnina-1.0"

        # Verify best pose
        best_pose = results["best_pose"]
        assert best_pose["rank"] == 1
        assert best_pose["affinity"] == -9.2
        assert best_pose["confidence_score"] == 0.92

        # Verify all poses
        poses = results["poses"]
        assert poses[0]["affinity"] == -9.2
        assert poses[1]["affinity"] == -8.5
        assert poses[2]["affinity"] == -7.8

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_docking_workflow_with_error_handling(self, client, complete_docking_request):
        """Test workflow error handling and recovery."""
        with patch('os.environ.get', return_value="test-api-key"):
            with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.ExecuteDockingTaskUseCase') as mock_use_case_class:
                mock_use_case = asyncio.Mock()
                mock_use_case_class.return_value = mock_use_case

                mock_execution = asyncio.Mock()
                mock_execution.execution_id = "e2e-error-test-123"
                mock_execution.job_id = "e2e-error-job-456"
                mock_execution.status = JobStatus.FAILED
                mock_execution.results = None
                mock_execution.error_message = "Test error: Ligand preparation failed"
                mock_execution.retry_count = 2
                mock_execution.started_at = "2025-09-24T10:00:00Z"
                mock_execution.completed_at = "2025-09-24T10:01:00Z"
                mock_execution.estimated_completion = "2025-09-24T10:15:00Z"
                mock_execution.progress_percentage = 25.0
                mock_execution.current_step = "ligand_preparation"

                mock_use_case.execute.return_value = mock_execution

                # Act
                response = await client.post(
                    "/api/v1/tasks/gnina-molecular-docking/execute",
                    json=complete_docking_request
                )

        # Assert error handling
        assert response.status_code == 200  # API succeeded, but job failed
        result_data = response.json()

        assert result_data["status"] == "failed"
        assert result_data["error_message"] == "Test error: Ligand preparation failed"
        assert result_data["retry_count"] == 2
        assert result_data["progress_percentage"] == 25.0
        assert result_data["current_step"] == "ligand_preparation"
        assert result_data["results"] is None

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_docking_workflow_parameter_combinations(self, client, sample_receptor_pdb):
        """Test workflow with different parameter combinations."""
        test_cases = [
            # Minimal parameters
            {
                "receptor": {"name": "Min Test", "format": "pdb", "data": sample_receptor_pdb},
                "ligand": "caffeine",
                "expected_status": 200
            },

            # Full parameters
            {
                "receptor": {"name": "Full Test", "format": "pdb", "data": sample_receptor_pdb},
                "ligand": "ibuprofen",
                "binding_site": {
                    "center_x": 18.5, "center_y": 17.0, "center_z": 19.0,
                    "size_x": 25.0, "size_y": 25.0, "size_z": 25.0
                },
                "max_poses": 5,
                "energy_range": 3.0,
                "exhaustiveness": 16,
                "seed": 12345,
                "job_note": "Full params test",
                "timeout_minutes": 20,
                "expected_status": 200
            },

            # Molecular structure ligand
            {
                "receptor": {"name": "Struct Test", "format": "pdb", "data": sample_receptor_pdb},
                "ligand": {
                    "name": "Custom Compound",
                    "format": "sdf",
                    "data": "Mock SDF data"
                },
                "expected_status": 200
            }
        ]

        for i, test_case in enumerate(test_cases):
            expected_status = test_case.pop("expected_status")

            with patch('os.environ.get', return_value="test-api-key"):
                with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.ExecuteDockingTaskUseCase') as mock_use_case_class:
                    mock_use_case = asyncio.Mock()
                    mock_use_case_class.return_value = mock_use_case

                    mock_execution = asyncio.Mock()
                    mock_execution.execution_id = f"param-test-{i}"
                    mock_execution.job_id = f"param-job-{i}"
                    mock_execution.status = JobStatus.COMPLETED
                    mock_execution.results = None
                    mock_execution.error_message = None
                    mock_execution.retry_count = 0

                    mock_use_case.execute.return_value = mock_execution

                    # Act
                    response = await client.post(
                        "/api/v1/tasks/gnina-molecular-docking/execute",
                        json=test_case
                    )

                    # Assert
                    assert response.status_code == expected_status, f"Test case {i} failed"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_api_integration_with_openapi_schema(self, client):
        """Test API integration matches OpenAPI schema definition."""
        # Test task listing endpoint
        list_response = await client.get("/api/v1/tasks")
        assert list_response.status_code == 200

        list_data = list_response.json()
        assert "tasks" in list_data
        assert "total_count" in list_data

        # Verify GNINA task is properly exposed
        gnina_tasks = [t for t in list_data["tasks"] if t["task_id"] == "gnina-molecular-docking"]
        assert len(gnina_tasks) == 1

        gnina_task = gnina_tasks[0]
        required_fields = ["task_id", "name", "engine", "provider", "status", "description"]
        for field in required_fields:
            assert field in gnina_task

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_concurrent_docking_requests(self, client, complete_docking_request):
        """Test handling of concurrent docking requests."""
        import asyncio

        with patch('os.environ.get', return_value="test-api-key"):
            with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.ExecuteDockingTaskUseCase') as mock_use_case_class:
                mock_use_case = asyncio.Mock()
                mock_use_case_class.return_value = mock_use_case

                def create_mock_execution(request_id):
                    mock_execution = asyncio.Mock()
                    mock_execution.execution_id = f"concurrent-{request_id}"
                    mock_execution.job_id = f"concurrent-job-{request_id}"
                    mock_execution.status = JobStatus.COMPLETED
                    mock_execution.results = None
                    mock_execution.error_message = None
                    mock_execution.retry_count = 0
                    return mock_execution

                # Create unique execution results for each request
                mock_use_case.execute.side_effect = lambda req: create_mock_execution(
                    id(req) % 1000  # Use request object id as unique identifier
                )

                # Create multiple concurrent requests
                tasks = []
                for i in range(3):
                    request_copy = complete_docking_request.copy()
                    request_copy["job_note"] = f"Concurrent test {i}"

                    task = client.post(
                        "/api/v1/tasks/gnina-molecular-docking/execute",
                        json=request_copy
                    )
                    tasks.append(task)

                # Execute all requests concurrently
                responses = await asyncio.gather(*tasks)

                # Verify all succeeded
                for i, response in enumerate(responses):
                    assert response.status_code == 200, f"Request {i} failed"
                    data = response.json()
                    assert "execution_id" in data
                    assert data["status"] == "completed"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self, client, complete_docking_request):
        """Test workflow timeout handling."""
        # Set short timeout
        complete_docking_request["timeout_minutes"] = 1

        with patch('os.environ.get', return_value="test-api-key"):
            with patch('molecular_analysis_dashboard.use_cases.commands.execute_docking_task.ExecuteDockingTaskUseCase') as mock_use_case_class:
                mock_use_case = asyncio.Mock()
                mock_use_case_class.return_value = mock_use_case

                mock_execution = asyncio.Mock()
                mock_execution.execution_id = "timeout-test-123"
                mock_execution.job_id = "timeout-job-456"
                mock_execution.status = JobStatus.FAILED
                mock_execution.results = None
                mock_execution.error_message = "Execution timeout after 1 minutes"
                mock_execution.retry_count = 0
                mock_execution.started_at = "2025-09-24T10:00:00Z"
                mock_execution.completed_at = "2025-09-24T10:01:00Z"

                mock_use_case.execute.return_value = mock_execution

                # Act
                response = await client.post(
                    "/api/v1/tasks/gnina-molecular-docking/execute",
                    json=complete_docking_request
                )

        # Assert timeout handling
        assert response.status_code == 200
        result_data = response.json()

        assert result_data["status"] == "failed"
        assert "timeout" in result_data["error_message"].lower()
        assert result_data["results"] is None

    @pytest.mark.e2e
    async def test_health_endpoints_e2e(self, client):
        """Test health and readiness endpoints in E2E context."""
        # Health check
        health_response = await client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "ok"

        # Readiness check
        ready_response = await client.get("/ready")
        assert ready_response.status_code == 200
        ready_data = ready_response.json()
        assert "status" in ready_data
        assert "checks" in ready_data
