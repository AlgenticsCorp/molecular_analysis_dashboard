"""API endpoint tests for molecule upload functionality."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io
from uuid import UUID, uuid4
from datetime import datetime

from src.molecular_analysis_dashboard.presentation.api.main import app
from src.molecular_analysis_dashboard.domain.entities.molecule import Molecule


class TestMoleculeUploadAPI:
    """Test molecule upload API endpoints."""

    @pytest.fixture
    def client(self):
        """Test client for API testing."""
        return TestClient(app)

    @pytest.fixture
    def mock_org_id(self):
        """Mock organization ID for testing."""
        return uuid4()

    @pytest.fixture
    def mock_user_id(self):
        """Mock user ID for testing."""
        return uuid4()

    def create_test_molecule(
        self,
        molecule_id: str = "mol-123",
        name: str = "test_molecule.pdb",
        format: str = "pdb",
        uri: str = "/storage/uploads/test-org/molecules/mol-123.pdb",
        org_id: UUID | None = None,
        uploaded_by: UUID | None = None,
        size: int = 1000
    ) -> Molecule:
        """Create a test molecule entity with proper parameters."""
        if org_id is None:
            org_id = uuid4()
        if uploaded_by is None:
            uploaded_by = uuid4()

        return Molecule(
            molecule_id=UUID(molecule_id.replace("mol-", "00000000-0000-0000-0000-000000000")),
            org_id=org_id,
            name=name,
            format=format,
            uri=uri,
            uploaded_by=uploaded_by,
            visibility="private",
            created_at=datetime.now(),
            checksum="test-checksum",
            size_bytes=size
        )

    @pytest.fixture
    def sample_pdb_content(self):
        """Sample PDB file content for testing."""
        return """HEADER    TEST MOLECULE                           01-JAN-24   1ABC
TITLE     TEST MOLECULE FOR UNIT TESTING
ATOM      1  N   ALA A   1      20.154  16.967  14.365  1.00 20.00           N
ATOM      2  CA  ALA A   1      21.155  17.999  14.618  1.00 20.00           C
ATOM      3  C   ALA A   1      22.593  17.506  14.897  1.00 20.00           C
ATOM      4  O   ALA A   1      23.047  16.651  14.154  1.00 20.00           O
ATOM      5  CB  ALA A   1      20.623  18.902  15.739  1.00 20.00           C
END"""

    @pytest.fixture
    def sample_sdf_content(self):
        """Sample SDF file content for testing."""
        return """
  Mrv2311 01012400002D

  4  3  0  0  0  0            999 V2000
   -0.4125    0.7145    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.4125   -0.7145    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.4125   -0.7145    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.4125    0.7145    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
  1  4  1  0  0  0  0
  2  3  1  0  0  0  0
  3  1  1  0  0  0  0
M  END
$$$$
"""

    def test_upload_molecule_pdb_success(self, client, sample_pdb_content):
        """Test successful PDB molecule upload."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.UploadMoleculeUseCase') as mock_use_case:
            # Mock the use case
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = self.create_test_molecule(
                molecule_id="mol-123",
                name="test_molecule.pdb",
                uri="/storage/uploads/test-org/molecules/mol-123.pdb",
                format="pdb",
                size=len(sample_pdb_content.encode())
            )

            # Create file upload
            files = {
                "file": ("test_molecule.pdb", sample_pdb_content, "chemical/x-pdb")
            }

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.post("/api/v1/molecules/upload", files=files)

        assert response.status_code == 201
        data = response.json()
        assert "molecule_id" in data
        assert data["name"] == "test_molecule.pdb"
        assert data["format"] == "pdb"

    def test_upload_molecule_sdf_success(self, client, sample_sdf_content):
        """Test successful SDF molecule upload."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.UploadMoleculeUseCase') as mock_use_case:
            # Mock the use case
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = self.create_test_molecule(
                molecule_id="mol-456",
                name="test_molecule.sdf",
                uri="/storage/uploads/test-org/molecules/mol-456.sdf",
                format="sdf",
                size=len(sample_sdf_content.encode())
            )

            # Create file upload
            files = {
                "file": ("test_molecule.sdf", sample_sdf_content, "chemical/x-mdl-sdfile")
            }

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.post("/api/v1/molecules/upload", files=files)

        assert response.status_code == 201
        data = response.json()
        assert "molecule_id" in data
        assert data["name"] == "test_molecule.sdf"
        assert data["format"] == "sdf"

    def test_upload_molecule_invalid_format(self, client):
        """Test upload with invalid file format."""
        # Create invalid file
        files = {
            "file": ("test.txt", "This is not a molecular file", "text/plain")
        }

        # Mock authentication
        with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
            mock_auth.return_value = "test-org-123"

            response = client.post("/api/v1/molecules/upload", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "Invalid file format" in data["detail"]

    def test_upload_molecule_empty_file(self, client):
        """Test upload with empty file."""
        # Create empty file
        files = {
            "file": ("empty.pdb", "", "chemical/x-pdb")
        }

        # Mock authentication
        with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
            mock_auth.return_value = "test-org-123"

            response = client.post("/api/v1/molecules/upload", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()

    def test_upload_molecule_too_large(self, client):
        """Test upload with file that's too large."""
        # Create large content (simulate file over size limit)
        large_content = "ATOM" + "A" * (10 * 1024 * 1024)  # 10MB+ file

        files = {
            "file": ("large.pdb", large_content, "chemical/x-pdb")
        }

        # Mock authentication
        with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
            mock_auth.return_value = "test-org-123"

            response = client.post("/api/v1/molecules/upload", files=files)

        assert response.status_code == 413
        data = response.json()
        assert "too large" in data["detail"].lower()

    def test_upload_molecule_no_file(self, client):
        """Test upload with no file provided."""
        # Mock authentication
        with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
            mock_auth.return_value = "test-org-123"

            response = client.post("/api/v1/molecules/upload")

        assert response.status_code == 422  # Unprocessable Entity

    def test_upload_molecule_unauthorized(self, client, sample_pdb_content):
        """Test upload without proper authentication."""
        files = {
            "file": ("test_molecule.pdb", sample_pdb_content, "chemical/x-pdb")
        }

        # No authentication mock - should fail
        response = client.post("/api/v1/molecules/upload", files=files)

        assert response.status_code == 401

    def test_upload_molecule_storage_error(self, client, sample_pdb_content):
        """Test upload when storage service is unavailable."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.UploadMoleculeUseCase') as mock_use_case:
            # Mock storage error
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.side_effect = Exception("Storage service unavailable")

            files = {
                "file": ("test_molecule.pdb", sample_pdb_content, "chemical/x-pdb")
            }

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.post("/api/v1/molecules/upload", files=files)

        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"].lower()

    def test_get_molecule_success(self, client):
        """Test successful molecule retrieval."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.GetMoleculeUseCase') as mock_use_case:
            # Mock the use case
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = self.create_test_molecule(
                molecule_id="mol-123",
                name="test_molecule.pdb",
                uri="/storage/uploads/test-org/molecules/mol-123.pdb",
                format="pdb",
                size=1000
            )

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.get("/api/v1/molecules/mol-123")

        assert response.status_code == 200
        data = response.json()
        assert "molecule_id" in data
        assert data["name"] == "test_molecule.pdb"

    def test_get_molecule_not_found(self, client):
        """Test molecule retrieval when molecule doesn't exist."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.GetMoleculeUseCase') as mock_use_case:
            # Mock not found
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = None

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.get("/api/v1/molecules/non-existent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_list_molecules_success(self, client):
        """Test successful molecule listing."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.ListMoleculesUseCase') as mock_use_case:
            # Mock the use case
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = [
                self.create_test_molecule(
                    molecule_id="mol-123",
                    name="molecule1.pdb",
                    uri="/storage/uploads/test-org/molecules/mol-123.pdb",
                    format="pdb",
                    size=1000
                ),
                self.create_test_molecule(
                    molecule_id="mol-456",
                    name="molecule2.sdf",
                    uri="/storage/uploads/test-org/molecules/mol-456.sdf",
                    format="sdf",
                    size=2000
                )
            ]

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.get("/api/v1/molecules/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["molecules"]) == 2
        assert "molecule_id" in data["molecules"][0]
        assert "molecule_id" in data["molecules"][1]

    def test_delete_molecule_success(self, client):
        """Test successful molecule deletion."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.DeleteMoleculeUseCase') as mock_use_case:
            # Mock the use case
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = True

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.delete("/api/v1/molecules/mol-123")

        assert response.status_code == 204

    def test_delete_molecule_not_found(self, client):
        """Test molecule deletion when molecule doesn't exist."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.DeleteMoleculeUseCase') as mock_use_case:
            # Mock not found
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = False

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.delete("/api/v1/molecules/non-existent")

        assert response.status_code == 404


class TestMoleculeDownloadAPI:
    """Test molecule download/access API endpoints."""

    @pytest.fixture
    def client(self):
        """Test client for API testing."""
        return TestClient(app)

    def test_download_molecule_success(self, client):
        """Test successful molecule file download."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.GetMoleculeFileUseCase') as mock_use_case:
            # Mock the use case
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = {
                "content": b"HEADER TEST MOLECULE\nATOM 1 N ALA\nEND",
                "content_type": "chemical/x-pdb",
                "filename": "test_molecule.pdb"
            }

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.get("/api/v1/molecules/mol-123/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "chemical/x-pdb"
        assert "attachment; filename=test_molecule.pdb" in response.headers.get("content-disposition", "")

    def test_get_presigned_url_success(self, client):
        """Test successful presigned URL generation."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.GetPresignedUrlUseCase') as mock_use_case:
            # Mock the use case
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = {
                "url": "http://storage:8080/uploads/test-org/molecules/mol-123.pdb?token=abc123",
                "expires_in": 3600
            }

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.get("/api/v1/molecules/mol-123/presigned-url")

        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["expires_in"] == 3600

    def test_get_molecule_metadata_success(self, client):
        """Test successful molecule metadata retrieval."""
        with patch('src.molecular_analysis_dashboard.use_cases.molecules.GetMoleculeMetadataUseCase') as mock_use_case:
            # Mock the use case
            mock_instance = AsyncMock()
            mock_use_case.return_value = mock_instance
            mock_instance.execute.return_value = {
                "atom_count": 42,
                "molecular_weight": 180.16,
                "formula": "C6H12O6",
                "charge": 0,
                "bonds": 41,
                "rings": 1
            }

            # Mock authentication
            with patch('src.molecular_analysis_dashboard.presentation.api.dependencies.get_current_org') as mock_auth:
                mock_auth.return_value = "test-org-123"

                response = client.get("/api/v1/molecules/mol-123/metadata")

        assert response.status_code == 200
        data = response.json()
        assert data["atom_count"] == 42
        assert data["molecular_weight"] == 180.16
        assert data["formula"] == "C6H12O6"
