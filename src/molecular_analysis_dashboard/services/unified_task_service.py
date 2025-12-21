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
from pathlib import Path
from urllib.parse import urljoin, urlparse
import re
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
DEFAULT_TIMESTAMP = datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat()


class UnifiedTaskService:
    """Service for managing both database and framework tasks"""

    STATUS_ALIASES = {
        'succeeded': 'completed',
        'success': 'completed',
        'successful': 'completed',
        'finished': 'completed',
        'complete': 'completed',
        'failed': 'failed',
        'failure': 'failed',
        'errored': 'failed',
        'error': 'failed',
        'cancelled': 'cancelled',
        'canceled': 'cancelled',
    }

    TERMINAL_STATUSES = {'completed', 'failed', 'cancelled'}

    def __init__(self):
        self.task_framework = TaskExecutionService()
        self._framework_tasks_cache = {}

    def _normalize_status_value(self, status: Optional[str]) -> Optional[str]:
        if status is None:
            return None

        normalized = str(status).strip().lower()
        if not normalized:
            return None

        return self.STATUS_ALIASES.get(normalized, normalized)
        
    def _normalize_task(
        self,
        task_id: str,
        metadata: Dict[str, Any],
        source: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Transform metadata into a TaskTemplate-compatible payload."""

        extra = extra or {}

        provider_value = self._resolve_provider(metadata, extra, source)
        provider_type = self._resolve_provider_type(metadata, extra, provider_value)
        engine_value = self._resolve_engine(metadata, extra, provider_value, source)
        status_value = self._resolve_status(metadata, extra)
        parameters = self._resolve_parameters(metadata, extra)
        outputs = self._resolve_outputs(metadata, extra)
        raw_resources = self._resolve_resource_block(metadata, extra)
        execution_estimate = self._resolve_execution_estimate(metadata, extra)
        interface_type = self._resolve_interface_type(metadata, extra)
        created_at = self._resolve_timestamp('created_at', metadata, extra)
        updated_at = self._resolve_timestamp('updated_at', metadata, extra)
        subcategory = metadata.get('subcategory') or extra.get('subcategory')

        normalized: Dict[str, Any] = {
            'id': task_id,
            'name': metadata.get('name', task_id.replace('-', ' ').title()),
            'description': metadata.get('description', ''),
            'version': metadata.get('version', '1.0.0'),
            'category': metadata.get('category', 'general'),
            'subcategory': subcategory,
            'tags': metadata.get('tags', []),
            'engine': engine_value,
            'status': status_value,
            'parameters': parameters,
            'resource_requirements': self._normalize_resource_requirements(raw_resources),
            'execution_time_estimate': execution_estimate,
            'provider': provider_value,
            'provider_type': provider_type,
            'interface_type': interface_type,
            'source': source,
            'created_at': created_at,
            'updated_at': updated_at,
        }

        if outputs:
            normalized['outputs'] = outputs

        for key, value in extra.items():
            if key in {
                'parameters',
                'resource_requirements',
                'execution_time_estimate',
                'provider',
                'provider_type',
                'interface_type',
                'created_at',
                'updated_at',
                'subcategory',
                'status',
                'engine',
                'outputs',
            }:
                continue
            if value is not None:
                normalized[key] = value

        return normalized

    def _normalize_resource_requirements(self, resources: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not resources:
            return {}

        normalized: Dict[str, Any] = {}

        cpu_value = self._parse_numeric(
            resources.get('cpu_cores')
            or resources.get('cpu')
            or resources.get('vcpus')
        )
        if cpu_value is not None:
            normalized['cpu_cores'] = cpu_value

        memory_value = self._parse_memory(
            resources.get('memory_gb')
            or resources.get('memory')
            or resources.get('ram')
        )
        if memory_value is not None:
            normalized['memory_gb'] = memory_value

        disk_value = self._parse_numeric(
            resources.get('disk_gb')
            or resources.get('disk')
            or resources.get('storage')
        )
        if disk_value is not None:
            normalized['disk_gb'] = disk_value

        gpu_value = resources.get('gpu') or resources.get('gpu_type')
        if gpu_value is not None:
            normalized['gpu'] = gpu_value

        return normalized

    def _parse_numeric(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            match = re.findall(r"[-+]?\d*\.?\d+", cleaned)
            if not match:
                return None
            try:
                return float(match[0])
            except ValueError:
                return None
        return None

    def _parse_memory(self, value: Any) -> Optional[float]:
        numeric_value = self._parse_numeric(value)
        if numeric_value is None:
            return None
        if isinstance(value, str):
            lowered = value.lower()
            if 'ti' in lowered or 'tb' in lowered:
                return round(numeric_value * 1024, 2)
            if 'mi' in lowered or 'mb' in lowered:
                return round(numeric_value / 1024, 2)
        return round(numeric_value, 2)

    def _resolve_provider(self, metadata: Dict[str, Any], extra: Dict[str, Any], source: str) -> str:
        provider = metadata.get('provider') or extra.get('provider')
        if provider:
            return provider
        return 'internal' if source == 'framework' else 'database'

    def _resolve_provider_type(
        self,
        metadata: Dict[str, Any],
        extra: Dict[str, Any],
        provider: str,
    ) -> Optional[str]:
        provider_type = metadata.get('provider_type') or extra.get('provider_type')
        if provider_type:
            return provider_type

        lowered = provider.lower() if isinstance(provider, str) else ''
        if lowered in {'internal', 'domestic'}:
            return 'domestic'
        if lowered in {'neurosnap', 'cloud', 'external'}:
            return 'cloud'
        return None

    def _resolve_engine(
        self,
        metadata: Dict[str, Any],
        extra: Dict[str, Any],
        provider: str,
        source: str,
    ) -> str:
        return metadata.get('engine') or extra.get('engine') or provider or source

    def _resolve_status(self, metadata: Dict[str, Any], extra: Dict[str, Any]) -> str:
        return metadata.get('status') or extra.get('status') or 'active'

    def _resolve_parameters(self, metadata: Dict[str, Any], extra: Dict[str, Any]) -> List[Dict[str, Any]]:
        parameters = extra.get('parameters')
        if parameters is not None:
            return parameters
        return metadata.get('parameters', [])

    def _resolve_outputs(self, metadata: Dict[str, Any], extra: Dict[str, Any]) -> List[Dict[str, Any]]:
        outputs = extra.get('outputs')
        if outputs is not None:
            return outputs
        return metadata.get('outputs', [])

    def _resolve_resource_block(self, metadata: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
        return extra.get('resource_requirements') or metadata.get('resource_requirements', {})

    def _resolve_execution_estimate(self, metadata: Dict[str, Any], extra: Dict[str, Any]) -> float:
        estimate = metadata.get('execution_time_estimate')
        if estimate is None:
            estimate = extra.get('execution_time_estimate')
        return estimate if estimate is not None else 0

    def _resolve_interface_type(self, metadata: Dict[str, Any], extra: Dict[str, Any]) -> Optional[str]:
        return metadata.get('interface_type') or extra.get('interface_type')

    def _resolve_timestamp(
        self,
        field: str,
        metadata: Dict[str, Any],
        extra: Dict[str, Any],
    ) -> str:
        return metadata.get(field) or extra.get(field) or DEFAULT_TIMESTAMP

    def _timestamp_or_none(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        try:
            return value.isoformat()
        except AttributeError:
            return None

    def _prepare_database_task(self, task_def: TaskDefinition) -> Dict[str, Any]:
        metadata = dict(task_def.task_metadata or {})
        if 'version' not in metadata and getattr(task_def, 'version', None):
            metadata['version'] = task_def.version

        extra = {
            'parameters': self._extract_parameters_from_spec(task_def.interface_spec),
            'task_definition_id': str(task_def.task_definition_id),
            'status': 'active' if getattr(task_def, 'is_active', True) else 'inactive',
            'created_at': self._timestamp_or_none(getattr(task_def, 'created_at', None)),
            'updated_at': self._timestamp_or_none(getattr(task_def, 'updated_at', None)),
        }

        return self._normalize_task(task_def.task_id, metadata, 'database', extra)

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
                await self._download_output_files(execution, framework_results)
                output_files = await file_service.get_execution_files(
                    execution_id=UUID(execution_id),
                    file_type='output'
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to download output files: %s", exc)

        provider_status = framework_results.get('status')
        normalized_status = self._normalize_status_value(provider_status)

        execution.output_data = {
            'binding_affinity': framework_results.get('binding_affinity'),
            'top_poses_count': framework_results.get('top_poses_count'),
            'computation_time': framework_results.get('computation_time'),
            'status': normalized_status or provider_status,
        }

        if isinstance(provider_status, str) and normalized_status != provider_status:
            execution.output_data['provider_status'] = provider_status

        execution.update_status(normalized_status or 'completed')
        execution = await self._save_execution(execution)

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
    
    def _resolve_download_provider(self, execution: TaskFrameworkExecution) -> Tuple[Optional[str], Dict[str, str], str]:
        metadata = self._get_framework_task(execution.task_id) or {}
        provider_name = str(metadata.get('provider', '') or '').lower()
        provider_type = str(metadata.get('provider_type', '') or '').lower()

        if provider_type == 'domestic' or provider_name == 'domestic':
            base_url = os.getenv("GNINA_SERVICE_URL") or "http://gnina-service:8080/api/v1/gnina"
            return base_url, {}, provider_name or provider_type or 'domestic'

        api_key = os.getenv("NEUROSNAP_API_KEY")
        if not api_key:
            raise RuntimeError("NEUROSNAP_API_KEY not configured for cloud provider downloads")

        return None, {"X-API-KEY": api_key}, provider_name or provider_type or 'cloud'

    def _resolve_download_url(self, base_url: Optional[str], url: str) -> Optional[str]:
        if url.startswith("http"):
            return url
        if not base_url:
            return None
        base = base_url.rstrip('/')
        if url.startswith('/'):
            return urljoin(base, url)
        return urljoin(f"{base}/", url)

    @staticmethod
    def _derive_output_identity(alias: str, resolved_url: str, job_id: str) -> Tuple[str, str]:
        parsed = urlparse(resolved_url)
        filename = Path(parsed.path).name or f"{alias or job_id}.bin"
        parameter_name = alias or Path(filename).stem
        return filename, parameter_name.replace('.', '_')

    @staticmethod
    def _guess_content_type(filename: str) -> str:
        suffix = filename.lower()
        if suffix.endswith('.csv'):
            return 'text/csv'
        if suffix.endswith('.sdf'):
            return 'chemical/x-mdl-sdfile'
        if suffix.endswith('.pdbqt'):
            return 'chemical/x-pdbqt'
        if suffix.endswith('.pdb'):
            return 'chemical/x-pdb'
        return 'application/octet-stream'

    async def _handle_completed_transition(
        self,
        execution_id: str,
        execution: TaskFrameworkExecution,
        framework_status: Dict[str, Any],
        normalized_status: Optional[str],
    ) -> None:
        if normalized_status != 'completed':
            return

        logger.info(
            "Job %s completed, downloading output files",
            execution_id,
        )
        try:
            await self._download_output_files(execution, framework_status)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to download output files for %s: %s",
                execution_id,
                exc,
            )

    async def _update_execution_status_from_provider(
        self,
        execution_id: str,
        execution: TaskFrameworkExecution,
        framework_status: Dict[str, Any],
    ) -> Tuple[Optional[str], Optional[str]]:
        provider_status = framework_status.get('status')
        normalized_status = self._normalize_status_value(provider_status)

        if normalized_status and execution.status != normalized_status:
            execution.update_status(normalized_status)
            execution = await self._save_execution(execution)
            await self._handle_completed_transition(execution_id, execution, framework_status, normalized_status)

        return provider_status, normalized_status

    async def _download_output_files(self, execution: TaskFrameworkExecution, framework_results: Dict[str, Any]) -> None:
        """Download output files from a provider and persist them locally.

        Supports both NeuroSnap (cloud) and domestic providers (e.g., GNINA).
        Files are downloaded as soon as a job completes so links remain valid.
        """
        from .execution_file_service import ExecutionFileService

        download_urls = framework_results.get('download_urls', {})
        if not download_urls:
            logger.info("No download URLs found for execution %s", execution.execution_id)
            return

        job_id = framework_results.get('job_id')
        if not job_id:
            logger.error("No job_id found in framework_results for execution %s", execution.execution_id)
            return

        try:
            base_url, base_headers, provider_label = self._resolve_download_provider(execution)
        except RuntimeError as exc:
            logger.warning("%s; skipping output download for execution %s", exc, execution.execution_id)
            return

        logger.info(
            "Downloading %s output file(s) for execution %s from provider %s",
            len(download_urls),
            execution.execution_id,
            provider_label or "unknown",
        )

        file_service = ExecutionFileService()
        import httpx

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            for alias, url in download_urls.items():
                resolved_url = self._resolve_download_url(base_url, url) if url else None
                if not resolved_url:
                    logger.warning(
                        "Skipping download for execution %s because URL '%s' cannot be resolved",
                        execution.execution_id,
                        url,
                    )
                    continue

                filename, parameter_name = self._derive_output_identity(alias, resolved_url, job_id)
                request_headers = dict(base_headers)

                try:
                    logger.info("Downloading %s from %s", filename, resolved_url)
                    response = await client.get(resolved_url, headers=request_headers)
                    response.raise_for_status()
                    await file_service.store_output_file_content(
                        execution_id=execution.execution_id,
                        parameter_name=parameter_name,
                        filename=filename,
                        content=response.content,
                        content_type=self._guess_content_type(filename),
                        org_id=execution.org_id,
                    )
                    logger.info(
                        "Stored %s (%s bytes) for execution %s",
                        filename,
                        len(response.content),
                        execution.execution_id,
                    )
                except httpx.HTTPStatusError as exc:
                    logger.error(
                        "Failed to download %s (HTTP %s) from %s",
                        filename,
                        exc.response.status_code,
                        resolved_url,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to download or store output file %s: %s", filename, exc)
    
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
            
            return [self._prepare_database_task(td) for td in task_definitions]
    
    async def _get_database_task(self, task_id: str, org_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Get a specific task from database by task_id"""
        async for db in get_db():
            query = select(TaskDefinition).where(TaskDefinition.task_id == task_id)
            
            if org_id:
                query = query.where(TaskDefinition.org_id == org_id)
            
            result = await db.execute(query)
            td = result.scalars().first()
            
            if td:
                return self._prepare_database_task(td)

            return None
    
    def _get_framework_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks from framework"""
        try:
            framework_tasks = self.task_framework.get_available_tasks()
            
            tasks = []
            for task_id, task_info in framework_tasks.items():
                tasks.append(self._normalize_task(task_id, task_info, 'framework'))

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
                return self._normalize_task(task_id, task_info, 'framework')

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
        
        execution = await self._save_execution(execution)
        
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
            execution = await self._save_execution(execution)
        
        try:
            # Execute through framework - pass execution object and task definition
            external_job_id = await self.task_framework.execute_task(
                task_id, execution, task_definition.task_metadata
            )
            
            # Update execution with external job ID
            execution.external_job_id = external_job_id
            execution.status = 'running'
            execution.started_at = datetime.now(timezone.utc)
            execution = await self._save_execution(execution)
            
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
            execution = await self._save_execution(execution)
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
    
    async def _save_execution(self, execution: TaskFrameworkExecution) -> TaskFrameworkExecution:
        """Save execution to database and return a managed instance."""
        async for db in get_db():
            merged = await db.merge(execution)
            await db.commit()
            await db.refresh(merged)
            return merged
    
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
        normalized_status = self._normalize_status_value(execution.status)
        payload = {
            'execution_id': str(execution.execution_id),
            'task_id': execution.task_id,
            'status': normalized_status or execution.status,
            'created_at': execution.created_at.isoformat() if execution.created_at else None,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'error_message': execution.error_message,
            'external_job_id': execution.external_job_id,
            'progress': execution.progress_percentage,
        }

        if normalized_status and normalized_status != execution.status:
            payload['provider_status'] = execution.status

        return payload

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

        provider_status, normalized_status = await self._update_execution_status_from_provider(
            execution_id,
            execution,
            framework_status,
        )

        normalized_framework_status = dict(framework_status)
        if normalized_status is not None:
            normalized_framework_status['status_normalized'] = normalized_status

        canonical_status = self._normalize_status_value(execution.status) or execution.status

        status_dict.update(
            {
                'status': canonical_status,
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'progress': framework_status.get('progress', execution.progress_percentage),
                'message': framework_status.get('message'),
                'framework_status': normalized_framework_status,
            }
        )

        canonical_lower = (canonical_status or '').lower() if isinstance(canonical_status, str) else ''
        if isinstance(provider_status, str) and provider_status.lower() != canonical_lower:
            status_dict['provider_status'] = provider_status

        return status_dict


# Global instance
unified_task_service = UnifiedTaskService()
