# Professional Python Project Template

[![CI](https://github.com/your-org/your-repo/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/your-repo/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/your-org/your-repo/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/your-repo)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional Python project template implementing **Clean Architecture** (Hexagonal/Ports & Adapters) with comprehensive tooling for AI agent-assisted development.

> Governance and Policies: see `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, and `CHANGELOG.md`.

## 🚀 **Using This Template**

1. **Click "Use this template"** button above
2. **Create your new repository** from this template
3. **Clone your new repository** locally
4. **Run the setup script**: `./bootstrap.sh your_package_name`
5. **Start developing** with all tools pre-configured!

## 🗺️ **New to this repository?** Start with [NAVIGATION.md](NAVIGATION.md) to understand the structure.

## 🚀 **Quick Setup:** Follow [SETUP.md](SETUP.md) for installation instructions.

## 🏗️ Architecture

This template enforces **SOLID principles** and **Clean Architecture** patterns:

```
src/your_package_name/
├── domain/          # Business entities and domain services
├── use_cases/       # Application services (business logic)
├── ports/           # Abstract interfaces (dependency inversion)
├── adapters/        # Concrete implementations (DB, HTTP, CLI)
├── infrastructure/  # DI containers, configuration, logging
├── presentation/    # Controllers, CLI, API endpoints
└── shared/          # Cross-cutting utilities
```

## 🚀 Quick Start

### 1. **For New Projects from Template**

```bash
# 1. Clone the template
git clone <this-template> my-new-project
cd my-new-project

# 2. Bootstrap with your package name (lowercase, underscores only)
chmod +x bootstrap.sh
./bootstrap.sh my_package_name

# Examples:
# ./bootstrap.sh order_service
# ./bootstrap.sh data_processor
# ./bootstrap.sh web_api
```

**Package naming rules**: Use lowercase letters, numbers, and underscores only.
- ✅ Good: `user_service`, `data_api`, `ml_pipeline`
- ❌ Bad: `User-Service`, `DataAPI`, `web.api`

### 2. **For Existing Projects**

```bash
# Activate environment and install dependencies
source .venv/bin/activate
pip install -e ".[dev,docs,tools]"
pre-commit install
```

### 3. **Verify Installation**

```bash
# Run quality checks
pre-commit run --all-files

# Run tests
pytest

# Generate documentation
mkdocs serve

# Generate code atlas
python tools/extract_schema.py
python tools/render_graphs.py --repo-url https://github.com/your-org/your-repo/blob/main
```

## 🛠️ Development Workflow

### Code Quality Gates

Every commit is protected by:

- **Code formatting**: Black, isort
- **Type checking**: mypy with strict settings
- **Linting**: flake8, pylint, bandit
- **Docstring enforcement**: pydocstyle, flake8-docstrings
- **Complexity analysis**: radon (cyclomatic & maintainability)
- **Security scanning**: bandit
- **Test coverage**: pytest-cov (≥80% required)

### Documentation Standards

**Mandatory docstrings** for all public APIs using Google style:

```python
def process_order(order_id: str, user_id: str) -> OrderResult:
    """
    Process a customer order through the fulfillment pipeline.

    Args:
        order_id: Unique identifier for the order.
        user_id: Customer's user identifier.

    Returns:
        OrderResult containing processing status and details.

    Raises:
        OrderNotFoundError: If order_id doesn't exist.
        InsufficientInventoryError: If items are out of stock.

    Example:
        >>> result = process_order("ORD-123", "USR-456")
        >>> result.status
        'completed'
    """
```

### Automated Code Atlas

The template automatically generates:

- **Schema extraction** (`docs/schema.json`): Machine-readable API documentation
- **Call graphs** (`docs/atlas/calls.svg`): Function-level dependency visualization
- **Import graphs** (`docs/atlas/imports.svg`): Module dependency visualization
- **Interactive docs** (`mkdocs serve`): Browsable API documentation

## 📊 Quality Metrics

### Complexity Thresholds

- **Cyclomatic Complexity**: ≤ 10 per function
- **Maintainability Index**: ≥ B grade
- **Max function length**: ≤ 60 statements
- **Max function args**: ≤ 6 parameters

### Test Coverage

- **Minimum coverage**: 80%
- **Test types**: Unit, Integration, E2E
- **Test organization**: Mirror `src/` structure in `tests/`

## 🤖 AI Agent Integration

This template is optimized for AI-assisted development:

### For LLM Agents

1. **Read** `DEVELOPER_GUIDE.md` for architecture patterns
2. **Analyze** `docs/schema.json` for current API surface
3. **Review** `docs/atlas/*.svg` for dependency relationships
4. **Follow** docstring templates for consistent documentation
5. **Validate** changes with `pre-commit run --all-files`

### Agent-Friendly Features

- **Single source of truth**: Code generates all documentation
- **Clear contracts**: Comprehensive type hints and docstrings
- **Dependency visualization**: Understand impact of changes
- **Automated validation**: Immediate feedback on code quality
- **Standardized structure**: Predictable file organization

## 🔧 Project Customization

### 1. Update Project Metadata

Edit `pyproject.toml`:
```toml
[project]
name = "your-actual-package-name"
description = "Your project description"
authors = [{name = "Your Name", email = "your.email@domain.com"}]
```

### 2. Rename Package Directory

```bash
mv src/yourpkg src/your_actual_package
# Update imports throughout codebase
```

### 3. Configure Repository URLs

Update in `pyproject.toml` and CI workflows:
```toml
[project.urls]
Homepage = "https://github.com/your-org/your-repo"
Repository = "https://github.com/your-org/your-repo"
```

## 📁 Project Structure

```
project-root/
├── .github/workflows/           # CI/CD pipelines
├── .vscode/                    # VS Code configuration
├── docs/                       # Documentation
│   ├── atlas/                  # Generated graphs
│   ├── schema.json            # API schema
│   └── *.md                   # Manual documentation
├── src/your_package_name/     # Source code
│   ├── domain/                # Business logic
│   ├── use_cases/             # Application services
│   ├── ports/                 # Interfaces
│   ├── adapters/              # Implementations
│   ├── infrastructure/        # Configuration & DI
│   ├── presentation/          # Controllers & CLI
│   └── shared/                # Utilities
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
├── tools/                     # Development tools
├── bootstrap.sh               # Project setup script
├── pyproject.toml             # Project configuration
└── DEVELOPER_GUIDE.md         # Architecture guide
```

## 📚 Documentation

- **Architecture Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- **API Documentation**: `mkdocs serve` (auto-generated)
- **Code Atlas**: `docs/atlas/` (dependency graphs)
- **API Schema**: `docs/schema.json` (machine-readable)

## 🧪 Testing Strategy

### Test Organization
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Service integration tests
└── e2e/           # Full system tests
```

### Running Tests
```bash
# All tests
pytest

# Specific test types
pytest -m unit
pytest -m integration
pytest -m e2e

# With coverage (replace 'your_package_name' with actual package)
pytest --cov=src/your_package_name --cov-report=html
```

## 🔄 Continuous Integration

GitHub Actions workflow includes:

- **Multi-Python versions**: 3.9, 3.10, 3.11, 3.12
- **Cross-platform**: Linux, macOS, Windows
- **Quality gates**: All linting and testing
- **Security scanning**: Bandit, safety
- **Documentation**: Auto-build and deploy
- **Atlas generation**: Dependency graphs
- **Coverage reporting**: Codecov integration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the established patterns
4. Ensure all quality gates pass: `pre-commit run --all-files`
5. Add/update tests and documentation
6. Submit a pull request

## 🙏 Acknowledgments

- **Clean Architecture**: Robert C. Martin
- **Ports & Adapters**: Alistair Cockburn
- **SOLID Principles**: Robert C. Martin
- **Python Tooling**: Black, isort, mypy, pytest, and the amazing Python community
