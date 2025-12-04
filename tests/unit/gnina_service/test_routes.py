"""Route-level tests for the GNINA microservice."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator, Dict, Tuple

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from gnina_service import job_manager as job_manager_module
from gnina_service.job_manager import GninaJobManager, GninaServiceSettings
from gnina_service.routes import JOB_NOT_FOUND_DETAIL, router as gnina_router


@pytest_asyncio.fixture
async def gnina_test_app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncGenerator[Tuple[AsyncClient, GninaJobManager], None]:
    settings = GninaServiceSettings(
        storage_dir=str(tmp_path),
        simulated_runtime_seconds=0.2,
        simulated_progress_interval=0.05,
    )
    manager = GninaJobManager(config=settings)

    async def fast_progress(job):  # type: ignore[no-untyped-def]
        await asyncio.sleep(0)
        job.mark_progress(0.5, message="Testing")

    manager._simulate_progress = fast_progress  # type: ignore[assignment]

    from gnina_service import routes as routes_module

    monkeypatch.setattr(routes_module, "job_manager", manager)
    monkeypatch.setattr(job_manager_module, "job_manager", manager)

    app = FastAPI()
    app.include_router(gnina_router)

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    try:
        yield client, manager
    finally:
        await client.aclose()


async def _wait_for_completion(client: AsyncClient, job_id: str) -> Dict[str, str]:
    for _ in range(200):
        status_response = await client.get(f"/api/v1/gnina/jobs/{job_id}")
        status_response.raise_for_status()
        payload = status_response.json()
        if payload.get("status") == "succeeded":
            return payload
        await asyncio.sleep(0.05)
    raise AssertionError("GNINA job did not reach succeeded state in time")


@pytest.mark.asyncio
async def test_submit_and_retrieve_results(gnina_test_app: Tuple[AsyncClient, GninaJobManager]) -> None:
    client, manager = gnina_test_app

    files = {
        "receptor_file": ("receptor.pdbqt", b"ATOM", "chemical/x-pdbqt"),
        "ligand_file": ("ligand.sdf", b"LIG", "chemical/x-mdl-sdfile"),
    }
    advanced = {"autobox_ligand": "reference.sdf", "cnn_scoring": "refinement"}
    data = {
        "exhaustiveness": "4",
        "job_name": "Integration Test",
        "advanced_parameters": json.dumps(advanced),
    }

    response = await client.post("/api/v1/gnina/jobs", files=files, data=data)
    assert response.status_code == 201
    job_id = response.json()["job_id"]
    assert job_id

    status_payload = await _wait_for_completion(client, job_id)
    assert status_payload["job_id"] == job_id
    assert status_payload["status"] == "succeeded"

    results_response = await client.get(f"/api/v1/gnina/jobs/{job_id}/results")
    assert results_response.status_code == 200
    results_payload = results_response.json()
    assert results_payload["job_id"] == job_id
    assert results_payload["status"] == "succeeded"
    assert results_payload["binding_affinity"] == -7.5
    assert results_payload["metadata"]["parameters"]["advanced_parameters"] == advanced

    file_response = await client.get(f"/api/v1/gnina/jobs/{job_id}/files/docked_pose.pdbqt")
    assert file_response.status_code == 200
    assert file_response.content.startswith(b"REMARK Placeholder GNINA pose")

    storage_root = Path(manager.settings.storage_dir) / job_id / "results"
    assert (storage_root / "results.json").exists()


@pytest.mark.asyncio
async def test_submit_with_empty_file_rejected(
    gnina_test_app: Tuple[AsyncClient, GninaJobManager]
) -> None:
    client, _ = gnina_test_app

    files = {
        "receptor_file": ("receptor.pdbqt", b"", "chemical/x-pdbqt"),
        "ligand_file": ("ligand.sdf", b"LIG", "chemical/x-mdl-sdfile"),
    }

    response = await client.post("/api/v1/gnina/jobs", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Receptor file is empty"


@pytest.mark.asyncio
async def test_get_unknown_job_returns_404(
    gnina_test_app: Tuple[AsyncClient, GninaJobManager]
) -> None:
    client, _ = gnina_test_app

    status_response = await client.get("/api/v1/gnina/jobs/unknown")
    assert status_response.status_code == 404
    assert status_response.json()["detail"] == JOB_NOT_FOUND_DETAIL