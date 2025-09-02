# Project Setup - Single Source of Truth

This document provides the **definitive setup instructions** for this project. Choose your scenario below.

## 🆕 **Scenario A: Starting a New Project from Template**

### Step 1: Clone and Customize
```bash
# 1. Clone the template repository
git clone https://github.com/AlgenticsCorp/code_template.git my-new-project
cd my-new-project

# 2. Remove template git history and start fresh
rm -rf .git
git init
git add .
git commit -m "Initial commit from template"
```

### Step 2: Bootstrap with Your Package Name
```bash
# Replace 'my_package_name' with your actual package name
# Package name must be lowercase with underscores (snake_case)
chmod +x bootstrap.sh
./bootstrap.sh my_package_name
```

**Examples of good package names:**
- `./bootstrap.sh order_management`
- `./bootstrap.sh data_processor`
- `./bootstrap.sh web_api`
- `./bootstrap.sh ml_pipeline`

### Step 3: Customize Project Metadata
Edit the automatically updated `pyproject.toml`:
```toml
[project]
name = "my-package-name"  # Already updated by bootstrap
description = "Your project description here"  # ← Update this
authors = [{name = "Your Name", email = "your.email@domain.com"}]  # ← Update this
```

## 🔄 **Scenario B: Working with Existing Project**

If the project is already set up and you're adding new code:

### Step 1: Environment Setup
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install dependencies (if not already done)
pip install -e ".[dev,docs,tools]"

# 3. Install pre-commit hooks (if not already done)
pre-commit install
```

### Step 2: Understand Current Structure
```bash
# Analyze current codebase
python tools/extract_schema.py
cat docs/schema.json

# Review dependency relationships
python tools/render_graphs.py
# View generated files: docs/atlas/calls.svg and docs/atlas/imports.svg
```

### Step 3: Ready to Code!
Follow the [LLM_AGENT_GUIDE.md](LLM_AGENT_GUIDE.md) for development workflow.

## 🤖 **For LLM Agents: Package Name Replacement**

When working with this template, **always replace `yourpkg` with the actual package name**:

### Method 1: Use Bootstrap Script (Recommended)
```bash
./bootstrap.sh actual_package_name
```

### Method 2: Manual Replacement (if needed)
```bash
# Replace all occurrences of 'yourpkg' with your package name
find . -type f -name "*.py" -exec sed -i 's/yourpkg/actual_package_name/g' {} +
find . -type f -name "*.md" -exec sed -i 's/yourpkg/actual_package_name/g' {} +
find . -type f -name "*.toml" -exec sed -i 's/yourpkg/actual_package_name/g' {} +

# Rename the package directory
mv src/yourpkg src/actual_package_name
```

## 🔧 Dependencies

All dependencies are managed in `pyproject.toml`:

- **Core dependencies**: Listed in `[project] dependencies`
- **Development tools**: Listed in `[project.optional-dependencies] dev`
- **Documentation**: Listed in `[project.optional-dependencies] docs`
- **Code analysis tools**: Listed in `[project.optional-dependencies] tools`

Install dependency groups:
```bash
pip install -e ".[dev]"        # Development tools only
pip install -e ".[docs]"       # Documentation tools only
pip install -e ".[tools]"      # Code analysis tools only
pip install -e ".[dev,docs,tools]"  # Everything (recommended)
```

## ✅ Verification Commands

After setup, verify everything works:

```bash
# 1. Code quality checks
pre-commit run --all-files

# 2. Type checking
mypy src/

# 3. Test suite
pytest

# 4. Code atlas generation
python tools/extract_schema.py
python tools/render_graphs.py

# 5. Documentation build
mkdocs serve
```

## 🎯 Daily Development Workflow

```bash
# Activate environment
source .venv/bin/activate

# Before making changes
pre-commit run --all-files
pytest

# After making changes
pre-commit run --all-files
pytest
python tools/extract_schema.py
python tools/render_graphs.py

# Commit changes
git add .
git commit -m "feat(domain): add new feature"
```

## 🚨 Common Issues

### Issue: `pre-commit command not found`
**Solution**: Ensure you've activated the virtual environment and installed dev dependencies.

### Issue: `ModuleNotFoundError: No module named 'yourpkg'`
**Solution**:
1. If using template: Run `./bootstrap.sh your_package_name`
2. If package renamed: Install with `pip install -e .`

### Issue: `Tool not found in PATH`
**Solution**: Install the tools group: `pip install -e ".[tools]"`

### Issue: Bootstrap script fails with "Invalid package name"
**Solution**: Use lowercase letters, numbers, and underscores only. Examples: `my_project`, `data_api`, `ml_service`

## 📋 Package Naming Rules

**✅ Valid package names:**
- `order_service`
- `data_processor`
- `web_api`
- `ml_pipeline`
- `user_management`

**❌ Invalid package names:**
- `Order-Service` (hyphens not allowed)
- `DataProcessor` (CamelCase not allowed)
- `web.api` (dots not allowed)
- `123project` (can't start with number)
- `web-api` (hyphens not allowed)

---

**Note**: This is the single source of truth for setup instructions. Other documentation files reference this document to avoid duplication and ensure consistency.
