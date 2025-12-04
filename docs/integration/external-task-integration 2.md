# Integrating A New External Task

This guide walks through onboarding a new provider-backed computation so that it flows end-to-end:

1. **Provider Discovery** – confirm the external API contract and identify the provider-specific service handle.
2. **Adapter Implementation** – add or extend a task adapter in `src/molecular_analysis_dashboard/adapters/providers/` that translates unified requests into provider submissions.
3. **Task Registration** – declare the task in `config/tasks/` so the unified task registry exposes it via `/api/v1/tasks-unified`.
4. **Unified API Wiring** – ensure the task is reachable through the unified execute/status/results endpoints and that required files land in storage.
5. **Frontend Surfacing** – expose the task in the dashboard UI through the task service and relevant views.

Each section below highlights the artifacts to touch, recommended conventions, and validation steps.

## 1. Provider Discovery

- Collect the provider submission recipe: required multipart field names, optional parameters, note/metadata handling, and response schema. Pay attention to provider quirks such as omitted fields meaning `false` or the order of keys inside JSON payloads.
- Verify the service identifier by calling the provider capability endpoint (for example `GET https://<provider>/api/services`) or consulting vendor documentation.
- Capture example payloads in `docs/integration/provider-examples/` if you need to share curl/python snippets with teammates. Update these examples whenever you learn about format nuances so future adapters stay aligned.
- Confirm authentication requirements (API key header, OAuth token, etc.) and whether rate limits apply.

## 2. Adapter Implementation

Create a new adapter class if none exists for the provider/task combination. Use the existing adapters under
`src/molecular_analysis_dashboard/adapters/providers/` as references.

Key guidelines:

- Reuse a provider-specific base class if one already exists (for example, see how the NeuroSnap adapters inherit from a shared base).
- Keep multipart construction provider-native; map framework parameter names to provider field names (e.g., `structure_file`
  → `Input Structure`).
- URL-encode service names and `note` values before generating submission URLs when a provider requires query parameters.
- Set sensible defaults inside the adapter so missing optional parameters fall back to provider defaults. Only include an optional field in the multipart payload when the provider expects a non-default override.
- Support multiple input sources where needed (e.g., uploaded ligand files plus JSON descriptors) and normalize data before submitting to the provider.
- Log descriptive errors and rethrow them as `RuntimeError` so the unified task framework can surface informative messages.

Implementation checklist:

- [ ] Add the adapter class to the appropriate module.
- [ ] Export it via the module so tests and importers can access it.
- [ ] Update or add unit tests under `tests/unit/adapters/` to cover multipart payload construction and error handling (mock the HTTP client).

## 3. Task Registration

Add a task definition JSON file under `config/tasks/`. Copy the structure used by the existing task definitions:

```json
{
  "id": "provider-task-id",
  "adapter": {
    "module": "molecular_analysis_dashboard.adapters.providers.<module>",
    "class": "<AdapterClass>"
  },
  "metadata": {
    "name": "Display Name",
    "description": "What the task does",
    "version": "1.0.0",
    "category": "domain",
    "tags": ["tag"],
    "provider": "provider-name",
    "interface_type": "openapi",
    "parameters": [
      {
        "name": "structure_file",
        "type": "file",
        "required": true,
        "description": "Primary model input",
        "validation": {
          "file_types": [".pdb"],
          "max_size_mb": 100
        }
      }
    ]
  }
}
```

After adding the config file, restart the API so the `TaskRegistry` re-reads the configuration.

### Validation

- `curl http://localhost:8000/api/v1/tasks-unified/` should now list the new `id`.
- `curl http://localhost:8000/api/v1/tasks-unified/<task-id>` returns the merged metadata.

## 4. Unified API Wiring

The unified task routes live in `src/molecular_analysis_dashboard/presentation/api/routes/unified_tasks.py`.

- Confirm the task requires no special-case routing. The execute endpoint streams parameters through the adapter via `TaskExecutionService`.
- Validate file uploads land in storage (`storage:8080/uploads/...`).
- Poll status until completion: `GET /api/v1/tasks-unified/executions/<execution_id>/status` and collect results from `.../results`.
- If you need post-processing (e.g., transforming provider outputs into dashboard-friendly files), extend
  `TaskExecutionService` or a dedicated results service.

Functional smoke test (example):

```bash
curl -s -o /tmp/task_execute.json -w "%{http_code}" \
  -F "structure_file=@/path/to/input.pdb" \
  http://localhost:8000/api/v1/tasks-unified/<task-id>/execute

curl http://localhost:8000/api/v1/tasks-unified/executions/<execution_id>/status
curl http://localhost:8000/api/v1/tasks-unified/executions/<execution_id>/results
```

Ensure the adapter reports a provider job id and that result payloads include download URLs or stored files.

## 5. Frontend Surfacing

Frontend integration involves three layers under `frontend/`:

1. **Task Service** – Update `src/services/taskService.ts` (or equivalent) so it fetches the unified `/available` list and recognizes the new task metadata.
2. **Forms/Views** – Add form components for collecting task parameters. Reuse existing file-upload and number-input components.
3. **Execution Details** – Extend the execution detail view to render task-specific outputs (e.g., embed molecular viewer, download buttons).

Checklist:

- [ ] Add localized strings / documentation for the new task.
- [ ] Include validation and helper copy explaining required inputs.
- [ ] Wire execution polling to show progress and surface provider errors gracefully.
- [ ] Write a Cypress/Vitest smoke test where feasible (mocking the API).

## 6. Operational Readiness

- Document environment variables (API keys, base URLs) in `SETUP.md` and `.env.example`.
- Add monitoring hooks or logging around adapter submission and result handling for production observability.
- Update release notes (`CHANGELOG.md`) summarizing the new task availability.
- Coordinate with DevOps to rotate or provision credentials in target environments.

## 7. Examples

### Example: AMBER Relaxation

The AMBER integration demonstrates the full flow:

1. **Adapter** – `NeuroSnapAmberRelaxationAdapter` maps unified parameters to provider fields and posts to `https://neurosnap.ai/api/job/submit/AMBER%20Relaxation`.
2. **Config** – `config/tasks/neurosnap-amber-relaxation.json` advertises the task.
3. **Unified API** – `/api/v1/tasks-unified/neurosnap-amber-relaxation/execute` accepts file uploads and returns framework execution IDs.
4. **Frontend** – The molecular dynamics UI queries the unified tasks endpoint and displays relaxed structure outputs.

Review these files when onboarding a structurally similar task.

### Folding Workflows

Multiple folding services share the same adapter foundation with service-specific subclasses. The general approach is:

1. **Adapters** – Create a base folding adapter that handles shared parsing (for example, raw or FASTA sequence ingestion) and derive lightweight subclasses for individual provider offerings.
2. **Config** – Add one task definition JSON per provider offering and point each to the appropriate adapter subclass.
3. **Unified API** – Ensure each task appears under `/api/v1/tasks-unified/` once the API container is rebuilt or restarted.
4. **Validation** – Smoke test execution/status/results endpoints for one service to confirm the shared foundation behaves as expected.

### Example: AutoDock Vina Docking

This docking workflow illustrates how to combine file uploads with inline ligand descriptors while honouring provider-specific flags:

1. **Adapter** – `NeuroSnapAutoDockVinaAdapter` accepts receptor files, optional ligand files, and JSON ligand entries, omitting `Local Only` / `Score Only` fields when false so the provider defaults remain intact.
2. **Config** – `config/tasks/neurosnap-autodock-vina-docking.json` describes the unified parameters (`receptor_file`, `ligand_entries_json`, `scoring_function`, etc.).
3. **Provider Example** – `docs/integration/provider-examples/neurosnap-autodock-vina.md` captures the raw multipart format supplied by NeuroSnap.
4. **Validation** – Submitting through `/api/v1/tasks-unified/neurosnap-autodock-vina-docking/execute` stores the execution and returns job IDs; results become available via the standard unified endpoints once downloaded.

## 8. Troubleshooting

- **Submission 4xx**: Verify service name, multipart field labels, and the API key header. Use `docker compose exec api sh -c 'curl ...'` to debug from inside the container.
- **Missing in `/tasks-unified/`**: Ensure the config file is valid JSON and that the adapter class imports without error.
- **Result Files Empty**: Confirm the provider returned file metadata; add logging in the adapter’s result handling to inspect raw payloads.
- **Frontend Not Showing Task**: Check cache/state management (the frontend may memoize available tasks). Refresh the browser or reset mocked data.

## 9. Recap

1. Confirm the provider API contract and authentication.
2. Implement or update the adapter to translate unified inputs to provider requests.
3. Register the task so the unified framework knows about it.
4. Verify backend execution, storage, and result retrieval.
5. Surface the task in the frontend and add automated coverage.
6. Document credentials and update release notes.

Following this flow keeps new external tasks consistent with the existing catalog while minimizing duplicated wiring.
