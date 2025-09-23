Below is a precise, implementation-level description of the front end for your Molecular Docking Platform, aligned with the three UI screenshots (Dashboard, Task Library, Execute/Run wizard).

⸻

Overall architecture
	•	Framework & language: React + TypeScript for a typed component model and safe prop/API contracts. React’s own guide and the TS handbook are the primary references.  ￼ ￼
	•	Routing: React Router with a shell layout and nested routes for each left-nav section (Dashboard, Task Library, Execute Task, Pipelines, Job Monitor, File Manager, Admin Panel, Settings). Parent routes render an <Outlet /> for the child pages.  ￼
	•	Data fetching / server-state: TanStack Query (queries, mutations, cache, background refresh) for all REST/GraphQL calls and job-status data.  ￼
	•	Live updates: WebSocket streams for job progress/logs to avoid polling (native browser API).  ￼
	•	Forms & validation: React Hook Form + Zod (via RHF resolvers) to strongly validate docking parameters (e.g., box sizes, GA runs) at runtime with TS inference for form values.  ￼ ￼
	•	3D structure viewing: 3Dmol.js (recommended) or NGL Viewer to preview PDB/PDBQT/SDF in results and file previews. Both are established, WebGL-based viewers with dev docs.  ￼ ￼ ￼
	•	Build tooling: Vite for fast HMR/dev and optimized Rollup production builds.  ￼

⸻

Layout, routing, and pages

App shell (persistent)
	•	Left rail navigation that matches the screenshots (icons + labels).
	•	Top bar with notifications (bell), user avatar, and a product title.
	•	Implement as a parent route <Shell> with the rail/top bar; each section is a child route rendered via <Outlet />.  ￼

Route map (representative):

/                       → Dashboard
/tasks                  → Task Library
/tasks/:taskId/execute  → Execute Task (wizard)
/pipelines              → Pipelines
/jobs                   → Job Monitor
/files                  → File Manager
/admin                  → Admin Panel
/settings               → Settings

Nested routing follows the official pattern (parent path + child segments).  ￼

⸻

Page-by-page behavior

1) Dashboard
	•	Cards: “Design Pipeline”, “Start Job”, “View Results” (exactly as shown).
	•	Notifications banner: shows “Failed to load dashboard data” style alerts when summary endpoints fail.
	•	Recent activity: small list/table of recent jobs (SUCCEEDED/FAILED).
	•	Data: useQuery for /api/summary and /api/jobs?limit=5; retry/backoff handled by TanStack Query.  ￼

2) Task Library
	•	Search bar + filters (Category, Advanced Filters) and task cards for:
	•	AutoDock 4 (tags: Docking, Built-in, protein-ligand; CPU: medium; Memory: low; Duration: 5–30 min)
	•	AutoDock Vina (CPU: high; Memory: medium; Duration: 1–10 min)
	•	Execute button on each card routes to /tasks/:taskId/execute.
	•	Data: useQuery(['tasks'], fetchTasks) with client-side filtering, or server-side filters via query params.  ￼

3) Execute Task (multi-step wizard)

Step 1 – Configure Parameters
	•	Required parameters (from the screenshot):
	•	Search Space Size X/Y/Z (Å)
	•	GA Runs (AD4)
	•	Output Format (pdbqt)
	•	Advanced parameters (collapsible):
	•	Energy Evaluations (AD4)
	•	Validation via Zod schema (e.g., box sizes ≥ 8 Å; integers for GA runs/evaluations) enforced by React Hook Form resolver.  ￼

Step 2 – Upload Files
	•	Dropzone for receptor and ligand; show filename, size, and a quick 3D preview component (3Dmol/NGL).  ￼ ￼

Step 3 – Review & Execute
	•	Show a read-only summary of parameters + inputs; submit a POST /api/jobs mutation (useMutation) and navigate to Job Monitor on success.  ￼

Step 4 – Monitor Progress
	•	Inline progress bar and live log/metrics over WebSocket (/ws/jobs/:id). Update a local store from onmessage and render status badges/percent complete; no polling.  ￼

4) Pipelines
	•	Node-and-edge canvas (e.g., “Prepare Receptor” → “Dock” → “Post-process/Report”).
	•	Each node opens a side panel with typed params (same form system as Execute).
	•	Run pipeline triggers POST /api/pipelines/{id}/run and opens Job Monitor to a grouped run.

5) Job Monitor
	•	Table with filters (status, task type, date).
	•	Details drawer: parameters, logs (live via WebSocket), and Artifacts (download links + pose gallery).
	•	3D viewer renders the selected pose (cartoon receptor + sticks ligand). 3Dmol’s tutorial shows this pattern clearly.  ￼

6) File Manager
	•	Grid/list of files with sort/filter; preview structures (3D viewer).
	•	Actions: Upload, Delete, “Send to Task” (prefills Execute Step 2).

7) Admin Panel
	•	Users/roles, compute profiles, engine settings.
	•	Form stack is the same (RHF + Zod) for consistency.  ￼

8) Settings
	•	Personal defaults (e.g., preferred engine, default viewer representation), API tokens, theme.

⸻

Core reusable components
	•	PageHeader (title, breadcrumbs, actions)
	•	DataTable<T> (column defs, sort, server/client pagination)
	•	Stepper (for the Execute wizard)
	•	ParamField (number + units + tooltip + validation error)
	•	FilePicker (drag-drop, progress, preview)
	•	JobProgress (status badge + percent + live event stream)
	•	MoleculeViewer (3Dmol or NGL wrapper with props: structureUrl, style, focusSelection)  ￼ ￼

⸻

State & data layer patterns
	•	Queries for lists/detail (tasks, files, pipelines, jobs).
	•	Mutations for create/update (jobs, pipelines, uploads), with invalidation of related queries on success.
	•	Cache lifetimes tuned per view (e.g., jobs staleTime: 15_000ms, files longer).
	•	WebSocket streams merge into React state for “now-casting” progress. TanStack Query keeps historical data fresh in the background.  ￼

⸻

3D viewer specifics
	•	3Dmol.js: lightweight, good defaults, URL-based loaders for PDB/PDBQT/SDF; programmatic styling (cartoon, sticks) and zoomTo() for selections (ligand vs receptor). Docs + tutorial show both URL embedding and imperative API usage.  ￼
	•	NGL (alternative): rich representation controls and trajectories; documented manual for devs.  ￼

⸻

Build & developer experience
	•	Vite for scaffolding and dev server; TypeScript template (npm create vite@latest my-app -- --template react-ts).  ￼
	•	If you prefer a step-by-step blog tutorial: LogRocket’s or Medium’s Vite+React+TS guides (secondary references).  ￼ ￼

⸻
