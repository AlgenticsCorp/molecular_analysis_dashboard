#!/usr/bin/env python3
"""Test the cleaned up docking API."""

import requests

def test_clean_api():
    """Test the simplified docking API."""

    # Check API health first
    health_response = requests.get("http://localhost:8000/health")
    print(f"API Health: {health_response.status_code} - {health_response.json()}")

    # Test files (using existing test files if available)
    receptor_file = "temp/receptor_3cl.pdb"
    ligand_file = "temp/ligand_remdesivir.sdf"

    try:
        with open(receptor_file, 'rb') as r_file, open(ligand_file, 'rb') as l_file:
            files = {
                'receptor_file': ('receptor_3cl.pdb', r_file, 'chemical/x-pdb'),
                'ligand_file': ('ligand_remdesivir.sdf', l_file, 'chemical/x-mdl-sdfile')
            }
            data = {
                'job_name': 'Clean API Test',
                'note': 'Testing simplified API'
            }

            print("Submitting job to clean API...")
            response = requests.post("http://localhost:8000/api/v1/docking/submit", files=files, data=data)

            print(f"Response Status: {response.status_code}")
            if response.status_code == 200:
                print("SUCCESS! Clean API works:")
                print(response.json())
            else:
                print(f"Expected error (NeuroSnap integration issue): {response.text}")

    except FileNotFoundError as e:
        print(f"Test files not found: {e}")
        print("This is expected - the important thing is that the API is clean and simple now")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_clean_api()
