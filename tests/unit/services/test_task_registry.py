import json
from pathlib import Path

from molecular_analysis_dashboard.services.task_registry import TaskRegistry


def _write_config(tmp_path: Path, filename: str, payload: dict) -> Path:
    path = tmp_path / filename
    path.write_text(json.dumps(payload))
    return path


def _build_valid_config(**overrides: object) -> dict:
    config = {
        "id": "sample-task",
        "adapter": {
            "module": "molecular_analysis_dashboard.adapters.providers.neurosnap_task_adapter",
            "class": "NeuroSnapDockingAdapter",
        },
        "metadata": {
            "name": "Sample Task",
            "description": "Run a sample docking job",
            "category": "external",
            "parameters": [
                {
                    "name": "ligand_file",
                    "type": "file",
                    "description": "Ligand structure",
                }
            ],
        },
    }
    config.update(overrides)
    return config


def test_loads_valid_task_config(tmp_path: Path) -> None:
    _write_config(tmp_path, "valid.json", _build_valid_config())

    registry = TaskRegistry(config_dir=tmp_path)

    assert registry.errors == {}
    task = registry.get_task_config("sample-task")
    assert task is not None
    metadata = registry.get_metadata("sample-task")
    assert metadata is not None
    assert metadata["name"] == "Sample Task"


def test_rejects_missing_parameter_name(tmp_path: Path) -> None:
    invalid_config = _build_valid_config()
    invalid_config["metadata"]["parameters"][0].pop("name")
    _write_config(tmp_path, "missing-name.json", invalid_config)

    registry = TaskRegistry(config_dir=tmp_path)

    assert "missing-name.json" in registry.errors
    message = registry.errors["missing-name.json"]
    assert "metadata.parameters[0].name is required" in message
    assert registry.get_task_config("sample-task") is None


def test_rejects_missing_adapter_module(tmp_path: Path) -> None:
    invalid_config = _build_valid_config()
    invalid_config["adapter"].pop("module")
    invalid_config["id"] = "broken-task"
    _write_config(tmp_path, "missing-module.json", invalid_config)

    registry = TaskRegistry(config_dir=tmp_path)

    assert "missing-module.json" in registry.errors
    message = registry.errors["missing-module.json"]
    assert "adapter.module is required" in message
    assert registry.get_task_config("broken-task") is None
