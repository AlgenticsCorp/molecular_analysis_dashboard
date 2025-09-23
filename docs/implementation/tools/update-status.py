#!/usr/bin/env python3
"""
Implementation Status Management Tool

This script helps developers update phase and feature status throughout
the implementation process.

Usage:
    python update-status.py --phase "3B" --feature "API Integration" --status "In Progress"
    python update-status.py --phase "3B" --progress 75
    python update-status.py --list-phases
    python update-status.py --generate-report
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Status constants
VALID_STATUSES = [
    "Not Started",
    "Planning",
    "In Progress",
    "Testing",
    "Complete",
    "Blocked",
    "Deferred"
]

PHASE_STATUSES = {
    "Not Started": "⏳",
    "Planning": "📋",
    "In Progress": "🔄",
    "Testing": "🧪",
    "Complete": "✅",
    "Blocked": "🚫",
    "Deferred": "⏸️"
}

class StatusManager:
    """Manage implementation phase and feature status."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.status_file = self.project_root / "docs" / "implementation" / "status" / "current-status.json"
        self.phases_dir = self.project_root / "docs" / "implementation" / "phases"

        # Ensure status directory exists
        self.status_file.parent.mkdir(parents=True, exist_ok=True)

        # Load or initialize status
        self.status_data = self._load_status()

    def _load_status(self) -> Dict:
        """Load current status from file."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # Initialize default status structure
        return {
            "last_updated": datetime.now().isoformat(),
            "phases": {
                "phase-1": {
                    "name": "Foundation & Setup",
                    "status": "Complete",
                    "progress": 100,
                    "start_date": "2025-01-01",
                    "completion_date": "2025-01-31",
                    "features": {}
                },
                "phase-2": {
                    "name": "Core Development",
                    "status": "Complete",
                    "progress": 100,
                    "start_date": "2025-02-01",
                    "completion_date": "2025-02-28",
                    "features": {}
                },
                "phase-3a": {
                    "name": "Gateway Architecture Design",
                    "status": "Complete",
                    "progress": 100,
                    "start_date": "2025-03-01",
                    "completion_date": "2025-03-15",
                    "features": {}
                },
                "phase-3b": {
                    "name": "Service Implementation",
                    "status": "Not Started",
                    "progress": 0,
                    "start_date": None,
                    "target_completion": "2025-03-30",
                    "features": {}
                },
                "phase-3c": {
                    "name": "Security Framework",
                    "status": "Not Started",
                    "progress": 0,
                    "features": {}
                },
                "phase-3d": {
                    "name": "Service Discovery",
                    "status": "Not Started",
                    "progress": 0,
                    "features": {}
                },
                "phase-3e": {
                    "name": "Production Hardening",
                    "status": "Not Started",
                    "progress": 0,
                    "features": {}
                },
                "phase-4a": {
                    "name": "Task Integration",
                    "status": "Not Started",
                    "progress": 0,
                    "features": {}
                },
                "phase-4b": {
                    "name": "Docking Engines",
                    "status": "Not Started",
                    "progress": 0,
                    "features": {}
                },
                "phase-4c": {
                    "name": "Advanced Pipelines",
                    "status": "Not Started",
                    "progress": 0,
                    "features": {}
                }
            }
        }

    def _save_status(self):
        """Save status to file."""
        self.status_data["last_updated"] = datetime.now().isoformat()
        with open(self.status_file, 'w') as f:
            json.dump(self.status_data, f, indent=2)

    def update_phase_status(self, phase_id: str, status: str, progress: Optional[int] = None):
        """Update phase status."""
        phase_key = f"phase-{phase_id.lower()}"

        if phase_key not in self.status_data["phases"]:
            print(f"❌ Phase {phase_id} not found. Available phases:")
            self.list_phases()
            return False

        if status not in VALID_STATUSES:
            print(f"❌ Invalid status '{status}'. Valid statuses: {', '.join(VALID_STATUSES)}")
            return False

        phase = self.status_data["phases"][phase_key]
        old_status = phase["status"]
        phase["status"] = status

        if progress is not None:
            phase["progress"] = max(0, min(100, progress))

        # Auto-set dates based on status changes
        if status == "In Progress" and old_status == "Not Started":
            phase["start_date"] = datetime.now().date().isoformat()
        elif status == "Complete" and old_status != "Complete":
            phase["completion_date"] = datetime.now().date().isoformat()

        self._save_status()

        icon = PHASE_STATUSES.get(status, "📋")
        print(f"✅ {icon} Updated Phase {phase_id} ({phase['name']}) to '{status}'")
        if progress is not None:
            print(f"   Progress: {progress}%")

        return True

    def update_feature_status(self, phase_id: str, feature_name: str, status: str,
                            owner: Optional[str] = None, notes: Optional[str] = None):
        """Update feature status within a phase."""
        phase_key = f"phase-{phase_id.lower()}"

        if phase_key not in self.status_data["phases"]:
            print(f"❌ Phase {phase_id} not found.")
            return False

        if status not in VALID_STATUSES:
            print(f"❌ Invalid status '{status}'. Valid statuses: {', '.join(VALID_STATUSES)}")
            return False

        phase = self.status_data["phases"][phase_key]

        if "features" not in phase:
            phase["features"] = {}

        feature_key = feature_name.lower().replace(" ", "_")

        if feature_key not in phase["features"]:
            phase["features"][feature_key] = {
                "name": feature_name,
                "status": "Not Started",
                "created_date": datetime.now().date().isoformat()
            }

        feature = phase["features"][feature_key]
        feature["status"] = status
        feature["last_updated"] = datetime.now().date().isoformat()

        if owner:
            feature["owner"] = owner
        if notes:
            feature["notes"] = notes

        self._save_status()

        icon = PHASE_STATUSES.get(status, "📋")
        print(f"✅ {icon} Updated feature '{feature_name}' in Phase {phase_id} to '{status}'")

        return True

    def list_phases(self):
        """List all phases with their current status."""
        print("\n📋 Implementation Phases Status:")
        print("=" * 60)

        for phase_key, phase in self.status_data["phases"].items():
            status = phase["status"]
            progress = phase.get("progress", 0)
            icon = PHASE_STATUSES.get(status, "📋")

            phase_id = phase_key.replace("phase-", "").upper()
            name = phase["name"]

            print(f"{icon} {phase_id}: {name}")
            print(f"   Status: {status} ({progress}%)")

            if phase.get("start_date"):
                print(f"   Started: {phase['start_date']}")
            if phase.get("completion_date"):
                print(f"   Completed: {phase['completion_date']}")
            elif phase.get("target_completion"):
                print(f"   Target: {phase['target_completion']}")

            # List features if any
            features = phase.get("features", {})
            if features:
                print(f"   Features ({len(features)}):")
                for feature_key, feature in features.items():
                    feat_icon = PHASE_STATUSES.get(feature["status"], "📋")
                    owner_info = f" ({feature['owner']})" if feature.get("owner") else ""
                    print(f"     {feat_icon} {feature['name']}{owner_info}")

            print()

    def list_features(self, phase_id: str):
        """List features for a specific phase."""
        phase_key = f"phase-{phase_id.lower()}"

        if phase_key not in self.status_data["phases"]:
            print(f"❌ Phase {phase_id} not found.")
            return False

        phase = self.status_data["phases"][phase_key]
        features = phase.get("features", {})

        print(f"\n📋 Features for Phase {phase_id.upper()}: {phase['name']}")
        print("=" * 60)

        if not features:
            print("No features tracked yet.")
            return True

        for feature_key, feature in features.items():
            status = feature["status"]
            icon = PHASE_STATUSES.get(status, "📋")

            print(f"{icon} {feature['name']}")
            print(f"   Status: {status}")
            print(f"   Created: {feature['created_date']}")

            if feature.get("last_updated"):
                print(f"   Updated: {feature['last_updated']}")
            if feature.get("owner"):
                print(f"   Owner: {feature['owner']}")
            if feature.get("notes"):
                print(f"   Notes: {feature['notes']}")
            print()

        return True

    def generate_summary_report(self):
        """Generate a summary report of all phases."""
        total_phases = len(self.status_data["phases"])
        completed_phases = sum(1 for p in self.status_data["phases"].values() if p["status"] == "Complete")
        in_progress_phases = sum(1 for p in self.status_data["phases"].values() if p["status"] == "In Progress")

        print("\n📊 Implementation Summary Report")
        print("=" * 50)
        print(f"Last Updated: {self.status_data['last_updated'][:19]}")
        print(f"Total Phases: {total_phases}")
        print(f"Completed: {completed_phases} ({completed_phases/total_phases*100:.1f}%)")
        print(f"In Progress: {in_progress_phases}")
        print(f"Not Started: {total_phases - completed_phases - in_progress_phases}")

        print(f"\n📈 Overall Progress:")
        total_progress = sum(p.get("progress", 0) for p in self.status_data["phases"].values())
        avg_progress = total_progress / total_phases

        progress_bar = "█" * int(avg_progress / 5) + "░" * (20 - int(avg_progress / 5))
        print(f"[{progress_bar}] {avg_progress:.1f}%")

        # Show next priorities
        print(f"\n🎯 Current Priorities:")
        for phase_key, phase in self.status_data["phases"].items():
            if phase["status"] in ["In Progress", "Planning"]:
                phase_id = phase_key.replace("phase-", "").upper()
                icon = PHASE_STATUSES.get(phase["status"], "📋")
                print(f"   {icon} {phase_id}: {phase['name']} ({phase.get('progress', 0)}%)")

        return True


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Manage implementation phase status")

    parser.add_argument("--phase", help="Phase ID (e.g., '3B', '4A')")
    parser.add_argument("--feature", help="Feature name within phase")
    parser.add_argument("--status", choices=VALID_STATUSES, help="New status")
    parser.add_argument("--progress", type=int, help="Progress percentage (0-100)")
    parser.add_argument("--owner", help="Feature owner")
    parser.add_argument("--notes", help="Additional notes")

    parser.add_argument("--list-phases", action="store_true", help="List all phases")
    parser.add_argument("--list-features", action="store_true", help="List features for specified phase")
    parser.add_argument("--generate-report", action="store_true", help="Generate summary report")

    args = parser.parse_args()

    manager = StatusManager()

    # Handle list operations
    if args.list_phases:
        manager.list_phases()
        return

    if args.list_features:
        if not args.phase:
            print("❌ --phase required with --list-features")
            return
        manager.list_features(args.phase)
        return

    if args.generate_report:
        manager.generate_summary_report()
        return

    # Handle update operations
    if args.phase and args.status:
        if args.feature:
            # Update feature status
            manager.update_feature_status(
                args.phase, args.feature, args.status, args.owner, args.notes
            )
        else:
            # Update phase status
            manager.update_phase_status(args.phase, args.status, args.progress)

    elif args.phase and args.progress is not None:
        # Update just progress
        phase_key = f"phase-{args.phase.lower()}"
        if phase_key in manager.status_data["phases"]:
            manager.update_phase_status(args.phase,
                                      manager.status_data["phases"][phase_key]["status"],
                                      args.progress)

    else:
        print("Usage examples:")
        print("  python update-status.py --list-phases")
        print("  python update-status.py --phase '3B' --status 'In Progress'")
        print("  python update-status.py --phase '3B' --feature 'API Integration' --status 'Complete'")
        print("  python update-status.py --generate-report")


if __name__ == "__main__":
    main()
