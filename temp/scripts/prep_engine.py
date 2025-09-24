"""
prep_engine.py

Ligand and Protein Preparation Module for Docking Workflows.

This module automates the preparation of molecules for docking using:
- RDKit (3D conformer generation, optimization)
- OpenBabel (format conversion)
- PubChem API (SMILES resolution from drug name)

Author: Ahmad Abboud, Algentics
"""

import os
import subprocess
import logging
from rdkit import Chem
from rdkit.Chem import AllChem
import requests

logging.basicConfig(level=logging.INFO)

class LigandPreparationError(Exception):
    """Custom exception for ligand preparation errors."""
    pass

class MoleculePreparator:
    """
    Handles preparation of ligand molecules:
    1. Fetch SMILES by drug name.
    2. Generate 3D conformer and optimize.
    3. Convert to docking format (e.g., PDBQT).
    """

    def __init__(self, output_dir: str = "./data/ligands"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_smiles(self, drug_name: str) -> str:
        """
        Fetches canonical SMILES string from PubChem using the drug name.
        """
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/property/CanonicalSMILES/JSON"
        r = requests.get(url)
        if r.status_code != 200:
            raise LigandPreparationError(f"Failed to query PubChem for {drug_name}")
        try:
            return r.json()['PropertyTable']['Properties'][0]['CanonicalSMILES']
        except Exception:
            raise LigandPreparationError(f"SMILES not found for {drug_name}")

    def smiles_to_3d_mol(self, smiles: str) -> Chem.Mol:
        """
        Converts SMILES string into a 3D RDKit molecule with hydrogens and optimized geometry.
        """
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            raise LigandPreparationError("Invalid SMILES string")
        mol = Chem.AddHs(mol)
        if AllChem.EmbedMolecule(mol) != 0:
            raise LigandPreparationError("3D embedding failed")
        AllChem.MMFFOptimizeMolecule(mol)
        return mol

    def save_mol_file(self, mol: Chem.Mol, mol_path: str):
        """
        Saves the RDKit molecule to a MOL file.
        """
        Chem.MolToMolFile(mol, mol_path)

    def convert_to_pdbqt(self, mol_path: str, pdbqt_path: str):
        """
        Uses OpenBabel to convert MOL file to PDBQT format.
        """
        command = f"obabel -imol {mol_path} -opdbqt -O {pdbqt_path}"
        result = subprocess.run(command, shell=True, capture_output=True)
        if result.returncode != 0:
            raise LigandPreparationError("OpenBabel conversion failed:\n" + result.stderr.decode())

    def prepare_ligand(self, drug_name: str) -> str:
        """
        Main workflow to go from drug name → SMILES → MOL → PDBQT.
        Returns path to the prepared ligand file.
        """
        logging.info(f"Preparing ligand for: {drug_name}")
        smiles = self.fetch_smiles(drug_name)
        mol = self.smiles_to_3d_mol(smiles)

        mol_path = os.path.join(self.output_dir, f"{drug_name}.mol")
        pdbqt_path = os.path.join(self.output_dir, f"{drug_name}.pdbqt")

        self.save_mol_file(mol, mol_path)
        self.convert_to_pdbqt(mol_path, pdbqt_path)
        logging.info(f"Ligand prepared: {pdbqt_path}")
        return pdbqt_path

    def validate_preparation(self, pdbqt_path: str) -> bool:
        """
        Basic validation to check that the final PDBQT file exists and is not empty.
        """
        if not os.path.exists(pdbqt_path):
            logging.warning("PDBQT file not found.")
            return False
        if os.path.getsize(pdbqt_path) < 500:  # heuristic threshold
            logging.warning("PDBQT file seems too small, check output.")
            return False
        return True
