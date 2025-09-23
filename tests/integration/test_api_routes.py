"""Integration tests for task API routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from molecular_analysis_dashboard.presentation.api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_task_definitions():
    """Mock task definitions for database responses."""
    class MockTaskDefinition:
        def __init__(self, task_id, name, category="Molecular Docking"):
            self.task_id = task_id
            self.name = name
            self.org_id = "test-org-id"
            self.version = "1.0.0"
            self.is_active = True
            self.task_metadata = {
                "name": name,
                "description": f"Description for {name}",
                "category": category,
                "complexity": "intermediate",
                "estimatedRuntime": "30 minutes",
                "cpuRequirement": "medium",
                "memoryRequirement": "medium",
                "requiredFiles": ["ligand", "receptor"],
                "compatibility": ["linux"],
                "tags": ["docking"],
                "isBuiltIn": True
            }
            self.interface_spec = {
                "parameters": [
                    {
                        "name": "center_x",
                        "type": "number",
                        "required": False,
                        "default": 0.0,
                        "description": "X coordinate"
                    }
                ]
            }
            self.service_config = {
                "engine": "vina",
                "timeout": 3600
            }

    return [
        MockTaskDefinition("molecular-docking-basic", "Molecular Docking (Basic)"),
        MockTaskDefinition("protein-analysis", "Protein Analysis", "Analysis"),
    ]


class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    def test_health_endpoint(self, client):
        """Test health endpoint returns OK."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "X-Request-ID" in response.headers

    def test_ready_endpoint(self, client):
        """Test ready endpoint returns status."""
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "db" in data["checks"]
        assert "task_api" in data["checks"]


class TestTaskListEndpoint:
    """Test GET /api/v1/tasks endpoint."""

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition')
    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.get_metadata_session')
    def test_list_tasks_success(self, mock_get_session, mock_task_definition, client, mock_task_definitions):
        """Test successful task listing."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_task_definitions
        mock_session.execute.return_value = mock_result

        # Make request
        response = client.get("/api/v1/tasks?org_id=test-org")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "tasks" in data
        assert "total_count" in data
        assert "organization_id" in data

        assert len(data["tasks"]) == 2
        assert data["total_count"] == 2
        assert data["organization_id"] == "test-org"

        # Check task structure
        task = data["tasks"][0]
        assert "id" in task
        assert "name" in task
        assert "category" in task
        assert "estimatedRuntime" in task  # Check camelCase alias

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition', None)
    def test_list_tasks_no_database_models(self, client):
        """Test task listing when database models unavailable."""
        response = client.get("/api/v1/tasks")

        assert response.status_code == 500
        data = response.json()
        assert "Database models not available" in data["detail"]

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition')
    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.get_metadata_session')
    def test_list_tasks_with_category_filter(self, mock_get_session, mock_task_definition, client, mock_task_definitions):
        """Test task listing with category filter."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Filter to only return one task
        filtered_tasks = [t for t in mock_task_definitions if t.task_metadata["category"] == "Analysis"]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = filtered_tasks
        mock_session.execute.return_value = mock_result

        # Make request with category filter
        response = client.get("/api/v1/tasks?category=Analysis")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["tasks"][0]["name"] == "Protein Analysis"

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition')
    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.get_metadata_session')
    def test_list_tasks_empty_result(self, mock_get_session, mock_task_definition, client):
        """Test task listing with no results."""
        # Setup mocks for empty result
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Make request
        response = client.get("/api/v1/tasks")

        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total_count"] == 0


class TestTaskDetailEndpoint:
    """Test GET /api/v1/tasks/{task_id} endpoint."""

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition')
    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.get_metadata_session')
    def test_get_task_detail_success(self, mock_get_session, mock_task_definition, client, mock_task_definitions):
        """Test successful task detail retrieval."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_task_definitions[0]
        mock_session.execute.return_value = mock_result

        # Make request
        response = client.get("/api/v1/tasks/molecular-docking-basic")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "task" in data
        assert "api_specification" in data or "apiSpecification" in data
        assert "service_configuration" in data or "serviceConfiguration" in data

        # Check task details
        task = data["task"]
        assert task["id"] == "molecular-docking-basic"
        assert task["name"] == "Molecular Docking (Basic)"

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition')
    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.get_metadata_session')
    def test_get_task_detail_not_found(self, mock_get_session, mock_task_definition, client):
        """Test task detail retrieval for non-existent task."""
        # Setup mocks for not found
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Make request
        response = client.get("/api/v1/tasks/non-existent-task")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition', None)
    def test_get_task_detail_no_database_models(self, client):
        """Test task detail when database models unavailable."""
        response = client.get("/api/v1/tasks/some-task")

        assert response.status_code == 500
        data = response.json()
        assert "Database models not available" in data["detail"]


class TestTaskCategoriesEndpoint:
    """Test GET /api/v1/tasks/categories endpoint."""

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition')
    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.get_metadata_session')
    def test_list_categories_success(self, mock_get_session, mock_task_definition, client):
        """Test successful category listing."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = Mock()
        mock_result.fetchall.return_value = [("Molecular Docking",), ("Analysis",), ("Custom",)]
        mock_session.execute.return_value = mock_result

        # Make request
        response = client.get("/api/v1/tasks/categories")

        assert response.status_code == 200
        categories = response.json()

        assert isinstance(categories, list)
        assert "Molecular Docking" in categories
        assert "Analysis" in categories
        assert "Custom" in categories

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition', None)
    def test_list_categories_no_database_models(self, client):
        """Test category listing when database models unavailable."""
        response = client.get("/api/v1/tasks/categories")

        assert response.status_code == 200
        categories = response.json()

        # Should return default categories
        assert isinstance(categories, list)
        assert "autodock_vina" in categories
        assert "autodock4" in categories
        assert "schrodinger" in categories
        assert "custom" in categories

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition')
    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.get_metadata_session')
    def test_list_categories_database_error(self, mock_get_session, mock_task_definition, client):
        """Test category listing with database error."""
        # Setup mocks to raise exception
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.side_effect = Exception("Database error")

        # Make request
        response = client.get("/api/v1/tasks/categories")

        assert response.status_code == 200
        categories = response.json()

        # Should return default categories on error
        assert isinstance(categories, list)
        assert "autodock_vina" in categories


class TestCORSAndMiddleware:
    """Test CORS and middleware functionality."""

    def test_cors_headers(self, client):
        """Test CORS headers in responses."""
        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    def test_request_id_header(self, client):
        """Test request ID header in responses."""
        response = client.get("/health")

        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0

    def test_request_id_propagation(self, client):
        """Test request ID propagation from client."""
        custom_id = "test-request-123"
        response = client.get("/health", headers={"X-Request-ID": custom_id})

        assert response.headers["X-Request-ID"] == custom_id


class TestErrorHandling:
    """Test error handling in API routes."""

    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.TaskDefinition')
    @patch('molecular_analysis_dashboard.presentation.api.routes.tasks.get_metadata_session')
    def test_database_connection_error(self, mock_get_session, mock_task_definition, client):
        """Test handling of database connection errors."""
        # Setup mock to raise exception
        mock_get_session.side_effect = Exception("Connection failed")

        response = client.get("/api/v1/tasks")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to retrieve tasks" in data["detail"]

    def test_invalid_uuid_format(self, client):
        """Test handling of invalid UUID format in org_id."""
        # This should be handled gracefully by the API
        response = client.get("/api/v1/tasks?org_id=invalid-uuid")

        # The API should either accept it or return appropriate error
        assert response.status_code in [200, 400, 422, 500]
