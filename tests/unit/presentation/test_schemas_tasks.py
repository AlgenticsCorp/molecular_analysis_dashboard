"""Unit tests for task API schemas."""

import pytest

from molecular_analysis_dashboard.presentation.api.schemas.tasks import (
    TaskTemplate,
    TaskParameter,
    TaskListResponse,
    TaskDetailResponse,
    TaskComplexity,
    TaskCategory,
    ResourceRequirement,
)


@pytest.fixture
def sample_task_parameter():
    """Sample TaskParameter for testing."""
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
    """Sample TaskTemplate for testing."""
    return TaskTemplate(
        id="test-task",
        name="Test Task",
        description="A test task",
        category=TaskCategory.AUTODOCK_VINA,
        version="1.0.0",
        complexity=TaskComplexity.INTERMEDIATE,
        estimatedRuntime="30 minutes",
        cpuRequirement=ResourceRequirement.MEDIUM,
        memoryRequirement=ResourceRequirement.MEDIUM,
        requiredFiles=["ligand", "receptor"],
        parameters=[],
        compatibility=["linux", "macos"],
        tags=["docking"],
        documentation=None,
        examples=None,
        isBuiltIn=True
    )


class TestTaskParameter:
    """Test TaskParameter schema validation."""

    def test_task_parameter_creation(self, sample_task_parameter):
        """Test creating a valid TaskParameter."""
        param = sample_task_parameter

        assert param.name == "center_x"
        assert param.type == "number"
        assert param.required is False
        assert param.default == 0.0
        assert param.description == "X coordinate for binding site center"
        assert param.options is None

    def test_task_parameter_required_fields(self):
        """Test TaskParameter with only required fields."""
        param = TaskParameter(
            name="test_param",
            type="string",
            required=True,
            default=None,
            description="Test parameter",
            options=None
        )

        assert param.name == "test_param"
        assert param.type == "string"
        assert param.required is True
        assert param.default is None
        assert param.options is None

    def test_task_parameter_with_options(self):
        """Test TaskParameter with select options."""
        param = TaskParameter(
            name="analysis_type",
            type="select",
            required=True,
            default=None,
            description="Type of analysis",
            options=["binding", "stability", "dynamics"]
        )

        assert param.options == ["binding", "stability", "dynamics"]


class TestTaskTemplate:
    """Test TaskTemplate schema validation and serialization."""

    def test_task_template_creation(self, sample_task_template):
        """Test creating a valid TaskTemplate."""
        template = sample_task_template

        assert template.id == "test-task"
        assert template.category == TaskCategory.AUTODOCK_VINA
        assert template.complexity == TaskComplexity.INTERMEDIATE
        assert template.cpu_requirement == ResourceRequirement.MEDIUM

    def test_task_template_field_aliases(self, sample_task_template):
        """Test TaskTemplate field aliases for camelCase conversion."""
        template = sample_task_template

        # Test serialization with aliases
        data = template.model_dump(by_alias=True)

        assert "estimatedRuntime" in data
        assert "cpuRequirement" in data
        assert "memoryRequirement" in data
        assert "requiredFiles" in data
        assert "isBuiltIn" in data

        # Verify alias values
        assert data["estimatedRuntime"] == "30 minutes"
        assert data["cpuRequirement"] == "medium"
        assert data["isBuiltIn"] is True

    def test_task_template_enum_validation(self):
        """Test TaskTemplate enum validation."""
        # Valid enums should work
        template = TaskTemplate(
            id="test-task",
            name="Test Task",
            description="A test task",
            category=TaskCategory.SCHRODINGER,
            version="1.0.0",
            complexity=TaskComplexity.ADVANCED,
            estimatedRuntime="2 hours",
            cpuRequirement=ResourceRequirement.HIGH,
            memoryRequirement=ResourceRequirement.HIGH,
            requiredFiles=[],
            parameters=[],
            compatibility=[],
            tags=[],
            documentation=None,
            examples=None,
            isBuiltIn=True
        )

        assert template.category == TaskCategory.SCHRODINGER
        assert template.complexity == TaskComplexity.ADVANCED
        assert template.cpu_requirement == ResourceRequirement.HIGH

    def test_task_template_with_parameters(self):
        """Test TaskTemplate with parameter list."""
        params = [
            TaskParameter(
                name="center_x",
                type="number",
                required=False,
                default=0.0,
                description="X coordinate",
                options=None
            ),
            TaskParameter(
                name="ligand_file",
                type="file",
                required=True,
                default=None,
                description="Ligand structure file",
                options=None
            )
        ]

        template = TaskTemplate(
            id="docking-task",
            name="Docking Task",
            description="Molecular docking task",
            category=TaskCategory.AUTODOCK_VINA,
            version="1.0.0",
            complexity=TaskComplexity.INTERMEDIATE,
            estimatedRuntime="45 minutes",
            cpuRequirement=ResourceRequirement.MEDIUM,
            memoryRequirement=ResourceRequirement.MEDIUM,
            requiredFiles=["ligand", "receptor"],
            parameters=params,
            compatibility=["linux"],
            tags=["molecular-docking"],
            documentation=None,
            examples=None,
            isBuiltIn=True
        )

        assert len(template.parameters) == 2
        assert template.parameters[0].name == "center_x"
        assert template.parameters[1].required is True


class TestTaskResponses:
    """Test task response schemas."""

    def test_task_list_response(self, sample_task_template):
        """Test TaskListResponse schema."""
        response = TaskListResponse(
            tasks=[sample_task_template],
            total_count=1,
            organization_id="test-org"
        )

        assert len(response.tasks) == 1
        assert response.total_count == 1
        assert response.organization_id == "test-org"

    def test_task_detail_response(self, sample_task_template):
        """Test TaskDetailResponse schema."""
        api_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }

        service_config = {
            "engine": "test",
            "timeout": 300
        }

        response = TaskDetailResponse(
            task=sample_task_template,
            api_specification=api_spec,
            service_configuration=service_config
        )

        assert response.task.id == "test-task"
        assert response.api_specification["openapi"] == "3.0.0"
        assert response.service_configuration["engine"] == "test"

    def test_empty_task_list_response(self):
        """Test TaskListResponse with empty task list."""
        response = TaskListResponse(
            tasks=[],
            total_count=0,
            organization_id="empty-org"
        )

        assert response.tasks == []
        assert response.total_count == 0
        assert response.organization_id == "empty-org"


class TestEnums:
    """Test enum definitions."""

    def test_task_complexity_enum(self):
        """Test TaskComplexity enum values."""
        assert TaskComplexity.BEGINNER == "beginner"
        assert TaskComplexity.INTERMEDIATE == "intermediate"
        assert TaskComplexity.ADVANCED == "advanced"

    def test_task_category_enum(self):
        """Test TaskCategory enum values."""
        assert TaskCategory.AUTODOCK_VINA == "autodock_vina"
        assert TaskCategory.AUTODOCK4 == "autodock4"
        assert TaskCategory.SCHRODINGER == "schrodinger"
        assert TaskCategory.CUSTOM == "custom"

    def test_resource_requirement_enum(self):
        """Test ResourceRequirement enum values."""
        assert ResourceRequirement.LOW == "low"
        assert ResourceRequirement.MEDIUM == "medium"
        assert ResourceRequirement.HIGH == "high"
