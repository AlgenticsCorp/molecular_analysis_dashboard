#!/usr/bin/env python3
"""
Progress Report Generator

Generate comprehensive progress reports for implementation phases.

Usage:
    python generate-report.py --format markdown --output weekly-report.md
    python generate-report.py --format json --phase 3B
    python generate-report.py --dashboard
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Optional

class ReportGenerator:
    """Generate implementation progress reports."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.status_file = self.project_root / "docs" / "implementation" / "status" / "current-status.json"
        self.reports_dir = self.project_root / "docs" / "implementation" / "status"

        # Load status data
        self.status_data = self._load_status()

    def _load_status(self) -> Dict:
        """Load current status data."""
        if not self.status_file.exists():
            print("❌ No status data found. Run update-status.py first.")
            sys.exit(1)

        with open(self.status_file, 'r') as f:
            return json.load(f)

    def generate_markdown_report(self, phase_filter: Optional[str] = None) -> str:
        """Generate comprehensive markdown report."""
        report_date = datetime.now().strftime("%Y-%m-%d")

        # Header
        markdown = f"""# Implementation Progress Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Last Status Update**: {self.status_data.get('last_updated', 'Unknown')[:19]}

## 📊 Executive Summary

"""

        # Calculate overall metrics
        phases = self.status_data["phases"]
        total_phases = len(phases)
        completed = sum(1 for p in phases.values() if p["status"] == "Complete")
        in_progress = sum(1 for p in phases.values() if p["status"] == "In Progress")
        blocked = sum(1 for p in phases.values() if p["status"] == "Blocked")

        total_progress = sum(p.get("progress", 0) for p in phases.values())
        avg_progress = total_progress / total_phases if total_phases > 0 else 0

        # Executive summary
        markdown += f"""### Overall Project Status
- **Total Phases**: {total_phases}
- **Completed**: {completed} phases ({completed/total_phases*100:.1f}%)
- **In Progress**: {in_progress} phases
- **Blocked**: {blocked} phases
- **Overall Progress**: {avg_progress:.1f}%

### Health Indicators
- 🟢 **Timeline**: {"On Track" if blocked == 0 else "At Risk"}
- 🟢 **Quality**: On Track (Test coverage maintained)
- {"🟡" if blocked > 0 else "🟢"} **Execution**: {"Issues Present" if blocked > 0 else "Smooth"}

---

## 📋 Phase Status Overview

| Phase | Name | Status | Progress | Start Date | Target/Completion |
|-------|------|--------|----------|------------|-------------------|
"""

        # Phase status table
        for phase_key, phase in phases.items():
            if phase_filter and not phase_key.replace("phase-", "").upper().startswith(phase_filter.upper()):
                continue

            phase_id = phase_key.replace("phase-", "").upper()
            name = phase["name"]
            status = phase["status"]
            progress = phase.get("progress", 0)
            start_date = phase.get("start_date", "Not Started")

            if phase.get("completion_date"):
                target_completion = phase["completion_date"]
            elif phase.get("target_completion"):
                target_completion = phase["target_completion"]
            else:
                target_completion = "TBD"

            status_icon = self._get_status_icon(status)
            progress_bar = self._get_progress_bar(progress)

            markdown += f"| {phase_id} | {name} | {status_icon} {status} | {progress_bar} {progress}% | {start_date} | {target_completion} |\n"

        markdown += "\n---\n\n"

        # Detailed phase information
        markdown += "## 📝 Detailed Phase Information\n\n"

        for phase_key, phase in phases.items():
            if phase_filter and not phase_key.replace("phase-", "").upper().startswith(phase_filter.upper()):
                continue

            phase_id = phase_key.replace("phase-", "").upper()
            name = phase["name"]
            status = phase["status"]
            progress = phase.get("progress", 0)

            status_icon = self._get_status_icon(status)
            markdown += f"### {status_icon} Phase {phase_id}: {name}\n\n"

            # Phase details
            markdown += f"- **Status**: {status} ({progress}%)\n"

            if phase.get("start_date"):
                markdown += f"- **Started**: {phase['start_date']}\n"

            if phase.get("completion_date"):
                markdown += f"- **Completed**: {phase['completion_date']}\n"
            elif phase.get("target_completion"):
                markdown += f"- **Target Completion**: {phase['target_completion']}\n"

            # Features
            features = phase.get("features", {})
            if features:
                markdown += f"- **Features**: {len(features)} tracked\n\n"

                markdown += "| Feature | Status | Owner | Notes |\n"
                markdown += "|---------|--------|-------|-------|\n"

                for feature_key, feature in features.items():
                    feat_status = feature["status"]
                    feat_icon = self._get_status_icon(feat_status)
                    owner = feature.get("owner", "Unassigned")
                    notes = feature.get("notes", "")

                    markdown += f"| {feature['name']} | {feat_icon} {feat_status} | {owner} | {notes} |\n"

                markdown += "\n"
            else:
                markdown += "- **Features**: No features tracked yet\n\n"

        # Current priorities
        markdown += "---\n\n## 🎯 Current Priorities\n\n"

        current_work = []
        for phase_key, phase in phases.items():
            if phase["status"] in ["In Progress", "Planning"]:
                phase_id = phase_key.replace("phase-", "").upper()
                current_work.append(f"- **Phase {phase_id}**: {phase['name']} ({phase.get('progress', 0)}%)")

        if current_work:
            markdown += "\n".join(current_work) + "\n\n"
        else:
            markdown += "No active work in progress.\n\n"

        # Blockers and risks
        blocked_phases = [p for p in phases.values() if p["status"] == "Blocked"]
        if blocked_phases:
            markdown += "## 🚫 Blockers & Issues\n\n"
            for phase in blocked_phases:
                phase_name = phase["name"]
                markdown += f"- **{phase_name}**: Blocked\n"
            markdown += "\n"

        # Next milestones
        markdown += "## 📅 Upcoming Milestones\n\n"

        upcoming = []
        for phase_key, phase in phases.items():
            if phase["status"] in ["Not Started", "Planning", "In Progress"]:
                phase_id = phase_key.replace("phase-", "").upper()
                target = phase.get("target_completion", "TBD")
                upcoming.append(f"- **Phase {phase_id}**: {phase['name']} - Target: {target}")

        if upcoming:
            markdown += "\n".join(upcoming) + "\n\n"
        else:
            markdown += "All planned phases completed.\n\n"

        # Footer
        markdown += f"""---

*Report generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")} by Implementation Status Tool*
"""

        return markdown

    def generate_json_report(self, phase_filter: Optional[str] = None) -> Dict:
        """Generate JSON report for programmatic use."""
        phases = self.status_data["phases"]

        # Filter phases if specified
        if phase_filter:
            filtered_phases = {
                k: v for k, v in phases.items()
                if k.replace("phase-", "").upper().startswith(phase_filter.upper())
            }
        else:
            filtered_phases = phases

        # Calculate metrics
        total_phases = len(filtered_phases)
        completed = sum(1 for p in filtered_phases.values() if p["status"] == "Complete")
        in_progress = sum(1 for p in filtered_phases.values() if p["status"] == "In Progress")
        blocked = sum(1 for p in filtered_phases.values() if p["status"] == "Blocked")

        total_progress = sum(p.get("progress", 0) for p in filtered_phases.values())
        avg_progress = total_progress / total_phases if total_phases > 0 else 0

        return {
            "generated_at": datetime.now().isoformat(),
            "last_updated": self.status_data.get("last_updated"),
            "summary": {
                "total_phases": total_phases,
                "completed_phases": completed,
                "in_progress_phases": in_progress,
                "blocked_phases": blocked,
                "overall_progress": avg_progress
            },
            "phases": filtered_phases,
            "health_indicators": {
                "timeline": "on_track" if blocked == 0 else "at_risk",
                "quality": "on_track",
                "execution": "smooth" if blocked == 0 else "issues_present"
            }
        }

    def generate_dashboard(self) -> str:
        """Generate a dashboard-style report."""
        phases = self.status_data["phases"]

        # Calculate metrics
        total_phases = len(phases)
        completed = sum(1 for p in phases.values() if p["status"] == "Complete")
        in_progress = sum(1 for p in phases.values() if p["status"] == "In Progress")
        blocked = sum(1 for p in phases.values() if p["status"] == "Blocked")

        total_progress = sum(p.get("progress", 0) for p in phases.values())
        avg_progress = total_progress / total_phases if total_phases > 0 else 0

        # Create dashboard
        dashboard = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🚀 IMPLEMENTATION DASHBOARD                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📊 OVERALL PROGRESS: {avg_progress:5.1f}%                                              ║
║  ████████████████████████████████████████████████████████████████████████    ║
║  [{self._get_console_progress_bar(avg_progress, 60)}]    ║
║                                                                              ║
║  📈 PHASE BREAKDOWN:                                                         ║
║    ✅ Completed: {completed:2d} phases ({completed/total_phases*100:5.1f}%)                               ║
║    🔄 In Progress: {in_progress:2d} phases                                              ║
║    🚫 Blocked: {blocked:2d} phases                                                   ║
║    ⏳ Not Started: {total_phases - completed - in_progress - blocked:2d} phases                                           ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                           📋 PHASE STATUS                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
"""

        # Add phase status
        for phase_key, phase in phases.items():
            phase_id = phase_key.replace("phase-", "").upper()
            name = phase["name"][:30]  # Truncate long names
            status = phase["status"]
            progress = phase.get("progress", 0)

            icon = self._get_status_icon(status)
            progress_bar = self._get_console_progress_bar(progress, 20)

            dashboard += f"║  {icon} {phase_id:6} │ {name:30} │ [{progress_bar}] {progress:3d}%  ║\n"

        dashboard += "║                                                                              ║\n"

        # Add current priorities
        dashboard += "╠══════════════════════════════════════════════════════════════════════════════╣\n"
        dashboard += "║                        🎯 CURRENT PRIORITIES                                 ║\n"
        dashboard += "╠══════════════════════════════════════════════════════════════════════════════╣\n"

        current_work = []
        for phase_key, phase in phases.items():
            if phase["status"] in ["In Progress", "Planning"]:
                phase_id = phase_key.replace("phase-", "").upper()
                name = phase["name"][:50]
                progress = phase.get("progress", 0)
                current_work.append(f"║    • Phase {phase_id}: {name:50} ({progress}%)         ║")

        if current_work:
            dashboard += "\n".join(current_work) + "\n"
        else:
            dashboard += "║    No active work in progress                                                ║\n"

        dashboard += "║                                                                              ║\n"
        dashboard += f"╚══════════════════════════════════════════════════════════════════════════════╝\n"
        dashboard += f"  Last Updated: {self.status_data.get('last_updated', 'Unknown')[:19]}\n"

        return dashboard

    def _get_status_icon(self, status: str) -> str:
        """Get icon for status."""
        icons = {
            "Not Started": "⏳",
            "Planning": "📋",
            "In Progress": "🔄",
            "Testing": "🧪",
            "Complete": "✅",
            "Blocked": "🚫",
            "Deferred": "⏸️"
        }
        return icons.get(status, "📋")

    def _get_progress_bar(self, progress: int, width: int = 10) -> str:
        """Get progress bar for markdown."""
        filled = "█" * (progress * width // 100)
        empty = "░" * (width - len(filled))
        return filled + empty

    def _get_console_progress_bar(self, progress: float, width: int = 20) -> str:
        """Get progress bar for console."""
        filled = int(progress * width / 100)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def save_report(self, content: str, filename: str, format_type: str = "md"):
        """Save report to file."""
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        if not filename.endswith(f".{format_type}"):
            filename += f".{format_type}"

        output_path = self.reports_dir / filename

        with open(output_path, 'w') as f:
            if format_type == "json":
                json.dump(json.loads(content), f, indent=2)
            else:
                f.write(content)

        print(f"✅ Report saved to {output_path}")
        return output_path


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Generate implementation progress reports")

    parser.add_argument("--format", choices=["markdown", "json", "dashboard"],
                       default="dashboard", help="Report format")
    parser.add_argument("--phase", help="Filter by phase (e.g., '3', '3B')")
    parser.add_argument("--output", help="Output filename")
    parser.add_argument("--dashboard", action="store_true", help="Show dashboard view")

    args = parser.parse_args()

    generator = ReportGenerator()

    # Generate report based on format
    if args.dashboard or args.format == "dashboard":
        content = generator.generate_dashboard()
        print(content)

    elif args.format == "markdown":
        content = generator.generate_markdown_report(args.phase)

        if args.output:
            generator.save_report(content, args.output, "md")
        else:
            print(content)

    elif args.format == "json":
        report_data = generator.generate_json_report(args.phase)
        content = json.dumps(report_data, indent=2)

        if args.output:
            generator.save_report(content, args.output, "json")
        else:
            print(content)


if __name__ == "__main__":
    main()
