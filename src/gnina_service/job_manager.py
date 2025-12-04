"""Job execution and storage primitives for the GNINA service."""

from __future__ import annotations

import asyncio
import logging
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

import aiofiles

from .models import GninaJob, JobStatus
from .settings import GninaServiceSettings, settings

logger = logging.getLogger(__name__)

POSE_TEMPLATE = """REMARK Placeholder GNINA pose for {job_id}\nREMARK Parameters: {parameters}\nENDMDL\n"""


class GninaJobManager:
    """Handles lifecycle of GNINA jobs including persistence and simulation."""

    def __init__(self, config: Optional[GninaServiceSettings] = None) -> None:
        self.settings = config or settings
        self.settings.prepare()
        self._jobs: Dict[str, GninaJob] = {}
        self._jobs_lock = asyncio.Lock()
        self._background_tasks: Dict[str, asyncio.Task[Any]] = {}

    async def submit_job(
        self,
        *,
        parameters: Dict[str, Any],
        files: Dict[str, Tuple[str, bytes]],
    ) -> GninaJob:
        """Persist incoming payload and schedule execution."""

        job_id = uuid4().hex
        storage_path = self.settings.storage_dir / job_id
        await self._persist_files(storage_path, files)
        job = GninaJob(job_id=job_id, parameters=parameters, storage_path=storage_path)
        async with self._jobs_lock:
            self._jobs[job_id] = job
        logger.info("Queued GNINA job %s", job_id)
        task = asyncio.create_task(self._run_job(job_id))
        self._background_tasks[job_id] = task
        task.add_done_callback(lambda finished: self._background_tasks.pop(job_id, None))
        return job

    async def get_job(self, job_id: str) -> Optional[GninaJob]:
        async with self._jobs_lock:
            return self._jobs.get(job_id)

    async def _persist_files(self, root: Path, files: Dict[str, Tuple[str, bytes]]) -> None:
        root.mkdir(parents=True, exist_ok=True)
        for key, data in files.items():
            filename, payload = data
            safe_name = Path(filename).name if filename else f"{key}.bin"
            target = root / "inputs" / safe_name
            target.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(target, "wb") as handle:
                await handle.write(payload)

    async def _run_job(self, job_id: str) -> None:
        job = await self.get_job(job_id)
        if not job:
            logger.error("Attempted to run unknown GNINA job %s", job_id)
            return

        try:
            job.mark_running()
            await self._write_status(job)
            await self._simulate_progress(job)
            payload = self._generate_result(job)
            job.mark_success(payload)
            await self._write_result_files(job, payload)
        except Exception as exc:  # noqa: BLE001 - unexpected runtime failures become failed jobs
            logger.exception("GNINA job %s failed", job_id)
            job.mark_failure(str(exc))
        finally:
            await self._write_status(job)

    async def _simulate_progress(self, job: GninaJob) -> None:
        total = max(1, int(self.settings.simulated_runtime_seconds))
        interval = max(0.1, self.settings.simulated_progress_interval)
        steps = max(1, int(total / interval))
        for index in range(steps):
            await asyncio.sleep(interval)
            fraction = min(0.9, (index + 1) / steps)
            job.mark_progress(fraction, message="Running GNINA docking simulation")
            await self._write_status(job)

    def _generate_result(self, job: GninaJob) -> Dict[str, Any]:
        pose_data = POSE_TEMPLATE.format(job_id=job.job_id, parameters=job.parameters)
        poses_relative_path = "results/docked_pose.pdbqt"
        return {
            "binding_affinity": -7.5,
            "poses": [
                {
                    "pose_rank": 1,
                    "score": -7.5,
                    "file_name": poses_relative_path,
                }
            ],
            "download_urls": {
                "pose": f"/api/v1/gnina/jobs/{job.job_id}/files/docked_pose.pdbqt",
            },
            "raw_pose_data": pose_data,
        }

    async def _write_result_files(self, job: GninaJob, payload: Dict[str, Any]) -> None:
        results_dir = job.storage_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        pose_path = results_dir / "docked_pose.pdbqt"
        pose_content = payload.get("raw_pose_data", "")
        async with aiofiles.open(pose_path, "w", encoding="utf-8") as handle:
            await handle.write(pose_content)
        payload.pop("raw_pose_data", None)
        summary_path = results_dir / "results.json"
        async with aiofiles.open(summary_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(job.to_result_payload()))

    async def _write_status(self, job: GninaJob) -> None:
        status_path = job.storage_path / "status.json"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(status_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(job.to_status_payload()))


job_manager = GninaJobManager()
