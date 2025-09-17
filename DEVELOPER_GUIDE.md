# Developer Guide: Architecture, Metadata, Quality Gates & Workflow

This repo is optimized for clarity, safe changes, and LLM-agent productivity. We use:

- A Ports & Adapters (Hexagonal/Clean) structure for easy extension and testing.
- A `src/` layout to avoid import gotchas and ensure tests run against the installed package.
- Auto-generated metadata, graphs, and docs from the code itself (single source of truth).
- SOLID principles and PEP 8/257/484 enforced via linters, docstring checkers, and CI.

## Repo layout (Clean/Hexagonal + src/)

```
repo/
├─ pyproject.toml
├─ src/
│  └─ your_package_name/
│     ├─ domain/          # entities, domain services
│     ├─ use_cases/       # application services
│     ├─ ports/           # abstract interfaces
│     ├─ adapters/        # implementations (db/http/cli/etc.)
│     ├─ infrastructure/  # DI, config, logging
│     ├─ presentation/    # http/cli/workers (thin I/O)
│     └─ shared/          # small cross-cutting utils
├─ tests/ (unit/, integration/, e2e/)
├─ tools/ (automation scripts)
├─ docs/  (site/, atlas artifacts)
└─ .github/workflows/ci.yml
```

## Local environment: venv + install

Create & activate a virtual environment:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Install the project in development mode:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev,docs,tools]"
```

## Quality guardrails (SOLID + PEPs + Docstrings)

- Follow SOLID to keep code understandable, extendable, and testable.
- Style & naming: PEP 8; docstrings: PEP 257; types: PEP 484.
- Docstrings are mandatory at module, class, and function levels. We use Google style (preferred) or NumPy style.

### Docstring templates

#### Module (top of file):

```python
"""
<Summary of module>.

Details:
- Responsibilities
- Dependencies
- Assumptions/limitations
"""
```

#### Class:

```python
class OrderProcessor:
    """
    Application service for processing customer orders.

    Attributes:
        repo (OrderRepositoryPort): Persistence interface.
        notifier (NotifierPort): Notification interface.
    """
```

#### Function:

```python
def price_with_tax(amount: float, rate: float) -> float:
    """
    Compute price including tax.

    Args:
        amount (float): Base amount.
        rate (float): Tax rate (0.15 = 15%).

    Returns:
        float: Total with tax.

    Raises:
        ValueError: If inputs are negative.

    Example:
        >>> price_with_tax(100, 0.15)
        115.0
    """
```

## Code Commenting Guidelines (Professional Schema)

Goal: Comments make intent obvious, capture the “why,” and reduce cognitive load. Prefer self-documenting code first; add comments where non-obvious. Keep comments accurate and up to date.

Principles:
- Prefer explaining “why” over restating “what” the code already says.
- Place comments at the smallest helpful scope (inline, block, function, module).
- Use full sentences for multi-line comments. Keep to ~100 chars/line.
- Remove stale comments; if behavior changes, update the comment in the same commit.

Comment types and schema:
- Module/file header: Use a module docstring (PEP 257). Summarize responsibilities, dependencies, assumptions.
- Public API docstrings: Mandatory Google style (already defined above). Include Args/Returns/Raises/Examples.
- Block comment (above code): Use when rationale, invariants, edge-cases, or trade-offs need explaining.
    - Format:
        ```python
        # RATIONALE: batching reduces DB round-trips from O(n) to O(1).
        # INVARIANT: items are unique by (org_id, key).
        ```
- Inline comment (end-of-line or just above a line): Use sparingly for non-obvious intent.
    - Format: `# why this line exists`
- Decision/TODO/FIXME/NOTE/Security tags:
    - Use canonical tags at the start of the comment and include traceability:
        - `# TODO(#123) [@owner] 2025-09-03: replace O(n^2) loop with bulk upsert`
        - `# FIXME: incorrect timezone handling around DST; see issue #456`
        - `# NOTE: idempotent by design; safe to retry`
        - `# SECURITY: avoid logging secrets; tokens are redacted upstream`
    - Convert TODOs to issues when work spills over a PR; keep tags short and actionable.
- Snippet comments (required): Any code snippet in docs, README, PR descriptions, or docstring Examples must include brief comments for context and non-obvious steps.
    - First line: context/purpose of the snippet.
    - Add inline comments for complex lines; avoid over-commenting trivial ones.

Style rules:
- Python inline/block comments start with `# ` (single space after hash).
- Wrap multi-line comments to ~100 columns; separate from code with a blank line when they’re long.
- Avoid commented-out code in committed files. If you must show alternatives, put them in docs.
- Keep comments neutral and professional; no blame or jokes.

Examples:

1) Block + inline comments around a tricky section

```python
def top_k(items: list[int], k: int) -> list[int]:
        """Return the k largest items. Assumes k << len(items)."""
        # RATIONALE: heapq.nlargest is O(n log k), faster than sorting O(n log n) for small k.
        import heapq

        if k <= 0:
                return []

        # NOTE: defensive copy to avoid mutating caller’s list; heapq works on iterables.
        return heapq.nlargest(k, list(items))
```

2) Decision/TODO with traceability

```python
# TODO(#321) [@data-eng] 2025-09-03: replace per-row inserts with COPY for large batches
save_rows(rows)
```

3) Snippet in docs with required comments

```python
# Submit a job and poll status until completion (simplified example)
job_id = api.submit_job(molecule_path)  # returns UUID

while True:
        status = api.get_job_status(job_id)
        if status.done:
                break  # stop polling when finished
        time.sleep(1)  # backoff/jitter omitted for brevity

result = api.get_job_result(job_id)  # retrieve final artifact
```

Checklist before merging:
- [ ] Public functions/classes have Google-style docstrings.
- [ ] Complex blocks have a brief rationale comment.
- [ ] TODO/FIXME/NOTE/SECURITY tags use the schema and link to issues when relevant.
- [ ] Snippets in docs/PRs have minimal context comments.

## Auto-generated Code Atlas

- `extract_schema.py`: builds `docs/schema.json` with functions, signatures, and docs.
- `render_graphs.py`: builds `docs/atlas/*.svg` (module + call graphs).
- MkDocs + mkdocstrings: generates browsable API docs from docstrings/types.

## Pre-commit hooks (with docstring enforcement)

Pre-commit hooks are automatically configured to enforce:

- **Code formatting**: Black and isort
- **Type checking**: mypy with strict settings
- **Linting**: flake8, pylint with extensive plugins
- **Security**: bandit scanning
- **Docstrings**: pydocstyle and flake8-docstrings
- **Complexity**: radon for cyclomatic complexity and maintainability
- **Atlas generation**: Automatic schema and graph updates

Run the hooks:

```bash
pre-commit install
pre-commit run --all-files
```

## CI Workflow (with docstring checks)

The GitHub Actions workflow includes:

- **Multi-Python versions**: 3.9, 3.10, 3.11, 3.12
- **Quality gates**: Code formatting, linting, type checking, security scanning
- **Documentation**: Auto-build and deployment
- **Atlas generation**: Dependency graphs and schema extraction
- **Test coverage**: Comprehensive testing with coverage reporting

## Workflow for Changes

### Before editing:

1. Read function/class/module docstring (summary, args, returns, raises).
2. Review schema & graphs (dependencies).
3. Inspect related tests.
4. Check complexity & maintainability budgets.

### Adding:

- Write docstrings & type hints.
- Add unit tests.
- Run extract/render, pre-commit, pytest.

### Modifying:

- Update docstrings/types to reflect changes.
- Update tests.
- Run pre-commit & pytest.

### Deleting:

- Check call graph for dependents.
- Remove/update tests.
- Refresh schema & graphs.

## Unit testing

- Use pytest.
- Place tests under `tests/`.
- Write tests for happy path, edge cases, error conditions.
- Use fixtures (`conftest.py`) for setup.
- Run:

```bash
pytest -q
```

## Coding standards & configs

`.flake8`:

```ini
[flake8]
max-line-length = 100
extend-ignore = E203,W503
docstring-convention = google
extend-select = D
ignore = D401
exclude = .venv,build,dist,site
```

`.pylintrc`:

```ini
[FORMAT]
max-line-length=100
max-module-lines=600

[DESIGN]
max-args=6
max-locals=15
max-branches=12
max-returns=6
max-statements=60
```

## Daily commands (cheat sheet)

```bash
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pre-commit run -a          # format, lint, docstring, complexity
pytest -q                  # run tests
python tools/extract_schema.py
python tools/render_graphs.py --repo-url https://github.com/your-org/your-repo/blob/main
mkdocs serve               # preview docs
```

## Summary

With this guide:

- Every file/class/function has mandatory docstrings (checked by pydocstyle + flake8-docstrings).
- Code Atlas (schema + graphs + docs) is always up to date.
- CI blocks missing docs, style violations, or oversized/complex functions.
- LLM-agents and humans can confidently read and modify code with clear contracts.
