# Storage Adapter Implementation

## Overview

The storage adapter provides a **pluggable file storage architecture** that supports local filesystem (development) and cloud object storage (production) with consistent interfaces, metadata tracking, and organized artifact management.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Use Cases Layer                              │
├─────────────────────────────────────────────────────────────────┤
│               StoragePort (Interface)                           │
├─────────────────────────────────────────────────────────────────┤
│                    Adapters Layer                               │
│  ┌──────────────────┐ ┌──────────────────┐ ┌─────────────────┐  │
│  │LocalStorage      │ │S3StorageAdapter  │ │MinIOAdapter     │  │
│  │Adapter           │ │                  │ │                 │  │
│  │                  │ │• AWS S3          │ │• Self-hosted    │  │
│  │• Local FS        │ │• IAM Roles       │ │• S3 Compatible  │  │
│  │• Directory Org   │ │• Bucket Policies │ │• Development    │  │
│  │• File Metadata   │ │• Versioning      │ │• Testing        │  │
│  └──────────────────┘ └──────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## File Organization Strategy

### Hierarchical Structure

```
storage_root/
├── organizations/
│   ├── org_001/
│   │   ├── jobs/
│   │   │   ├── job_123e4567-e89b-12d3-a456-426614174000/
│   │   │   │   ├── inputs/
│   │   │   │   │   ├── receptor.pdbqt           # Original receptor file
│   │   │   │   │   ├── ligand.sdf               # Original ligand file
│   │   │   │   │   └── metadata.json            # Input metadata
│   │   │   │   ├── outputs/
│   │   │   │   │   ├── vina_result.pdbqt        # Docking results
│   │   │   │   │   ├── vina_execution.log       # Engine logs
│   │   │   │   │   ├── scores.json              # Parsed scores
│   │   │   │   │   └── analysis_report.pdf      # Generated reports
│   │   │   │   ├── intermediate/
│   │   │   │   │   ├── preprocessed_receptor.pdbqt
│   │   │   │   │   └── converted_ligand.pdbqt
│   │   │   │   └── metadata.json                # Job-level metadata
│   │   │   └── job_456.../
│   │   ├── molecules/
│   │   │   ├── receptors/
│   │   │   │   ├── protein_001.pdbqt
│   │   │   │   └── protein_002.pdbqt
│   │   │   └── ligands/
│   │   │       ├── compound_001.sdf
│   │   │       └── compound_002.mol2
│   │   └── cache/
│   │       ├── input_signatures/
│   │       │   └── sha256_hash.json             # Cached results
│   │       └── processed_molecules/
│   │           └── converted_files/
│   └── org_002/
│       └── ...
├── shared/
│   ├── templates/                               # Shared templates
│   └── reference_data/                          # Reference datasets
└── system/
    ├── logs/                                   # System logs
    └── backups/                                # Backup metadata
```

### Path Templates

```python
# File path generation patterns
PATH_TEMPLATES = {
    "job_input": "{org_id}/jobs/{job_id}/inputs/{filename}",
    "job_output": "{org_id}/jobs/{job_id}/outputs/{filename}",
    "job_intermediate": "{org_id}/jobs/{job_id}/intermediate/{filename}",
    "job_metadata": "{org_id}/jobs/{job_id}/metadata.json",
    "molecule_receptor": "{org_id}/molecules/receptors/{molecule_id}.{ext}",
    "molecule_ligand": "{org_id}/molecules/ligands/{molecule_id}.{ext}",
    "cache_signature": "{org_id}/cache/input_signatures/{signature_hash}.json",
    "processed_molecule": "{org_id}/cache/processed_molecules/{molecule_id}_{version}.{ext}"
}
```

## Storage Port Interface

```python
# ports/storage_port.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import asyncio
from enum import Enum

class ArtifactType(Enum):
    """Types of artifacts stored in the system."""
    RECEPTOR = "receptor"
    LIGAND = "ligand"
    DOCKING_RESULT = "docking_result"
    EXECUTION_LOG = "execution_log"
    ANALYSIS_REPORT = "analysis_report"
    PREPROCESSED_FILE = "preprocessed_file"
    CACHE_ENTRY = "cache_entry"
    JOB_METADATA = "job_metadata"

@dataclass
class StorageMetadata:
    """Metadata associated with stored files."""
    file_path: str                          # Logical path in storage
    original_filename: str                  # Original filename from upload
    content_type: str                       # MIME type
    size_bytes: int                         # File size
    checksum_sha256: str                   # SHA256 hash for integrity
    created_at: datetime                   # Upload timestamp

    # Artifact classification
    artifact_type: ArtifactType            # Type of artifact
    job_id: Optional[str] = None           # Associated job ID
    molecule_id: Optional[str] = None      # Associated molecule ID

    # Storage backend info
    backend_type: str = None               # local, s3, minio
    backend_path: str = None               # Physical path/key in backend

    # Custom metadata
    custom_metadata: Dict[str, Any] = None # Additional key-value metadata

@dataclass
class UploadRequest:
    """Request to upload a file to storage."""
    org_id: str                            # Organization ID
    file_content: bytes                    # File content to upload
    filename: str                          # Desired filename
    artifact_type: ArtifactType           # Type of artifact

    # Optional associations
    job_id: Optional[str] = None          # Associated job
    molecule_id: Optional[str] = None     # Associated molecule

    # Custom metadata
    metadata: Dict[str, Any] = None       # Additional metadata

    # Upload options
    overwrite: bool = False               # Allow overwriting existing files
    content_type: Optional[str] = None    # Override content type detection

@dataclass
class DownloadResponse:
    """Response from file download."""
    content: bytes                        # File content
    metadata: StorageMetadata            # File metadata

class StoragePort(ABC):
    """Abstract interface for file storage operations."""

    @abstractmethod
    async def upload_file(self, request: UploadRequest) -> StorageMetadata:
        """
        Upload a file to storage.

        Args:
            request: Upload request with file content and metadata

        Returns:
            StorageMetadata for the uploaded file

        Raises:
            StorageError: If upload fails
            FileExistsError: If file exists and overwrite=False
        """
        pass

    @abstractmethod
    async def download_file(self, org_id: str, file_path: str) -> DownloadResponse:
        """
        Download a file from storage.

        Args:
            org_id: Organization ID
            file_path: Logical file path

        Returns:
            DownloadResponse with file content and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If download fails
        """
        pass

    @abstractmethod
    async def get_file_metadata(self, org_id: str, file_path: str) -> StorageMetadata:
        """
        Get metadata for a file without downloading content.

        Args:
            org_id: Organization ID
            file_path: Logical file path

        Returns:
            StorageMetadata for the file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    async def delete_file(self, org_id: str, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            org_id: Organization ID
            file_path: Logical file path

        Returns:
            True if file was deleted, False if not found

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def list_files(
        self,
        org_id: str,
        prefix: str = "",
        artifact_type: Optional[ArtifactType] = None,
        job_id: Optional[str] = None
    ) -> List[StorageMetadata]:
        """
        List files matching criteria.

        Args:
            org_id: Organization ID
            prefix: Path prefix filter
            artifact_type: Filter by artifact type
            job_id: Filter by job ID

        Returns:
            List of StorageMetadata for matching files
        """
        pass

    @abstractmethod
    async def generate_upload_url(
        self,
        org_id: str,
        file_path: str,
        content_type: str,
        expires_in_seconds: int = 3600
    ) -> str:
        """
        Generate a pre-signed upload URL (for direct client uploads).

        Args:
            org_id: Organization ID
            file_path: Target file path
            content_type: Expected content type
            expires_in_seconds: URL expiration time

        Returns:
            Pre-signed upload URL

        Note:
            Not all storage backends support this feature
        """
        pass

    @abstractmethod
    async def generate_download_url(
        self,
        org_id: str,
        file_path: str,
        expires_in_seconds: int = 3600
    ) -> str:
        """
        Generate a pre-signed download URL.

        Args:
            org_id: Organization ID
            file_path: File path to download
            expires_in_seconds: URL expiration time

        Returns:
            Pre-signed download URL
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check storage backend health.

        Returns:
            Dict with health status and backend info
        """
        pass
```

## Local Storage Adapter Implementation

```python
# adapters/storage/local_storage_adapter.py
import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
import aiofiles
import aiofiles.os

from ports.storage_port import (
    StoragePort, StorageMetadata, UploadRequest, DownloadResponse, ArtifactType
)
from infrastructure.config import get_storage_settings

logger = logging.getLogger(__name__)

class LocalStorageAdapter(StoragePort):
    """Local filesystem storage adapter."""

    def __init__(self):
        self.settings = get_storage_settings()
        self.base_path = Path(self.settings.uploads_dir)
        self.results_path = Path(self.settings.results_dir)

        # Ensure base directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(parents=True, exist_ok=True)

        # Path templates for file organization
        self.path_templates = {
            ArtifactType.RECEPTOR: "organizations/{org_id}/molecules/receptors/{filename}",
            ArtifactType.LIGAND: "organizations/{org_id}/molecules/ligands/{filename}",
            ArtifactType.DOCKING_RESULT: "organizations/{org_id}/jobs/{job_id}/outputs/{filename}",
            ArtifactType.EXECUTION_LOG: "organizations/{org_id}/jobs/{job_id}/outputs/{filename}",
            ArtifactType.ANALYSIS_REPORT: "organizations/{org_id}/jobs/{job_id}/outputs/{filename}",
            ArtifactType.PREPROCESSED_FILE: "organizations/{org_id}/jobs/{job_id}/intermediate/{filename}",
            ArtifactType.CACHE_ENTRY: "organizations/{org_id}/cache/{filename}",
            ArtifactType.JOB_METADATA: "organizations/{org_id}/jobs/{job_id}/metadata.json"
        }

    def _get_file_path(self, request: UploadRequest) -> Path:
        """Generate file path based on artifact type and organization."""
        template = self.path_templates.get(request.artifact_type)
        if not template:
            raise ValueError(f"No path template for artifact type: {request.artifact_type}")

        # Choose base directory based on artifact type
        if request.artifact_type in [ArtifactType.DOCKING_RESULT, ArtifactType.EXECUTION_LOG,
                                   ArtifactType.ANALYSIS_REPORT, ArtifactType.PREPROCESSED_FILE]:
            base_dir = self.results_path
        else:
            base_dir = self.base_path

        # Format path template
        relative_path = template.format(
            org_id=request.org_id,
            job_id=request.job_id or "unknown",
            molecule_id=request.molecule_id or "unknown",
            filename=request.filename
        )

        return base_dir / relative_path

    def _get_metadata_path(self, file_path: Path) -> Path:
        """Get metadata file path for a given file."""
        return file_path.with_suffix(file_path.suffix + '.metadata.json')

    async def _calculate_checksum(self, content: bytes) -> str:
        """Calculate SHA256 checksum of file content."""
        return hashlib.sha256(content).hexdigest()

    async def _save_metadata(self, metadata: StorageMetadata, metadata_path: Path):
        """Save metadata to disk."""
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        metadata_dict = {
            "file_path": metadata.file_path,
            "original_filename": metadata.original_filename,
            "content_type": metadata.content_type,
            "size_bytes": metadata.size_bytes,
            "checksum_sha256": metadata.checksum_sha256,
            "created_at": metadata.created_at.isoformat(),
            "artifact_type": metadata.artifact_type.value,
            "job_id": metadata.job_id,
            "molecule_id": metadata.molecule_id,
            "backend_type": metadata.backend_type,
            "backend_path": metadata.backend_path,
            "custom_metadata": metadata.custom_metadata or {}
        }

        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata_dict, indent=2))

    async def _load_metadata(self, metadata_path: Path) -> StorageMetadata:
        """Load metadata from disk."""
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        async with aiofiles.open(metadata_path, 'r') as f:
            content = await f.read()
            metadata_dict = json.loads(content)

        return StorageMetadata(
            file_path=metadata_dict["file_path"],
            original_filename=metadata_dict["original_filename"],
            content_type=metadata_dict["content_type"],
            size_bytes=metadata_dict["size_bytes"],
            checksum_sha256=metadata_dict["checksum_sha256"],
            created_at=datetime.fromisoformat(metadata_dict["created_at"]),
            artifact_type=ArtifactType(metadata_dict["artifact_type"]),
            job_id=metadata_dict.get("job_id"),
            molecule_id=metadata_dict.get("molecule_id"),
            backend_type=metadata_dict.get("backend_type"),
            backend_path=metadata_dict.get("backend_path"),
            custom_metadata=metadata_dict.get("custom_metadata")
        )

    async def upload_file(self, request: UploadRequest) -> StorageMetadata:
        """Upload file to local storage."""
        try:
            # Generate file path
            file_path = self._get_file_path(request)
            metadata_path = self._get_metadata_path(file_path)

            # Check if file exists and overwrite policy
            if file_path.exists() and not request.overwrite:
                raise FileExistsError(f"File already exists: {request.filename}")

            # Create directory structure
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Calculate checksum and detect content type
            checksum = await self._calculate_checksum(request.file_content)
            content_type = request.content_type or mimetypes.guess_type(request.filename)[0] or 'application/octet-stream'

            # Write file content
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(request.file_content)

            # Create metadata
            metadata = StorageMetadata(
                file_path=str(file_path.relative_to(self.base_path if file_path.is_relative_to(self.base_path) else self.results_path)),
                original_filename=request.filename,
                content_type=content_type,
                size_bytes=len(request.file_content),
                checksum_sha256=checksum,
                created_at=datetime.utcnow(),
                artifact_type=request.artifact_type,
                job_id=request.job_id,
                molecule_id=request.molecule_id,
                backend_type="local",
                backend_path=str(file_path),
                custom_metadata=request.metadata
            )

            # Save metadata
            await self._save_metadata(metadata, metadata_path)

            logger.info(f"Uploaded file: {request.filename} to {file_path}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to upload file {request.filename}: {e}")
            raise StorageError(f"Upload failed: {e}") from e

    async def download_file(self, org_id: str, file_path: str) -> DownloadResponse:
        """Download file from local storage."""
        try:
            # Find the actual file path (check both base directories)
            possible_paths = [
                self.base_path / file_path,
                self.results_path / file_path
            ]

            actual_file_path = None
            for path in possible_paths:
                if path.exists():
                    actual_file_path = path
                    break

            if not actual_file_path:
                raise FileNotFoundError(f"File not found: {file_path}")

            # Load metadata
            metadata_path = self._get_metadata_path(actual_file_path)
            metadata = await self._load_metadata(metadata_path)

            # Read file content
            async with aiofiles.open(actual_file_path, 'rb') as f:
                content = await f.read()

            # Verify checksum
            actual_checksum = await self._calculate_checksum(content)
            if actual_checksum != metadata.checksum_sha256:
                logger.warning(f"Checksum mismatch for {file_path}: expected {metadata.checksum_sha256}, got {actual_checksum}")

            return DownloadResponse(content=content, metadata=metadata)

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            raise StorageError(f"Download failed: {e}") from e

    async def get_file_metadata(self, org_id: str, file_path: str) -> StorageMetadata:
        """Get file metadata without downloading content."""
        try:
            # Find the actual file path
            possible_paths = [
                self.base_path / file_path,
                self.results_path / file_path
            ]

            actual_file_path = None
            for path in possible_paths:
                if path.exists():
                    actual_file_path = path
                    break

            if not actual_file_path:
                raise FileNotFoundError(f"File not found: {file_path}")

            # Load metadata
            metadata_path = self._get_metadata_path(actual_file_path)
            return await self._load_metadata(metadata_path)

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get metadata for {file_path}: {e}")
            raise StorageError(f"Metadata retrieval failed: {e}") from e

    async def delete_file(self, org_id: str, file_path: str) -> bool:
        """Delete file from local storage."""
        try:
            # Find the actual file path
            possible_paths = [
                self.base_path / file_path,
                self.results_path / file_path
            ]

            actual_file_path = None
            for path in possible_paths:
                if path.exists():
                    actual_file_path = path
                    break

            if not actual_file_path:
                return False  # File not found

            # Delete metadata file first
            metadata_path = self._get_metadata_path(actual_file_path)
            if metadata_path.exists():
                await aiofiles.os.remove(metadata_path)

            # Delete main file
            await aiofiles.os.remove(actual_file_path)

            # Clean up empty directories
            try:
                actual_file_path.parent.rmdir()
            except OSError:
                pass  # Directory not empty, that's fine

            logger.info(f"Deleted file: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise StorageError(f"Deletion failed: {e}") from e

    async def list_files(
        self,
        org_id: str,
        prefix: str = "",
        artifact_type: Optional[ArtifactType] = None,
        job_id: Optional[str] = None
    ) -> List[StorageMetadata]:
        """List files matching criteria."""
        try:
            files = []

            # Search in both directories
            search_dirs = [self.base_path, self.results_path]

            for base_dir in search_dirs:
                org_dir = base_dir / "organizations" / org_id
                if not org_dir.exists():
                    continue

                # Recursively find all .metadata.json files
                for metadata_path in org_dir.rglob("*.metadata.json"):
                    try:
                        metadata = await self._load_metadata(metadata_path)

                        # Apply filters
                        if prefix and not metadata.file_path.startswith(prefix):
                            continue

                        if artifact_type and metadata.artifact_type != artifact_type:
                            continue

                        if job_id and metadata.job_id != job_id:
                            continue

                        files.append(metadata)

                    except Exception as e:
                        logger.warning(f"Failed to load metadata from {metadata_path}: {e}")
                        continue

            # Sort by creation time (newest first)
            files.sort(key=lambda x: x.created_at, reverse=True)
            return files

        except Exception as e:
            logger.error(f"Failed to list files for org {org_id}: {e}")
            raise StorageError(f"File listing failed: {e}") from e

    async def generate_upload_url(
        self,
        org_id: str,
        file_path: str,
        content_type: str,
        expires_in_seconds: int = 3600
    ) -> str:
        """Generate upload URL (not supported for local storage)."""
        raise NotImplementedError("Local storage does not support pre-signed upload URLs")

    async def generate_download_url(
        self,
        org_id: str,
        file_path: str,
        expires_in_seconds: int = 3600
    ) -> str:
        """Generate download URL (not supported for local storage)."""
        raise NotImplementedError("Local storage does not support pre-signed download URLs")

    async def health_check(self) -> Dict[str, Any]:
        """Check local storage health."""
        try:
            # Check if directories are accessible and writable
            test_file = self.base_path / ".health_check"

            # Write test file
            async with aiofiles.open(test_file, 'w') as f:
                await f.write("health_check")

            # Read test file
            async with aiofiles.open(test_file, 'r') as f:
                content = await f.read()

            # Clean up test file
            await aiofiles.os.remove(test_file)

            # Check disk space
            disk_usage = shutil.disk_usage(self.base_path)

            return {
                "status": "healthy",
                "backend_type": "local",
                "base_path": str(self.base_path),
                "results_path": str(self.results_path),
                "disk_usage": {
                    "total_bytes": disk_usage.total,
                    "used_bytes": disk_usage.used,
                    "free_bytes": disk_usage.free,
                    "usage_percent": round((disk_usage.used / disk_usage.total) * 100, 2)
                },
                "readable": True,
                "writable": content == "health_check"
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "backend_type": "local",
                "error": str(e)
            }

# Custom exceptions
class StorageError(Exception):
    """Base storage error."""
    pass

class FileExistsError(StorageError):
    """File already exists error."""
    pass
```

## Storage Factory and Configuration

```python
# infrastructure/storage_factory.py
from typing import Dict, Type
from ports.storage_port import StoragePort
from adapters.storage.local_storage_adapter import LocalStorageAdapter
from adapters.storage.s3_storage_adapter import S3StorageAdapter
from adapters.storage.minio_storage_adapter import MinIOStorageAdapter
from infrastructure.config import get_storage_settings

class StorageFactory:
    """Factory for creating storage adapter instances."""

    _adapters: Dict[str, Type[StoragePort]] = {
        "local": LocalStorageAdapter,
        "s3": S3StorageAdapter,
        "minio": MinIOStorageAdapter,
    }

    @classmethod
    def create_storage_adapter(cls) -> StoragePort:
        """Create storage adapter based on configuration."""
        settings = get_storage_settings()
        adapter_class = cls._adapters.get(settings.storage_backend)

        if not adapter_class:
            raise ValueError(f"Unknown storage backend: {settings.storage_backend}")

        return adapter_class()

    @classmethod
    def register_adapter(cls, backend_name: str, adapter_class: Type[StoragePort]):
        """Register a custom storage adapter."""
        cls._adapters[backend_name] = adapter_class

# Singleton storage instance
_storage_adapter: StoragePort = None

def get_storage_adapter() -> StoragePort:
    """Get singleton storage adapter instance."""
    global _storage_adapter
    if _storage_adapter is None:
        _storage_adapter = StorageFactory.create_storage_adapter()
    return _storage_adapter
```

## Usage in Use Cases

```python
# use_cases/file_management_service.py
from typing import List
from pathlib import Path
from ports.storage_port import UploadRequest, ArtifactType, StorageMetadata
from infrastructure.storage_factory import get_storage_adapter

class FileManagementService:
    """Use case for managing files and artifacts."""

    def __init__(self):
        self.storage = get_storage_adapter()

    async def upload_molecule(
        self,
        org_id: str,
        file_content: bytes,
        filename: str,
        molecule_type: str,  # "receptor" or "ligand"
        molecule_id: str
    ) -> StorageMetadata:
        """Upload a molecule file (receptor or ligand)."""

        artifact_type = ArtifactType.RECEPTOR if molecule_type == "receptor" else ArtifactType.LIGAND

        request = UploadRequest(
            org_id=org_id,
            file_content=file_content,
            filename=filename,
            artifact_type=artifact_type,
            molecule_id=molecule_id,
            metadata={
                "molecule_type": molecule_type,
                "upload_source": "api"
            }
        )

        return await self.storage.upload_file(request)

    async def upload_job_result(
        self,
        org_id: str,
        job_id: str,
        file_content: bytes,
        filename: str,
        result_type: str  # "docking_result", "log", "report"
    ) -> StorageMetadata:
        """Upload a job result file."""

        type_mapping = {
            "docking_result": ArtifactType.DOCKING_RESULT,
            "log": ArtifactType.EXECUTION_LOG,
            "report": ArtifactType.ANALYSIS_REPORT
        }

        artifact_type = type_mapping.get(result_type, ArtifactType.DOCKING_RESULT)

        request = UploadRequest(
            org_id=org_id,
            file_content=file_content,
            filename=filename,
            artifact_type=artifact_type,
            job_id=job_id,
            metadata={
                "result_type": result_type,
                "generated_by": "docking_engine"
            }
        )

        return await self.storage.upload_file(request)

    async def get_job_files(self, org_id: str, job_id: str) -> List[StorageMetadata]:
        """Get all files associated with a job."""
        return await self.storage.list_files(org_id=org_id, job_id=job_id)

    async def download_file(self, org_id: str, file_path: str) -> bytes:
        """Download file content."""
        response = await self.storage.download_file(org_id, file_path)
        return response.content

    async def delete_job_files(self, org_id: str, job_id: str) -> int:
        """Delete all files associated with a job."""
        files = await self.get_job_files(org_id, job_id)
        deleted_count = 0

        for file_metadata in files:
            try:
                if await self.storage.delete_file(org_id, file_metadata.file_path):
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file_metadata.file_path}: {e}")

        return deleted_count
```

## API Integration

```python
# presentation/api/storage_router.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List
from use_cases.file_management_service import FileManagementService
from infrastructure.auth import get_current_org_id

router = APIRouter(prefix="/storage", tags=["storage"])

@router.post("/molecules/{molecule_type}")
async def upload_molecule(
    molecule_type: str,
    molecule_id: str,
    file: UploadFile = File(...),
    org_id: str = Depends(get_current_org_id),
    file_service: FileManagementService = Depends()
):
    """Upload a molecule file (receptor or ligand)."""
    if molecule_type not in ["receptor", "ligand"]:
        raise HTTPException(status_code=400, detail="Invalid molecule type")

    content = await file.read()

    try:
        metadata = await file_service.upload_molecule(
            org_id=org_id,
            file_content=content,
            filename=file.filename,
            molecule_type=molecule_type,
            molecule_id=molecule_id
        )

        return {
            "file_path": metadata.file_path,
            "size_bytes": metadata.size_bytes,
            "checksum": metadata.checksum_sha256,
            "uploaded_at": metadata.created_at.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

@router.get("/jobs/{job_id}/files")
async def list_job_files(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    file_service: FileManagementService = Depends()
):
    """List all files for a job."""
    try:
        files = await file_service.get_job_files(org_id, job_id)

        return {
            "job_id": job_id,
            "file_count": len(files),
            "files": [
                {
                    "file_path": f.file_path,
                    "filename": f.original_filename,
                    "artifact_type": f.artifact_type.value,
                    "size_bytes": f.size_bytes,
                    "created_at": f.created_at.isoformat()
                }
                for f in files
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File listing failed: {e}")
```

## Configuration Integration

Update `.env`:

```bash
# Storage Configuration
STORAGE_BACKEND=local
STORAGE_UPLOADS_DIR=/data/uploads
STORAGE_RESULTS_DIR=/data/results

# File Organization
STORAGE_FILE_PATH_TEMPLATE={org_id}/{job_id}/{artifact_type}/{filename}

# S3/MinIO Configuration (when STORAGE_BACKEND=s3 or minio)
STORAGE_S3_ENDPOINT_URL=http://minio:9000
STORAGE_S3_ACCESS_KEY=minioadmin
STORAGE_S3_SECRET_KEY=minioadmin
STORAGE_S3_BUCKET_NAME=mad-artifacts
STORAGE_S3_REGION=us-east-1
```

## Testing Strategy

```python
# tests/integration/test_storage_adapter.py
import pytest
import tempfile
from pathlib import Path
from adapters.storage.local_storage_adapter import LocalStorageAdapter
from ports.storage_port import UploadRequest, ArtifactType

@pytest.mark.integration
async def test_local_storage_upload_download():
    """Test local storage upload and download cycle."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Configure adapter with temp directory
        adapter = LocalStorageAdapter()
        adapter.base_path = Path(temp_dir)

        # Upload test file
        test_content = b"test molecule data"
        request = UploadRequest(
            org_id="test_org",
            file_content=test_content,
            filename="test_molecule.pdbqt",
            artifact_type=ArtifactType.RECEPTOR,
            molecule_id="mol_123"
        )

        metadata = await adapter.upload_file(request)
        assert metadata.size_bytes == len(test_content)
        assert metadata.original_filename == "test_molecule.pdbqt"

        # Download and verify
        download_response = await adapter.download_file("test_org", metadata.file_path)
        assert download_response.content == test_content
        assert download_response.metadata.checksum_sha256 == metadata.checksum_sha256

@pytest.mark.integration
async def test_storage_health_check():
    """Test storage health check."""
    adapter = get_storage_adapter()
    health = await adapter.health_check()

    assert "status" in health
    assert health["status"] in ["healthy", "unhealthy"]
```

This comprehensive storage adapter implementation provides:

1. **Pluggable architecture** with clear interface separation
2. **Organized file structure** with logical path templates
3. **Metadata tracking** for all stored files
4. **Local storage implementation** as the foundation
5. **Integration patterns** for use cases and API endpoints
6. **Configuration management** aligned with existing settings
7. **Testing strategies** for validation
8. **Extensibility** for adding S3/MinIO adapters following the same pattern

The storage system is designed to handle the molecular analysis workflow's file management needs while providing a foundation for scaling to cloud storage solutions.
