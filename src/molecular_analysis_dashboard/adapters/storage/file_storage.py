"""File storage adapter for local filesystem and container storage."""

import hashlib
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional
from uuid import UUID

import aiofiles

from ..ports.storage import StorageError, StoragePort

logger = logging.getLogger(__name__)


class FileStorageAdapter(StoragePort):
    """Local filesystem storage adapter implementation."""

    # Supported molecular file formats
    SUPPORTED_EXTENSIONS = {
        ".pdb",
        ".pdbqt",
        ".sdf",
        ".mol",
        ".mol2",
        ".xyz",
        ".cif",
        ".mmcif",
        ".cml",
        ".smiles",
    }

    SUPPORTED_MIME_TYPES = {
        "chemical/x-pdb",
        "chemical/x-sdf",
        "chemical/x-mol2",
        "chemical/x-xyz",
        "chemical/x-cif",
        "chemical/x-mmcif",
        "chemical/x-cml",
        "chemical/x-smiles",
        "text/plain",
        "application/octet-stream",
    }

    def __init__(self, storage_root: str = "/storage"):
        """
        Initialize file storage adapter.

        Args:
            storage_root: Root directory for file storage
        """
        self.storage_root = Path(storage_root)
        self.uploads_dir = self.storage_root / "uploads"
        self.results_dir = self.storage_root / "results"
        self.temp_dir = self.storage_root / "temp"

        # Create directories if they don't exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for directory in [self.uploads_dir, self.results_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")

    def _generate_file_path(self, file_name: str, organization_id: UUID, content_hash: str) -> Path:
        """
        Generate a unique file path for storage.

        Args:
            file_name: Original filename
            organization_id: Organization owning the file
            content_hash: SHA256 hash of file content

        Returns:
            Path object for file storage
        """
        # Extract file extension
        file_extension = Path(file_name).suffix.lower()

        # Create organization subdirectory
        org_dir = self.uploads_dir / str(organization_id)
        org_dir.mkdir(exist_ok=True)

        # Generate unique filename using hash and original extension
        unique_filename = f"{content_hash}{file_extension}"

        return org_dir / unique_filename

    def _generate_uri(self, file_path: Path) -> str:
        """
        Generate storage URI for a file path.

        Args:
            file_path: Path to the stored file

        Returns:
            Storage URI string
        """
        # Create relative path from storage root
        relative_path = file_path.relative_to(self.storage_root)
        return f"storage://{relative_path.as_posix()}"

    def _uri_to_path(self, file_uri: str) -> Path:
        """
        Convert storage URI to file path.

        Args:
            file_uri: Storage URI

        Returns:
            Path object for the file

        Raises:
            StorageError: If URI format is invalid
        """
        if not file_uri.startswith("storage://"):
            raise StorageError(f"Invalid storage URI format: {file_uri}")

        relative_path = file_uri[10:]  # Remove "storage://" prefix
        return self.storage_root / relative_path

    async def _calculate_hash(self, file_content: BinaryIO) -> str:
        """
        Calculate SHA256 hash of file content.

        Args:
            file_content: Binary file content

        Returns:
            SHA256 hash as hexadecimal string
        """
        hash_sha256 = hashlib.sha256()

        # Reset file pointer to beginning
        file_content.seek(0)

        # Read file in chunks for memory efficiency
        while chunk := file_content.read(8192):
            hash_sha256.update(chunk)

        # Reset file pointer again
        file_content.seek(0)

        return hash_sha256.hexdigest()

    def validate_file_type(self, file_name: str, content_type: str) -> bool:
        """
        Validate if file type is supported for molecular analysis.

        Args:
            file_name: Original filename
            content_type: MIME type of the file

        Returns:
            True if file type is supported
        """
        file_extension = Path(file_name).suffix.lower()

        # Check extension
        if file_extension not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file extension: {file_extension}")
            return False

        # Check MIME type
        if content_type not in self.SUPPORTED_MIME_TYPES:
            logger.warning(f"Unsupported MIME type: {content_type}")
            return False

        return True

    async def store_file(
        self, file_content: BinaryIO, file_name: str, content_type: str, organization_id: UUID
    ) -> str:
        """
        Store a file and return its URI.

        Args:
            file_content: Binary file content to store
            file_name: Original filename
            content_type: MIME type of the file
            organization_id: Organization owning the file

        Returns:
            Storage URI for the stored file

        Raises:
            StorageError: If file storage fails
        """
        try:
            # Validate file type
            if not self.validate_file_type(file_name, content_type):
                raise StorageError(f"Unsupported file type: {file_name} ({content_type})")

            # Calculate content hash
            content_hash = await self._calculate_hash(file_content)

            # Generate file path
            file_path = self._generate_file_path(file_name, organization_id, content_hash)

            # Check if file already exists (deduplication)
            if file_path.exists():
                logger.info(f"File already exists, returning existing URI: {file_path}")
                return self._generate_uri(file_path)

            # Store file content
            async with aiofiles.open(file_path, "wb") as f:
                file_content.seek(0)
                content = file_content.read()
                await f.write(content)

            # Set appropriate file permissions
            os.chmod(file_path, 0o644)

            logger.info(f"Stored file: {file_name} -> {file_path}")

            return self._generate_uri(file_path)

        except Exception as e:
            logger.error(f"Failed to store file {file_name}: {str(e)}")
            raise StorageError(f"File storage failed: {str(e)}")

    async def retrieve_file(self, file_uri: str) -> Optional[BinaryIO]:
        """
        Retrieve a file by its URI.

        Args:
            file_uri: Storage URI of the file

        Returns:
            Binary file content or None if not found

        Raises:
            StorageError: If file retrieval fails
        """
        try:
            file_path = self._uri_to_path(file_uri)

            if not file_path.exists():
                logger.warning(f"File not found: {file_uri}")
                return None

            # Return file handle (caller responsible for closing)
            return open(file_path, "rb")

        except Exception as e:
            logger.error(f"Failed to retrieve file {file_uri}: {str(e)}")
            raise StorageError(f"File retrieval failed: {str(e)}")

    async def delete_file(self, file_uri: str) -> bool:
        """
        Delete a file by its URI.

        Args:
            file_uri: Storage URI of the file

        Returns:
            True if file was deleted, False if not found

        Raises:
            StorageError: If file deletion fails
        """
        try:
            file_path = self._uri_to_path(file_uri)

            if not file_path.exists():
                logger.warning(f"File not found for deletion: {file_uri}")
                return False

            file_path.unlink()
            logger.info(f"Deleted file: {file_uri}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_uri}: {str(e)}")
            raise StorageError(f"File deletion failed: {str(e)}")

    async def generate_presigned_url(
        self, file_uri: str, expiration_seconds: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for file access.

        For local storage, this returns a direct URL to the storage service.

        Args:
            file_uri: Storage URI of the file
            expiration_seconds: URL validity duration (ignored for local storage)

        Returns:
            Presigned URL or None if file not found

        Raises:
            StorageError: If URL generation fails
        """
        try:
            file_path = self._uri_to_path(file_uri)

            if not file_path.exists():
                logger.warning(f"File not found for presigned URL: {file_uri}")
                return None

            # Convert storage URI to HTTP URL for storage service
            relative_path = file_path.relative_to(self.storage_root)
            presigned_url = f"http://storage:8080/{relative_path.as_posix()}"

            logger.info(f"Generated presigned URL: {file_uri} -> {presigned_url}")

            return presigned_url

        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {file_uri}: {str(e)}")
            raise StorageError(f"Presigned URL generation failed: {str(e)}")

    async def get_file_info(self, file_uri: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata information.

        Args:
            file_uri: Storage URI of the file

        Returns:
            Dictionary with file metadata or None if not found

        Raises:
            StorageError: If metadata retrieval fails
        """
        try:
            file_path = self._uri_to_path(file_uri)

            if not file_path.exists():
                logger.warning(f"File not found for metadata: {file_uri}")
                return None

            stat = file_path.stat()

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = "application/octet-stream"

            metadata = {
                "uri": file_uri,
                "name": file_path.name,
                "size": stat.st_size,
                "mime_type": mime_type,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "extension": file_path.suffix.lower(),
            }

            logger.info(f"Retrieved metadata for: {file_uri}")

            return metadata

        except Exception as e:
            logger.error(f"Failed to get file info for {file_uri}: {str(e)}")
            raise StorageError(f"File metadata retrieval failed: {str(e)}")
