"""Ligand preparation adapter implementation using RDKit and OpenBabel."""

import logging
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

try:
    import requests
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError as e:
    requests = None
    Chem = None
    AllChem = None
    rdkit_import_error = e

from ...domain.entities.docking_job import MolecularStructure
from ...domain.exceptions import (
    DrugNameResolutionError,
    FormatConversionError,
    GeometryOptimizationError,
    LigandPreparationError,
    SMILESConversionError,
    StructureValidationError,
)
from ...ports.external.molecular_prep_port import MolecularPreparationPort

logger = logging.getLogger(__name__)


class RDKitLigandPrepAdapter(MolecularPreparationPort):
    """RDKit and OpenBabel-based ligand preparation implementation.

    Based on temp/scripts/prep_engine.py functionality for complete
    ligand preparation workflows from drug names to docking-ready structures.
    """

    def __init__(self):
        """Initialize ligand preparation adapter."""
        # Check for required dependencies
        if Chem is None or AllChem is None:
            raise ImportError(f"RDKit is required for ligand preparation: {rdkit_import_error}")
        if requests is None:
            raise ImportError("requests library is required for PubChem API access")

        # Supported formats
        self._input_formats = ["smiles", "sdf", "mol", "mol2"]
        self._output_formats = ["sdf", "mol2", "pdbqt", "mol"]

    async def fetch_smiles_from_drug_name(self, drug_name: str) -> str:
        """Fetch canonical SMILES string from PubChem.

        Based on prep_engine.py fetch_smiles method.

        Args:
            drug_name: Common drug name (e.g., "osimertinib")

        Returns:
            Canonical SMILES string

        Raises:
            DrugNameResolutionError: If drug name cannot be resolved
        """
        try:
            # PubChem REST API for compound lookup
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/property/CanonicalSMILES/JSON"

            logger.info(f"Fetching SMILES for drug: {drug_name}")

            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                raise DrugNameResolutionError(
                    f"PubChem query failed for {drug_name}: {response.status_code}"
                )

            try:
                data = response.json()
                smiles = data["PropertyTable"]["Properties"][0]["CanonicalSMILES"]
                logger.info(f"Found SMILES for {drug_name}: {smiles}")
                return smiles

            except (KeyError, IndexError) as e:
                raise DrugNameResolutionError(f"SMILES not found for {drug_name}: {str(e)}")

        except requests.RequestException as e:
            raise DrugNameResolutionError(
                f"Network error fetching SMILES for {drug_name}: {str(e)}"
            )

    async def smiles_to_3d_structure(
        self,
        smiles: str,
        name: Optional[str] = None,
        optimize: bool = True,
    ) -> MolecularStructure:
        """Convert SMILES string to optimized 3D molecular structure.

        Based on prep_engine.py smiles_to_3d_mol method.

        Args:
            smiles: SMILES string representation
            name: Optional molecule name
            optimize: Whether to perform geometry optimization

        Returns:
            3D molecular structure with optimized geometry

        Raises:
            SMILESConversionError: If 3D generation fails
        """
        try:
            logger.info(f"Converting SMILES to 3D structure: {smiles}")

            # Parse SMILES
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise SMILESConversionError(f"Invalid SMILES string: {smiles}")

            # Add hydrogens
            mol = Chem.AddHs(mol)

            # Generate 3D coordinates
            embed_result = AllChem.EmbedMolecule(mol)
            if embed_result != 0:
                # Try alternative embedding method
                embed_result = AllChem.EmbedMolecule(mol, randomSeed=42)
                if embed_result != 0:
                    raise SMILESConversionError("3D coordinate embedding failed")

            # Optimize geometry if requested
            if optimize:
                try:
                    AllChem.MMFFOptimizeMolecule(mol)
                    logger.debug("Geometry optimization completed with MMFF")
                except Exception as e:
                    logger.warning(f"MMFF optimization failed, trying UFF: {str(e)}")
                    try:
                        AllChem.UFFOptimizeMolecule(mol)
                        logger.debug("Geometry optimization completed with UFF")
                    except Exception as e2:
                        logger.warning(f"UFF optimization also failed: {str(e2)}")

            # Convert to MOL format
            mol_data = Chem.MolToMolBlock(mol)

            structure = MolecularStructure(
                name=name or f"mol_from_smiles",
                format="mol",
                data=mol_data,
                properties={
                    "smiles": smiles,
                    "optimized": optimize,
                    "num_atoms": mol.GetNumAtoms(),
                    "num_bonds": mol.GetNumBonds(),
                },
            )

            logger.info(f"Successfully converted SMILES to 3D structure: {structure.name}")
            return structure

        except Exception as e:
            if isinstance(e, SMILESConversionError):
                raise
            raise SMILESConversionError(f"3D structure generation failed: {str(e)}")

    async def convert_format(
        self,
        structure: MolecularStructure,
        target_format: str,
        add_hydrogens: bool = True,
    ) -> MolecularStructure:
        """Convert molecular structure between formats.

        Uses OpenBabel for format conversions like prep_engine.py convert_to_pdbqt method.

        Args:
            structure: Input molecular structure
            target_format: Desired output format (sdf, mol2, pdbqt, etc.)
            add_hydrogens: Whether to add explicit hydrogens

        Returns:
            Structure in target format

        Raises:
            FormatConversionError: If conversion fails
        """
        try:
            target_format = target_format.lower()
            if target_format not in self._output_formats:
                raise FormatConversionError(f"Unsupported target format: {target_format}")

            logger.info(f"Converting {structure.format} to {target_format}")

            # For RDKit-supported conversions, use RDKit directly
            if structure.format.lower() == "mol" and target_format == "sdf":
                # MOL to SDF is trivial (SDF is MOL with additional metadata)
                sdf_data = structure.data
                if not sdf_data.endswith("$$$$\n"):
                    sdf_data += "$$$$\n"

                return MolecularStructure(
                    name=structure.name,
                    format="sdf",
                    data=sdf_data,
                    properties=structure.properties.copy(),
                )

            # For other conversions, use OpenBabel
            return await self._convert_with_openbabel(structure, target_format, add_hydrogens)

        except Exception as e:
            if isinstance(e, FormatConversionError):
                raise
            raise FormatConversionError(f"Format conversion failed: {str(e)}")

    async def _convert_with_openbabel(
        self,
        structure: MolecularStructure,
        target_format: str,
        add_hydrogens: bool = True,
    ) -> MolecularStructure:
        """Convert format using OpenBabel command-line tool."""
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=f".{structure.format.lower()}", delete=False
            ) as input_file:
                input_file.write(structure.data)
                input_path = input_file.name

            with tempfile.NamedTemporaryFile(
                mode="r", suffix=f".{target_format}", delete=False
            ) as output_file:
                output_path = output_file.name

            try:
                # Build OpenBabel command
                cmd = [
                    "obabel",
                    f"-i{structure.format.lower()}",
                    input_path,
                    f"-o{target_format}",
                    "-O",
                    output_path,
                ]

                if add_hydrogens:
                    cmd.append("-h")  # Add hydrogens

                logger.debug(f"Running OpenBabel: {' '.join(cmd)}")

                # Run conversion
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode != 0:
                    raise FormatConversionError(f"OpenBabel conversion failed: {result.stderr}")

                # Read converted data
                with open(output_path, "r") as f:
                    converted_data = f.read()

                if not converted_data.strip():
                    raise FormatConversionError("OpenBabel produced empty output")

                converted_structure = MolecularStructure(
                    name=structure.name,
                    format=target_format,
                    data=converted_data,
                    properties=structure.properties.copy(),
                )

                logger.info(f"Successfully converted to {target_format}")
                return converted_structure

            finally:
                # Clean up temporary files
                import os

                try:
                    os.unlink(input_path)
                    os.unlink(output_path)
                except OSError:
                    pass

        except subprocess.TimeoutExpired:
            raise FormatConversionError("OpenBabel conversion timed out")
        except FileNotFoundError:
            raise FormatConversionError(
                "OpenBabel not found. Please install OpenBabel: conda install -c conda-forge openbabel"
            )

    async def optimize_geometry(
        self,
        structure: MolecularStructure,
        method: str = "mmff94",
    ) -> MolecularStructure:
        """Optimize molecular geometry using RDKit force field methods.

        Args:
            structure: Input molecular structure
            method: Optimization method (mmff94, uff, etc.)

        Returns:
            Structure with optimized geometry

        Raises:
            GeometryOptimizationError: If optimization fails
        """
        try:
            logger.info(f"Optimizing geometry with {method}")

            # Parse structure with RDKit
            if structure.format.lower() == "sdf":
                mol = Chem.MolFromMolBlock(structure.data, removeHs=False)
            elif structure.format.lower() == "mol":
                mol = Chem.MolFromMolBlock(structure.data, removeHs=False)
            else:
                raise GeometryOptimizationError(
                    f"Unsupported format for optimization: {structure.format}"
                )

            if mol is None:
                raise GeometryOptimizationError("Failed to parse molecular structure")

            # Optimize based on method
            if method.lower() == "mmff94":
                result = AllChem.MMFFOptimizeMolecule(mol)
                if result != 0:
                    raise GeometryOptimizationError("MMFF94 optimization failed to converge")
            elif method.lower() == "uff":
                result = AllChem.UFFOptimizeMolecule(mol)
                if result != 0:
                    raise GeometryOptimizationError("UFF optimization failed to converge")
            else:
                raise GeometryOptimizationError(f"Unsupported optimization method: {method}")

            # Convert back to original format
            optimized_data = Chem.MolToMolBlock(mol)
            if structure.format.lower() == "sdf" and not optimized_data.endswith("$$$$\n"):
                optimized_data += "$$$$\n"

            optimized_structure = MolecularStructure(
                name=structure.name,
                format=structure.format,
                data=optimized_data,
                properties={
                    **structure.properties,
                    "optimized": True,
                    "optimization_method": method,
                },
            )

            logger.info("Geometry optimization completed")
            return optimized_structure

        except Exception as e:
            if isinstance(e, GeometryOptimizationError):
                raise
            raise GeometryOptimizationError(f"Geometry optimization failed: {str(e)}")

    async def validate_structure(
        self,
        structure: MolecularStructure,
    ) -> Dict[str, Any]:
        """Validate molecular structure quality and properties.

        Args:
            structure: Molecular structure to validate

        Returns:
            Validation report with warnings/errors

        Raises:
            StructureValidationError: If validation fails
        """
        try:
            validation_report = {
                "valid": True,
                "warnings": [],
                "errors": [],
                "properties": {},
            }

            # Basic format validation
            if not structure.data or not structure.data.strip():
                validation_report["valid"] = False
                validation_report["errors"].append("Empty structure data")
                return validation_report

            # Try to parse with RDKit
            try:
                if structure.format.lower() in ["sdf", "mol"]:
                    mol = Chem.MolFromMolBlock(structure.data, removeHs=False)
                    if mol is None:
                        validation_report["valid"] = False
                        validation_report["errors"].append("Failed to parse molecular structure")
                        return validation_report

                    # Calculate basic properties
                    validation_report["properties"] = {
                        "num_atoms": mol.GetNumAtoms(),
                        "num_bonds": mol.GetNumBonds(),
                        "num_conformers": mol.GetNumConformers(),
                        "has_3d_coords": mol.GetNumConformers() > 0,
                        "molecular_weight": (
                            Chem.Descriptors.MolWt(mol) if hasattr(Chem, "Descriptors") else None
                        ),
                    }

                    # Validation checks
                    if mol.GetNumAtoms() == 0:
                        validation_report["warnings"].append("No atoms found in structure")

                    if mol.GetNumConformers() == 0:
                        validation_report["warnings"].append("No 3D coordinates found")

                    # Check for reasonable size
                    if mol.GetNumAtoms() > 1000:
                        validation_report["warnings"].append("Very large molecule (>1000 atoms)")

                else:
                    validation_report["warnings"].append(
                        f"Cannot validate format {structure.format} with RDKit"
                    )

            except Exception as e:
                validation_report["warnings"].append(f"RDKit validation failed: {str(e)}")

            logger.info(
                f"Structure validation completed: {len(validation_report['errors'])} errors, {len(validation_report['warnings'])} warnings"
            )
            return validation_report

        except Exception as e:
            raise StructureValidationError(f"Structure validation failed: {str(e)}")

    async def prepare_ligand_from_drug_name(
        self,
        drug_name: str,
        target_format: str = "sdf",
    ) -> MolecularStructure:
        """Complete ligand preparation pipeline from drug name.

        Based on prep_engine.py prepare_ligand method.

        Args:
            drug_name: Common drug name
            target_format: Desired output format

        Returns:
            Ready-to-dock ligand structure

        Raises:
            LigandPreparationError: If any step in pipeline fails
        """
        try:
            logger.info(f"Starting ligand preparation pipeline for: {drug_name}")

            # Step 1: Drug name → SMILES
            smiles = await self.fetch_smiles_from_drug_name(drug_name)

            # Step 2: SMILES → 3D structure
            structure = await self.smiles_to_3d_structure(smiles, name=drug_name, optimize=True)

            # Step 3: Format conversion if needed
            if target_format.lower() != structure.format.lower():
                structure = await self.convert_format(structure, target_format, add_hydrogens=True)

            # Step 4: Validation
            validation = await self.validate_structure(structure)
            if not validation["valid"]:
                raise LigandPreparationError(
                    f"Prepared ligand failed validation: {validation['errors']}"
                )

            if validation["warnings"]:
                logger.warning(f"Ligand preparation warnings: {validation['warnings']}")

            logger.info(f"Ligand preparation completed successfully: {structure.name}")
            return structure

        except Exception as e:
            if isinstance(
                e,
                (
                    DrugNameResolutionError,
                    SMILESConversionError,
                    FormatConversionError,
                    StructureValidationError,
                ),
            ):
                raise LigandPreparationError(f"Ligand preparation failed: {str(e)}")
            raise LigandPreparationError(f"Unexpected error in ligand preparation: {str(e)}")

    def get_supported_input_formats(self) -> List[str]:
        """Get list of supported input molecular formats."""
        return self._input_formats.copy()

    def get_supported_output_formats(self) -> List[str]:
        """Get list of supported output molecular formats."""
        return self._output_formats.copy()
