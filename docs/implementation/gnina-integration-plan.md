# GNINA Task Framework & Pipeline Builder Integration Plan

**Last Updated**: November 13, 2025  
**Current Status**: ✅ Core Integration Complete | ⚠️ Results UI Pending  

> **⚠️ IMPORTANT**: This document contains the original integration plan.  
> **For current implementation status**, see: `integration-summary.md`  
> 
> **Recent Major Updates (Nov 12-13, 2025)**:
> - ✅ Celery background polling implemented (10-second intervals)
> - ✅ ExecutionFileService with hybrid storage (local + external URLs)
> - ✅ execution_files table for file metadata (no base64 in database)
> - ✅ Real-time job monitoring in JobManager
> - ✅ Files stored to /storage/uploads/ via storage service
> - ⚠️ Results visualization UI pending (backend ready)

## 📋 **PROJECT CONTEXT & STRATEGIC DIRECTION**

### Architecture Decision ✅
- **Task Storage**: Framework tasks (code-based) in `neurosnap_task_adapter.py`
- **Rationale**: Same tasks for all organizations, only developers add new tasks
- **Database Role**: `task_definitions` table NOT used for framework tasks (by design)
- **File Storage**: Hybrid model - local files in storage service + external NeuroSnap URLs
- **Background Processing**: Celery workers for status polling and task execution
- **Primary Focus**: Single task execution complete → Results UI → Pipeline builder

### User Requirements ✅
1. ✅ Tasks shared across all organizations (no org-specific tasks)
2. ✅ Only developers add new computational services (no dynamic registration UI)
3. 🔄 Non-developers create multi-step workflows via visual pipeline builder
4. ✅ Execution data is org-isolated (but tasks remain shared)
5. 🔄 Nextflow executes workflows in background
6. **Current Priority**: Complete results UI → Pipeline builder

### Implementation Status Summary (Nov 13, 2025)

**✅ Completed (Production Ready)**:
- Task execution with file uploads
- Background status polling (Celery)
- Real-time job monitoring
- File storage service integration
- Database schema (executions + files)
- API endpoints for tasks & executions

**⚠️ In Progress (Estimated 8-12 hours)**:
- Store result file metadata in execution_files table (1-2 hrs)
- TaskResults.tsx visualization component (3-4 hrs)
- Navigation from JobManager to Results (30 min)
- File download service in frontend (1-2 hrs)
- End-to-end testing (2-3 hrs)

**📅 Future Work (Weeks 3-8)**:
- Visual pipeline builder (React Flow)
- Nextflow script generation
- Pipeline execution engine
- Template gallery & sharing

### What We're NOT Building
- ❌ Dynamic task registration UI (developers add tasks via code)
- ❌ Per-organization custom tasks (same tasks for all orgs)
- ❌ Database-driven task definitions (framework tasks sufficient)
- ❌ Task marketplace or task discovery features

### What We ARE Building (Priority Order)
1. **Visual Pipeline Builder** (PRIMARY FOCUS - Week 3-6)
2. **Single Task Execution** (Foundation - Week 1-2)
3. **Pipeline Execution Engine** (Core Value - Week 5-6)
4. **Template Gallery** (User Experience - Week 7-8)

---

## ✅ **COMPLETED WORK**

### Database Integration ✅
- [x] Created `task_framework_executions` table (migration `20251111_2150_80835240e483`)
- [x] Created `execution_files` table for file metadata (migration `20250112_execution_files.py`)
- [x] Created `pipeline_templates`, `pipeline_executions`, `pipeline_step_results` tables (SQL migration `20251112_pipeline_builder.sql`)
- [x] `task_definitions` table exists but unused (framework tasks bypass database - **by design**)
- [x] Added indexes for performance (org_id, user_id, status, created_at, external_job_id)
- [x] PostgreSQL exposed on port 5432 for external pgAdmin access
- [x] Fixed alembic migration chain (corrected down_revision from '17e8ba7cf10e' to '001_meta')
- [x] Removed duplicate/malformed migrations

### Backend API ✅
- [x] Created `UnifiedTaskService` combining database + framework tasks
- [x] Created `ExecutionFileService` for hybrid file storage (local + external URLs)
- [x] Framework tasks in `neurosnap_task_adapter.py` (`get_available_tasks()` returns GNINA)
- [x] Implemented `/api/v1/tasks-unified/available` endpoint
- [x] Implemented `/api/v1/tasks-unified/health` endpoint
- [x] Implemented `/api/v1/tasks-unified/{task_id}` get task details
- [x] Implemented `/api/v1/tasks-unified/{task_id}/execute` endpoint with file uploads
- [x] Implemented `/api/v1/tasks-unified/executions/{id}/status` endpoint (used by polling)
- [x] Implemented `/api/v1/tasks-unified/executions/{id}/results` endpoint
- [x] Implemented `/api/v1/tasks-unified/executions` list user executions
- [x] Fixed async database patterns (AsyncGenerator instead of context manager)
- [x] Standardized response format ('id' field instead of 'task_id')
- [x] File storage: NO base64 encoding, only metadata in database

### Background Processing ✅
- [x] Celery workers configured and running
- [x] Redis message broker integration
- [x] `poll_job_status()` task polls internal API every 10 seconds
- [x] Synchronous HTTP calls (no async in Celery workers)
- [x] Auto-scheduling for non-terminal job states
- [x] Polling stops on completion/failure/cancellation
- [x] Tested with live jobs - successfully updated stuck jobs to completed

### File Storage ✅
- [x] Storage service (nginx) running on port 8080
- [x] Files stored to `/storage/uploads/{org_id}/{execution_id}/`
- [x] ExecutionFileService.store_input_file() implemented
- [x] ExecutionFileService.store_output_file() implemented (for NeuroSnap URLs)
- [x] ExecutionFileService.get_execution_files() implemented
- [x] ExecutionFileService.get_file_content() implemented
- [x] MD5 + SHA256 integrity checks
- [x] Hybrid storage: Local files + external NeuroSnap URLs

### Frontend Integration ✅
- [x] Updated `taskService.ts` to use `/api/v1/tasks-unified/available`
- [x] Fixed health check endpoint to use absolute path
- [x] Enabled `useApiTasks` feature flag by default
- [x] Task Library displays GNINA tasks from API
- [x] API health status shows "Healthy"
- [x] Updated navigation from `/jobs/create` to `/execute-tasks`
- [x] JobManager displays real-time execution data
- [x] Auto-refresh every 5 seconds in JobManager
- [x] Status badges and progress indicators
- [x] Fixed frontend .env.production for Docker deployment

### Infrastructure ✅
- [x] Docker services rebuilt and running (api, frontend, gateway, postgres, redis, worker, storage)
- [x] Gateway routes configured (/api/* → api:8000, /* → frontend)
- [x] Storage service configured (nginx serving /storage/uploads/)
- [x] All containers healthy
- [x] Gateway DNS resolution working (after restart fix)
- [x] Local PostgreSQL@14 stopped to avoid port 5432 conflicts
- [x] All migrations executed successfully

### Architecture Analysis ✅
- [x] Documented dual-track task system (framework vs database) in `CURRENT_SYSTEM_ANALYSIS.md`
- [x] Documented storage architecture fix in `storage-architecture-fix.md`
- [x] Documented complete integration in `integration-summary.md`
- [x] Confirmed framework tasks appropriate for user requirements
- [x] Designed pipeline builder schema with React Flow + Nextflow support
- [x] Clean Architecture with Ports & Adapters pattern validated

---

## 🔄 **REMAINING WORK - UPDATED ROADMAP**

### **Current Priority: Results Visualization (Week 1-2)**

**Goal**: Complete the results viewing workflow so users can see and download job outputs.

#### Phase 1A: Dynamic Task Execution Form ✅ COMPLETED
**Status**: ✅ Fully functional - users can submit GNINA tasks with file uploads

**What Was Implemented**:

1. ✅ **Updated ExecuteTasks.tsx** to be task-agnostic:
   - Reads `task_id` from query parameter (`?task=gnina-molecular-docking`)
   - Fetches task details from `/api/v1/tasks-unified/{task_id}` API
   - Dynamically generates form using `DynamicTaskForm` component
   - 3-step wizard: Configure → Review → Execute → Success

2. ✅ **Created DynamicTaskForm.tsx** component:
   - Generic form generator supporting all parameter types
   - Handles: file, string, number, integer, boolean, select/enum
   - Built-in validation (required, min/max, pattern, allowed_values)
   - Error display and field-level error messages

3. ✅ **Created FileUploadField.tsx** component:
   - Drag-and-drop file upload with visual feedback
   - File validation (type: .pdb/.sdf/.pdbqt, max size: 100MB)
   - File preview with name and size display
   - Remove file functionality

4. ✅ **Fixed Backend API Issues**:
   - **File Storage**: Files stored via ExecutionFileService to /storage/uploads/
   - **Duplicate Tasks**: Fixed by prioritizing framework tasks over database tasks
   - **Database Constraints**: Created system organization and user (UUID: `00000000-0000-0000-0000-000000000000`)
   - **Model Field Mismatches**: Fixed `TaskFrameworkExecution` to use correct fields
   - **File Handling**: Files stored to storage service, only metadata in database

5. ✅ **API Endpoints Working**:
   - `GET /api/v1/tasks-unified/available` - Returns GNINA tasks (framework source)
   - `GET /api/v1/tasks-unified/{task_id}` - Returns task details with parameters
   - `POST /api/v1/tasks-unified/{task_id}/execute` - Accepts FormData with files
   - Successfully submitted test jobs with file uploads

3. ✅ **Created FileUploadField.tsx** component:
   - Drag-and-drop file upload with visual feedback
   - File validation (type: .pdb/.sdf/.pdbqt, max size: 100MB)
   - File preview with name and size display
   - Remove file functionality

4. ✅ **Fixed Backend API Issues**:
   - **File Content Loss**: Fixed by storing file content as base64 in `input_data`
   - **Duplicate Tasks**: Fixed by prioritizing framework tasks over database tasks
   - **Database Constraints**: Created system organization and user (UUID: `00000000-0000-0000-0000-000000000000`)
   - **Model Field Mismatches**: Fixed `TaskFrameworkExecution` to use correct fields (`task_id`, `display_name`, `input_data`)
   - **Adapter Signature**: Fixed to decode base64 file content before submitting to NeuroSnap

5. ✅ **API Endpoints Working**:
   - `GET /api/v1/tasks-unified/available` - Returns 1 GNINA task (framework source)
   - `GET /api/v1/tasks-unified/{task_id}` - Returns task details with parameters
   - `POST /api/v1/tasks-unified/{task_id}/execute` - Accepts FormData with files
   - Successfully submitted test job: `execution_id: ff7a09e4-e365-4165-8cb8-befdb31ea362`, `job_id: 6914d0ed8b9522d6ffefa776`

**Test Results**:
```bash
curl -X POST \
  -F "receptor_file=@EGFR_KD_L858R_T790M_model_1.pdb" \
  -F "ligand_file=@erlotinib.sdf" \
  -F "exhaustiveness=2" \
  http://localhost/api/v1/tasks-unified/gnina-molecular-docking/execute
# Response: {"execution_id": "...", "job_id": "...", "status": "running", ...}
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
```

**Next Steps**: Phase 1B - Task Monitoring & Status

---

#### Phase 1B: Task Monitoring & Status ✅ COMPLETED
**Status**: ✅ Fully functional - users can monitor job executions in real-time

**What Was Implemented**:

1. ✅ **Updated JobManager.tsx** to show real task executions:
   - Removed mock data insertion (disabled WebSocket mock animation)
   - Integrated with `/api/v1/tasks-unified/executions` API endpoint
   - Displays real execution data from database (9 GNINA jobs)
   - Shows "Live Data" green chip instead of "Offline Mode"
   - Auto-refreshes every 10 seconds using TanStack Query

2. ✅ **Real-time Status Display**:
   - Status badges: Pending, Running, Completed, Failed, Cancelled
   - Progress bars showing completion percentage
   - Runtime calculation from started_at and completed_at timestamps
   - Task type display (gnina-molecular-docking)

3. ✅ **View Details Dialog** with real data:
   - **Overview Tab**: Job ID, task type, priority, progress, runtime
   - **Parameters Tab**: JSON display of input_data from execution
   - **Files Tab**: Real input/output files from `/results` endpoint
     - Input files: Input_Ligand.json (7.81 KB), Input_Receptor.zip (38.24 KB)
     - Output files: output.csv (597 bytes), output.sdf (45.28 KB)
     - Download buttons with actual URLs from NeuroSnap API
   - **Logs Tab**: Error messages and execution logs
   - **Resources Tab**: Placeholder for CPU/memory metrics

4. ✅ **Enhanced File Integration**:
   - Changed inputFiles/outputFiles from `string[]` to objects:
     ```typescript
     interface FileInfo {
       name: string;
       size: string;
       url?: string; // Download URL from NeuroSnap
     }
     ```
   - Fetches file details from `/executions/{id}/results` endpoint
   - Parses `raw_data.in` for input files
   - Parses `raw_data.out` for output files with sizes
   - Displays file names, sizes, and clickable download buttons

5. ✅ **API Endpoints Working**:
   - `GET /api/v1/tasks-unified/executions` - Lists all user executions
   - `GET /api/v1/tasks-unified/executions/{id}/status` - Job status details
   - `GET /api/v1/tasks-unified/executions/{id}/results` - File URLs and metadata

**Test Results**:
```bash
# List executions
curl http://localhost:8000/api/v1/tasks-unified/executions
# Returns: 9 executions with full details

# Get execution status
curl http://localhost:8000/api/v1/tasks-unified/executions/ff7a09e4-.../status
# Returns: status, progress, timestamps, framework_status

# Get execution results  
curl http://localhost:8000/api/v1/tasks-unified/executions/ff7a09e4-.../results
# Returns: files[], download_urls{}, raw_data with input/output file info
```

**Next Steps**: Phase 1C - Enhanced Results Display with 3D Visualization

---

#### Phase 1C: Results Display & Visualization

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

### WEEK 3-4: Visual Pipeline Builder UI (PRIMARY FOCUS)

**Goal**: Drag-drop canvas for creating multi-step workflows using framework tasks as building blocks.

#### Phase 2A: React Flow Integration

**What's Needed**:

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install reactflow
   ```

2. **Create PipelineBuilder Page** (`/pipeline-builder`):
   ```typescript
   import ReactFlow, { 
     Background, 
     Controls, 
     MiniMap, 
     addEdge, 
     useNodesState, 
     useEdgesState 
   } from 'reactflow';
   import 'reactflow/dist/style.css';
   
   export const PipelineBuilder: React.FC = () => {
     const [nodes, setNodes, onNodesChange] = useNodesState([]);
     const [edges, setEdges, onEdgesChange] = useEdgesState([]);
     
     const onConnect = (params) => setEdges((eds) => addEdge(params, eds));
     
     return (
       <Box sx={{ height: '100vh', display: 'flex' }}>
         <TaskPalette onTaskDrag={handleTaskDrag} />
         <ReactFlow
           nodes={nodes}
           edges={edges}
           onNodesChange={onNodesChange}
           onEdgesChange={onEdgesChange}
           onConnect={onConnect}
         >
           <Background />
           <Controls />
           <MiniMap />
         </ReactFlow>
         <PipelineToolbar onSave={savePipeline} onExecute={executePipeline} />
       </Box>
     );
   };
   ```

3. **Create TaskPalette Component**:
   ```typescript
   export const TaskPalette: React.FC = () => {
     const { data: tasks } = useTasks(); // Fetch from /api/v1/tasks-unified/available
     
     return (
       <Box sx={{ width: 250, borderRight: 1, p: 2 }}>
         <Typography variant="h6">Available Tasks</Typography>
         {tasks.map(task => (
           <TaskCard
             key={task.task_id}
             task={task}
             draggable
             onDragStart={(e) => {
               e.dataTransfer.setData('application/reactflow', JSON.stringify(task));
               e.dataTransfer.effectAllowed = 'move';
             }}
           />
         ))}
       </Box>
     );
   };
   ```

4. **Custom Task Node Component**:
   ```typescript
   const TaskNode = ({ data }) => {
     return (
       <Box sx={{ 
         border: 2, 
         borderRadius: 2, 
         p: 2, 
         bgcolor: 'white',
         minWidth: 200
       }}>
         <Typography variant="subtitle2">{data.label}</Typography>
         <Typography variant="caption" color="text.secondary">
           {data.task_id}
         </Typography>
         <Handle type="target" position="top" />
         <Handle type="source" position="bottom" />
       </Box>
     );
   };
   
   const nodeTypes = { taskNode: TaskNode };
   ```

**Files to Create**:
- `frontend/src/pages/PipelineBuilder.tsx` - NEW page
- `frontend/src/components/pipeline/TaskPalette.tsx` - NEW component
- `frontend/src/components/pipeline/TaskNode.tsx` - NEW custom node
- `frontend/src/components/pipeline/PipelineToolbar.tsx` - NEW toolbar

---

#### Phase 2B: Parameter Configuration & Validation

**What's Needed**:

1. **Node Configuration Modal**:
   ```typescript
   export const NodeConfigModal: React.FC<{ node, onSave }> = ({ node, onSave }) => {
     const [parameters, setParameters] = useState(node.data.parameters || {});
     
     return (
       <Dialog open={!!node}>
         <DialogTitle>Configure {node.data.label}</DialogTitle>
         <DialogContent>
           <DynamicTaskForm
             parameters={node.data.task.parameters}
             values={parameters}
             onChange={setParameters}
             allowFileUpload={false} // Files handled per execution, not per template
           />
         </DialogContent>
         <DialogActions>
           <Button onClick={onClose}>Cancel</Button>
           <Button onClick={() => onSave(parameters)}>Save</Button>
         </DialogActions>
       </Dialog>
     );
   };
   ```

2. **Edge Validation** (Ensure output → input compatibility):
   ```typescript
   const isValidConnection = (connection) => {
     const sourceNode = nodes.find(n => n.id === connection.source);
     const targetNode = nodes.find(n => n.id === connection.target);
     
     // Check if source output type matches target input type
     const sourceOutput = sourceNode.data.task.outputs;
     const targetInput = targetNode.data.task.parameters;
     
     // Validate compatibility
     return validateTypeCompatibility(sourceOutput, targetInput);
   };
   ```

3. **Parameter Mapping UI**:
   ```typescript
   // When connecting nodes, allow mapping outputs to inputs
   <EdgeConfigDialog
     sourceNode={sourceNode}
     targetNode={targetNode}
     onSave={saveParameterMapping}
   />
   ```

**Files to Create**:
- `frontend/src/components/pipeline/NodeConfigModal.tsx` - NEW modal
- `frontend/src/components/pipeline/EdgeConfigDialog.tsx` - NEW dialog
- `frontend/src/utils/pipelineValidation.ts` - NEW validation logic

---

#### Phase 2C: Template Saving & Loading

**What's Needed**:

1. **Backend API - Pipeline Templates**:
   ```python
   @router.post("/api/v1/pipelines/templates")
   async def create_pipeline_template(
       template: PipelineTemplateCreate,
       org_id: UUID = Depends(get_current_org_id),
       user_id: UUID = Depends(get_current_user_id)
   ):
       # Save to pipeline_templates table
       pipeline_id = await db.execute(
           """
           INSERT INTO pipeline_templates 
           (name, description, template_data, created_by, org_id, is_public)
           VALUES ($1, $2, $3, $4, $5, $6)
           RETURNING pipeline_id
           """,
           template.name,
           template.description,
           json.dumps(template.template_data),
           user_id,
           org_id,
           template.is_public
       )
       return {"pipeline_id": pipeline_id}
   
   @router.get("/api/v1/pipelines/templates")
   async def list_pipeline_templates(org_id: UUID = Depends(get_current_org_id)):
       # Fetch templates for org + public templates
       templates = await db.fetch(
           """
           SELECT * FROM pipeline_templates 
           WHERE org_id = $1 OR is_public = TRUE
           ORDER BY created_at DESC
           """,
           org_id
       )
       return templates
   
   @router.get("/api/v1/pipelines/templates/{pipeline_id}")
   async def get_pipeline_template(pipeline_id: UUID):
       template = await db.fetchrow(
           "SELECT * FROM pipeline_templates WHERE pipeline_id = $1",
           pipeline_id
       )
       return template
   ```

2. **Frontend - Save Pipeline**:
   ```typescript
   const savePipeline = async () => {
     const templateData = {
       nodes: nodes,
       edges: edges,
       viewport: reactFlowInstance.getViewport()
     };
     
     await fetch('/api/v1/pipelines/templates', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         name: pipelineName,
         description: pipelineDescription,
         template_data: templateData,
         is_public: isPublic
       })
     });
   };
   ```

3. **Frontend - Load Pipeline**:
   ```typescript
   const loadPipeline = async (pipelineId: string) => {
     const response = await fetch(`/api/v1/pipelines/templates/${pipelineId}`);
     const template = await response.json();
     
     setNodes(template.template_data.nodes);
     setEdges(template.template_data.edges);
     reactFlowInstance.setViewport(template.template_data.viewport);
   };
   ```

**Files to Create**:
- `src/molecular_analysis_dashboard/presentation/api/routes/pipeline_templates.py` - NEW API routes
- `frontend/src/services/pipelineService.ts` - NEW service
- `frontend/src/components/pipeline/SavePipelineDialog.tsx` - NEW dialog
- `frontend/src/pages/PipelineGallery.tsx` - NEW template gallery page

---

### WEEK 5-6: Nextflow Integration & Execution Engine (CORE VALUE)

**Goal**: Convert React Flow graphs to Nextflow scripts and execute multi-step workflows.

#### Phase 3A: Nextflow Script Generator

**What's Needed**:

1. **Backend - Nextflow Generator Service**:
   ```python
   # src/molecular_analysis_dashboard/services/nextflow_generator.py
   
   class NextflowScriptGenerator:
       def generate_script(self, pipeline_data: Dict) -> str:
           """
           Convert React Flow graph to Nextflow DSL
           
           Input: { "nodes": [...], "edges": [...] }
           Output: Nextflow script string
           """
           script_lines = [
               "#!/usr/bin/env nextflow",
               "nextflow.enable.dsl=2",
               ""
           ]
           
           # Generate process for each node
           for node in pipeline_data['nodes']:
               script_lines.extend(self._generate_process(node))
           
           # Generate workflow
           script_lines.append("workflow {")
           
           # Build execution graph from edges
           execution_order = self._topological_sort(
               pipeline_data['nodes'],
               pipeline_data['edges']
           )
           
           for step in execution_order:
               script_lines.append(f"    {step}")
           
           script_lines.append("}")
           
           return "\n".join(script_lines)
       
       def _generate_process(self, node: Dict) -> List[str]:
           task_id = node['data']['task_id']
           node_id = node['id']
           params = node['data']['parameters']
           
           return [
               f"process {node_id} {{",
               f"    container '{self._get_container_image(task_id)}'",
               f"    publishDir 'results/{node_id}', mode: 'copy'",
               f"    ",
               f"    input:",
               f"    path input_files",
               f"    ",
               f"    output:",
               f"    path 'output/*'",
               f"    ",
               f"    script:",
               f"    \"\"\"",
               f"    {self._generate_task_command(task_id, params)}",
               f"    \"\"\"",
               f"}}",
               f""
           ]
       
       def _generate_task_command(self, task_id: str, params: Dict) -> str:
           if task_id == 'gnina-molecular-docking':
               return f"""
               gnina -r ${{input_files[0]}} \\
                     -l ${{input_files[1]}} \\
                     -o output/docked.pdbqt \\
                     --cnn_scoring rescore \\
                     --num_modes {params.get('num_modes', 10)}
               """
           # Add more task types as needed
           return ""
       
       def _topological_sort(self, nodes: List, edges: List) -> List[str]:
           # Implement topological sort for execution order
           # Return list of Nextflow channel operations
           pass
   ```

2. **Backend - Pipeline Execution Endpoint**:
   ```python
   @router.post("/api/v1/pipelines/{pipeline_id}/execute")
   async def execute_pipeline(
       pipeline_id: UUID,
       execution_params: PipelineExecutionParams,
       org_id: UUID = Depends(get_current_org_id),
       user_id: UUID = Depends(get_current_user_id),
       background_tasks: BackgroundTasks
   ):
       # 1. Load pipeline template
       template = await db.fetchrow(
           "SELECT * FROM pipeline_templates WHERE pipeline_id = $1",
           pipeline_id
       )
       
       # 2. Generate Nextflow script
       generator = NextflowScriptGenerator()
       nf_script = generator.generate_script(template['template_data'])
       
       # 3. Create execution record
       execution_id = await db.execute(
           """
           INSERT INTO pipeline_executions 
           (pipeline_id, org_id, user_id, status, nextflow_script, input_params)
           VALUES ($1, $2, $3, 'pending', $4, $5)
           RETURNING execution_id
           """,
           pipeline_id, org_id, user_id, nf_script, json.dumps(execution_params)
       )
       
       # 4. Execute Nextflow in background
       background_tasks.add_task(
           execute_nextflow_pipeline,
           execution_id,
           nf_script,
           execution_params
       )
       
       return {"execution_id": execution_id, "status": "pending"}
   ```

3. **Nextflow Executor**:
   ```python
   async def execute_nextflow_pipeline(
       execution_id: UUID,
       nf_script: str,
       params: Dict
   ):
       # 1. Create temp directory for execution
       work_dir = f"/tmp/pipelines/{execution_id}"
       os.makedirs(work_dir, exist_ok=True)
       
       # 2. Write Nextflow script
       script_path = f"{work_dir}/pipeline.nf"
       with open(script_path, 'w') as f:
           f.write(nf_script)
       
       # 3. Prepare input files
       # Copy uploaded files to work_dir
       
       # 4. Execute Nextflow
       process = await asyncio.create_subprocess_exec(
           'nextflow', 'run', script_path,
           '-work-dir', f'{work_dir}/work',
           stdout=asyncio.subprocess.PIPE,
           stderr=asyncio.subprocess.PIPE
       )
       
       # 5. Stream output and update status
       async for line in process.stdout:
           await update_pipeline_log(execution_id, line.decode())
       
       # 6. Wait for completion
       await process.wait()
       
       # 7. Update final status
       if process.returncode == 0:
           await update_pipeline_status(execution_id, 'completed')
           await collect_results(execution_id, work_dir)
       else:
           stderr = await process.stderr.read()
           await update_pipeline_status(
               execution_id, 
               'failed', 
               error_message=stderr.decode()
           )
   ```

**Files to Create**:
- `src/molecular_analysis_dashboard/services/nextflow_generator.py` - NEW script generator
- `src/molecular_analysis_dashboard/services/nextflow_executor.py` - NEW executor
- `src/molecular_analysis_dashboard/presentation/api/routes/pipeline_executions.py` - NEW API routes

---

#### Phase 3B: Step-by-Step Progress Tracking

**What's Needed**:

1. **Parse Nextflow Output**:
   ```python
   def parse_nextflow_log(log_line: str) -> Optional[StepUpdate]:
       # Parse Nextflow stdout for step completion
       # Example: [TaskName] Submitted process > step_1 (1)
       # Example: [TaskName] Completed process > step_1 (1)
       
       if match := re.match(r'\[(.+?)\] (Submitted|Completed) process > (\w+)', log_line):
           task_name, status, step_id = match.groups()
           return StepUpdate(
               step_id=step_id,
               status='running' if status == 'Submitted' else 'completed',
               timestamp=datetime.now()
           )
       return None
   ```

2. **Update Step Results Table**:
   ```python
   async def update_step_status(execution_id: UUID, step_update: StepUpdate):
       await db.execute(
           """
           INSERT INTO pipeline_step_results 
           (execution_id, step_number, task_id, status, started_at, completed_at)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (execution_id, step_number)
           DO UPDATE SET 
               status = EXCLUDED.status,
               completed_at = EXCLUDED.completed_at
           """,
           execution_id,
           step_update.step_number,
           step_update.task_id,
           step_update.status,
           step_update.started_at,
           step_update.completed_at
       )
   ```

3. **Frontend - Progress Visualization**:
   ```typescript
   export const PipelineProgress: React.FC<{ executionId }> = ({ executionId }) => {
     const { data: steps } = useQuery({
       queryKey: ['pipeline-steps', executionId],
       queryFn: () => fetch(`/api/v1/pipelines/executions/${executionId}/steps`),
       refetchInterval: 3000
     });
     
     return (
       <Box>
         {steps.map(step => (
           <StepProgressCard
             key={step.step_number}
             step={step}
             status={step.status}
             duration={calculateDuration(step.started_at, step.completed_at)}
           />
         ))}
       </Box>
     );
   };
   ```

**Files to Create**:
- `frontend/src/components/pipeline/PipelineProgress.tsx` - NEW progress tracker
- `frontend/src/components/pipeline/StepProgressCard.tsx` - NEW step card
- `frontend/src/pages/PipelineExecution.tsx` - NEW execution monitor page

---

#### Phase 3C: Intermediate Results Handling

**What's Needed**:

1. **Collect Step Outputs**:
   ```python
   async def collect_step_results(execution_id: UUID, work_dir: str):
       # After Nextflow completes, collect outputs from each step
       results_dir = f"{work_dir}/results"
       
       for step_dir in os.listdir(results_dir):
           step_path = f"{results_dir}/{step_dir}"
           
           # Upload to storage service
           output_urls = []
           for output_file in os.listdir(step_path):
               file_path = f"{step_path}/{output_file}"
               url = await storage_service.upload_file(file_path)
               output_urls.append(url)
           
           # Update database
           await db.execute(
               """
               UPDATE pipeline_step_results
               SET output_data = $1
               WHERE execution_id = $2 AND step_number = $3
               """,
               json.dumps({"output_files": output_urls}),
               execution_id,
               int(step_dir.split('_')[1])
           )
   ```

2. **API - Get Step Results**:
   ```python
   @router.get("/api/v1/pipelines/executions/{execution_id}/steps/{step_number}/results")
   async def get_step_results(execution_id: UUID, step_number: int):
       step = await db.fetchrow(
           """
           SELECT * FROM pipeline_step_results
           WHERE execution_id = $1 AND step_number = $2
           """,
           execution_id, step_number
       )
       return step
   ```

3. **Frontend - View Intermediate Results**:
   ```typescript
   const StepResultsViewer: React.FC<{ executionId, stepNumber }> = (props) => {
     const { data } = useQuery({
       queryKey: ['step-results', props.executionId, props.stepNumber],
       queryFn: () => fetch(`/api/v1/pipelines/executions/${props.executionId}/steps/${props.stepNumber}/results`)
     });
     
     return (
       <Dialog open>
         <DialogTitle>Step {props.stepNumber} Results</DialogTitle>
         <DialogContent>
           {data.output_data?.output_files.map(url => (
             <FileDownloadButton key={url} url={url} />
           ))}
           {/* Show task-specific visualization if available */}
           {data.task_id === 'gnina-molecular-docking' && (
             <MoleculeViewer pdbUrl={data.output_data.docked_ligand_url} />
           )}
         </DialogContent>
       </Dialog>
     );
   };
   ```

---

### WEEK 7-8: Template Gallery & Sharing (USER EXPERIENCE)

#### Phase 4A: Template Gallery UI

**What's Needed**:

1. **Gallery Page**:
   ```typescript
   export const PipelineGallery: React.FC = () => {
     const [filter, setFilter] = useState<'my' | 'public' | 'all'>('all');
     const { data: templates } = useQuery({
       queryKey: ['pipeline-templates', filter],
       queryFn: () => fetch(`/api/v1/pipelines/templates?filter=${filter}`)
     });
     
     return (
       <Box>
         <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
           <Typography variant="h4">Pipeline Templates</Typography>
           <Button onClick={() => navigate('/pipeline-builder')}>
             Create New Pipeline
           </Button>
         </Box>
         
         <ToggleButtonGroup value={filter} onChange={setFilter}>
           <ToggleButton value="my">My Templates</ToggleButton>
           <ToggleButton value="public">Public Templates</ToggleButton>
           <ToggleButton value="all">All</ToggleButton>
         </ToggleButtonGroup>
         
         <Grid container spacing={2} sx={{ mt: 2 }}>
           {templates.map(template => (
             <Grid item xs={12} md={6} lg={4}>
               <PipelineTemplateCard
                 template={template}
                 onUse={() => loadTemplate(template.pipeline_id)}
                 onEdit={() => editTemplate(template.pipeline_id)}
                 onDelete={() => deleteTemplate(template.pipeline_id)}
               />
             </Grid>
           ))}
         </Grid>
       </Box>
     );
   };
   ```

2. **Template Card**:
   ```typescript
   const PipelineTemplateCard: React.FC<{ template }> = ({ template }) => {
     return (
       <Card>
         <CardContent>
           <Typography variant="h6">{template.name}</Typography>
           <Typography variant="body2" color="text.secondary">
             {template.description}
           </Typography>
           <Box sx={{ mt: 2 }}>
             <Chip label={`${template.template_data.nodes.length} steps`} size="small" />
             <Chip label={template.is_public ? 'Public' : 'Private'} size="small" />
           </Box>
           <Typography variant="caption" display="block" sx={{ mt: 1 }}>
             Created by {template.created_by} on {formatDate(template.created_at)}
           </Typography>
         </CardContent>
         <CardActions>
           <Button size="small" onClick={onUse}>Use Template</Button>
           {canEdit && <Button size="small" onClick={onEdit}>Edit</Button>}
           {canDelete && <Button size="small" color="error" onClick={onDelete}>Delete</Button>}
         </CardActions>
       </Card>
     );
   };
   ```

**Files to Create**:
- `frontend/src/pages/PipelineGallery.tsx` - NEW gallery page
- `frontend/src/components/pipeline/PipelineTemplateCard.tsx` - NEW template card

---

#### Phase 4B: Template Versioning

**What's Needed**:

1. **Database Schema Update**:
   ```sql
   ALTER TABLE pipeline_templates ADD COLUMN version INTEGER DEFAULT 1;
   ALTER TABLE pipeline_templates ADD COLUMN parent_pipeline_id UUID REFERENCES pipeline_templates(pipeline_id);
   
   CREATE INDEX idx_pipeline_templates_parent ON pipeline_templates(parent_pipeline_id);
   ```

2. **Backend - Create New Version**:
   ```python
   @router.post("/api/v1/pipelines/templates/{pipeline_id}/versions")
   async def create_new_version(
       pipeline_id: UUID,
       template: PipelineTemplateUpdate
   ):
       # Get current max version
       current = await db.fetchrow(
           "SELECT MAX(version) as max_version FROM pipeline_templates WHERE parent_pipeline_id = $1 OR pipeline_id = $1",
           pipeline_id
       )
       
       new_version = (current['max_version'] or 0) + 1
       
       # Create new version record
       new_id = await db.execute(
           """
           INSERT INTO pipeline_templates 
           (name, description, template_data, created_by, org_id, is_public, version, parent_pipeline_id)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
           RETURNING pipeline_id
           """,
           template.name, template.description, json.dumps(template.template_data),
           user_id, org_id, template.is_public, new_version, pipeline_id
       )
       
       return {"pipeline_id": new_id, "version": new_version}
   ```

3. **Frontend - Version Selector**:
   ```typescript
   const TemplateVersionSelector: React.FC<{ pipelineId }> = ({ pipelineId }) => {
     const { data: versions } = useQuery({
       queryKey: ['pipeline-versions', pipelineId],
       queryFn: () => fetch(`/api/v1/pipelines/templates/${pipelineId}/versions`)
     });
     
     return (
       <Select value={selectedVersion} onChange={handleVersionChange}>
         {versions.map(v => (
           <MenuItem value={v.version}>
             v{v.version} - {formatDate(v.created_at)}
           </MenuItem>
         ))}
       </Select>
     );
   };
   ```

---

#### Phase 4C: Execution History

**What's Needed**:

1. **Backend - List Executions**:
   ```python
   @router.get("/api/v1/pipelines/executions")
   async def list_pipeline_executions(
       org_id: UUID = Depends(get_current_org_id),
       limit: int = 50,
       offset: int = 0
   ):
       executions = await db.fetch(
           """
           SELECT 
               pe.*,
               pt.name as pipeline_name,
               u.username as executed_by
           FROM pipeline_executions pe
           JOIN pipeline_templates pt ON pe.pipeline_id = pt.pipeline_id
           JOIN users u ON pe.user_id = u.user_id
           WHERE pe.org_id = $1
           ORDER BY pe.created_at DESC
           LIMIT $2 OFFSET $3
           """,
           org_id, limit, offset
       )
       return executions
   ```

2. **Frontend - Execution History Page**:
   ```typescript
   export const PipelineHistory: React.FC = () => {
     const { data: executions } = useQuery({
       queryKey: ['pipeline-executions'],
       queryFn: () => fetch('/api/v1/pipelines/executions')
     });
     
     return (
       <DataGrid
         rows={executions}
         columns={[
           { field: 'pipeline_name', headerName: 'Pipeline' },
           { field: 'executed_by', headerName: 'User' },
           { field: 'status', headerName: 'Status', renderCell: StatusBadge },
           { field: 'created_at', headerName: 'Started' },
           { field: 'completed_at', headerName: 'Completed' },
           { field: 'actions', renderCell: ActionsCell }
         ]}
       />
     );
   };
   ```

**Files to Create**:
- `frontend/src/pages/PipelineHistory.tsx` - NEW history page

---

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

## 📊 **IMPLEMENTATION PRIORITY - UPDATED**

### Sprint 1 (Week 1): Single Task Foundation
**Goal**: Users can execute GNINA tasks, monitor progress, view results
- ✅ ~~Database & API setup~~ DONE
- 🔨 Dynamic task execution form
- 🔨 Task submission workflow
- 🔨 Task monitoring page
- 🔨 Results display with 3D visualization

### Sprint 2 (Week 2): Single Task Polish
**Goal**: Complete single task execution workflow
- 🔨 Error handling improvements
- 🔨 File storage integration
- 🔨 Job manager integration
- 🔨 Authentication/authorization
- 🔨 Integration tests

### Sprint 3 (Week 3): Pipeline Builder UI
**Goal**: Visual workflow creation
- 🔨 React Flow integration
- 🔨 Task palette component
- 🔨 Custom task nodes
- 🔨 Edge validation
- 🔨 Node configuration modal

### Sprint 4 (Week 4): Pipeline Templates
**Goal**: Save and load pipelines
- 🔨 Template save/load API
- 🔨 Pipeline gallery UI
- 🔨 Template cards
- 🔨 Public/private sharing

### Sprint 5 (Week 5): Nextflow Integration
**Goal**: Execute multi-step workflows
- 🔨 Nextflow script generator
- 🔨 Pipeline execution API
- 🔨 Nextflow executor service
- 🔨 Step-by-step progress tracking

### Sprint 6 (Week 6): Pipeline Execution Polish
**Goal**: Complete pipeline execution workflow
- 🔨 Intermediate results handling
- 🔨 Pipeline progress visualization
- 🔨 Error recovery & retry
- 🔨 Execution history

### Sprint 7 (Week 7): Template Gallery Enhancement
**Goal**: Rich template experience
- 🔨 Template versioning
- 🔨 Template import/export
- 🔨 Template search/filter
- 🔨 Usage analytics

### Sprint 8 (Week 8): Testing & Documentation
**Goal**: Production-ready system
- 🔨 E2E tests (single tasks + pipelines)
- 🔨 Performance optimization
- 🔨 User documentation
- 🔨 Developer guides

---

## 🎯 **SUCCESS CRITERIA - UPDATED**

### Single Task Execution ✅
- [x] GNINA task visible in Task Library
- [x] API returns task details correctly
- [ ] User can upload receptor + ligand files via dynamic form
- [ ] Task execution creates database record with org isolation
- [ ] User can monitor execution progress in real-time
- [ ] Results display with 3D molecular visualization (3Dmol.js)
- [ ] Job Manager shows all task executions
- [ ] Error states handled gracefully
- [ ] Response time < 2s for all operations

### Pipeline Builder ✅
- [ ] Drag-drop canvas with React Flow
- [ ] Task palette shows all framework tasks
- [ ] Custom task nodes with visual indicators
- [ ] Edge connections validated (type compatibility)
- [ ] Node configuration modal for parameters
- [ ] Save pipeline as template (public/private)
- [ ] Load existing templates
- [ ] Template gallery with search/filter

### Pipeline Execution ✅
- [ ] Generate valid Nextflow scripts from graphs
- [ ] Execute Nextflow workflows in background
- [ ] Step-by-step progress tracking
- [ ] Intermediate results accessible per step
- [ ] Error recovery and retry logic
- [ ] Org-isolated execution data
- [ ] Execution history view
- [ ] Template versioning

### System-Wide ✅
- [x] Clean Architecture maintained
- [x] Framework tasks as building blocks
- [ ] Authentication/authorization implemented
- [ ] File storage integration complete
- [ ] E2E tests for all workflows
- [ ] User + developer documentation
- [ ] Performance benchmarks met

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

### Pipeline Builder Tables ✅
```sql
CREATE TABLE pipeline_templates (
    pipeline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    created_by UUID NOT NULL REFERENCES users(user_id),
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_data JSONB NOT NULL, -- React Flow graph: {nodes, edges, viewport}
    
    is_public BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE pipeline_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID NOT NULL REFERENCES pipeline_templates(pipeline_id),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    nextflow_script TEXT NOT NULL,
    input_params JSONB,
    
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE pipeline_step_results (
    step_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES pipeline_executions(execution_id),
    
    step_number INTEGER NOT NULL,
    task_id VARCHAR(255) NOT NULL, -- e.g., 'gnina-molecular-docking'
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    UNIQUE (execution_id, step_number)
);

-- Indexes
CREATE INDEX idx_pipeline_templates_org ON pipeline_templates(org_id);
CREATE INDEX idx_pipeline_templates_public ON pipeline_templates(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_pipeline_executions_org ON pipeline_executions(org_id);
CREATE INDEX idx_pipeline_executions_user ON pipeline_executions(user_id);
CREATE INDEX idx_pipeline_executions_status ON pipeline_executions(status);
CREATE INDEX idx_pipeline_step_results_execution ON pipeline_step_results(execution_id);
```

### Task Definitions (Framework Tasks - Not Used) ⚠️
```sql
-- Table exists but empty by design
-- Framework tasks are code-based in neurosnap_task_adapter.py
SELECT COUNT(*) FROM task_definitions; -- Returns: 0

-- This is CORRECT for the current architecture
-- Only developers add tasks via code, not database
```

---

## 🔧 **API Endpoints Status**

### Task Execution (Implemented) ✅
- `GET /api/v1/tasks-unified/available` - List all framework tasks
- `GET /api/v1/tasks-unified/health` - Health check
- `GET /api/v1/tasks-unified/{task_id}` - Get task details
- `POST /api/v1/tasks-unified/{task_id}/execute` - Execute single task
- `GET /api/v1/tasks-unified/executions/{id}/status` - Get execution status
- `GET /api/v1/tasks-unified/executions/{id}/results` - Get execution results
- `GET /api/v1/tasks-unified/executions` - List user executions

### Task Execution (Planned) ⏳
- `POST /api/v1/tasks-unified/executions/{id}/cancel` - Cancel execution
- `POST /api/v1/tasks-unified/{task_id}/validate` - Validate parameters before execution
- `GET /api/v1/tasks-unified/executions/{id}/logs` - Stream execution logs

### Pipeline Templates (Planned) 🆕
- `POST /api/v1/pipelines/templates` - Create pipeline template
- `GET /api/v1/pipelines/templates` - List templates (org + public)
- `GET /api/v1/pipelines/templates/{id}` - Get template details
- `PUT /api/v1/pipelines/templates/{id}` - Update template
- `DELETE /api/v1/pipelines/templates/{id}` - Delete template
- `POST /api/v1/pipelines/templates/{id}/versions` - Create new version
- `GET /api/v1/pipelines/templates/{id}/versions` - List versions

### Pipeline Execution (Planned) 🆕
- `POST /api/v1/pipelines/{id}/execute` - Execute pipeline
- `GET /api/v1/pipelines/executions` - List pipeline executions
- `GET /api/v1/pipelines/executions/{id}` - Get execution details
- `GET /api/v1/pipelines/executions/{id}/steps` - Get step-by-step progress
- `GET /api/v1/pipelines/executions/{id}/steps/{step}/results` - Get step results
- `POST /api/v1/pipelines/executions/{id}/cancel` - Cancel pipeline execution
- `GET /api/v1/pipelines/executions/{id}/logs` - Stream Nextflow logs

---

## 🎨 **Frontend Components Status**

### Single Task Execution
**Existing** ✅
- `TaskLibrary.tsx` - Shows tasks, updated to navigate correctly
- `taskService.ts` - Fetches from unified API correctly

**Needs Update** 🔄
- `ExecuteTasks.tsx` - Exists but hardcoded, needs dynamic form generation
- `JobManager.tsx` - Exists but doesn't show framework executions

**Needs Creation** 🆕
- `DynamicTaskForm.tsx` - Generic form generator from task parameters
- `FileUploadField.tsx` - File upload component with validation
- `TaskMonitor.tsx` - Real-time execution monitoring page
- `TaskResults.tsx` - Results display with 3D visualization
- `MoleculeViewer.tsx` - 3Dmol.js integration for structure viewing
- `StatusIndicator.tsx` - Visual status badges
- `useTaskExecution.ts` - React hook for task execution state

### Pipeline Builder (All New) 🆕
- `PipelineBuilder.tsx` - Main pipeline builder page with React Flow
- `TaskPalette.tsx` - Draggable task list sidebar
- `TaskNode.tsx` - Custom node component for React Flow
- `PipelineToolbar.tsx` - Save/execute/export toolbar
- `NodeConfigModal.tsx` - Configure task parameters modal
- `EdgeConfigDialog.tsx` - Map outputs to inputs dialog
- `PipelineGallery.tsx` - Template gallery page
- `PipelineTemplateCard.tsx` - Template card component
- `PipelineProgress.tsx` - Step-by-step execution progress
- `StepProgressCard.tsx` - Individual step status card
- `PipelineExecution.tsx` - Pipeline execution monitor page
- `PipelineHistory.tsx` - Execution history page
- `pipelineService.ts` - API service for pipelines
- `usePipeline.ts` - React hook for pipeline state

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

### Running a Single Task
```bash
# 1. Access dashboard
open http://localhost/task-library

# 2. Run GNINA task
# - Click "GNINA Molecular Docking"
# - Click "Run Task"
# - Upload receptor.pdb and ligand.sdf
# - Enter job name
# - Click "Execute"
# - Monitor progress at /task-monitor/{id}
# - View results at /task-results/{id}
```

### Creating a Pipeline
```bash
# 1. Open pipeline builder
open http://localhost/pipeline-builder

# 2. Build workflow
# - Drag GNINA task from palette to canvas
# - Drag protein folding task to canvas
# - Connect output of GNINA to input of folding
# - Configure each node's parameters
# - Click "Save Pipeline"
# - Name it "Docking + Folding Workflow"

# 3. Execute pipeline
# - Click "Execute Pipeline"
# - Upload initial input files
# - Monitor at /pipeline-execution/{id}
# - View step-by-step progress
# - Access intermediate results
```

### Using Templates
```bash
# 1. Browse templates
open http://localhost/pipeline-gallery

# 2. Load template
# - Filter by "Public" templates
# - Find "Standard Drug Discovery Pipeline"
# - Click "Use Template"
# - Customize parameters if needed
# - Click "Execute"
```

---

## ⚡ **Next Immediate Actions - UPDATED ROADMAP**

### This Week (Week 1): Single Task Foundation
**Priority**: Get single task execution working end-to-end
1. ✅ Run pipeline builder migration (create 3 new tables)
2. 🔨 Create `DynamicTaskForm.tsx` component
3. 🔨 Update `ExecuteTasks.tsx` to use query parameter + dynamic form
4. 🔨 Implement file upload handling
5. 🔨 Test task submission end-to-end
6. 🔨 Create `TaskMonitor.tsx` page
7. 🔨 Implement status polling

### Next Week (Week 2): Results & Polish
**Priority**: Complete single task workflow
1. 🔨 Create `TaskResults.tsx` page  
2. 🔨 Integrate 3Dmol.js for molecular visualization
3. 🔨 Update `JobManager.tsx` to show task executions
4. 🔨 Add authentication to task endpoints
5. 🔨 Implement file storage integration
6. 🔨 Write integration tests for task workflow

### Following Weeks (Week 3-8): Pipeline Builder Focus
**Priority**: Visual workflow creation system
1. 🔨 **Week 3**: React Flow integration + TaskPalette
2. 🔨 **Week 4**: Template save/load + gallery
3. 🔨 **Week 5**: Nextflow script generator + executor
4. 🔨 **Week 6**: Step-by-step tracking + intermediate results
5. 🔨 **Week 7**: Template versioning + sharing
6. 🔨 **Week 8**: E2E tests + documentation

---

## 📝 **Key Architecture Decisions Documented**

### Why Framework Tasks (Code-Based)?
✅ **Decision**: Keep tasks in `neurosnap_task_adapter.py`, NOT in database
- **Reason**: Only developers add computational services
- **Benefit**: Version control, type safety, simpler deployment
- **Tradeoff**: Can't add tasks without code deployment (acceptable for our use case)

### Why Empty task_definitions Table?
✅ **Decision**: Table exists but unused for framework tasks
- **Reason**: Framework tasks bypass database lookup
- **Benefit**: Faster task retrieval, simpler data flow
- **Note**: Table kept for potential future database-driven tasks (different use case)

### Why Pipeline Builder Priority?
✅ **Decision**: Focus on visual workflow creation over single task polish
- **Reason**: Non-developers create complex workflows (primary value proposition)
- **Benefit**: Differentiator from simple task execution systems
- **Approach**: Build minimal single task execution first, then focus on pipelines

### Why Nextflow for Orchestration?
✅ **Decision**: Use Nextflow instead of custom workflow engine
- **Reason**: Industry standard, battle-tested, scalable
- **Benefit**: Containerization, parallelization, reproducibility built-in
- **Approach**: Generate Nextflow DSL from React Flow graphs

---

## 📖 **Related Documentation**

- **Architecture Analysis**: `/docs/implementation/CURRENT_SYSTEM_ANALYSIS.md`
- **Pipeline Builder Design**: `/docs/architecture/pipeline-builder-design.md`
- **Database Migrations**: `/database/migrations/20251112_pipeline_builder.sql`
- **API Routes**: `/src/molecular_analysis_dashboard/presentation/api/routes/unified_tasks.py`
- **Framework Tasks**: `/src/molecular_analysis_dashboard/adapters/providers/neurosnap_task_adapter.py`

---

## 🎯 **Definition of Done**

### Sprint 1-2: Single Task Execution
- [ ] User can execute any framework task via dynamic form
- [ ] File uploads work for all file parameter types
- [ ] Task monitoring shows real-time status updates
- [ ] Results page displays task-specific outputs (3D for molecules)
- [ ] Job Manager shows task executions with filters
- [ ] All task executions are org-isolated
- [ ] Integration tests pass for full workflow
- [ ] Error states handled with user-friendly messages

### Sprint 3-4: Pipeline Builder UI
- [ ] Drag-drop canvas functional with React Flow
- [ ] All framework tasks appear in task palette
- [ ] Nodes can be connected with validation
- [ ] Node configuration modal works for all parameter types
- [ ] Pipelines can be saved as templates
- [ ] Templates load correctly into builder
- [ ] Public/private sharing implemented
- [ ] Gallery shows all accessible templates

### Sprint 5-6: Pipeline Execution
- [ ] Nextflow scripts generated correctly from graphs
- [ ] Pipeline executions run in background
- [ ] Step-by-step progress visible in UI
- [ ] Intermediate results accessible
- [ ] Error recovery works (retry failed steps)
- [ ] All executions are org-isolated
- [ ] Execution history shows past runs
- [ ] Logs streamable in real-time

### Sprint 7-8: Production Ready
- [ ] Template versioning works
- [ ] Import/export functional
- [ ] E2E tests cover all major workflows
- [ ] Performance benchmarks met (< 2s API response)
- [ ] User documentation complete
- [ ] Developer guides written
- [ ] Security audit passed
- [ ] Load testing completed

---

## 🔐 **Security Considerations**

### Organization Isolation ✅
- All task executions filtered by `org_id`
- All pipeline executions filtered by `org_id`
- Templates can be public OR org-private
- File uploads scoped to org storage

### Authentication & Authorization 🔄
- [ ] JWT token validation implemented
- [ ] User permissions checked on all endpoints
- [ ] Template access control enforced
- [ ] Execution ownership verified

### File Upload Security 🔄
- [ ] File type validation (PDB, SDF, PDBQT only)
- [ ] File size limits enforced (max 100MB)
- [ ] Malware scanning integrated
- [ ] Uploaded files isolated per org

### Nextflow Execution Security 🔄
- [ ] Script injection prevented
- [ ] Containerized execution enforced
- [ ] Resource limits applied (CPU, memory, time)
- [ ] Network isolation configured

---

## 📈 **Performance Targets**

### API Response Times
- Task list: < 500ms
- Task execution submission: < 1s
- Status check: < 200ms
- Results retrieval: < 2s (excluding large file download)
- Pipeline template load: < 1s

### Database Queries
- Execution history pagination: < 300ms
- Template gallery: < 500ms
- Step results: < 200ms per step

### Nextflow Execution
- Script generation: < 2s
- Workflow submission: < 5s
- Progress updates: Every 3s maximum

---

## 🧪 **Testing Strategy**

### Unit Tests
- Task parameter validation
- Nextflow script generation logic
- React Flow graph transformations
- Parameter type compatibility checks

### Integration Tests
- Full task execution workflow (submit → monitor → results)
- Pipeline save/load cycle
- Nextflow execution with mocked containers
- File upload/download flow

### E2E Tests
- Complete user journey: Task Library → Execute → Monitor → Results
- Complete pipeline journey: Builder → Save → Execute → Monitor → View Steps
- Template sharing workflow

### Performance Tests
- Concurrent task executions (100 simultaneous)
- Large pipeline graphs (50+ nodes)
- Rapid status polling (1000 requests/min)

---

**Last Updated**: November 12, 2025  
**Status**: Pipeline builder migration created, ready to execute  
**Next Action**: Run migration and start Week 1 implementation (DynamicTaskForm.tsx)