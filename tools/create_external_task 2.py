#!/usr/bin/env python3
"""Scaffold a new external task configuration entry.

The script generates a JSON configuration compatible with the task registry.
It does not register adapters or database records automatically, but it creates a
consistent starting point for new integrations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import dedent

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "config" / "tasks"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a task config skeleton that the task registry can load.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            Examples
            --------
            Create a GNINA configuration in the default directory:
                python tools/create_external_task.py \\
                    --task-id gnina-molecular-docking \\
                    --name "GNINA Molecular Docking" \\
                    --description "Dock small molecules" \\
                    --adapter-module molecular_analysis_dashboard.adapters.providers.neurosnap_task_adapter \\
                    --adapter-class NeuroSnapDockingAdapter
            """
        ),
    )

    parser.add_argument("--task-id", required=True, help="Unique identifier for the task")
    parser.add_argument("--name", required=True, help="Human readable name")
    parser.add_argument("--description", required=True, help="Short summary of the task")
    parser.add_argument(
        "--category",
        default="external",
        help="Logical category used for grouping tasks (default: external)",
    )
    parser.add_argument(
        "--adapter-module",
        required=True,
        help="Python module path that exposes the adapter class",
    )
    parser.add_argument(
        "--adapter-class",
        required=True,
        help="Adapter class name inside the provided module",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional explicit output path. Defaults to config/tasks/<task-id>.json",
    )

    return parser


def build_config(args: argparse.Namespace) -> dict[str, object]:
    return {
        "id": args.task_id,
        "adapter": {
            "module": args.adapter_module,
            "class": args.adapter_class,
        },
        "metadata": {
            "name": args.name,
            "description": args.description,
            "category": args.category,
            "version": "1.0.0",
            "tags": [],
            "provider": "external",
            "interface_type": "openapi",
            "parameters": [
                {
                    "name": "example_file",
                    "type": "file",
                    "required": True,
                    "description": "Replace with your first required input file",
                    "validation": {
                        "file_types": [".dat"],
                        "max_size_mb": 50
                    }
                }
            ],
            "resource_requirements": {
                "cpu": "2",
                "memory": "4Gi"
            },
            "execution_time_estimate": 600,
            "source": "framework"
        }
    }


def ensure_output_path(path: Path) -> None:
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)



def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    output_path = args.output or (DEFAULT_OUTPUT_DIR / f"{args.task_id}.json")
    ensure_output_path(output_path)

    config = build_config(args)
    output_path.write_text(json.dumps(config, indent=2))
    print(f"Created task configuration at {output_path}")


if __name__ == "__main__":
    main()
