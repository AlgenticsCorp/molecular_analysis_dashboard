# Task Results Architecture Analysis

## System Overview

This document analyzes the existing hybrid storage and results architecture to inform the TaskResults page implementation.

## Existing Components

### 1. Storage Architecture

The system implements a **Hybrid Storage Pattern**:

#### Local Storage Adapter
- **Location**: `src/molecular_analysis_dashboard/adapters/storage/file_storage.py`
- **Purpose**: Manages molecular files in local filesystem
- **Structure**:
  ```
  /storage/
  ├── uploads/           # User-uploaded molecular files
  │   └── {org_id}/
  │       ├── receptors/
  │       └── ligands/
  ├── results/           # Job execution results
  │   └── {org_id}/
  │       └── jobs/
  │           └── {job_id}/
  │               ├── inputs/
  │               ├── outputs/
  │               └── intermediate/
  └── temp/              # Temporary processing files
  ```

#### Storage Port Interface
- **Location**: `src/molecular_analysis_dashboard/ports/storage.py`
- **Methods**:
  - `store_file()` - Upload and store files
  - `retrieve_file()` - Download file content
  - `delete_file()` - Remove files
  - `generate_presigned_url()` - Create download URLs
  - `get_file_info()` - Get file metadata
  - `validate_file_type()` - Check supported formats

#### Supported File Formats
```python
SUPPORTED_EXTENSIONS = {
    ".pdb", ".pdbqt", ".sdf", ".mol", ".mol2",
    ".xyz", ".cif", ".mmcif", ".cml", ".smiles"
}
```

### 2. Results Flow Architecture

#### External Provider (NeuroSnap API)
The system uses **NeuroSnap Cloud** as the execution engine:

```
┌──────────────────┐
│  Frontend        │
│  ExecuteTasks    │
└────────┬─────────┘
         │ Submit job
         ↓
┌──────────────────┐
│  Backend API     │
│  unified_tasks   │
└────────┬─────────┘
         │ Execute via TaskFramework
         ↓
┌──────────────────┐
│  NeuroSnap API   │
│  (External)      │
└────────┬─────────┘
         │ Store job_id
         ↓
┌──────────────────┐
│  Local Database  │
│  task_framework  │
│  _executions     │
└──────────────────┘
```

#### Results Retrieval Pattern

**Files are stored EXTERNALLY on NeuroSnap servers**, not in local storage adapter:

```python
# From unified_tasks.py - get_execution_results()
async def get_execution_results(self, execution_id: str):
    # Query TaskFramework (which calls NeuroSnap API)
    framework_results = await self.task_framework.get_execution_results(
        execution_id
    )
    
    # Returns:
    {
        "job_id": "neurosnap_job_id",
        "status": "completed",
        "files": ["output.sdf", "output.csv"],
        "download_urls": {
            "output.sdf": "https://neurosnap.ai/api/job/file/{job_id}/out/output.sdf",
            "output.csv": "https://neurosnap.ai/api/job/file/{job_id}/out/output.csv"
        },
        "raw_data": {
            "in": [["ligand.sdf", "7.81 KB"], ...],
            "out": [["output.sdf", "45.28 KB"], ...]
        }
    }
```

### 3. Unified Task API Endpoints

#### Current Endpoints
```
GET  /api/v1/tasks-unified/executions
     → List all executions (9 GNINA jobs in DB)

GET  /api/v1/tasks-unified/executions/{execution_id}/status
     → Get status, progress, timestamps

GET  /api/v1/tasks-unified/executions/{execution_id}/results
     → Get files and download URLs from NeuroSnap
```

#### NeuroSnap Unified Provider
```
GET  /api/v1/providers/neurosnap/status/{job_id}
     → Direct NeuroSnap status check

GET  /api/v1/providers/neurosnap/results/{job_id}
     → Direct NeuroSnap results fetch

GET  /api/v1/providers/neurosnap/download/{job_id}/{filename}
     → Proxy download from NeuroSnap
```

### 4. Frontend Components

#### Existing Molecular Viewer
- **Location**: `frontend/src/components/molecular/MolecularViewerSimple.tsx`
- **Library**: 3Dmol.js
- **Features**:
  - PDB/SDF format support
  - Interactive 3D rendering
  - Style controls (stick, cartoon, sphere)
  - Zoom, rotate, pan controls
  - Demo in FileManager page

#### FileManager Page
- **Purpose**: Demonstration of molecular viewer
- **Data**: Sample static PDB data
- **Features**:
  - File upload UI (non-functional)
  - 3D viewer demo with sample protein
  - File cards with metadata
  - Preview dialog

#### JobManager Page (Recently Updated)
- **Purpose**: Display execution history
- **Data Source**: `/api/v1/tasks-unified/executions`
- **File Display**: Shows real input/output files from NeuroSnap
- **File Structure**:
  ```typescript
  interface Job {
    inputFiles: Array<{ name: string; size: string; url?: string }>;
    outputFiles: Array<{ name: string; size: string; url?: string }>;
  }
  ```

## Key Architectural Decisions

### 1. Hybrid Storage Model

**Local Storage** (`FileStorageAdapter`):
- User-uploaded molecules (receptors/ligands)
- Template files
- Cached preprocessed files
- NOT used for job results

**External Storage** (NeuroSnap Cloud):
- Job execution artifacts
- Docking results (SDF, CSV, PDBQT)
- Execution logs
- Downloaded via presigned URLs

### 2. File Access Pattern

```
User uploads → Local storage (inputs/)
     ↓
Submit to NeuroSnap → Files uploaded to NeuroSnap
     ↓
Job executes → Results stored on NeuroSnap
     ↓
Results ready → Frontend gets download URLs
     ↓
User downloads → Direct from NeuroSnap (presigned URLs)
```

### 3. Database Schema

#### task_framework_executions table
```sql
CREATE TABLE task_framework_executions (
    execution_id UUID PRIMARY KEY,
    task_id VARCHAR(255),
    status VARCHAR(50),
    progress_percentage INTEGER,
    input_data JSONB,      -- Parameters sent to NeuroSnap
    output_data JSONB,     -- Results from NeuroSnap (download URLs)
    job_id VARCHAR(255),   -- External NeuroSnap job_id
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);
```

The `output_data` JSONB column stores:
```json
{
  "job_id": "neurosnap_id",
  "status": "completed",
  "files": ["output.sdf", "output.csv"],
  "download_urls": {
    "output.sdf": "https://...",
    "output.csv": "https://..."
  },
  "raw_data": {
    "in": [...],
    "out": [...]
  }
}
```

## TaskResults Page Requirements

Based on this architecture, the TaskResults page should:

### 1. Data Source
- **Primary**: `GET /api/v1/tasks-unified/executions/{execution_id}/results`
- **Secondary**: `GET /api/v1/tasks-unified/executions/{execution_id}/status`
- **Files**: Download URLs from `output_data.download_urls`

### 2. File Handling
- **DO NOT** use local `FileStorageAdapter` for results
- **DO** use NeuroSnap presigned URLs directly
- **Cache**: Consider caching file content in browser for 3D viewer

### 3. Molecular Visualization
- Reuse `MolecularViewerSimple` component
- Fetch file content from NeuroSnap URL
- Display PDB/SDF results in 3D viewer
- Support for GNINA output formats (.sdf primary)

### 4. Results Display Sections

#### A. Job Information Card
- Execution ID
- Task name (from database)
- Status badge
- Start/end times
- Runtime duration
- Progress (if running)

#### B. Docking Scores Table (for GNINA)
```
Parse output.csv for:
- Ligand name
- Binding affinity (kcal/mol)
- RMSD values
- Pose ranking
```

#### C. 3D Molecular Viewer
- Load output.sdf from NeuroSnap URL
- Interactive visualization
- Multiple pose support
- Zoom/rotate controls

#### D. Files Section
```typescript
Files shown:
- Input files (from raw_data.in)
  - Input_Ligand.json (7.81 KB)
  - Input_Receptor.zip (38.24 KB)
  
- Output files (from raw_data.out)
  - output.csv (597 bytes) - Docking scores
  - output.sdf (45.28 KB) - 3D structures
```

#### E. Download Actions
- Individual file download buttons
- "Download All Results" (zip)
- Direct links using presigned URLs

### 5. API Integration Pattern

```typescript
// TaskResults.tsx
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { taskService } from '../services/taskService';
import MolecularViewer from '../components/molecular/MolecularViewerSimple';

export const TaskResults: React.FC = () => {
  const { executionId } = useParams();
  
  // Fetch execution status
  const { data: statusData } = useQuery({
    queryKey: ['execution-status', executionId],
    queryFn: () => taskService.getExecutionStatus(executionId),
    refetchInterval: (data) => 
      data?.status === 'running' ? 5000 : false
  });
  
  // Fetch results (only if completed)
  const { data: resultsData } = useQuery({
    queryKey: ['execution-results', executionId],
    queryFn: () => taskService.getExecutionResults(executionId),
    enabled: statusData?.status === 'completed'
  });
  
  // Fetch 3D molecule file for viewer
  const outputSdfUrl = resultsData?.download_urls?.['output.sdf'];
  const { data: moleculeData } = useQuery({
    queryKey: ['molecule-file', outputSdfUrl],
    queryFn: async () => {
      const response = await fetch(outputSdfUrl);
      return await response.text();
    },
    enabled: !!outputSdfUrl
  });
  
  return (
    <Box>
      {/* Job Info Card */}
      {/* Docking Scores Table */}
      {/* 3D Viewer */}
      {moleculeData && (
        <MolecularViewer
          moleculeData={moleculeData}
          format="sdf"
          height={500}
          showControls={true}
        />
      )}
      {/* Files Download Section */}
    </Box>
  );
};
```

### 6. taskService.ts Additions

```typescript
// frontend/src/services/taskService.ts

export const taskService = {
  // Existing methods...
  
  getExecutionStatus: async (executionId: string) => {
    const response = await fetch(
      `/api/v1/tasks-unified/executions/${executionId}/status`
    );
    return response.json();
  },
  
  getExecutionResults: async (executionId: string) => {
    const response = await fetch(
      `/api/v1/tasks-unified/executions/${executionId}/results`
    );
    return response.json();
  },
  
  // Helper to parse CSV scores
  parseDockingScores: (csvContent: string) => {
    const lines = csvContent.trim().split('\n');
    const headers = lines[0].split(',');
    return lines.slice(1).map(line => {
      const values = line.split(',');
      return headers.reduce((obj, header, i) => {
        obj[header] = values[i];
        return obj;
      }, {});
    });
  }
};
```

## Migration Path

### Phase 1: Basic Results Display (CURRENT NEED)
1. ✅ Already have: API endpoints for results
2. ✅ Already have: MolecularViewer component
3. ✅ Already have: File download URLs from NeuroSnap
4. ❌ Need: TaskResults page component
5. ❌ Need: Docking scores table component
6. ❌ Need: Route configuration

### Phase 2: Enhanced Visualization
- Multiple pose viewer
- Ligand-receptor overlay
- Distance measurements
- Surface rendering

### Phase 3: Analysis Tools
- Score comparison charts
- Binding site analysis
- Export capabilities (PNG, report PDF)

## Implementation Recommendations

### DO's ✅
1. **Use NeuroSnap URLs directly** - Files are already hosted externally
2. **Reuse MolecularViewer** - Already working with 3Dmol.js
3. **Follow JobManager pattern** - Similar data structure
4. **Cache molecule data** - Avoid re-downloading for 3D viewer
5. **Handle running state** - Show progress for incomplete jobs

### DON'Ts ❌
1. **Don't use FileStorageAdapter** - Results aren't in local storage
2. **Don't create new file upload** - Files come from NeuroSnap
3. **Don't reinvent 3D viewer** - MolecularViewerSimple works
4. **Don't store results locally** - Keep hybrid model clean
5. **Don't ignore error states** - NeuroSnap calls can fail

## File Organization

Suggested new files:
```
frontend/src/
├── pages/
│   └── TaskResults.tsx          # Main results page (NEW)
├── components/
│   ├── molecular/
│   │   └── MolecularViewerSimple.tsx  # ✅ Already exists
│   └── results/
│       ├── DockingScoresTable.tsx     # NEW - Parse CSV, show scores
│       ├── JobInfoCard.tsx            # NEW - Status, timing, metadata
│       └── ResultsFileList.tsx        # NEW - Download buttons
├── services/
│   └── taskService.ts           # ✅ Update with results methods
└── types/
    └── results.ts               # NEW - TypeScript interfaces
```

## Next Steps

1. Create TaskResults page skeleton
2. Integrate with existing API endpoints
3. Add 3D viewer for output.sdf
4. Parse and display docking scores
5. Add file download UI
6. Wire up routing from JobManager "View Details"

This architecture analysis reveals a clean separation:
- **Local storage** = User uploads and cache
- **NeuroSnap** = Execution and results
- **Database** = Metadata and job tracking
- **Frontend** = Visualization and download orchestration
