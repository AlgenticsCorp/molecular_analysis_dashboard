"""Storage adapter port for molecular file management."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID


class StoragePort(ABC):
    """Abstract interface for file storage operations."""

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def generate_presigned_url(
        self, file_uri: str, expiration_seconds: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for file access.

        Args:
            file_uri: Storage URI of the file
            expiration_seconds: URL validity duration

        Returns:
            Presigned URL or None if file not found

        Raises:
            StorageError: If URL generation fails
        """
        pass

    @abstractmethod
    async def get_file_info(self, file_uri: str) -> Optional[dict]:
        """
        Get file metadata information.

        Args:
            file_uri: Storage URI of the file

        Returns:
            Dictionary with file metadata or None if not found

        Raises:
            StorageError: If metadata retrieval fails
        """
        pass

    @abstractmethod
    def validate_file_type(self, file_name: str, content_type: str) -> bool:
        """
        Validate if file type is supported for molecular analysis.

        Args:
            file_name: Original filename
            content_type: MIME type of the file

        Returns:
            True if file type is supported
        """
        pass


class StorageError(Exception):
    """Exception raised for storage operation errors."""

    pass
