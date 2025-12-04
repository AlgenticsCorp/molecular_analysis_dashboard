# Current System Analysis: Task Definitions vs Framework Tasks

**Date**: November 12, 2025  
**Status**: System Architecture Analysis  
**Purpose**: Understanding the dual-track task system and alignment with documentation

---

## 🎯 Executive Summary

The Molecular Analysis Dashboard currently implements a **dual-track task system**:

1. **Database-Driven Tasks** (`task_definitions` table) - Designed for dynamic, user-configurable tasks
2. **Framework Tasks** (Code-based) - Currently used for GNINA integration

### Current State
- ✅ Database schema complete with `task_definitions` table (22 tables total)
- ✅ Framework tasks implemented and operational (GNINA docking)
- ✅ `task_framework_executions` table tracking framework executions
- ⚠️ **Gap**: `task_definitions` table is empty - not currently used
- ⚠️ **Temporary**: GNINA tasks hard-coded in `neurosnap_task_adapter.py`

---

## 📊 Architecture Analysis

### **Designed System (Per Documentation)**

According to `docs/architecture/pipeline-builder-design.md` and `docs/database/design/schema.md`:

```
┌─────────────────────────────────────────────────┐
│         METADATA DATABASE (Shared)              │
├─────────────────────────────────────────────────┤
│                                                 │
│  task_definitions                               │
│  ├── Dynamic task registry                     │
│  ├── OpenAPI specifications                    │
│  ├── Service endpoints                         │
│  ├── Parameter schemas                         │
│  └── Org-scoped task definitions              │
│                                                 │
│  PURPOSE: Store user-configurable tasks        │
│           without code deployment              │
└─────────────────────────────────────────────────┘
```

**Key Design Principles**:
- Tasks stored as **database records** with OpenAPI specs
- **Runtime task registration** - no frontend redeployment needed
- **Multi-tenant**: Organizations can define custom tasks
- **Dynamic form generation** from OpenAPI schemas
- **Service discovery** integration

### **Current Implementation**

```
┌─────────────────────────────────────────────────┐
│         FRAMEWORK TASKS (Code-Based)            │
├─────────────────────────────────────────────────┤
│                                                 │
│  neurosnap_task_adapter.py                      │
│  └── get_available_tasks()                     │
│      └── Returns hardcoded dict:               │
│          {                                      │
│            "gnina-molecular-docking": {         │
│              "name": "GNINA Docking",          │
│              "parameters": [...],              │
│              "provider": "neurosnap"           │
│            }                                    │
│          }                                      │
│                                                 │
│  PURPOSE: Quick GNINA integration              │
│           Bypasses database layer              │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│         DATABASE TASKS (Empty)                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  task_definitions table: 0 rows                │
│                                                 │
│  STATUS: Schema exists, not populated          │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Component Breakdown

### **1. Task Definitions Table (`task_definitions`)**

**Purpose** (Per Documentation):
- Store reusable analysis task definitions
- Enable dynamic task registration without code changes
- Support multi-tenant custom task creation
- Integrate with Pipeline Builder for workflow composition

**Schema**:
```sql
CREATE TABLE task_definitions (
    task_definition_id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(org_id),
    task_id VARCHAR(100) NOT NULL,          -- Human-readable ID
    version VARCHAR(20) NOT NULL,
    
    -- Task Metadata
    task_metadata JSONB NOT NULL,           -- name, description, category
    interface_spec JSONB NOT NULL,          -- Parameters, inputs, outputs
    service_config JSONB NOT NULL,          -- Endpoint, authentication
    
    -- Pipeline Builder Support
    openapi_spec JSONB,                     -- OpenAPI 3.0 specification
    service_endpoint VARCHAR(500),          -- REST API endpoint
    health_check_endpoint VARCHAR(500),     -- Health monitoring
    docker_image VARCHAR(500),              -- Container image
    resource_requirements JSONB,            -- CPU, memory, GPU
    
    -- Lifecycle
    is_active BOOLEAN NOT NULL,
    is_system BOOLEAN NOT NULL,             -- Built-in vs custom
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

**Current Status**: ✅ Schema exists, ❌ No data, ❌ Not used

**Use Cases** (Documented):
1. **Admin adds new computational service** → Registers in `task_definitions`
2. **Frontend dynamically loads tasks** → Queries `task_definitions`
3. **Pipeline Builder** → Composes tasks from `task_definitions`
4. **Organizations create custom workflows** → Reference `task_definitions`

---

### **2. Framework Tasks (Current Implementation)**

**Location**: `src/molecular_analysis_dashboard/adapters/providers/neurosnap_task_adapter.py`

**Implementation**:
```python
class TaskExecutionService:
    async def get_available_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available framework tasks."""
        return {
            "gnina-molecular-docking": {
                "name": "GNINA Molecular Docking",
                "description": "Perform molecular docking using GNINA via NeuroSnap",
                "version": "1.0.0",
                "category": "molecular-docking",
                "tags": ["docking", "gnina", "protein-ligand"],
                "provider": "neurosnap",
                "parameters": [
                    {
                        "name": "receptor_file",
                        "type": "file",
                        "required": True,
                        "description": "Protein receptor file (PDB format)"
                    },
                    {
                        "name": "ligand_file",
                        "type": "file",
                        "required": True,
                        "description": "Ligand file (SDF/MOL2 format)"
                    },
                    {
                        "name": "exhaustiveness",
                        "type": "integer",
                        "required": False,
                        "default": 8,
                        "description": "Exhaustiveness of the global search"
                    }
                ],
                "execution_time_estimate": 600
            }
        }
```

**Characteristics**:
- ✅ **Fast to implement** - No database setup needed
- ✅ **Type-safe** - Python code with IDE support
- ❌ **Hardcoded** - Requires code deployment to add tasks
- ❌ **Not multi-tenant** - Same tasks for all organizations
- ❌ **No versioning** - Changes affect all users immediately

---

### **3. Task Execution Tracking**

**Framework Executions**: `task_framework_executions` table
```sql
CREATE TABLE task_framework_executions (
    execution_id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(org_id),
    user_id UUID REFERENCES users(user_id),
    task_id VARCHAR(100) NOT NULL,          -- Framework task identifier
    display_name VARCHAR(200) NOT NULL,
    
    -- Execution State
    status VARCHAR(50) NOT NULL,
    external_job_id VARCHAR(255),           -- NeuroSnap job ID
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    
    -- Progress Tracking
    progress_percentage INTEGER DEFAULT 0,
    estimated_duration_seconds INTEGER,
    actual_duration_seconds INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Metadata
    extra_metadata JSONB
);
```

**Status**: ✅ Implemented and operational

**Database Executions**: `task_executions` table (legacy)
- Designed for database-defined tasks
- Currently unused since `task_definitions` is empty

---

## 🔄 Data Flow Analysis

### **Current Flow (Framework Tasks)**

```
Frontend (TaskLibrary.tsx)
    ↓ GET /api/v1/tasks-unified/available
UnifiedTaskService.get_all_tasks()
    ↓ calls
TaskExecutionService.get_available_tasks()
    ↓ returns
Hardcoded Dict["gnina-molecular-docking"]
    ↓ formatted and returned
Frontend displays: "GNINA Molecular Docking"
```

**Execution Flow**:
```
User submits task
    ↓ POST /api/v1/tasks-unified/{task_id}/execute
UnifiedTaskService.execute_task()
    ↓ _is_framework_task() → True
    ↓ _execute_framework_task()
TaskExecutionService.execute_task()
    ↓ NeuroSnapDockingAdapter.submit_task()
    ↓ POST /api/v1/providers/neurosnap/docking/submit
NeuroSnap API (external)
    ↓ Returns job_id
TaskFrameworkExecution record created
    ↓ status: "submitted"
    ↓ external_job_id: "neurosnap-job-123"
Frontend polls: GET /api/v1/tasks-unified/executions/{id}/status
```

### **Intended Flow (Database Tasks)**

```
Admin adds task via API
    ↓ POST /api/v1/task-definitions
TaskDefinition record created
    ↓ org_id, task_id, openapi_spec, etc.
Database stores OpenAPI spec
    ↓
Frontend queries tasks
    ↓ GET /api/v1/tasks-unified/available
UnifiedTaskService._get_database_tasks()
    ↓ SELECT * FROM task_definitions WHERE org_id = ?
Returns org-specific + system tasks
    ↓
Frontend generates dynamic form from interface_spec
    ↓
User submits task
    ↓ POST /api/v1/tasks-unified/{task_id}/execute
UnifiedTaskService._execute_database_task()
    ↓ Calls task's service_endpoint
    ↓ Records in task_executions table
```

**Status**: ⚠️ Database task flow **NOT IMPLEMENTED** - raises `NotImplementedError`

---

## 📋 Gap Analysis

### **What's Complete**

| Component | Status | Notes |
|-----------|--------|-------|
| Database schema | ✅ Complete | 22 tables including `task_definitions` |
| Framework tasks | ✅ Operational | GNINA docking working |
| Execution tracking | ✅ Implemented | `task_framework_executions` table |
| API endpoints | ✅ Complete | 7 unified task endpoints |
| Frontend integration | ✅ Working | Tasks display in Task Library |
| Health monitoring | ✅ Functional | Status checks operational |

### **What's Missing**

| Component | Status | Impact |
|-----------|--------|--------|
| Database task population | ❌ Not started | Can't use dynamic task registry |
| Dynamic form generation | ❌ Not implemented | Hard-coded forms only |
| Task execution UI | ❌ Not implemented | Can't submit tasks from frontend |
| Task monitoring page | ❌ Not implemented | No real-time status |
| Results visualization | ❌ Not implemented | No 3D molecule viewer |
| Pipeline Builder | ❌ Future phase | Multi-step workflows |
| Database task execution | ❌ NotImplementedError | `_execute_database_task()` stub |

---

## 🎯 Alignment with Documentation

### **Documentation States**:

1. **Multi-Tenant Task System** (docs/database/design/schema.md)
   - ✅ Schema designed for org-scoped tasks
   - ❌ Not implemented - tasks are global

2. **Dynamic Task Registry** (docs/architecture/pipeline-builder-design.md)
   - ✅ Table structure supports OpenAPI specs
   - ❌ No runtime task registration

3. **Pipeline Builder Integration** (docs/architecture/pipeline-builder-design.md)
   - ✅ Schema ready for workflow composition
   - ❌ Pipeline Builder not implemented

4. **Clean Architecture** (docs/architecture/project-design-overview.md)
   - ✅ Ports & Adapters pattern followed
   - ✅ UnifiedTaskService bridges both systems

### **Current vs Intended State**

```
INTENDED:
┌─────────────────────────────────────────┐
│  Admin registers task in DB             │
│  ↓                                      │
│  Frontend dynamically loads from DB     │
│  ↓                                      │
│  User selects task → form generated     │
│  ↓                                      │
│  Execution tracked in task_executions   │
└─────────────────────────────────────────┘

CURRENT:
┌─────────────────────────────────────────┐
│  Developer hardcodes task in Python     │
│  ↓                                      │
│  Frontend loads from code               │
│  ↓                                      │
│  User sees task (no execution yet)      │
│  ↓                                      │
│  Execution tracked in framework table   │
└─────────────────────────────────────────┘
```

---

## 🛤️ Evolution Path

### **Phase 1: Current State (GNINA Integration)**
**Status**: 40% Complete

```
[Framework Tasks] ────→ [Frontend Display]
       ↓
[task_framework_executions]
```

**Completed**:
- ✅ GNINA task defined in code
- ✅ Backend API endpoints
- ✅ Frontend task display
- ✅ Execution tracking table

**Pending**:
- ⏳ Dynamic form generation
- ⏳ Task execution UI
- ⏳ Monitoring dashboard
- ⏳ Results visualization

### **Phase 2: Database Task Integration**
**Status**: Not Started

```
[task_definitions] ────→ [UnifiedTaskService]
       ↓                         ↓
[Dynamic Forms]          [task_executions]
```

**Required**:
- Implement `_execute_database_task()`
- Populate `task_definitions` with GNINA
- Build dynamic form generator
- Add task registration API

### **Phase 3: Pipeline Builder**
**Status**: Design Complete

```
[Pipeline Templates] ────→ [Nextflow Scripts]
       ↓                           ↓
[Visual Workflow Builder]    [Multi-Step Execution]
```

**Documented in**:
- `docs/architecture/pipeline-builder-design.md`
- `docs/implementation/plan.md` (Stage 6)

---

## 💡 Recommendations

### **Short Term (Complete Current Phase)**

1. **Move GNINA to Database**
   ```sql
   INSERT INTO task_definitions (
       org_id, task_id, version,
       task_metadata, interface_spec, service_config,
       openapi_spec, service_endpoint, is_active, is_system
   ) VALUES (
       '00000000-0000-0000-0000-000000000000', -- System tasks
       'gnina-molecular-docking',
       '1.0.0',
       '{"name": "GNINA Molecular Docking", "category": "docking"}'::jsonb,
       '{"parameters": [...]}'::jsonb,
       '{"provider": "neurosnap", "endpoint": "/api/v1/providers/neurosnap/docking/submit"}'::jsonb,
       '{"openapi": "3.0.0", ...}'::jsonb,
       '/api/v1/providers/neurosnap/docking/submit',
       TRUE,
       TRUE
   );
   ```

2. **Implement Database Task Execution**
   - Complete `UnifiedTaskService._execute_database_task()`
   - Add service endpoint invocation logic
   - Track executions in `task_executions` table

3. **Build Dynamic Forms**
   - Create `DynamicTaskForm.tsx` component
   - Parse `interface_spec` to generate form fields
   - Implement file upload handling

### **Medium Term (Align with Documentation)**

1. **Multi-Tenant Task Support**
   - Allow orgs to register custom tasks
   - Add task management UI
   - Implement org-scoped task queries

2. **OpenAPI Integration**
   - Store full OpenAPI 3.0 specs
   - Generate client code from specs
   - Validate submissions against schemas

3. **Service Discovery**
   - Health check integration
   - Dynamic service registration
   - Container orchestration support

### **Long Term (Pipeline Builder)**

1. **Visual Workflow Editor**
   - React Flow integration
   - Task composition UI
   - Dependency validation

2. **Nextflow Integration**
   - Script generation from visual pipelines
   - Workflow execution engine
   - Result aggregation

---

## 📝 Summary

### **Current Architecture**

The system implements a **pragmatic interim solution**:
- Framework tasks provide rapid GNINA integration
- Database schema ready for future dynamic tasks
- Clean architecture allows both systems to coexist
- UnifiedTaskService abstracts the difference from frontend

### **Alignment Status**

| Aspect | Alignment | Notes |
|--------|-----------|-------|
| Database Schema | ✅ Perfect | Schema matches documentation |
| Task Storage | ⚠️ Partial | Framework tasks bypass DB |
| Multi-Tenancy | ❌ Gap | Tasks are global, not org-scoped |
| Dynamic Registration | ❌ Gap | Requires code deployment |
| Pipeline Builder Ready | ✅ Yes | Schema supports future workflows |
| Clean Architecture | ✅ Yes | Ports & Adapters implemented |

### **Conclusion**

The current implementation is a **valid stepping stone**:
- ✅ Delivers GNINA functionality quickly
- ✅ Maintains architectural integrity
- ✅ Doesn't block future database task migration
- ⚠️ Deviates from multi-tenant dynamic task vision
- ⚠️ Requires migration path to align with documentation

**Next Priority**: Complete Phase 1 (dynamic forms, execution UI, monitoring) before migrating to database tasks.

---

**Document Owner**: AI Assistant  
**Review Cycle**: After each implementation phase  
**Related Docs**: 
- `docs/architecture/pipeline-builder-design.md`
- `docs/database/design/schema.md`
- `docs/implementation/plan.md`
- `docs/implementation/gnina-integration-plan.md`
