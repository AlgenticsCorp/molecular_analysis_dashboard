"""Adapter for integrating with the in-house GNINA docking service."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

import httpx

from .neurosnap_task_adapter import TaskExecutorPort, TaskExecution

DEFAULT_GNINA_SERVICE_URL = "http://gnina-service:8080/api/v1/gnina"
DEFAULT_TIMEOUT = 60.0

logger = logging.getLogger(__name__)


class GninaServiceAdapter(TaskExecutorPort):
    """Provider adapter that talks to the internal GNINA docking microservice."""

    FILE_PARAMETERS = {"receptor_file", "ligand_file"}
    OPTIONAL_FIELDS = {
        "job_name",
        "note",
        "exhaustiveness",
        "num_modes",
        "energy_range",
        "seed",
        "cnn_scoring",
        "scoring",
        "advanced_parameters",
    }

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = DEFAULT_TIMEOUT,
    ) -> None:
        base = base_url or os.getenv("GNINA_SERVICE_URL") or DEFAULT_GNINA_SERVICE_URL
        self.base_url = base.rstrip("/")
        self.api_key = api_key or os.getenv("GNINA_SERVICE_API_KEY")
        try:
            self.timeout_seconds = float(timeout_seconds or DEFAULT_TIMEOUT)
        except (TypeError, ValueError) as exc:  # noqa: FBT001 - runtime validation of config
            raise ValueError("timeout_seconds must be numeric") from exc

        logger.debug("GNINA service adapter configured with base URL %s", self.base_url)

    async def submit_task(self, execution: TaskExecution, task_definition: Dict[str, Any]) -> str:
        """Submit a docking job to the GNINA service."""

        from ...services.execution_file_service import ExecutionFileService

        if not execution.input_data:
            raise RuntimeError("Execution payload missing input metadata")

        file_service = ExecutionFileService()
        files_payload = {}
        for field in self.FILE_PARAMETERS:
            file_info = execution.input_data.get(field)
            if not file_info:
                raise RuntimeError(f"Missing required input '{field}'")

            filename, content, content_type = await self._load_file_bytes(file_service, file_info, field)
            files_payload[field] = (filename, content, content_type or "application/octet-stream")

        data_payload = self._build_parameter_payload(execution.input_data)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/jobs",
                    data=data_payload,
                    files=files_payload,
                    headers=self._build_headers(),
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:  # noqa: BLE001 - bubble as runtime error for unified handling
            logger.error("GNINA submission failed: %s", exc)
            raise RuntimeError(f"Failed to submit GNINA job: {exc}") from exc

        payload = response.json()
        job_id = payload.get("job_id")
        if not isinstance(job_id, str) or not job_id.strip():
            raise RuntimeError("GNINA service response missing job identifier")

        logger.debug("GNINA job submitted successfully: %s", job_id)
        return job_id

    async def get_task_status(self, external_job_id: str) -> Dict[str, Any]:
        """Fetch execution status from the GNINA service."""

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    f"{self.base_url}/jobs/{external_job_id}",
                    headers=self._build_headers(),
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:  # noqa: BLE001
            logger.error("GNINA status fetch failed for %s: %s", external_job_id, exc)
            raise RuntimeError(f"Failed to fetch GNINA job status: {exc}") from exc

        payload = response.json()
        return {
            "job_id": external_job_id,
            "status": payload.get("status", "unknown"),
            "progress": payload.get("progress"),
            "message": payload.get("message"),
            "started_at": payload.get("started_at"),
            "completed_at": payload.get("completed_at"),
            "raw_response": payload,
        }

    async def get_task_results(self, external_job_id: str) -> Dict[str, Any]:
        """Fetch completed job results from the GNINA service."""

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    f"{self.base_url}/jobs/{external_job_id}/results",
                    headers=self._build_headers(),
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:  # noqa: BLE001
            logger.error("GNINA results fetch failed for %s: %s", external_job_id, exc)
            raise RuntimeError(f"Failed to fetch GNINA job results: {exc}") from exc

        payload = response.json()
        return {
            "job_id": external_job_id,
            "status": payload.get("status", "unknown"),
            "binding_affinity": payload.get("binding_affinity"),
            "poses": payload.get("poses"),
            "download_urls": payload.get("download_urls", {}),
            "metadata": payload.get("metadata", {}),
            "raw_response": payload,
        }

    async def _load_file_bytes(
        self,
        file_service: Any,
        file_info: Dict[str, Any],
        field_name: str,
    ) -> Tuple[str, bytes, Optional[str]]:
        file_id_value = file_info.get("file_id")
        if not file_id_value:
            raise RuntimeError(f"File metadata for '{field_name}' missing file_id")

        try:
            file_uuid = UUID(str(file_id_value))
        except ValueError as exc:  # noqa: FBT001 - runtime validation
            raise RuntimeError(f"Invalid file identifier for '{field_name}'") from exc

        content = await file_service.get_file_content(file_uuid)
        if content is None:
            raise RuntimeError(f"Unable to load stored content for '{field_name}'")

        return (
            file_info.get("filename") or f"{field_name}.dat",
            content,
            file_info.get("content_type"),
        )

    def _build_parameter_payload(self, input_data: Dict[str, Any]) -> Dict[str, str]:
        payload: Dict[str, str] = {}
        for key in self.OPTIONAL_FIELDS:
            if key not in input_data:
                continue
            value = input_data[key]
            if value is None or value == "":
                continue
            if isinstance(value, bool):
                payload[key] = "true" if value else "false"
            elif isinstance(value, (dict, list)):
                payload[key] = json.dumps(value)
            else:
                payload[key] = str(value)
        return payload

    def _build_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
