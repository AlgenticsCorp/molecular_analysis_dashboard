"""Legacy AMBER relaxation endpoints now delegated to unified task framework."""

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(
    prefix="/api/v1/providers/neurosnap/molecular-dynamics",
    tags=["🔬 Molecular Dynamics", "☁️ NeuroSnap Cloud"],
)


@router.post("/amber-relaxation/submit")
async def submit_amber_relaxation_job(
    structure_file: UploadFile = File(..., description="Input protein structure in PDB format"),
    max_iterations: int = 2500,
    tolerance: float = 1.0,
    job_name: str = "AMBER Relaxation",
    note: str = "Molecular dynamics relaxation analysis",
):
    """Return deprecation guidance for the legacy AMBER submission endpoint."""

    del structure_file, max_iterations, tolerance, job_name, note

    raise HTTPException(
        status_code=410,
        detail="Endpoint retired. Use POST /api/v1/tasks-unified/neurosnap-amber-relaxation/execute instead.",
    )


@router.post("/amber-relaxation/submit-simple")
async def submit_simple_amber_relaxation_job(
    structure_file: UploadFile = File(..., description="Input protein structure in PDB format"),
    job_name: str = "Simple AMBER Relaxation",
):
    """Return deprecation guidance for the simplified AMBER endpoint."""

    del structure_file, job_name

    raise HTTPException(
        status_code=410,
        detail="Endpoint retired. Use POST /api/v1/tasks-unified/neurosnap-amber-relaxation/execute instead.",
    )
