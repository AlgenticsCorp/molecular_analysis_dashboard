import asyncio
import json
import pytest

from molecular_analysis_dashboard.adapters.providers.neurosnap_task_adapter import (
    NeuroSnapAutoDockVinaAdapter,
)


class _DummyFileService:
    async def get_file_content(self, file_id):  # noqa: D401 - simple stub
        await asyncio.sleep(0)
        if file_id == "lig1":
            return b"MOCK_LIGAND"
        raise RuntimeError("unexpected file_id")


@pytest.mark.asyncio
async def test_build_ligand_payload_supports_file_and_entries():
    adapter = NeuroSnapAutoDockVinaAdapter(base_url="https://example.com")
    params = {
        "ligand_file": {
            "file_id": "lig1",
            "filename": "ligand.sdf",
            "content_type": "chemical/x-mdl-sdfile",
        },
        "ligand_entries_json": json.dumps([
            {"data": "C=C=C", "type": "smiles"},
        ]),
    }

    payload = await adapter._build_ligand_payload(_DummyFileService(), params)
    ligands = json.loads(payload)

    assert any(entry["type"] == "sdf" for entry in ligands)
    assert any(entry["data"] == "C=C=C" and entry["type"] == "smiles" for entry in ligands)


@pytest.mark.asyncio
async def test_build_ligand_payload_rejects_invalid_json():
    adapter = NeuroSnapAutoDockVinaAdapter(base_url="https://example.com")
    params = {"ligand_entries_json": "{invalid"}

    with pytest.raises(RuntimeError, match="valid JSON"):
        await adapter._build_ligand_payload(_DummyFileService(), params)


def test_infer_ligand_type_from_extension():
    adapter = NeuroSnapAutoDockVinaAdapter(base_url="https://example.com")
    assert adapter._infer_ligand_type("example.smi", None) == "smiles"
    assert adapter._infer_ligand_type("example.pdbqt", None) == "pdbqt"
    assert adapter._infer_ligand_type(None, "chemical/x-mdl-sdfile") == "sdf"
