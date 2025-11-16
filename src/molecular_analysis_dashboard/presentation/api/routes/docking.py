"""Legacy NeuroSnap docking endpoints.

These routes previously implemented direct integrations with the NeuroSnap GNINA
API. The unified task framework now handles execution, status polling, and file
management for docking jobs. The endpoints below explicitly signal their
deprecation and guide callers to the replacement route so we do not maintain two
separate integration paths.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter(
    prefix="/api/v1/providers/neurosnap/docking",
    tags=["🎯 Molecular Docking", "☁️ NeuroSnap Cloud"],
)


@router.post("/submit")
async def submit_job(
    receptor_file: UploadFile = File(..., description="Protein receptor structure in PDB format"),
    ligand_file: UploadFile = File(..., description="Ligand molecule structure in SDF format"),
    job_name: str = Form(default="GNINA Docking"),
    note: str = Form(default="Docking analysis"),
):
    """Return deprecation guidance for the legacy submission endpoint."""

    # Explicitly mark unused parameters to keep FastAPI schema definitions intact.
    del receptor_file, ligand_file, job_name, note

    raise HTTPException(
        status_code=410,
        detail="Endpoint retired. Use POST /api/v1/tasks-unified/gnina-molecular-docking/execute instead.",
    )
