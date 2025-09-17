#!/usr/bin/env python3
"""Health check script for template validation."""

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is supported."""
    if sys.version_info < (3, 9):
        return False, f"Python {sys.version} < 3.9 (minimum required)"
    return True, f"Python {sys.version} ✓"


def check_command_available(cmd: str) -> Tuple[bool, str]:
    """Check if a command is available in PATH."""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True, f"{cmd} available ✓"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, f"{cmd} not found"


def check_python_import(module: str) -> Tuple[bool, str]:
    """Check if a Python module can be imported."""
    try:
        importlib.import_module(module)
        return True, f"{module} importable ✓"
    except ImportError:
        return False, f"{module} not importable"


def check_file_exists(filepath: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        return True, f"{filepath} exists ✓"
    return False, f"{filepath} missing"


def run_health_checks() -> bool:
    """Run all health checks and return overall status."""
    checks: List[Tuple[bool, str]] = []

    print("🔍 Running Template Health Checks...\n")

    # Python version check
    checks.append(check_python_version())

    # Critical Python modules
    critical_modules = [
        "pytest",
        "black",
        "isort",
        "mypy",
        "flake8",
        "bandit",
        "pylint",
        "pre_commit",
    ]

    for module in critical_modules:
        checks.append(check_python_import(module))

    # Optional system commands
    optional_commands = ["dot", "pyan3"]
    for cmd in optional_commands:
        result, msg = check_command_available(cmd)
        if result:
            checks.append((True, f"{msg}"))
        else:
            checks.append((True, f"{msg} (optional)"))

    # Critical files
    critical_files = [
        "pyproject.toml",
        ".pre-commit-config.yaml",
        "bootstrap.sh",
        "src/molecular_analysis_dashboard/__init__.py",
    ]

    for filepath in critical_files:
        checks.append(check_file_exists(filepath))

    # Print results
    failed_checks = 0
    for success, message in checks:
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        if not success:
            failed_checks += 1

    print(f"\n📊 Summary: {len(checks) - failed_checks}/{len(checks)} checks passed")

    if failed_checks == 0:
        print("🎉 All health checks passed! Template is ready to use.")
        return True
    else:
        print(f"⚠️  {failed_checks} checks failed. See above for details.")
        return False


def main() -> None:
    """Main health check runner."""
    try:
        success = run_health_checks()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
