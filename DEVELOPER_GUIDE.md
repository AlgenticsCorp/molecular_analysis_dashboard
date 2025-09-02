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
