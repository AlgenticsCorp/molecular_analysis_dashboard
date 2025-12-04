# Amber Relaxation Integration Plan

**Last Updated**: November 14, 2025  
**Author**: GitHub Copilot (GPT-5-Codex Preview)

---

## 1. Background & Objectives
- Extend the unified task framework to support NeuroSnap Amber Relaxation workflows alongside existing GNINA docking.
- Provide a consistent submission, monitoring, and results experience in the Job Manager and Task Library.
- Ensure the new task reuses shared infrastructure (execution records, file storage, polling, download flows) with minimal duplication.

## 2. Current State Snapshot
- Backend exposes `/api/v1/providers/neurosnap/molecular-dynamics/amber-relaxation/submit`; no linkage to task framework.
- Unified task pipeline currently advertises only `gnina-molecular-docking` and assumes fixed file fields in the execute route.
- Frontend Task Library and Execute flow consume unified task metadata via API and generate forms dynamically.
- Celery polling, execution file storage, and Job Manager UI already support multiple tasks conceptually but lack Amber-specific metadata.

## 3. High-Level Requirements
1. Register an `amber-relaxation` (final name TBD) framework task surfaced by `/api/v1/tasks-unified/available`.
2. Support submission through `/api/v1/tasks-unified/{task_id}/execute` with required parameters:
   - `structure_file` (file upload, PDB/PDBQT)
   - `max_iterations` (integer)
   - `tolerance` (float)
   - `job_name` (string, optional default)
   - `note` (string, optional default)
3. Route execution through TaskExecutionService using a dedicated NeuroSnap adapter that calls the existing Amber REST endpoint and records external job IDs.
4. Persist input file metadata and poll for job status/results exactly as GNINA tasks do, including automatic output file downloads when available.
5. Surface Amber executions in Job Manager with parameters, files, and results displayed correctly.
6. Update documentation to describe the new capability and its configuration knobs.

## 4. Backend Integration Plan
1. **Adapter Layer**
   - Create `NeuroSnapAmberRelaxationAdapter` alongside the docking adapter.
   - Handle multipart submission to `/api/v1/providers/neurosnap/molecular-dynamics/amber-relaxation/submit` (internal API) with proper form fields.
   - Map stored execution `input_data` entries back to files using `ExecutionFileService` similar to docking.
2. **Task Registry**
   - Expand `TaskExecutionService.adapters` to include the Amber adapter and expose metadata in `get_available_tasks()` (id, parameters, resource profile, defaults).
   - Move GNINA and Amber metadata into declarative JSON under `config/tasks/` so registry-driven loading keeps backend/front-end in sync.
   - Ensure parameter schema matches frontend expectations (type names, defaults, validation bounds).
3. **Unified Task Execution Endpoint**
   - Refactor `/tasks-unified/{task_id}/execute` route to parse arbitrary file+field combinations rather than hard-coded GNINA names.
   - Use task definition metadata to coerce numeric/boolean values and to identify file parameters for storage.
   - Preserve support for legacy `parameters` JSON payload if provided.
4. **Result & Polling Flow**
   - Confirm Celery polling and results retrieval use adapter polymorphism (should work after registry update).
   - Extend any result normalization (if needed) to capture Amber-specific metrics (e.g., energy terms) once response structure is known.
5. **Validation & Error Handling**
   - Implement format checks for `structure_file` (PDB/PDBQT) either in adapter or service validation layer.
   - Provide clear error messages when required parameters missing or conversion fails.

## 5. Frontend Integration Plan
1. **Task Metadata Consumption**
   - No structural changes expected; ensure Task Library surfaces new task once backend exposes it.
   - Verify `TaskTemplate` type or fallback mapping can handle missing fields (engine/status). Add defaults if necessary.
2. **Execute Flow**
   - Confirm `DynamicTaskForm` correctly renders Amber parameter types (file, integer, number, string) and enforces validation hints.
   - Ensure review step presents numeric values properly (avoid `NaN` when optional fields blank).
3. **Job Manager**
   - Validate Amber executions display file lists and parameter JSON without GNINA-specific assumptions.
   - If output preview/visualization differs (e.g., no ligand file), adjust conditional UI.
4. **Docs & UX Copy**
   - Update Task Library descriptions and onboarding docs to mention Amber relaxation support.

## 6. Infrastructure & Configuration
- Confirm `.env` / Vite env files expose any new flags if Amber requires toggles (e.g., `VITE_ENABLE_AMBER_TASK`).
- Ensure docker-compose and Celery workers do not require additional services beyond existing NeuroSnap connectivity.
- Verify NeuroSnap API key covers Amber endpoint usage; document prerequisites in `SETUP.md` or dedicated docs.

## 7. Testing Strategy
- **Unit/Service Tests**: Add adapter tests mocking NeuroSnap responses; extend execution service tests for new task ID.
- **API Contract Tests**: Exercise `/tasks-unified/available`, `/tasks-unified/{id}`, `/execute`, `/executions/{id}/status` with Amber payload.
- **Frontend**: Run `npm run type-check` and targeted Vitest suite (if available) for task components; consider Cypress smoke test if coverage exists.
- **Integration Smoke**: Manual or automated submission against staging NeuroSnap to confirm end-to-end behavior, including file downloads.

## 8. Risks & Mitigations
- **API Contract Drift**: NeuroSnap Amber response schema may differ; log raw payloads and gracefully handle unknown fields.
- **Execution Parameter Casting**: Incorrect type coercion can break submissions; rely on task metadata to drive conversions with validation feedback.
- **File Size Limits**: Amber structures may exceed GNINA defaults; confirm 100 MB cap sufficient or expose configurable limit.
- **Parallel Polling Load**: Additional tasks increase Celery polling traffic; monitor and adjust cadence if required.

## 9. Milestones & Deliverables
1. **Day 0**: Plan approved (this document) and branch setup.
2. **Day 1**: Backend adapter + unified task endpoint refactor passing unit tests.
3. **Day 2**: Frontend surfaces task, execute flow verified locally, Job Manager displays Amber runs.
4. **Day 3**: Documentation updates, integration tests, final QA and deployment readiness.

## 10. Open Questions
- Do Amber result payloads include downloadable files similar to GNINA, and should we auto-download them?
- Should Amber tasks appear in specific Task Library category (e.g., "Molecular Dynamics") requiring taxonomy updates?
- Are there additional optional parameters (temperature, solvent) we should expose in the schema now or later?

---

> **Next Action**: Implement backend adapter & dynamic execute endpoint changes, then expose task metadata to the frontend API.
