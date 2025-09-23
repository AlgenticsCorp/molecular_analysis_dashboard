# Development Guides Documentation

*Comprehensive development workflows and practices for the molecular analysis platform.*

## Overview

This section provides essential development guides, workflows, and best practices for contributing to the molecular analysis dashboard, covering everything from local setup to advanced development patterns.

## Development Guide Components

### **[Local Development Setup](local-setup.md)**
Complete guide for setting up the development environment
- Docker-based development environment configuration
- Database setup and migration procedures
- Frontend and backend service coordination
- Environment variable configuration and secrets management
- Development tools and IDE configuration

### **[Testing Strategies](testing.md)**
Comprehensive testing methodologies and implementation
- Unit testing patterns for Clean Architecture layers
- Integration testing for multi-service workflows
- End-to-end testing with molecular analysis pipelines
- Performance testing and benchmarking strategies
- Test data management and fixture creation

### **[Code Quality Standards](code-quality.md)**
Code quality enforcement and best practices
- Linting configuration (Black, isort, flake8, ESLint)
- Type checking with mypy and TypeScript
- Code coverage requirements and reporting
- Pre-commit hooks and automated quality checks
- Documentation standards and requirements

### **[Debugging Techniques](debugging.md)**
Advanced debugging strategies for molecular analysis workflows
- Docker container debugging and log analysis
- Async/await debugging in FastAPI and Celery
- Database query optimization and analysis
- Frontend state debugging with React DevTools
- Performance profiling and bottleneck identification

## Development Workflow

### Docker-First Development
```bash
# Complete development environment startup
cd molecular_analysis_dashboard

# Start core services (always first)
docker compose up -d postgres redis

# Run database migrations
docker compose run --rm migrate

# Start API and worker services
docker compose up -d api worker

# Start frontend (separate terminal)
cd frontend && npm run dev

# Scale workers for development
docker compose up -d --scale worker=2
```

### Environment Configuration
```bash
# Development environment variables
cat > .env.development << EOF
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/molecular_analysis
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=localhost
API_PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Storage (local development)
STORAGE_TYPE=local
STORAGE_PATH=/app/data

# Security (development keys)
JWT_SECRET_KEY=development-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Docking Engines (configure paths as needed)
VINA_EXECUTABLE_PATH=/usr/local/bin/vina
SMINA_EXECUTABLE_PATH=/usr/local/bin/smina
GNINA_EXECUTABLE_PATH=/usr/local/bin/gnina
EOF
```

### Development Server Management
```python
# Development server orchestration
import asyncio
import subprocess
import signal
import sys
from pathlib import Path

class DevelopmentServerManager:
    """Orchestrate development services"""

    def __init__(self):
        self.processes = {}
        self.project_root = Path(__file__).parent.parent

    async def start_services(self):
        """Start all development services in correct order"""

        print("🐳 Starting Docker services...")
        await self.run_command([
            "docker", "compose", "up", "-d",
            "postgres", "redis"
        ])

        print("⏳ Waiting for services to be ready...")
        await asyncio.sleep(5)

        print("🗄️  Running database migrations...")
        await self.run_command([
            "docker", "compose", "run", "--rm", "migrate"
        ])

        print("🚀 Starting API and worker services...")
        await self.run_command([
            "docker", "compose", "up", "-d",
            "api", "worker"
        ])

        print("⚛️  Starting frontend development server...")
        self.processes['frontend'] = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=self.project_root / "frontend"
        )

        print("✅ All services started successfully!")
        print("🌐 API: http://localhost:8000")
        print("🌐 Frontend: http://localhost:5173")
        print("📚 API Docs: http://localhost:8000/docs")

    async def stop_services(self):
        """Stop all development services"""

        print("🛑 Stopping development services...")

        # Stop frontend process
        if 'frontend' in self.processes:
            self.processes['frontend'].terminate()

        # Stop Docker services
        await self.run_command([
            "docker", "compose", "down"
        ])

        print("✅ All services stopped")

    async def run_command(self, command):
        """Run command with proper error handling"""
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(command)}\n{stderr.decode()}")

        return stdout.decode()

# CLI script for development
if __name__ == "__main__":
    manager = DevelopmentServerManager()

    def signal_handler(signum, frame):
        asyncio.create_task(manager.stop_services())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        asyncio.run(manager.stop_services())
    else:
        asyncio.run(manager.start_services())

        # Keep running
        try:
            while True:
                asyncio.sleep(1)
        except KeyboardInterrupt:
            asyncio.run(manager.stop_services())
```

### Code Quality Automation
```python
# Pre-commit hook configuration
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11
        exclude: ^(migrations/|frontend/)

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
        exclude: ^(migrations/|frontend/)

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        exclude: ^(migrations/|frontend/)
        args: [
          "--max-line-length=88",
          "--extend-ignore=E203,W503"
        ]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
        exclude: ^(migrations/|frontend/|tests/)
        additional_dependencies: [types-all]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.4
    hooks:
      - id: bandit
        exclude: ^(tests/|frontend/)
        args: ["-r", ".", "-x", "tests"]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.35.0
    hooks:
      - id: eslint
        files: ^frontend/.*\.(js|jsx|ts|tsx)$
        additional_dependencies:
          - eslint@8.35.0
          - "@typescript-eslint/parser"
          - "@typescript-eslint/eslint-plugin"

# Quality check script
#!/bin/bash
# scripts/check-quality.sh

set -e

echo "🔍 Running code quality checks..."

echo "📝 Running Black formatter..."
black --check src/ tests/

echo "📦 Running isort import sorter..."
isort --check-only src/ tests/

echo "🔬 Running flake8 linter..."
flake8 src/ tests/

echo "🎯 Running mypy type checker..."
mypy src/

echo "🛡️ Running bandit security checker..."
bandit -r src/ -x tests/

echo "⚛️ Running frontend linting..."
cd frontend
npm run lint
npm run type-check

echo "✅ All quality checks passed!"
```

### Testing Workflow
```python
# Comprehensive testing script
#!/usr/bin/env python3
# scripts/run-tests.py

import asyncio
import subprocess
import sys
from pathlib import Path

class TestRunner:
    """Orchestrate comprehensive testing workflow"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}

    async def run_all_tests(self):
        """Run complete test suite"""

        print("🧪 Starting comprehensive test suite...")

        # Start test database
        await self.start_test_database()

        try:
            # Run backend tests
            await self.run_backend_tests()

            # Run frontend tests
            await self.run_frontend_tests()

            # Run integration tests
            await self.run_integration_tests()

            # Run E2E tests
            await self.run_e2e_tests()

        finally:
            await self.cleanup_test_database()

        self.report_results()

    async def run_backend_tests(self):
        """Run backend test suite"""

        print("🐍 Running backend tests...")

        # Unit tests
        result = await self.run_pytest([
            "tests/unit/",
            "--cov=src/molecular_analysis_dashboard",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
        self.test_results['backend_unit'] = result

        # Integration tests
        result = await self.run_pytest([
            "tests/integration/",
            "-v"
        ])
        self.test_results['backend_integration'] = result

    async def run_frontend_tests(self):
        """Run frontend test suite"""

        print("⚛️ Running frontend tests...")

        # Unit tests
        result = await self.run_command([
            "npm", "test", "--", "--coverage"
        ], cwd=self.project_root / "frontend")
        self.test_results['frontend_unit'] = result

        # Type checking
        result = await self.run_command([
            "npm", "run", "type-check"
        ], cwd=self.project_root / "frontend")
        self.test_results['frontend_types'] = result

    async def run_integration_tests(self):
        """Run cross-service integration tests"""

        print("🔗 Running integration tests...")

        result = await self.run_pytest([
            "tests/integration/api/",
            "tests/integration/workflows/",
            "-v", "--tb=short"
        ])
        self.test_results['integration'] = result

    async def run_e2e_tests(self):
        """Run end-to-end tests"""

        print("🎭 Running E2E tests...")

        # Start E2E test environment
        await self.run_command([
            "docker", "compose", "-f", "docker-compose.test.yml",
            "up", "--abort-on-container-exit"
        ])

        self.test_results['e2e'] = True

    async def start_test_database(self):
        """Start test database services"""
        await self.run_command([
            "docker", "compose", "up", "-d",
            "postgres-test", "redis-test"
        ])

        # Wait for services to be ready
        await asyncio.sleep(5)

    async def cleanup_test_database(self):
        """Clean up test database"""
        await self.run_command([
            "docker", "compose", "down", "-v"
        ])

    async def run_pytest(self, args):
        """Run pytest with given arguments"""
        try:
            await self.run_command(["python", "-m", "pytest"] + args)
            return True
        except RuntimeError:
            return False

    async def run_command(self, command, cwd=None):
        """Run command with error handling"""
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd or self.project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"❌ Command failed: {' '.join(command)}")
            print(f"Error: {stderr.decode()}")
            raise RuntimeError(f"Command failed: {' '.join(command)}")

        return stdout.decode()

    def report_results(self):
        """Report test results summary"""

        print("\n📊 Test Results Summary:")
        print("=" * 50)

        for test_type, passed in self.test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_type:20} {status}")

        all_passed = all(self.test_results.values())

        if all_passed:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed!")
            sys.exit(1)

if __name__ == "__main__":
    runner = TestRunner()
    asyncio.run(runner.run_all_tests())
```

## Development Best Practices

### Clean Architecture Development
- **Dependency Direction**: Always point dependencies inward toward domain layer
- **Interface Segregation**: Define narrow, focused interfaces in ports layer
- **Dependency Injection**: Use dependency injection for all external dependencies
- **Pure Domain Logic**: Keep domain entities free of framework dependencies
- **Use Case Orchestration**: Coordinate domain logic through use case classes

### Async/Await Patterns
- **Consistent Async**: Use async/await throughout the stack
- **Connection Management**: Properly manage database connections in async context
- **Error Handling**: Handle async exceptions appropriately
- **Testing**: Test async functions with pytest-asyncio
- **Performance**: Profile async performance under concurrent load

### Multi-Tenant Development
- **Context Setting**: Always set tenant context for database operations
- **Data Isolation**: Verify tenant isolation in all development
- **Resource Limits**: Consider per-tenant resource limits
- **Testing**: Test multi-tenant scenarios extensively
- **Performance**: Monitor per-tenant performance metrics

### Container Development
- **Local Development**: Use Docker for consistent development environment
- **Volume Mounting**: Mount source code for live reload
- **Environment Parity**: Keep development/production environments similar
- **Resource Allocation**: Allocate appropriate resources for development containers
- **Debugging**: Configure containers for debugging support

## Related Documentation

- **[Local Development Tools](../tools/README.md)** - Development utilities and scripts
- **[Architecture Patterns](../../architecture/README.md)** - Clean Architecture implementation
- **[Database Management](../../database/management/README.md)** - Database development procedures
- **[API Development](../../api/README.md)** - API development guidelines
- **[Deployment Guides](../../deployment/README.md)** - Deployment and CI/CD setup
