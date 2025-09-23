"""Use cases for molecule upload and storage operations."""

import hashlib
import logging
from datetime import datetime
from typing import BinaryIO, Optional
from uuid import UUID, uuid4

from ...domain.entities.molecule import Molecule
from ...ports.storage import StorageError, StoragePort

logger = logging.getLogger(__name__)


class UploadMoleculeUseCase:
    """Use case for uploading and storing molecular files."""

    def __init__(self, storage_adapter: StoragePort):
        """
        Initialize the upload molecule use case.

        Args:
            storage_adapter: Storage adapter for file operations
        """
        self.storage_adapter = storage_adapter

    async def execute(
        self,
        file_content: BinaryIO,
        file_name: str,
        content_type: str,
        organization_id: UUID,
        uploaded_by: UUID,
        molecule_name: str,
        file_format: str,
        properties: Optional[dict] = None,
        tags: Optional[list] = None,
        visibility: str = "private",
    ) -> Molecule:
        """
        Execute molecule upload operation.

        Args:
            file_content: Binary file content
            file_name: Original filename
            content_type: MIME type
            organization_id: Organization ID
            uploaded_by: User ID who uploaded the file
            molecule_name: Display name for the molecule
            file_format: Molecule file format
            properties: Additional molecule properties
            tags: Molecule tags
            visibility: Visibility level

        Returns:
            Molecule entity with storage information

        Raises:
            StorageError: If file storage fails
            ValueError: If file validation fails
        """
        try:
            # Validate file type
            if not self.storage_adapter.validate_file_type(file_name, content_type):
                raise ValueError(f"Unsupported file type: {file_name} ({content_type})")

            # Calculate file size and checksum
            file_content.seek(0)
            content_bytes = file_content.read()
            file_size = len(content_bytes)
            checksum = hashlib.sha256(content_bytes).hexdigest()

            # Reset file pointer for storage
            file_content.seek(0)

            # Store file using storage adapter
            storage_uri = await self.storage_adapter.store_file(
                file_content=file_content,
                file_name=file_name,
                content_type=content_type,
                organization_id=organization_id,
            )

            # Create molecule entity
            molecule = Molecule(
                molecule_id=uuid4(),
                org_id=organization_id,
                name=molecule_name,
                format=file_format,
                uri=storage_uri,
                checksum=checksum,
                size_bytes=file_size,
                properties=properties or {},
                tags=tags or [],
                uploaded_by=uploaded_by,
                visibility=visibility,
                created_at=datetime.utcnow(),
            )

            logger.info(f"Successfully uploaded molecule: {molecule_name} ({storage_uri})")

            return molecule

        except StorageError:
            logger.error(f"Storage error during molecule upload: {molecule_name}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during molecule upload: {str(e)}")
            raise StorageError(f"Upload failed: {str(e)}")


class GetMoleculeFileUseCase:
    """Use case for retrieving molecule files."""

    def __init__(self, storage_adapter: StoragePort):
        """
        Initialize the get molecule file use case.

        Args:
            storage_adapter: Storage adapter for file operations
        """
        self.storage_adapter = storage_adapter

    async def execute(self, storage_uri: str) -> Optional[BinaryIO]:
        """
        Retrieve molecule file by storage URI.

        Args:
            storage_uri: Storage URI of the molecule file

        Returns:
            Binary file content or None if not found

        Raises:
            StorageError: If file retrieval fails
        """
        try:
            file_content = await self.storage_adapter.retrieve_file(storage_uri)

            if file_content is None:
                logger.warning(f"Molecule file not found: {storage_uri}")
            else:
                logger.info(f"Retrieved molecule file: {storage_uri}")

            return file_content

        except StorageError:
            logger.error(f"Storage error during file retrieval: {storage_uri}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during file retrieval: {str(e)}")
            raise StorageError(f"File retrieval failed: {str(e)}")


class GeneratePresignedUrlUseCase:
    """Use case for generating presigned URLs for molecule files."""

    def __init__(self, storage_adapter: StoragePort):
        """
        Initialize the presigned URL use case.

        Args:
            storage_adapter: Storage adapter for file operations
        """
        self.storage_adapter = storage_adapter

    async def execute(self, storage_uri: str, expiration_seconds: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for molecule file access.

        Args:
            storage_uri: Storage URI of the molecule file
            expiration_seconds: URL validity duration

        Returns:
            Presigned URL or None if file not found

        Raises:
            StorageError: If URL generation fails
        """
        try:
            presigned_url = await self.storage_adapter.generate_presigned_url(
                storage_uri, expiration_seconds
            )

            if presigned_url is None:
                logger.warning(f"Cannot generate URL for missing file: {storage_uri}")
            else:
                logger.info(f"Generated presigned URL for: {storage_uri}")

            return presigned_url

        except StorageError:
            logger.error(f"Storage error during URL generation: {storage_uri}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during URL generation: {str(e)}")
            raise StorageError(f"URL generation failed: {str(e)}")


class GetFileInfoUseCase:
    """Use case for retrieving file metadata information."""

    def __init__(self, storage_adapter: StoragePort):
        """
        Initialize the get file info use case.

        Args:
            storage_adapter: Storage adapter for file operations
        """
        self.storage_adapter = storage_adapter

    async def execute(self, storage_uri: str) -> Optional[dict]:
        """
        Get file metadata information.

        Args:
            storage_uri: Storage URI of the file

        Returns:
            Dictionary with file metadata or None if not found

        Raises:
            StorageError: If metadata retrieval fails
        """
        try:
            file_info = await self.storage_adapter.get_file_info(storage_uri)

            if file_info is None:
                logger.warning(f"File info not found: {storage_uri}")
            else:
                logger.info(f"Retrieved file info for: {storage_uri}")

            return file_info

        except StorageError:
            logger.error(f"Storage error during file info retrieval: {storage_uri}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during file info retrieval: {str(e)}")
            raise StorageError(f"File info retrieval failed: {str(e)}")
