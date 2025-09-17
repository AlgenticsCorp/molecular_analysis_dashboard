# Docking Engine Integration

## Overview

The docking engine integration layer provides a **pluggable adapter architecture** that supports multiple molecular docking engines (AutoDock Vina, Smina, Gnina, and custom engines) with consistent interfaces, error handling, and execution strategies.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Use Cases Layer                              │
├─────────────────────────────────────────────────────────────────┤
│               DockingEnginePort (Interface)                     │
├─────────────────────────────────────────────────────────────────┤
│                    Adapters Layer                               │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐        │
│  │VinaAdapter    │ │SminaAdapter   │ │GninaAdapter   │  ...   │
│  │               │ │               │ │               │        │
│  │• CLI Wrapper  │ │• CLI Wrapper  │ │• CLI Wrapper  │        │
│  │• Container    │ │• Container    │ │• Container    │        │
│  │• File I/O     │ │• File I/O     │ │• File I/O     │        │
│  └───────────────┘ └───────────────┘ └───────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Execution Strategies                            │
│  • Local Binary Execution                                      │
│  • Docker Container Execution                                  │
│  • Remote API Execution (future)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Port Interface Definition

```python
# ports/docking_engine_port.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import asyncio

@dataclass
class DockingInput:
    """Standardized docking input parameters."""
    receptor_file: Path          # Receptor (target protein) file path
    ligand_file: Path           # Ligand (small molecule) file path
    output_dir: Path            # Directory for output files

    # Common parameters (engine-agnostic)
    search_space: Dict[str, float] = None  # {center_x, center_y, center_z, size_x, size_y, size_z}
    exhaustiveness: int = 8                # Search exhaustiveness
    num_poses: int = 9                    # Number of output poses
    energy_range: float = 3.0             # Energy range for poses

    # Engine-specific parameters
    engine_params: Dict[str, Any] = None   # Additional engine-specific options

    # Execution context
    job_id: str = None                    # For tracking and cleanup
    timeout_seconds: int = 3600           # Execution timeout

@dataclass
class DockingResult:
    """Standardized docking execution result."""
    success: bool                         # Execution success status
    output_files: List[Path]             # Generated output files
    scores: List[float]                  # Binding affinity scores
    poses: int                           # Number of generated poses

    # Execution metadata
    execution_time_seconds: float        # Total execution time
    engine_version: str                  # Engine version used
    command_executed: str                # Full command that was run

    # Error information (if success=False)
    error_message: str = None            # Human-readable error message
    error_code: int = None               # Engine-specific error code
    stderr: str = None                   # Raw stderr output
    stdout: str = None                   # Raw stdout output

    # Performance metrics
    memory_usage_mb: float = None        # Peak memory usage
    cpu_time_seconds: float = None       # CPU time consumed

class DockingEnginePort(ABC):
    """Abstract interface for molecular docking engines."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return the name of the docking engine."""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> Dict[str, List[str]]:
        """
        Return supported file formats.

        Returns:
            Dict with 'receptor' and 'ligand' keys, each containing list of extensions
        """
        pass

    @abstractmethod
    async def validate_input(self, docking_input: DockingInput) -> List[str]:
        """
        Validate input parameters and files.

        Args:
            docking_input: Input parameters to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        pass

    @abstractmethod
    async def execute_docking(self, docking_input: DockingInput) -> DockingResult:
        """
        Execute molecular docking.

        Args:
            docking_input: Docking parameters and input files

        Returns:
            DockingResult with execution results and metadata

        Raises:
            DockingEngineError: If execution fails
            DockingTimeoutError: If execution exceeds timeout
        """
        pass

    @abstractmethod
    async def get_engine_info(self) -> Dict[str, Any]:
        """
        Get engine information and capabilities.

        Returns:
            Dict containing version, features, and configuration
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the engine is available and functional.

        Returns:
            True if engine is healthy, False otherwise
        """
        pass
```

## AutoDock Vina Adapter Implementation

```python
# adapters/docking_engines/vina_adapter.py
import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import time

from ports.docking_engine_port import DockingEnginePort, DockingInput, DockingResult
from infrastructure.config import get_docking_settings

logger = logging.getLogger(__name__)

class VinaAdapter(DockingEnginePort):
    """AutoDock Vina docking engine adapter."""

    def __init__(self):
        self.settings = get_docking_settings()
        self._vina_executable = self.settings.vina_executable
        self._use_containers = self.settings.use_containers
        self._container_image = "quay.io/biocontainers/autodock-vina:1.2.3--py39h99928e9_2"

    @property
    def engine_name(self) -> str:
        return "autodock_vina"

    @property
    def supported_formats(self) -> Dict[str, List[str]]:
        return {
            "receptor": [".pdbqt"],
            "ligand": [".pdbqt", ".sdf", ".mol2"]
        }

    async def validate_input(self, docking_input: DockingInput) -> List[str]:
        """Validate Vina-specific input requirements."""
        errors = []

        # Check file existence
        if not docking_input.receptor_file.exists():
            errors.append(f"Receptor file not found: {docking_input.receptor_file}")

        if not docking_input.ligand_file.exists():
            errors.append(f"Ligand file not found: {docking_input.ligand_file}")

        # Check file formats
        receptor_ext = docking_input.receptor_file.suffix.lower()
        ligand_ext = docking_input.ligand_file.suffix.lower()

        if receptor_ext not in self.supported_formats["receptor"]:
            errors.append(f"Unsupported receptor format: {receptor_ext}")

        if ligand_ext not in self.supported_formats["ligand"]:
            errors.append(f"Unsupported ligand format: {ligand_ext}")

        # Validate search space
        if docking_input.search_space:
            required_keys = ["center_x", "center_y", "center_z", "size_x", "size_y", "size_z"]
            missing_keys = [k for k in required_keys if k not in docking_input.search_space]
            if missing_keys:
                errors.append(f"Missing search space parameters: {missing_keys}")

        # Validate parameter ranges
        if docking_input.exhaustiveness < 1 or docking_input.exhaustiveness > 32:
            errors.append("Exhaustiveness must be between 1 and 32")

        if docking_input.num_poses < 1 or docking_input.num_poses > 100:
            errors.append("Number of poses must be between 1 and 100")

        return errors

    async def execute_docking(self, docking_input: DockingInput) -> DockingResult:
        """Execute AutoDock Vina docking."""
        start_time = time.time()

        try:
            # Create output directory
            docking_input.output_dir.mkdir(parents=True, exist_ok=True)

            if self._use_containers:
                result = await self._execute_with_container(docking_input)
            else:
                result = await self._execute_with_binary(docking_input)

            result.execution_time_seconds = time.time() - start_time
            return result

        except asyncio.TimeoutError:
            raise DockingTimeoutError(
                f"Vina execution exceeded timeout of {docking_input.timeout_seconds}s"
            )
        except Exception as e:
            logger.error(f"Vina execution failed: {e}")
            return DockingResult(
                success=False,
                output_files=[],
                scores=[],
                poses=0,
                execution_time_seconds=time.time() - start_time,
                engine_version=await self._get_vina_version(),
                command_executed="",
                error_message=str(e),
                stderr=getattr(e, 'stderr', ''),
                stdout=getattr(e, 'stdout', '')
            )

    async def _execute_with_container(self, docking_input: DockingInput) -> DockingResult:
        """Execute Vina using Docker container."""
        # RATIONALE: container execution provides isolation and reproducibility
        output_file = docking_input.output_dir / f"{docking_input.job_id}_vina_result.pdbqt"
        log_file = docking_input.output_dir / f"{docking_input.job_id}_vina.log"

        # Build Docker command
        cmd = self._build_container_command(docking_input, output_file, log_file)

        # Execute with timeout
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=docking_input.output_dir
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=docking_input.timeout_seconds
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        return await self._parse_vina_results(
            process.returncode,
            stdout.decode(),
            stderr.decode(),
            output_file,
            log_file,
            cmd
        )

    async def _execute_with_binary(self, docking_input: DockingInput) -> DockingResult:
        """Execute Vina using local binary."""
        output_file = docking_input.output_dir / f"{docking_input.job_id}_vina_result.pdbqt"
        log_file = docking_input.output_dir / f"{docking_input.job_id}_vina.log"

        # Build command arguments
        cmd = self._build_vina_command(docking_input, output_file, log_file)

        # Execute with timeout
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=docking_input.output_dir
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=docking_input.timeout_seconds
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        return await self._parse_vina_results(
            process.returncode,
            stdout.decode(),
            stderr.decode(),
            output_file,
            log_file,
            cmd
        )

    def _build_vina_command(self, docking_input: DockingInput, output_file: Path, log_file: Path) -> List[str]:
        """Build Vina command line arguments."""
        cmd = [
            self._vina_executable,
            "--receptor", str(docking_input.receptor_file),
            "--ligand", str(docking_input.ligand_file),
            "--out", str(output_file),
            "--log", str(log_file),
            "--exhaustiveness", str(docking_input.exhaustiveness),
            "--num_modes", str(docking_input.num_poses),
            "--energy_range", str(docking_input.energy_range)
        ]

        # Add search space if provided
        if docking_input.search_space:
            space = docking_input.search_space
            cmd.extend([
                "--center_x", str(space["center_x"]),
                "--center_y", str(space["center_y"]),
                "--center_z", str(space["center_z"]),
                "--size_x", str(space["size_x"]),
                "--size_y", str(space["size_y"]),
                "--size_z", str(space["size_z"])
            ])

        # Add engine-specific parameters
        if docking_input.engine_params:
            for key, value in docking_input.engine_params.items():
                cmd.extend([f"--{key}", str(value)])

        return cmd

    def _build_container_command(self, docking_input: DockingInput, output_file: Path, log_file: Path) -> List[str]:
        """Build Docker command for containerized execution."""
        # Mount directories for input/output
        receptor_dir = docking_input.receptor_file.parent
        ligand_dir = docking_input.ligand_file.parent
        output_dir = docking_input.output_dir

        cmd = [
            "docker", "run", "--rm",
            "-v", f"{receptor_dir}:/input/receptor:ro",
            "-v", f"{ligand_dir}:/input/ligand:ro",
            "-v", f"{output_dir}:/output",
            "--memory", self.settings.container_memory_limit,
            "--cpus", self.settings.container_cpu_limit,
            self._container_image,
            "vina"
        ]

        # Add Vina-specific arguments (adjust paths for container)
        receptor_name = docking_input.receptor_file.name
        ligand_name = docking_input.ligand_file.name
        output_name = output_file.name
        log_name = log_file.name

        cmd.extend([
            "--receptor", f"/input/receptor/{receptor_name}",
            "--ligand", f"/input/ligand/{ligand_name}",
            "--out", f"/output/{output_name}",
            "--log", f"/output/{log_name}",
            "--exhaustiveness", str(docking_input.exhaustiveness),
            "--num_modes", str(docking_input.num_poses),
            "--energy_range", str(docking_input.energy_range)
        ])

        # Add search space parameters
        if docking_input.search_space:
            space = docking_input.search_space
            cmd.extend([
                "--center_x", str(space["center_x"]),
                "--center_y", str(space["center_y"]),
                "--center_z", str(space["center_z"]),
                "--size_x", str(space["size_x"]),
                "--size_y", str(space["size_y"]),
                "--size_z", str(space["size_z"])
            ])

        return cmd

    async def _parse_vina_results(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
        output_file: Path,
        log_file: Path,
        command: List[str]
    ) -> DockingResult:
        """Parse Vina execution results."""
        success = returncode == 0 and output_file.exists()

        if not success:
            return DockingResult(
                success=False,
                output_files=[],
                scores=[],
                poses=0,
                execution_time_seconds=0,
                engine_version=await self._get_vina_version(),
                command_executed=" ".join(command),
                error_message=f"Vina execution failed with return code {returncode}",
                error_code=returncode,
                stderr=stderr,
                stdout=stdout
            )

        # Parse binding scores from log file
        scores = []
        poses = 0

        if log_file.exists():
            try:
                log_content = log_file.read_text()
                scores, poses = self._extract_scores_from_log(log_content)
            except Exception as e:
                logger.warning(f"Failed to parse Vina log file: {e}")

        output_files = [output_file]
        if log_file.exists():
            output_files.append(log_file)

        return DockingResult(
            success=True,
            output_files=output_files,
            scores=scores,
            poses=poses,
            execution_time_seconds=0,  # Will be set by caller
            engine_version=await self._get_vina_version(),
            command_executed=" ".join(command),
            stdout=stdout,
            stderr=stderr
        )

    def _extract_scores_from_log(self, log_content: str) -> tuple[List[float], int]:
        """Extract binding affinity scores from Vina log output."""
        scores = []
        lines = log_content.split('\n')

        # Look for the results table in Vina output
        in_results_section = False
        for line in lines:
            if 'mode' in line and 'affinity' in line:
                in_results_section = True
                continue

            if in_results_section and line.strip():
                try:
                    # Parse line like: "   1       -8.5      0.000      0.000"
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        score = float(parts[1])
                        scores.append(score)
                except (ValueError, IndexError):
                    # End of results table or unparseable line
                    break

        return scores, len(scores)

    async def _get_vina_version(self) -> str:
        """Get AutoDock Vina version."""
        try:
            if self._use_containers:
                cmd = [
                    "docker", "run", "--rm", self._container_image,
                    "vina", "--version"
                ]
            else:
                cmd = [self._vina_executable, "--version"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            version_output = stdout.decode() + stderr.decode()

            # Extract version from output
            for line in version_output.split('\n'):
                if 'AutoDock Vina' in line:
                    return line.strip()

            return "unknown"

        except Exception:
            return "unknown"

    async def get_engine_info(self) -> Dict[str, Any]:
        """Get Vina engine information."""
        return {
            "name": self.engine_name,
            "version": await self._get_vina_version(),
            "supported_formats": self.supported_formats,
            "execution_mode": "container" if self._use_containers else "binary",
            "container_image": self._container_image if self._use_containers else None,
            "executable_path": self._vina_executable if not self._use_containers else None,
            "features": [
                "flexible_ligand_docking",
                "exhaustive_search",
                "multiple_poses",
                "binding_affinity_scoring"
            ],
            "parameter_ranges": {
                "exhaustiveness": {"min": 1, "max": 32, "default": 8},
                "num_poses": {"min": 1, "max": 100, "default": 9},
                "energy_range": {"min": 0.1, "max": 10.0, "default": 3.0}
            }
        }

    async def health_check(self) -> bool:
        """Check if Vina is available and functional."""
        try:
            version = await self._get_vina_version()
            return version != "unknown"
        except Exception:
            return False

# Custom exceptions
class DockingEngineError(Exception):
    """Base exception for docking engine errors."""
    pass

class DockingTimeoutError(DockingEngineError):
    """Docking execution exceeded timeout."""
    pass

class DockingValidationError(DockingEngineError):
    """Input validation failed."""
    pass
```

## Engine Registry and Factory

```python
# infrastructure/docking_engine_registry.py
from typing import Dict, Type, List
from ports.docking_engine_port import DockingEnginePort
from adapters.docking_engines.vina_adapter import VinaAdapter
from adapters.docking_engines.smina_adapter import SminaAdapter
from adapters.docking_engines.gnina_adapter import GninaAdapter
from infrastructure.config import get_docking_settings

class DockingEngineRegistry:
    """Registry for available docking engines."""

    def __init__(self):
        self.settings = get_docking_settings()
        self._engines: Dict[str, Type[DockingEnginePort]] = {
            "vina": VinaAdapter,
            "smina": SminaAdapter,
            "gnina": GninaAdapter,
        }
        self._instances: Dict[str, DockingEnginePort] = {}

    def get_engine(self, engine_name: str) -> DockingEnginePort:
        """Get engine instance by name."""
        if engine_name not in self.settings.enabled_engines:
            raise ValueError(f"Engine '{engine_name}' is not enabled")

        if engine_name not in self._engines:
            raise ValueError(f"Unknown engine: '{engine_name}'")

        # Return cached instance or create new one
        if engine_name not in self._instances:
            engine_class = self._engines[engine_name]
            self._instances[engine_name] = engine_class()

        return self._instances[engine_name]

    def list_engines(self) -> List[str]:
        """List all available engine names."""
        return list(self._engines.keys())

    def list_enabled_engines(self) -> List[str]:
        """List enabled engine names."""
        return [
            name for name in self._engines.keys()
            if name in self.settings.enabled_engines
        ]

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all enabled engines."""
        health_status = {}

        for engine_name in self.list_enabled_engines():
            try:
                engine = self.get_engine(engine_name)
                health_status[engine_name] = await engine.health_check()
            except Exception:
                health_status[engine_name] = False

        return health_status

# Singleton registry instance
_registry: DockingEngineRegistry = None

def get_docking_engine_registry() -> DockingEngineRegistry:
    """Get singleton docking engine registry."""
    global _registry
    if _registry is None:
        _registry = DockingEngineRegistry()
    return _registry
```

## Usage in Use Cases

```python
# use_cases/docking_job_service.py
from ports.docking_engine_port import DockingInput
from infrastructure.docking_engine_registry import get_docking_engine_registry

class DockingJobService:
    """Use case for executing docking jobs."""

    def __init__(self):
        self.engine_registry = get_docking_engine_registry()

    async def execute_docking_job(
        self,
        job_id: str,
        engine_name: str,
        receptor_file: Path,
        ligand_file: Path,
        output_dir: Path,
        **params
    ) -> DockingResult:
        """Execute a docking job with specified engine."""

        # Get engine instance
        engine = self.engine_registry.get_engine(engine_name)

        # Prepare input
        docking_input = DockingInput(
            receptor_file=receptor_file,
            ligand_file=ligand_file,
            output_dir=output_dir,
            job_id=job_id,
            **params
        )

        # Validate input
        validation_errors = await engine.validate_input(docking_input)
        if validation_errors:
            raise DockingValidationError(f"Validation failed: {validation_errors}")

        # Execute docking
        result = await engine.execute_docking(docking_input)

        return result
```

## Configuration Integration

Add to `.env`:

```bash
# Docking Engine Configuration
DOCKING_ENABLED_ENGINES=vina,smina
DOCKING_EXECUTION_TIMEOUT=3600
DOCKING_MAX_CONCURRENT_JOBS=5

# Container Settings
DOCKING_USE_CONTAINERS=true
DOCKING_CONTAINER_MEMORY_LIMIT=2G
DOCKING_CONTAINER_CPU_LIMIT=1.0

# Binary Paths (when not using containers)
DOCKING_VINA_EXECUTABLE=/usr/local/bin/vina
DOCKING_SMINA_EXECUTABLE=/usr/local/bin/smina
DOCKING_GNINA_EXECUTABLE=/usr/local/bin/gnina
```

## Testing Strategy

```python
# tests/unit/test_vina_adapter.py
import pytest
from unittest.mock import AsyncMock, patch
from adapters.docking_engines.vina_adapter import VinaAdapter

@pytest.mark.unit
async def test_vina_validation():
    """Test input validation for Vina adapter."""
    adapter = VinaAdapter()

    # Test missing files
    docking_input = DockingInput(
        receptor_file=Path("/nonexistent/receptor.pdbqt"),
        ligand_file=Path("/nonexistent/ligand.pdbqt"),
        output_dir=Path("/tmp/output")
    )

    errors = await adapter.validate_input(docking_input)
    assert len(errors) == 2  # Both files missing
    assert "Receptor file not found" in errors[0]
    assert "Ligand file not found" in errors[1]

@pytest.mark.integration
async def test_vina_execution():
    """Test actual Vina execution (requires Docker or Vina binary)."""
    # This test would use real files and validate execution
    pass
```

## Error Handling and Monitoring

```python
# infrastructure/docking_monitoring.py
import logging
from typing import Dict, Any
from datetime import datetime

class DockingExecutionMonitor:
    """Monitor docking execution performance and errors."""

    def __init__(self):
        self.logger = logging.getLogger("docking.monitor")

    async def log_execution_start(self, job_id: str, engine_name: str, params: Dict[str, Any]):
        """Log start of docking execution."""
        self.logger.info(
            "Docking execution started",
            extra={
                "job_id": job_id,
                "engine": engine_name,
                "timestamp": datetime.utcnow().isoformat(),
                "params": params
            }
        )

    async def log_execution_result(self, job_id: str, result: DockingResult):
        """Log docking execution result."""
        self.logger.info(
            "Docking execution completed",
            extra={
                "job_id": job_id,
                "success": result.success,
                "execution_time": result.execution_time_seconds,
                "poses_generated": result.poses,
                "best_score": min(result.scores) if result.scores else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        if not result.success:
            self.logger.error(
                "Docking execution failed",
                extra={
                    "job_id": job_id,
                    "error_message": result.error_message,
                    "error_code": result.error_code,
                    "stderr": result.stderr[:1000] if result.stderr else None  # Truncate long output
                }
            )
```

This comprehensive docking engine integration documentation provides:

1. **Clear interfaces** via the `DockingEnginePort`
2. **Concrete implementation** for AutoDock Vina with both binary and container execution
3. **Registry pattern** for managing multiple engines
4. **Proper error handling** and validation
5. **Configuration integration** with the existing config system
6. **Testing strategies** for both unit and integration tests
7. **Monitoring and logging** capabilities

The architecture is extensible - adding Smina or Gnina adapters would follow the same pattern, implementing the `DockingEnginePort` interface.
