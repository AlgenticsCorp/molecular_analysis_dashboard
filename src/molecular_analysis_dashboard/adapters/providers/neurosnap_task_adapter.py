"""
NeuroSnap Provider Adapter for Task Framework Integration.

This adapter bridges the task framework with NeuroSnap provider-specific endpoints.
It handles the translation between generic task execution and provider-specific APIs.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from requests_toolbelt.multipart.encoder import MultipartEncoder

DEFAULT_NEUROSNAP_BASE_URL = "https://neurosnap.ai"
DEFAULT_TASK_NOTE = "Task framework execution"
from uuid import UUID
import asyncio
import importlib
import logging
import aiofiles
import httpx
from abc import ABC, abstractmethod

from ...services.task_registry import TaskRegistry


logger = logging.getLogger(__name__)


class TaskExecutorPort(ABC):
    """Port interface for task execution."""
    
    @abstractmethod
    async def submit_task(self, execution: Any, task_definition: Dict[str, Any]) -> str:
        """Submit task for execution."""
        pass


class TaskExecution:
    """Task execution entity placeholder."""
    
    def __init__(self, execution_id: str, task_id: str, parameters: Dict[str, Any]):
        self.execution_id = execution_id
        self.task_id = task_id
        self.parameters = parameters
        self.status = "PENDING"
        self.external_job_id = None


class NeuroSnapBaseAdapter(TaskExecutorPort):
    """Shared helper for NeuroSnap-backed tasks."""

    def __init__(self, base_url: str = DEFAULT_NEUROSNAP_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def _get_api_key(self) -> str:
        api_key = os.getenv("NEUROSNAP_API_KEY")
        if not api_key:
            raise RuntimeError("NEUROSNAP_API_KEY environment variable is required for NeuroSnap tasks")
        return api_key

    async def get_task_status(self, external_job_id: str) -> Dict[str, Any]:
        """Fetch job status through the unified NeuroSnap status endpoint."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/job/status/{external_job_id}",
                    headers={"X-API-KEY": self._get_api_key()},
                )
                response.raise_for_status()
                payload = response.json()

        except Exception as exc:
            raise RuntimeError(f"Failed to get task status: {exc}") from exc

        status_value: str
        if isinstance(payload, str):
            status_value = payload
        else:
            status_value = payload.get("status", "unknown")

        return {
            "job_id": external_job_id,
            "status": status_value,
            "raw_response": payload,
        }

    async def get_task_results(self, external_job_id: str) -> Dict[str, Any]:
        """Fetch job results through the unified NeuroSnap results endpoint."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/job/data/{external_job_id}/",
                    headers={"X-API-KEY": self._get_api_key()},
                )
                response.raise_for_status()
                data_payload = response.json()

        except Exception as exc:
            raise RuntimeError(f"Failed to get task results: {exc}") from exc

        files: list[str] = []
        if isinstance(data_payload, dict):
            raw_files = data_payload.get("out") or []
            if isinstance(raw_files, list):
                for entry in raw_files:
                    if isinstance(entry, list) and entry:
                        files.append(str(entry[0]))

        download_urls = {
            filename: f"{self.base_url}/api/job/file/{external_job_id}/out/{filename}"
            for filename in files
        }

        return {
            "job_id": external_job_id,
            "status": "completed",
            "files": files,
            "download_urls": download_urls,
            "raw_data": data_payload,
        }


class NeuroSnapDockingAdapter(NeuroSnapBaseAdapter):
    """Adapter for executing GNINA docking tasks via NeuroSnap provider endpoints."""

    def __init__(self, base_url: str = DEFAULT_NEUROSNAP_BASE_URL) -> None:
        super().__init__(base_url)

    async def _load_file_bytes(
        self,
        file_service: Any,
        file_info: Optional[Dict[str, Any]],
        missing_message: str,
    ) -> tuple[str, bytes, str]:
        if not file_info:
            raise RuntimeError(missing_message)

        file_id = file_info.get("file_id")
        content = await file_service.get_file_content(file_id)
        if not content:
            raise RuntimeError(missing_message)

        return (
            file_info.get("filename", "file"),
            content,
            file_info.get("content_type", "application/octet-stream"),
        )

    async def _prepare_receptor_field(
        self,
        file_service: Any,
        parameters: Dict[str, Any],
    ) -> tuple[str, bytes, str]:
        return await self._load_file_bytes(
            file_service,
            parameters.get("receptor_file"),
            "receptor_file parameter is required for GNINA docking",
        )

    async def _prepare_ligand_field(
        self,
        file_service: Any,
        parameters: Dict[str, Any],
    ) -> Optional[str]:
        ligand_info = parameters.get("ligand_file")
        if not ligand_info:
            return None

        _, content, _ = await self._load_file_bytes(
            file_service,
            ligand_info,
            "ligand_file parameter is missing required file content",
        )

        try:
            ligand_text = content.decode("utf-8")
        except UnicodeDecodeError:
            ligand_text = content.decode("latin-1")

        ligand_payload = [
            {
                "data": ligand_text,
                "type": "sdf",
            }
        ]
        return json.dumps(ligand_payload)

    def _compose_note(self, parameters: Dict[str, Any]) -> str:
        job_name = parameters.get("job_name", "GNINA Docking")
        note = parameters.get("note")

        if job_name and note:
            return f"{job_name}: {note}"
        if job_name:
            return job_name
        return note or DEFAULT_TASK_NOTE

    async def submit_task(
        self,
        execution: TaskExecution,
        task_definition: Dict[str, Any],
    ) -> str:
        """Submit GNINA docking task to NeuroSnap provider endpoint."""

        try:
            from ...services.execution_file_service import ExecutionFileService

            file_service = ExecutionFileService()
            parameters = execution.input_data or {}

            receptor_field = await self._prepare_receptor_field(file_service, parameters)
            ligand_payload = await self._prepare_ligand_field(file_service, parameters)

            fields: Dict[str, Any] = {
                "Input Receptor": receptor_field,
            }

            if ligand_payload is not None:
                fields["Input Ligand"] = ligand_payload

            encoder = MultipartEncoder(fields=fields)
            headers = {
                "X-API-KEY": self._get_api_key(),
                "Content-Type": encoder.content_type,
            }

            note_value = self._compose_note(parameters)
            submission_url = f"{self.base_url}/api/job/submit/GNINA"
            if note_value:
                submission_url = f"{submission_url}?note={quote(note_value)}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    submission_url,
                    headers=headers,
                    content=encoder.to_string(),
                )
                response.raise_for_status()

                result = response.json()
                job_id = result.get("job_id") if isinstance(result, dict) else result
                if not isinstance(job_id, str):
                    raise RuntimeError("Unexpected response payload from NeuroSnap GNINA API")
                return job_id

        except Exception as exc:
            raise RuntimeError(f"Failed to submit GNINA docking task: {exc}") from exc


class NeuroSnapAutoDockVinaAdapter(NeuroSnapDockingAdapter):
    """Adapter for executing AutoDock Vina (smina) tasks via NeuroSnap endpoints."""

    SERVICE_NAME = "AutoDock Vina (smina)"

    def __init__(self, base_url: str = DEFAULT_NEUROSNAP_BASE_URL) -> None:
        super().__init__(base_url)

    def _compose_note(self, parameters: Dict[str, Any]) -> str:
        job_name = parameters.get("job_name", "AutoDock Vina Docking")
        note = parameters.get("note")

        if job_name and note:
            return f"{job_name}: {note}"
        if job_name:
            return job_name
        return note or DEFAULT_TASK_NOTE

    async def _build_ligand_payload(
        self,
        file_service: Any,
        parameters: Dict[str, Any],
    ) -> str:
        file_payload = await self._collect_ligands_from_files(file_service, parameters)
        entry_payload = self._collect_ligands_from_entries(parameters)
        payload = file_payload + entry_payload

        if not payload:
            raise RuntimeError("At least one ligand must be provided via ligand_file or ligand_entries_json")

        return json.dumps(payload)

    async def _collect_ligands_from_files(
        self,
        file_service: Any,
        parameters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        ligand_files = parameters.get("ligand_file")
        if not ligand_files:
            return []

        entries = ligand_files if isinstance(ligand_files, list) else [ligand_files]
        payload: List[Dict[str, Any]] = []

        for entry in entries:
            filename, content, _ = await self._load_file_bytes(
                file_service,
                entry,
                "ligand_file parameter is missing required file content",
            )
            text = self._decode_ligand_content(content)
            payload.append(
                {
                    "data": text,
                    "type": self._infer_ligand_type(filename, entry.get("content_type")),
                }
            )

        return payload

    def _collect_ligands_from_entries(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        ligand_entries = parameters.get("ligand_entries_json")
        if not ligand_entries:
            return []

        parsed_entries = self._parse_ligand_entries(ligand_entries)
        payload: List[Dict[str, Any]] = []

        for index, entry in enumerate(parsed_entries):
            if isinstance(entry, str):
                payload.append({"data": entry, "type": "smiles"})
                continue
            if not isinstance(entry, dict):
                raise RuntimeError(f"ligand_entries_json entry {index} must be a string or object")
            data = entry.get("data")
            if not data:
                raise RuntimeError(f"ligand_entries_json entry {index} is missing 'data'")
            payload.append({"data": data, "type": entry.get("type", "smiles")})

        return payload

    def _parse_ligand_entries(self, ligand_entries: Any) -> List[Any]:
        if isinstance(ligand_entries, list):
            return ligand_entries
        if not isinstance(ligand_entries, str):
            raise RuntimeError("ligand_entries_json must be a JSON array")
        candidate = ligand_entries.strip()
        if not candidate:
            return []
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise RuntimeError("ligand_entries_json must be valid JSON") from exc
        if not isinstance(parsed, list):
            raise RuntimeError("ligand_entries_json must be a JSON array")
        return parsed

    def _decode_ligand_content(self, content: bytes) -> str:
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1")

    def _infer_ligand_type(self, filename: Optional[str], content_type: Optional[str]) -> str:
        if content_type:
            normalized = content_type.lower()
            content_matches = {
                "pdbqt": "pdbqt",
                "pdb": "pdb",
                "sdf": "sdf",
                "mol": "mol",
                "smiles": "smiles",
            }
            for needle, ligand_type in content_matches.items():
                if needle in normalized:
                    return ligand_type

        if filename:
            _, ext = os.path.splitext(filename.lower())
            extension_map = {
                ".pdbqt": "pdbqt",
                ".pdb": "pdb",
                ".sdf": "sdf",
                ".mol": "mol",
                ".smiles": "smiles",
                ".smi": "smiles",
            }
            if ext in extension_map:
                return extension_map[ext]

        return "sdf"

    async def submit_task(
        self,
        execution: TaskExecution,
        task_definition: Dict[str, Any],
    ) -> str:
        """Submit AutoDock Vina task to NeuroSnap provider endpoint."""

        try:
            from ...services.execution_file_service import ExecutionFileService

            file_service = ExecutionFileService()
            parameters = execution.input_data or {}

            receptor_field = await self._prepare_receptor_field(
                file_service,
                parameters,
            )
            ligand_payload = await self._build_ligand_payload(file_service, parameters)

            fields: Dict[str, Any] = {
                "Input Receptor": receptor_field,
                "Input Ligand": ligand_payload,
            }

            scoring_function = parameters.get("scoring_function")
            if scoring_function:
                fields["Scoring Function"] = str(scoring_function)

            if parameters.get("local_only"):
                fields["Local Only"] = "true"

            if parameters.get("score_only"):
                fields["Score Only"] = "true"

            minimization_iterations = parameters.get("minimization_iterations")
            if minimization_iterations not in (None, ""):
                fields["Minimization Iterations"] = str(minimization_iterations)

            encoder = MultipartEncoder(fields=fields)
            headers = {
                "X-API-KEY": self._get_api_key(),
                "Content-Type": encoder.content_type,
            }

            note_value = self._compose_note(parameters)
            submission_url = f"{self.base_url}/api/job/submit/{quote(self.SERVICE_NAME)}"
            if note_value:
                submission_url = f"{submission_url}?note={quote(note_value)}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    submission_url,
                    headers=headers,
                    content=encoder.to_string(),
                )
                response.raise_for_status()

                result = response.json()
                job_id = result.get("job_id") if isinstance(result, dict) else result
                if not isinstance(job_id, str):
                    raise RuntimeError("Unexpected response payload from NeuroSnap AutoDock Vina API")
                return job_id

        except Exception as exc:
            raise RuntimeError(f"Failed to submit AutoDock Vina task: {exc}") from exc


class NeuroSnapDynamicBindAdapter(NeuroSnapAutoDockVinaAdapter):
    """Adapter for NeuroSnap DynamicBind docking service."""

    SERVICE_NAME = "DynamicBind"
    MIN_NUMBER_SAMPLES = 5
    MIN_INFERENCE_STEPS = 5
    DEFAULT_NUMBER_SAMPLES = 10
    DEFAULT_INFERENCE_STEPS = 20

    def _compose_note(self, parameters: Dict[str, Any]) -> str:
        # Override to ensure the provider note reflects DynamicBind instead of the Vina base class default
        job_name = parameters.get("job_name", "DynamicBind Docking")
        note = parameters.get("note")

        if job_name and note:
            return f"{job_name}: {note}"
        if job_name:
            return job_name
        return note or DEFAULT_TASK_NOTE

    async def submit_task(
        self,
        execution: TaskExecution,
        task_definition: Dict[str, Any],
    ) -> str:
        """Submit DynamicBind task to NeuroSnap provider endpoint."""

        try:
            from ...services.execution_file_service import ExecutionFileService

            file_service = ExecutionFileService()
            parameters = execution.input_data or {}

            receptor_field = await self._prepare_receptor_field(file_service, parameters)
            ligand_payload = await self._build_ligand_payload(file_service, parameters)

            # Enforce provider minimums and defaults for sampling params
            number_samples = parameters.get("number_samples")
            if number_samples is None:
                number_samples = self.DEFAULT_NUMBER_SAMPLES
            if isinstance(number_samples, str):
                try:
                    number_samples = int(number_samples)
                except ValueError:
                    raise RuntimeError("number_samples must be an integer")
            if number_samples < self.MIN_NUMBER_SAMPLES:
                raise RuntimeError(
                    f"number_samples must be >= {self.MIN_NUMBER_SAMPLES} for DynamicBind"
                )

            inference_steps = parameters.get("inference_steps")
            if inference_steps is None:
                inference_steps = self.DEFAULT_INFERENCE_STEPS
            if isinstance(inference_steps, str):
                try:
                    inference_steps = int(inference_steps)
                except ValueError:
                    raise RuntimeError("inference_steps must be an integer")
            if inference_steps < self.MIN_INFERENCE_STEPS:
                raise RuntimeError(
                    f"inference_steps must be >= {self.MIN_INFERENCE_STEPS} for DynamicBind"
                )

            fields: Dict[str, Any] = {
                "Input Receptor": receptor_field,
                "Input Ligand": ligand_payload,
            }

            # Optional numeric/string parameters
            if number_samples is not None:
                fields["Number Samples"] = str(number_samples)

            if inference_steps is not None:
                fields["Inference Steps"] = str(inference_steps)

            if parameters.get("model_version"):
                fields["Model Version"] = parameters.get("model_version")

            if parameters.get("random_seed") is not None:
                fields["Random Seed"] = str(parameters.get("random_seed"))

            # Optional booleans are only sent when True, matching provider guidance
            if bool(parameters.get("relax_structure")):
                fields["Relax Structure"] = "true"

            if bool(parameters.get("noise_structure")):
                fields["Noise Structure"] = "true"

            encoder = MultipartEncoder(fields=fields)
            headers = {
                "X-API-KEY": self._get_api_key(),
                "Content-Type": encoder.content_type,
            }

            note_value = self._compose_note(parameters)
            submission_url = f"{self.base_url}/api/job/submit/{self.SERVICE_NAME}"
            if note_value:
                submission_url = f"{submission_url}?note={quote(note_value)}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    submission_url,
                    headers=headers,
                    content=encoder.to_string(),
                )
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    # Surface provider error body to aid debugging when they return 400s
                    body = exc.response.text
                    raise RuntimeError(
                        f"Provider responded {exc.response.status_code}: {body or exc.response.reason_phrase}"
                    ) from exc

                result = response.json()
                job_id = result.get("job_id") if isinstance(result, dict) else result
                if not isinstance(job_id, str):
                    raise RuntimeError("Unexpected response payload from NeuroSnap DynamicBind API")
                return job_id

        except Exception as exc:
            raise RuntimeError(f"Failed to submit DynamicBind task: {exc}") from exc


class NeuroSnapAmberRelaxationAdapter(NeuroSnapBaseAdapter):
    """Adapter for executing Amber relaxation tasks via NeuroSnap provider endpoints."""

    def __init__(self, base_url: str = DEFAULT_NEUROSNAP_BASE_URL) -> None:
        super().__init__(base_url)
        self.service_name = "AMBER Relaxation"

    def _compose_note(self, parameters: Dict[str, Any]) -> str:
        job_name = parameters.get("job_name", "AMBER Relaxation")
        note = parameters.get("note")

        if job_name and note:
            return f"{job_name}: {note}"
        if job_name:
            return job_name
        return note or DEFAULT_TASK_NOTE

    async def submit_task(
        self,
        execution: TaskExecution,
        task_definition: Dict[str, Any],
    ) -> str:
        """Submit Amber relaxation task to NeuroSnap provider endpoint."""

        parameters = execution.input_data or {}
        structure_info = parameters.get("structure_file")

        if not structure_info:
            raise RuntimeError("structure_file parameter is required for Amber Relaxation task")

        file_id = structure_info.get("file_id")
        if not file_id:
            raise RuntimeError("structure_file metadata missing file identifier")

        from ...services.execution_file_service import ExecutionFileService

        file_service = ExecutionFileService()
        content = await file_service.get_file_content(file_id)

        if not content:
            raise RuntimeError("Unable to load structure file content for submission")

        try:
            fields: Dict[str, Any] = {
                "Input Structure": (
                    structure_info.get("filename", "structure.pdb"),
                    content,
                    structure_info.get("content_type", "chemical/x-pdb"),
                )
            }

            max_iterations = parameters.get("max_iterations")
            tolerance = parameters.get("tolerance")

            if max_iterations is not None:
                fields["Max Iterations"] = str(max_iterations)
            else:
                fields["Max Iterations"] = "2500"

            if tolerance is not None:
                fields["Tolerance"] = str(tolerance)
            else:
                fields["Tolerance"] = "1"

            encoder = MultipartEncoder(fields=fields)
            headers = {
                "X-API-KEY": self._get_api_key(),
                "Content-Type": encoder.content_type,
            }

            note_value = self._compose_note(parameters)
            submission_url = f"{self.base_url}/api/job/submit/{quote(self.service_name)}"
            if note_value:
                submission_url = f"{submission_url}?note={quote(note_value)}"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    submission_url,
                    headers=headers,
                    content=encoder.to_string(),
                )
                response.raise_for_status()

                result = response.json()
                if isinstance(result, dict):
                    job_id = result.get("job_id")
                else:
                    job_id = result

                if not isinstance(job_id, str):
                    raise RuntimeError("Unexpected response payload from NeuroSnap Amber Relaxation API")

                return job_id

        except Exception as exc:
            raise RuntimeError(f"Failed to submit Amber relaxation task: {exc}") from exc

    async def _prepare_file_data(self, file_param: Any) -> Dict[str, Any]:
        """Prepare file data for multipart submission."""
        
        if isinstance(file_param, dict):
            # Handle file data passed as dictionary 
            return {
                'content': file_param.get('content', b''),
                'filename': file_param.get('filename', 'file.dat')
            }
        elif hasattr(file_param, 'read'):
            # Handle file-like objects
            content = await file_param.read()
            filename = getattr(file_param, 'filename', 'file.dat')
            return {'content': content, 'filename': filename}
        else:
            # Handle string paths to files
            async with aiofiles.open(file_param, 'rb') as f:
                content = await f.read()
            return {'content': content, 'filename': file_param.split('/')[-1]}


class NeuroSnapFoldingAdapterBase(NeuroSnapBaseAdapter):
    """Shared behaviour for NeuroSnap AlphaFold3-based folding services."""

    SEQUENCES_REQUIRED_MSG = "sequences parameter must include at least one entry"

    def __init__(
        self,
        service_name: str,
        default_job_name: str,
        base_url: str = DEFAULT_NEUROSNAP_BASE_URL,
    ) -> None:
        super().__init__(base_url)
        self.service_name = service_name
        self.default_job_name = default_job_name

    def _compose_note(self, parameters: Dict[str, Any]) -> str:
        job_name = parameters.get("job_name", self.default_job_name)
        note = parameters.get("note")

        if job_name and note:
            return f"{job_name}: {note}"
        if job_name:
            return job_name
        return note or DEFAULT_TASK_NOTE

    def _parse_json_list(self, value: Any, field_name: str) -> List[Any]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return []
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{field_name} must be valid JSON") from exc
            if not isinstance(parsed, list):
                raise RuntimeError(f"{field_name} must be a JSON array")
            return parsed
        raise RuntimeError(f"{field_name} must be a JSON array or JSON-encoded string")

    def _normalize_sequence_type(self, raw_type: str, index: int) -> str:
        mapping = {
            "aa": "aa",
            "protein": "aa",
            "proteins": "aa",
            "dna": "dna",
            "rna": "rna",
        }
        normalized = mapping.get(raw_type.lower())
        if not normalized:
            raise RuntimeError(f"sequences[{index}] has unsupported type '{raw_type}'")
        return normalized

    def _parse_sequences(self, parameters: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        raw_sequences = parameters.get("sequences")
        try:
            sequence_entries = self._parse_json_list(raw_sequences, "sequences")
        except RuntimeError as json_error:
            if isinstance(raw_sequences, str):
                try:
                    return self._parse_fasta_sequences(raw_sequences)
                except RuntimeError as fasta_error:
                    raise RuntimeError(
                        "sequences must be valid JSON or FASTA-formatted text"
                    ) from fasta_error
            raise json_error

        return self._build_sequence_payload(sequence_entries)

    def _infer_sequence_type(self, sequence: str) -> str:
        letters = {char for char in sequence.upper() if char.isalpha()}
        dna_letters = {"A", "C", "G", "T", "N"}
        rna_letters = {"A", "C", "G", "U", "N"}

        if letters and letters.issubset(dna_letters):
            return "dna"
        if letters and letters.issubset(rna_letters):
            return "rna"
        return "aa"

    def _parse_fasta_sequences(self, raw_value: str) -> Dict[str, Dict[str, str]]:
        candidate = (raw_value or "").strip()
        if not candidate:
            raise RuntimeError(self.SEQUENCES_REQUIRED_MSG)

        entries: List[Dict[str, str]] = []
        current_name: Optional[str] = None
        current_sequence: List[str] = []

        def flush_current() -> None:
            if not current_sequence:
                return
            sequence_value = "".join(current_sequence)
            entries.append(self._make_sequence_entry(current_name, sequence_value))
            current_sequence.clear()

        for line in candidate.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith(">"):
                flush_current()
                current_name = stripped[1:].strip() or None
                continue

            current_sequence.append(stripped.replace(" ", ""))

        flush_current()

        if not entries:
            sanitized = candidate.replace(" ", "").replace("\n", "")
            if not sanitized:
                raise RuntimeError(self.SEQUENCES_REQUIRED_MSG)
            entries.append(self._make_sequence_entry(None, sanitized))

        return self._build_sequence_payload(entries)

    def _build_sequence_payload(self, sequence_entries: List[Any]) -> Dict[str, Dict[str, str]]:
        if not sequence_entries:
            raise RuntimeError(self.SEQUENCES_REQUIRED_MSG)

        payload: Dict[str, Dict[str, str]] = {}
        for index, entry in enumerate(sequence_entries):
            if not isinstance(entry, dict):
                raise RuntimeError(f"sequences[{index}] must be an object")

            name = entry.get("name")
            sequence = entry.get("sequence")
            seq_type = entry.get("type") or "aa"

            if not name:
                name = f"sequence_{index + 1}"
            if not sequence:
                raise RuntimeError(f"sequences[{index}] missing sequence")

            normalized_sequence = "".join(str(sequence).split()).upper()
            if not normalized_sequence:
                raise RuntimeError(f"sequences[{index}] missing sequence")

            normalized_type = self._normalize_sequence_type(str(seq_type), index)
            payload.setdefault(normalized_type, {})[str(name)] = normalized_sequence

        return payload

    def _make_sequence_entry(self, name: Optional[str], sequence: str) -> Dict[str, str]:
        cleaned_sequence = "".join(sequence.split()).upper()
        if not cleaned_sequence:
            raise RuntimeError(self.SEQUENCES_REQUIRED_MSG)

        return {
            "name": name or "",
            "sequence": cleaned_sequence,
            "type": self._infer_sequence_type(cleaned_sequence),
        }

    def _parse_molecules(self, parameters: Dict[str, Any]) -> List[Dict[str, str]]:
        molecule_entries = self._parse_json_list(parameters.get("molecules"), "molecules")
        parsed: List[Dict[str, str]] = []

        for index, entry in enumerate(molecule_entries):
            if not isinstance(entry, dict):
                raise RuntimeError(f"molecules[{index}] must be an object")

            data = entry.get("data")
            mol_type = entry.get("type") or "sdf"
            if not data:
                raise RuntimeError(f"molecules[{index}] missing data")

            parsed.append({
                "data": str(data),
                "type": str(mol_type),
            })

        return parsed

    async def _prepare_file_tuple(
        self,
        file_service: Any,
        file_info: Optional[Dict[str, Any]],
        default_filename: str,
        default_content_type: str,
    ) -> Optional[Tuple[str, bytes, str]]:
        if not file_info:
            return None

        file_id = file_info.get("file_id")
        if not file_id:
            raise RuntimeError("File metadata missing file_id")

        content = await file_service.get_file_content(UUID(str(file_id)))
        if content is None:
            raise RuntimeError("Unable to load file content from storage")

        filename = file_info.get("filename") or default_filename
        content_type = file_info.get("content_type") or default_content_type
        return filename, content, content_type

    def _decode_text(self, content: bytes) -> str:
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1")

    def _infer_molecule_type(self, filename: str) -> str:
        lowered = filename.lower()
        if lowered.endswith(".sdf"):
            return "sdf"
        if lowered.endswith(".mol"):
            return "mol"
        if lowered.endswith(".pdb"):
            return "pdb"
        if lowered.endswith(".smiles") or lowered.endswith(".smi"):
            return "smiles"
        return "sdf"

    async def _collect_molecules(
        self,
        parameters: Dict[str, Any],
        file_service: Any,
    ) -> List[Dict[str, str]]:
        molecules = self._parse_molecules(parameters)

        molecule_file_info = parameters.get("molecule_file")
        if molecule_file_info:
            file_tuple = await self._prepare_file_tuple(
                file_service,
                molecule_file_info,
                "molecule.sdf",
                "application/octet-stream",
            )
            if file_tuple:
                filename, content, _ = file_tuple
                molecules.append(
                    {
                        "data": self._decode_text(content),
                        "type": self._infer_molecule_type(filename),
                    }
                )

        return molecules

    async def _build_common_fields(
        self,
        parameters: Dict[str, Any],
        file_service: Any,
    ) -> Dict[str, Any]:
        sequences_payload = self._parse_sequences(parameters)
        fields: Dict[str, Any] = {
            "Input Sequences": json.dumps(sequences_payload),
        }

        molecules_payload = await self._collect_molecules(parameters, file_service)
        if molecules_payload:
            fields["Input Molecules"] = json.dumps(molecules_payload)

        residue_modifications = parameters.get("residue_modifications")
        if residue_modifications:
            fields["Residue Modifications"] = residue_modifications

        msa_mode = parameters.get("msa_mode") or "mmseqs2_uniref_env"
        fields["MSA Mode"] = str(msa_mode)

        custom_msa_tuple = await self._prepare_file_tuple(
            file_service,
            parameters.get("custom_msa_file"),
            "custom_msa.txt",
            "text/plain",
        )
        if custom_msa_tuple:
            fields["Custom MSA"] = custom_msa_tuple

        number_recycles = parameters.get("number_recycles")
        fields["Number Recycles"] = str(number_recycles if number_recycles is not None else 6)

        sampling_steps = parameters.get("sampling_steps")
        fields["Sampling Steps"] = str(sampling_steps if sampling_steps is not None else 200)

        diffusion_samples = parameters.get("diffusion_samples")
        fields["Diffusion Samples"] = str(diffusion_samples if diffusion_samples is not None else 5)

        return fields

    def _build_submission_url(self, note_value: Optional[str]) -> str:
        encoded_service = quote(self.service_name, safe="")
        submission_url = f"{self.base_url}/api/job/submit/{encoded_service}"
        if note_value:
            submission_url = f"{submission_url}?note={quote(note_value)}"
        return submission_url

    async def _submit_with_fields(self, fields: Dict[str, Any], note_value: Optional[str]) -> str:
        encoder = MultipartEncoder(fields=fields)
        headers = {
            "X-API-KEY": self._get_api_key(),
            "Content-Type": encoder.content_type,
        }

        submission_url = self._build_submission_url(note_value)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    submission_url,
                    headers=headers,
                    content=encoder.to_string(),
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text.strip()
                raise RuntimeError(
                    f"NeuroSnap folding API returned {exc.response.status_code}: {detail or 'no response body'}"
                ) from exc

            result = response.json()
            job_id = result.get("job_id") if isinstance(result, dict) else result
            if not isinstance(job_id, str):
                raise RuntimeError("Unexpected response payload from NeuroSnap folding API")
            return job_id


class NeuroSnapIntelliFoldAdapter(NeuroSnapFoldingAdapterBase):
    """Adapter for NeuroSnap IntelliFold (AlphaFold3) folding tasks."""

    def __init__(self, base_url: str = DEFAULT_NEUROSNAP_BASE_URL) -> None:
        super().__init__("IntelliFold (AlphaFold3)", "IntelliFold Prediction", base_url)

    async def submit_task(
        self,
        execution: TaskExecution,
        task_definition: Dict[str, Any],
    ) -> str:
        try:
            from ...services.execution_file_service import ExecutionFileService

            file_service = ExecutionFileService()
            parameters = execution.input_data or {}

            fields = await self._build_common_fields(parameters, file_service)

            note_value = self._compose_note(parameters)
            return await self._submit_with_fields(fields, note_value)

        except Exception as exc:
            raise RuntimeError(f"Failed to submit IntelliFold task: {exc}") from exc


class NeuroSnapBoltz2Adapter(NeuroSnapFoldingAdapterBase):
    """Adapter for NeuroSnap Boltz-2 (AlphaFold3) folding tasks."""

    def __init__(self, base_url: str = DEFAULT_NEUROSNAP_BASE_URL) -> None:
        super().__init__("Boltz-2 (AlphaFold3)", "Boltz-2 Folding", base_url)

    async def submit_task(
        self,
        execution: TaskExecution,
        task_definition: Dict[str, Any],
    ) -> str:
        try:
            from ...services.execution_file_service import ExecutionFileService

            file_service = ExecutionFileService()
            parameters = execution.input_data or {}

            fields = await self._build_common_fields(parameters, file_service)

            cyclic = parameters.get("cyclic_biopolymers")
            if cyclic:
                fields["Cyclic Biopolymers"] = cyclic

            binder_sequence = parameters.get("binder_sequence")
            if binder_sequence:
                fields["Binder Sequence"] = binder_sequence

            pocket_restraints = parameters.get("pocket_restraints")
            if pocket_restraints:
                fields["Pocket Restraints"] = pocket_restraints

            covalent_restraints = parameters.get("covalent_restraints")
            if covalent_restraints:
                fields["Covalent Restraints"] = covalent_restraints

            if parameters.get("use_inference_time_potentials"):
                fields["Use Inference Time Potentials"] = "true"

            if parameters.get("molecular_weight_correction"):
                fields["Molecular Weight Correction"] = "true"

            sampling_steps_affinity = parameters.get("sampling_steps_affinity")
            fields["Sampling Steps Affinity"] = str(
                sampling_steps_affinity if sampling_steps_affinity is not None else 200
            )

            diffusion_samples_affinity = parameters.get("diffusion_samples_affinity")
            fields["Diffusion Samples Affinity"] = str(
                diffusion_samples_affinity if diffusion_samples_affinity is not None else 5
            )

            step_scale = parameters.get("step_scale")
            fields["Step Scale"] = str(step_scale if step_scale is not None else 1.5)

            note_value = self._compose_note(parameters)
            return await self._submit_with_fields(fields, note_value)

        except Exception as exc:
            raise RuntimeError(f"Failed to submit Boltz-2 folding task: {exc}") from exc


class TaskExecutionService:
    """Service for managing task executions with provider adapters."""

    def __init__(self, registry: Optional[TaskRegistry] = None) -> None:
        self.registry = registry or TaskRegistry()
        self.adapters: Dict[str, TaskExecutorPort] = {}
        self._adapter_errors: Dict[str, str] = {}
        self._initialize_adapters()

    def _initialize_adapters(self) -> None:
        """Instantiate adapters declared in the registry."""

        self.adapters.clear()
        self._adapter_errors.clear()

        for task_id, config in self.registry.list_tasks().items():
            adapter_config = config.get("adapter") or {}
            try:
                adapter = self._instantiate_adapter(adapter_config)
                if adapter:
                    self.adapters[task_id] = adapter
                    logger.debug("Adapter ready for task '%s'", task_id)
            except Exception as exc:  # noqa: BLE001 - capture adapter init errors for observability
                self._adapter_errors[task_id] = str(exc)
                logger.error("Failed to initialize adapter for task %s: %s", task_id, exc)

    def _instantiate_adapter(self, adapter_config: Dict[str, Any]) -> Optional[TaskExecutorPort]:
        """Create adapter instance based on registry configuration."""

        module_path = adapter_config.get("module")
        class_name = adapter_config.get("class")

        if not module_path or not class_name:
            raise ValueError("Adapter configuration missing 'module' or 'class'")

        module = importlib.import_module(module_path)
        adapter_cls = getattr(module, class_name, None)
        if adapter_cls is None:
            raise ImportError(f"Adapter class '{class_name}' not found in module '{module_path}'")

        options = adapter_config.get("options") or {}
        return adapter_cls(**options)

    def get_available_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available framework tasks."""
        metadata = self.registry.list_metadata()
        return {
            task_id: task_meta
            for task_id, task_meta in metadata.items()
            if task_id in self.adapters
        }

    def get_adapter_errors(self) -> Dict[str, str]:
        """Expose adapter initialization errors for diagnostics."""
        return dict(self._adapter_errors)

    async def execute_task(self, 
                          task_id: str,
                          execution: TaskExecution,
                          task_definition: Dict[str, Any]) -> str:
        """Execute a task using the appropriate provider adapter."""
        
        adapter = self.adapters.get(task_id)
        if not adapter:
            raise ValueError(f"No adapter found for task: {task_id}")

        # Submit task to provider
        task_info = task_definition or self.registry.get_metadata(task_id) or {}
        external_job_id = await adapter.submit_task(execution, task_info)
        
        # Update execution with external job ID
        execution.external_job_id = external_job_id
        execution.status = "SUBMITTED"
        
        return external_job_id

    async def get_execution_status(self, task_id: str, external_job_id: str) -> Dict[str, Any]:
        """Get execution status from provider."""
        
        adapter = self.adapters.get(task_id)
        if not adapter:
            raise ValueError(f"No adapter found for task: {task_id}")

        return await adapter.get_task_status(external_job_id)

    async def get_execution_results(self, task_id: str, external_job_id: str) -> Dict[str, Any]:
        """Get execution results from provider."""
        
        adapter = self.adapters.get(task_id)
        if not adapter:
            raise ValueError(f"No adapter found for task: {task_id}")

        return await adapter.get_task_results(external_job_id)