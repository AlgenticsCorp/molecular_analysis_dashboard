import os
import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from dotenv import load_dotenv

def submit_alphafold3_job(
    sequence_aa: dict,
    ligand_file: str = None,
    job_note: str = "AlphaFold3 (Boltz-1) structure prediction",
    model_version: str = "Boltz-1x (with potentials)",
    msa_mode: str = "mmseqs2_uniref_env",
    num_recycles: str = "6",
    sampling_steps: str = "200",
    diffusion_samples: str = "5",
    step_scale: str = "1.638"
):
    # Load API key
    load_dotenv()
    api_key = os.getenv("NEUROSNAP_API_KEY")  # Reusing same key

    if not api_key:
        raise ValueError("❌ API key not found in .env file as NEUROSNAP_API_KEY")

    fields = {
        "Input Sequences": json.dumps({"aa": sequence_aa}),
        "Model Version": model_version,
        "MSA Mode": msa_mode,
        "Number Recycles": num_recycles,
        "Sampling Steps": sampling_steps,
        "Diffusion Samples": diffusion_samples,
        "Step Scale": step_scale,
    }

    if ligand_file and os.path.exists(ligand_file):
        with open(ligand_file) as f:
            ligand_data = f.read()
        fields["Input Molecules"] = json.dumps([{"type": "sdf", "data": ligand_data}])

    multipart_data = MultipartEncoder(fields=fields)

    response = requests.post(
        f"https://neurosnap.ai/api/job/submit/Boltz-1 (AlphaFold3)?note={job_note}",
        headers={
            "X-API-KEY": api_key,
            "Content-Type": multipart_data.content_type
        },
        data=multipart_data
    )

    try:
        job_info = response.json()
        print("✅ AlphaFold3 job submitted successfully.")
        # print("Job ID:", job_info.get("job_id", "Unknown"))
        return job_info
    except json.JSONDecodeError:
        print("❌ Response is not JSON:")
        print(response.text)
        return None
