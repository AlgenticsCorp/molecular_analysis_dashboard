# Troubleshooting Guide

This guide helps resolve common issues with the template setup and development workflow.

## Quick Diagnostics

Run the health check first:
```bash
python tools/health_check.py
```

## Common Issues

### 1. Pre-commit Hook Failures

**Problem**: Pre-commit hooks fail during commit
```
❌ mypy failed
❌ black failed
❌ isort failed
```

**Solutions**:

1. **Auto-fix formatting issues**:
   ```bash
   pre-commit run --all-files
   ```

2. **Skip hooks temporarily** (emergency only):
   ```bash
   git commit -m "fix: emergency commit" --no-verify
   ```

3. **Check specific hook**:
   ```bash
   pre-commit run mypy --all-files
   pre-commit run black --all-files
   ```

### 2. Missing Dependencies

**Problem**: Import errors or command not found
```
ModuleNotFoundError: No module named 'pytest'
Command 'pre-commit' not found
```

**Solutions**:

1. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Reinstall dependencies**:
   ```bash
   pip install -e ".[dev,docs,tools]"
   ```

3. **Check Python version**:
   ```bash
   python --version  # Should be >= 3.9
   ```

### 3. Coverage Failures

**Problem**: Tests pass but coverage fails
```
❌ Coverage below 80%
```

**Solutions**:

1. **Check current coverage**:
   ```bash
   pytest --cov=src/yourpkg --cov-report=term-missing
   ```

2. **For template usage** (disable strict coverage):
   ```toml
   # In pyproject.toml [tool.pytest.ini_options]
   addopts = "--cov=src --cov-report=term-missing"
   # Remove: "--cov-fail-under=80"
   ```

3. **Add missing tests**:
   - Focus on uncovered lines shown in report
   - Add unit tests for business logic
   - Integration tests for adapters

### 4. MyPy Type Errors

**Problem**: Type checking failures
```
❌ error: Cannot find implementation or library stub
❌ error: Incompatible return value type
```

**Solutions**:

1. **Install type stubs**:
   ```bash
   pip install types-requests types-python-dateutil
   ```

2. **Add type ignores** (temporary):
   ```python
   import requests  # type: ignore
   ```

3. **Check mypy configuration**:
   ```toml
   # In pyproject.toml
   [tool.mypy]
   python_version = "3.9"
   strict = true
   ignore_missing_imports = true
   ```

### 5. Tool Compatibility Issues

**Problem**: Optional tools fail (pyan3, radon, etc.)
```
❌ Command 'pyan3' not found
❌ radon failed
```

**Solutions**:

1. **Install optional tools**:
   ```bash
   pip install pyan3 radon
   ```

2. **Skip optional tools**:
   ```bash
   # Remove from .pre-commit-config.yaml or disable
   python tools/render_graphs.py  # Has built-in fallbacks
   ```

3. **System dependencies** (for graph rendering):
   ```bash
   # macOS
   brew install graphviz

   # Ubuntu/Debian
   sudo apt-get install graphviz
   ```

### 6. Bootstrap Script Issues

**Problem**: Bootstrap fails during setup
```
❌ Failed to install dependencies
❌ Invalid package name
```

**Solutions**:

1. **Check package name format**:
   ```bash
   ./bootstrap.sh my_project        # ✅ Good
   ./bootstrap.sh MyProject         # ❌ Bad
   ./bootstrap.sh my-project        # ❌ Bad
   ```

2. **Manual dependency installation**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -e ".[dev,docs,tools]"
   ```

3. **Check Python and pip**:
   ```bash
   python3 --version
   pip --version
   which python3
   ```

### 7. GitHub Actions CI Failures

**Problem**: CI pipeline fails on GitHub
```
❌ Tests failed
❌ Quality gates failed
❌ Documentation build failed
```

**Solutions**:

1. **Test locally first**:
   ```bash
   # Run same checks as CI
   pre-commit run --all-files
   pytest
   python tools/health_check.py
   ```

2. **Check Python version matrix**:
   - CI tests on Python 3.9, 3.10, 3.11, 3.12
   - Ensure compatibility across versions

3. **Review GitHub workflow**:
   - Check `.github/workflows/` files
   - Verify secret environment variables
   - Check branch protection rules

### 8. Documentation Issues

**Problem**: Docs don't build or render incorrectly
```
❌ mkdocs build failed
❌ API docs missing
```

**Solutions**:

1. **Build docs locally**:
   ```bash
   mkdocs serve  # Development server
   mkdocs build  # Production build
   ```

2. **Update API documentation**:
   ```bash
   python tools/extract_schema.py
   ```

3. **Check mkdocs configuration**:
   ```yaml
   # In mkdocs.yml
   site_name: Your Project
   theme:
     name: material
   ```

## Environment Reset

If all else fails, reset the environment:

```bash
# 1. Clean virtual environment
rm -rf .venv
rm -rf .pytest_cache
rm -rf __pycache__
find . -name "*.pyc" -delete

# 2. Fresh bootstrap
./bootstrap.sh your_package_name

# 3. Verify setup
python tools/health_check.py
pre-commit run --all-files
pytest
```

## Getting Help

1. **Run diagnostics**:
   ```bash
   python tools/health_check.py
   ```

2. **Check logs**:
   ```bash
   pre-commit run --all-files --verbose
   pytest -v
   ```

3. **Gather system info**:
   ```bash
   python --version
   pip list
   pre-commit --version
   ```

4. **Review documentation**:
   - `DEVELOPER_GUIDE.md` - Development workflow
   - `LLM_AGENT_GUIDE.md` - AI agent instructions
   - `GITHUB_WORKFLOW.md` - Git workflow
   - `README.md` - Project overview

## Emergency Procedures

### Skip All Quality Checks
```bash
git commit -m "emergency: bypass checks" --no-verify
git push origin main --no-verify
```

### Force Push (Use with caution)
```bash
git push origin main --force-with-lease
```

### Reset to Known Good State
```bash
git fetch origin
git reset --hard origin/main
```

Remember: These emergency procedures should only be used when absolutely necessary and with team coordination.
