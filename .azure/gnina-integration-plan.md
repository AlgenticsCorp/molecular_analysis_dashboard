# GNINA Docking Service Integration Plan

## Overview

Based on analysis of the Neurosnap API tutorial and existing scripts in `temp/scripts/`, this plan outlines the integration of GNINA molecular docking services as our first concrete molecular analysis provider. GNINA will be accessed via the Neurosnap cloud API, providing production-grade docking without requiring local GNINA containerization.

## Key Components from Analysis

### From Neurosnap API Tutorial
- **Authentication**: X-API-KEY header-based authentication
- **Job Submission**: POST `/api/job/submit/SERVICE_NAME` with multipart/form-data
- **Status Polling**: GET `/api/job/status/JOB_ID` for execution monitoring
- **Result Retrieval**: GET `/api/job/files/JOB_ID/out` and `/api/job/file/JOB_ID/out/FILE_NAME`
- **Service Discovery**: GET `/api/services` for available services

### From Existing Scripts
- **submit_gnina_job.py**: Complete GNINA submission workflow
- **prep_engine.py**: Ligand preparation pipeline (drug name → SMILES → 3D → PDBQT)
- **SRS_Pipeline_Tutorial.ipynb**: End-to-end molecular resistance analysis

## Architecture Integration Strategy

### 1. Provider Architecture Pattern
```
External Provider (Neurosnap API) → HTTP Task Service Adapter → Domain Use Cases
```

Instead of containerized services, we'll use Neurosnap as our "service provider":
- **Service Discovery**: Query Neurosnap `/api/services` endpoint
- **Task Execution**: Submit jobs to Neurosnap API
- **Result Processing**: Retrieve and parse Neurosnap job outputs

### 2. Clean Architecture Placement

```
src/molecular_analysis_dashboard/
├── domain/
│   ├── entities/
│   │   ├── docking_job.py          # DockingJob entity with GNINA-specific fields
│   │   └── molecular_structure.py  # Molecule, Receptor, Ligand entities
│   └── services/
│       └── ligand_preparation.py   # Port for ligand prep services
├── use_cases/
│   ├── commands/
│   │   ├── execute_docking_task.py    # Main docking execution use case
│   │   └── prepare_ligand.py          # Ligand preparation workflow
│   └── queries/
│       └── get_docking_results.py     # Retrieve docking analysis results
├── ports/
│   └── external/
│       ├── docking_engine_port.py     # Abstract docking engine interface
│       ├── molecular_prep_port.py     # Abstract ligand preparation interface
│       └── neurosnap_api_port.py      # Neurosnap-specific API interface
├── adapters/
│   ├── external/
│   │   ├── neurosnap_adapter.py       # Neurosnap API implementation
│   │   └── ligand_prep_adapter.py     # RDKit/OpenBabel implementation
│   └── http/
│       └── neurosnap_client.py        # HTTP client for Neurosnap API
└── infrastructure/
    └── config/
        └── neurosnap_settings.py      # API keys and endpoints
```

## Implementation Phases

### Phase 1: Core Neurosnap Integration (Week 1)

#### 1.1 Neurosnap API Adapter
**File**: `src/molecular_analysis_dashboard/adapters/external/neurosnap_adapter.py`

```python
class NeuroSnapAdapter(DockingEnginePort):
    """Neurosnap API implementation for GNINA docking."""

    async def submit_docking_job(self, receptor_pdb: str, ligand_sdf: str, job_note: str) -> str:
        """Submit GNINA docking job to Neurosnap API."""

    async def get_job_status(self, job_id: str) -> JobStatus:
        """Poll job execution status."""

    async def retrieve_results(self, job_id: str) -> DockingResults:
        """Download and parse docking results."""
```

#### 1.2 HTTP Client Implementation
**File**: `src/molecular_analysis_dashboard/adapters/http/neurosnap_client.py`

Based on `temp/scripts/submit_gnina_job.py`:
- Multipart form data handling
- Authentication with X-API-KEY header
- Error handling and retry logic
- File upload/download capabilities

#### 1.3 Domain Entities
**File**: `src/molecular_analysis_dashboard/domain/entities/docking_job.py`

```python
@dataclass
class GninaDockingJob:
    job_id: str
    receptor_file: str
    ligand_file: Optional[str]
    job_status: JobStatus
    results: Optional[DockingResults]
    neurosnap_job_id: Optional[str]  # External provider job ID
```

### Phase 2: Ligand Preparation Pipeline (Week 1-2)

#### 2.1 Molecular Preparation Port
**File**: `src/molecular_analysis_dashboard/ports/external/molecular_prep_port.py`

```python
class MolecularPreparationPort(ABC):
    @abstractmethod
    async def fetch_smiles_from_drug_name(self, drug_name: str) -> str:
        """Fetch SMILES from PubChem API."""

    @abstractmethod
    async def generate_3d_conformer(self, smiles: str) -> MoleculeStructure:
        """Generate optimized 3D conformer using RDKit."""

    @abstractmethod
    async def convert_format(self, molecule: MoleculeStructure, target_format: str) -> str:
        """Convert molecular format (MOL → SDF → PDBQT)."""
```

#### 2.2 RDKit/OpenBabel Adapter
**File**: `src/molecular_analysis_dashboard/adapters/external/ligand_prep_adapter.py`

Based on `temp/scripts/prep_engine.py`:
- PubChem API integration for SMILES resolution
- RDKit 3D conformer generation and optimization
- OpenBabel format conversions
- Validation and error handling

### Phase 3: Task Execution Integration (Week 2)

#### 3.1 GNINA Task Definition Schema
**Database Record**: Create in TaskDefinition table

```json
{
  "task_id": "gnina-molecular-docking",
  "task_metadata": {
    "name": "GNINA Molecular Docking",
    "description": "Neural network-guided molecular docking using GNINA via Neurosnap API",
    "category": "molecular_docking",
    "provider": "neurosnap",
    "engine": "gnina"
  },
  "interface_spec": {
    "openapi": "3.0.0",
    "info": {"title": "GNINA Docking API", "version": "1.0.0"},
    "paths": {
      "/execute": {
        "post": {
          "requestBody": {
            "required": true,
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "required": ["receptor"],
                  "properties": {
                    "receptor": {
                      "type": "object",
                      "properties": {
                        "type": {"enum": ["pdb_file", "pdb_data"]},
                        "data": {"type": "string"},
                        "name": {"type": "string"}
                      }
                    },
                    "ligand": {
                      "type": "object",
                      "properties": {
                        "type": {"enum": ["drug_name", "smiles", "sdf_data"]},
                        "data": {"type": "string"}
                      }
                    },
                    "job_note": {"type": "string"}
                  }
                }
              }
            }
          }
        }
      }
    }
  },
  "service_config": {
    "provider": "neurosnap",
    "service_name": "GNINA",
    "timeout": 3600,
    "retry_attempts": 3
  }
}
```

#### 3.2 Execute Docking Task Use Case
**File**: `src/molecular_analysis_dashboard/use_cases/commands/execute_docking_task.py`

```python
class ExecuteDockingTaskUseCase:
    async def execute(self, task_id: str, parameters: Dict[str, Any]) -> TaskExecution:
        # 1. Load task definition from database
        # 2. Validate parameters against OpenAPI schema
        # 3. Prepare ligand if needed (drug_name → SMILES → SDF)
        # 4. Submit to Neurosnap via adapter
        # 5. Create TaskExecution record
        # 6. Return execution details
```

#### 3.3 Task Execution Endpoint
**File**: `src/molecular_analysis_dashboard/presentation/api/routes/tasks.py`

Add POST `/api/v1/tasks/{task_id}/execute` endpoint:

```python
@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str,
    parameters: TaskExecutionRequest,
    db: AsyncSession = Depends(get_metadata_session)
) -> TaskExecutionResponse:
    """Execute a molecular analysis task."""
```

### Phase 4: Complete Pipeline Integration (Week 3)

#### 4.1 SRS Pipeline Implementation
Based on `temp/SRS_Pipeline_Tutorial_P0076655_FINAL.ipynb`:

1. **Mutation Data Processing**: Parse clinical mutation data (MSK-CHORD, TCGA)
2. **Structure Prediction Integration**: Connect with AlphaFold3 via Neurosnap
3. **Resistance Analysis**: Compare wild-type vs mutant docking scores
4. **Clinical Validation**: Compare predictions with real patient outcomes

#### 4.2 Pipeline Template Creation
**Database Record**: Create PipelineTemplate for end-to-end workflow

```json
{
  "name": "structural-drug-resistance-analysis",
  "display_name": "Structural Drug Resistance Analysis",
  "description": "Complete pipeline for predicting drug resistance from mutation data",
  "workflow_definition": {
    "steps": [
      {"name": "parse_mutations", "task_id": "mutation-parser"},
      {"name": "predict_structure", "task_id": "alphafold3-prediction"},
      {"name": "prepare_ligand", "task_id": "ligand-preparation"},
      {"name": "dock_wildtype", "task_id": "gnina-molecular-docking"},
      {"name": "dock_mutant", "task_id": "gnina-molecular-docking"},
      {"name": "analyze_resistance", "task_id": "resistance-analyzer"}
    ]
  }
}
```

## Testing Strategy

### Unit Tests
- Neurosnap API adapter (mocked HTTP calls)
- Ligand preparation pipeline (RDKit/OpenBabel)
- Task execution use cases
- OpenAPI schema validation

### Integration Tests
- End-to-end GNINA docking with test receptor/ligand
- Pipeline execution with sample mutation data
- Error handling and timeout scenarios

### Clinical Validation Tests
- Reproduce SRS tutorial results with P-0076655 data
- Validate resistance predictions against known clinical outcomes
- Performance benchmarking against literature values

## Success Metrics

1. **Functional**: Successfully execute GNINA docking via Neurosnap API
2. **Performance**: Complete docking within 1 hour for typical receptor/ligand pairs
3. **Accuracy**: Reproduce tutorial binding affinity predictions within ±0.5 kcal/mol
4. **Integration**: Seamless execution through our task execution endpoint
5. **Clinical**: Validate resistance predictions match real patient outcomes

## Risk Mitigation

### API Dependencies
- **Risk**: Neurosnap API availability/rate limits
- **Mitigation**: Implement retry logic, queue management, fallback providers

### Molecular Data Quality
- **Risk**: Invalid PDB/SDF data causing job failures
- **Mitigation**: Comprehensive input validation, format conversion utilities

### Clinical Data Integration
- **Risk**: Complex mutation parsing and validation
- **Mitigation**: Use established parsers from temp/scripts, extensive testing

## Next Steps

1. **Start Implementation**: Begin with Phase 1 - Neurosnap adapter creation
2. **Database Setup**: Create GNINA task definition records
3. **Testing Infrastructure**: Set up test data and validation pipelines
4. **Documentation**: Create API documentation and usage examples

This plan provides a clear roadmap for integrating production-grade GNINA molecular docking into our platform, leveraging existing scripts and the Neurosnap cloud API for immediate functionality while maintaining our Clean Architecture principles.
