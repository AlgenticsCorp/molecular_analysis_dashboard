"""
Unified Task Service combining database task definitions with task framework
"""

from typing import Dict, List, Any, Optional, Union, Tuple, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import json
import logging
from datetime import datetime, timezone
import sys
import os

# Add the database directory to path to import models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'database'))

from database.models.metadata import TaskDefinition
from database.models.task_execution import TaskFrameworkExecution
from ..adapters.providers.neurosnap_task_adapter import TaskExecutionService
from ..infrastructure.database import get_metadata_session as get_db

if TYPE_CHECKING:  # pragma: no cover - used for type checkers only
    from .execution_file_service import ExecutionFileService

logger = logging.getLogger(__name__)

# System organization ID for framework/system tasks
SYSTEM_ORG_ID = UUID('00000000-0000-0000-0000-000000000000')


class UnifiedTaskService:
    """Service for managing both database and framework tasks"""
    
    def __init__(self):
        self.task_framework = TaskExecutionService()
        self._framework_tasks_cache = {}
        
    async def get_all_tasks(self, org_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get all available tasks from both database and framework"""
        # Get framework tasks first (they take priority)
        framework_tasks = self._get_framework_tasks()
        framework_task_ids = {task['id'] for task in framework_tasks}
        
        # Get database tasks, excluding ones that exist in framework
        db_tasks = await self._get_database_tasks(org_id)
        unique_db_tasks = [task for task in db_tasks if task['id'] not in framework_task_ids]
        
        # Combine: framework tasks + unique database tasks
        return framework_tasks + unique_db_tasks
    
    async def get_task_by_id(self, task_id: str, org_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Get specific task by ID"""
        # Check database first
        db_task = await self._get_database_task(task_id, org_id)
        if db_task:
            return db_task
            
        # Check framework
        framework_task = self._get_framework_task(task_id)
        return framework_task
    
    async def execute_task(
        self, 
        task_id: str,
        parameters: Dict[str, Any],
        files: Optional[Dict[str, Any]] = None,
        org_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Execute a task through appropriate system"""
        
        # Determine if this is a framework task
        if self._is_framework_task(task_id):
            return await self._execute_framework_task(
                task_id, parameters, files, org_id, user_id
            )
        else:
            # Execute through existing database system
            return await self._execute_database_task(
                task_id, parameters, files, org_id, user_id
            )
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of task execution"""
        
        # Check if it's a framework execution
        execution = await self._get_task_execution(execution_id)
        if execution:
            return await self._get_framework_execution_status(execution_id)
        else:
            # Check legacy job system - not implemented yet
            return None
    
    async def get_execution_results(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get results of completed execution with input/output file listings"""
        
        execution = await self._get_task_execution(execution_id)
        if not execution:
            return None
        
        # Get input and output files from execution_files table
        from .execution_file_service import ExecutionFileService
        file_service = ExecutionFileService()
        
        input_files = await file_service.get_execution_files(
            execution_id=UUID(execution_id),
            file_type='input'
        )
        output_files = await file_service.get_execution_files(
            execution_id=UUID(execution_id),
            file_type='output'
        )
        
        # Get NeuroSnap results if available
        neurosnap_results = None
        if execution.external_job_id:
            neurosnap_results, output_files = await self._refresh_framework_results(
                execution=execution,
                execution_id=execution_id,
                file_service=file_service,
                output_files=output_files,
            )
        
        # Return combined data
        return {
            'execution_id': execution_id,
            'task_id': execution.task_id,
            'display_name': execution.display_name,
            'status': execution.status,
            'created_at': execution.created_at.isoformat() if execution.created_at else None,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'error_message': execution.error_message,
            'neurosnap_results': neurosnap_results or execution.output_data,
            'input_files': input_files,
            'output_files': output_files
        }

    async def _refresh_framework_results(
        self,
        execution: TaskFrameworkExecution,
        execution_id: str,
        file_service: 'ExecutionFileService',
        output_files: List[Dict[str, Any]],
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Fetch fresh results from NeuroSnap, downloading files if needed."""

        framework_results: Optional[Dict[str, Any]] = None
        try:
            framework_results = await self.task_framework.get_execution_results(
                execution.task_id,
                execution.external_job_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Unable to refresh NeuroSnap results for %s (%s): %s",
                execution_id,
                execution.external_job_id,
                exc,
            )
            return None, output_files

        if not framework_results:
            return None, output_files

        download_urls = framework_results.get('download_urls', {})
        local_output_files = [f for f in output_files if f.get('storage_backend') == 'local']
        if download_urls and len(local_output_files) == 0:
            logger.warning(
                "Output files not yet downloaded for %s, downloading now",
                execution_id,
            )
            try:
                await self._download_output_files(execution_id, framework_results)
                output_files = await file_service.get_execution_files(
                    execution_id=UUID(execution_id),
                    file_type='output'
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to download output files: %s", exc)

        execution.output_data = {
            'binding_affinity': framework_results.get('binding_affinity'),
            'top_poses_count': framework_results.get('top_poses_count'),
            'computation_time': framework_results.get('computation_time'),
            'status': framework_results.get('status')
        }
        execution.update_status('completed')
        await self._save_execution(execution)

        return framework_results, output_files

    async def delete_execution(self, execution_id: str, delete_files: bool = True) -> bool:
        """Remove an execution along with its associated files."""

        try:
            execution_uuid = UUID(execution_id)
        except ValueError as exc:
            raise ValueError("Invalid execution ID") from exc

        async for db in get_db():
            execution = await db.get(TaskFrameworkExecution, execution_uuid)
            if not execution:
                return False

            try:
                if delete_files:
                    from .execution_file_service import ExecutionFileService

                    file_service = ExecutionFileService()
                    await file_service.delete_execution_files(execution_uuid)

                await db.delete(execution)
                await db.commit()
            except Exception:
                await db.rollback()
                raise

            return True
    
    async def _download_output_files(self, execution_id: str, framework_results: Dict[str, Any]) -> None:
        """Download output files from NeuroSnap and store locally when job completes.
        
        This is called automatically when the status changes to 'completed' during polling.
        Files are downloaded immediately while NeuroSnap URLs are still valid.
        """
        from .execution_file_service import ExecutionFileService
        
        download_urls = framework_results.get('download_urls', {})
        if not download_urls:
            logger.info(f"No download URLs found for execution {execution_id}")
            return
        
        # Get job_id from framework results
        job_id = framework_results.get('job_id')
        if not job_id:
            logger.error(f"No job_id found in framework_results for execution {execution_id}")
            return
        
        api_key = os.getenv("NEUROSNAP_API_KEY")
        if not api_key:
            logger.warning("NEUROSNAP_API_KEY not configured; skipping NeuroSnap file downloads")
            return

        logger.info(f"Downloading {len(download_urls)} output file(s) from NeuroSnap for execution {execution_id}")
        
        file_service = ExecutionFileService()
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            for filename, url in download_urls.items():
                try:
                    logger.info(f"Downloading {filename} from NeuroSnap URL: {url}")
                    response = await client.get(url, headers={"X-API-KEY": api_key})
                    response.raise_for_status()
                    file_content = response.content
                    
                    # Determine content type from extension
                    content_type = 'application/octet-stream'
                    if filename.endswith('.csv'):
                        content_type = 'text/csv'
                    elif filename.endswith('.sdf'):
                        content_type = 'chemical/x-mdl-sdfile'
                    elif filename.endswith('.pdbqt'):
                        content_type = 'chemical/x-pdbqt'
                    elif filename.endswith('.pdb'):
                        content_type = 'chemical/x-pdb'
                    
                    # Store file locally
                    await file_service.store_output_file_content(
                        execution_id=UUID(execution_id),
                        parameter_name=filename.replace('.', '_'),  # e.g., output_csv, output_sdf
                        filename=filename,
                        content=file_content,
                        content_type=content_type
                    )
                    logger.info(f"Successfully stored {filename} ({len(file_content)} bytes)")
                except httpx.HTTPStatusError as e:
                    logger.error(f"Failed to download {filename} from NeuroSnap (HTTP {e.response.status_code}): {url}")
                except Exception as e:
                    logger.error(f"Failed to download/store output file {filename}: {e}")
    
    async def list_user_executions(
        self, 
        user_id: UUID, 
        org_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List user's task executions"""
        
        async for db in get_db():
            query = select(TaskFrameworkExecution).where(TaskFrameworkExecution.user_id == user_id)

            if org_id:
                query = query.where(TaskFrameworkExecution.org_id == org_id)

            query = query.order_by(TaskFrameworkExecution.created_at.desc()).limit(limit)
            result = await db.execute(query)
            executions = result.scalars().all()
            
            return [execution.to_dict() for execution in executions]
    
    # Private methods for database operations
    async def _get_database_tasks(self, org_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get tasks from database"""
        async for db in get_db():
            query = select(TaskDefinition).where(TaskDefinition.is_active == True)
            
            if org_id:
                query = query.where(TaskDefinition.org_id == org_id)
            
            result = await db.execute(query)
            task_definitions = result.scalars().all()
            
            tasks = []
            for td in task_definitions:
                task_dict = {
                    'id': td.task_id,
                    'name': td.task_metadata.get('name', td.task_id),
                    'description': td.task_metadata.get('description', 'No description available'),
                    'version': td.version,
                    'category': td.task_metadata.get('category', 'general'),
                    'tags': td.task_metadata.get('tags', []),
                    'parameters': self._extract_parameters_from_spec(td.interface_spec),
                    'resource_requirements': td.task_metadata.get('resource_requirements', {}),
                    'execution_time_estimate': td.task_metadata.get('execution_time_estimate', 300),
                    'source': 'database',
                    'task_definition_id': str(td.task_definition_id)
                }
                tasks.append(task_dict)
            
            return tasks
    
    async def _get_database_task(self, task_id: str, org_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Get a specific task from database by task_id"""
        async for db in get_db():
            query = select(TaskDefinition).where(TaskDefinition.task_id == task_id)
            
            if org_id:
                query = query.where(TaskDefinition.org_id == org_id)
            
            result = await db.execute(query)
            td = result.scalars().first()
            
            if td:
                return {
                    'id': td.task_id,
                    'name': td.task_metadata.get('name', td.task_id),
                    'description': td.task_metadata.get('description', 'No description available'),
                    'version': td.version,
                    'category': td.task_metadata.get('category', 'general'),
                    'tags': td.task_metadata.get('tags', []),
                    'parameters': self._extract_parameters_from_spec(td.interface_spec),
                    'resource_requirements': td.task_metadata.get('resource_requirements', {}),
                    'execution_time_estimate': td.task_metadata.get('execution_time_estimate', 300),
                    'source': 'database',
                    'task_definition_id': str(td.task_definition_id)
                }
            
            return None
    
    def _get_framework_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks from framework"""
        try:
            framework_tasks = self.task_framework.get_available_tasks()
            
            # Convert to standard format
            tasks = []
            for task_id, task_info in framework_tasks.items():
                task_dict = {
                    'id': task_id,
                    'name': task_info.get('name', task_id.replace('-', ' ').title()),
                    'description': task_info.get('description', ''),
                    'version': task_info.get('version', '1.0.0'),
                    'category': task_info.get('category', 'computational'),
                    'tags': task_info.get('tags', []),
                    'parameters': task_info.get('parameters', []),
                    'resource_requirements': task_info.get('resource_requirements', {}),
                    'execution_time_estimate': task_info.get('execution_time_estimate', 1200),
                    'source': 'framework'
                }
                tasks.append(task_dict)
                
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching framework tasks: {e}")
            return []
    
    def _get_framework_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task from framework by task_id"""
        try:
            framework_tasks = self.task_framework.get_available_tasks()
            task_info = framework_tasks.get(task_id)
            
            if task_info:
                return {
                    'id': task_id,
                    'name': task_info.get('name', task_id.replace('-', ' ').title()),
                    'description': task_info.get('description', ''),
                    'version': task_info.get('version', '1.0.0'),
                    'category': task_info.get('category', 'computational'),
                    'tags': task_info.get('tags', []),
                    'parameters': task_info.get('parameters', []),
                    'resource_requirements': task_info.get('resource_requirements', {}),
                    'execution_time_estimate': task_info.get('execution_time_estimate', 1200),
                    'source': 'framework'
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Error fetching framework task {task_id}: {e}")
            return None
    
    def _is_framework_task(self, task_id: str) -> bool:
        """Check if task is handled by framework"""
        framework_tasks = self.task_framework.get_available_tasks()
        return task_id in framework_tasks
    
    async def _execute_framework_task(
        self,
        task_id: str,
        parameters: Dict[str, Any],
        files: Optional[Dict[str, Any]],
        org_id: Optional[UUID],
        user_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Execute task through framework and record in database"""
        
        # Create execution ID
        execution_id = uuid4()
        
        # Get task definition for database record
        task_definition = await self._get_or_create_framework_task_definition(
            task_id, org_id
        )
        
        # Create execution record FIRST (before storing files to satisfy foreign key)
        execution = TaskFrameworkExecution(
            execution_id=execution_id,
            task_id=task_id,
            display_name=task_definition.task_metadata.get('name', task_id),
            org_id=org_id or SYSTEM_ORG_ID,  # Use system org ID if none provided
            user_id=user_id or SYSTEM_ORG_ID,  # Use system org ID if no user
            status='pending',
            input_data=parameters  # Start with just parameters
        )
        
        await self._save_execution(execution)
        
        # Now store files and update input_data with file references
        input_data = {**parameters}
        if files:
            # Store files using ExecutionFileService (no base64 encoding!)
            from .execution_file_service import ExecutionFileService
            file_service = ExecutionFileService()
            
            for key, file_info in files.items():
                content = file_info.get('content', b'')
                filename = file_info.get('filename')
                content_type = file_info.get('content_type')
                
                # Store file and get metadata
                file_record = await file_service.store_input_file(
                    execution_id=execution_id,
                    parameter_name=key,
                    filename=filename,
                    content=content,
                    content_type=content_type,
                    org_id=org_id
                )
                
                # Store only file reference in input_data (NOT content!)
                input_data[key] = {
                    'filename': file_record['filename'],
                    'size': file_record['size'],
                    'content_type': file_record['content_type'],
                    'file_id': file_record['file_id']  # Reference to execution_files table
                }
            
            # Update execution with file references
            execution.input_data = input_data
            await self._save_execution(execution)
        
        try:
            # Execute through framework - pass execution object and task definition
            external_job_id = await self.task_framework.execute_task(
                task_id, execution, task_definition.task_metadata
            )
            
            # Update execution with external job ID
            execution.external_job_id = external_job_id
            execution.status = 'running'
            execution.started_at = datetime.now(timezone.utc)
            await self._save_execution(execution)
            
            # Schedule background polling task
            from ..infrastructure.tasks import poll_job_status
            poll_job_status.apply_async(
                args=[str(execution_id), external_job_id, task_id],
                countdown=10  # Start polling in 10 seconds
            )
            logger.info(f"Scheduled status polling for execution {execution_id}")
            
            return {
                'execution_id': str(execution_id),
                'job_id': external_job_id,
                'status': 'running',
                'task_id': task_id,
                'created_at': execution.created_at.isoformat()
            }
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            await self._save_execution(execution)
            raise
    
    async def _get_or_create_framework_task_definition(
        self, 
        task_id: str, 
        org_id: Optional[UUID]
    ) -> TaskDefinition:
        """Get or create task definition for framework task"""
        
        async for db in get_db():
            # Try to find existing definition
            query = select(TaskDefinition).where(
                TaskDefinition.task_id == task_id,
                TaskDefinition.is_system == True
            )
            result = await db.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                return existing
            
            # Create new definition
            framework_task = self._get_framework_task(task_id)
            if not framework_task:
                raise ValueError(f"Framework task {task_id} not found")
            
            # Create task definition - use SYSTEM_ORG_ID for framework/system tasks
            task_def = TaskDefinition(
                task_id=task_id,
                org_id=org_id or SYSTEM_ORG_ID,  # Use system org ID if none provided
                version=framework_task.get('version', '1.0.0'),
                task_metadata=framework_task,
                interface_spec=self._generate_interface_spec(framework_task),
                service_config={
                    'source': 'framework',
                    'provider': 'task_framework'
                },
                is_active=True,
                is_system=True
            )
            
            db.add(task_def)
            await db.commit()
            await db.refresh(task_def)
            
            return task_def
    
    def _generate_interface_spec(self, framework_task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI spec from framework task info"""
        return {
            'openapi': '3.0.0',
            'info': {
                'title': framework_task.get('name', 'Framework Task'),
                'version': framework_task.get('version', '1.0.0')
            },
            'paths': {
                '/execute': {
                    'post': {
                        'summary': framework_task.get('description', ''),
                        'requestBody': {
                            'content': {
                                'multipart/form-data': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': self._convert_parameters_to_schema(
                                            framework_task.get('parameters', [])
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _convert_parameters_to_schema(self, parameters: List[Dict]) -> Dict[str, Any]:
        """Convert framework parameters to OpenAPI schema"""
        properties = {}
        
        for param in parameters:
            param_name = param.get('name', '')
            param_type = param.get('type', 'string')
            
            schema_prop = {'type': param_type}
            
            if param.get('description'):
                schema_prop['description'] = param['description']
            if param.get('required', False):
                schema_prop['required'] = True
            if param_type == 'file':
                schema_prop = {'type': 'string', 'format': 'binary'}
                
            properties[param_name] = schema_prop
        
        return properties
    
    async def _get_task_execution(self, execution_id: str) -> Optional[TaskFrameworkExecution]:
        """Get task execution by ID"""
        try:
            async for db in get_db():
                query = select(TaskFrameworkExecution).where(
                    TaskFrameworkExecution.execution_id == UUID(execution_id)
                )
                result = await db.execute(query)
                execution = result.scalar_one_or_none()
                return execution
        except Exception as e:
            logger.error(f"Error getting task execution {execution_id}: {e}")
            return None
    
    async def _save_execution(self, execution: TaskFrameworkExecution):
        """Save execution to database"""
        async for db in get_db():
            db.add(execution)
            await db.commit()
            await db.refresh(execution)
    
    def _extract_parameters_from_spec(self, interface_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract parameter info from OpenAPI spec"""
        parameters = []
        
        try:
            paths = interface_spec.get('paths', {})
            execute_path = paths.get('/execute', {})
            post_spec = execute_path.get('post', {})
            request_body = post_spec.get('requestBody', {})
            content = request_body.get('content', {})
            form_data = content.get('multipart/form-data', {})
            schema = form_data.get('schema', {})
            properties = schema.get('properties', {})
            
            for param_name, param_spec in properties.items():
                param = {
                    'name': param_name,
                    'type': param_spec.get('type', 'string'),
                    'description': param_spec.get('description', ''),
                    'required': param_name in schema.get('required', [])
                }
                
                if param_spec.get('format') == 'binary':
                    param['type'] = 'file'
                    
                parameters.append(param)
                
        except Exception as e:
            logger.warning(f"Error extracting parameters from spec: {e}")
        
        return parameters
    
    async def _execute_database_task(
        self,
        task_id: str,
        parameters: Dict[str, Any],
        files: Optional[Dict[str, Any]],
        org_id: Optional[UUID],
        user_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Execute task through database/job system - placeholder for now"""
        raise NotImplementedError(
            "Database task execution not yet implemented. "
            "Please use the job creation system for database-defined tasks."
        )
    
    async def _get_framework_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of framework task execution"""

        try:
            execution = await self._get_task_execution(execution_id)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error getting execution status %s: %s", execution_id, exc)
            return None

        if not execution:
            return None

        status_dict = self._build_execution_status_payload(execution)

        if execution.external_job_id and execution.task_id:
            framework_status = await self._try_get_framework_status(execution_id, execution)
            status_dict = await self._apply_framework_status_updates(
                execution_id,
                execution,
                status_dict,
                framework_status,
            )

        return status_dict

    def _build_execution_status_payload(self, execution: TaskFrameworkExecution) -> Dict[str, Any]:
        return {
            'execution_id': str(execution.execution_id),
            'task_id': execution.task_id,
            'status': execution.status,
            'created_at': execution.created_at.isoformat() if execution.created_at else None,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'error_message': execution.error_message,
            'external_job_id': execution.external_job_id,
            'progress': execution.progress_percentage,
        }

    async def _try_get_framework_status(
        self,
        execution_id: str,
        execution: TaskFrameworkExecution,
    ) -> Optional[Dict[str, Any]]:
        try:
            return await self.task_framework.get_execution_status(
                execution.task_id,
                execution.external_job_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error getting framework status for %s: %s", execution_id, exc)
            return None

    async def _apply_framework_status_updates(
        self,
        execution_id: str,
        execution: TaskFrameworkExecution,
        status_dict: Dict[str, Any],
        framework_status: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not framework_status:
            return status_dict

        new_status = framework_status.get('status')
        if new_status and new_status != execution.status:
            old_status = execution.status
            execution.update_status(new_status)
            await self._save_execution(execution)

            if new_status == 'completed' and old_status != 'completed':
                logger.info(
                    "Job %s completed, downloading output files",
                    execution_id,
                )
                try:
                    await self._download_output_files(execution_id, framework_status)
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Failed to download output files for %s: %s",
                        execution_id,
                        exc,
                    )

        status_dict.update({
            'progress': framework_status.get('progress', execution.progress_percentage),
            'message': framework_status.get('message'),
            'framework_status': framework_status,
        })
        return status_dict


# Global instance
unified_task_service = UnifiedTaskService()
