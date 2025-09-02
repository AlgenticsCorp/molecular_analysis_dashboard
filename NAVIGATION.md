# 🗺️ Repository Navigation Guide

This file helps you navigate the repository efficiently and know exactly where to find what you need.

## 📚 Documentation Hierarchy

### 🎯 **Start Here (Primary Documents)**
1. **[README.md](README.md)** - Project overview and quick start
2. **[SETUP.md](SETUP.md)** - **SINGLE SOURCE OF TRUTH** for installation
3. **[LLM_AGENT_GUIDE.md](LLM_AGENT_GUIDE.md)** - Step-by-step guide for AI agents

### 📖 **Detailed Guides**
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Architecture and development workflow
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines and PR process
- **[GITHUB_WORKFLOW.md](GITHUB_WORKFLOW.md)** - Step-by-step GitHub push instructions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[.docstring-template.md](.docstring-template.md)** - Documentation templates

### 🔧 **Configuration Files**
- **[pyproject.toml](pyproject.toml)** - Project configuration and dependencies
- **[.pre-commit-config.yaml](.pre-commit-config.yaml)** - Quality gate configuration
- **[.flake8](.flake8)** - Linting configuration
- **[mkdocs.yml](mkdocs.yml)** - Documentation site configuration

## 🏗️ Source Code Structure

```
src/your_package_name/
├── __init__.py                  # Package entry point
├── py.typed                     # Type checking marker
├── domain/                      # Business logic (pure)
│   └── __init__.py
├── use_cases/                   # Application services
│   └── __init__.py
├── ports/                       # Abstract interfaces
│   └── __init__.py
├── adapters/                    # External integrations
│   └── __init__.py
├── infrastructure/              # DI and configuration
│   └── __init__.py
├── presentation/                # Controllers and CLI
│   └── __init__.py
└── shared/                      # Cross-cutting utilities
    └── __init__.py
```

## 🧪 Test Structure

```
tests/
├── __init__.py                  # Test package marker
├── conftest.py                  # Pytest configuration
├── unit/                        # Fast, isolated tests
├── integration/                 # Service integration tests
└── e2e/                        # End-to-end tests
```

## 🛠️ Tools and Scripts

```
tools/
├── extract_schema.py           # Generate API documentation
├── render_graphs.py            # Generate dependency graphs
└── health_check.py             # Validate template setup
```

## 📄 Generated Artifacts

```
docs/
├── index.md                    # Documentation homepage
├── api.md                      # API reference
├── schema.json                 # Machine-readable API (generated)
└── atlas/                      # Dependency graphs (generated)
    ├── calls.svg
    └── imports.svg
```

## 🤖 For LLM Agents

### Quick Reference Commands
```bash
# Setup project (with your package name)
./bootstrap.sh your_package_name

# Analyze codebase
python tools/extract_schema.py
cat docs/schema.json

# Check dependencies
python tools/render_graphs.py
# View: docs/atlas/*.svg

# Validate changes
pre-commit run --all-files
pytest
```

### Decision Tree for Agents

**🔍 Need to understand architecture?**
→ Read `DEVELOPER_GUIDE.md`

**🚀 Need to set up environment?**
→ Follow `SETUP.md`

**🔨 Need to make code changes?**
→ Follow `LLM_AGENT_GUIDE.md`

**🤝 Need to contribute?**
→ Read `CONTRIBUTING.md`

**🔀 Need to push code to GitHub?**
→ Follow `GITHUB_WORKFLOW.md`

**❓ Having issues with setup or tools?**
→ Check `TROUBLESHOOTING.md`

**❓ Need to understand current codebase?**
→ Run `python tools/extract_schema.py` and read `docs/schema.json`

**🔗 Need to understand dependencies?**
→ Run `python tools/render_graphs.py` and view `docs/atlas/*.svg`

## 🎯 Common Tasks

| Task | Primary File | Supporting Files |
|------|-------------|------------------|
| **Setup new environment** | SETUP.md | bootstrap.sh (with package name), pyproject.toml |
| **Understand architecture** | DEVELOPER_GUIDE.md | LLM_AGENT_GUIDE.md |
| **Make code changes** | LLM_AGENT_GUIDE.md | DEVELOPER_GUIDE.md |
| **Submit contribution** | CONTRIBUTING.md | SETUP.md |
| **Push code to GitHub** | GITHUB_WORKFLOW.md | CONTRIBUTING.md |
| **Document new code** | .docstring-template.md | DEVELOPER_GUIDE.md |
| **Configure tools** | pyproject.toml | .pre-commit-config.yaml, .flake8 |

## 🚨 Avoiding Confusion

### ✅ **Always Use These for Setup**
- `SETUP.md` - Single source of truth
- `./bootstrap.sh` - Automated setup script
- `pyproject.toml` - Dependency management

### ❌ **Never Use These (Deprecated)**
- ~~requirements.txt~~ - Not used (we use pyproject.toml)
- ~~Manual pip installs~~ - Use bootstrap script or SETUP.md

### 🔄 **Document Update Order**
When making changes that affect setup or architecture:

1. Update source code
2. Update `LLM_AGENT_GUIDE.md` (if patterns change)
3. Update `DEVELOPER_GUIDE.md` (if architecture changes)
4. Update `CONTRIBUTING.md` (if process changes)
5. Update `README.md` (if overview changes)
6. **Never update** `SETUP.md` unless installation process changes

---

**💡 Pro Tip**: Bookmark this file! It's your compass for navigating the entire repository efficiently.
