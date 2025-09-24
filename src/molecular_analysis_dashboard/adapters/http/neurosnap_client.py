"""HTTP client for Neurosnap API integration."""

import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from requests_toolbelt.multipart.encoder import MultipartEncoder

from ...domain.entities.docking_job import JobStatus
from ...domain.exceptions import (
    AuthenticationError,
    FileDownloadError,
    FileListingError,
    JobListingError,
    JobSubmissionError,
    JobUpdateError,
    ServiceDiscoveryError,
    StatusCheckError,
)

logger = logging.getLogger(__name__)


class NeuroSnapClient:
    """HTTP client for Neurosnap API integration.

    Based on the Neurosnap API tutorial and temp/scripts/submit_gnina_job.py.
    Handles authentication, job submission, status polling, and result retrieval.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://neurosnap.ai",
        timeout: float = 30.0,
    ):
        """Initialize Neurosnap API client.

        Args:
            api_key: Neurosnap API key for authentication
            base_url: Base URL for Neurosnap API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "NeuroSnapClient":
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self) -> None:
        """Ensure HTTP session is initialized."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"X-API-KEY": self.api_key},
            )

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"X-API-KEY": self.api_key}
        if additional_headers:
            headers.update(additional_headers)
        return headers

    async def list_services(self) -> List[Dict[str, Any]]:
        """List all available Neurosnap services.

        Returns:
            List of service metadata

        Raises:
            ServiceDiscoveryError: If service listing fails
        """
        await self._ensure_session()

        try:
            url = f"{self.base_url}/api/services"
            logger.info(f"Listing services: {url}")

            async with self._session.get(url) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status != 200:
                    error_text = await response.text()
                    raise ServiceDiscoveryError(
                        f"Service listing failed: {response.status} - {error_text}"
                    )

                services = await response.json()
                logger.info(f"Found {len(services)} available services")
                return services

        except aiohttp.ClientError as e:
            raise ServiceDiscoveryError(f"Network error listing services: {str(e)}")

    async def submit_job(
        self,
        service_name: str,
        input_data: Dict[str, Any],
        job_note: Optional[str] = None,
    ) -> str:
        """Submit job to Neurosnap service.

        Args:
            service_name: Name of Neurosnap service (e.g., 'GNINA')
            input_data: Service-specific input data formatted for multipart upload
            job_note: Optional job description

        Returns:
            Neurosnap job ID

        Raises:
            JobSubmissionError: If job submission fails
        """
        await self._ensure_session()

        try:
            # Build URL with optional note parameter
            url = f"{self.base_url}/api/job/submit/{service_name}"
            if job_note:
                url += f"?note={job_note}"

            logger.info(f"Submitting job to {service_name}: {url}")

            # Create multipart form data (synchronous operation)
            multipart_data = MultipartEncoder(fields=input_data)

            headers = self._get_headers({"Content-Type": multipart_data.content_type})

            async with self._session.post(
                url,
                data=multipart_data.to_string(),  # Convert to bytes for aiohttp
                headers=headers,
            ) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status != 200:
                    error_text = await response.text()
                    raise JobSubmissionError(
                        f"Job submission failed: {response.status} - {error_text}"
                    )

                job_id = await response.json()
                # Handle both string and dict responses
                if isinstance(job_id, dict):
                    job_id = job_id.get("job_id", str(job_id))

                logger.info(f"Job submitted successfully: {job_id}")
                return str(job_id)

        except aiohttp.ClientError as e:
            raise JobSubmissionError(f"Network error submitting job: {str(e)}")

    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get job execution status.

        Args:
            job_id: Neurosnap job ID

        Returns:
            Current job status

        Raises:
            StatusCheckError: If status check fails
        """
        await self._ensure_session()

        try:
            url = f"{self.base_url}/api/job/status/{job_id}"
            logger.debug(f"Checking job status: {url}")

            async with self._session.get(url) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 404:
                    raise StatusCheckError(f"Job not found: {job_id}")
                elif response.status != 200:
                    error_text = await response.text()
                    raise StatusCheckError(f"Status check failed: {response.status} - {error_text}")

                status_data = await response.json()
                # Handle both string and dict responses
                if isinstance(status_data, dict):
                    status_str = status_data.get("status", status_data)
                else:
                    status_str = str(status_data).strip('"')  # Remove quotes

                # Map Neurosnap statuses to our domain statuses
                status_mapping = {
                    "pending": JobStatus.PENDING,
                    "running": JobStatus.RUNNING,
                    "completed": JobStatus.COMPLETED,
                    "failed": JobStatus.FAILED,
                }

                mapped_status = status_mapping.get(status_str.lower(), JobStatus.PENDING)
                logger.debug(f"Job {job_id} status: {mapped_status.value}")
                return mapped_status

        except aiohttp.ClientError as e:
            raise StatusCheckError(f"Network error checking job status: {str(e)}")

    async def list_job_files(
        self,
        job_id: str,
        file_type: str = "out",
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
        await self._ensure_session()

        try:
            url = f"{self.base_url}/api/job/files/{job_id}/{file_type}"
            logger.debug(f"Listing {file_type} files for job {job_id}: {url}")

            async with self._session.get(url) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 404:
                    raise FileListingError(f"Job not found or no {file_type} files: {job_id}")
                elif response.status != 200:
                    error_text = await response.text()
                    raise FileListingError(f"File listing failed: {response.status} - {error_text}")

                files = await response.json()
                logger.debug(f"Found {len(files)} {file_type} files for job {job_id}")
                return files

        except aiohttp.ClientError as e:
            raise FileListingError(f"Network error listing files: {str(e)}")

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
        await self._ensure_session()

        try:
            url = f"{self.base_url}/api/job/file/{job_id}/{file_type}/{file_name}"
            logger.debug(f"Downloading file {file_name} from job {job_id}: {url}")

            async with self._session.get(url) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 404:
                    raise FileDownloadError(f"File not found: {file_name}")
                elif response.status != 200:
                    error_text = await response.text()
                    raise FileDownloadError(
                        f"File download failed: {response.status} - {error_text}"
                    )

                file_content = await response.read()
                logger.info(f"Downloaded {len(file_content)} bytes from {file_name}")
                return file_content

        except aiohttp.ClientError as e:
            raise FileDownloadError(f"Network error downloading file: {str(e)}")

    async def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs for authenticated user.

        Returns:
            List of job metadata

        Raises:
            JobListingError: If job listing fails
        """
        await self._ensure_session()

        try:
            url = f"{self.base_url}/api/jobs"
            logger.debug(f"Listing user jobs: {url}")

            async with self._session.get(url) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status != 200:
                    error_text = await response.text()
                    raise JobListingError(f"Job listing failed: {response.status} - {error_text}")

                jobs = await response.json()
                logger.debug(f"Found {len(jobs)} user jobs")
                return jobs

        except aiohttp.ClientError as e:
            raise JobListingError(f"Network error listing jobs: {str(e)}")

    async def set_job_note(self, job_id: str, note: str) -> None:
        """Set or update job note/description.

        Args:
            job_id: Neurosnap job ID
            note: Job note/description

        Raises:
            JobUpdateError: If note update fails
        """
        await self._ensure_session()

        try:
            url = f"{self.base_url}/api/job/note/set"
            data = {"job_id": job_id, "note": note}

            logger.debug(f"Setting job note for {job_id}: {note}")

            async with self._session.post(url, json=data) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status != 200:
                    error_text = await response.text()
                    raise JobUpdateError(
                        f"Job note update failed: {response.status} - {error_text}"
                    )

                logger.debug(f"Successfully updated note for job {job_id}")

        except aiohttp.ClientError as e:
            raise JobUpdateError(f"Network error updating job note: {str(e)}")
