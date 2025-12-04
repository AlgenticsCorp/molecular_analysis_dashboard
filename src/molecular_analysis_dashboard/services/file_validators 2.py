"""
File validators for molecular structure formats.

This module provides validation classes for different molecular file formats
used in computational chemistry and structural biology:
- PDB (Protein Data Bank)
- SDF (Structure Data File)
- PDBQT (AutoDock PDBQT)
- MOL2 (Tripos MOL2)
- XYZ (XYZ coordinate file)

Each validator checks format-specific requirements and returns detailed
validation results including atom counts, structural information, and errors.
"""

import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Raised when file validation fails."""
    
    pass


class PDBValidator:
    """Validate PDB (Protein Data Bank) format files."""
    
    @staticmethod
    def validate(content: bytes) -> Dict[str, Any]:
        """
        Validate PDB file structure and extract metadata.
        
        Args:
            content: Raw file bytes
            
        Returns:
            Dictionary with validation results:
            - is_valid: bool
            - atom_count: int
            - hetatm_count: int
            - has_coordinates: bool
            - has_header: bool
            - format: str
            - errors: list
            - warnings: list
            
        Raises:
            FileValidationError: If file cannot be decoded or is severely malformed
        """
        errors = []
        warnings = []
        
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = content.decode("latin-1")
                warnings.append("File decoded with latin-1 encoding instead of UTF-8")
            except Exception as e:
                raise FileValidationError(f"Cannot decode PDB file: {str(e)}")
        
        lines = content_str.split("\n")
        
        # Count record types
        atom_count = sum(1 for line in lines if line.startswith("ATOM  "))
        hetatm_count = sum(1 for line in lines if line.startswith("HETATM"))
        total_atoms = atom_count + hetatm_count
        
        # Check for header
        has_header = any(line.startswith("HEADER") for line in lines[:50])
        if not has_header:
            warnings.append("No HEADER record found")
        
        # Check for END record
        has_end = any(line.startswith("END") for line in lines[-10:])
        if not has_end:
            warnings.append("No END record found")
        
        # Validate coordinate lines (check first few ATOM lines)
        has_coordinates = False
        coordinate_issues = []
        
        for i, line in enumerate(lines):
            if line.startswith("ATOM  ") or line.startswith("HETATM"):
                if len(line) < 54:  # Minimum length for coordinates
                    coordinate_issues.append(f"Line {i+1}: Too short for coordinates")
                    continue
                
                try:
                    # Try to parse coordinates (columns 31-54)
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip())
                    z = float(line[46:54].strip())
                    has_coordinates = True
                    break  # Found valid coordinates
                except (ValueError, IndexError):
                    coordinate_issues.append(f"Line {i+1}: Invalid coordinate format")
                
                if len(coordinate_issues) > 5:
                    break  # Don't check all lines
        
        # Validation rules
        if total_atoms == 0:
            errors.append("No ATOM or HETATM records found")
        
        if not has_coordinates:
            errors.append("No valid coordinates found in ATOM/HETATM records")
        
        if coordinate_issues:
            warnings.extend(coordinate_issues[:3])  # Only show first 3
            if len(coordinate_issues) > 3:
                warnings.append(f"... and {len(coordinate_issues) - 3} more coordinate issues")
        
        is_valid = len(errors) == 0 and total_atoms > 0 and has_coordinates
        
        return {
            "is_valid": is_valid,
            "atom_count": atom_count,
            "hetatm_count": hetatm_count,
            "total_atoms": total_atoms,
            "has_coordinates": has_coordinates,
            "has_header": has_header,
            "has_end": has_end,
            "format": "pdb",
            "errors": errors,
            "warnings": warnings,
        }


class SDFValidator:
    """Validate SDF (Structure Data File) format files."""
    
    @staticmethod
    def validate(content: bytes) -> Dict[str, Any]:
        """
        Validate SDF file structure and extract metadata.
        
        Args:
            content: Raw file bytes
            
        Returns:
            Dictionary with validation results:
            - is_valid: bool
            - molecule_count: int
            - has_mol_block: bool
            - has_atom_count: bool
            - format: str
            - errors: list
            - warnings: list
            
        Raises:
            FileValidationError: If file cannot be decoded
        """
        errors = []
        warnings = []
        
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = content.decode("latin-1")
                warnings.append("File decoded with latin-1 encoding instead of UTF-8")
            except Exception as e:
                raise FileValidationError(f"Cannot decode SDF file: {str(e)}")
        
        lines = content_str.split("\n")
        
        # Check for MOL block terminator ($$$$)
        has_mol_block = "$$$$" in content_str
        molecule_count = content_str.count("$$$$")
        
        if not has_mol_block:
            errors.append("No molecule block terminator ($$$$) found")
        
        # Check counts line (line 4 in SDF format)
        # Format: aaabbblllfffcccsssxxxrrrpppiiimmmvvvvvv
        # where aaa = number of atoms, bbb = number of bonds
        has_atom_count = False
        atom_count = 0
        bond_count = 0
        
        if len(lines) > 3:
            counts_line = lines[3].strip()
            if counts_line and len(counts_line) >= 6:
                try:
                    atom_count = int(counts_line[0:3].strip())
                    bond_count = int(counts_line[3:6].strip())
                    has_atom_count = True
                except ValueError:
                    errors.append("Invalid counts line (line 4): Cannot parse atom/bond counts")
            else:
                errors.append("Counts line (line 4) is too short or missing")
        else:
            errors.append("File too short - missing counts line")
        
        # Check for coordinate block (lines following counts line)
        has_coordinates = False
        if has_atom_count and len(lines) > 4 + atom_count:
            try:
                # Try to parse first coordinate line
                coord_line = lines[4].strip()
                parts = coord_line.split()
                if len(parts) >= 4:
                    # First 3 values should be coordinates (x, y, z)
                    float(parts[0])
                    float(parts[1])
                    float(parts[2])
                    has_coordinates = True
            except (ValueError, IndexError):
                warnings.append("Cannot parse coordinate block")
        
        # Check for M  END
        has_m_end = any(line.strip().startswith("M  END") for line in lines)
        if not has_m_end:
            warnings.append("No 'M  END' record found in MOL block")
        
        # Validation summary
        if molecule_count == 0:
            errors.append("No molecules found in SDF file")
        
        is_valid = (
            len(errors) == 0
            and has_mol_block
            and has_atom_count
            and molecule_count > 0
        )
        
        return {
            "is_valid": is_valid,
            "has_mol_block": has_mol_block,
            "has_atom_count": has_atom_count,
            "molecule_count": molecule_count,
            "atom_count": atom_count,
            "bond_count": bond_count,
            "has_coordinates": has_coordinates,
            "has_m_end": has_m_end,
            "format": "sdf",
            "errors": errors,
            "warnings": warnings,
        }


class PDBQTValidator:
    """Validate PDBQT (AutoDock PDBQT) format files."""
    
    @staticmethod
    def validate(content: bytes) -> Dict[str, Any]:
        """
        Validate PDBQT file structure (based on PDB with AutoDock extensions).
        
        Args:
            content: Raw file bytes
            
        Returns:
            Dictionary with validation results:
            - is_valid: bool
            - atom_count: int
            - has_root: bool
            - has_torsions: bool
            - torsion_count: int
            - format: str
            - errors: list
            - warnings: list
            
        Raises:
            FileValidationError: If file cannot be decoded
        """
        errors = []
        warnings = []
        
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = content.decode("latin-1")
                warnings.append("File decoded with latin-1 encoding instead of UTF-8")
            except Exception as e:
                raise FileValidationError(f"Cannot decode PDBQT file: {str(e)}")
        
        lines = content_str.split("\n")
        
        # PDBQT is PDB format with AutoDock extensions
        # Check for ATOM records
        atom_count = sum(1 for line in lines if line.startswith("ATOM  "))
        hetatm_count = sum(1 for line in lines if line.startswith("HETATM"))
        total_atoms = atom_count + hetatm_count
        
        # Check for AutoDock-specific records
        has_root = any(line.startswith("ROOT") for line in lines)
        has_endroot = any(line.startswith("ENDROOT") for line in lines)
        has_torsdof = any(line.startswith("TORSDOF") for line in lines)
        
        # Count torsions (BRANCH/ENDBRANCH pairs)
        branch_count = sum(1 for line in lines if line.startswith("BRANCH"))
        endbranch_count = sum(1 for line in lines if line.startswith("ENDBRANCH"))
        
        if branch_count != endbranch_count:
            errors.append(
                f"Mismatched BRANCH ({branch_count}) and ENDBRANCH ({endbranch_count}) records"
            )
        
        # Check for charges (PDBQT should have charges in columns 71-76)
        has_charges = False
        for line in lines:
            if line.startswith("ATOM  ") and len(line) > 70:
                try:
                    charge_str = line[70:76].strip()
                    if charge_str:
                        float(charge_str)
                        has_charges = True
                        break
                except ValueError:
                    pass
        
        if not has_charges:
            warnings.append("No partial charges found (expected in columns 71-76)")
        
        # Check for atom types (last field on ATOM lines)
        has_atom_types = False
        for line in lines:
            if line.startswith("ATOM  ") and len(line) > 77:
                atom_type = line[77:].strip()
                if atom_type:
                    has_atom_types = True
                    break
        
        if not has_atom_types:
            warnings.append("No AutoDock atom types found")
        
        # Validation rules
        if total_atoms == 0:
            errors.append("No ATOM or HETATM records found")
        
        if has_root and not has_endroot:
            errors.append("ROOT record found without matching ENDROOT")
        
        is_valid = len(errors) == 0 and total_atoms > 0
        
        return {
            "is_valid": is_valid,
            "atom_count": atom_count,
            "hetatm_count": hetatm_count,
            "total_atoms": total_atoms,
            "has_root": has_root,
            "has_endroot": has_endroot,
            "has_torsdof": has_torsdof,
            "has_charges": has_charges,
            "has_atom_types": has_atom_types,
            "branch_count": branch_count,
            "endbranch_count": endbranch_count,
            "torsion_count": branch_count,
            "format": "pdbqt",
            "errors": errors,
            "warnings": warnings,
        }


class MOL2Validator:
    """Validate MOL2 (Tripos MOL2) format files."""
    
    @staticmethod
    def validate(content: bytes) -> Dict[str, Any]:
        """
        Validate MOL2 file structure.
        
        Args:
            content: Raw file bytes
            
        Returns:
            Dictionary with validation results:
            - is_valid: bool
            - has_molecule_section: bool
            - has_atom_section: bool
            - has_bond_section: bool
            - atom_count: int
            - bond_count: int
            - format: str
            - errors: list
            - warnings: list
            
        Raises:
            FileValidationError: If file cannot be decoded
        """
        errors = []
        warnings = []
        
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = content.decode("latin-1")
                warnings.append("File decoded with latin-1 encoding instead of UTF-8")
            except Exception as e:
                raise FileValidationError(f"Cannot decode MOL2 file: {str(e)}")
        
        lines = content_str.split("\n")
        
        # MOL2 format has sections starting with @<TRIPOS>
        has_molecule_section = any("@<TRIPOS>MOLECULE" in line for line in lines)
        has_atom_section = any("@<TRIPOS>ATOM" in line for line in lines)
        has_bond_section = any("@<TRIPOS>BOND" in line for line in lines)
        
        if not has_molecule_section:
            errors.append("Missing @<TRIPOS>MOLECULE section")
        
        if not has_atom_section:
            errors.append("Missing @<TRIPOS>ATOM section")
        
        # Parse atom and bond counts from MOLECULE section
        atom_count = 0
        bond_count = 0
        
        if has_molecule_section:
            in_molecule = False
            line_after_molecule = 0
            
            for line in lines:
                if "@<TRIPOS>MOLECULE" in line:
                    in_molecule = True
                    line_after_molecule = 0
                    continue
                
                if in_molecule:
                    line_after_molecule += 1
                    # Line 2 after @<TRIPOS>MOLECULE contains counts: num_atoms num_bonds ...
                    if line_after_molecule == 2:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            try:
                                atom_count = int(parts[0])
                                bond_count = int(parts[1])
                            except ValueError:
                                errors.append("Cannot parse atom/bond counts from MOLECULE section")
                        break
        
        # Verify ATOM section has expected number of atoms
        if has_atom_section:
            atom_lines = 0
            in_atom_section = False
            
            for line in lines:
                if "@<TRIPOS>ATOM" in line:
                    in_atom_section = True
                    continue
                
                if in_atom_section:
                    if line.startswith("@<TRIPOS>"):
                        break
                    if line.strip():
                        atom_lines += 1
            
            if atom_count > 0 and atom_lines != atom_count:
                warnings.append(
                    f"ATOM section has {atom_lines} lines but MOLECULE declares {atom_count} atoms"
                )
        
        # Validation summary
        if atom_count == 0:
            errors.append("No atoms declared in MOLECULE section")
        
        is_valid = (
            len(errors) == 0
            and has_molecule_section
            and has_atom_section
            and atom_count > 0
        )
        
        return {
            "is_valid": is_valid,
            "has_molecule_section": has_molecule_section,
            "has_atom_section": has_atom_section,
            "has_bond_section": has_bond_section,
            "atom_count": atom_count,
            "bond_count": bond_count,
            "format": "mol2",
            "errors": errors,
            "warnings": warnings,
        }


class XYZValidator:
    """Validate XYZ coordinate format files."""
    
    @staticmethod
    def validate(content: bytes) -> Dict[str, Any]:
        """
        Validate XYZ file structure.
        
        XYZ format:
        Line 1: Number of atoms
        Line 2: Comment line
        Lines 3+: Element X Y Z (one per atom)
        
        Args:
            content: Raw file bytes
            
        Returns:
            Dictionary with validation results:
            - is_valid: bool
            - atom_count: int
            - has_coordinates: bool
            - format: str
            - errors: list
            - warnings: list
            
        Raises:
            FileValidationError: If file cannot be decoded
        """
        errors = []
        warnings = []
        
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = content.decode("latin-1")
                warnings.append("File decoded with latin-1 encoding instead of UTF-8")
            except Exception as e:
                raise FileValidationError(f"Cannot decode XYZ file: {str(e)}")
        
        lines = [line.strip() for line in content_str.split("\n") if line.strip()]
        
        if len(lines) < 3:
            errors.append("XYZ file too short (minimum 3 lines required)")
            return {
                "is_valid": False,
                "atom_count": 0,
                "has_coordinates": False,
                "format": "xyz",
                "errors": errors,
                "warnings": warnings,
            }
        
        # Parse atom count from first line
        try:
            declared_atom_count = int(lines[0].strip())
        except ValueError:
            errors.append(f"Invalid atom count on line 1: '{lines[0]}'")
            return {
                "is_valid": False,
                "atom_count": 0,
                "has_coordinates": False,
                "format": "xyz",
                "errors": errors,
                "warnings": warnings,
            }
        
        # Line 2 is comment (skip validation)
        
        # Validate coordinate lines (starting from line 3)
        coordinate_lines = lines[2:]
        has_coordinates = False
        actual_atom_count = 0
        
        for i, line in enumerate(coordinate_lines, start=3):
            parts = line.split()
            
            if len(parts) < 4:
                errors.append(f"Line {i}: Expected 'Element X Y Z', got '{line}'")
                continue
            
            # First part should be element symbol
            element = parts[0]
            if not re.match(r"^[A-Z][a-z]?$", element):
                warnings.append(f"Line {i}: '{element}' may not be a valid element symbol")
            
            # Next 3 should be coordinates
            try:
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                has_coordinates = True
                actual_atom_count += 1
            except ValueError:
                errors.append(f"Line {i}: Cannot parse coordinates from '{line}'")
                continue
        
        # Check if atom count matches
        if actual_atom_count != declared_atom_count:
            errors.append(
                f"Atom count mismatch: declared {declared_atom_count}, found {actual_atom_count}"
            )
        
        is_valid = (
            len(errors) == 0
            and has_coordinates
            and actual_atom_count == declared_atom_count
            and actual_atom_count > 0
        )
        
        return {
            "is_valid": is_valid,
            "atom_count": actual_atom_count,
            "declared_atom_count": declared_atom_count,
            "has_coordinates": has_coordinates,
            "format": "xyz",
            "errors": errors,
            "warnings": warnings,
        }


# Validator registry
VALIDATORS = {
    "pdb": PDBValidator,
    "sdf": SDFValidator,
    "pdbqt": PDBQTValidator,
    "mol2": MOL2Validator,
    "xyz": XYZValidator,
}


def get_validator(file_format: str):
    """
    Get validator class for a file format.
    
    Args:
        file_format: File format (pdb, sdf, pdbqt, mol2, xyz)
        
    Returns:
        Validator class
        
    Raises:
        ValueError: If format is not supported
    """
    file_format = file_format.lower()
    
    if file_format not in VALIDATORS:
        raise ValueError(
            f"Unsupported format '{file_format}'. "
            f"Supported formats: {', '.join(VALIDATORS.keys())}"
        )
    
    return VALIDATORS[file_format]


def validate_file(content: bytes, file_format: str) -> Dict[str, Any]:
    """
    Validate a file of the specified format.
    
    Args:
        content: Raw file bytes
        file_format: File format (pdb, sdf, pdbqt, mol2, xyz)
        
    Returns:
        Dictionary with validation results
        
    Raises:
        ValueError: If format is not supported
        FileValidationError: If validation fails critically
    """
    validator_class = get_validator(file_format)
    return validator_class.validate(content)
