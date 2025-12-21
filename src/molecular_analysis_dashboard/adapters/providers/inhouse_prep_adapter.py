"""In-house protein and ligand preparation adapters."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

import MDAnalysis as mda
from rdkit import Chem
from rdkit.Chem import AllChem

from ...services.execution_file_service import ExecutionFileService
from .neurosnap_task_adapter import TaskExecutorPort

logger = logging.getLogger(__name__)

DEFAULT_PDB2PQR_BINARY = os.getenv("PDB2PQR_BINARY", "pdb2pqr")
DEFAULT_EMBED_SEED = 42


def _to_uuid(value: str) -> UUID:
    try:
        return UUID(str(value))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Invalid execution identifier") from exc


class _InHousePrepBase(TaskExecutorPort):
    """Shared helpers for in-house preparation adapters."""

    def __init__(self, pdb2pqr_binary: str = DEFAULT_PDB2PQR_BINARY) -> None:
        self.pdb2pqr_binary = pdb2pqr_binary
        self.file_service = ExecutionFileService()

    async def _load_file(self, file_info: Optional[Dict[str, Any]], field: str) -> tuple[str, bytes, str]:
        if not file_info or "file_id" not in file_info:
            raise RuntimeError(f"{field} parameter is required")

        content = await self.file_service.get_file_content(file_info["file_id"])
        if not content:
            raise RuntimeError(f"File content missing for {field}")

        filename = file_info.get("filename") or f"{field}.bin"
        content_type = file_info.get("content_type") or "application/octet-stream"
        return filename, content, content_type

    async def _store_output(
        self,
        execution_id: UUID,
        parameter_name: str,
        filename: str,
        content: bytes,
        content_type: str,
        org_id: Optional[UUID],
    ) -> Dict[str, Any]:
        return await self.file_service.store_output_file_content(
            execution_id=execution_id,
            parameter_name=parameter_name,
            filename=filename,
            content=content,
            content_type=content_type,
            org_id=org_id,
        )

    async def get_task_status(self, external_job_id: str) -> Dict[str, Any]:
        return {
            "job_id": external_job_id,
            "status": "completed",
            "progress": 100,
        }

    async def get_task_results(self, external_job_id: str) -> Dict[str, Any]:
        execution_id = _to_uuid(external_job_id)
        output_files = await self.file_service.get_execution_files(execution_id=execution_id, file_type="output")
        download_urls = {
            file["parameter_name"]: file.get("url")
            for file in output_files
            if file.get("parameter_name") and file.get("url")
        }
        return {
            "job_id": external_job_id,
            "status": "completed",
            "download_urls": download_urls,
            "files": output_files,
        }


class CleanAndDryAdapter(_InHousePrepBase):
    """Remove non-protein atoms from a receptor structure."""

    async def submit_task(self, execution: Any, task_definition: Dict[str, Any]) -> str:
        org_id = getattr(execution, "org_id", None)
        receptor_info = (execution.input_data or {}).get("receptor_file")

        filename, content, _ = await self._load_file(receptor_info, "receptor_file")
        execution_id = getattr(execution, "execution_id", None)
        if not execution_id:
            raise RuntimeError("Execution ID is required")

        def _run_clean(in_bytes: bytes, original_name: str) -> bytes:
            with tempfile.TemporaryDirectory() as tmp:
                input_path = Path(tmp) / original_name
                output_path = Path(tmp) / "cleaned_receptor.pdb"
                input_path.write_bytes(in_bytes)

                universe = mda.Universe(str(input_path))
                protein = universe.select_atoms("protein")
                if protein.n_atoms == 0:
                    raise RuntimeError("No protein atoms found in receptor_file")
                protein.write(str(output_path))
                return output_path.read_bytes()

        cleaned_bytes = await asyncio.to_thread(_run_clean, content, filename)
        await self._store_output(
            execution_id=execution_id,
            parameter_name="cleaned_receptor",
            filename="cleaned_receptor.pdb",
            content=cleaned_bytes,
            content_type="chemical/x-pdb",
            org_id=org_id,
        )

        job_id = str(execution_id)
        logger.info("Cleaned receptor stored for execution %s", job_id)
        return job_id


class ProtonateAndPrepareAdapter(_InHousePrepBase):
    """Protonate a receptor and prepare ligands with 3D embeddings."""

    async def submit_task(self, execution: Any, task_definition: Dict[str, Any]) -> str:
        parameters = execution.input_data or {}
        org_id = getattr(execution, "org_id", None)
        execution_id = getattr(execution, "execution_id", None)
        if not execution_id:
            raise RuntimeError("Execution ID is required")

        receptor_info = parameters.get("receptor_file")
        ligand_info = parameters.get("ligand_file")
        embed_seed = parameters.get("embed_seed", DEFAULT_EMBED_SEED)
        ph_value = float(parameters.get("ph", 7.4))
        if not 0.0 <= ph_value <= 14.0:
            raise RuntimeError("ph must be between 0.0 and 14.0")

        receptor_filename, receptor_bytes, _ = await self._load_file(receptor_info, "receptor_file")
        ligand_filename, ligand_bytes, _ = await self._load_file(ligand_info, "ligand_file")

        def _run_protonate_and_prepare(
            receptor_content: bytes,
            ligand_content: bytes,
            receptor_name: str,
            ligand_name: str,
            seed: int,
            ph: float,
        ) -> tuple[bytes, bytes]:
            with tempfile.TemporaryDirectory() as tmp:
                receptor_in = Path(tmp) / receptor_name
                ligand_in = Path(tmp) / ligand_name
                receptor_out_pdb = Path(tmp) / "protonated_receptor.pdb"
                receptor_out_pqr = Path(tmp) / "protonated_receptor.pqr"
                ligand_out = Path(tmp) / "prepared_ligands.sdf"

                receptor_in.write_bytes(receptor_content)
                ligand_in.write_bytes(ligand_content)

                cmd = [
                    self.pdb2pqr_binary,
                    "--ff=AMBER",
                    "--titration-state-method=propka",
                    f"--with-ph={ph}",
                    "--noopt",
                    "--pdb-output",
                    str(receptor_out_pdb),
                    str(receptor_in),
                    str(receptor_out_pqr),
                ]

                try:
                    subprocess.run(
                        cmd,
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                    )
                except FileNotFoundError as exc:
                    raise RuntimeError(f"pdb2pqr binary not found: {self.pdb2pqr_binary}") from exc
                except subprocess.CalledProcessError as exc:  # noqa: PERF203
                    stderr_msg = exc.stderr.decode() if exc.stderr else ""
                    raise RuntimeError(f"pdb2pqr failed: {stderr_msg or exc}") from exc

                suppl = Chem.SDMolSupplier(str(ligand_in))
                writer = Chem.SDWriter(str(ligand_out))
                written = 0
                for idx, mol in enumerate(suppl):
                    if mol is None:
                        continue
                    try:
                        mol = Chem.AddHs(mol, addCoords=True)
                        params = AllChem.ETKDG()
                        params.randomSeed = int(seed)
                        res = AllChem.EmbedMolecule(mol, params)
                        if res == -1:
                            res = AllChem.EmbedMolecule(mol, params, useRandomCoords=True)
                        if res != -1:
                            try:
                                AllChem.MMFFOptimizeMolecule(mol)
                            except Exception:  # noqa: BLE001
                                pass
                        writer.write(mol)
                        written += 1
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Failed to prepare ligand %s: %s", idx, exc)
                writer.close()

                if written == 0:
                    raise RuntimeError("No ligands could be prepared from ligand_file")

                return receptor_out_pdb.read_bytes(), ligand_out.read_bytes()

        protonated_bytes, ligands_bytes = await asyncio.to_thread(
            _run_protonate_and_prepare,
            receptor_bytes,
            ligand_bytes,
            receptor_filename,
            ligand_filename,
            embed_seed,
            ph_value,
        )

        await self._store_output(
            execution_id=execution_id,
            parameter_name="protonated_receptor",
            filename="protonated_receptor.pdb",
            content=protonated_bytes,
            content_type="chemical/x-pdb",
            org_id=org_id,
        )
        await self._store_output(
            execution_id=execution_id,
            parameter_name="prepared_ligands",
            filename="prepared_ligands.sdf",
            content=ligands_bytes,
            content_type="chemical/x-mdl-sdfile",
            org_id=org_id,
        )

        job_id = str(execution_id)
        logger.info("Protonation and ligand prep stored for execution %s", job_id)
        return job_id
