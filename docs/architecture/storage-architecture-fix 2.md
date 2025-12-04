# Storage Architecture Fix: File Storage & Parameter Types

## 🔴 Critical Issues Identified

### Issue 1: Base64 Encoding Files in Database (CURRENT BAD PRACTICE)

**Current Implementation** (`unified_task_service.py` lines 275-283):
```python
# ❌ WRONG: Storing entire file content as base64 in JSONB
input_data[key] = {
    'filename': file_info['filename'],
    'content_type': file_info.get('content_type'),
    'size': len(content),
    'content_base64': base64.b64encode(content).decode('utf-8')  # ❌ BAD!
}
```

**Problems:**
- ❌ Database bloat (PDB files: 100KB-10MB, SDF files: 10KB-5MB stored in `task_framework_executions.input_data` JSONB)
- ❌ Query performance degradation (JSONB with MB of base64 data)
- ❌ Memory consumption when loading execution history
- ❌ No streaming capability for large files
- ❌ PostgreSQL JSONB has practical limits (~1GB per field, but performs poorly >1MB)
- ❌ Duplicated storage (same file uploaded multiple times = multiple copies)

**Impact:**
- Production database will grow **exponentially** with each execution
- Loading `/executions` endpoint will become **slow** as history grows
- Cannot support large files (>10MB protein complexes, trajectory files)

---

### Issue 2: No Differentiation Between File and String Parameters

**Current Problem:**
- Task definitions support BOTH file parameters (`receptor_file`, `ligand_file`) AND string parameters (`job_name`, `note`)
- But `input_data` JSONB stores them the same way
- No type safety or validation based on parameter type
- Frontend can't dynamically render correct input fields

**Example from GNINA Task:**
```json
{
  "properties": {
    "receptor_file": { "type": "string", "format": "binary" },  // FILE
    "ligand_file": { "type": "string", "format": "binary" },   // FILE
    "job_name": { "type": "string" },                           // STRING
    "note": { "type": "string" }                                // STRING
  }
}
```

---

## ✅ Correct Architecture: Hybrid Storage Model

### Principle: **Separate File Storage from Metadata**

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXECUTION INPUT DATA                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. String/Number Parameters → Database JSONB                  │
│     ├─ job_name: "EGFR_docking"                               │
│     ├─ note: "Test run with erlotinib"                        │
│     └─ exhaustiveness: 8                                       │
│                                                                 │
│  2. File Parameters → Storage Service (nginx/S3)               │
│     ├─ receptor_file → /storage/uploads/{org_id}/{exec_id}/    │
│     │                  receptor.pdb                            │
│     ├─ ligand_file → /storage/uploads/{org_id}/{exec_id}/      │
│     │                ligand.sdf                                │
│     └─ Database stores ONLY metadata:                          │
│         {                                                      │
│           "filename": "receptor.pdb",                          │
│           "size": 245678,                                      │
│           "content_type": "chemical/x-pdb",                    │
│           "storage_path": "/uploads/org123/exec456/receptor.pdb"│
│         }                                                      │
│                                                                 │
│  3. Results (Outputs) → NeuroSnap Cloud URLs                   │
│     ├─ output.sdf → https://neurosnap.ai/api/job/{id}/out/... │
│     └─ output.csv → https://neurosnap.ai/api/job/{id}/out/... │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📐 Proposed Database Schema Changes

### Option A: Add Dedicated `execution_files` Table (RECOMMENDED)

```sql
-- New table for tracking input/output files separately
CREATE TABLE execution_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES task_framework_executions(execution_id) ON DELETE CASCADE,
    
    -- File classification
    parameter_name VARCHAR(100) NOT NULL,  -- e.g., 'receptor_file', 'ligand_file'
    file_type VARCHAR(20) NOT NULL,        -- 'input' or 'output'
    
    -- File metadata
    filename VARCHAR(255) NOT NULL,
    size_bytes BIGINT NOT NULL,
    content_type VARCHAR(100),
    
    -- Storage location
    storage_backend VARCHAR(50) NOT NULL,  -- 'local', 's3', 'neurosnap_cloud'
    storage_path TEXT NOT NULL,            -- e.g., '/uploads/{org_id}/{exec_id}/receptor.pdb'
    download_url TEXT,                     -- For external files (NeuroSnap results)
    
    -- Checksums for integrity
    md5_hash VARCHAR(32),
    sha256_hash VARCHAR(64),
    
    -- Timestamps
    uploaded_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,                  -- For temporary files
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(execution_id, parameter_name, file_type)
);

CREATE INDEX idx_execution_files_execution ON execution_files(execution_id);
CREATE INDEX idx_execution_files_type ON execution_files(execution_id, file_type);
```

**Benefits:**
- ✅ Separate file storage from parameter data
- ✅ Can query all files for an execution efficiently
- ✅ Supports file expiration/cleanup policies
- ✅ Track checksums for data integrity
- ✅ Support multiple storage backends per execution
- ✅ No JSONB size limits

---

### Modified `task_framework_executions.input_data` Structure

**OLD (Base64 embedded):**
```json
{
  "receptor_file": {
    "filename": "receptor.pdb",
    "size": 245678,
    "content_type": "chemical/x-pdb",
    "content_base64": "QVRPTSAgICAgIDEgIE4gICBN..."  // ❌ 300KB+ of base64!
  },
  "job_name": "EGFR_docking",
  "note": "Test run"
}
```

**NEW (File reference):**
```json
{
  "receptor_file": {
    "filename": "receptor.pdb",
    "size": 245678,
    "content_type": "chemical/x-pdb",
    "file_id": "550e8400-e29b-41d4-a716-446655440000"  // ✅ Reference to execution_files
  },
  "ligand_file": {
    "filename": "ligand.sdf",
    "size": 12345,
    "content_type": "chemical/x-mdl-sdfile",
    "file_id": "660e8400-e29b-41d4-a716-446655440001"
  },
  "job_name": "EGFR_docking",     // ✅ Plain string parameter
  "note": "Test run"              // ✅ Plain string parameter
}
```

---

## 🏗️ Implementation Plan

### Phase 1: Database Migration (Critical)

**Migration:** `20251113_execution_files_table.sql`

```sql
-- Create execution_files table
CREATE TABLE execution_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES task_framework_executions(execution_id) ON DELETE CASCADE,
    parameter_name VARCHAR(100) NOT NULL,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('input', 'output')),
    filename VARCHAR(255) NOT NULL,
    size_bytes BIGINT NOT NULL,
    content_type VARCHAR(100),
    storage_backend VARCHAR(50) NOT NULL,
    storage_path TEXT NOT NULL,
    download_url TEXT,
    md5_hash VARCHAR(32),
    sha256_hash VARCHAR(64),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(execution_id, parameter_name, file_type)
);

CREATE INDEX idx_execution_files_execution ON execution_files(execution_id);
CREATE INDEX idx_execution_files_type ON execution_files(execution_id, file_type);

-- Cleanup policy: Delete orphaned files older than 90 days
CREATE INDEX idx_execution_files_expires ON execution_files(expires_at) WHERE expires_at IS NOT NULL;
```

---

### Phase 2: Update Service Layer

**File:** `src/molecular_analysis_dashboard/services/unified_task_service.py`

```python
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

async def execute_task(
    self,
    task_id: str,
    parameters: Dict[str, Any],
    files: Optional[Dict[str, Any]] = None,
    org_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Execute a task with proper file storage"""
    
    # Create execution record first
    execution_id = str(uuid4())
    
    # Prepare input_data (strings/numbers only)
    input_data = {**parameters}
    
    # Handle file uploads separately
    if files:
        for param_name, file_info in files.items():
            content = file_info['content']
            filename = file_info['filename']
            content_type = file_info.get('content_type')
            
            # 1. Generate storage path
            storage_path = f"/uploads/{org_id}/{execution_id}/{filename}"
            
            # 2. Calculate checksums
            md5_hash = hashlib.md5(content).hexdigest()
            sha256_hash = hashlib.sha256(content).hexdigest()
            
            # 3. Store file to storage service
            file_storage_adapter = self._get_storage_adapter()  # Local/S3/MinIO
            await file_storage_adapter.store_file(
                path=storage_path,
                content=content,
                content_type=content_type
            )
            
            # 4. Create execution_files record
            file_record = await self._create_execution_file(
                execution_id=execution_id,
                parameter_name=param_name,
                file_type='input',
                filename=filename,
                size_bytes=len(content),
                content_type=content_type,
                storage_backend='local',  # or 's3', 'minio'
                storage_path=storage_path,
                md5_hash=md5_hash,
                sha256_hash=sha256_hash
            )
            
            # 5. Store ONLY file reference in input_data
            input_data[param_name] = {
                'filename': filename,
                'size': len(content),
                'content_type': content_type,
                'file_id': str(file_record['file_id'])  # ✅ Reference, not content!
            }
    
    # Create execution with lightweight input_data
    execution = await self.task_repo.create_execution(
        task_id=task_id,
        org_id=org_id,
        user_id=user_id,
        input_data=input_data,  # ✅ No base64 content!
        status='pending'
    )
    
    # ... rest of execution logic
```

---

### Phase 3: Update NeuroSnap Adapter

**File:** `src/molecular_analysis_dashboard/adapters/providers/neurosnap_task_adapter.py`

```python
async def execute_task(self, execution: TaskFrameworkExecution) -> Dict[str, Any]:
    """Execute task with file retrieval from storage"""
    
    parameters = execution.input_data
    
    # Fetch file parameters from execution_files table
    if 'receptor_file' in parameters:
        receptor_info = parameters['receptor_file']
        file_id = receptor_info.get('file_id')
        
        # Fetch file from execution_files and storage
        file_record = await self._get_execution_file(file_id)
        content = await self._retrieve_file_content(file_record)
        
        # Create UploadFile for NeuroSnap API
        receptor_file = self._create_upload_file(
            filename=file_record['filename'],
            content=content,
            content_type=file_record['content_type']
        )
    
    # Handle string parameters (no change needed)
    job_name = parameters.get('job_name', 'Unnamed Job')
    note = parameters.get('note', '')
    
    # Submit to NeuroSnap
    neurosnap_service = NeuroSnapService(api_key=self.api_key)
    result = await neurosnap_service.submit_gnina_docking(
        receptor_file=receptor_file,
        ligand_file=ligand_file,
        job_name=job_name,
        note=note
    )
    
    # Store result files in execution_files as 'output' type
    await self._store_result_files(
        execution_id=execution.execution_id,
        result_urls=result['download_urls']
    )
    
    return result
```

---

### Phase 4: Update Task Definition Schema Parsing

**Goal:** Differentiate file vs. string parameters from OpenAPI spec

**File:** `src/molecular_analysis_dashboard/services/unified_task_service.py`

```python
def parse_task_parameters(self, task_definition: Dict[str, Any]) -> Dict[str, Any]:
    """Parse OpenAPI spec to identify parameter types"""
    
    interface_spec = task_definition.get('interface_spec', {})
    schema = interface_spec.get('paths', {}).get('/execute', {}).get('post', {})
    request_body = schema.get('requestBody', {})
    properties = request_body.get('content', {}).get('multipart/form-data', {}).get('schema', {}).get('properties', {})
    
    parameter_types = {}
    for param_name, param_spec in properties.items():
        # Check if it's a file parameter
        if param_spec.get('format') == 'binary':
            parameter_types[param_name] = {
                'type': 'file',
                'required': param_name in schema.get('required', []),
                'description': param_spec.get('description'),
                'accept': self._get_file_extensions(param_spec)  # e.g., '.pdb'
            }
        else:
            parameter_types[param_name] = {
                'type': param_spec.get('type', 'string'),  # 'string', 'integer', 'boolean'
                'required': param_name in schema.get('required', []),
                'description': param_spec.get('description'),
                'default': param_spec.get('default'),
                'enum': param_spec.get('enum')
            }
    
    return parameter_types
```

---

### Phase 5: Update Frontend Components

**File:** `frontend/src/components/tasks/DynamicTaskForm.tsx`

```typescript
interface TaskParameter {
  name: string;
  type: 'file' | 'string' | 'integer' | 'boolean';
  required: boolean;
  description?: string;
  accept?: string;  // For file inputs: '.pdb,.sdf'
  default?: any;
  enum?: string[];
}

// Render field based on parameter type
{parameter.type === 'file' ? (
  <FileUploadField
    name={parameter.name}
    accept={parameter.accept}
    required={parameter.required}
    onChange={(file) => handleFileChange(parameter.name, file)}
  />
) : parameter.type === 'string' ? (
  <Input
    type="text"
    value={formData[parameter.name] || parameter.default || ''}
    onChange={(e) => handleChange(parameter.name, e.target.value)}
  />
) : parameter.type === 'integer' ? (
  <Input
    type="number"
    value={formData[parameter.name] || parameter.default || ''}
    onChange={(e) => handleChange(parameter.name, parseInt(e.target.value))}
  />
) : null}
```

---

## 🎯 Storage Backend Switching

### Environment-Based Configuration

```yaml
# .env.development
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=/storage
STORAGE_BASE_URL=http://storage:8080

# .env.production
STORAGE_BACKEND=s3
STORAGE_S3_BUCKET=molecular-analysis-uploads
STORAGE_S3_REGION=us-east-1
STORAGE_BASE_URL=https://s3.amazonaws.com/molecular-analysis-uploads
```

### Adapter Factory Pattern

```python
def _get_storage_adapter(self):
    """Get storage adapter based on environment"""
    backend = os.getenv('STORAGE_BACKEND', 'local')
    
    if backend == 's3':
        return S3StorageAdapter(
            bucket=os.getenv('STORAGE_S3_BUCKET'),
            region=os.getenv('STORAGE_S3_REGION')
        )
    elif backend == 'minio':
        return MinIOStorageAdapter(
            endpoint=os.getenv('MINIO_ENDPOINT'),
            access_key=os.getenv('MINIO_ACCESS_KEY'),
            secret_key=os.getenv('MINIO_SECRET_KEY')
        )
    else:
        return LocalStorageAdapter(
            base_path=os.getenv('STORAGE_LOCAL_PATH', '/storage'),
            base_url=os.getenv('STORAGE_BASE_URL', 'http://storage:8080')
        )
```

---

## 📊 Storage Organization

### Input Files (User Uploads)

```
/storage/uploads/{org_id}/{execution_id}/{filename}

Examples:
/storage/uploads/12345678-1234-1234-1234-123456789012/
                 550e8400-e29b-41d4-a716-446655440000/
                 receptor.pdb
                 
/storage/uploads/12345678-1234-1234-1234-123456789012/
                 550e8400-e29b-41d4-a716-446655440000/
                 ligand.sdf
```

### Result Files (NeuroSnap Downloads)

**Option 1: Store External URLs (Current - RECOMMENDED)**
```json
{
  "storage_backend": "neurosnap_cloud",
  "download_url": "https://neurosnap.ai/api/job/file/abc123/out/output.sdf",
  "expires_at": "2025-11-19T12:00:00Z"
}
```

**Option 2: Mirror to Local/S3 (Future)**
```
/storage/results/{org_id}/{execution_id}/{filename}

Example:
/storage/results/12345678-1234-1234-1234-123456789012/
                 550e8400-e29b-41d4-a716-446655440000/
                 output.sdf
```

---

## 🧹 File Cleanup Policies

### Automatic Cleanup Background Job

```python
# Celery beat task
@celery_app.task
async def cleanup_expired_files():
    """Delete files past their expiration date"""
    
    # Find expired files
    expired_files = await db.execute(
        "SELECT * FROM execution_files WHERE expires_at < NOW()"
    )
    
    for file_record in expired_files:
        # Delete from storage backend
        storage = get_storage_adapter(file_record['storage_backend'])
        await storage.delete_file(file_record['storage_path'])
        
        # Delete database record
        await db.execute(
            "DELETE FROM execution_files WHERE file_id = %s",
            file_record['file_id']
        )
```

### Retention Policy

```python
# Set expiration when creating execution_files
expires_at = now() + timedelta(days=90)  # Keep for 90 days

# For important results, set expires_at = NULL (keep forever)
```

---

## 🔄 Migration Strategy

### Step 1: Add `execution_files` table (safe, non-breaking)
```sql
-- Run migration
psql -f database/migrations/20251113_execution_files_table.sql
```

### Step 2: Update code to use new storage (dual-write period)
```python
# Write to BOTH old (base64) and new (file table)
# Read from new, fallback to old for backward compatibility
```

### Step 3: Backfill existing executions (optional)
```python
# For existing executions with base64 content, extract and store in execution_files
# This can be a background job
```

### Step 4: Remove base64 encoding (breaking change)
```python
# Stop writing base64 content
# Only use execution_files table
```

---

## 📈 Performance Comparison

### Before (Base64 in JSONB)
```
Execution with 2 files (receptor 200KB + ligand 50KB):
- Database row size: ~350KB
- Loading 100 executions: ~35MB transferred from DB
- Query time: 2-5 seconds
```

### After (File References)
```
Execution with 2 files:
- Database row size: ~2KB (metadata only)
- Loading 100 executions: ~200KB transferred from DB
- Query time: 100-200ms
- Files loaded on-demand when needed
```

**Improvement: 175x smaller database payload, 10-25x faster queries**

---

## ✅ Summary

### Critical Changes Required:

1. **Database:** Add `execution_files` table to separate file storage from metadata
2. **Service Layer:** Stop base64 encoding, use `FileStorageAdapter` + `execution_files` table
3. **Task Definitions:** Parse OpenAPI spec to identify file vs. string parameters
4. **Frontend:** Render correct input components based on parameter type
5. **API:** Return file metadata with `file_id` references, not embedded base64

### Benefits:

✅ Scalable file storage (supports GB-sized files)  
✅ Proper separation of concerns (files != parameters)  
✅ Type-safe parameter handling (file vs. string vs. integer)  
✅ Cloud-ready architecture (swap Local → S3 via env var)  
✅ 175x smaller database payload  
✅ 10-25x faster query performance  
✅ Support for file expiration/cleanup  
✅ Data integrity with checksums  
✅ Streaming support for large files  

### Next Steps:

1. Create migration: `20251113_execution_files_table.sql`
2. Update `unified_task_service.py` to use file storage
3. Update `neurosnap_task_adapter.py` to retrieve files by `file_id`
4. Update `DynamicTaskForm.tsx` to render correct input types
5. Test with real GNINA docking execution
6. Deploy and monitor performance improvements
