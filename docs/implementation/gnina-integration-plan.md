# GNINA Task Framework Integration Plan

## ✅ **COMPLETED WORK**

### Database Integration ✅
- [x] Created `task_framework_executions` table (migration `20251111_2150_80835240e483`)
- [x] Seeded GNINA task definition in `task_definitions` table
- [x] Added indexes for performance (org_id, user_id, status, created_at)
- [x] PostgreSQL exposed on port 5432 for external pgAdmin access

### Backend API ✅
- [x] Created `UnifiedTaskService` combining database + framework tasks
- [x] Implemented `/api/v1/tasks-unified/available` endpoint (returns 2 GNINA tasks)
- [x] Implemented `/api/v1/tasks-unified/health` endpoint
- [x] Implemented `/api/v1/tasks-unified/{task_id}` get task details
- [x] Implemented `/api/v1/tasks-unified/{task_id}/execute` endpoint
- [x] Implemented `/api/v1/tasks-unified/executions/{id}/status` endpoint
- [x] Implemented `/api/v1/tasks-unified/executions/{id}/results` endpoint
- [x] Implemented `/api/v1/tasks-unified/executions` list user executions
- [x] Fixed async database patterns (AsyncGenerator instead of context manager)
- [x] Standardized response format ('id' field instead of 'task_id')

### Frontend Integration ✅
- [x] Updated `taskService.ts` to use `/api/v1/tasks-unified/available`
- [x] Fixed health check endpoint to use absolute path
- [x] Enabled `useApiTasks` feature flag by default
- [x] Task Library displays 2 GNINA tasks from API (not fallback)
- [x] API health status shows "Healthy"
- [x] Updated navigation from `/jobs/create` to `/execute-tasks`

### Infrastructure ✅
- [x] Docker services rebuilt and running (api, frontend, gateway, postgres, redis)
- [x] Gateway routes configured (/api/* → api, /* → frontend)
- [x] All containers healthy

---

## � **REMAINING WORK**

### Phase 1: Dynamic Task Execution Form (HIGH PRIORITY)

**Current Issue**: TaskLibrary "Run Task" button navigates to `/execute-tasks?task=gnina-molecular-docking`, but ExecuteTasks page is hardcoded for a specific docking workflow.

**What's Needed**:

1. **Update ExecuteTasks.tsx** to be task-agnostic:
   ```typescript
   // Parse query parameter
   const searchParams = new URLSearchParams(location.search);
   const taskId = searchParams.get('task');
   
   // Fetch task details from API
   const task = await fetch(`/api/v1/tasks-unified/${taskId}`);
   
   // Dynamically generate form based on task.parameters
   const form = generateDynamicForm(task.parameters);
   ```

2. **Create Dynamic Form Generator**:
   ```typescript
   function generateDynamicForm(parameters: TaskParameter[]) {
     return parameters.map(param => {
       switch(param.type) {
         case 'file': return <FileUploadField {...param} />;
         case 'string': return <TextField {...param} />;
         case 'integer': return <NumberField {...param} />;
         case 'boolean': return <SwitchField {...param} />;
         default: return <TextField {...param} />;
       }
     });
   }
   ```

3. **Handle File Uploads**:
   ```typescript
   // For GNINA: receptor_file (PDB) + ligand_file (SDF)
   const formData = new FormData();
   formData.append('receptor_file', receptorFile);
   formData.append('ligand_file', ligandFile);
   formData.append('job_name', jobName);
   formData.append('note', note);
   
   await fetch(`/api/v1/tasks-unified/${taskId}/execute`, {
     method: 'POST',
     body: formData
   });
   ```

4. **Submit Task Execution**:
   - Validate all required parameters
   - Show loading state during submission
   - Handle errors gracefully
   - On success: redirect to monitoring page with execution_id

**Files to Modify**:
- `frontend/src/pages/ExecuteTasks.tsx` - Make dynamic
- `frontend/src/components/task/DynamicTaskForm.tsx` - NEW component
- `frontend/src/components/task/FileUploadField.tsx` - NEW component

---

### Phase 2: Task Monitoring & Status (HIGH PRIORITY)

**Current Issue**: After task execution, no way to monitor progress or see status.

**What's Needed**:

1. **Create TaskMonitor Page** (`/task-monitor/{execution_id}`):
   ```typescript
   export const TaskMonitor: React.FC = () => {
     const { executionId } = useParams();
     const { status, refetch } = useQuery({
       queryKey: ['execution', executionId],
       queryFn: () => fetch(`/api/v1/tasks-unified/executions/${executionId}/status`),
       refetchInterval: 5000 // Poll every 5 seconds
     });
     
     return (
       <Box>
         <StatusIndicator status={status.status} />
         <ProgressBar progress={status.progress} />
         <ExecutionDetails execution={status} />
         {status.status === 'completed' && <ViewResultsButton />}
       </Box>
     );
   };
   ```

2. **Status Display**:
   - Pending: Show queued message
   - Running: Show progress bar, estimated time remaining
   - Completed: Show success message, "View Results" button
   - Failed: Show error message, "Retry" button

3. **Real-time Updates**:
   - Poll status endpoint every 5 seconds while running
   - Stop polling when completed/failed
   - Show notification when status changes

**Files to Create**:
- `frontend/src/pages/TaskMonitor.tsx` - NEW page
- `frontend/src/components/task/StatusIndicator.tsx` - NEW component
- `frontend/src/hooks/useTaskExecution.ts` - NEW hook

**Routes to Add** (in `App.tsx`):
```typescript
<Route path="/task-monitor/:executionId" element={<TaskMonitor />} />
```

---

### Phase 3: Results Display (HIGH PRIORITY)

**Current Issue**: No way to view completed task results.

**What's Needed**:

1. **Create ResultsViewer Page** (`/task-results/{execution_id}`):
   ```typescript
   export const ResultsViewer: React.FC = () => {
     const { executionId } = useParams();
     const { data: results } = useQuery({
       queryKey: ['results', executionId],
       queryFn: () => fetch(`/api/v1/tasks-unified/executions/${executionId}/results`)
     });
     
     return (
       <Box>
         <ResultsSummary results={results} />
         <MolecularVisualization poses={results.poses} />
         <DownloadButtons files={results.output_files} />
         <DockingScores scores={results.scores} />
       </Box>
     );
   };
   ```

2. **GNINA-Specific Results**:
   ```typescript
   interface GNINAResults {
     job_id: string;
     status: string;
     poses: Array<{
       rank: number;
       score: number;
       pdb_data: string;
     }>;
     scores: {
       cnn_score: number;
       cnn_affinity: number;
     };
     output_files: {
       docked_ligand_url: string;
       log_file_url: string;
     };
   }
   ```

3. **3D Molecular Visualization**:
   ```typescript
   // Use 3Dmol.js (already in CSP headers)
   import $3Dmol from '3dmol';
   
   function MoleculeViewer({ pdbData }) {
     useEffect(() => {
       const viewer = $3Dmol.createViewer('viewer', {
         backgroundColor: 'white'
       });
       viewer.addModel(pdbData, 'pdb');
       viewer.setStyle({}, {cartoon: {color: 'spectrum'}});
       viewer.zoomTo();
       viewer.render();
     }, [pdbData]);
     
     return <div id="viewer" style={{height: '500px'}} />;
   }
   ```

4. **Download Functionality**:
   - Download docked poses (PDB/PDBQT)
   - Download log files
   - Download score spreadsheet (CSV)

**Files to Create**:
- `frontend/src/pages/TaskResults.tsx` - NEW page
- `frontend/src/components/results/MoleculeViewer.tsx` - NEW 3D viewer
- `frontend/src/components/results/DockingScores.tsx` - NEW scores table
- `frontend/src/components/results/DownloadButton.tsx` - NEW component

---

### Phase 4: Job Manager Integration (MEDIUM PRIORITY)

**Current Issue**: JobManager (`/job-manager`) doesn't show task framework executions.

**What's Needed**:

1. **Update JobManager to Query Unified Executions**:
   ```typescript
   const { data: executions } = useQuery({
     queryKey: ['executions'],
     queryFn: () => fetch('/api/v1/tasks-unified/executions?limit=50')
   });
   ```

2. **Add Execution Table**:
   ```typescript
   <DataGrid
     rows={executions}
     columns={[
       { field: 'execution_id', headerName: 'ID' },
       { field: 'task_id', headerName: 'Task' },
       { field: 'status', headerName: 'Status', renderCell: StatusBadge },
       { field: 'created_at', headerName: 'Created' },
       { field: 'actions', headerName: 'Actions', renderCell: ActionButtons }
     ]}
   />
   ```

3. **Action Buttons**:
   - View Status → Navigate to `/task-monitor/{execution_id}`
   - View Results → Navigate to `/task-results/{execution_id}` (if completed)
   - Cancel → Call cancel endpoint (if running)
   - Retry → Resubmit with same parameters (if failed)

**Files to Modify**:
- `frontend/src/pages/JobManager.tsx` - Add framework executions

---

### Phase 5: Backend Completion (MEDIUM PRIORITY)

**What's Needed**:

1. **Complete Missing Methods in UnifiedTaskService**:

   Currently stubbed (raises NotImplementedError):
   ```python
   async def _execute_database_task(...)
   ```
   
   **Solution**: Route to existing job creation system or implement separately

2. **Add Task Cancellation**:
   ```python
   @router.post("/api/v1/tasks-unified/executions/{execution_id}/cancel")
   async def cancel_execution(execution_id: str):
       execution = await unified_task_service.get_execution(execution_id)
       if execution.external_job_id:
           # Cancel via NeuroSnap API
           await task_framework.cancel_task(execution.task_id, execution.external_job_id)
       execution.update_status('cancelled')
       await save_execution(execution)
       return {"status": "cancelled"}
   ```

3. **Add Authentication/Authorization**:
   ```python
   # Replace placeholder auth functions
   def get_current_org_id() -> UUID:
       # Actual JWT/session validation
       token = request.headers.get('Authorization')
       user = decode_jwt(token)
       return user.org_id
   ```

4. **Add File Storage Integration**:
   ```python
   # Store uploaded files to storage service
   async def save_uploaded_file(file: UploadFile):
       file_path = f"/storage/uploads/{uuid4()}_{file.filename}"
       # Save to storage container
       return file_path
   ```

**Files to Modify**:
- `src/molecular_analysis_dashboard/services/unified_task_service.py`
- `src/molecular_analysis_dashboard/presentation/api/routes/unified_tasks.py`

---

### Phase 6: Testing & Validation (MEDIUM PRIORITY)

**What's Needed**:

1. **API Integration Tests**:
   ```python
   # tests/integration/test_gnina_workflow.py
   async def test_gnina_end_to_end():
       # 1. Get task details
       task = await client.get("/api/v1/tasks-unified/gnina-molecular-docking")
       assert task.status_code == 200
       
       # 2. Execute task
       with open("test_receptor.pdb", "rb") as receptor, \
            open("test_ligand.sdf", "rb") as ligand:
           response = await client.post(
               "/api/v1/tasks-unified/gnina-molecular-docking/execute",
               files={"receptor_file": receptor, "ligand_file": ligand},
               data={"job_name": "Test Job"}
           )
       assert response.status_code == 200
       execution_id = response.json()["execution_id"]
       
       # 3. Check status
       status = await client.get(f"/api/v1/tasks-unified/executions/{execution_id}/status")
       assert status.json()["status"] in ["pending", "running"]
       
       # 4. Wait for completion (mock)
       # 5. Get results
       # 6. Validate results structure
   ```

2. **Frontend E2E Tests**:
   ```typescript
   // tests/e2e/gnina-workflow.spec.ts
   test('complete GNINA workflow', async ({ page }) => {
     // Navigate to task library
     await page.goto('/task-library');
     
     // Find GNINA task
     await page.getByText('GNINA Molecular Docking').click();
     
     // Click Run Task
     await page.getByRole('button', { name: 'Run Task' }).click();
     
     // Upload files
     await page.setInputFiles('input[name="receptor_file"]', 'test_receptor.pdb');
     await page.setInputFiles('input[name="ligand_file"]', 'test_ligand.sdf');
     
     // Submit
     await page.getByRole('button', { name: 'Execute' }).click();
     
     // Check redirect to monitor page
     await expect(page).toHaveURL(/\/task-monitor\/.+/);
     
     // Verify status display
     await expect(page.getByText(/pending|running/i)).toBeVisible();
   });
   ```

---

## 📋 **IMPLEMENTATION PRIORITY**

### Sprint 1 (2-3 days): Core Execution
1. ✅ ~~Database & API setup~~ DONE
2. 🔨 Dynamic task execution form
3. 🔨 Task submission workflow
4. 🔨 Basic error handling

### Sprint 2 (2-3 days): Monitoring & Results
1. 🔨 Task monitoring page
2. 🔨 Status polling system
3. 🔨 Results display page
4. 🔨 3D molecular visualization

### Sprint 3 (1-2 days): Integration & Polish
1. 🔨 Job manager integration
2. 🔨 Authentication/authorization
3. 🔨 File storage integration
4. 🔨 Error handling improvements

### Sprint 4 (1-2 days): Testing & Documentation
1. 🔨 Integration tests
2. 🔨 E2E tests
3. 🔨 User documentation
4. 🔨 Performance optimization

---

## 🎯 **SUCCESS CRITERIA**

- [x] GNINA task visible in Task Library
- [x] API returns task details correctly
- [ ] User can upload receptor + ligand files
- [ ] Task execution creates database record
- [ ] User can monitor execution progress
- [ ] Results display with 3D visualization
- [ ] Job Manager shows all executions
- [ ] Error states handled gracefully
- [ ] Response time < 2s for all operations
- [ ] End-to-end workflow documented

---

## 📊 **Current Database Schema**

### task_framework_executions Table ✅
```sql
CREATE TABLE task_framework_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_definition_id UUID NOT NULL REFERENCES task_definitions(task_definition_id),
    org_id UUID REFERENCES organizations(org_id),
    user_id UUID REFERENCES users(user_id),
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    external_job_id VARCHAR(100),
    input_data JSONB NOT NULL DEFAULT '{}',
    output_data JSONB,
    error_message TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    extra_metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_task_framework_executions_org ON task_framework_executions(org_id);
CREATE INDEX idx_task_framework_executions_user ON task_framework_executions(user_id);
CREATE INDEX idx_task_framework_executions_status ON task_framework_executions(status);
CREATE INDEX idx_task_framework_executions_created ON task_framework_executions(created_at DESC);
CREATE INDEX idx_task_framework_executions_external_job ON task_framework_executions(external_job_id);
```

### GNINA Task Definition ✅

### GNINA Task Definition ✅
```sql
-- Already seeded in database
SELECT task_id, version, task_metadata->>'name' as name
FROM task_definitions 
WHERE task_id = 'gnina-molecular-docking';

-- Returns:
-- task_id: gnina-molecular-docking
-- version: 1.0.0  
-- name: GNINA Molecular Docking
```

---

## 🔧 **API Endpoints Status**

### Implemented ✅
- `GET /api/v1/tasks-unified/available` - List all tasks (database + framework)
- `GET /api/v1/tasks-unified/health` - Health check
- `GET /api/v1/tasks-unified/{task_id}` - Get task details
- `POST /api/v1/tasks-unified/{task_id}/execute` - Execute task
- `GET /api/v1/tasks-unified/executions/{id}/status` - Get execution status
- `GET /api/v1/tasks-unified/executions/{id}/results` - Get execution results
- `GET /api/v1/tasks-unified/executions` - List user executions

### Not Yet Implemented ⏳
- `POST /api/v1/tasks-unified/executions/{id}/cancel` - Cancel execution
- `POST /api/v1/tasks-unified/{task_id}/validate` - Validate parameters before execution
- `GET /api/v1/tasks-unified/executions/{id}/logs` - Stream execution logs

---

## 🎨 **Frontend Components Status**

### Existing ✅
- `TaskLibrary.tsx` - Shows tasks, updated to navigate correctly
- `ExecuteTasks.tsx` - Exists but hardcoded for specific workflow
- `JobManager.tsx` - Exists but doesn't show framework executions
- `taskService.ts` - Fetches from unified API correctly

### Needs Creation 🆕
- `DynamicTaskForm.tsx` - Generic form generator from task parameters
- `FileUploadField.tsx` - File upload component with validation
- `TaskMonitor.tsx` - Real-time execution monitoring page
- `TaskResults.tsx` - Results display with 3D visualization
- `MoleculeViewer.tsx` - 3Dmol.js integration for structure viewing
- `StatusIndicator.tsx` - Visual status badges
- `useTaskExecution.ts` - React hook for task execution state

---

## 💾 **File Storage Integration**

**Current Gap**: Uploaded files (receptor.pdb, ligand.sdf) need proper handling.

**Required Implementation**:

1. **Storage Service Integration**:
   ```python
   # In unified_task_service.py
   async def _store_uploaded_file(self, file: UploadFile, org_id: UUID) -> str:
       """Save file to storage service and return URL"""
       file_id = uuid4()
       storage_path = f"/storage/uploads/{org_id}/{file_id}_{file.filename}"
       
       # Save to storage container
       async with aiofiles.open(storage_path, 'wb') as f:
           content = await file.read()
           await f.write(content)
       
       # Return accessible URL
       return f"http://storage:8080/uploads/{org_id}/{file_id}_{file.filename}"
   ```

2. **Update Execute Endpoint**:
   ```python
   # Store files and pass URLs to NeuroSnap
   receptor_url = await unified_task_service._store_uploaded_file(receptor_file, org_id)
   ligand_url = await unified_task_service._store_uploaded_file(ligand_file, org_id)
   
   # Pass URLs to NeuroSnap instead of file content
   result = await task_framework.execute_task(task_id, {
       "receptor_url": receptor_url,
       "ligand_url": ligand_url,
       "job_name": job_name
   })
   ```

---

## 🔐 **Authentication & Authorization**

**Current State**: Placeholder functions returning `None`

**Required Implementation**:

1. **JWT Token Validation**:
   ```python
   from fastapi import Depends, HTTPException
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   
   security = HTTPBearer()
   
   async def get_current_user(
       credentials: HTTPAuthorizationCredentials = Depends(security)
   ) -> User:
       token = credentials.credentials
       payload = decode_jwt(token)
       user = await db.get_user(payload['user_id'])
       if not user:
           raise HTTPException(status_code=401, detail="Invalid token")
       return user
   
   async def get_current_org_id(user: User = Depends(get_current_user)) -> UUID:
       return user.org_id
   
   async def get_current_user_id(user: User = Depends(get_current_user)) -> UUID:
       return user.user_id
   ```

2. **Permission Checks**:
   ```python
   async def check_execution_access(
       execution_id: UUID,
       user: User = Depends(get_current_user)
   ):
       execution = await db.get_execution(execution_id)
       if execution.user_id != user.user_id and user.role != 'admin':
           raise HTTPException(status_code=403, detail="Access denied")
       return execution
   ```

---

## 🔄 **NeuroSnap API Integration Details**

**Current Implementation**:
- `TaskExecutionService` in `neurosnap_task_adapter.py`
- Methods: `get_available_tasks()`, `execute_task()`, `get_task_status()`, `get_task_results()`

**Enhancement Needed**:

1. **Error Handling**:
   ```python
   async def execute_task(self, task_id: str, parameters: Dict, files: Optional[Dict]) -> Dict:
       try:
           response = await self.neurosnap_client.submit_job(...)
           return response
       except NeuroSnapAPIError as e:
           logger.error(f"NeuroSnap API error: {e}")
           raise HTTPException(status_code=502, detail=f"External service error: {str(e)}")
       except TimeoutError:
           raise HTTPException(status_code=504, detail="External service timeout")
   ```

2. **Retry Logic**:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=4, max=10)
   )
   async def get_task_status(self, task_id: str, job_id: str) -> Dict:
       return await self.neurosnap_client.get_status(job_id)
   ```

3. **Webhook Support** (Optional):
   ```python
   @router.post("/api/v1/webhooks/neurosnap/{execution_id}")
   async def neurosnap_webhook(execution_id: UUID, payload: Dict):
       """Receive status updates from NeuroSnap"""
       execution = await db.get_execution(execution_id)
       execution.update_status(payload['status'])
       if payload['status'] == 'completed':
           execution.output_data = payload['results']
       await db.save(execution)
       return {"status": "ok"}
   ```

---

## 📈 **Performance Considerations**

1. **Caching**:
   ```python
   from functools import lru_cache
   from datetime import timedelta
   
   @lru_cache(maxsize=100)
   async def get_task_definition(task_id: str) -> TaskDefinition:
       # Cache task definitions for 1 hour
       return await db.query(TaskDefinition).filter_by(task_id=task_id).first()
   ```

2. **Database Connection Pooling**:
   ```python
   # Already configured in infrastructure/database.py
   # But verify pool size is adequate:
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=20,  # Increase if needed
       max_overflow=40,
       pool_pre_ping=True
   )
   ```

3. **Background Task Processing**:
   ```python
   from fastapi import BackgroundTasks
   
   @router.post("/{task_id}/execute")
   async def execute_task(
       background_tasks: BackgroundTasks,
       ...
   ):
       # Submit execution
       execution = await create_execution(...)
       
       # Poll status in background
       background_tasks.add_task(poll_execution_status, execution.execution_id)
       
       return execution
   ```

---

## 🧪 **Testing Files Needed**

### Backend Tests
```
tests/
├── integration/
│   ├── test_unified_task_service.py
│   ├── test_gnina_workflow.py
│   └── test_task_execution_api.py
├── unit/
│   ├── test_task_adapters.py
│   └── test_parameter_validation.py
└── fixtures/
    ├── test_receptor.pdb
    └── test_ligand.sdf
```

### Frontend Tests  
```
frontend/tests/
├── e2e/
│   ├── gnina-workflow.spec.ts
│   └── task-monitoring.spec.ts
├── integration/
│   ├── task-execution.test.tsx
│   └── results-display.test.tsx
└── unit/
    ├── DynamicTaskForm.test.tsx
    └── MoleculeViewer.test.tsx
```

---

## 📝 **Documentation Needed**

1. **User Guide**: How to execute GNINA tasks
2. **API Documentation**: OpenAPI/Swagger for unified-tasks endpoints
3. **Developer Guide**: How to add new task types
4. **Troubleshooting**: Common errors and solutions

---

## 🚀 **Quick Start Guide** (After Full Implementation)

```bash
# 1. Start services
docker-compose up -d

# 2. Access dashboard
open http://localhost/task-library

# 3. Run GNINA task
# - Click "GNINA Molecular Docking"
# - Click "Run Task"
# - Upload receptor.pdb and ligand.sdf
# - Enter job name
# - Click "Execute"
# - Monitor progress at /task-monitor/{id}
# - View results at /task-results/{id}
```

---

## ⚡ **Next Immediate Actions**

### This Week:
1. Create `DynamicTaskForm.tsx` component
2. Update `ExecuteTasks.tsx` to use query parameter
3. Implement file upload handling
4. Test task submission end-to-end

### Next Week:
1. Create `TaskMonitor.tsx` page
2. Implement status polling
3. Create `TaskResults.tsx` page  
4. Integrate 3Dmol.js for visualization

### Following Week:
1. Update `JobManager.tsx`
2. Add authentication
3. Add integration tests
4. Write user documentation