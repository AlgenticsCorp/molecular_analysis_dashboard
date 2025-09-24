"""Neurosnap-specific API port for cloud-based molecular analysis services."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...domain.entities.docking_job import JobStatus


class NeuroSnapApiPort(ABC):
    """Abstract interface for Neurosnap cloud API integration.

    This port provides Neurosnap-specific functionality including
    authentication, service discovery, and result management.
    """

    @abstractmethod
    async def authenticate(self, api_key: str) -> bool:
        """Authenticate with Neurosnap API.

        Args:
            api_key: Neurosnap API key

        Returns:
            True if authentication successful

        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def list_available_services(self) -> List[Dict[str, Any]]:
        """List all available Neurosnap services.

        Returns:
            List of service metadata including:
            - Service name and description
            - Input/output requirements
            - Pricing and availability

        Raises:
            ServiceDiscoveryError: If service listing fails
        """
        pass

    @abstractmethod
    async def submit_job(
        self,
        service_name: str,
        input_data: Dict[str, Any],
        job_note: Optional[str] = None,
    ) -> str:
        """Submit job to Neurosnap service.

        Args:
            service_name: Name of Neurosnap service (e.g., 'GNINA')
            input_data: Service-specific input data
            job_note: Optional job description

        Returns:
            Neurosnap job ID

        Raises:
            JobSubmissionError: If job submission fails
        """
        pass

    @abstractmethod
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get job execution status.

        Args:
            job_id: Neurosnap job ID

        Returns:
            Current job status

        Raises:
            StatusCheckError: If status check fails
        """
        pass

    @abstractmethod
    async def list_job_files(
        self,
        job_id: str,
        file_type: str = "out",  # 'in' or 'out'
    ) -> List[str]:
        """List available files for a completed job.

        Args:
            job_id: Neurosnap job ID
            file_type: Type of files to list ('in' or 'out')

        Returns:
            List of available file names

        Raises:
            FileListingError: If file listing fails
        """
        pass

    @abstractmethod
    async def download_job_file(
        self,
        job_id: str,
        file_name: str,
        file_type: str = "out",
    ) -> bytes:
        """Download specific file from completed job.

        Args:
            job_id: Neurosnap job ID
            file_name: Name of file to download
            file_type: Type of file ('in' or 'out')

        Returns:
            File content as bytes

        Raises:
            FileDownloadError: If download fails
        """
        pass

    @abstractmethod
    async def list_user_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs for authenticated user.

        Returns:
            List of job metadata

        Raises:
            JobListingError: If job listing fails
        """
        pass

    @abstractmethod
    async def set_job_note(self, job_id: str, note: str) -> None:
        """Set or update job note/description.

        Args:
            job_id: Neurosnap job ID
            note: Job note/description

        Raises:
            JobUpdateError: If note update fails
        """
        pass

    @abstractmethod
    async def share_job(self, job_id: str) -> str:
        """Enable job sharing and get share ID.

        Args:
            job_id: Neurosnap job ID

        Returns:
            Share ID for public access

        Raises:
            JobSharingError: If sharing setup fails
        """
        pass

    @abstractmethod
    async def unshare_job(self, job_id: str) -> None:
        """Disable job sharing.

        Args:
            job_id: Neurosnap job ID

        Raises:
            JobSharingError: If sharing removal fails
        """
        pass

    @abstractmethod
    def get_api_base_url(self) -> str:
        """Get Neurosnap API base URL."""
        pass

    @abstractmethod
    def get_supported_services(self) -> List[str]:
        """Get list of supported service names."""
        pass
