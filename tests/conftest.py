"""Pytest configuration and shared fixtures.

This module provides common fixtures and configuration for all tests,
following pytest best practices and the developer guide standards.
"""

import pytest
from fastapi.testclient import TestClient

from molecular_analysis_dashboard.presentation.api.main import app
from molecular_analysis_dashboard.presentation.api.schemas.tasks import (
    TaskTemplate,
    TaskParameter,
    TaskCategory,
    TaskComplexity,
    ResourceRequirement,
)


@pytest.fixture(scope="session")
def test_client():
    """FastAPI test client for API testing.

    Provides a test client that can be used across all test modules
    for making HTTP requests to the API endpoints.
    """
    return TestClient(app)


@pytest.fixture
def sample_task_parameter():
    """Sample TaskParameter for testing.

    Returns:
        TaskParameter: A sample parameter with typical molecular docking values.
    """
    return TaskParameter(
        name="center_x",
        type="number",
        required=False,
        default=0.0,
        description="X coordinate for binding site center",
        options=None
    )


@pytest.fixture
def sample_task_template():
    """Sample TaskTemplate for testing.

    Returns:
        TaskTemplate: A complete task template with all required fields.
    """
    return TaskTemplate(
        id="test-molecular-docking",
        name="Test Molecular Docking",
        description="A test molecular docking task for unit tests",
        category=TaskCategory.AUTODOCK_VINA,
        version="1.0.0",
        complexity=TaskComplexity.INTERMEDIATE,
        estimatedRuntime="30 minutes",
        cpuRequirement=ResourceRequirement.MEDIUM,
        memoryRequirement=ResourceRequirement.MEDIUM,
        requiredFiles=["ligand.pdb", "receptor.pdb"],
        parameters=[],
        compatibility=["linux", "macos"],
        tags=["molecular-docking", "test"],
        documentation="Test documentation for molecular docking",
        examples=["example1.py", "example2.py"],
        isBuiltIn=True
    )


@pytest.fixture
def sample_task_definition_dict():
    """Sample task definition as dictionary for transformation testing.

    Returns:
        dict: Task definition in dictionary format as would come from database.
    """
    return {
        "id": "test-task-dict",
        "name": "Test Task from Dictionary",
        "description": "A test task definition in dictionary format",
        "category": "Molecular Docking",
        "version": "1.0.0",
        "config": {
            "type": "basic",
            "engine": "vina",
            "timeout": 3600,
            "api_specification": {
                "openapi": "3.0.0",
                "info": {
                    "title": "Test Task API",
                    "version": "1.0.0"
                },
                "paths": {
                    "/execute": {
                        "post": {
                            "summary": "Execute test task",
                            "requestBody": {
                                "content": {
                                    "multipart/form-data": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "input_file": {
                                                    "type": "string",
                                                    "format": "binary"
                                                },
                                                "test_param": {
                                                    "type": "string",
                                                    "default": "test_value",
                                                    "description": "Test parameter"
                                                }
                                            },
                                            "required": ["input_file"]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def mock_database_task_definition():
    """Mock database TaskDefinition object for testing.

    Returns:
        Mock object with attributes matching database TaskDefinition model.
    """
    class MockTaskDefinition:
        def __init__(self):
            self.task_id = "mock-db-task"
            self.version = "2.0.0"
            self.org_id = "test-org-123"
            self.is_active = True
            self.task_metadata = {
                "name": "Mock Database Task",
                "description": "A mock task from database",
                "category": "custom",
                "complexity": "advanced",
                "estimatedRuntime": "60 minutes",
                "cpuRequirement": "high",
                "memoryRequirement": "high",
                "requiredFiles": ["config.json"],
                "compatibility": ["linux"],
                "tags": ["mock", "database", "test"],
                "documentation": "Mock documentation",
                "examples": ["mock_example.py"],
                "isBuiltIn": False
            }
            self.interface_spec = {
                "parameters": [
                    {
                        "name": "mock_param",
                        "type": "integer",
                        "required": True,
                        "default": 42,
                        "description": "Mock parameter for testing",
                        "options": [1, 2, 3, 42]
                    }
                ]
            }
            self.service_config = {
                "engine": "mock_engine",
                "timeout": 7200,
                "additional_config": "test_value"
            }

    return MockTaskDefinition()


@pytest.fixture
def api_specification_sample():
    """Sample OpenAPI specification for testing.

    Returns:
        dict: Complete OpenAPI 3.0 specification.
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
            "description": "Sample API for testing"
        },
        "paths": {
            "/execute": {
                "post": {
                    "summary": "Execute task",
                    "requestBody": {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "input_file": {"type": "string", "format": "binary"},
                                        "param1": {"type": "string", "default": "value1"},
                                        "param2": {"type": "number", "default": 1.0}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/status/{job_id}": {
                "get": {
                    "summary": "Get job status",
                    "parameters": [
                        {
                            "name": "job_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def service_configuration_sample():
    """Sample service configuration for testing.

    Returns:
        dict: Service deployment configuration.
    """
    return {
        "engine": "sample_engine",
        "timeout": 1800,
        "max_retries": 3,
        "resource_limits": {
            "cpu": "2",
            "memory": "4Gi"
        },
        "environment": {
            "SAMPLE_ENV": "test_value"
        }
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and options."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Custom pytest collection rules
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Mark tests as slow if they use certain fixtures or have 'slow' in name
        if "slow" in item.name or any(fixture in item.fixturenames for fixture in ["test_client"]):
            item.add_marker(pytest.mark.slow)
