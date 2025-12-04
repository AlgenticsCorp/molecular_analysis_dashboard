"""Unit tests for the GNINA job manager."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from gnina_service.job_manager import GninaJobManager, GninaServiceSettings
from gnina_service.models import JobStatus


@pytest.mark.asyncio
async def test_submit_job_completes_and_persists_results(tmp_path: Path) -> None:
    settings = GninaServiceSettings(
        storage_dir=str(tmp_path),
        simulated_runtime_seconds=0.2,
        simulated_progress_interval=0.05,
    )
    manager = GninaJobManager(config=settings)

    job = await manager.submit_job(
        parameters={"exhaustiveness": 8},
        files={
            "receptor_file": ("receptor.pdbqt", b"ATOM"),
            "ligand_file": ("ligand.sdf", b"LIG"),
        },
    )

    for _ in range(40):
        stored_job = await manager.get_job(job.job_id)
        if stored_job and stored_job.status == JobStatus.SUCCEEDED:
            break
        await asyncio.sleep(0.05)

    stored_job = await manager.get_job(job.job_id)
    assert stored_job is not None, "Job should be retrievable after submission"
    assert stored_job.status == JobStatus.SUCCEEDED
    assert stored_job.result_payload is not None

    results_dir = tmp_path / job.job_id / "results"
    assert (results_dir / "docked_pose.pdbqt").exists()
    assert (results_dir / "results.json").exists()


@pytest.mark.asyncio
async def test_submit_job_records_failure(tmp_path: Path) -> None:
    settings = GninaServiceSettings(
        storage_dir=str(tmp_path),
        simulated_runtime_seconds=0.1,
        simulated_progress_interval=0.05,
    )
    manager = GninaJobManager(config=settings)

    async def failing_persist(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")

    manager._persist_files = failing_persist  # type: ignore[assignment]

    with pytest.raises(RuntimeError):
        await manager.submit_job(
            parameters={},
            files={"receptor_file": ("rec.pdbqt", b""), "ligand_file": ("lig.sdf", b"")},
        )

    assert not any(tmp_path.iterdir()), "Storage directory should remain empty on failure"
