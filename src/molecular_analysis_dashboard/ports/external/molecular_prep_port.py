"""Abstract port for molecular preparation services."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...domain.entities.docking_job import MolecularStructure


class MolecularPreparationPort(ABC):
    """Abstract interface for molecular preparation and conversion services.

    This port handles ligand preparation workflows including:
    - SMILES resolution from drug names
    - 3D conformer generation
    - Format conversions
    - Structure optimization
    """

    @abstractmethod
    async def fetch_smiles_from_drug_name(self, drug_name: str) -> str:
        """Fetch canonical SMILES string from drug name.

        Uses PubChem API or similar service to resolve drug names
        to standardized SMILES representations.

        Args:
            drug_name: Common drug name (e.g., "osimertinib")

        Returns:
            Canonical SMILES string

        Raises:
            DrugNameResolutionError: If drug name cannot be resolved
        """
        pass

    @abstractmethod
    async def smiles_to_3d_structure(
        self,
        smiles: str,
        name: Optional[str] = None,
        optimize: bool = True,
    ) -> MolecularStructure:
        """Convert SMILES string to optimized 3D molecular structure.

        Args:
            smiles: SMILES string representation
            name: Optional molecule name
            optimize: Whether to perform geometry optimization

        Returns:
            3D molecular structure with optimized geometry

        Raises:
            SMILESConversionError: If 3D generation fails
        """
        pass

    @abstractmethod
    async def convert_format(
        self,
        structure: MolecularStructure,
        target_format: str,
        add_hydrogens: bool = True,
    ) -> MolecularStructure:
        """Convert molecular structure between formats.

        Args:
            structure: Input molecular structure
            target_format: Desired output format (sdf, mol2, pdbqt, etc.)
            add_hydrogens: Whether to add explicit hydrogens

        Returns:
            Structure in target format

        Raises:
            FormatConversionError: If conversion fails
        """
        pass

    @abstractmethod
    async def optimize_geometry(
        self,
        structure: MolecularStructure,
        method: str = "mmff94",
    ) -> MolecularStructure:
        """Optimize molecular geometry using force field methods.

        Args:
            structure: Input molecular structure
            method: Optimization method (mmff94, uff, etc.)

        Returns:
            Structure with optimized geometry

        Raises:
            GeometryOptimizationError: If optimization fails
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def prepare_ligand_from_drug_name(
        self,
        drug_name: str,
        target_format: str = "sdf",
    ) -> MolecularStructure:
        """Complete ligand preparation pipeline from drug name.

        Convenience method that combines:
        1. Drug name → SMILES resolution
        2. SMILES → 3D structure generation
        3. Format conversion to target format
        4. Geometry optimization

        Args:
            drug_name: Common drug name
            target_format: Desired output format

        Returns:
            Ready-to-dock ligand structure

        Raises:
            LigandPreparationError: If any step in pipeline fails
        """
        pass

    @abstractmethod
    def get_supported_input_formats(self) -> List[str]:
        """Get list of supported input molecular formats."""
        pass

    @abstractmethod
    def get_supported_output_formats(self) -> List[str]:
        """Get list of supported output molecular formats."""
        pass
