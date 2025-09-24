"""Neurosnap API adapter for GNINA molecular docking."""

import json
import logging
from typing import Any, Dict, List, Optional

from ...adapters.http.neurosnap_client import NeuroSnapClient
from ...domain.entities.docking_job import (
    DockingPose,
    DockingResults,
    JobStatus,
    MolecularStructure,
)
from ...domain.exceptions import (
    DockingCancellationError,
    DockingResultsError,
    DockingStatusError,
    DockingSubmissionError,
    JobNotCompleteError,
    ServiceDiscoveryError,
    StructureValidationError,
)
from ...ports.external.docking_engine_port import DockingEnginePort
from ...ports.external.neurosnap_api_port import NeuroSnapApiPort

logger = logging.getLogger(__name__)


class NeuroSnapAdapter(DockingEnginePort, NeuroSnapApiPort):
    """Neurosnap API implementation for GNINA docking.

    Integrates with Neurosnap cloud API to provide molecular docking
    services without requiring local GNINA installation.
    """

    def __init__(self, api_key: str, base_url: str = "https://neurosnap.ai"):
        """Initialize Neurosnap adapter.

        Args:
            api_key: Neurosnap API key for authentication
            base_url: Base URL for Neurosnap API
        """
        self.api_key = api_key
        self.base_url = base_url
        self._client: Optional[NeuroSnapClient] = None

        # Supported formats based on Neurosnap API requirements
        self._supported_formats = {
            "receptor": ["pdb"],
            "ligand": ["sdf", "mol2"],
        }

        # Default GNINA parameters
        self._default_parameters = {
            "exhaustiveness": 8,
            "num_modes": 9,
            "energy_range": 3.0,
        }

    async def _get_client(self) -> NeuroSnapClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = NeuroSnapClient(self.api_key, self.base_url)
        return self._client

    async def close(self) -> None:
        """Close HTTP client connection."""
        if self._client:
            await self._client.close()
            self._client = None

    # DockingEnginePort implementation

    async def submit_docking_job(
        self,
        receptor: MolecularStructure,
        ligand: Optional[MolecularStructure] = None,
        job_note: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submit GNINA docking job to Neurosnap API.

        Based on temp/scripts/submit_gnina_job.py implementation.

        Args:
            receptor: Protein/receptor structure (PDB format)
            ligand: Optional ligand structure (SDF format)
            job_note: Human-readable job description
            parameters: GNINA-specific parameters (currently unused by Neurosnap)

        Returns:
            Neurosnap job ID for tracking

        Raises:
            DockingSubmissionError: If job submission fails
        """
        try:
            client = await self._get_client()

            # Validate input structures
            await self.validate_input_structure(receptor)
            if ligand:
                await self.validate_input_structure(ligand)

            # Prepare input data for Neurosnap GNINA service
            input_data = {}

            # Receptor is required (PDB format)
            receptor_entry = {
                "type": "pdb",
                "name": receptor.name or "receptor",
                "data": receptor.data,
            }
            input_data["Input Receptor"] = json.dumps([receptor_entry])

            # Ligand is optional (SDF format)
            if ligand:
                ligand_entry = {
                    "type": "sdf",
                    "name": ligand.name or "ligand",
                    "data": ligand.data,
                }
                input_data["Input Ligand"] = json.dumps([ligand_entry])

            logger.info(f"Submitting GNINA docking job: {job_note or 'No note'}")

            # Submit to Neurosnap
            job_id = await client.submit_job(
                service_name="GNINA",
                input_data=input_data,
                job_note=job_note or "GNINA docking via molecular analysis platform",
            )

            logger.info(f"GNINA job submitted successfully: {job_id}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to submit GNINA job: {str(e)}")
            raise DockingSubmissionError(f"GNINA job submission failed: {str(e)}")

    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get the current status of a GNINA docking job.

        Args:
            job_id: Neurosnap job ID (external_job_id from DockingEnginePort)

        Returns:
            Current job status

        Raises:
            DockingStatusError: If status check fails
        """
        try:
            client = await self._get_client()
            status = await client.get_job_status(job_id)
            logger.debug(f"Job {job_id} status: {status.value}")
            return status

        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {str(e)}")
            raise DockingStatusError(f"Status check failed: {str(e)}")

    async def retrieve_results(self, job_id: str) -> DockingResults:
        """Retrieve completed GNINA docking results.

        Args:
            external_job_id: Neurosnap job ID

        Returns:
            Complete docking analysis results with poses and scores

        Raises:
            DockingResultsError: If result retrieval fails
            JobNotCompleteError: If job hasn't finished yet
        """
        try:
            client = await self._get_client()

            # Check if job is completed\n            status = await client.get_job_status(job_id)\n            if status != JobStatus.COMPLETED:\n                raise JobNotCompleteError(f\"Job {job_id} not completed (status: {status.value})\")\n            \n            # List available output files\n            output_files = await client.list_job_files(job_id, file_type=\"out\")\n            logger.info(f\"Found {len(output_files)} output files for job {job_id}\")

            # Look for GNINA-specific result files
            result_files = self._identify_result_files(output_files)

            # Download and parse results
            poses = []
            metadata = {}

            for file_name in result_files:
                file_content = await client.download_job_file(job_id, file_name, file_type="out")

                if file_name.endswith(".sdf") or "poses" in file_name.lower():
                    # Parse docking poses from SDF or similar format
                    poses.extend(self._parse_docking_poses(file_content, file_name))
                elif file_name.endswith(".json") or "results" in file_name.lower():
                    # Parse metadata from JSON results
                    try:
                        file_data = json.loads(file_content.decode("utf-8"))
                        metadata.update(file_data)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        logger.warning(f"Could not parse JSON from {file_name}")

            if not poses:
                # If no poses found, create a single pose from metadata if available
                affinity_value = metadata.get("affinity") or metadata.get("binding_affinity")
                if affinity_value is not None:
                    try:
                        affinity = float(affinity_value)
                        poses = [
                            DockingPose(
                                rank=1,
                                affinity=affinity,
                                confidence_score=metadata.get("confidence_score"),
                                pose_data=metadata,
                            )
                        ]
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid affinity value in metadata: {affinity_value}")
                else:
                    logger.warning(f"No docking poses found in results for job {job_id}")

            results = DockingResults(
                poses=poses,
                engine_version="GNINA via Neurosnap",
                metadata=metadata,
            )

            logger.info(f"Retrieved {len(poses)} docking poses for job {job_id}")
            return results

        except JobNotCompleteError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve results for {job_id}: {str(e)}")
            raise DockingResultsError(f"Result retrieval failed: {str(e)}")

    def _identify_result_files(self, file_list: List[str]) -> List[str]:
        """Identify relevant result files from output file list."""
        result_files = []

        # Look for common GNINA output patterns
        patterns = [
            ".sdf",  # Docked poses
            "poses",  # Pose files
            "results",  # Result summaries
            ".json",  # Structured results
            "docked",  # Docked structures
            "out",  # General output
        ]

        for file_name in file_list:
            for pattern in patterns:
                if pattern in file_name.lower():
                    result_files.append(file_name)
                    break

        return result_files or file_list  # Return all files if no patterns match

    def _parse_docking_poses(self, file_content: bytes, file_name: str) -> List[DockingPose]:
        """Parse docking poses from file content."""
        poses = []

        try:
            content_str = file_content.decode("utf-8")

            # Simple SDF parsing for binding affinity scores
            if file_name.endswith(".sdf"):
                poses = self._parse_sdf_poses(content_str)
            else:
                # For other formats, try to extract numeric scores
                poses = self._parse_generic_scores(content_str)

        except Exception as e:
            logger.warning(f"Failed to parse poses from {file_name}: {str(e)}")

        return poses

    def _parse_sdf_poses(self, sdf_content: str) -> List[DockingPose]:
        """Parse docking poses from SDF format."""
        poses = []
        rank = 1

        # Split SDF into individual molecules
        molecules = sdf_content.split("$$$$")

        for mol_block in molecules:
            if not mol_block.strip():
                continue

            # Look for binding affinity in SDF properties
            affinity = self._extract_affinity_from_sdf(mol_block)
            if affinity is not None:
                poses.append(
                    DockingPose(
                        rank=rank,
                        affinity=affinity,
                        pose_data={"sdf_block": mol_block.strip()},
                    )
                )
                rank += 1

        return poses

    def _parse_generic_scores(self, content: str) -> List[DockingPose]:
        """Parse binding scores from generic text format."""
        poses = []

        # Look for common score patterns in text
        import re

        # Pattern for binding affinity scores
        affinity_patterns = [
            r"affinity[:\s]+([+-]?\d+\.?\d*)",  # "affinity: -8.5"
            r"binding[:\s]+([+-]?\d+\.?\d*)",  # "binding: -8.5"
            r"score[:\s]+([+-]?\d+\.?\d*)",  # "score: -8.5"
        ]

        rank = 1
        for pattern in affinity_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    affinity = float(match)
                    poses.append(
                        DockingPose(
                            rank=rank,
                            affinity=affinity,
                            pose_data={"raw_content": content[:500]},  # Store excerpt
                        )
                    )
                    rank += 1
                except ValueError:
                    continue

            if poses:  # Stop after first successful pattern
                break

        return poses

    def _extract_affinity_from_sdf(self, sdf_block: str) -> Optional[float]:
        """Extract binding affinity from SDF property block."""
        # Look for common SDF property names for binding affinity
        import re

        property_patterns = [
            r">\s*<AFFINITY>\s*([+-]?\d+\.?\d*)",
            r">\s*<BINDING_AFFINITY>\s*([+-]?\d+\.?\d*)",
            r">\s*<SCORE>\s*([+-]?\d+\.?\d*)",
            r">\s*<ENERGY>\s*([+-]?\d+\.?\d*)",
        ]

        for pattern in property_patterns:
            match = re.search(pattern, sdf_block, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running GNINA docking job.

        Note: Neurosnap API doesn't currently support job cancellation.

        Args:
            job_id: Neurosnap job ID

        Returns:
            False (cancellation not supported)

        Raises:
            DockingCancellationError: Always raised as cancellation is not supported
        """
        raise DockingCancellationError("Job cancellation is not supported by Neurosnap API")

    async def list_available_services(self) -> List[Dict[str, Any]]:
        """List available docking services from Neurosnap.

        Returns:
            List of available services with metadata

        Raises:
            ServiceDiscoveryError: If service listing fails
        """
        try:
            client = await self._get_client()
            services = await client.list_services()

            # Filter for GNINA and related docking services
            docking_services = []
            for service in services:
                service_name = service.get("title", "").lower()
                if "gnina" in service_name or "dock" in service_name:
                    docking_services.append(service)

            logger.info(f"Found {len(docking_services)} docking services")
            return docking_services

        except Exception as e:
            logger.error(f"Failed to list available services: {str(e)}")
            raise ServiceDiscoveryError(f"Service discovery failed: {str(e)}")

    async def validate_input_structure(self, structure: MolecularStructure) -> bool:
        """Validate molecular structure for GNINA compatibility.

        Args:
            structure: Molecular structure to validate

        Returns:
            True if structure is valid

        Raises:
            StructureValidationError: If validation fails
        """
        try:
            # Check format compatibility
            if structure.format.lower() == "pdb":
                # Basic PDB validation
                if not structure.data.strip():
                    raise StructureValidationError("Empty PDB data")
                if "ATOM" not in structure.data and "HETATM" not in structure.data:
                    raise StructureValidationError("No ATOM/HETATM records found in PDB")

            elif structure.format.lower() in ["sdf", "mol2"]:
                # Basic ligand format validation
                if not structure.data.strip():
                    raise StructureValidationError(f"Empty {structure.format} data")

            else:
                raise StructureValidationError(
                    f"Unsupported format: {structure.format}. "
                    f"Supported formats: {list(self._supported_formats.values())}"
                )

            return True

        except StructureValidationError:
            raise
        except Exception as e:
            raise StructureValidationError(f"Structure validation failed: {str(e)}")

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported molecular formats for GNINA via Neurosnap."""
        return self._supported_formats.copy()

    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default GNINA docking parameters."""
        return self._default_parameters.copy()

    # NeuroSnapApiPort implementation

    async def authenticate(self, api_key: str) -> bool:
        """Test authentication with Neurosnap API."""
        try:
            client = NeuroSnapClient(api_key, self.base_url)
            await client.list_services()  # Test call
            await client.close()
            return True
        except Exception:
            return False

    async def submit_job(
        self,
        service_name: str,
        input_data: Dict[str, Any],
        job_note: Optional[str] = None,
    ) -> str:
        """Submit job to Neurosnap service (delegates to client)."""
        client = await self._get_client()
        return await client.submit_job(service_name, input_data, job_note)

    async def list_job_files(
        self,
        job_id: str,
        file_type: str = "out",
    ) -> List[str]:
        """List job files (delegates to client)."""
        client = await self._get_client()
        return await client.list_job_files(job_id, file_type)

    async def download_job_file(
        self,
        job_id: str,
        file_name: str,
        file_type: str = "out",
    ) -> bytes:
        """Download job file (delegates to client)."""
        client = await self._get_client()
        return await client.download_job_file(job_id, file_name, file_type)

    async def list_user_jobs(self) -> List[Dict[str, Any]]:
        """List user jobs (delegates to client)."""
        client = await self._get_client()
        return await client.list_jobs()

    async def set_job_note(self, job_id: str, note: str) -> None:
        """Set job note (delegates to client)."""
        client = await self._get_client()
        await client.set_job_note(job_id, note)

    async def share_job(self, job_id: str) -> str:
        """Enable job sharing (not implemented in client yet)."""
        raise NotImplementedError("Job sharing not yet implemented")

    async def unshare_job(self, job_id: str) -> None:
        """Disable job sharing (not implemented in client yet)."""
        raise NotImplementedError("Job unsharing not yet implemented")

    def get_api_base_url(self) -> str:
        """Get Neurosnap API base URL."""
        return self.base_url

    def get_supported_services(self) -> List[str]:
        """Get list of supported service names."""
        return ["GNINA"]  # We focus on GNINA for now
