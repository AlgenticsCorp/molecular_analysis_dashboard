# Task Framework Plug-in Architecture Plan

**Status**: In Progress (registry + metadata bootstrap implemented)  
**Last Updated**: November 14, 2025  
**Owner**: GitHub Copilot (GPT-5-Codex Preview)

---

## 1. Goals
- Allow new computational tasks to be added without modifying core unified task code paths.
- Standardize onboarding sequence for future providers (NeuroSnap variants, local engines, third-party services).
- Preserve consistent API/UX semantics for submission, monitoring, results, and file artifacts.

## 2. Architectural Overview
- **TaskExecutorPort**: slim async interface describing `submit`, `status`, `results`, optional `cancel`, `health`. All adapters implement this contract.
- **Adapter Registry**: dynamic loader responsible for discovering adapters + metadata at startup. Primary responsibilities:
  - Resolve configuration source (entry-points, env-provided module paths, or YAML manifest).
  - Instantiate adapters, hand back tuple of (`task_id`, `metadata`, `adapter`).
  - Provide lookup for `UnifiedTaskService` by task ID.
- **Task Metadata Store**: declarative JSON objects (initial implementation under `config/tasks/*.json`; YAML support optional later) describing parameters, defaults, validation, output descriptors, UI hints. Example fields:
  - `name`, `category`, `tags`, `execution_time_estimate`, `resource_requirements`.
  - Parameter schema (type, required, validation, file constraints, UI widget hints).
  - Optional `results_schema` for front-end hints.
- **Framework Service Flow**: UnifiedTaskService uses registry API instead of hard-coded adapters:
  1. At boot, registry loads and caches adapters + metadata.
  2. `get_all_tasks()` merges registry metadata with DB-defined tasks.
  3. `execute_task()` resolves adapter via registry, stores metadata reference ID, persists file references, delegates to adapter.
  4. Status/results processing logic remains unchanged, but adapters can provide optional capability flags (supports-cancel, provides-downloads, etc.).

## 3. Implementation Tasks
1. **Registry Skeleton**
   - Create `TaskPluginRegistry` module offering `load()`, `get_adapter(task_id)`, `get_metadata(task_id)`, `list_tasks()`.
   - Support primary discovery methods:
   - Static config (default in repo) living under `config/tasks/*.json`.
     - Optional entrypoint mechanism for external packages (future).
   - Logging + error handling if any adapter fails to load.

2. **Metadata Refactor**
   - Move GNINA and Amber metadata into JSON docs (complete).
   - Update `TaskExecutionService` or replacement to read metadata via registry rather than inline dictionaries (complete for initial tasks).
   - Ensure serialization for `/tasks-unified/available` endpoints matches existing contract (validated via manual check; add automated test).

3. **Adapter Refactor**
   - Update current NeuroSnap adapters to register themselves through the registry with metadata keys.
   - Remove direct initialization of adapters inside UnifiedTaskService.
   - Provide factory hooks for dependency injection (base URL, credentials, HTTP clients).

4. **Unified Task Service Updates**
   - Swap direct adapter references for registry lookups.
   - Adjust caching strategy (registry already caches metadata).
   - Update `_get_framework_tasks`, `_get_framework_task`, `_is_framework_task` to operate on registry outputs.

5. **Configuration & Environment**
   - Introduce optional manifest (e.g., `tasks.manifest.yaml`) for environment-specific overrides (future work).
   - Provide env var to restrict tasks per deployment (`ENABLED_FRAMEWORK_TASKS=...`).

6. **Testing Strategy**
   - Unit tests for registry loader (happy path, missing metadata, invalid adapter).
   - Contract tests using mock adapters to ensure UnifiedTaskService handles submit/status/results with registry-injected adapter.
   - API integration tests covering `/available`, `/execute`, `/status`, `/results` with registry-sourced tasks.
   - Lint-type validation to ensure metadata schemas match front-end expectations.

7. **Documentation**
   - Developer guide: "Adding a New Task" (step-by-step) referencing the registry, metadata schema, tests, and deployment toggles.
   - Update architecture docs (frontend + backend) to explain plugin model and how Task Library consumes metadata.

## 4. Open Questions / Follow-ups
- Do we need multi-tenant restrictions (task availability by organization)? If so, manifest should support scoping/labels consumed by UnifiedTaskService.
- Should registry support lazy loading (on-demand import) to reduce boot time? Evaluate once number of tasks grows.
- Determine canonical location for per-task result schemas so front-end can render custom views without code changes.

## 5. Next Steps (Immediate)
1. Implement registry skeleton + YAML loader.
2. Move GNINA metadata into YAML and validate `/available` output parity.
3. Register Amber adapter via registry and re-run integration test (after DB constraint fix).
4. Document setup in `/docs/implementation/task-framework-plugin-architecture.md` (this file) and extend developer guide.

---

> Tracking issue TODO: link to GitHub ticket once created for full migration to plugin architecture.
