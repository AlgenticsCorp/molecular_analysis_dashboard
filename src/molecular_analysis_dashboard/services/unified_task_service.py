"""
Unified Task Service combining database task definitions with task framework
"""

from typing import Dict, List, Any, Optional, Union
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
        framework_tasks = await self._get_framework_tasks()
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
        framework_task = await self._get_framework_task(task_id)
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
        if await self._is_framework_task(task_id):
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
        """Get results of completed execution"""
        
        execution = await self._get_task_execution(execution_id)
        if execution:
            if execution.external_job_id:
                # Get results from framework
                framework_results = await self.task_framework.get_execution_results(
                    execution.task_id, execution.external_job_id
                )
                
                # Update database with results
                if framework_results:
                    execution.output_data = framework_results
                    execution.update_status('completed')
                    await self._save_execution(execution)
                
                return framework_results
            else:
                return execution.output_data
        
        return None
    
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
    
    async def _get_framework_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks from framework"""
        try:
            framework_tasks = await self.task_framework.get_available_tasks()
            
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
    
    async def _get_framework_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task from framework by task_id"""
        try:
            framework_tasks = await self.task_framework.get_available_tasks()
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
    
    async def _is_framework_task(self, task_id: str) -> bool:
        """Check if task is handled by framework"""
        framework_tasks = await self.task_framework.get_available_tasks()
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
        
        # Create execution record
        execution_id = uuid4()
        
        # Get task definition for database record
        task_definition = await self._get_or_create_framework_task_definition(
            task_id, org_id
        )
        
        # Merge parameters and files into input_data
        input_data = {**parameters}
        if files:
            # Store complete file information in input_data (including content as base64)
            import base64
            for key, file_info in files.items():
                content = file_info.get('content', b'')
                input_data[key] = {
                    'filename': file_info.get('filename'),
                    'content_type': file_info.get('content_type'),
                    'size': len(content),
                    'content_base64': base64.b64encode(content).decode('utf-8')
                }
        
        # Create execution record using actual table columns
        execution = TaskFrameworkExecution(
            execution_id=execution_id,
            task_id=task_id,
            display_name=task_definition.task_metadata.get('name', task_id),
            org_id=org_id or SYSTEM_ORG_ID,  # Use system org ID if none provided
            user_id=user_id or SYSTEM_ORG_ID,  # Use system org ID if no user
            status='pending',
            input_data=input_data
        )
        
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
            framework_task = await self._get_framework_task(task_id)
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
            if not execution:
                return None
            
            status_dict = {
                'execution_id': str(execution.execution_id),
                'task_id': execution.task_id,
                'status': execution.status,
                'created_at': execution.created_at.isoformat() if execution.created_at else None,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'error_message': execution.error_message,
                'external_job_id': execution.external_job_id,
                'progress': execution.progress_percentage
            }
            
            # If there's an external job ID, get status from framework
            if execution.external_job_id and execution.task_id:
                try:
                    framework_status = await self.task_framework.get_execution_status(
                        execution.task_id,
                        execution.external_job_id
                    )
                    
                    # Update database if status changed
                    if framework_status and framework_status.get('status') != execution.status:
                        execution.update_status(framework_status['status'])
                        await self._save_execution(execution)
                    
                    # Merge framework status
                    if framework_status:
                        status_dict.update({
                            'progress': framework_status.get('progress', execution.progress_percentage),
                            'message': framework_status.get('message'),
                            'framework_status': framework_status
                        })
                        
                except Exception as e:
                    logger.error(f"Error getting framework status: {e}")
            
            return status_dict
            
        except Exception as e:
            logger.error(f"Error getting execution status: {e}")
            return None


# Global instance
unified_task_service = UnifiedTaskService()
