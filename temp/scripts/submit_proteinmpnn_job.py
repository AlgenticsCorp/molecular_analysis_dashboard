import os
import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from dotenv import load_dotenv

def submit_proteinmpnn_job(
    structure_file,
    job_note="ProteinMPNN stability scoring",
    model_type="v_48_020",
    model_version="original",
    num_sequences="100",
    sampling_temp="0.1",
    homo_oligomer=False,
    fixed_positions=None
):
    # Load API key
    load_dotenv()
    api_key = os.getenv("NEUROSNAP_API_KEY")  # Reusing the same variable for convenience

    if not api_key:
        raise ValueError("❌ API key not found in .env file as NEUROSNAP_API_KEY")

    # Read PDB structure
    with open(structure_file) as f:
        pdb_data = f.read()

    # Build fields
    fields = {
        "Input Structure": json.dumps([
            {
                "type": "pdb",
                "name": os.path.basename(structure_file).split('.')[0],
                "data": pdb_data
            }
        ]),
        "Model Type": model_type,
        "Model Version": model_version,
        "Number Sequences": num_sequences,
        "Sampling Temperature": sampling_temp,
    }

    if homo_oligomer:
        fields["Homo-oligomer"] = "true"

    if fixed_positions:
        fields["Fixed Positions"] = fixed_positions

    # Add zero biases for all amino acids
    amino_acids = [
        "Alanine", "Arginine", "Asparagine", "Aspartic acid", "Cysteine",
        "Glutamine", "Glutamic acid", "Glycine", "Histidine", "Isoleucine",
        "Leucine", "Lysine", "Methionine", "Phenylalanine", "Proline",
        "Serine", "Threonine", "Tryptophan", "Tyrosine", "Valine"
    ]
    for aa in amino_acids:
        fields[f"{aa} Bias"] = "0"

    # Create multipart payload
    multipart_data = MultipartEncoder(fields=fields)

    # Send API request
    response = requests.post(
        f"https://neurosnap.ai/api/job/submit/ProteinMPNN?note={job_note}",
        headers={
            "X-API-KEY": api_key,
            "Content-Type": multipart_data.content_type
        },
        data=multipart_data
    )

    # Handle response
    if response.status_code == 200:
        job_info = response.json()
        print("✅ ProteinMPNN job submitted successfully.")
        # print("Job ID:", job_info.get("job_id", "Unknown"))
        return job_info
    else:
        print("❌ Failed to submit ProteinMPNN job.")
        print("Status Code:", response.status_code)
        print(response.text)
        return None
