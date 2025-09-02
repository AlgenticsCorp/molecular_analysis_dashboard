#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Bootstrapping Professional Python Project Template...${NC}"

# --- 0) Get package name from user ---
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <package_name>${NC}"
    echo -e "${YELLOW}Example: $0 my_awesome_project${NC}"
    echo ""
    echo -e "${RED}Error: Package name is required${NC}"
    echo "The package name should be:"
    echo "  - Python-compatible (letters, numbers, underscores)"
    echo "  - Lowercase with underscores (snake_case)"
    echo "  - Descriptive of your project"
    exit 1
fi

PACKAGE_NAME="$1"

# Validate package name
if ! echo "$PACKAGE_NAME" | grep -qE '^[a-z][a-z0-9_]*$'; then
    echo -e "${RED}Error: Invalid package name '$PACKAGE_NAME'${NC}"
    echo "Package name must:"
    echo "  - Start with a lowercase letter"
    echo "  - Contain only lowercase letters, numbers, and underscores"
    echo "  - Use snake_case convention"
    echo ""
    echo "Examples of valid names: my_project, data_processor, web_api"
    exit 1
fi

echo -e "${GREEN}✓ Using package name: $PACKAGE_NAME${NC}"

# --- 1) Setup virtual environment ---
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}📦 Setting up virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists, skipping creation${NC}"
fi

source .venv/bin/activate
python -m pip install --upgrade pip

# --- 2) Project structure ---
echo -e "${BLUE}📁 Creating project structure for package '$PACKAGE_NAME'...${NC}"

# Create directories only if they don't exist
create_dir_if_not_exists() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo -e "${GREEN}✓ Created: $1${NC}"
    else
        echo -e "${YELLOW}⚠️  Already exists: $1${NC}"
    fi
}

create_dir_if_not_exists "src/$PACKAGE_NAME"
create_dir_if_not_exists "src/$PACKAGE_NAME/domain/entities"
create_dir_if_not_exists "src/$PACKAGE_NAME/domain/services"
create_dir_if_not_exists "src/$PACKAGE_NAME/domain/value_objects"
create_dir_if_not_exists "src/$PACKAGE_NAME/domain/events"
create_dir_if_not_exists "src/$PACKAGE_NAME/use_cases/commands"
create_dir_if_not_exists "src/$PACKAGE_NAME/use_cases/queries"
create_dir_if_not_exists "src/$PACKAGE_NAME/ports/repository"
create_dir_if_not_exists "src/$PACKAGE_NAME/ports/notification"
create_dir_if_not_exists "src/$PACKAGE_NAME/ports/external"
create_dir_if_not_exists "src/$PACKAGE_NAME/adapters/database"
create_dir_if_not_exists "src/$PACKAGE_NAME/adapters/http"
create_dir_if_not_exists "src/$PACKAGE_NAME/adapters/messaging"
create_dir_if_not_exists "src/$PACKAGE_NAME/adapters/filesystem"
create_dir_if_not_exists "src/$PACKAGE_NAME/infrastructure"
create_dir_if_not_exists "src/$PACKAGE_NAME/presentation"
create_dir_if_not_exists "src/$PACKAGE_NAME/shared"
create_dir_if_not_exists "tests/unit/domain"
create_dir_if_not_exists "tests/unit/use_cases"
create_dir_if_not_exists "tests/unit/adapters"
create_dir_if_not_exists "tests/integration"
create_dir_if_not_exists "tests/e2e"
create_dir_if_not_exists "tools"
create_dir_if_not_exists "docs/atlas"
create_dir_if_not_exists "docs/getting-started"
create_dir_if_not_exists ".vscode"
create_dir_if_not_exists ".github/workflows"

# --- 3) Create source files only if they don't exist ---
echo -e "${BLUE}📝 Creating source files...${NC}"

create_file_if_not_exists() {
    if [ ! -f "$1" ]; then
        cat > "$1" <<EOF
$2
EOF
        echo -e "${GREEN}✓ Created: $1${NC}"
    else
        echo -e "${YELLOW}⚠️  Already exists: $1${NC}"
    fi
}

# Package init files
create_file_if_not_exists "src/$PACKAGE_NAME/__init__.py" "\"\"\"
$PACKAGE_NAME package root module.

Details:
- Entry point for the application
- Exports main public interfaces
- Provides version information
\"\"\"

__version__ = \"0.1.0\"
__author__ = \"Your Name\"
__email__ = \"your.email@company.com\"

__all__ = [
    \"__version__\",
    \"__author__\",
    \"__email__\",
]"

# Type marker
create_file_if_not_exists "src/$PACKAGE_NAME/py.typed" ""

# Layer init files
create_file_if_not_exists "src/$PACKAGE_NAME/domain/__init__.py" "\"\"\"Domain layer - pure business logic.\"\"\""
create_file_if_not_exists "src/$PACKAGE_NAME/use_cases/__init__.py" "\"\"\"Use cases layer - application services.\"\"\""
create_file_if_not_exists "src/$PACKAGE_NAME/ports/__init__.py" "\"\"\"Ports layer - abstract interfaces.\"\"\""
create_file_if_not_exists "src/$PACKAGE_NAME/adapters/__init__.py" "\"\"\"Adapters layer - external integrations.\"\"\""
create_file_if_not_exists "src/$PACKAGE_NAME/infrastructure/__init__.py" "\"\"\"Infrastructure layer - configuration and dependency injection.\"\"\""
create_file_if_not_exists "src/$PACKAGE_NAME/presentation/__init__.py" "\"\"\"Presentation layer - controllers and CLI.\"\"\""
create_file_if_not_exists "src/$PACKAGE_NAME/shared/__init__.py" "\"\"\"Shared utilities layer.\"\"\""

# Test files
create_file_if_not_exists "tests/__init__.py" "\"\"\"Test package.\"\"\""
create_file_if_not_exists "tests/conftest.py" "\"\"\"Pytest configuration and shared fixtures.\"\"\"
import pytest


@pytest.fixture
def sample_fixture():
    \"\"\"Sample fixture for testing.\"\"\"
    return \"test_data\""

# --- 4) Update pyproject.toml with package name ---
if [ -f "pyproject.toml" ]; then
    echo -e "${BLUE}🔧 Updating pyproject.toml with package name...${NC}"
    # Update package name in pyproject.toml
    sed -i.backup "s/your-package-name/$PACKAGE_NAME/g" pyproject.toml
    sed -i.backup "s/yourpkg\\./$PACKAGE_NAME\\./g" pyproject.toml
    sed -i.backup "s/yourpkg/$PACKAGE_NAME/g" pyproject.toml
    rm pyproject.toml.backup 2>/dev/null || true
    echo -e "${GREEN}✓ Updated pyproject.toml${NC}"
else
    echo -e "${YELLOW}⚠️  pyproject.toml not found, skipping update${NC}"
fi

# --- 5) Install dependencies ---
echo -e "${BLUE}📦 Installing dependencies...${NC}"
if pip install -e ".[dev,docs,tools]"; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    echo -e "${YELLOW}💡 Try running manually: pip install -e '.[dev,docs,tools]'${NC}"
    exit 1
fi

# --- 6) Setup pre-commit hooks ---
if [ -f ".pre-commit-config.yaml" ]; then
    echo -e "${BLUE}🔧 Setting up pre-commit hooks...${NC}"
    if pre-commit install; then
        echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
    else
        echo -e "${YELLOW}⚠️  Pre-commit installation failed, continuing...${NC}"
        echo -e "${YELLOW}💡 Try running manually later: pre-commit install${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  .pre-commit-config.yaml not found, skipping pre-commit setup${NC}"
fi

# --- 7) Run health check ---
echo -e "${BLUE}🔍 Running health check...${NC}"
if python tools/health_check.py; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Health check found issues, but bootstrap completed${NC}"
    echo -e "${YELLOW}💡 Run 'python tools/health_check.py' for details${NC}"
fi

echo ""
echo -e "${GREEN}✅ Bootstrap complete for package '$PACKAGE_NAME'!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Review and customize pyproject.toml metadata"
echo "2. Read DEVELOPER_GUIDE.md for development workflow"
echo "3. Read LLM_AGENT_GUIDE.md for AI agent instructions"
echo "4. Run: pre-commit run --all-files"
echo "5. Run: pytest"
echo "6. Run: python tools/extract_schema.py"
echo "7. Run: python tools/render_graphs.py"
echo ""
echo -e "${YELLOW}💡 Pro tip: Your package is now available as 'src/$PACKAGE_NAME'${NC}"
