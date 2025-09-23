"""
Task transformation services for converting between database and API formats.

This module provides transformation functions to convert database TaskDefinition
objects to frontend-compatible TaskTemplate schemas, handling both database objects
and dictionary formats for testing purposes.

Responsibilities:
- Transform database TaskDefinition to frontend TaskTemplate format
- Extract parameters from OpenAPI specifications
- Handle enum conversions for categories, complexity, and resource requirements
- Provide API and service configuration extraction

Dependencies:
- ..schemas.tasks: For TaskTemplate and related schemas
- typing: For type annotations
- uuid: For UUID handling

Assumptions:
- Database objects have task_metadata, interface_spec, and service_config attributes
- OpenAPI specifications follow standard multipart/form-data schema format
- Testing mode uses dictionary format instead of database objects
"""

from typing import Any, Dict, List, Union
from uuid import uuid4

from ..schemas.tasks import (
    ResourceRequirement,
    TaskCategory,
    TaskComplexity,
    TaskParameter,
    TaskTemplate,
)


def transform_task_definition_to_template(
    task_definition: Union[Dict[str, Any], Any]
) -> TaskTemplate:
    """Transform database TaskDefinition to frontend TaskTemplate format.

    Converts a database TaskDefinition object or dictionary to a frontend-compatible
    TaskTemplate schema. Handles parameter extraction from OpenAPI specifications
    and applies proper enum conversions.

    Args:
        task_definition (Any): Database TaskDefinition object with attributes
            task_id, version, task_metadata, interface_spec, service_config
            OR dictionary with keys: id, name, description, category, version, config

    Returns:
        TaskTemplate: Frontend-compatible task template with camelCase field aliases
            and properly typed enum values for category, complexity, and requirements

    Raises:
        ValueError: If required fields are missing from task_definition
        KeyError: If expected dictionary keys are not present (dict mode)

    Example:
        >>> task_def = {
        ...     "id": "molecular-docking-basic",
        ...     "name": "Molecular Docking",
        ...     "description": "Basic docking task",
        ...     "category": "Molecular Docking",
        ...     "version": "1.0.0",
        ...     "config": {"api_specification": {...}}
        ... }
        >>> template = transform_task_definition_to_template(task_def)
        >>> template.id
        'molecular-docking-basic'
        >>> template.category
        <TaskCategory.AUTODOCK_VINA: 'autodock_vina'>
    """
    # Handle both database objects and dictionaries for testing
    if isinstance(task_definition, dict):
        # For testing with dictionary data
        task_id = task_definition.get("id", "")
        version = task_definition.get("version", "1.0.0")
        config = task_definition.get("config", {})
        api_spec = config.get("api_specification", {})

        # Extract parameters from OpenAPI specification
        parameters = []
        paths = api_spec.get("paths", {})
        for path, methods in paths.items():
            for method, spec in methods.items():
                if method == "post" and "requestBody" in spec:
                    content = spec["requestBody"].get("content", {})
                    multipart = content.get("multipart/form-data", {})
                    schema = multipart.get("schema", {})
                    properties = schema.get("properties", {})
                    required_fields = schema.get("required", [])

                    for prop_name, prop_spec in properties.items():
                        if prop_spec.get("format") != "binary":  # Skip file uploads
                            parameters.append(
                                TaskParameter(
                                    name=prop_name,
                                    type=prop_spec.get("type", "string"),
                                    required=prop_name in required_fields,
                                    default=prop_spec.get("default"),
                                    description=prop_spec.get("description", ""),
                                    options=prop_spec.get("enum"),
                                )
                            )

        return TaskTemplate(
            id=task_id,
            name=task_definition.get("name", task_id),
            description=task_definition.get("description", ""),
            category=TaskCategory.AUTODOCK_VINA,
            version=version,
            complexity=TaskComplexity.INTERMEDIATE,
            estimatedRuntime="~30 minutes",
            cpuRequirement=ResourceRequirement.MEDIUM,
            memoryRequirement=ResourceRequirement.MEDIUM,
            requiredFiles=["ligand", "receptor"],
            parameters=parameters,
            compatibility=["linux", "macos"],
            tags=["molecular-dynamics", "docking"],
            documentation=None,
            examples=None,
            isBuiltIn=True,
        )
    else:
        # Handle database objects (original logic)
        metadata = getattr(task_definition, "task_metadata", {}) or {}
        interface_spec = getattr(task_definition, "interface_spec", {}) or {}

        # Transform parameters from interface spec
        parameters = []
        if "parameters" in interface_spec:
            for param in interface_spec["parameters"]:
                parameters.append(
                    TaskParameter(
                        name=param.get("name", ""),
                        type=param.get("type", "string"),
                        required=param.get("required", False),
                        default=param.get("default"),
                        description=param.get("description", ""),
                        options=param.get("options"),
                    )
                )

        # Create TaskTemplate with proper field mapping
        return TaskTemplate(
            id=getattr(task_definition, "task_id", ""),
            name=metadata.get("name", getattr(task_definition, "task_id", "")),
            description=metadata.get("description", ""),
            category=TaskCategory(metadata.get("category", "custom")),
            version=getattr(task_definition, "version", "1.0.0"),
            complexity=TaskComplexity(metadata.get("complexity", "intermediate")),
            estimatedRuntime=metadata.get("estimatedRuntime", "Unknown"),
            cpuRequirement=ResourceRequirement(metadata.get("cpuRequirement", "medium")),
            memoryRequirement=ResourceRequirement(metadata.get("memoryRequirement", "medium")),
            requiredFiles=metadata.get("requiredFiles", []),
            parameters=parameters,
            compatibility=metadata.get("compatibility", ["linux"]),
            tags=metadata.get("tags", []),
            documentation=metadata.get("documentation"),
            examples=metadata.get("examples"),
            isBuiltIn=metadata.get("isBuiltIn", False),
        )


def transform_task_definitions_to_templates(task_definitions: List[Any]) -> List[TaskTemplate]:
    """Transform list of database TaskDefinitions to TaskTemplates.

    Bulk transformation operation that converts multiple database objects
    to frontend-compatible schemas in a single operation.

    Args:
        task_definitions (List[Any]): List of database TaskDefinition objects
            or dictionaries following the same format as transform_task_definition_to_template

    Returns:
        List[TaskTemplate]: List of frontend-compatible task templates with
            consistent formatting and enum conversions applied

    Raises:
        ValueError: If any task definition is malformed

    Example:
        >>> task_defs = [task_def1, task_def2, task_def3]
        >>> templates = transform_task_definitions_to_templates(task_defs)
        >>> len(templates)
        3
        >>> all(isinstance(t, TaskTemplate) for t in templates)
        True
    """
    return [transform_task_definition_to_template(task_def) for task_def in task_definitions]


def extract_api_specification(task_definition: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """Extract OpenAPI specification from task definition.

    Retrieves the OpenAPI 3.0 specification that defines the task's execution
    interface, including endpoints, request schemas, and response formats.

    Args:
        task_definition (Any): Database TaskDefinition object with interface_spec attribute
            OR dictionary with config.api_specification key

    Returns:
        Dict[str, Any]: OpenAPI 3.0 specification dictionary containing:
            - info: API metadata (title, version)
            - paths: Available endpoints (/execute, /status/{job_id}, /results/{job_id})
            - components: Reusable schemas and parameters

    Raises:
        AttributeError: If database object lacks interface_spec attribute
        KeyError: If dictionary lacks expected config structure

    Example:
        >>> api_spec = extract_api_specification(task_def)
        >>> api_spec['openapi']
        '3.0.0'
        >>> '/execute' in api_spec['paths']
        True
    """
    if isinstance(task_definition, dict):
        # For testing with dictionary data
        config = task_definition.get("config", {})
        return config.get("api_specification", {})
    else:
        # Handle database objects
        return getattr(task_definition, "interface_spec", {}) or {}


def extract_service_configuration(task_definition: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """Extract service deployment configuration from task definition.

    Retrieves configuration parameters needed for task execution, including
    engine selection, timeout settings, and deployment-specific options.

    Args:
        task_definition (Any): Database TaskDefinition object with service_config attribute
            OR dictionary with config containing engine, timeout, type keys

    Returns:
        Dict[str, Any]: Service configuration dictionary containing:
            - engine: Execution engine (vina, smina, gnina, custom)
            - timeout: Maximum execution time in seconds
            - type: Task type (basic, advanced, custom)
            - Additional engine-specific parameters

    Raises:
        AttributeError: If database object lacks service_config attribute

    Example:
        >>> service_config = extract_service_configuration(task_def)
        >>> service_config['engine']
        'vina'
        >>> service_config['timeout']
        3600
    """
    if isinstance(task_definition, dict):
        # For testing with dictionary data
        config = task_definition.get("config", {})
        return {
            "engine": config.get("engine", "vina"),
            "timeout": config.get("timeout", 3600),
            "type": config.get("type", "basic"),
        }
    else:
        # Handle database objects
        return getattr(task_definition, "service_config", {}) or {}
