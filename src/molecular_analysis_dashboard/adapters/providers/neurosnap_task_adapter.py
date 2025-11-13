"""
NeuroSnap Provider Adapter for Task Framework Integration.

This adapter bridges the task framework with NeuroSnap provider-specific endpoints.
It handles the translation between generic task execution and provider-specific APIs.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
import asyncio
import aiofiles
from fastapi import UploadFile
import httpx
from abc import ABC, abstractmethod


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


class NeuroSnapDockingAdapter(TaskExecutorPort):
    """Adapter for executing GNINA docking tasks via NeuroSnap provider endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.docking_endpoint = "/api/v1/providers/neurosnap/docking/submit"

    async def submit_task(self, 
                         execution: TaskExecution,
                         task_definition: Dict[str, Any]) -> str:
        """Submit GNINA docking task to NeuroSnap provider endpoint."""
        
        try:
            # Import ExecutionFileService to retrieve file content
            from ...services.execution_file_service import ExecutionFileService
            file_service = ExecutionFileService()
            
            # Extract parameters from task execution
            parameters = execution.input_data
            
            # Prepare files and form data for httpx
            files = {}
            form_data = {}
            
            # Handle file parameters - retrieve from execution_files table
            if 'receptor_file' in parameters:
                receptor_info = parameters['receptor_file']
                file_id = receptor_info.get('file_id')
                
                # Fetch file content from storage
                content = await file_service.get_file_content(file_id)
                if content:
                    files['receptor_file'] = (
                        receptor_info['filename'],
                        content,
                        receptor_info.get('content_type', 'chemical/x-pdb')
                    )
            
            if 'ligand_file' in parameters:
                ligand_info = parameters['ligand_file']
                file_id = ligand_info.get('file_id')
                
                # Fetch file content from storage
                content = await file_service.get_file_content(file_id)
                if content:
                    files['ligand_file'] = (
                        ligand_info['filename'],
                        content,
                        ligand_info.get('content_type', 'chemical/x-mdl-sdfile')
                    )

            # Handle string parameters (no change needed)
            form_data['job_name'] = parameters.get('job_name', 'GNINA Docking')
            form_data['note'] = parameters.get('note', 'Task framework execution')

            # Submit to provider endpoint
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}{self.docking_endpoint}",
                    files=files,
                    data=form_data
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Return the external job ID from NeuroSnap
                return result.get('job_id')
                
        except Exception as e:
            raise RuntimeError(f"Failed to submit GNINA docking task: {e}")

    async def get_task_status(self, external_job_id: str) -> Dict[str, Any]:
        """Get task status from NeuroSnap provider endpoint."""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/providers/neurosnap/status/{external_job_id}"
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise RuntimeError(f"Failed to get task status: {e}")

    async def get_task_results(self, external_job_id: str) -> Dict[str, Any]:
        """Get task results from NeuroSnap provider endpoint."""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/providers/neurosnap/results/{external_job_id}"
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise RuntimeError(f"Failed to get task results: {e}")

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

    def __init__(self):
        self.adapters = {
            'gnina-molecular-docking': NeuroSnapDockingAdapter()
        }

    async def get_available_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available framework tasks."""
        # Return tasks that have adapters configured as a dictionary
        return {
            "gnina-molecular-docking": {
                "name": "GNINA Molecular Docking",
                "description": "Perform molecular docking using GNINA via NeuroSnap",
                "version": "1.0.0",
                "category": "molecular-docking",
                "tags": ["docking", "gnina", "protein-ligand"],
                "provider": "neurosnap",
                "interface_type": "openapi",
                "parameters": [
                    {
                        "name": "receptor_file",
                        "type": "file",
                        "required": True,
                        "description": "Protein receptor file (PDB format)"
                    },
                    {
                        "name": "ligand_file",
                        "type": "file",
                        "required": True,
                        "description": "Ligand file (SDF/MOL2 format)"
                    },
                    {
                        "name": "exhaustiveness",
                        "type": "integer",
                        "required": False,
                        "default": 8,
                        "description": "Exhaustiveness of the global search"
                    }
                ],
                "resource_requirements": {
                    "cpu": "2",
                    "memory": "4Gi"
                },
                "execution_time_estimate": 600
            }
        }

    async def execute_task(self, 
                          task_id: str,
                          execution: TaskExecution,
                          task_definition: Dict[str, Any]) -> str:
        """Execute a task using the appropriate provider adapter."""
        
        adapter = self.adapters.get(task_id)
        if not adapter:
            raise ValueError(f"No adapter found for task: {task_id}")

        # Submit task to provider
        external_job_id = await adapter.submit_task(execution, task_definition)
        
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