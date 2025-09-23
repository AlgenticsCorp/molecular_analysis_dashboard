#!/usr/bin/env python3
"""
Documentation Validation Tool

Validate completeness of implementation documentation.

Usage:
    python validate-documentation.py
    python validate-documentation.py --phase 3B
    python validate-documentation.py --fix
"""

import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import json

class DocumentationValidator:
    """Validate implementation documentation completeness."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.docs_root = self.project_root / "docs" / "implementation"
        self.phases_dir = self.docs_root / "phases"
        self.templates_dir = self.docs_root / "templates"

        # Required files for each phase
        self.required_files = {
            "planning.md": "Phase planning document",
            "implementation.md": "Implementation guide",
            "progress.md": "Progress tracking",
            "completion-report.md": "Completion report"
        }

        # Load phase information
        self.phases = self._discover_phases()

    def _discover_phases(self) -> Dict[str, Dict]:
        """Discover all phases in the phases directory."""
        phases = {}

        if not self.phases_dir.exists():
            return phases

        for item in self.phases_dir.iterdir():
            if item.is_dir() and item.name.startswith("phase-"):
                phase_id = item.name
                phases[phase_id] = {
                    "path": item,
                    "name": phase_id.replace("phase-", "").upper(),
                    "exists": True
                }

        return phases

    def validate_phase_documentation(self, phase_id: Optional[str] = None) -> Dict[str, List]:
        """Validate documentation for specific phase or all phases."""
        results = {
            "missing_files": [],
            "empty_files": [],
            "template_files": [],
            "valid_files": [],
            "warnings": []
        }

        phases_to_check = [phase_id] if phase_id else list(self.phases.keys())

        for pid in phases_to_check:
            if pid not in self.phases:
                results["warnings"].append(f"Phase {pid} directory does not exist")
                continue

            phase_path = self.phases[pid]["path"]

            # Check each required file
            for filename, description in self.required_files.items():
                file_path = phase_path / filename

                if not file_path.exists():
                    results["missing_files"].append({
                        "phase": pid,
                        "file": filename,
                        "description": description,
                        "path": str(file_path)
                    })
                else:
                    # Check if file is empty or just template
                    content = file_path.read_text()

                    if len(content.strip()) == 0:
                        results["empty_files"].append({
                            "phase": pid,
                            "file": filename,
                            "path": str(file_path)
                        })
                    elif self._is_template_content(content):
                        results["template_files"].append({
                            "phase": pid,
                            "file": filename,
                            "path": str(file_path)
                        })
                    else:
                        results["valid_files"].append({
                            "phase": pid,
                            "file": filename,
                            "path": str(file_path),
                            "size": len(content)
                        })

        return results

    def _is_template_content(self, content: str) -> bool:
        """Check if content appears to be template/placeholder text."""
        template_indicators = [
            "[Phase Name",
            "[YYYY-MM-DD]",
            "[Description]",
            "[TODO:",
            "Template",
            "[Fill in",
            "[Replace with"
        ]

        return any(indicator in content for indicator in template_indicators)

    def validate_overall_structure(self) -> Dict[str, List]:
        """Validate overall documentation structure."""
        results = {
            "missing_directories": [],
            "missing_templates": [],
            "missing_tools": [],
            "structural_issues": []
        }

        # Check main directories exist
        required_dirs = [
            "phases",
            "templates",
            "tools",
            "status"
        ]

        for dir_name in required_dirs:
            dir_path = self.docs_root / dir_name
            if not dir_path.exists():
                results["missing_directories"].append({
                    "directory": dir_name,
                    "path": str(dir_path)
                })

        # Check templates exist
        required_templates = [
            "phase-planning-template.md",
            "implementation-guide-template.md",
            "completion-report-template.md",
            "status-update-template.md"
        ]

        for template_name in required_templates:
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                results["missing_templates"].append({
                    "template": template_name,
                    "path": str(template_path)
                })

        # Check tools exist
        required_tools = [
            "update-status.py",
            "generate-report.py",
            "validate-documentation.py"
        ]

        tools_dir = self.docs_root / "tools"
        for tool_name in required_tools:
            tool_path = tools_dir / tool_name
            if not tool_path.exists():
                results["missing_tools"].append({
                    "tool": tool_name,
                    "path": str(tool_path)
                })

        return results

    def generate_missing_phase_files(self, phase_id: str) -> List[str]:
        """Generate missing files for a phase using templates."""
        if phase_id not in self.phases:
            print(f"❌ Phase {phase_id} does not exist")
            return []

        phase_path = self.phases[phase_id]["path"]
        created_files = []

        # Create missing files from templates
        for filename, description in self.required_files.items():
            file_path = phase_path / filename

            if not file_path.exists():
                template_name = self._get_template_name(filename)
                template_path = self.templates_dir / template_name

                if template_path.exists():
                    # Copy template and customize
                    template_content = template_path.read_text()
                    customized_content = self._customize_template(template_content, phase_id)

                    file_path.write_text(customized_content)
                    created_files.append(str(file_path))
                    print(f"✅ Created {filename} for Phase {phase_id}")
                else:
                    # Create basic placeholder
                    placeholder_content = self._create_placeholder_content(filename, phase_id)
                    file_path.write_text(placeholder_content)
                    created_files.append(str(file_path))
                    print(f"⚠️  Created placeholder {filename} for Phase {phase_id}")

        return created_files

    def _get_template_name(self, filename: str) -> str:
        """Get template name for a given file."""
        template_mapping = {
            "planning.md": "phase-planning-template.md",
            "implementation.md": "implementation-guide-template.md",
            "completion-report.md": "completion-report-template.md",
            "progress.md": "status-update-template.md"
        }
        return template_mapping.get(filename, "")

    def _customize_template(self, template_content: str, phase_id: str) -> str:
        """Customize template content for specific phase."""
        phase_name = self._get_phase_name(phase_id)

        # Replace common placeholders
        customized = template_content.replace(
            "[Phase Name and Number]",
            f"Phase {phase_id.replace('phase-', '').upper()}: {phase_name}"
        )

        customized = customized.replace(
            "[YYYY-MM-DD]",
            "TBD"
        )

        return customized

    def _get_phase_name(self, phase_id: str) -> str:
        """Get human-readable phase name."""
        phase_names = {
            "phase-1": "Foundation & Setup",
            "phase-2": "Core Development",
            "phase-3a": "Gateway Architecture Design",
            "phase-3b": "Service Implementation",
            "phase-3c": "Security Framework",
            "phase-3d": "Service Discovery",
            "phase-3e": "Production Hardening",
            "phase-4a": "Task Integration",
            "phase-4b": "Docking Engines",
            "phase-4c": "Advanced Pipelines"
        }
        return phase_names.get(phase_id, "Unknown Phase")

    def _create_placeholder_content(self, filename: str, phase_id: str) -> str:
        """Create basic placeholder content."""
        phase_name = self._get_phase_name(phase_id)
        phase_display = phase_id.replace("phase-", "").upper()

        if filename == "planning.md":
            return f"""# Phase {phase_display}: {phase_name} - Planning

**Status**: Planning
**Owner**: TBD

## Objectives
- [Define phase objectives]

## Features
- [List key features to implement]

## Timeline
- **Target Start**: TBD
- **Target Completion**: TBD

## Dependencies
- [List dependencies]

*This is a placeholder file. Please update with actual planning details.*
"""
        elif filename == "implementation.md":
            return f"""# Phase {phase_display}: {phase_name} - Implementation Guide

**Status**: Not Started
**Last Updated**: {phase_display}

## Setup
[Implementation setup instructions]

## Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Testing
[Testing instructions]

*This is a placeholder file. Please update with actual implementation details.*
"""
        elif filename == "progress.md":
            return f"""# Phase {phase_display}: {phase_name} - Progress Tracking

**Last Updated**: TBD
**Status**: Not Started
**Progress**: 0%

## Current Status
[Status description]

## Completed Items
- [None yet]

## In Progress
- [Nothing in progress]

## Blockers
- [No blockers yet]

*This is a placeholder file. Update regularly during implementation.*
"""
        else:  # completion-report.md
            return f"""# Phase {phase_display}: {phase_name} - Completion Report

**Status**: Not Complete
**Completion Date**: TBD

## Summary
[Phase completion summary]

## Deliverables
- [List completed deliverables]

## Metrics
[Key metrics and achievements]

## Lessons Learned
[Key lessons and insights]

*This file should be completed when the phase is finished.*
"""

    def print_validation_results(self, results: Dict, structure_results: Optional[Dict] = None):
        """Print validation results in a readable format."""
        print("\n📋 Documentation Validation Report")
        print("=" * 50)

        # Structure validation
        if structure_results:
            print("\n🏗️  Structure Validation:")

            if structure_results["missing_directories"]:
                print("  ❌ Missing Directories:")
                for item in structure_results["missing_directories"]:
                    print(f"    • {item['directory']}")

            if structure_results["missing_templates"]:
                print("  ❌ Missing Templates:")
                for item in structure_results["missing_templates"]:
                    print(f"    • {item['template']}")

            if structure_results["missing_tools"]:
                print("  ❌ Missing Tools:")
                for item in structure_results["missing_tools"]:
                    print(f"    • {item['tool']}")

            if not any([structure_results["missing_directories"],
                       structure_results["missing_templates"],
                       structure_results["missing_tools"]]):
                print("  ✅ Structure is complete")

        # Phase documentation validation
        print(f"\n📄 Phase Documentation:")

        if results["missing_files"]:
            print(f"  ❌ Missing Files ({len(results['missing_files'])}):")
            for item in results["missing_files"]:
                print(f"    • {item['phase']}/{item['file']} - {item['description']}")

        if results["empty_files"]:
            print(f"  ⚠️  Empty Files ({len(results['empty_files'])}):")
            for item in results["empty_files"]:
                print(f"    • {item['phase']}/{item['file']}")

        if results["template_files"]:
            print(f"  ⚠️  Template Files ({len(results['template_files'])}):")
            for item in results["template_files"]:
                print(f"    • {item['phase']}/{item['file']} - Needs customization")

        if results["valid_files"]:
            print(f"  ✅ Valid Files ({len(results['valid_files'])}):")
            for item in results["valid_files"]:
                size_kb = item['size'] / 1024
                print(f"    • {item['phase']}/{item['file']} ({size_kb:.1f}KB)")

        # Summary
        total_expected = len(self.phases) * len(self.required_files)
        total_valid = len(results["valid_files"])
        completion_rate = (total_valid / total_expected * 100) if total_expected > 0 else 0

        print(f"\n📊 Summary:")
        print(f"  • Documentation Completeness: {completion_rate:.1f}%")
        print(f"  • Valid Files: {total_valid}/{total_expected}")
        print(f"  • Issues Found: {len(results['missing_files']) + len(results['empty_files']) + len(results['template_files'])}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Validate implementation documentation")

    parser.add_argument("--phase", help="Validate specific phase (e.g., 'phase-3b')")
    parser.add_argument("--fix", action="store_true", help="Generate missing files")
    parser.add_argument("--structure", action="store_true", help="Validate overall structure")

    args = parser.parse_args()

    validator = DocumentationValidator()

    # Validate structure if requested
    structure_results = None
    if args.structure:
        structure_results = validator.validate_overall_structure()

    # Validate phase documentation
    results = validator.validate_phase_documentation(args.phase)

    # Print results
    validator.print_validation_results(results, structure_results)

    # Generate missing files if requested
    if args.fix:
        print("\n🔧 Generating Missing Files...")

        if args.phase:
            phases_to_fix = [args.phase]
        else:
            # Find phases with missing files
            phases_to_fix = list(set(item["phase"] for item in results["missing_files"]))

        for phase_id in phases_to_fix:
            created_files = validator.generate_missing_phase_files(phase_id)
            if created_files:
                print(f"  ✅ Created {len(created_files)} files for {phase_id}")

        print("\n💡 Note: Generated files are templates. Please customize them with actual content.")


if __name__ == "__main__":
    main()
