# 🛠️ Development Setup Guide

This comprehensive guide will get you from zero to a fully functional development environment for the Molecular Analysis Dashboard.

## 📋 **Prerequisites**

### **Required Software**
- **Python 3.9+** (3.11+ recommended)
- **Node.js 18+** (for frontend development)
- **Docker & Docker Compose** (for services)
- **Git** (for versi# Frontend environment variables (.env.local)
# Gateway-based API access (recommended for production-like development)
VITE_API_BASE_URL=http://localhost/api
VITE_WS_URL=ws://localhost/ws

# Direct API access (for debugging)
# VITE_API_BASE_URL=http://localhost:8000
# VITE_WS_URL=ws://localhost:8000/ws

# CORS settings for backend (.env)
# Gateway handles CORS, but for direct API access:
CORS_ORIGINS=http://localhost,http://localhost:3000,http://127.0.0.1:3000ontrol)

### **System Requirements**
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space for dependencies and Docker images
- **OS**: macOS, Linux, or Windows with WSL2

### **Check Your System**
```bash
# Verify prerequisites
python --version    # Should be 3.9+
node --version      # Should be 18+
docker --version    # Should be 20+
git --version       # Any recent version
```

---

## 🚀 **Step 1: Repository Setup**

### **Clone the Repository**
```bash
# Clone the main repository
git clone https://github.com/AlgenticsCorp/molecular_analysis_dashboard.git
cd molecular_analysis_dashboard

# Or fork first, then clone your fork
git clone https://github.com/YOUR_USERNAME/molecular_analysis_dashboard.git
cd molecular_analysis_dashboard
git remote add upstream https://github.com/AlgenticsCorp/molecular_analysis_dashboard.git
```

### **Explore the Structure**
```bash
# Get familiar with the project layout
tree -L 2
# Or use ls to see top-level directories
ls -la
```

Key directories:
```
molecular_analysis_dashboard/
├── src/                    # Python backend source code
├── frontend/              # React TypeScript frontend
├── database/              # Database setup and migrations
├── docker/                # Docker configurations
├── tests/                 # Test suites
├── docs/                  # Documentation (you're reading this!)
└── tools/                 # Development utilities
```

---

## 🐍 **Step 2: Python Backend Setup**

### **Create Virtual Environment**
```bash
# Create isolated Python environment
python -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Windows (Command Prompt):
.venv\Scripts\activate.bat
```

### **Install Python Dependencies**
```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install project in development mode with all extras
pip install -e ".[dev,docs,tools]"

# Verify installation
python -c "import molecular_analysis_dashboard; print('✅ Backend installed successfully')"
```

### **Set Up Code Quality Tools**
```bash
# Install pre-commit hooks for automated code quality
pre-commit install

# Test pre-commit setup
pre-commit run --all-files
```

This installs hooks for:
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **flake8**: Linting
- **bandit**: Security scanning

---

## 🗄️ **Step 3: Database Setup**

### **Start Database Services**
```bash
# Navigate to database directory
cd database

# Start PostgreSQL and Redis using Docker
make up

# Wait for services to be ready (about 30 seconds)
make health
```

### **Run Database Migrations**
```bash
# Create database schema (22+ tables)
make migrate

# Verify migration success
make migrate-status
```

### **Seed Test Data**
```bash
# Add initial data for development
make seed

# Verify data was created
make shell
# In PostgreSQL shell:
\dt                              # List tables
SELECT COUNT(*) FROM organizations; # Should show test orgs
\q                              # Exit shell
```

### **Database Management Commands**
```bash
# Useful database commands
make down          # Stop database services
make restart       # Restart services
make logs          # View service logs
make backup        # Backup database
make reset         # Complete reset (DANGER: deletes all data)
```

---

## ⚛️ **Step 4: Frontend Setup**

### **Install Node.js Dependencies**
```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Verify installation
npm run type-check
```

### **Frontend Development Commands**
```bash
# Start development server (hot reload enabled)
npm run dev         # Starts on http://localhost:3000

# Other useful commands
npm run build       # Production build
npm run preview     # Preview production build
npm test            # Run tests
npm run lint        # Lint TypeScript/React code
npm run type-check  # TypeScript type checking
```

---

## 🚀 **Step 5: Start Development Services**

### **🐳 Start All Services with Docker Compose (Recommended)**
```bash
# Navigate to project root
cd ../

# Start infrastructure services first
docker compose up -d postgres redis

# Run database migrations
docker compose run --rm migrate

# Start all application services including gateway
docker compose up -d
```

**All services are now accessible through the gateway:**
- **🌐 Dashboard**: http://localhost (frontend through gateway)
- **📊 API Documentation**: http://localhost/api/docs (API through gateway)
- **🔍 Health Check**: http://localhost/health (gateway health status)
- **⚙️ API Endpoints**: http://localhost/api/v1/* (all API routes)

> **✅ Gateway Architecture**: All services route through port 80 for unified access

### **🛠️ Alternative: Individual Service Development**

For debugging specific services, you can also run them individually:

#### **Backend API Only**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Start FastAPI development server (bypass gateway)
uvicorn src.molecular_analysis_dashboard.presentation.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Frontend Only**
```bash
# In a new terminal, navigate to frontend
cd frontend

# Start React development server
npm run dev         # Starts on http://localhost:3000
```

### **Start Background Workers (Optional)**
```bash
# In another terminal, start Celery workers for background tasks
source .venv/bin/activate
celery -A src.molecular_analysis_dashboard.infrastructure.celery_app worker --loglevel=info
```

---

## 🧪 **Step 6: Verify Your Setup**

### **Run Tests**
```bash
# Run backend unit tests (should be fast)
pytest -m unit --tb=short

# Run integration tests (requires database)
pytest -m integration --tb=short

# Run frontend tests
cd frontend
npm test
```

### **Test API Endpoints**
```bash
# Test gateway health (recommended)
curl http://localhost/health
# Should return gateway status and service health

# Test API through gateway
curl http://localhost/api/v1/health
# Should return: {"status": "ok"}

# Direct API access (if running individual services)
curl http://localhost:8000/health
# Should return: {"status": "ok"}

curl http://localhost:8000/ready
# Should return: {"status": "ready", "checks": {...}}
```

### **Test Frontend**
1. Open http://localhost in your browser (gateway-routed frontend)
2. You should see the Molecular Analysis Dashboard interface
3. Try navigating through different sections
4. Test API integration by checking browser dev tools network tab

**Alternative direct access (if running individual services):**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### **End-to-End Verification**
```bash
# Run a simple end-to-end test
pytest tests/e2e/test_basic_workflow.py -v

# If this passes, your setup is complete! 🎉
```

---

## 🔧 **IDE Setup (VS Code Recommended)**

### **Install VS Code Extensions**
```bash
# Install VS Code extensions via command line
code --install-extension ms-python.python
code --install-extension ms-python.pylance
code --install-extension ms-python.black-formatter
code --install-extension bradlc.vscode-tailwindcss
code --install-extension ms-vscode.vscode-typescript-next
code --install-extension esbenp.prettier-vscode
code --install-extension ms-azuretools.vscode-docker
```

### **VS Code Workspace Settings**
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "100"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "typescript.preferences.importModuleSpecifier": "relative",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### **Launch Configuration**
Create `.vscode/launch.json` for debugging:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.molecular_analysis_dashboard.presentation.main:app",
                "--reload"
            ],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        },
        {
            "name": "Python Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/"],
            "console": "integratedTerminal"
        }
    ]
}
```

---

## 🌍 **Environment Configuration**

### **Environment Variables**
Create `.env` file in project root:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://mad:mad_password@localhost:5432/mad
REDIS_URL=redis://localhost:6379/0

# Development settings
DEVELOPMENT=true
DEBUG=true
LOG_LEVEL=DEBUG

# Security (use strong values in production)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
SECRET_KEY=your-super-secret-app-key-change-in-production

# File storage (local for development)
STORAGE_TYPE=local
STORAGE_ROOT=/tmp/molecular_analysis_storage

# API configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Frontend configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME="Molecular Analysis Dashboard (Dev)"
```

### **Load Environment Variables**
The application automatically loads `.env` files. For manual loading:
```bash
# Export environment variables
set -a
source .env
set +a
```

---

## 🐛 **Troubleshooting**

### **Common Issues and Solutions**

#### **"Command not found" Errors**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall project in development mode
pip install -e ".[dev,docs,tools]"
```

#### **Database Connection Issues**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart database services
cd database
make restart
make health
```

#### **Port Already in Use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process (replace PID with actual process ID)
kill -9 PID

# Or use different port
uvicorn src.molecular_analysis_dashboard.presentation.main:app --port 8001
```

#### **Frontend Build Issues**
```bash
# Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### **Python Import Errors**
```bash
# Check Python path
python -c "import sys; print('\\n'.join(sys.path))"

# Ensure project is installed in development mode
pip install -e .

# Check virtual environment
which python
# Should point to .venv/bin/python
```

#### **Test Failures**
```bash
# Run tests with verbose output
pytest -v -s tests/path/to/failing_test.py

# Check test database
cd database
make health

# Reset test database if needed
ALEMBIC_BRANCH=test make migrate-down
ALEMBIC_BRANCH=test make migrate
```

### **Getting Help**

If you're still stuck after trying these solutions:

1. **Check existing issues** on GitHub
2. **Search documentation** for similar problems
3. **Ask in GitHub Discussions** with:
   - Your operating system
   - Python/Node.js versions
   - Complete error message
   - Steps you've already tried

---

## ✅ **Setup Verification Checklist**

Before you start developing, ensure all these work:

### **Backend**
- [ ] Virtual environment activated
- [ ] Dependencies installed without errors
- [ ] Database services running (`make health` succeeds)
- [ ] Migrations applied successfully
- [ ] FastAPI server starts without errors
- [ ] Health endpoint returns {"status": "ok"}
- [ ] Unit tests pass (`pytest -m unit`)

### **Frontend**
- [ ] Node.js dependencies installed
- [ ] TypeScript compilation successful
- [ ] Development server starts
- [ ] Frontend loads in browser
- [ ] No console errors in browser
- [ ] Frontend tests pass (`npm test`)

### **Integration**
- [ ] Frontend can communicate with backend
- [ ] Integration tests pass (`pytest -m integration`)
- [ ] Pre-commit hooks work (`pre-commit run --all-files`)
- [ ] Code quality tools run without errors

### **Development Tools**
- [ ] VS Code opens project without issues
- [ ] Python debugging works in VS Code
- [ ] TypeScript IntelliSense works
- [ ] Git operations work correctly

---

## 🎉 **You're Ready!**

Congratulations! You now have a fully functional development environment for the Molecular Analysis Dashboard.

### **Next Steps**
1. **Read the [Architecture Overview](architecture.md)** to understand the system design
2. **Try the [First Contribution](first-contribution.md)** guide to make your first change
3. **Explore the codebase** - start with `src/molecular_analysis_dashboard/domain/`
4. **Run the full test suite** to see how everything works together
5. **Join the community** - participate in discussions and code reviews

### **Development Workflow**
```bash
# Daily development routine:

# 1. Start your day
source .venv/bin/activate
cd database && make up && cd ..

# 2. Start development servers
uvicorn src.molecular_analysis_dashboard.presentation.main:app --reload &
cd frontend && npm run dev &

# 3. Make changes, run tests
pytest -m unit  # Quick feedback

# 4. Before committing
pre-commit run --all-files
pytest  # Full test suite
```

Happy coding! 🚀
