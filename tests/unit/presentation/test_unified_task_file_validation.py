import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile
from io import BytesIO

from molecular_analysis_dashboard.presentation.api.routes import unified_tasks


def _make_upload(filename: str, content: bytes = b"data", content_type: str = "application/octet-stream") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content), content_type=content_type)


def test_validate_file_upload_accepts_allowed_extension():
    spec = {"validation": {"file_types": [".pdb", ".pdbqt"]}}
    upload = _make_upload("structure.pdb")

    try:
        unified_tasks._validate_file_upload("receptor_file", upload, b"test", spec)
    except HTTPException as exc:  # pragma: no cover
        pytest.fail(f"Unexpected validation error: {exc.detail}")


def test_validate_file_upload_rejects_disallowed_extension():
    spec = {"validation": {"file_types": [".pdb", ".pdbqt"]}}
    upload = _make_upload("ligand.sdf")

    with pytest.raises(HTTPException) as ctx:
        unified_tasks._validate_file_upload("receptor_file", upload, b"test", spec)

    assert ctx.value.status_code == 400
    assert "receptor_file" in ctx.value.detail


def test_validate_file_upload_rejects_oversized_file():
    spec = {"validation": {"max_size_mb": 1}}
    upload = _make_upload("big_file.pdb")
    oversized_content = b"0" * (2 * 1024 * 1024)

    with pytest.raises(HTTPException) as ctx:
        unified_tasks._validate_file_upload("receptor_file", upload, oversized_content, spec)

    assert ctx.value.status_code == 400
    assert "maximum allowed size" in ctx.value.detail
