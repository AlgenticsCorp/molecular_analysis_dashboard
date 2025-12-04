"""Unit tests for ExecutionFileService cleanup helpers."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, List
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock

from molecular_analysis_dashboard.adapters.storage.file_storage import FileStorageAdapter
from molecular_analysis_dashboard.services.execution_file_service import ExecutionFileService


class _FakeResult:
    """Simple result wrapper matching SQLAlchemy API surface used in tests."""

    def __init__(self, rows: List[Any] | None = None) -> None:
        self._rows = rows or []

    def fetchall(self) -> List[Any]:
        return list(self._rows)


@pytest.mark.asyncio
async def test_delete_execution_files_removes_local_files(tmp_path, monkeypatch):
    """Deleting execution files removes DB rows and prunes storage artifacts."""

    storage_root = tmp_path / "storage"
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))

    adapter = FileStorageAdapter(storage_root=str(storage_root))
    service = ExecutionFileService(storage_adapter=adapter)

    execution_id = uuid4()
    relative_path = f"/uploads/system/{execution_id}/input.pdb"
    file_path = storage_root / "uploads" / "system" / str(execution_id)
    absolute_path = file_path / "input.pdb"
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_text("data")

    select_rows = [(str(uuid4()), "local", relative_path)]

    fake_session = AsyncMock()

    async def execute_side_effect(query, params):
        await asyncio.sleep(0)
        statement = str(query).strip().upper()
        if statement.startswith("SELECT"):
            return _FakeResult(select_rows)
        return _FakeResult()

    fake_session.execute.side_effect = execute_side_effect
    fake_session.commit = AsyncMock()

    @asynccontextmanager
    async def fake_get_metadata_session():
        yield fake_session

    monkeypatch.setattr(
        "molecular_analysis_dashboard.services.execution_file_service.get_metadata_session",
        fake_get_metadata_session,
    )

    result = await service.delete_execution_files(execution_id)

    assert result == {"deleted": 1, "failed": 0}
    assert not absolute_path.exists()
    assert not file_path.exists()
    assert fake_session.execute.await_count == 2
    fake_session.commit.assert_awaited_once()


def test_safe_remove_handles_read_only_files(tmp_path, monkeypatch):
    """_safe_remove should remove read-only files and clean empty folders."""

    storage_root = tmp_path / "storage"
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))

    adapter = FileStorageAdapter(storage_root=str(storage_root))
    service = ExecutionFileService(storage_adapter=adapter)

    execution_id = uuid4()
    relative_path = f"/uploads/system/{execution_id}/readonly.pdb"
    file_path = storage_root / "uploads" / "system" / str(execution_id)
    absolute_path = file_path / "readonly.pdb"
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_text("data")
    absolute_path.chmod(0o400)

    assert service._safe_remove(relative_path) is True
    assert not absolute_path.exists()
    assert not file_path.exists()
