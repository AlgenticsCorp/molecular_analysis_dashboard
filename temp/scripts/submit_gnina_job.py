import os
import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from dotenv import load_dotenv

def submit_gnina_job(receptor_file, ligand_file=None, job_note="GNINA docking job"):
    # Load API key from .env file
    load_dotenv()
    API_KEY = os.getenv("NEUROSNAP_API_KEY")

    if not API_KEY:
        raise ValueError("❌ API key not found in .env file. Set NEUROSNAP_API_KEY")

    # Read receptor structure (can be AlphaFold3 output with or without ligand)
    with open(receptor_file) as f:
        receptor_data = f.read()

    # Base fields with receptor only
    fields = {
        "Input Receptor": json.dumps([
            {
                "type": "pdb",
                "name": os.path.basename(receptor_file).split('.')[0],
                "data": receptor_data
            }
        ])
    }

    # If ligand is specified and needed (e.g., for rescoring or custom ligand)
    if ligand_file and os.path.exists(ligand_file):
        with open(ligand_file) as f:
            ligand_data = f.read()
        fields["Input Ligand"] = json.dumps([
            {
                "type": "sdf",
                "data": ligand_data
            }
        ])

    # Build and send the multipart request
    multipart_data = MultipartEncoder(fields=fields)

    response = requests.post(
        f"https://neurosnap.ai/api/job/submit/GNINA?note={job_note}",
        headers={
            "X-API-KEY": API_KEY,
            "Content-Type": multipart_data.content_type
        },
        data=multipart_data
    )

    # Handle response
    if response.status_code == 200:
        job_info = response.json()
        print("✅ GNINA job submitted successfully.")
        # print("Job ID:", job_info.get("job_id", "Unknown"))
        return job_info
    else:
        print("❌ GNINA job submission failed.")
        print(f"Status Code: {response.status_code}")
        print(response.text)
        return None
