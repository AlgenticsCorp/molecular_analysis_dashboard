"""Unit tests for task transformation services."""

import pytest

from molecular_analysis_dashboard.presentation.api.services.task_transformer import (
    transform_task_definition_to_template,
    transform_task_definitions_to_templates,
    extract_api_specification,
    extract_service_configuration,
)
from molecular_analysis_dashboard.presentation.api.schemas.tasks import (
    TaskTemplate,
    TaskCategory,
    TaskComplexity,
    ResourceRequirement,
)


@pytest.fixture
def sample_task_definition_dict():
    """Sample task definition as dictionary for testing."""
    return {
        "id": "molecular-docking-basic",
        "name": "Molecular Docking (Basic)",
        "description": "Perform molecular docking using AutoDock Vina",
        "category": "Molecular Docking",
        "version": "1.0.0",
        "config": {
            "type": "basic",
            "engine": "vina",
            "timeout": 3600,
            "api_specification": {
                "openapi": "3.0.0",
                "info": {
                    "title": "Molecular Docking Basic API",
                    "version": "1.0.0"
                },
                "paths": {
                    "/execute": {
                        "post": {
                            "summary": "Execute molecular docking",
                            "requestBody": {
                                "content": {
                                    "multipart/form-data": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "ligand_file": {
                                                    "type": "string",
                                                    "format": "binary"
                                                },
                                                "receptor_file": {
                                                    "type": "string",
                                                    "format": "binary"
                                                },
                                                "center_x": {
                                                    "type": "number",
                                                    "default": 0.0,
                                                    "description": "X coordinate"
                                                },
                                                "center_y": {
                                                    "type": "number",
                                                    "default": 0.0
                                                },
                                                "exhaustiveness": {
                                                    "type": "integer",
                                                    "default": 8
                                                }
                                            },
                                            "required": ["ligand_file", "receptor_file"]
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
    """Mock database TaskDefinition object for testing."""
    class MockTaskDefinition:
        def __init__(self):
            self.task_id = "test-task-db"
            self.version = "2.0.0"
            self.task_metadata = {
                "name": "Test Task from DB",
                "description": "A test task from database",
                "category": "custom",
                "complexity": "intermediate",
                "estimatedRuntime": "45 minutes",
                "cpuRequirement": "medium",
                "memoryRequirement": "medium",
                "requiredFiles": ["input"],
                "compatibility": ["linux"],
                "tags": ["test"],
                "isBuiltIn": False
            }
            self.interface_spec = {
                "parameters": [
                    {
                        "name": "test_param",
                        "type": "string",
                        "required": True,
                        "default": "test_value",
                        "description": "Test parameter"
                    }
                ]
            }
            self.service_config = {
                "engine": "test_engine",
                "timeout": 1800
            }

    return MockTaskDefinition()


class TestTransformTaskDefinition:
    """Test task definition transformation."""

    def test_transform_dict_to_template(self, sample_task_definition_dict):
        """Test transforming dictionary task definition to template."""
        template = transform_task_definition_to_template(sample_task_definition_dict)

        assert isinstance(template, TaskTemplate)
        assert template.id == "molecular-docking-basic"
        assert template.name == "Molecular Docking (Basic)"
        assert template.description == "Perform molecular docking using AutoDock Vina"
        assert template.category == TaskCategory.AUTODOCK_VINA
        assert template.version == "1.0.0"

        # Check default values for dict mode
        assert template.complexity == TaskComplexity.INTERMEDIATE
        assert template.cpu_requirement == ResourceRequirement.MEDIUM
        assert template.is_built_in is True

    def test_transform_dict_parameter_extraction(self, sample_task_definition_dict):
        """Test parameter extraction from OpenAPI specification."""
        template = transform_task_definition_to_template(sample_task_definition_dict)

        # Should extract non-binary parameters
        param_names = [p.name for p in template.parameters]
        assert "center_x" in param_names
        assert "center_y" in param_names
        assert "exhaustiveness" in param_names

        # Should skip binary file parameters
        assert "ligand_file" not in param_names
        assert "receptor_file" not in param_names

        # Check parameter details
        center_x_param = next(p for p in template.parameters if p.name == "center_x")
        assert center_x_param.type == "number"
        assert center_x_param.default == 0.0
        assert center_x_param.description == "X coordinate"
        assert center_x_param.required is False

    def test_transform_database_object_to_template(self, mock_database_task_definition):
        """Test transforming database object to template."""
        template = transform_task_definition_to_template(mock_database_task_definition)

        assert isinstance(template, TaskTemplate)
        assert template.id == "test-task-db"
        assert template.name == "Test Task from DB"
        assert template.version == "2.0.0"
        assert template.complexity == TaskComplexity.INTERMEDIATE
        assert template.cpu_requirement == ResourceRequirement.MEDIUM
        assert template.is_built_in is False

        # Check parameters from interface spec
        assert len(template.parameters) == 1
        param = template.parameters[0]
        assert param.name == "test_param"
        assert param.type == "string"
        assert param.required is True

    def test_transform_multiple_definitions(self, sample_task_definition_dict, mock_database_task_definition):
        """Test transforming list of task definitions."""
        definitions = [sample_task_definition_dict, mock_database_task_definition]
        templates = transform_task_definitions_to_templates(definitions)

        assert len(templates) == 2
        assert all(isinstance(t, TaskTemplate) for t in templates)
        assert templates[0].id == "molecular-docking-basic"
        assert templates[1].id == "test-task-db"


class TestExtractApiSpecification:
    """Test API specification extraction."""

    def test_extract_from_dict(self, sample_task_definition_dict):
        """Test extracting API spec from dictionary."""
        api_spec = extract_api_specification(sample_task_definition_dict)

        assert api_spec["openapi"] == "3.0.0"
        assert "paths" in api_spec
        assert "/execute" in api_spec["paths"]
        assert api_spec["info"]["title"] == "Molecular Docking Basic API"

    def test_extract_from_database_object(self, mock_database_task_definition):
        """Test extracting API spec from database object."""
        api_spec = extract_api_specification(mock_database_task_definition)

        # Mock object has interface_spec with parameters
        assert "parameters" in api_spec
        assert len(api_spec["parameters"]) == 1

    def test_extract_empty_spec(self):
        """Test extracting from object with no API spec."""
        empty_dict = {"config": {}}
        api_spec = extract_api_specification(empty_dict)
        assert api_spec == {}

        class EmptyObject:
            interface_spec = {}

        empty_obj = EmptyObject()
        api_spec = extract_api_specification(empty_obj)
        assert api_spec == {}


class TestExtractServiceConfiguration:
    """Test service configuration extraction."""

    def test_extract_from_dict(self, sample_task_definition_dict):
        """Test extracting service config from dictionary."""
        service_config = extract_service_configuration(sample_task_definition_dict)

        assert service_config["engine"] == "vina"
        assert service_config["timeout"] == 3600
        assert service_config["type"] == "basic"

    def test_extract_from_database_object(self, mock_database_task_definition):
        """Test extracting service config from database object."""
        service_config = extract_service_configuration(mock_database_task_definition)

        assert service_config["engine"] == "test_engine"
        assert service_config["timeout"] == 1800

    def test_extract_default_config(self):
        """Test extracting from object with minimal config."""
        minimal_dict = {"config": {"engine": "custom"}}
        service_config = extract_service_configuration(minimal_dict)

        assert service_config["engine"] == "custom"
        assert service_config["timeout"] == 3600  # default
        assert service_config["type"] == "basic"  # default


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_task_definition_dict(self):
        """Test with empty dictionary."""
        empty_dict = {}
        template = transform_task_definition_to_template(empty_dict)

        assert template.id == ""
        assert template.name == ""
        assert template.category == TaskCategory.AUTODOCK_VINA
        assert len(template.parameters) == 0

    def test_malformed_api_specification(self):
        """Test with malformed API specification."""
        malformed_dict = {
            "id": "test",
            "config": {
                "api_specification": {
                    "paths": {
                        "/execute": {
                            "post": {
                                "requestBody": {
                                    "content": {
                                        # Missing multipart/form-data
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        template = transform_task_definition_to_template(malformed_dict)
        assert len(template.parameters) == 0  # No parameters extracted

    def test_object_without_required_attributes(self):
        """Test with object missing required attributes."""
        class MinimalObject:
            pass

        minimal_obj = MinimalObject()
        template = transform_task_definition_to_template(minimal_obj)

        # Should handle gracefully with getattr defaults
        assert template.id == ""
        assert template.version == "1.0.0"
        assert len(template.parameters) == 0
