"""Configuration helpers for the GNINA microservice."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class GninaServiceSettings:
    """Loads runtime settings for the GNINA microservice."""

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        simulated_runtime_seconds: Optional[float] = None,
        simulated_progress_interval: Optional[float] = None,
    ) -> None:
        storage_root = storage_dir or os.getenv("GNINA_SERVICE_STORAGE_DIR") or "/tmp/gnina_service"
        self.storage_dir = Path(storage_root)
        runtime_value = simulated_runtime_seconds or os.getenv("GNINA_SIMULATED_RUNTIME_SECONDS") or "6"
        interval_value = simulated_progress_interval or os.getenv("GNINA_SIMULATED_PROGRESS_INTERVAL") or "1.5"
        self.simulated_runtime_seconds = float(runtime_value)
        self.simulated_progress_interval = float(interval_value)

    def prepare(self) -> None:
        """Ensure required directories are present before handling requests."""

        self.storage_dir.mkdir(parents=True, exist_ok=True)


settings = GninaServiceSettings()
