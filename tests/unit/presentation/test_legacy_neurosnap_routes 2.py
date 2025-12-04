from fastapi.testclient import TestClient

from molecular_analysis_dashboard.presentation.api.main import app


client = TestClient(app)


def test_legacy_docking_endpoint_returns_410() -> None:
    files = {
        "receptor_file": ("receptor.pdb", b"ATOM", "application/octet-stream"),
        "ligand_file": ("ligand.sdf", b"HEADER", "application/octet-stream"),
    }

    response = client.post(
        "/api/v1/providers/neurosnap/docking/submit",
        files=files,
        data={"job_name": "GNINA", "note": "Legacy"},
    )

    assert response.status_code == 410
    assert response.json() == {
        "detail": "Endpoint retired. Use POST /api/v1/tasks-unified/gnina-molecular-docking/execute instead.",
    }


def test_legacy_amber_relaxation_endpoint_returns_410() -> None:
    response = client.post(
        "/api/v1/providers/neurosnap/molecular-dynamics/amber-relaxation/submit",
        files={"structure_file": ("structure.pdb", b"ATOM", "application/octet-stream")},
        data={"max_iterations": 1000, "tolerance": 0.5, "job_name": "Amber", "note": "Legacy"},
    )

    assert response.status_code == 410
    assert response.json() == {
        "detail": "Endpoint retired. Use POST /api/v1/tasks-unified/neurosnap-amber-relaxation/execute instead.",
    }


def test_simple_amber_endpoint_returns_410() -> None:
    response = client.post(
        "/api/v1/providers/neurosnap/molecular-dynamics/amber-relaxation/submit-simple",
        files={"structure_file": ("structure.pdb", b"ATOM", "application/octet-stream")},
        data={"job_name": "Amber Simple"},
    )

    assert response.status_code == 410
    assert response.json() == {
        "detail": "Endpoint retired. Use POST /api/v1/tasks-unified/neurosnap-amber-relaxation/execute instead.",
    }
