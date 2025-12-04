"""Service for managing execution file storage and metadata."""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..adapters.storage.file_storage import FileStorageAdapter
from ..infrastructure.database import get_metadata_session

logger = logging.getLogger(__name__)


class ExecutionFileService:
    """Service for handling file storage and metadata for task executions."""
    
    def __init__(self, storage_adapter: Optional[FileStorageAdapter] = None):
        """
        Initialize execution file service.
        
        Args:
            storage_adapter: Storage adapter for file operations (defaults to FileStorageAdapter)
        """
        self.storage_adapter = storage_adapter or FileStorageAdapter()
    
    async def store_input_file(
        self,
        execution_id: UUID,
        parameter_name: str,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
        org_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Store an input file and create database record.
        
        Args:
            execution_id: ID of the task execution
            parameter_name: Name of the parameter (e.g., 'receptor_file')
            filename: Original filename
            content: File content as bytes
            content_type: MIME type of the file
            org_id: Organization ID for path organization
            
        Returns:
            Dictionary with file metadata including file_id
        """
        # Calculate checksums for integrity
        md5_hash = hashlib.md5(content).hexdigest()
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Generate storage path
        storage_backend = os.getenv('STORAGE_BACKEND', 'local')
        storage_path = self._generate_storage_path(
            org_id=org_id,
            execution_id=execution_id,
            filename=filename
        )
        
        # Store file to storage backend
        try:
            # For local storage, ensure directory exists
            if storage_backend == 'local':
                storage_dir = Path(f"/storage{storage_path}").parent
                storage_dir.mkdir(parents=True, exist_ok=True)
                
                # Write file asynchronously
                import aiofiles
                async with aiofiles.open(f"/storage{storage_path}", 'wb') as f:
                    await f.write(content)
                
                logger.info(f"Stored file to local storage: {storage_path}")
            
            # S3/MinIO storage support to be added in future
            # elif storage_backend == 's3':
            #     await self.s3_adapter.store_file(storage_path, content)
            
        except Exception as e:
            logger.error(f"Failed to store file {filename}: {e}")
            raise
        
        # Create database record
        file_record = await self._create_file_record(
            execution_id=execution_id,
            parameter_name=parameter_name,
            file_type='input',
            filename=filename,
            size_bytes=len(content),
            content_type=content_type,
            storage_backend=storage_backend,
            storage_path=storage_path,
            md5_hash=md5_hash,
            sha256_hash=sha256_hash
        )
        
        return file_record
    
    async def store_output_file(
        self,
        execution_id: UUID,
        parameter_name: str,
        filename: str,
        download_url: str,
        size_bytes: int = 0,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store metadata for an output file (typically external NeuroSnap URLs).
        DEPRECATED: Use store_output_file_content instead to download and store files locally.
        
        Args:
            execution_id: ID of the task execution
            parameter_name: Name of the output (e.g., 'output_sdf')
            filename: Filename of the result
            download_url: External download URL (NeuroSnap)
            size_bytes: File size in bytes
            content_type: MIME type
            
        Returns:
            Dictionary with file metadata
        """
        file_record = await self._create_file_record(
            execution_id=execution_id,
            parameter_name=parameter_name,
            file_type='output',
            filename=filename,
            size_bytes=size_bytes,
            content_type=content_type,
            storage_backend='neurosnap_cloud',
            storage_path='',  # Not applicable for external URLs
            download_url=download_url
        )
        
        return file_record
    
    async def store_output_file_content(
        self,
        execution_id: UUID,
        parameter_name: str,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
        org_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Download and store an output file locally (same as input files).
        
        Args:
            execution_id: ID of the task execution
            parameter_name: Name of the output (e.g., 'output_sdf')
            filename: Filename of the result
            content: File content as bytes
            content_type: MIME type
            org_id: Organization ID for path organization
            
        Returns:
            Dictionary with file metadata including file_id
        """
        # Calculate checksums for integrity
        md5_hash = hashlib.md5(content).hexdigest()
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Generate storage path
        storage_backend = os.getenv('STORAGE_BACKEND', 'local')
        storage_path = self._generate_storage_path(
            org_id=org_id,
            execution_id=execution_id,
            filename=filename
        )
        
        # Store file to storage backend
        try:
            # For local storage, ensure directory exists
            if storage_backend == 'local':
                storage_dir = Path(f"/storage{storage_path}").parent
                storage_dir.mkdir(parents=True, exist_ok=True)
                
                # Write file asynchronously
                import aiofiles
                async with aiofiles.open(f"/storage{storage_path}", 'wb') as f:
                    await f.write(content)
                
                logger.info(f"Stored output file to local storage: {storage_path}")
            
        except Exception as e:
            logger.error(f"Failed to store output file {filename}: {e}")
            raise
        
        # Create database record
        file_record = await self._create_file_record(
            execution_id=execution_id,
            parameter_name=parameter_name,
            file_type='output',
            filename=filename,
            size_bytes=len(content),
            content_type=content_type,
            storage_backend=storage_backend,
            storage_path=storage_path,
            md5_hash=md5_hash,
            sha256_hash=sha256_hash
        )
        
        return file_record
    
    async def get_execution_files(
        self,
        execution_id: UUID,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all files associated with an execution.
        
        Args:
            execution_id: ID of the task execution
            file_type: Filter by 'input' or 'output' (optional)
            
        Returns:
            List of file metadata dictionaries
        """
        async for db in get_metadata_session():
            query = text("""
                SELECT file_id, execution_id, parameter_name, file_type, 
                       filename, size_bytes, content_type, storage_backend,
                       storage_path, download_url, md5_hash, sha256_hash,
                       uploaded_at, expires_at, created_at
                FROM execution_files
                WHERE execution_id = :execution_id
            """)
            
            if file_type:
                query = text("""
                    SELECT file_id, execution_id, parameter_name, file_type, 
                           filename, size_bytes, content_type, storage_backend,
                           storage_path, download_url, md5_hash, sha256_hash,
                           uploaded_at, expires_at, created_at
                    FROM execution_files
                    WHERE execution_id = :execution_id AND file_type = :file_type
                """)
                result = await db.execute(query, {
                    'execution_id': str(execution_id),
                    'file_type': file_type
                })
            else:
                result = await db.execute(query, {'execution_id': str(execution_id)})
            
            rows = result.fetchall()
            
            return [
                {
                    'file_id': row[0],
                    'execution_id': row[1],
                    'parameter_name': row[2],
                    'file_type': row[3],
                    'filename': row[4],
                    'size': row[5],
                    'content_type': row[6],
                    'storage_backend': row[7],
                    'storage_path': row[8],
                    'url': row[9] if row[9] else self._get_download_url(row[7], row[8]),
                    'md5_hash': row[10],
                    'sha256_hash': row[11],
                    'uploaded_at': row[12].isoformat() if row[12] else None,
                    'expires_at': row[13].isoformat() if row[13] else None
                }
                for row in rows
            ]
    
    async def get_file_content(
        self,
        file_id: UUID
    ) -> Optional[bytes]:
        """
        Retrieve file content from storage.
        
        Args:
            file_id: ID of the file record
            
        Returns:
            File content as bytes, or None if not found
        """
        async for db in get_metadata_session():
            query = text("""
                SELECT storage_backend, storage_path, download_url
                FROM execution_files
                WHERE file_id = :file_id
            """)
            result = await db.execute(query, {'file_id': str(file_id)})
            row = result.fetchone()
            
            if not row:
                return None
            
            storage_backend, storage_path, _ = row
            
            # For local storage, read from filesystem
            if storage_backend == 'local':
                try:
                    import aiofiles
                    async with aiofiles.open(f"/storage{storage_path}", 'rb') as f:
                        return await f.read()
                except Exception as e:
                    logger.error(f"Failed to read file {storage_path}: {e}")
                    return None
            
            # For external URLs (NeuroSnap), would need to download
            # This is typically not needed as we return URLs directly
            elif storage_backend == 'neurosnap_cloud':
                logger.warning("Cannot retrieve content from external NeuroSnap URL")
                return None
            
            return None
    
    async def get_file(
        self,
        file_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get file metadata by file_id.
        
        Args:
            file_id: UUID of the file
            
        Returns:
            Dictionary with file metadata or None if not found
        """
        async for db in get_metadata_session():
            query = text("""
                SELECT file_id, execution_id, parameter_name, file_type, 
                       filename, size_bytes, content_type, storage_backend,
                       storage_path, download_url, md5_hash, sha256_hash,
                       uploaded_at, expires_at
                FROM execution_files
                WHERE file_id = :file_id
            """)
            
            result = await db.execute(query, {'file_id': file_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            return {
                'file_id': row[0],
                'execution_id': row[1],
                'parameter_name': row[2],
                'file_type': row[3],
                'filename': row[4],
                'size_bytes': row[5],
                'content_type': row[6],
                'storage_backend': row[7],
                'storage_path': row[8],
                'download_url': row[9],
                'md5_hash': row[10],
                'sha256_hash': row[11],
                'uploaded_at': row[12].isoformat() if row[12] else None,
                'expires_at': row[13].isoformat() if row[13] else None
            }
    
    async def get_file_by_execution_and_param(
        self,
        execution_id: str,
        parameter_name: str,
        file_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get file metadata by execution_id, parameter_name, and file_type.
        
        Args:
            execution_id: UUID of the execution
            parameter_name: Parameter name (e.g., 'receptor_file', 'output_csv')
            file_type: 'input' or 'output'
            
        Returns:
            Dictionary with file metadata or None if not found
        """
        async for db in get_metadata_session():
            query = text("""
                SELECT file_id, execution_id, parameter_name, file_type, 
                       filename, size_bytes, content_type, storage_backend,
                       storage_path, download_url, md5_hash, sha256_hash,
                       uploaded_at, expires_at
                FROM execution_files
                WHERE execution_id = :execution_id 
                  AND parameter_name = :parameter_name
                  AND file_type = :file_type
                LIMIT 1
            """)
            
            result = await db.execute(query, {
                'execution_id': execution_id,
                'parameter_name': parameter_name,
                'file_type': file_type
            })
            row = result.fetchone()
            
            if not row:
                return None
            
            return {
                'file_id': row[0],
                'execution_id': row[1],
                'parameter_name': row[2],
                'file_type': row[3],
                'filename': row[4],
                'size_bytes': row[5],
                'content_type': row[6],
                'storage_backend': row[7],
                'storage_path': row[8],
                'download_url': row[9],
                'md5_hash': row[10],
                'sha256_hash': row[11],
                'uploaded_at': row[12].isoformat() if row[12] else None,
                'expires_at': row[13].isoformat() if row[13] else None
            }

    async def delete_execution_files(self, execution_id: UUID) -> Dict[str, Any]:
        """Remove all file records and storage artifacts tied to an execution."""

        deleted_records = 0
        failed_paths: List[str] = []

        async for db in get_metadata_session():
            query = text(
                """
                SELECT file_id, storage_backend, storage_path
                FROM execution_files
                WHERE execution_id = :execution_id
                """
            )
            result = await db.execute(query, {"execution_id": str(execution_id)})
            rows = result.fetchall()

            if not rows:
                return {"deleted": 0, "failed": 0}

            storage_paths = {
                row[2]
                for row in rows
                if row[1] == 'local' and row[2]
            }

            for storage_path in storage_paths:
                if not self._safe_remove(storage_path):
                    failed_paths.append(storage_path)

            await db.execute(
                text("DELETE FROM execution_files WHERE execution_id = :execution_id"),
                {"execution_id": str(execution_id)}
            )
            await db.commit()

            deleted_records = len(rows)
            break

        return {"deleted": deleted_records, "failed": len(failed_paths)}
    
    def _generate_storage_path(
        self,
        org_id: Optional[UUID],
        execution_id: UUID,
        filename: str
    ) -> str:
        """
        Generate storage path for a file.
        
        Format: /uploads/{org_id}/{execution_id}/{filename}
        """
        org_part = str(org_id) if org_id else 'system'
        return f"/uploads/{org_part}/{execution_id}/{filename}"
    
    def _get_download_url(
        self,
        storage_backend: str,
        storage_path: str
    ) -> Optional[str]:
        """Generate download URL based on storage backend."""
        if storage_backend == 'local':
            # Use nginx storage service URL
            base_url = os.getenv('STORAGE_BASE_URL', 'http://storage:8080')
            return f"{base_url}{storage_path}"
        
        # For S3, MinIO, etc., would generate presigned URLs here
        return None

    def _safe_remove(self, storage_path: str) -> bool:
        """Delete a file from local storage and prune empty directories."""
        if not storage_path:
            return True

        storage_root = Path(os.getenv('STORAGE_ROOT', '/storage')).resolve()
        absolute_path = (storage_root / storage_path.lstrip('/')).resolve()

        try:
            if storage_root not in absolute_path.parents and absolute_path != storage_root:
                logger.warning("Refusing to remove path outside storage root: %s", absolute_path)
                return False

            if not absolute_path.exists():
                return True

            try:
                absolute_path.unlink()
            except PermissionError:
                try:
                    absolute_path.chmod(0o600)
                    absolute_path.unlink()
                except Exception as exc:
                    logger.warning("Failed to remove stored file '%s': %s", absolute_path, exc)
                    return False

            self._cleanup_empty_dirs(absolute_path.parent, storage_root)
            return True
        except Exception as exc:  # pragma: no cover - best effort cleanup
            logger.warning("Failed to remove stored file '%s': %s", absolute_path, exc)
            return False

    def _cleanup_empty_dirs(self, start: Path, root: Path) -> None:
        """Remove empty directories up to the storage root."""
        current = start
        try:
            while current.is_dir() and current != root:
                if any(current.iterdir()):
                    break
                current.rmdir()
                current = current.parent
        except Exception as exc:  # pragma: no cover - best effort cleanup
            logger.debug("Failed to prune directory '%s': %s", current, exc)
    
    async def _create_file_record(
        self,
        execution_id: UUID,
        parameter_name: str,
        file_type: str,
        filename: str,
        size_bytes: int,
        storage_backend: str,
        storage_path: str,
        content_type: Optional[str] = None,
        download_url: Optional[str] = None,
        md5_hash: Optional[str] = None,
        sha256_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update execution_files database record."""
        file_id = uuid4()
        
        async for db in get_metadata_session():
            query = text("""
                INSERT INTO execution_files (
                    file_id, execution_id, parameter_name, file_type,
                    filename, size_bytes, content_type, storage_backend,
                    storage_path, download_url, md5_hash, sha256_hash
                )
                VALUES (
                    :file_id, :execution_id, :parameter_name, :file_type,
                    :filename, :size_bytes, :content_type, :storage_backend,
                    :storage_path, :download_url, :md5_hash, :sha256_hash
                )
                ON CONFLICT (execution_id, parameter_name, file_type)
                DO UPDATE SET
                    filename = EXCLUDED.filename,
                    size_bytes = EXCLUDED.size_bytes,
                    content_type = EXCLUDED.content_type,
                    storage_backend = EXCLUDED.storage_backend,
                    storage_path = EXCLUDED.storage_path,
                    download_url = EXCLUDED.download_url,
                    md5_hash = EXCLUDED.md5_hash,
                    sha256_hash = EXCLUDED.sha256_hash,
                    uploaded_at = CURRENT_TIMESTAMP
                RETURNING file_id, filename, size_bytes, content_type,
                          storage_backend, storage_path, download_url
            """)
            
            result = await db.execute(query, {
                'file_id': str(file_id),
                'execution_id': str(execution_id),
                'parameter_name': parameter_name,
                'file_type': file_type,
                'filename': filename,
                'size_bytes': size_bytes,
                'content_type': content_type,
                'storage_backend': storage_backend,
                'storage_path': storage_path,
                'download_url': download_url,
                'md5_hash': md5_hash,
                'sha256_hash': sha256_hash
            })
            
            await db.commit()
            
            row = result.fetchone()
            return {
                'file_id': str(row[0]),
                'filename': row[1],
                'size': row[2],
                'content_type': row[3],
                'storage_backend': row[4],
                'storage_path': row[5],
                'url': row[6] if row[6] else self._get_download_url(row[4], row[5])
            }
