"""
NeuroSnap Provider Adapter for Task Framework Integration.

This adapter bridges the task framework with NeuroSnap provider-specific endpoints.
It handles the translation between generic task execution and provider-specific APIs.
"""

from typing import Any, Dict, Optional

DEFAULT_NEUROSNAP_BASE_URL = "http://localhost:8000"
DEFAULT_TASK_NOTE = "Task framework execution"
from uuid import UUID
import asyncio
import importlib
import logging
import aiofiles
import httpx
from abc import ABC, abstractmethod

from ...services.task_registry import TaskRegistry


logger = logging.getLogger(__name__)


class TaskExecutorPort(ABC):
    """Port interface for task execution."""
    
    @abstractmethod
    async def submit_task(self, execution: Any, task_definition: Dict[str, Any]) -> str:
        """Submit task for execution."""
        pass


class TaskExecution:
    """Task execution entity placeholder."""
    
    def __init__(self, execution_id: str, task_id: str, parameters: Dict[str, Any]):
        self.execution_id = execution_id
        self.task_id = task_id
        self.parameters = parameters
        self.status = "PENDING"
        self.external_job_id = None


class NeuroSnapBaseAdapter(TaskExecutorPort):
    """Shared helper for NeuroSnap-backed tasks."""

    def __init__(self, base_url: str = DEFAULT_NEUROSNAP_BASE_URL) -> None:
        self.base_url = base_url

    async def get_task_status(self, external_job_id: str) -> Dict[str, Any]:
        """Fetch job status through the unified NeuroSnap status endpoint."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/providers/neurosnap/status/{external_job_id}"
                )
                response.raise_for_status()
                return response.json()

        except Exception as exc:
            raise RuntimeError(f"Failed to get task status: {exc}") from exc

    async def get_task_results(self, external_job_id: str) -> Dict[str, Any]:
        """Fetch job results through the unified NeuroSnap results endpoint."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/providers/neurosnap/results/{external_job_id}"
                )
                response.raise_for_status()
                return response.json()

        except Exception as exc:
            raise RuntimeError(f"Failed to get task results: {exc}") from exc


class NeuroSnapDockingAdapter(NeuroSnapBaseAdapter):
    """Adapter for executing GNINA docking tasks via NeuroSnap provider endpoints."""

    def __init__(self, base_url: str = DEFAULT_NEUROSNAP_BASE_URL) -> None:
        super().__init__(base_url)
        self.docking_endpoint = "/api/v1/providers/neurosnap/docking/submit"

    async def submit_task(
        self,
        execution: TaskExecution,
        task_definition: Dict[str, Any],
    ) -> str:
        """Submit GNINA docking task to NeuroSnap provider endpoint."""

        try:
            from ...services.execution_file_service import ExecutionFileService

            file_service = ExecutionFileService()
            parameters = execution.input_data or {}

            files: Dict[str, Any] = {}
            form_data: Dict[str, Any] = {}

            receptor_info = parameters.get("receptor_file")
            if receptor_info:
                file_id = receptor_info.get("file_id")
                content = await file_service.get_file_content(file_id)
                if content:
                    files["receptor_file"] = (
                        receptor_info.get("filename", "receptor.pdb"),
                        content,
                        receptor_info.get("content_type", "chemical/x-pdb"),
                    )

            ligand_info = parameters.get("ligand_file")
            if ligand_info:
                file_id = ligand_info.get("file_id")
                content = await file_service.get_file_content(file_id)
                if content:
                    files["ligand_file"] = (
                        ligand_info.get("filename", "ligand.sdf"),
                        content,
                        ligand_info.get("content_type", "chemical/x-mdl-sdfile"),
                    )

            form_data["job_name"] = parameters.get("job_name", "GNINA Docking")
            form_data["note"] = parameters.get("note", DEFAULT_TASK_NOTE)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}{self.docking_endpoint}",
                    files=files,
                    data=form_data,
                )
                response.raise_for_status()

                result = response.json()
                return result.get("job_id")

        except Exception as exc:
            raise RuntimeError(f"Failed to submit GNINA docking task: {exc}") from exc


class NeuroSnapAmberRelaxationAdapter(NeuroSnapBaseAdapter):
    """Adapter for executing Amber relaxation tasks via NeuroSnap provider endpoints."""

    def __init__(self, base_url: str = DEFAULT_NEUROSNAP_BASE_URL) -> None:
        super().__init__(base_url)
        self.relaxation_endpoint = "/api/v1/providers/neurosnap/molecular-dynamics/amber-relaxation/submit"

    async def submit_task(
        self,
        execution: TaskExecution,
        task_definition: Dict[str, Any],
    ) -> str:
        """Submit Amber relaxation task to NeuroSnap provider endpoint."""

        parameters = execution.input_data or {}
        structure_info = parameters.get("structure_file")

        if not structure_info:
            raise RuntimeError("structure_file parameter is required for Amber Relaxation task")

        file_id = structure_info.get("file_id")
        if not file_id:
            raise RuntimeError("structure_file metadata missing file identifier")

        from ...services.execution_file_service import ExecutionFileService

        file_service = ExecutionFileService()
        content = await file_service.get_file_content(file_id)

        if not content:
            raise RuntimeError("Unable to load structure file content for submission")

        files = {
            "structure_file": (
                structure_info.get("filename", "structure.pdb"),
                content,
                structure_info.get("content_type", "chemical/x-pdb"),
            )
        }

        job_name = parameters.get("job_name") or "AMBER Relaxation"
        note = parameters.get("note") or DEFAULT_TASK_NOTE
        max_iterations = parameters.get("max_iterations")
        tolerance = parameters.get("tolerance")

        form_data = {
            "job_name": job_name,
            "note": note,
            "max_iterations": str(max_iterations if max_iterations is not None else 2500),
            "tolerance": str(tolerance if tolerance is not None else 1.0),
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}{self.relaxation_endpoint}",
                    files=files,
                    data=form_data,
                )
                response.raise_for_status()

                result = response.json()
                if isinstance(result, dict):
                    job_id = result.get("job_id")
                else:
                    job_id = result

                if not isinstance(job_id, str):
                    raise RuntimeError("Unexpected response payload from NeuroSnap Amber Relaxation API")

                return job_id

        except Exception as exc:
            raise RuntimeError(f"Failed to submit Amber relaxation task: {exc}") from exc

    async def _prepare_file_data(self, file_param: Any) -> Dict[str, Any]:
        """Prepare file data for multipart submission."""
        
        if isinstance(file_param, dict):
            # Handle file data passed as dictionary 
            return {
                'content': file_param.get('content', b''),
                'filename': file_param.get('filename', 'file.dat')
            }
        elif hasattr(file_param, 'read'):
            # Handle file-like objects
            content = await file_param.read()
            filename = getattr(file_param, 'filename', 'file.dat')
            return {'content': content, 'filename': filename}
        else:
            # Handle string paths to files
            async with aiofiles.open(file_param, 'rb') as f:
                content = await f.read()
            return {'content': content, 'filename': file_param.split('/')[-1]}


class TaskExecutionService:
    """Service for managing task executions with provider adapters."""

    def __init__(self, registry: Optional[TaskRegistry] = None) -> None:
        self.registry = registry or TaskRegistry()
        self.adapters: Dict[str, TaskExecutorPort] = {}
        self._adapter_errors: Dict[str, str] = {}
        self._initialize_adapters()

    def _initialize_adapters(self) -> None:
        """Instantiate adapters declared in the registry."""

        self.adapters.clear()
        self._adapter_errors.clear()

        for task_id, config in self.registry.list_tasks().items():
            adapter_config = config.get("adapter") or {}
            try:
                adapter = self._instantiate_adapter(adapter_config)
                if adapter:
                    self.adapters[task_id] = adapter
                    logger.debug("Adapter ready for task '%s'", task_id)
            except Exception as exc:  # noqa: BLE001 - capture adapter init errors for observability
                self._adapter_errors[task_id] = str(exc)
                logger.error("Failed to initialize adapter for task %s: %s", task_id, exc)

    def _instantiate_adapter(self, adapter_config: Dict[str, Any]) -> Optional[TaskExecutorPort]:
        """Create adapter instance based on registry configuration."""

        module_path = adapter_config.get("module")
        class_name = adapter_config.get("class")

        if not module_path or not class_name:
            raise ValueError("Adapter configuration missing 'module' or 'class'")

        module = importlib.import_module(module_path)
        adapter_cls = getattr(module, class_name, None)
        if adapter_cls is None:
            raise ImportError(f"Adapter class '{class_name}' not found in module '{module_path}'")

        options = adapter_config.get("options") or {}
        return adapter_cls(**options)

    def get_available_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available framework tasks."""
        metadata = self.registry.list_metadata()
        return {
            task_id: task_meta
            for task_id, task_meta in metadata.items()
            if task_id in self.adapters
        }

    def get_adapter_errors(self) -> Dict[str, str]:
        """Expose adapter initialization errors for diagnostics."""
        return dict(self._adapter_errors)

    async def execute_task(self, 
                          task_id: str,
                          execution: TaskExecution,
                          task_definition: Dict[str, Any]) -> str:
        """Execute a task using the appropriate provider adapter."""
        
        adapter = self.adapters.get(task_id)
        if not adapter:
            raise ValueError(f"No adapter found for task: {task_id}")

        # Submit task to provider
        task_info = task_definition or self.registry.get_metadata(task_id) or {}
        external_job_id = await adapter.submit_task(execution, task_info)
        
        # Update execution with external job ID
        execution.external_job_id = external_job_id
        execution.status = "SUBMITTED"
        
        return external_job_id

    async def get_execution_status(self, task_id: str, external_job_id: str) -> Dict[str, Any]:
        """Get execution status from provider."""
        
        adapter = self.adapters.get(task_id)
        if not adapter:
            raise ValueError(f"No adapter found for task: {task_id}")

        return await adapter.get_task_status(external_job_id)

    async def get_execution_results(self, task_id: str, external_job_id: str) -> Dict[str, Any]:
        """Get execution results from provider."""
        
        adapter = self.adapters.get(task_id)
        if not adapter:
            raise ValueError(f"No adapter found for task: {task_id}")

        return await adapter.get_task_results(external_job_id)