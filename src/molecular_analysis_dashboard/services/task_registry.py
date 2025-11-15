"""Task registry for loading framework task adapters and metadata."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_TASK_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "tasks"


class TaskRegistry:
    """Registry that loads framework task configurations from disk."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self.config_dir = Path(config_dir) if config_dir else DEFAULT_TASK_CONFIG_DIR
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._errors: Dict[str, str] = {}
        self.reload()

    @property
    def errors(self) -> Dict[str, str]:
        """Return loading errors keyed by filename."""
        return deepcopy(self._errors)

    def reload(self) -> None:
        """Reload task configurations from the config directory."""
        self._tasks.clear()
        self._errors.clear()

        if not self.config_dir.exists():
            logger.warning("Task registry directory does not exist: %s", self.config_dir)
            return

        for entry in sorted(self.config_dir.glob("*.json")):
            try:
                with entry.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)

                task_id = data.get("id")
                if not task_id:
                    raise ValueError("Task configuration missing required 'id' field")

                if task_id in self._tasks:
                    raise ValueError(f"Duplicate task identifier detected: {task_id}")

                self._tasks[task_id] = data
                logger.debug("Registered task '%s' from %s", task_id, entry)

            except Exception as exc:  # noqa: BLE001 - need to capture loader errors generically
                self._errors[entry.name] = str(exc)
                logger.error("Failed to load task config %s: %s", entry, exc)

    def get_task_config(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Return the raw configuration for a task."""
        task = self._tasks.get(task_id)
        return deepcopy(task) if task else None

    def get_metadata(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Return the metadata section for a task."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        metadata = task.get("metadata") or {}
        return deepcopy(metadata)

    def get_adapter_config(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Return adapter configuration details for a task."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        adapter = task.get("adapter") or {}
        return deepcopy(adapter)

    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Return all task configurations keyed by task identifier."""
        return deepcopy(self._tasks)

    def list_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Return metadata for all registered tasks keyed by task identifier."""
        return {task_id: deepcopy(cfg.get("metadata", {})) for task_id, cfg in self._tasks.items()}