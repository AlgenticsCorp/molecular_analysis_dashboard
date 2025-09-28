# Service Integration Guide

**Version:** 1.0
**Last Updated:** September 27, 2025
**Based on:** Successful NeuroSnap GNINA Integration Patterns

This guide provides a comprehensive, step-by-step process for integrating new external services into the Molecular Analysis Dashboard. It follows the Clean Architecture patterns and proven integration approaches established during the NeuroSnap GNINA integration milestone.

## 📋 **Prerequisites**

Before starting a new service integration:

- [ ] **Clean Architecture Understanding**: Review [Clean Architecture Guide](../architecture/system-design/clean-architecture.md)
- [ ] **Development Environment**: [Development Setup](../getting-started/setup.md) complete
- [ ] **API Basics**: Familiar with [FastAPI patterns](../api/contracts/README.md)
- [ ] **Testing Setup**: [Testing Workflows](../workflows/testing-workflows.md) configured

## 🎯 **Integration Overview**

### **Service Integration Components**
Every external service integration involves these core components:

```
External Service Integration
├── 1. Domain Layer (Business Logic)
│   ├── Entity Models (Molecule, Job, Result)
│   └── Port Interfaces (Abstract contracts)
├── 2. Infrastructure Layer (External Adapters)
│   ├── Service Adapter (HTTP client, authentication)
│   └── Configuration (Settings, credentials)
├── 3. Application Layer (Use Cases)
│   ├── Orchestration Logic (Submit, Monitor, Retrieve)
│   └── Error Handling (Service-specific exceptions)
├── 4. Presentation Layer (API Endpoints)
│   ├── FastAPI Routes (REST endpoints)
│   ├── Pydantic Schemas (Request/Response validation)
│   └── OpenAPI Documentation (SwaggerUI)
└── 5. Testing Strategy
    ├── Unit Tests (Domain, Use Cases)
    ├── Integration Tests (API, External Service)
    └── End-to-End Tests (Complete workflows)
```

---

## 🏗️ **Step-by-Step Integration Process**

### **Phase 1: Planning & Design** (1-2 hours)

#### **Step 1.1: Service Analysis**
Research and document the external service:

1. **Service Documentation**: Collect API documentation, authentication methods
2. **Endpoints Analysis**: Identify key endpoints (submit, status, results, download)
3. **Authentication**: Determine auth method (API key, OAuth2, custom)
4. **Data Formats**: Input/output formats (JSON, multipart, binary files)
5. **Rate Limits**: Understand service limitations and quotas

**Template: Service Analysis Document**
```markdown
# [Service Name] Integration Analysis

## Service Overview
- **Provider**: [Company/Organization]
- **Base URL**: https://api.example.com
- **Documentation**: [Link to docs]
- **Purpose**: [Brief description of what this service does]

## Authentication
- **Method**: [API Key / OAuth2 / Custom]
- **Headers**: [Required authentication headers]
- **Credentials**: [How to obtain/configure credentials]

## Key Endpoints
- **Submit Job**: POST /api/v1/jobs
- **Check Status**: GET /api/v1/jobs/{job_id}
- **Get Results**: GET /api/v1/jobs/{job_id}/results
- **Download Files**: GET /api/v1/jobs/{job_id}/files/{filename}

## Input/Output Formats
- **Input**: [File formats, parameters]
- **Output**: [Result formats, file types]
- **Errors**: [Common error responses]
```

#### **Step 1.2: Integration Scope Definition**
Define what functionality to implement:

```markdown
## Integration Scope
- [ ] Job submission with file uploads
- [ ] Real-time status monitoring
- [ ] Result retrieval and parsing
- [ ] File download capabilities
- [ ] Error handling and retry logic
- [ ] SwaggerUI documentation
```

---

### **Phase 2: Infrastructure Setup** (2-3 hours)

#### **Step 2.1: Project Structure Creation**
Create the directory structure for your service:

```bash
cd src/molecular_analysis_dashboard

# Create provider-specific directories
mkdir -p adapters/external/providers/[service_name]
mkdir -p tests/unit/adapters/external/[service_name]
mkdir -p tests/integration/providers/[service_name]
```

**Example for a service called "ChemDock":**
```bash
mkdir -p adapters/external/providers/chemdock
mkdir -p tests/unit/adapters/external/chemdock
mkdir -p tests/integration/providers/chemdock
```

#### **Step 2.2: Environment Configuration**
Add service configuration to settings:

1. **Update `infrastructure/settings.py`:**
```python
# Add to Settings class
class Settings(BaseSettings):
    # ... existing settings ...

    # [Service Name] Configuration
    [SERVICE_NAME]_API_URL: str = "https://api.example.com"
    [SERVICE_NAME]_API_KEY: Optional[str] = None
    [SERVICE_NAME]_TIMEOUT: int = 600
    [SERVICE_NAME]_MAX_RETRIES: int = 3

    class Config:
        env_file = ".env"
```

2. **Update `.env.example`:**
```bash
# [Service Name] Configuration
[SERVICE_NAME]_API_URL=https://api.example.com
[SERVICE_NAME]_API_KEY=your-api-key-here
[SERVICE_NAME]_TIMEOUT=600
[SERVICE_NAME]_MAX_RETRIES=3
```

---

### **Phase 3: Domain Layer Implementation** (1-2 hours)

#### **Step 3.1: Port Interface Definition**
Create the abstract interface for your service:

**File:** `ports/external/[service_name]_port.py`
```python
"""Port interface for [Service Name] integration."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from domain.entities.job import Job, JobStatus
from domain.entities.result import JobResult

class [ServiceName]Port(ABC):
    """Abstract interface for [Service Name] docking service."""

    @abstractmethod
    async def submit_job(
        self,
        ligand_file: bytes,
        receptor_file: bytes,
        parameters: Dict[str, Any]
    ) -> str:
        """Submit a docking job and return job ID."""
        pass

    @abstractmethod
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get current status of a job."""
        pass

    @abstractmethod
    async def get_job_results(self, job_id: str) -> JobResult:
        """Retrieve job results and metadata."""
        pass

    @abstractmethod
    async def download_result_file(self, job_id: str, filename: str) -> bytes:
        """Download a specific result file."""
        pass

    @abstractmethod
    async def list_result_files(self, job_id: str) -> List[str]:
        """List available result files for a job."""
        pass
```

---

### **Phase 4: Infrastructure Layer Implementation** (4-6 hours)

#### **Step 4.1: Service Adapter Implementation**
Create the concrete implementation of your port:

**File:** `adapters/external/providers/[service_name]/[service_name]_adapter.py`

```python
"""[Service Name] service adapter implementation."""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ports.external.[service_name]_port import [ServiceName]Port
from domain.entities.job import JobStatus
from domain.entities.result import JobResult
from infrastructure.settings import get_settings

logger = logging.getLogger(__name__)

class [ServiceName]Adapter([ServiceName]Port):
    """Concrete implementation of [Service Name] integration."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.[SERVICE_NAME]_API_URL
        self.api_key = self.settings.[SERVICE_NAME]_API_KEY
        self.timeout = self.settings.[SERVICE_NAME]_TIMEOUT
        self.max_retries = self.settings.[SERVICE_NAME]_MAX_RETRIES

        if not self.api_key:
            raise ValueError("[Service Name] API key not configured")

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "MolecularAnalysisDashboard/1.0"
        }

    async def submit_job(
        self,
        ligand_file: bytes,
        receptor_file: bytes,
        parameters: Dict[str, Any]
    ) -> str:
        """Submit a docking job to [Service Name]."""

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Prepare multipart form data
            files = {
                "ligand": ("ligand.pdb", ligand_file, "chemical/x-pdb"),
                "receptor": ("receptor.pdb", receptor_file, "chemical/x-pdb")
            }

            data = {
                **parameters,
                "job_type": "molecular_docking",
                "return_format": "json"
            }

            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/jobs",
                    headers=self._get_headers(),
                    files=files,
                    data=data
                )
                response.raise_for_status()

                result = response.json()
                job_id = result.get("job_id")

                if not job_id:
                    raise ValueError(f"No job_id in [Service Name] response: {result}")

                logger.info(f"[Service Name] job submitted successfully: {job_id}")
                return job_id

            except httpx.HTTPStatusError as e:
                logger.error(f"[Service Name] API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"[Service Name] submission failed: {e.response.status_code}")
            except Exception as e:
                logger.error(f"[Service Name] submission error: {e}")
                raise

    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get current status of a [Service Name] job."""

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/jobs/{job_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()

                result = response.json()
                status_str = result.get("status", "unknown").lower()

                # Map service-specific statuses to our domain statuses
                status_mapping = {
                    "pending": JobStatus.PENDING,
                    "running": JobStatus.RUNNING,
                    "completed": JobStatus.COMPLETED,
                    "failed": JobStatus.FAILED,
                    "cancelled": JobStatus.CANCELLED
                }

                return status_mapping.get(status_str, JobStatus.UNKNOWN)

            except httpx.HTTPStatusError as e:
                logger.error(f"[Service Name] status check error: {e.response.status_code}")
                if e.response.status_code == 404:
                    return JobStatus.NOT_FOUND
                raise Exception(f"[Service Name] status check failed: {e.response.status_code}")

    async def get_job_results(self, job_id: str) -> JobResult:
        """Retrieve job results from [Service Name]."""

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/jobs/{job_id}/results",
                    headers=self._get_headers()
                )
                response.raise_for_status()

                result = response.json()

                return JobResult(
                    job_id=job_id,
                    status=JobStatus.COMPLETED,
                    files=result.get("files", []),
                    metadata=result.get("metadata", {}),
                    created_at=datetime.fromisoformat(result.get("created_at")),
                    completed_at=datetime.fromisoformat(result.get("completed_at"))
                )

            except httpx.HTTPStatusError as e:
                logger.error(f"[Service Name] results error: {e.response.status_code}")
                raise Exception(f"[Service Name] results retrieval failed: {e.response.status_code}")

    async def download_result_file(self, job_id: str, filename: str) -> bytes:
        """Download a specific result file from [Service Name]."""

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/jobs/{job_id}/files/{filename}",
                    headers=self._get_headers()
                )
                response.raise_for_status()

                return response.content

            except httpx.HTTPStatusError as e:
                logger.error(f"[Service Name] file download error: {e.response.status_code}")
                raise Exception(f"[Service Name] file download failed: {e.response.status_code}")

    async def list_result_files(self, job_id: str) -> List[str]:
        """List available result files for a [Service Name] job."""

        result = await self.get_job_results(job_id)
        return [file_info.get("name", "") for file_info in result.files]
```

#### **Step 4.2: Authentication Module** (if needed)
For complex authentication, create a separate auth module:

**File:** `adapters/external/providers/[service_name]/authentication.py`
```python
"""Authentication handling for [Service Name]."""

import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta

class [ServiceName]AuthHandler:
    """Handle authentication for [Service Name] API."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary."""

        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token

        # Token expired or doesn't exist, get new one
        return await self._refresh_token()

    async def _refresh_token(self) -> str:
        """Refresh the access token."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

            return self._access_token
```

---

### **Phase 5: Application Layer Implementation** (2-3 hours)

#### **Step 5.1: Use Case Implementation**
Create use cases that orchestrate the service integration:

**File:** `use_cases/external/submit_[service_name]_job.py`
```python
"""Use case for submitting jobs to [Service Name]."""

import logging
from typing import Dict, Any

from ports.external.[service_name]_port import [ServiceName]Port
from domain.entities.job import Job
from shared.exceptions import ServiceIntegrationError

logger = logging.getLogger(__name__)

class Submit[ServiceName]JobUseCase:
    """Use case for submitting molecular docking jobs to [Service Name]."""

    def __init__(self, [service_name]_port: [ServiceName]Port):
        self.[service_name]_port = [service_name]_port

    async def execute(
        self,
        ligand_file: bytes,
        receptor_file: bytes,
        parameters: Dict[str, Any],
        user_id: str,
        org_id: str
    ) -> str:
        """
        Submit a molecular docking job to [Service Name].

        Args:
            ligand_file: Ligand structure file content
            receptor_file: Receptor structure file content
            parameters: Docking parameters
            user_id: User identifier
            org_id: Organization identifier

        Returns:
            str: Job ID from [Service Name]

        Raises:
            ServiceIntegrationError: If submission fails
        """

        try:
            # Add metadata to parameters
            enhanced_parameters = {
                **parameters,
                "submitted_by": user_id,
                "organization": org_id,
                "source": "molecular_analysis_dashboard"
            }

            # Submit job to external service
            job_id = await self.[service_name]_port.submit_job(
                ligand_file=ligand_file,
                receptor_file=receptor_file,
                parameters=enhanced_parameters
            )

            logger.info(f"[Service Name] job submitted: {job_id} by user {user_id}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to submit [Service Name] job: {e}")
            raise ServiceIntegrationError(f"[Service Name] job submission failed: {str(e)}")
```

---

### **Phase 6: Presentation Layer Implementation** (3-4 hours)

#### **Step 6.1: API Routes Implementation**
Create FastAPI routes for your service:

**File:** `presentation/api/routes/providers/[service_name]/docking_routes.py`
```python
"""[Service Name] docking API routes."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import logging

from use_cases.external.submit_[service_name]_job import Submit[ServiceName]JobUseCase
from ports.external.[service_name]_port import [ServiceName]Port
from presentation.api.dependencies import get_current_user, get_[service_name]_port
from presentation.api.schemas.docking import (
    JobSubmissionResponse,
    JobStatusResponse,
    JobResultsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/providers/[service_name]/docking", tags=["[Service Name] GNINA"])

@router.post("/submit", response_model=JobSubmissionResponse)
async def submit_docking_job(
    ligand: UploadFile = File(..., description="Ligand structure file (PDB, SDF, MOL2)"),
    receptor: UploadFile = File(..., description="Receptor structure file (PDB)"),
    center_x: Optional[float] = Form(0.0, description="X coordinate for binding site center"),
    center_y: Optional[float] = Form(0.0, description="Y coordinate for binding site center"),
    center_z: Optional[float] = Form(0.0, description="Z coordinate for binding site center"),
    size_x: Optional[float] = Form(20.0, description="Search space size in X dimension"),
    size_y: Optional[float] = Form(20.0, description="Search space size in Y dimension"),
    size_z: Optional[float] = Form(20.0, description="Search space size in Z dimension"),
    exhaustiveness: Optional[int] = Form(8, description="Thoroughness of the search"),
    num_modes: Optional[int] = Form(9, description="Maximum number of binding modes to generate"),
    current_user: dict = Depends(get_current_user),
    [service_name]_port: [ServiceName]Port = Depends(get_[service_name]_port)
):
    """
    Submit a molecular docking job to [Service Name] GNINA.

    This endpoint accepts ligand and receptor files along with docking parameters
    and submits them to [Service Name] for processing using the GNINA engine.

    **File Requirements:**
    - Ligand: PDB, SDF, or MOL2 format
    - Receptor: PDB format
    - Files must be properly formatted molecular structures

    **Parameters:**
    - center_*: Define the binding site center coordinates
    - size_*: Define the search space dimensions (Angstroms)
    - exhaustiveness: Higher values = more thorough search (1-8)
    - num_modes: Number of output conformations (1-20)

    **Returns:**
    - job_id: Unique identifier for tracking the docking job
    - status: Initial job status (typically "submitted")
    - estimated_duration: Expected completion time
    """

    try:
        # Read uploaded files
        ligand_content = await ligand.read()
        receptor_content = await receptor.read()

        # Prepare parameters
        parameters = {
            "center_x": center_x,
            "center_y": center_y,
            "center_z": center_z,
            "size_x": size_x,
            "size_y": size_y,
            "size_z": size_z,
            "exhaustiveness": exhaustiveness,
            "num_modes": num_modes,
            "ligand_filename": ligand.filename,
            "receptor_filename": receptor.filename
        }

        # Submit job via use case
        use_case = Submit[ServiceName]JobUseCase([service_name]_port)
        job_id = await use_case.execute(
            ligand_file=ligand_content,
            receptor_file=receptor_content,
            parameters=parameters,
            user_id=current_user["sub"],
            org_id=current_user.get("org_id", "default")
        )

        return JobSubmissionResponse(
            job_id=job_id,
            status="submitted",
            message=f"Job submitted successfully to [Service Name]",
            estimated_duration="5-10 minutes"
        )

    except Exception as e:
        logger.error(f"[Service Name] job submission error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit docking job: {str(e)}"
        )

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    [service_name]_port: [ServiceName]Port = Depends(get_[service_name]_port)
):
    """
    Get the current status of a [Service Name] docking job.

    **Job Statuses:**
    - `pending`: Job queued, waiting to start
    - `running`: Job currently executing
    - `completed`: Job finished successfully
    - `failed`: Job encountered an error
    - `cancelled`: Job was cancelled by user or system

    **Progress Tracking:**
    For running jobs, additional progress information may be available
    including current step and estimated time remaining.
    """

    try:
        status = await [service_name]_port.get_job_status(job_id)

        return JobStatusResponse(
            job_id=job_id,
            status=status.value,
            progress=None,  # [Service Name] doesn't provide detailed progress
            message=f"Job status retrieved from [Service Name]",
            last_updated="2025-09-27T20:00:00Z"
        )

    except Exception as e:
        logger.error(f"[Service Name] status check error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

@router.get("/results/{job_id}", response_model=JobResultsResponse)
async def get_job_results(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    [service_name]_port: [ServiceName]Port = Depends(get_[service_name]_port)
):
    """
    Retrieve results and metadata for a completed [Service Name] docking job.

    **Available Results:**
    - Docked poses in SDF format
    - Binding affinity scores
    - RMSD values for pose accuracy
    - Log files with detailed execution information
    - Visualization files for molecular viewers

    **Result Files:**
    Each job produces multiple output files that can be downloaded
    individually using the download endpoint.
    """

    try:
        results = await [service_name]_port.get_job_results(job_id)

        return JobResultsResponse(
            job_id=job_id,
            status=results.status.value,
            files=results.files,
            metadata=results.metadata,
            created_at=results.created_at.isoformat(),
            completed_at=results.completed_at.isoformat() if results.completed_at else None
        )

    except Exception as e:
        logger.error(f"[Service Name] results retrieval error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job results: {str(e)}"
        )

@router.get("/download/{job_id}/{filename}")
async def download_result_file(
    job_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
    [service_name]_port: [ServiceName]Port = Depends(get_[service_name]_port)
):
    """
    Download a specific result file from a completed [Service Name] docking job.

    **Available Files:**
    - `docked_poses.sdf`: All docked poses with scores
    - `best_pose.pdb`: Highest scoring pose
    - `binding_affinities.txt`: Detailed scoring information
    - `docking.log`: Complete execution log
    - `pymol_session.pse`: PyMOL visualization session

    **File Formats:**
    Files are returned in their original format with appropriate
    Content-Type headers for direct use or download.
    """

    try:
        # Validate filename to prevent directory traversal
        if ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        file_content = await [service_name]_port.download_result_file(job_id, filename)

        # Determine content type based on file extension
        content_types = {
            '.sdf': 'chemical/x-mdl-sdfile',
            '.pdb': 'chemical/x-pdb',
            '.txt': 'text/plain',
            '.log': 'text/plain',
            '.pse': 'application/octet-stream'
        }

        file_ext = '.' + filename.split('.')[-1].lower()
        content_type = content_types.get(file_ext, 'application/octet-stream')

        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"[Service Name] file download error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file: {str(e)}"
        )
```

#### **Step 6.2: Dependency Injection Setup**
Add your service to the dependency injection system:

**File:** `presentation/api/dependencies.py` (add to existing file)
```python
# Add to existing dependencies

from adapters.external.providers.[service_name].[service_name]_adapter import [ServiceName]Adapter
from ports.external.[service_name]_port import [ServiceName]Port

async def get_[service_name]_port() -> [ServiceName]Port:
    """Dependency injection for [Service Name] port."""
    return [ServiceName]Adapter()
```

#### **Step 6.3: Route Registration**
Register your routes in the main application:

**File:** `presentation/api/main.py` (add to existing file)
```python
# Add to existing imports
from presentation.api.routes.providers.[service_name].docking_routes import router as [service_name]_router

# Add to existing app setup
app.include_router([service_name]_router)
```

---

### **Phase 7: Testing Implementation** (4-5 hours)

#### **Step 7.1: Unit Tests**
Create unit tests for your adapter:

**File:** `tests/unit/adapters/external/test_[service_name]_adapter.py`
```python
"""Unit tests for [Service Name] adapter."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from adapters.external.providers.[service_name].[service_name]_adapter import [ServiceName]Adapter
from domain.entities.job import JobStatus


class Test[ServiceName]Adapter:
    """Test [Service Name] adapter functionality."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance for testing."""
        with patch('adapters.external.providers.[service_name].[service_name]_adapter.get_settings') as mock_settings:
            mock_settings.return_value.[SERVICE_NAME]_API_URL = "https://api.test.com"
            mock_settings.return_value.[SERVICE_NAME]_API_KEY = "test-api-key"
            mock_settings.return_value.[SERVICE_NAME]_TIMEOUT = 60
            mock_settings.return_value.[SERVICE_NAME]_MAX_RETRIES = 3

            return [ServiceName]Adapter()

    @pytest.mark.asyncio
    async def test_submit_job_success(self, adapter):
        """Test successful job submission."""

        mock_response = {
            "job_id": "test-job-123",
            "status": "submitted",
            "message": "Job submitted successfully"
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status.return_value = None

            job_id = await adapter.submit_job(
                ligand_file=b"fake ligand data",
                receptor_file=b"fake receptor data",
                parameters={"center_x": 0.0, "center_y": 0.0, "center_z": 0.0}
            )

            assert job_id == "test-job-123"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_job_status_completed(self, adapter):
        """Test getting job status for completed job."""

        mock_response = {"status": "completed", "progress": 100}

        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status.return_value = None

            status = await adapter.get_job_status("test-job-123")

            assert status == JobStatus.COMPLETED
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_job_api_error(self, adapter):
        """Test job submission API error handling."""

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "API Error", request=None, response=AsyncMock(status_code=500)
            )

            with pytest.raises(Exception) as exc_info:
                await adapter.submit_job(
                    ligand_file=b"fake ligand data",
                    receptor_file=b"fake receptor data",
                    parameters={}
                )

            assert "[Service Name] submission failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_result_file(self, adapter):
        """Test downloading result files."""

        fake_file_content = b"fake file content"

        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value.content = fake_file_content
            mock_get.return_value.raise_for_status.return_value = None

            content = await adapter.download_result_file("test-job-123", "results.sdf")

            assert content == fake_file_content
            mock_get.assert_called_once()
```

#### **Step 7.2: Integration Tests**
Create integration tests for API routes:

**File:** `tests/integration/providers/test_[service_name]_api.py`
```python
"""Integration tests for [Service Name] API routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from presentation.api.main import app
from domain.entities.job import JobStatus

client = TestClient(app)

class Test[ServiceName]API:
    """Test [Service Name] API integration."""

    @pytest.fixture
    def mock_[service_name]_port(self):
        """Mock [Service Name] port for testing."""
        return AsyncMock()

    @patch('presentation.api.dependencies.get_[service_name]_port')
    @patch('presentation.api.dependencies.get_current_user')
    def test_submit_job_success(self, mock_user, mock_port_dep, mock_[service_name]_port):
        """Test successful job submission via API."""

        # Setup mocks
        mock_user.return_value = {"sub": "user123", "org_id": "org456"}
        mock_port_dep.return_value = mock_[service_name]_port
        mock_[service_name]_port.submit_job.return_value = "test-job-123"

        # Prepare test files
        ligand_file = ("ligand.pdb", b"fake ligand content", "chemical/x-pdb")
        receptor_file = ("receptor.pdb", b"fake receptor content", "chemical/x-pdb")

        # Make API request
        response = client.post(
            "/api/v1/providers/[service_name]/docking/submit",
            files={
                "ligand": ligand_file,
                "receptor": receptor_file
            },
            data={
                "center_x": 0.0,
                "center_y": 0.0,
                "center_z": 0.0,
                "exhaustiveness": 8
            }
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "submitted"

        # Verify service was called
        mock_[service_name]_port.submit_job.assert_called_once()

    @patch('presentation.api.dependencies.get_[service_name]_port')
    @patch('presentation.api.dependencies.get_current_user')
    def test_get_job_status(self, mock_user, mock_port_dep, mock_[service_name]_port):
        """Test job status retrieval via API."""

        # Setup mocks
        mock_user.return_value = {"sub": "user123"}
        mock_port_dep.return_value = mock_[service_name]_port
        mock_[service_name]_port.get_job_status.return_value = JobStatus.COMPLETED

        # Make API request
        response = client.get(
            "/api/v1/providers/[service_name]/docking/status/test-job-123"
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "completed"

    def test_submit_job_missing_files(self):
        """Test job submission with missing required files."""

        response = client.post(
            "/api/v1/providers/[service_name]/docking/submit",
            data={"center_x": 0.0}
        )

        assert response.status_code == 422  # Validation error
```

#### **Step 7.3: End-to-End Tests**
Create E2E tests for complete workflows:

**File:** `tests/e2e/test_[service_name]_workflow.py`
```python
"""End-to-end tests for [Service Name] docking workflow."""

import pytest
import time
from fastapi.testclient import TestClient

from presentation.api.main import app

client = TestClient(app)

@pytest.mark.e2e
@pytest.mark.slow
class Test[ServiceName]E2EWorkflow:
    """End-to-end workflow tests for [Service Name] integration."""

    @pytest.mark.skipif(
        not pytest.config.getoption("--e2e"),
        reason="E2E tests require --e2e flag"
    )
    def test_complete_docking_workflow(self):
        """Test complete workflow from job submission to result retrieval."""

        # Step 1: Submit job
        with open("tests/fixtures/sample_ligand.pdb", "rb") as ligand:
            with open("tests/fixtures/sample_receptor.pdb", "rb") as receptor:

                response = client.post(
                    "/api/v1/providers/[service_name]/docking/submit",
                    files={
                        "ligand": ("ligand.pdb", ligand.read(), "chemical/x-pdb"),
                        "receptor": ("receptor.pdb", receptor.read(), "chemical/x-pdb")
                    },
                    data={
                        "center_x": 0.0,
                        "center_y": 0.0,
                        "center_z": 0.0,
                        "exhaustiveness": 1  # Low exhaustiveness for faster testing
                    }
                )

        assert response.status_code == 200
        job_data = response.json()
        job_id = job_data["job_id"]

        # Step 2: Monitor job status
        max_wait = 300  # 5 minutes max wait
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_response = client.get(
                f"/api/v1/providers/[service_name]/docking/status/{job_id}"
            )

            assert status_response.status_code == 200
            status_data = status_response.json()

            if status_data["status"] == "completed":
                break
            elif status_data["status"] == "failed":
                pytest.fail(f"Job failed: {status_data}")

            time.sleep(10)  # Wait 10 seconds between checks

        # Step 3: Retrieve results
        results_response = client.get(
            f"/api/v1/providers/[service_name]/docking/results/{job_id}"
        )

        assert results_response.status_code == 200
        results_data = results_response.json()
        assert results_data["status"] == "completed"
        assert len(results_data["files"]) > 0

        # Step 4: Download result file
        first_file = results_data["files"][0]["name"]
        download_response = client.get(
            f"/api/v1/providers/[service_name]/docking/download/{job_id}/{first_file}"
        )

        assert download_response.status_code == 200
        assert len(download_response.content) > 0
```

---

### **Phase 8: Documentation & Testing** (2-3 hours)

#### **Step 8.1: API Documentation Enhancement**
Your OpenAPI documentation should automatically include your routes. Verify by:

1. **Start Development Server:**
```bash
docker compose up -d api
```

2. **Check SwaggerUI:**
   - Visit http://localhost/docs
   - Verify your service endpoints appear under "[Service Name] GNINA" tag
   - Test endpoints interactively

3. **Enhance Documentation:**
Add more detailed examples and error responses to your route docstrings.

#### **Step 8.2: Integration Testing**
Run your tests to ensure everything works:

```bash
# Unit tests
pytest tests/unit/adapters/external/test_[service_name]_adapter.py -v

# Integration tests
pytest tests/integration/providers/test_[service_name]_api.py -v

# End-to-end tests (optional, requires real service)
pytest tests/e2e/test_[service_name]_workflow.py -v --e2e
```

#### **Step 8.3: Service Documentation**
Create service-specific documentation:

**File:** `docs/integration/services/[service_name]-integration.md`
```markdown
# [Service Name] Integration Guide

## Overview
[Service Name] is integrated as a molecular docking provider offering GNINA-based docking capabilities.

## Configuration
```bash
# Environment variables
[SERVICE_NAME]_API_URL=https://api.[service_name].com
[SERVICE_NAME]_API_KEY=your-api-key
[SERVICE_NAME]_TIMEOUT=600
```

## API Endpoints
- POST `/api/v1/providers/[service_name]/docking/submit` - Submit docking job
- GET `/api/v1/providers/[service_name]/docking/status/{job_id}` - Check status
- GET `/api/v1/providers/[service_name]/docking/results/{job_id}` - Get results
- GET `/api/v1/providers/[service_name]/docking/download/{job_id}/{filename}` - Download files

## Usage Examples
[Include cURL examples and code samples]

## Troubleshooting
[Common issues and solutions]
```

---

## ✅ **Integration Checklist**

### **Phase 1: Planning & Design**
- [ ] Service analysis document created
- [ ] Integration scope defined
- [ ] Authentication method determined
- [ ] File formats and parameters documented

### **Phase 2: Infrastructure Setup**
- [ ] Directory structure created
- [ ] Environment configuration added
- [ ] Settings updated with service parameters

### **Phase 3: Domain Layer**
- [ ] Port interface created with all required methods
- [ ] Domain entities updated if needed

### **Phase 4: Infrastructure Layer**
- [ ] Service adapter implemented with proper error handling
- [ ] Authentication module created (if needed)
- [ ] Configuration validation added

### **Phase 5: Application Layer**
- [ ] Use cases implemented for all major operations
- [ ] Business logic properly orchestrated
- [ ] Error handling and logging added

### **Phase 6: Presentation Layer**
- [ ] FastAPI routes created with proper documentation
- [ ] Request/response schemas defined
- [ ] Dependency injection configured
- [ ] Routes registered in main application

### **Phase 7: Testing**
- [ ] Unit tests for adapter (80%+ coverage)
- [ ] Integration tests for API routes
- [ ] End-to-end workflow tests
- [ ] All tests passing

### **Phase 8: Documentation & Deployment**
- [ ] SwaggerUI documentation verified
- [ ] Service-specific documentation created
- [ ] Integration tested in development environment
- [ ] Configuration validated

---

## 🔧 **Common Integration Patterns**

### **Authentication Patterns**

#### **API Key Authentication**
```python
def _get_headers(self) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {self.api_key}",
        "X-API-Key": self.api_key
    }
```

#### **OAuth2 Authentication**
```python
async def _get_auth_headers(self) -> Dict[str, str]:
    token = await self.auth_handler.get_access_token()
    return {
        "Authorization": f"Bearer {token}"
    }
```

### **Error Handling Patterns**

#### **HTTP Status Code Mapping**
```python
def _handle_http_error(self, error: httpx.HTTPStatusError) -> Exception:
    status_mappings = {
        400: ValueError("Invalid request parameters"),
        401: AuthenticationError("Invalid API credentials"),
        403: AuthorizationError("Insufficient permissions"),
        404: JobNotFoundError("Job not found"),
        429: RateLimitError("Rate limit exceeded"),
        500: ServiceUnavailableError("Service temporarily unavailable")
    }

    error_class = status_mappings.get(error.response.status_code, Exception)
    return error_class(f"HTTP {error.response.status_code}: {error.response.text}")
```

#### **Retry Logic Pattern**
```python
async def _execute_with_retry(self, operation, max_retries: int = 3):
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt == max_retries:
                raise ServiceUnavailableError(f"Service unavailable after {max_retries} retries")

            wait_time = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait_time)
```

### **File Upload Patterns**

#### **Multipart Form Data**
```python
files = {
    "ligand": (ligand_filename, ligand_content, "chemical/x-pdb"),
    "receptor": (receptor_filename, receptor_content, "chemical/x-pdb")
}

data = {**parameters, "job_type": "molecular_docking"}

response = await client.post(url, files=files, data=data, headers=headers)
```

#### **JSON with Base64 Files**
```python
import base64

payload = {
    "ligand": {
        "filename": ligand_filename,
        "content": base64.b64encode(ligand_content).decode(),
        "content_type": "chemical/x-pdb"
    },
    "parameters": parameters
}

response = await client.post(url, json=payload, headers=headers)
```

---

## 🚀 **Next Steps After Integration**

### **1. Production Readiness**
- [ ] Load testing with realistic job volumes
- [ ] Error monitoring and alerting setup
- [ ] Performance optimization
- [ ] Security review and penetration testing

### **2. Feature Enhancement**
- [ ] Batch job submission capabilities
- [ ] Job cancellation functionality
- [ ] Result caching and optimization
- [ ] Advanced parameter validation

### **3. User Experience**
- [ ] Frontend integration for file uploads
- [ ] Real-time status updates via WebSockets
- [ ] 3D visualization of results
- [ ] Job history and management UI

### **4. Monitoring & Maintenance**
- [ ] Service health checks and uptime monitoring
- [ ] API usage analytics and rate limiting
- [ ] Cost tracking and optimization
- [ ] Regular dependency updates and security patches

---

## 📚 **Resources & References**

### **Internal Documentation**
- [Clean Architecture Guide](../../architecture/system-design/clean-architecture.md)
- [API Development Guide](../../api/contracts/README.md)
- [Testing Workflows](../../development/workflows/testing-workflows.md)
- [Deployment Guide](../../deployment/README.md)

### **External References**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [httpx Client Documentation](https://www.python-httpx.org/)
- [pytest Async Testing](https://pytest-asyncio.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)

### **Example Integrations**
- [NeuroSnap GNINA Integration](../../../src/molecular_analysis_dashboard/presentation/api/routes/docking.py) - Reference implementation
- [Completion Report](../../implementation/phases/phase-4/phase-4b/completion-report.md) - Integration success story

---

**This guide provides a complete, battle-tested approach to service integration based on our successful NeuroSnap GNINA integration. Follow these patterns for consistent, maintainable, and robust service integrations.**
