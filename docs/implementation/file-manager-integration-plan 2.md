# File Manager Integration Plan

**Status**: Planning Phase  
**Created**: November 14, 2025  
**Last Updated**: November 14, 2025  
**Priority**: High

## Overview

This document outlines the plan to integrate the File Manager frontend component with the backend API, enabling users to upload, manage, preview, and download molecular structure files independently of task executions.

## Current State Analysis

### Existing Frontend (FileManager.tsx)

**Features**:
- 3D molecular viewer integration (3Dmol.js)
- File card display with metadata (name, format, size, upload date)
- Preview dialog with interactive 3D visualization
- Upload, download, delete, and preview actions
- Support for multiple molecular formats: PDB, PDBQT, SDF, MOL2, XYZ

**Current Limitations**:
- Uses static sample data
- No API integration
- No actual file upload functionality
- No database persistence
- No user authentication/authorization

### Existing Backend APIs

#### Available Endpoints ✅

1. **File Download** - `GET /api/v1/tasks-unified/files/{file_id}/download`
   - Streams local files or redirects to external URLs
   - Handles both execution-tied and standalone files
   - Returns proper content headers

2. **Execution Files List** - `GET /api/v1/tasks-unified/executions/{execution_id}/files`
   - Lists files for specific execution
   - Optional `file_type` filter (input/output)
   - Returns metadata with checksums

3. **Upload Receptor** - `POST /api/v1/docking/upload/receptor`
   - Validates and stores PDB files
   - In-memory storage (testing only)
   - Returns file metadata

4. **Upload Ligand** - `POST /api/v1/docking/upload/ligand`
   - Validates and stores SDF files
   - In-memory storage (testing only)
   - Returns file metadata

#### Missing Endpoints ❌

1. **List All Files** - `GET /api/v1/files`
2. **Generic File Upload** - `POST /api/v1/files`
3. **Delete File** - `DELETE /api/v1/files/{file_id}`
4. **Get File Metadata** - `GET /api/v1/files/{file_id}`
5. **Update File Metadata** - `PATCH /api/v1/files/{file_id}`
6. **Bulk Delete** - `POST /api/v1/files/bulk-delete`

### Database Schema

**Current**: `execution_files` table
- Tied to task executions (`execution_id` required)
- Supports input and output files
- Has checksums (MD5, SHA256)
- Storage backend tracking (local, neurosnap_cloud)

**Gap**: No support for standalone files uploaded by users outside of task execution context.

## Requirements

### Functional Requirements

1. **File Upload**
   - Support PDB, PDBQT, SDF, MOL2, XYZ formats
   - Validate file format and structure
   - Store files with metadata (name, description, format, size)
   - Generate checksums for integrity
   - Associate with user (future: multi-user support)

2. **File Listing**
   - Display all user-uploaded files
   - Filter by format, date range, file type
   - Sort by name, date, size
   - Pagination support
   - Search by filename or description

3. **File Management**
   - View file metadata
   - Update file name/description
   - Delete single or multiple files
   - Download files

4. **File Preview**
   - Stream file content for preview
   - 3D visualization for structural files
   - Text preview for small files

5. **Storage Management**
   - Track storage usage per user
   - Enforce storage quotas
   - Clean up orphaned files

### Non-Functional Requirements

1. **Performance**
   - Upload files up to 100MB
   - List 1000+ files efficiently
   - Stream large files without memory issues

2. **Security**
   - Validate file formats to prevent malicious uploads
   - Scan for file size limits
   - Prevent directory traversal attacks
   - User-based access control

3. **Reliability**
   - Atomic file operations (upload/delete)
   - Database transaction consistency
   - Handle partial uploads gracefully

## Architecture Design

### Database Schema Changes

#### Option 1: Extend `execution_files` Table ⭐ RECOMMENDED

```sql
-- Make execution_id nullable to support standalone files
ALTER TABLE execution_files 
  ALTER COLUMN execution_id DROP NOT NULL;

-- Add user ownership and categorization
ALTER TABLE execution_files
  ADD COLUMN user_id UUID REFERENCES users(user_id),
  ADD COLUMN file_category VARCHAR(50) DEFAULT 'standalone',
  ADD COLUMN description TEXT,
  ADD COLUMN tags TEXT[],
  ADD COLUMN is_public BOOLEAN DEFAULT FALSE,
  ADD COLUMN created_by VARCHAR(255),
  ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add index for user queries
CREATE INDEX idx_execution_files_user_id ON execution_files(user_id);
CREATE INDEX idx_execution_files_category ON execution_files(file_category);
CREATE INDEX idx_execution_files_uploaded_at ON execution_files(uploaded_at);

-- Update unique constraint to handle nullable execution_id
ALTER TABLE execution_files
  DROP CONSTRAINT IF EXISTS execution_files_execution_id_parameter_name_file_type_key;

CREATE UNIQUE INDEX idx_execution_files_execution_context 
  ON execution_files(execution_id, parameter_name, file_type) 
  WHERE execution_id IS NOT NULL;

CREATE UNIQUE INDEX idx_execution_files_standalone 
  ON execution_files(file_id) 
  WHERE execution_id IS NULL;
```

**Benefits**:
- Reuse existing file service infrastructure
- Consistent file handling logic
- Single source of truth for all files
- Easier to associate uploaded files with future executions

#### Option 2: Create Separate `user_files` Table

```sql
CREATE TABLE user_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    file_category VARCHAR(50) DEFAULT 'molecular_structure',
    description TEXT,
    tags TEXT[],
    size_bytes BIGINT NOT NULL,
    content_type VARCHAR(100),
    storage_backend VARCHAR(50) DEFAULT 'local',
    storage_path TEXT NOT NULL,
    md5_hash VARCHAR(32),
    sha256_hash VARCHAR(64),
    is_public BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_user_files_user_id ON user_files(user_id);
CREATE INDEX idx_user_files_format ON user_files(file_format);
CREATE INDEX idx_user_files_uploaded_at ON user_files(uploaded_at);
```

**Benefits**:
- Clean separation of concerns
- Easier to add user-specific features
- No risk of breaking execution file logic

**Drawbacks**:
- Duplicate file handling code
- Two sources of truth for files
- More complex queries when joining execution and user files

### API Design

#### Base Router: `/api/v1/files`

All file management endpoints will use this base path.

#### Endpoints Specification

##### 1. Upload File

```
POST /api/v1/files
Content-Type: multipart/form-data

Request:
- file: File (required) - The molecular structure file
- name: string (optional) - Custom file name
- description: string (optional) - File description
- tags: string[] (optional) - Tags for categorization
- category: string (optional) - File category (default: 'molecular_structure')

Response: 201 Created
{
  "file_id": "uuid",
  "filename": "protein_structure.pdb",
  "original_filename": "1abc.pdb",
  "file_format": "pdb",
  "size_bytes": 1234567,
  "content_type": "chemical/x-pdb",
  "storage_backend": "local",
  "storage_path": "/uploads/user/{user_id}/{file_id}.pdb",
  "md5_hash": "abc123...",
  "sha256_hash": "def456...",
  "validation_info": {
    "is_valid": true,
    "atom_count": 1523,
    "has_coordinates": true
  },
  "uploaded_at": "2025-11-14T10:30:00Z",
  "created_by": "user@example.com"
}

Errors:
- 400: Invalid file format or validation failed
- 413: File too large
- 507: Insufficient storage quota
```

##### 2. List Files

```
GET /api/v1/files?format={format}&category={category}&search={query}&sort_by={field}&order={asc|desc}&page={page}&limit={limit}

Query Parameters:
- format: string (optional) - Filter by format (pdb, sdf, pdbqt, mol2, xyz)
- category: string (optional) - Filter by category
- search: string (optional) - Search in filename or description
- tags: string[] (optional) - Filter by tags
- sort_by: string (optional) - Sort field (name, size, uploaded_at) default: uploaded_at
- order: string (optional) - Sort order (asc, desc) default: desc
- page: int (optional) - Page number (default: 1)
- limit: int (optional) - Items per page (default: 50, max: 200)

Response: 200 OK
{
  "total_files": 125,
  "page": 1,
  "limit": 50,
  "total_pages": 3,
  "files": [
    {
      "file_id": "uuid",
      "filename": "protein_structure.pdb",
      "file_format": "pdb",
      "category": "molecular_structure",
      "description": "EGFR kinase domain structure",
      "tags": ["egfr", "kinase", "receptor"],
      "size_bytes": 1234567,
      "uploaded_at": "2025-11-14T10:30:00Z",
      "storage_backend": "local",
      "download_url": "/api/v1/files/{file_id}/download"
    },
    ...
  ]
}
```

##### 3. Get File Metadata

```
GET /api/v1/files/{file_id}

Response: 200 OK
{
  "file_id": "uuid",
  "filename": "protein_structure.pdb",
  "original_filename": "1abc.pdb",
  "file_format": "pdb",
  "category": "molecular_structure",
  "description": "EGFR kinase domain structure",
  "tags": ["egfr", "kinase", "receptor"],
  "size_bytes": 1234567,
  "content_type": "chemical/x-pdb",
  "storage_backend": "local",
  "storage_path": "/uploads/user/{user_id}/{file_id}.pdb",
  "md5_hash": "abc123...",
  "sha256_hash": "def456...",
  "uploaded_at": "2025-11-14T10:30:00Z",
  "updated_at": "2025-11-14T10:30:00Z",
  "created_by": "user@example.com",
  "download_url": "/api/v1/files/{file_id}/download"
}

Errors:
- 404: File not found
- 403: Access denied
```

##### 4. Update File Metadata

```
PATCH /api/v1/files/{file_id}

Request:
{
  "filename": "updated_name.pdb",
  "description": "Updated description",
  "tags": ["new", "tags"]
}

Response: 200 OK
{
  "file_id": "uuid",
  "filename": "updated_name.pdb",
  "description": "Updated description",
  "tags": ["new", "tags"],
  "updated_at": "2025-11-14T11:00:00Z"
}

Errors:
- 404: File not found
- 403: Access denied
- 400: Invalid update data
```

##### 5. Delete File

```
DELETE /api/v1/files/{file_id}

Response: 204 No Content

Errors:
- 404: File not found
- 403: Access denied
- 409: File is in use (referenced by active executions)
```

##### 6. Bulk Delete

```
POST /api/v1/files/bulk-delete

Request:
{
  "file_ids": ["uuid1", "uuid2", "uuid3"]
}

Response: 200 OK
{
  "deleted": 2,
  "failed": 1,
  "errors": [
    {
      "file_id": "uuid3",
      "reason": "File is in use by active execution"
    }
  ]
}
```

##### 7. Download File (Existing - No Changes)

```
GET /api/v1/files/{file_id}/download

Response: 200 OK (StreamingResponse or RedirectResponse)
Content-Type: {file content type}
Content-Disposition: attachment; filename="{filename}"
```

##### 8. Preview File Content

```
GET /api/v1/files/{file_id}/preview?lines={lines}

Query Parameters:
- lines: int (optional) - Number of lines to return (default: 100, max: 1000)

Response: 200 OK
{
  "file_id": "uuid",
  "filename": "protein.pdb",
  "file_format": "pdb",
  "preview_content": "ATOM      1  N   ALA A   1...",
  "total_lines": 15234,
  "preview_lines": 100,
  "is_truncated": true
}

Errors:
- 404: File not found
- 403: Access denied
- 415: Preview not supported for binary files
```

##### 9. Get Storage Statistics

```
GET /api/v1/files/stats

Response: 200 OK
{
  "total_files": 125,
  "total_size_bytes": 523456789,
  "total_size_formatted": "499.2 MB",
  "quota_bytes": 10737418240,
  "quota_formatted": "10.0 GB",
  "quota_used_percentage": 4.87,
  "files_by_format": {
    "pdb": 45,
    "sdf": 38,
    "pdbqt": 22,
    "mol2": 15,
    "xyz": 5
  },
  "storage_by_format": {
    "pdb": 345678901,
    "sdf": 123456789,
    ...
  }
}
```

### Service Layer Architecture

#### New Service: `UserFileService`

```python
# src/molecular_analysis_dashboard/services/user_file_service.py

from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
import hashlib
import magic
from fastapi import UploadFile

class UserFileService:
    """Service for managing user-uploaded files independently of task executions."""
    
    SUPPORTED_FORMATS = {
        'pdb': 'chemical/x-pdb',
        'pdbqt': 'chemical/x-pdbqt',
        'sdf': 'chemical/x-mdl-sdfile',
        'mol2': 'chemical/x-mol2',
        'xyz': 'chemical/x-xyz'
    }
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    STORAGE_BASE_PATH = Path("/storage/uploads/user")
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: Optional[UUID] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: str = "molecular_structure"
    ) -> Dict[str, Any]:
        """Upload and validate a molecular structure file."""
        
    async def list_files(
        self,
        user_id: Optional[UUID] = None,
        file_format: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "uploaded_at",
        order: str = "desc",
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List files with filtering, sorting, and pagination."""
        
    async def get_file_metadata(
        self,
        file_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get detailed metadata for a specific file."""
        
    async def update_file_metadata(
        self,
        file_id: UUID,
        user_id: Optional[UUID] = None,
        filename: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update file metadata (not the file content)."""
        
    async def delete_file(
        self,
        file_id: UUID,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Delete a file and its database record."""
        
    async def bulk_delete(
        self,
        file_ids: List[UUID],
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Delete multiple files in a single operation."""
        
    async def get_preview_content(
        self,
        file_id: UUID,
        user_id: Optional[UUID] = None,
        lines: int = 100
    ) -> Dict[str, Any]:
        """Get preview of file content for text-based formats."""
        
    async def get_storage_stats(
        self,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get storage usage statistics."""
        
    async def validate_file_format(
        self,
        content: bytes,
        file_format: str
    ) -> Dict[str, Any]:
        """Validate file format and structure."""
        
    def _calculate_checksums(self, content: bytes) -> Dict[str, str]:
        """Calculate MD5 and SHA256 checksums."""
        return {
            "md5": hashlib.md5(content).hexdigest(),
            "sha256": hashlib.sha256(content).hexdigest()
        }
```

#### File Validators

```python
# src/molecular_analysis_dashboard/services/file_validators.py

class PDBValidator:
    """Validate PDB (Protein Data Bank) format files."""
    
    @staticmethod
    def validate(content: bytes) -> Dict[str, Any]:
        """Validate PDB file structure."""
        content_str = content.decode("utf-8")
        lines = content_str.split("\n")
        
        atom_count = sum(1 for line in lines if line.startswith("ATOM"))
        hetatm_count = sum(1 for line in lines if line.startswith("HETATM"))
        has_coordinates = any("ATOM" in line and len(line.split()) >= 8 for line in lines[:100])
        has_header = any(line.startswith("HEADER") for line in lines[:50])
        
        return {
            "is_valid": atom_count > 0 and has_coordinates,
            "atom_count": atom_count,
            "hetatm_count": hetatm_count,
            "has_coordinates": has_coordinates,
            "has_header": has_header,
            "format": "pdb"
        }

class SDFValidator:
    """Validate SDF (Structure Data File) format files."""
    
    @staticmethod
    def validate(content: bytes) -> Dict[str, Any]:
        """Validate SDF file structure."""
        content_str = content.decode("utf-8")
        
        has_mol_block = "$$$$" in content_str
        lines = content_str.split("\n")
        
        # Check counts line (line 4 in SDF)
        has_atom_count = False
        if len(lines) > 3:
            counts_line = lines[3].strip()
            if counts_line and counts_line.split()[0].isdigit():
                has_atom_count = True
        
        molecule_count = content_str.count("$$$$")
        
        return {
            "is_valid": has_mol_block and has_atom_count,
            "has_mol_block": has_mol_block,
            "has_atom_count": has_atom_count,
            "molecule_count": molecule_count,
            "format": "sdf"
        }

# Similar validators for PDBQT, MOL2, XYZ...
```

## Implementation Plan

### Phase 1: Core File Management (Sprint 1 - Week 1)

**Priority**: HIGH

#### Tasks:

1. **Database Migration** (2 days)
   - [ ] Create migration script to extend `execution_files` table
   - [ ] Add user_id, description, tags columns
   - [ ] Make execution_id nullable
   - [ ] Update unique constraints and indexes
   - [ ] Test migration on development database
   - [ ] Document rollback procedure

2. **Backend - File Upload API** (3 days)
   - [ ] Create `UserFileService` class
   - [ ] Implement file validators (PDB, SDF, PDBQT, MOL2, XYZ)
   - [ ] Create `POST /api/v1/files` endpoint
   - [ ] Add file format detection
   - [ ] Implement checksum calculation
   - [ ] Add file size validation
   - [ ] Create unit tests for validators
   - [ ] Create integration tests for upload endpoint

3. **Backend - File Listing API** (2 days)
   - [ ] Implement `list_files()` in UserFileService
   - [ ] Create `GET /api/v1/files` endpoint
   - [ ] Add filtering by format, category, search
   - [ ] Implement pagination
   - [ ] Add sorting capabilities
   - [ ] Create unit tests
   - [ ] Create integration tests

4. **Backend - File Delete API** (1 day)
   - [ ] Implement `delete_file()` in UserFileService
   - [ ] Create `DELETE /api/v1/files/{file_id}` endpoint
   - [ ] Add check for files in use by executions
   - [ ] Implement physical file deletion
   - [ ] Create unit tests
   - [ ] Create integration tests

5. **Frontend - API Integration** (2 days)
   - [ ] Create `fileManagerApi.ts` service
   - [ ] Implement `uploadFile()` function
   - [ ] Implement `listFiles()` function
   - [ ] Implement `deleteFile()` function
   - [ ] Add error handling
   - [ ] Update FileManager.tsx to use APIs
   - [ ] Remove sample data
   - [ ] Add loading states
   - [ ] Add error messages

**Deliverables**:
- Working file upload with validation
- File listing with filters
- File deletion
- Updated FileManager UI connected to backend

**Success Criteria**:
- ✅ Users can upload PDB, SDF files
- ✅ Files appear in file manager list
- ✅ Users can filter and search files
- ✅ Users can delete files
- ✅ All tests passing
- ✅ No memory leaks with large files

### Phase 2: Enhanced Features (Sprint 2 - Week 2)

**Priority**: MEDIUM

#### Tasks:

1. **File Metadata Management** (2 days)
   - [ ] Create `GET /api/v1/files/{file_id}` endpoint
   - [ ] Create `PATCH /api/v1/files/{file_id}` endpoint
   - [ ] Add file tagging support
   - [ ] Implement description editing
   - [ ] Create frontend editing dialog
   - [ ] Add validation for metadata updates

2. **File Preview** (3 days)
   - [ ] Create `GET /api/v1/files/{file_id}/preview` endpoint
   - [ ] Implement streaming for large files
   - [ ] Add line limit parameter
   - [ ] Update frontend to use preview API
   - [ ] Optimize 3D viewer loading
   - [ ] Add preview for non-visual formats (text display)

3. **Bulk Operations** (2 days)
   - [ ] Create `POST /api/v1/files/bulk-delete` endpoint
   - [ ] Add multi-select in frontend
   - [ ] Implement bulk download (ZIP archive)
   - [ ] Add progress indicators
   - [ ] Implement error handling for partial failures

4. **Storage Statistics** (1 day)
   - [ ] Create `GET /api/v1/files/stats` endpoint
   - [ ] Calculate total storage usage
   - [ ] Group by file format
   - [ ] Add storage quota visualization in frontend
   - [ ] Display usage warnings

**Deliverables**:
- Metadata editing capability
- File preview without full download
- Bulk file operations
- Storage usage dashboard

**Success Criteria**:
- ✅ Users can edit file metadata
- ✅ Preview works for all supported formats
- ✅ Bulk delete handles 100+ files
- ✅ Storage stats accurate and fast

### Phase 3: Advanced Features (Sprint 3 - Week 3)

**Priority**: LOW

#### Tasks:

1. **Multi-Format Support** (3 days)
   - [ ] Add PDBQT validator
   - [ ] Add MOL2 validator
   - [ ] Add XYZ validator
   - [ ] Test 3D viewer with all formats
   - [ ] Add format conversion API (optional)

2. **File Sharing** (2 days)
   - [ ] Add `is_public` flag support
   - [ ] Create sharing link generation
   - [ ] Add access control checks
   - [ ] Implement shared file viewer

3. **Storage Optimization** (2 days)
   - [ ] Implement file deduplication (same hash)
   - [ ] Add automatic cleanup of orphaned files
   - [ ] Implement storage quota enforcement
   - [ ] Add compression for large files

4. **Enhanced Search** (1 day)
   - [ ] Add full-text search in descriptions
   - [ ] Implement tag-based filtering
   - [ ] Add date range filters
   - [ ] Add saved search filters

**Deliverables**:
- Full multi-format support
- File sharing capabilities
- Optimized storage
- Advanced search

**Success Criteria**:
- ✅ All 5 formats supported
- ✅ Public file sharing works
- ✅ Storage deduplication saves space
- ✅ Search returns relevant results fast

## Testing Strategy

### Unit Tests

```python
# tests/unit/services/test_user_file_service.py

async def test_upload_pdb_file():
    """Test PDB file upload with validation."""
    
async def test_upload_invalid_format():
    """Test rejection of unsupported format."""
    
async def test_list_files_with_filters():
    """Test file listing with format filter."""
    
async def test_delete_file_in_use():
    """Test prevention of deleting file in active execution."""
```

### Integration Tests

```python
# tests/integration/api/test_files_api.py

async def test_upload_download_cycle():
    """Test complete upload and download workflow."""
    
async def test_concurrent_uploads():
    """Test handling of simultaneous file uploads."""
    
async def test_large_file_streaming():
    """Test streaming of 100MB file."""
```

### Frontend Tests

```typescript
// frontend/src/pages/__tests__/FileManager.test.tsx

describe('FileManager', () => {
  it('uploads file successfully', async () => {
    // Test file upload
  });
  
  it('displays uploaded files', async () => {
    // Test file listing
  });
  
  it('deletes file on confirmation', async () => {
    // Test file deletion
  });
});
```

## Security Considerations

### File Upload Security

1. **Format Validation**
   - Verify magic bytes, not just extensions
   - Parse and validate file structure
   - Reject files with malicious content

2. **Size Limits**
   - Enforce max file size (100MB)
   - Stream large files to avoid memory issues
   - Monitor upload rates to prevent abuse

3. **Storage Security**
   - Generate random file IDs (UUIDs)
   - Store files outside web root
   - Prevent directory traversal attacks
   - Set proper file permissions (0644)

4. **Access Control**
   - Verify user ownership before operations
   - Check permissions for shared files
   - Log all file operations for audit

### API Security

1. **Authentication**
   - Require authentication for all endpoints
   - Use JWT tokens or session cookies
   - Implement rate limiting

2. **Authorization**
   - Verify user owns file before access
   - Check permissions for shared files
   - Prevent unauthorized deletion

3. **Input Validation**
   - Sanitize all user inputs
   - Validate file metadata
   - Prevent SQL injection in search queries

## Performance Optimization

### Database Optimization

1. **Indexes**
   - Index on user_id for fast user queries
   - Index on uploaded_at for date sorting
   - Index on file_format for format filtering
   - Composite index on (user_id, uploaded_at)

2. **Query Optimization**
   - Use pagination to limit result sets
   - Implement efficient counting queries
   - Cache frequently accessed metadata

### File Storage Optimization

1. **Streaming**
   - Stream large files instead of loading in memory
   - Use chunked uploads for large files
   - Implement resumable uploads

2. **Caching**
   - Cache file metadata in Redis
   - Cache preview content
   - Use CDN for static content

3. **Deduplication**
   - Check SHA256 before storing
   - Use hard links for duplicate files
   - Track reference counts

## Migration Strategy

### Phase 1: Database Migration

```bash
# Run migration
cd database
alembic revision --autogenerate -m "Add user file management support"
alembic upgrade head

# Verify migration
psql -d mad -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'execution_files';"
```

### Phase 2: Backend Deployment

```bash
# Build new API container
docker-compose build --no-cache api

# Deploy with zero downtime
docker-compose up -d --no-deps api

# Verify health
curl http://localhost/api/v1/health
```

### Phase 3: Frontend Deployment

```bash
# Build frontend
cd frontend
npm run build

# Deploy
docker-compose build --no-cache frontend
docker-compose up -d --no-deps frontend
```

## Rollback Plan

### Database Rollback

```bash
# Revert migration
cd database
alembic downgrade -1

# Verify
psql -d mad -c "\d execution_files"
```

### Application Rollback

```bash
# Revert to previous version
git checkout <previous-commit>
docker-compose build --no-cache api frontend
docker-compose up -d
```

## Monitoring and Metrics

### Key Metrics

1. **Upload Metrics**
   - Upload success rate
   - Average upload time
   - Upload errors by type
   - File size distribution

2. **Storage Metrics**
   - Total storage used
   - Storage by user
   - Storage by format
   - Growth rate

3. **Performance Metrics**
   - API response times
   - File listing query time
   - Download bandwidth usage
   - 95th percentile latency

### Alerts

1. **Storage Alerts**
   - Storage usage > 90%
   - Individual user > quota
   - Orphaned files detected

2. **Performance Alerts**
   - API response time > 2s
   - Upload failure rate > 5%
   - Database query time > 1s

## Documentation

### API Documentation

- Update OpenAPI/Swagger specs
- Add request/response examples
- Document error codes
- Add authentication requirements

### User Documentation

- File upload guide
- Supported formats reference
- Storage quota information
- Troubleshooting guide

### Developer Documentation

- Service architecture overview
- Database schema documentation
- Testing guidelines
- Deployment procedures

## Success Metrics

### Phase 1 Success Criteria

- [ ] 100% of core endpoints implemented
- [ ] 90%+ test coverage
- [ ] Upload works for 10MB+ files
- [ ] List 1000 files in < 500ms
- [ ] Zero SQL injection vulnerabilities
- [ ] Zero directory traversal vulnerabilities

### Phase 2 Success Criteria

- [ ] Preview works for all formats
- [ ] Bulk delete handles 100+ files
- [ ] Storage stats update in real-time
- [ ] Metadata updates in < 200ms

### Phase 3 Success Criteria

- [ ] All 5 formats fully supported
- [ ] File sharing works securely
- [ ] Deduplication saves 20%+ storage
- [ ] Search returns results in < 300ms

## Timeline

| Phase | Duration | Start Date | End Date |
|-------|----------|------------|----------|
| Phase 1: Core Features | 1 week | Nov 18, 2025 | Nov 22, 2025 |
| Phase 2: Enhanced Features | 1 week | Nov 25, 2025 | Nov 29, 2025 |
| Phase 3: Advanced Features | 1 week | Dec 2, 2025 | Dec 6, 2025 |
| Testing & Bug Fixes | 3 days | Dec 9, 2025 | Dec 11, 2025 |
| Documentation | 2 days | Dec 12, 2025 | Dec 13, 2025 |

**Total Duration**: ~3.5 weeks

## Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Large file uploads crash API | High | Medium | Implement streaming, memory limits |
| Storage fills up quickly | High | High | Add quota enforcement, cleanup jobs |
| File validation bypass | High | Low | Multi-layer validation, security review |
| Database migration fails | High | Low | Test on staging, backup before migration |
| Performance degradation | Medium | Medium | Load testing, query optimization |
| User data loss | High | Low | Backup strategy, transaction safety |

## Next Steps

1. **Immediate** (This Week)
   - Review and approve this plan
   - Set up development environment
   - Create feature branch: `feature/file-manager`
   - Begin database migration script

2. **Week 1** (Nov 18-22)
   - Implement Phase 1 tasks
   - Daily standups to track progress
   - Code reviews for all PRs

3. **Week 2** (Nov 25-29)
   - Implement Phase 2 tasks
   - Begin user acceptance testing
   - Performance testing

4. **Week 3** (Dec 2-6)
   - Implement Phase 3 tasks
   - Security audit
   - Final testing

## Conclusion

This integration plan provides a comprehensive roadmap for implementing a fully-functional File Manager system. The phased approach allows for incremental delivery of value while maintaining code quality and security standards.

The plan prioritizes core functionality first (upload, list, delete) to deliver immediate value, followed by enhanced features (preview, bulk operations) and advanced capabilities (multi-format, sharing).

By following this plan, we will deliver a robust, secure, and performant file management system that integrates seamlessly with the existing molecular analysis dashboard.
