"""
Task API schemas for molecular analysis dashboard.

This module defines Pydantic schemas for the task management API endpoints,
providing type-safe request and response models that match the frontend interface.

Responsibilities:
- Define TaskTemplate schema matching frontend TypeScript interfaces
- Provide validation and serialization for API endpoints
- Support field aliasing for camelCase/snake_case conversion
- Define enum types for task categories, complexity, and resource requirements

Dependencies:
- pydantic: For schema validation and serialization
- typing: For type annotations
- enum: For enumerated values

Assumptions:
- Frontend uses camelCase naming convention
- Backend uses snake_case naming convention
- All API responses follow consistent structure with error handling
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class TaskComplexity(str, Enum):
    """Task complexity levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TaskCategory(str, Enum):
    """Task categories."""

    AUTODOCK_VINA = "autodock_vina"
    AUTODOCK4 = "autodock4"
    SCHRODINGER = "schrodinger"
    CUSTOM = "custom"


class ResourceRequirement(str, Enum):
    """Resource requirement levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskParameter(BaseModel):
    """Task parameter definition."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, number, boolean, file, select)")
    required: bool = Field(..., description="Whether parameter is required")
    default: Optional[Union[str, int, float, bool]] = Field(None, description="Default value")
    description: str = Field(..., description="Parameter description")
    options: Optional[List[str]] = Field(None, description="Available options for select type")


class TaskTemplate(BaseModel):
    """Task template response schema matching frontend interface."""

    id: str = Field(..., description="Task identifier")
    name: str = Field(..., description="Task display name")
    description: str = Field(..., description="Task description")
    category: TaskCategory = Field(..., description="Task category")
    version: str = Field(..., description="Task version")
    complexity: TaskComplexity = Field(..., description="Task complexity level")
    estimated_runtime: str = Field(
        ..., alias="estimatedRuntime", description="Estimated execution time"
    )
    cpu_requirement: ResourceRequirement = Field(
        ..., alias="cpuRequirement", description="CPU requirement"
    )
    memory_requirement: ResourceRequirement = Field(
        ..., alias="memoryRequirement", description="Memory requirement"
    )
    required_files: List[str] = Field(
        ..., alias="requiredFiles", description="Required input files"
    )
    parameters: List[TaskParameter] = Field(..., description="Task parameters")
    compatibility: List[str] = Field(..., description="Supported platforms")
    tags: List[str] = Field(..., description="Task tags")
    documentation: Optional[str] = Field(None, description="Task documentation")
    examples: Optional[List[str]] = Field(None, description="Usage examples")
    is_built_in: bool = Field(..., alias="isBuiltIn", description="Whether task is built-in")

    class Config:
        """Pydantic configuration."""

        validate_by_name = True
        extra = "forbid"


class TaskListResponse(BaseModel):
    """Response schema for task list endpoint."""

    tasks: List[TaskTemplate] = Field(..., description="List of available tasks")
    total_count: int = Field(..., description="Total number of tasks")
    organization_id: str = Field(..., description="Organization ID")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class TaskDetailResponse(BaseModel):
    """Response schema for task detail endpoint."""

    task: TaskTemplate = Field(..., description="Task details")
    api_specification: Dict[str, Any] = Field(
        ..., description="OpenAPI specification for task execution"
    )
    service_configuration: Dict[str, Any] = Field(
        ..., description="Service deployment configuration"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    code: int = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
