"""Unit tests for file storage adapter functionality."""

import pytest
import tempfile
import shutil
from pathlib import Path
from uuid import UUID, uuid4
from io import BytesIO
import hashlib

from molecular_analysis_dashboard.adapters.storage.file_storage import FileStorageAdapter
from molecular_analysis_dashboard.ports.storage import StorageError


class TestFileStorageAdapter:
    """Test suite for FileStorageAdapter."""

    @pytest.fixture
    def temp_storage_root(self):
        """Create temporary storage root for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def storage_adapter(self, temp_storage_root):
        """Create storage adapter instance with temporary storage."""
        return FileStorageAdapter(storage_root=temp_storage_root)

    @pytest.fixture
    def sample_org_id(self):
        """Sample organization ID for testing."""
        return UUID("12345678-1234-5678-1234-123456789012")

    @pytest.fixture
    def sample_pdb_content(self):
        """Sample PDB file content for testing."""
        return b"""HEADER    TRANSFERASE/DNA                         20-MAY-93   1HTM
TITLE     CATABOLITE GENE ACTIVATOR PROTEIN COMPLEXED WITH DNA
COMPND    MOL_ID: 1;
COMPND   2 MOLECULE: CATABOLITE GENE ACTIVATOR PROTEIN;
COMPND   3 CHAIN: A, C;
ATOM      1  N   ALA A   1      20.154  16.967  17.286  1.00 11.18           N
ATOM      2  CA  ALA A   1      19.030  16.251  17.889  1.00 10.38           C
ATOM      3  C   ALA A   1      18.042  17.114  18.618  1.00  9.89           C
END"""

    def test_storage_adapter_initialization(self, temp_storage_root):
        """Test storage adapter initialization creates required directories."""
        adapter = FileStorageAdapter(storage_root=temp_storage_root)

        assert adapter.storage_root == Path(temp_storage_root)
        assert adapter.uploads_dir.exists()
        assert adapter.results_dir.exists()
        assert adapter.temp_dir.exists()

    def test_validate_file_type_supported_formats(self, storage_adapter):
        """Test file type validation for supported molecular formats."""
        supported_cases = [
            ("test.pdb", "chemical/x-pdb"),
            ("molecule.sdf", "chemical/x-sdf"),
            ("compound.mol2", "chemical/x-mol2"),
            ("structure.xyz", "chemical/x-xyz"),
            ("crystal.cif", "chemical/x-cif"),
            ("protein.pdbqt", "text/plain"),
            ("data.smiles", "chemical/x-smiles"),
        ]

        for filename, content_type in supported_cases:
            assert storage_adapter.validate_file_type(filename, content_type) is True

    def test_validate_file_type_unsupported_formats(self, storage_adapter):
        """Test file type validation rejects unsupported formats."""
        unsupported_cases = [
            ("document.pdf", "application/pdf"),
            ("image.png", "image/png"),
            ("script.py", "text/x-python"),
            ("archive.zip", "application/zip"),
            ("text.txt", "text/plain"),  # txt is not supported even with text/plain
        ]

        for filename, content_type in unsupported_cases:
            assert storage_adapter.validate_file_type(filename, content_type) is False

    @pytest.mark.asyncio
    async def test_store_file_success(self, storage_adapter, sample_org_id, sample_pdb_content):
        """Test successful file storage."""
        file_content = BytesIO(sample_pdb_content)

        storage_uri = await storage_adapter.store_file(
            file_content=file_content,
            file_name="test_protein.pdb",
            content_type="chemical/x-pdb",
            organization_id=sample_org_id
        )

        # Verify URI format
        assert storage_uri.startswith("storage://")
        assert "uploads" in storage_uri
        assert str(sample_org_id) in storage_uri

        # Verify file exists on disk
        file_path = storage_adapter._uri_to_path(storage_uri)
        assert file_path.exists()

        # Verify file content
        with open(file_path, 'rb') as f:
            stored_content = f.read()
        assert stored_content == sample_pdb_content

    @pytest.mark.asyncio
    async def test_store_file_deduplication(self, storage_adapter, sample_org_id, sample_pdb_content):
        """Test file deduplication based on content hash."""
        file_content1 = BytesIO(sample_pdb_content)
        file_content2 = BytesIO(sample_pdb_content)

        # Store same content twice
        uri1 = await storage_adapter.store_file(
            file_content=file_content1,
            file_name="protein1.pdb",
            content_type="chemical/x-pdb",
            organization_id=sample_org_id
        )

        uri2 = await storage_adapter.store_file(
            file_content=file_content2,
            file_name="protein2.pdb",
            content_type="chemical/x-pdb",
            organization_id=sample_org_id
        )

        # Should return same URI for identical content
        assert uri1 == uri2

    @pytest.mark.asyncio
    async def test_store_file_invalid_type(self, storage_adapter, sample_org_id):
        """Test file storage fails for invalid file types."""
        invalid_content = BytesIO(b"not a molecular file")

        with pytest.raises(StorageError, match="Unsupported file type"):
            await storage_adapter.store_file(
                file_content=invalid_content,
                file_name="invalid.txt",
                content_type="text/plain",
                organization_id=sample_org_id
            )

    @pytest.mark.asyncio
    async def test_retrieve_file_success(self, storage_adapter, sample_org_id, sample_pdb_content):
        """Test successful file retrieval."""
        # First store a file
        file_content = BytesIO(sample_pdb_content)
        storage_uri = await storage_adapter.store_file(
            file_content=file_content,
            file_name="test.pdb",
            content_type="chemical/x-pdb",
            organization_id=sample_org_id
        )

        # Then retrieve it
        retrieved_file = await storage_adapter.retrieve_file(storage_uri)

        assert retrieved_file is not None
        retrieved_content = retrieved_file.read()
        retrieved_file.close()

        assert retrieved_content == sample_pdb_content

    @pytest.mark.asyncio
    async def test_retrieve_file_not_found(self, storage_adapter):
        """Test file retrieval returns None for missing files."""
        non_existent_uri = "storage://uploads/nonexistent/file.pdb"

        result = await storage_adapter.retrieve_file(non_existent_uri)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage_adapter, sample_org_id, sample_pdb_content):
        """Test successful file deletion."""
        # Store a file
        file_content = BytesIO(sample_pdb_content)
        storage_uri = await storage_adapter.store_file(
            file_content=file_content,
            file_name="to_delete.pdb",
            content_type="chemical/x-pdb",
            organization_id=sample_org_id
        )

        # Verify file exists
        file_path = storage_adapter._uri_to_path(storage_uri)
        assert file_path.exists()

        # Delete file
        result = await storage_adapter.delete_file(storage_uri)
        assert result is True

        # Verify file is gone
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, storage_adapter):
        """Test file deletion returns False for missing files."""
        non_existent_uri = "storage://uploads/nonexistent/file.pdb"

        result = await storage_adapter.delete_file(non_existent_uri)
        assert result is False

    @pytest.mark.asyncio
    async def test_generate_presigned_url(self, storage_adapter, sample_org_id, sample_pdb_content):
        """Test presigned URL generation."""
        # Store a file
        file_content = BytesIO(sample_pdb_content)
        storage_uri = await storage_adapter.store_file(
            file_content=file_content,
            file_name="for_url.pdb",
            content_type="chemical/x-pdb",
            organization_id=sample_org_id
        )

        # Generate presigned URL
        presigned_url = await storage_adapter.generate_presigned_url(storage_uri)

        assert presigned_url is not None
        assert presigned_url.startswith("http://storage:8080/")
        assert "uploads" in presigned_url

    @pytest.mark.asyncio
    async def test_generate_presigned_url_not_found(self, storage_adapter):
        """Test presigned URL generation returns None for missing files."""
        non_existent_uri = "storage://uploads/nonexistent/file.pdb"

        result = await storage_adapter.generate_presigned_url(non_existent_uri)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_file_info(self, storage_adapter, sample_org_id, sample_pdb_content):
        """Test file metadata retrieval."""
        # Store a file
        file_content = BytesIO(sample_pdb_content)
        storage_uri = await storage_adapter.store_file(
            file_content=file_content,
            file_name="metadata_test.pdb",
            content_type="chemical/x-pdb",
            organization_id=sample_org_id
        )

        # Get file info
        file_info = await storage_adapter.get_file_info(storage_uri)

        assert file_info is not None
        assert file_info["uri"] == storage_uri
        assert file_info["size"] == len(sample_pdb_content)
        assert file_info["extension"] == ".pdb"
        assert "created_at" in file_info
        assert "modified_at" in file_info

    @pytest.mark.asyncio
    async def test_get_file_info_not_found(self, storage_adapter):
        """Test file info returns None for missing files."""
        non_existent_uri = "storage://uploads/nonexistent/file.pdb"

        result = await storage_adapter.get_file_info(non_existent_uri)
        assert result is None

    def test_uri_to_path_conversion(self, storage_adapter):
        """Test storage URI to file path conversion."""
        test_uri = "storage://uploads/org-id/file.pdb"
        expected_path = storage_adapter.storage_root / "uploads/org-id/file.pdb"

        result_path = storage_adapter._uri_to_path(test_uri)
        assert result_path == expected_path

    def test_uri_to_path_invalid_format(self, storage_adapter):
        """Test URI conversion fails for invalid URI format."""
        invalid_uri = "http://example.com/file.pdb"

        with pytest.raises(StorageError, match="Invalid storage URI format"):
            storage_adapter._uri_to_path(invalid_uri)

    @pytest.mark.asyncio
    async def test_content_hash_calculation(self, storage_adapter, sample_pdb_content):
        """Test content hash calculation."""
        file_content = BytesIO(sample_pdb_content)

        calculated_hash = await storage_adapter._calculate_hash(file_content)
        expected_hash = hashlib.sha256(sample_pdb_content).hexdigest()

        assert calculated_hash == expected_hash
        # Verify file pointer is reset
        assert file_content.tell() == 0

    def test_generate_file_path_organization_isolation(self, storage_adapter):
        """Test file path generation creates organization-specific directories."""
        org_id1 = UUID("11111111-1111-1111-1111-111111111111")
        org_id2 = UUID("22222222-2222-2222-2222-222222222222")

        path1 = storage_adapter._generate_file_path("test.pdb", org_id1, "hash123")
        path2 = storage_adapter._generate_file_path("test.pdb", org_id2, "hash123")

        assert str(org_id1) in str(path1)
        assert str(org_id2) in str(path2)
        assert path1 != path2
