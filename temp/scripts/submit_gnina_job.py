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

    print(f"📁 Reading files: receptor={receptor_file}, ligand={ligand_file}")

    # Use the CORRECT format from working example
    fields = {}

    # Receptor: tuple format (filename, binary_data)
    fields["Input Receptor"] = (os.path.basename(receptor_file), open(receptor_file, "rb"))

    # If ligand is specified - use JSON format with data first, then type
    if ligand_file and os.path.exists(ligand_file):
        with open(ligand_file, 'r') as f:
            ligand_data = f.read()
        fields["Input Ligand"] = json.dumps([{"data": ligand_data, "type": "sdf"}])
        print(f"✅ Added ligand: {ligand_file}")

    print(f"📤 Submitting GNINA job with correct format...")

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

    print(f"📥 Response: {response.status_code} - {response.text[:100]}...")

    # Handle response
    if response.status_code == 200:
        job_info = response.json()
        print("✅ GNINA job submitted successfully.")
        return job_info
    else:
        print("❌ GNINA job submission failed.")
        print(f"Status Code: {response.status_code}")
        print(response.text)
        return None
