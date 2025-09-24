# Development Tools Documentation

*Essential development utilities, scripts, and automation tools for the molecular analysis platform.*

## Overview

This section provides comprehensive documentation for development tools, utilities, and automation scripts that enhance developer productivity and maintain code quality throughout the molecular analysis dashboard project.

## Development Tool Components

### **[Development Tools](development-tools.md)**
Build system configuration and automation
- Docker build optimization and multi-stage builds
- Frontend build pipeline with Vite and TypeScript
- Python packaging and distribution setup
- Development vs production build configurations
- Asset optimization and bundling strategies

### **[Testing & Development Tools](development-tools.md)**
Test automation and quality assurance utilities
- Pytest configuration and custom fixtures
- Test data generation and molecular structure creation
- Coverage reporting and quality gates
- Performance testing and benchmarking tools
- Mock services for external docking engines

### **[LLM Agent Guide](llm-agent-guide.md)**
Automation scripts for common development tasks
- Environment setup and teardown scripts
- Database management and migration utilities
- Code generation and scaffolding tools
- Data seeding and fixture creation scripts
- Docker container management automation

### **[Development Tools](development-tools.md)**
Code quality enforcement and analysis utilities
- Linting and formatting tool configuration
- Type checking setup and validation
- Security scanning and vulnerability analysis
- Documentation generation and validation
- Pre-commit hooks and automated quality checks

## Essential Development Tools

### Project Automation Scripts
```bash
# scripts/dev-setup.sh - Complete development environment setup
#!/bin/bash

set -e

echo "🧬 Setting up Molecular Analysis Dashboard development environment..."

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not installed"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not installed"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 not installed"; exit 1; }

echo "✅ Prerequisites check passed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating development .env file..."
    cp .env.example .env
    echo "⚠️  Please review and update .env file with your configuration"
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Start Docker services
echo "🐳 Starting Docker services..."
docker compose up -d postgres redis

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
docker compose run --rm migrate

# Create development data
echo "🌱 Seeding development data..."
python scripts/seed-dev-data.py

echo "🎉 Development environment setup complete!"
echo ""
echo "🚀 Quick start:"
echo "  docker compose up -d api worker  # Start backend services"
echo "  cd frontend && npm run dev       # Start frontend (separate terminal)"
echo ""
echo "🌐 URLs:"
echo "  Frontend: http://localhost:5173"
echo "  API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
```

### Database Management Utilities
```python
# scripts/db-manager.py - Database management utility
import asyncio
import sys
import uuid
from pathlib import Path
from typing import Optional

import asyncpg
import typer
from sqlalchemy.ext.asyncio import create_async_engine

app = typer.Typer(help="Database management utilities")

class DatabaseManager:
    """Database management utilities"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url)

    async def create_test_organization(self, name: str) -> str:
        """Create a test organization with sample data"""

        org_id = str(uuid.uuid4())

        async with self.engine.begin() as conn:
            # Create organization
            await conn.execute(
                """
                INSERT INTO organizations (id, name, tier, created_at)
                VALUES ($1, $2, 'standard', NOW())
                """,
                org_id, name
            )

            # Create sample molecules
            molecules = [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Aspirin',
                    'smiles': 'CC(=O)OC1=CC=CC=C1C(=O)O',
                    'molecular_weight': 180.16
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Ibuprofen',
                    'smiles': 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O',
                    'molecular_weight': 206.28
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Acetaminophen',
                    'smiles': 'CC(=O)NC1=CC=C(C=C1)O',
                    'molecular_weight': 151.16
                }
            ]

            for mol in molecules:
                await conn.execute(
                    """
                    INSERT INTO molecules (id, organization_id, name, smiles, molecular_weight, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    """,
                    mol['id'], org_id, mol['name'], mol['smiles'], mol['molecular_weight']
                )

            # Create sample docking pipeline
            pipeline_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO pipelines (id, organization_id, name, engine_type, parameters, created_at)
                VALUES ($1, $2, 'Development Pipeline', 'vina', '{"exhaustiveness": 8}', NOW())
                """,
                pipeline_id, org_id
            )

            print(f"✅ Created organization '{name}' with ID: {org_id}")
            print(f"   📊 Added {len(molecules)} sample molecules")
            print(f"   🔧 Created development pipeline")

            return org_id

    async def reset_database(self, confirm: bool = False):
        """Reset database to clean state"""

        if not confirm:
            typer.confirm("⚠️  This will DELETE ALL DATA. Are you sure?", abort=True)

        async with self.engine.begin() as conn:
            # Drop all data (preserve schema)
            tables = [
                'job_results', 'docking_jobs', 'molecules',
                'pipelines', 'users', 'organizations'
            ]

            for table in tables:
                await conn.execute(f"TRUNCATE TABLE {table} CASCADE")

            print("🗑️  Database reset complete")

    async def backup_database(self, output_file: Path):
        """Create database backup"""

        import subprocess

        # Use pg_dump for backup
        cmd = [
            'pg_dump',
            '--no-owner',
            '--no-privileges',
            '--clean',
            '--if-exists',
            '--file', str(output_file),
            self.database_url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Database backup saved to {output_file}")
        else:
            print(f"❌ Backup failed: {result.stderr}")
            raise typer.Exit(1)

    async def restore_database(self, backup_file: Path):
        """Restore database from backup"""

        if not backup_file.exists():
            print(f"❌ Backup file not found: {backup_file}")
            raise typer.Exit(1)

        import subprocess

        cmd = [
            'psql',
            '--single-transaction',
            '--file', str(backup_file),
            self.database_url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Database restored from {backup_file}")
        else:
            print(f"❌ Restore failed: {result.stderr}")
            raise typer.Exit(1)

@app.command()
def create_org(
    name: str = typer.Argument(..., help="Organization name"),
    database_url: str = typer.Option(
        "postgresql://postgres:password@localhost/molecular_analysis",
        help="Database URL"
    )
):
    """Create test organization with sample data"""

    manager = DatabaseManager(database_url)

    async def run():
        await manager.create_test_organization(name)

    asyncio.run(run())

@app.command()
def reset(
    confirm: bool = typer.Option(False, "--yes", help="Skip confirmation"),
    database_url: str = typer.Option(
        "postgresql://postgres:password@localhost/molecular_analysis",
        help="Database URL"
    )
):
    """Reset database to clean state"""

    manager = DatabaseManager(database_url)

    async def run():
        await manager.reset_database(confirm)

    asyncio.run(run())

@app.command()
def backup(
    output_file: Path = typer.Argument(..., help="Output backup file"),
    database_url: str = typer.Option(
        "postgresql://postgres:password@localhost/molecular_analysis",
        help="Database URL"
    )
):
    """Create database backup"""

    manager = DatabaseManager(database_url)

    async def run():
        await manager.backup_database(output_file)

    asyncio.run(run())

@app.command()
def restore(
    backup_file: Path = typer.Argument(..., help="Backup file to restore"),
    database_url: str = typer.Option(
        "postgresql://postgres:password@localhost/molecular_analysis",
        help="Database URL"
    )
):
    """Restore database from backup"""

    manager = DatabaseManager(database_url)

    async def run():
        await manager.restore_database(backup_file)

    asyncio.run(run())

if __name__ == "__main__":
    app()
```

### Code Generation Utilities
```python
# scripts/generate-component.py - Component generation utility
import typer
from pathlib import Path
from typing import Optional
import re

app = typer.Typer(help="Code generation utilities")

class ComponentGenerator:
    """Generate boilerplate code for common components"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_root = project_root / "src" / "molecular_analysis_dashboard"
        self.frontend_root = project_root / "frontend" / "src"

    def generate_domain_entity(self, name: str) -> Path:
        """Generate domain entity with basic structure"""

        class_name = self._to_pascal_case(name)
        file_name = self._to_snake_case(name)

        entity_code = f'''"""
{class_name} domain entity for molecular analysis platform.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class {class_name}(BaseModel):
    """
    {class_name} domain entity.

    Represents a {name.lower()} in the molecular analysis system.
    """

    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        validate_assignment = True

    def __str__(self) -> str:
        return f"{class_name}(id={{self.id}}, name='{{self.name}}')"

    def __repr__(self) -> str:
        return (
            f"{class_name}("
            f"id={{self.id!r}}, "
            f"organization_id={{self.organization_id!r}}, "
            f"name={{self.name!r}})"
        )
'''

        entity_file = self.src_root / "domain" / "entities" / f"{file_name}.py"
        entity_file.parent.mkdir(parents=True, exist_ok=True)
        entity_file.write_text(entity_code.strip())

        return entity_file

    def generate_repository_port(self, name: str) -> Path:
        """Generate repository port interface"""

        class_name = self._to_pascal_case(name)
        file_name = self._to_snake_case(name)

        port_code = f'''"""
{class_name} repository port interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..domain.entities.{file_name} import {class_name}


class {class_name}RepositoryPort(ABC):
    """
    Repository port for {class_name} entities.

    Defines the contract for {class_name.lower()} data persistence operations.
    """

    @abstractmethod
    async def create(self, {file_name}: {class_name}) -> {class_name}:
        """
        Create a new {class_name.lower()}.

        Args:
            {file_name}: The {class_name.lower()} to create.

        Returns:
            The created {class_name.lower()} with assigned ID.

        Raises:
            RepositoryError: If creation fails.
        """
        pass

    @abstractmethod
    async def find_by_id(self, {file_name}_id: UUID) -> Optional[{class_name}]:
        """
        Find {class_name.lower()} by ID.

        Args:
            {file_name}_id: The {class_name.lower()} ID.

        Returns:
            The {class_name.lower()} if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_organization(self, organization_id: UUID) -> List[{class_name}]:
        """
        Find all {class_name.lower()}s for an organization.

        Args:
            organization_id: The organization ID.

        Returns:
            List of {class_name.lower()}s belonging to the organization.
        """
        pass

    @abstractmethod
    async def update(self, {file_name}: {class_name}) -> {class_name}:
        """
        Update an existing {class_name.lower()}.

        Args:
            {file_name}: The {class_name.lower()} to update.

        Returns:
            The updated {class_name.lower()}.

        Raises:
            RepositoryError: If update fails.
            NotFoundError: If {class_name.lower()} not found.
        """
        pass

    @abstractmethod
    async def delete(self, {file_name}_id: UUID) -> bool:
        """
        Delete a {class_name.lower()}.

        Args:
            {file_name}_id: The {class_name.lower()} ID.

        Returns:
            True if deleted successfully, False if not found.

        Raises:
            RepositoryError: If deletion fails.
        """
        pass
'''

        port_file = self.src_root / "ports" / "repository" / f"{file_name}_repository_port.py"
        port_file.parent.mkdir(parents=True, exist_ok=True)
        port_file.write_text(port_code.strip())

        return port_file

    def generate_use_case(self, entity_name: str, action: str) -> Path:
        """Generate use case for entity action"""

        entity_class = self._to_pascal_case(entity_name)
        action_class = self._to_pascal_case(action)
        file_name = f"{self._to_snake_case(action)}_{self._to_snake_case(entity_name)}_use_case"

        use_case_code = f'''"""
{action_class} {entity_class} use case implementation.
"""

from typing import Optional
from uuid import UUID

from ..domain.entities.{self._to_snake_case(entity_name)} import {entity_class}
from ..ports.repository.{self._to_snake_case(entity_name)}_repository_port import {entity_class}RepositoryPort
from ..shared.exceptions import NotFoundError, UseCaseError


class {action_class}{entity_class}UseCase:
    """
    Use case for {action.lower()}ing {entity_name.lower()}s.

    Orchestrates the business logic for {action.lower()}ing {entity_class} entities
    while maintaining clean architecture principles.
    """

    def __init__(self, {self._to_snake_case(entity_name)}_repository: {entity_class}RepositoryPort):
        self._{self._to_snake_case(entity_name)}_repository = {self._to_snake_case(entity_name)}_repository

    async def execute(self, organization_id: UUID, {self._to_snake_case(entity_name)}_data: dict) -> {entity_class}:
        """
        Execute the {action.lower()} {entity_name.lower()} use case.

        Args:
            organization_id: The organization ID.
            {self._to_snake_case(entity_name)}_data: Data for {action.lower()}ing the {entity_name.lower()}.

        Returns:
            The {action.lower()}d {entity_class}.

        Raises:
            UseCaseError: If the operation fails.
            NotFoundError: If referenced entities are not found.
        """
        try:
            # Validate organization access (implement based on requirements)
            await self._validate_organization_access(organization_id)

            # Create entity instance
            {self._to_snake_case(entity_name)} = {entity_class}(
                organization_id=organization_id,
                **{self._to_snake_case(entity_name)}_data
            )

            # Persist entity
            result = await self._{self._to_snake_case(entity_name)}_repository.create({self._to_snake_case(entity_name)})

            return result

        except Exception as e:
            raise UseCaseError(f"Failed to {action.lower()} {entity_name.lower()}: {{str(e)}}") from e

    async def _validate_organization_access(self, organization_id: UUID):
        """
        Validate that the organization exists and is accessible.

        Args:
            organization_id: The organization ID to validate.

        Raises:
            NotFoundError: If organization not found or not accessible.
        """
        # Implement organization validation logic
        pass
'''

        use_case_file = self.src_root / "use_cases" / "commands" / f"{file_name}.py"
        use_case_file.parent.mkdir(parents=True, exist_ok=True)
        use_case_file.write_text(use_case_code.strip())

        return use_case_file

    def generate_react_component(self, name: str, component_type: str = "component") -> Path:
        """Generate React TypeScript component"""

        component_name = self._to_pascal_case(name)
        file_name = self._to_pascal_case(name)

        if component_type == "page":
            template = self._generate_page_component(component_name)
            output_dir = self.frontend_root / "pages"
        else:
            template = self._generate_basic_component(component_name)
            output_dir = self.frontend_root / "components"

        component_file = output_dir / f"{file_name}.tsx"
        component_file.parent.mkdir(parents=True, exist_ok=True)
        component_file.write_text(template.strip())

        return component_file

    def _generate_basic_component(self, name: str) -> str:
        return f'''import React from 'react';
import {{ Box, Typography }} from '@mui/material';

interface {name}Props {{
  // Define component props here
}}

const {name}: React.FC<{name}Props> = (props) => {{
  return (
    <Box>
      <Typography variant="h6">
        {name} Component
      </Typography>
      {{/* Component content goes here */}}
    </Box>
  );
}};

export default {name};
'''

    def _generate_page_component(self, name: str) -> str:
        return f'''import React from 'react';
import {{ Container, Typography, Box }} from '@mui/material';
import {{ useQuery }} from '@tanstack/react-query';

const {name}Page: React.FC = () => {{
  // Page state and queries

  return (
    <Container maxWidth="lg">
      <Box py={{4}}>
        <Typography variant="h4" component="h1" gutterBottom>
          {name}
        </Typography>

        {{/* Page content goes here */}}
      </Box>
    </Container>
  );
}};

export default {name}Page;
'''

    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase"""
        return re.sub(r'[^a-zA-Z0-9]', ' ', text).title().replace(' ', '')

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

@app.command()
def entity(
    name: str = typer.Argument(..., help="Entity name"),
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory")
):
    """Generate domain entity"""

    generator = ComponentGenerator(project_root)
    entity_file = generator.generate_domain_entity(name)

    print(f"✅ Generated domain entity: {entity_file}")

@app.command()
def repository(
    name: str = typer.Argument(..., help="Entity name for repository"),
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory")
):
    """Generate repository port"""

    generator = ComponentGenerator(project_root)
    port_file = generator.generate_repository_port(name)

    print(f"✅ Generated repository port: {port_file}")

@app.command()
def use_case(
    entity: str = typer.Argument(..., help="Entity name"),
    action: str = typer.Argument(..., help="Use case action (e.g., create, update)"),
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory")
):
    """Generate use case"""

    generator = ComponentGenerator(project_root)
    use_case_file = generator.generate_use_case(entity, action)

    print(f"✅ Generated use case: {use_case_file}")

@app.command()
def react_component(
    name: str = typer.Argument(..., help="Component name"),
    component_type: str = typer.Option("component", help="Component type: component or page"),
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory")
):
    """Generate React component"""

    generator = ComponentGenerator(project_root)
    component_file = generator.generate_react_component(name, component_type)

    print(f"✅ Generated React component: {component_file}")

if __name__ == "__main__":
    app()
```

### Performance Monitoring Tools
```python
# scripts/performance-monitor.py - Performance monitoring utilities
import asyncio
import time
import psutil
import docker
from typing import Dict, Any, List
import json
from pathlib import Path

class PerformanceMonitor:
    """Monitor system and application performance"""

    def __init__(self):
        self.docker_client = docker.from_env()
        self.monitoring_active = False
        self.metrics_history = []

    async def start_monitoring(self, duration: int = 300, interval: int = 10):
        """Start performance monitoring for specified duration"""

        print(f"🔍 Starting performance monitoring for {duration}s (interval: {interval}s)")

        self.monitoring_active = True
        start_time = time.time()

        try:
            while self.monitoring_active and (time.time() - start_time) < duration:
                metrics = await self.collect_metrics()
                self.metrics_history.append({
                    'timestamp': time.time(),
                    **metrics
                })

                self.print_current_metrics(metrics)
                await asyncio.sleep(interval)

        finally:
            self.monitoring_active = False
            print("📊 Monitoring completed")

    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive performance metrics"""

        # System metrics
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        }

        # Docker container metrics
        container_metrics = await self.collect_container_metrics()

        # Database metrics
        db_metrics = await self.collect_database_metrics()

        return {
            'system': system_metrics,
            'containers': container_metrics,
            'database': db_metrics
        }

    async def collect_container_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Collect Docker container performance metrics"""

        container_metrics = {}

        try:
            containers = self.docker_client.containers.list(
                filters={'label': 'com.docker.compose.project=molecular_analysis_dashboard'}
            )

            for container in containers:
                stats = container.stats(stream=False)

                # Calculate CPU percentage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']

                cpu_percent = 0.0
                if system_delta > 0 and cpu_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * \
                                 len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100

                # Memory usage
                memory_usage = stats['memory_stats'].get('usage', 0)
                memory_limit = stats['memory_stats'].get('limit', 0)
                memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0

                container_metrics[container.name] = {
                    'cpu_percent': round(cpu_percent, 2),
                    'memory_usage_mb': round(memory_usage / 1024 / 1024, 2),
                    'memory_percent': round(memory_percent, 2),
                    'status': container.status
                }

        except Exception as e:
            print(f"⚠️  Error collecting container metrics: {e}")

        return container_metrics

    async def collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database performance metrics"""

        try:
            # This would connect to your database and collect metrics
            # Placeholder for actual database monitoring
            return {
                'active_connections': 0,
                'queries_per_second': 0,
                'cache_hit_ratio': 0,
                'lock_waits': 0
            }
        except Exception as e:
            print(f"⚠️  Error collecting database metrics: {e}")
            return {}

    def print_current_metrics(self, metrics: Dict[str, Any]):
        """Print current performance metrics"""

        print(f"\n⏱️  {time.strftime('%H:%M:%S')}")
        print("=" * 60)

        # System metrics
        system = metrics['system']
        print(f"💻 System: CPU {system['cpu_percent']:.1f}% | "
              f"Memory {system['memory_percent']:.1f}% | "
              f"Disk {system['disk_usage']:.1f}%")

        # Container metrics
        containers = metrics['containers']
        for name, stats in containers.items():
            print(f"🐳 {name}: CPU {stats['cpu_percent']:.1f}% | "
                  f"Memory {stats['memory_usage_mb']:.1f}MB ({stats['memory_percent']:.1f}%)")

    def save_report(self, output_file: Path):
        """Save performance report to file"""

        if not self.metrics_history:
            print("⚠️  No metrics to save")
            return

        report = {
            'monitoring_start': self.metrics_history[0]['timestamp'],
            'monitoring_end': self.metrics_history[-1]['timestamp'],
            'total_samples': len(self.metrics_history),
            'metrics': self.metrics_history,
            'summary': self._calculate_summary()
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📊 Performance report saved to {output_file}")

    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate performance summary statistics"""

        if not self.metrics_history:
            return {}

        cpu_values = [m['system']['cpu_percent'] for m in self.metrics_history]
        memory_values = [m['system']['memory_percent'] for m in self.metrics_history]

        return {
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            }
        }

# CLI for performance monitoring
if __name__ == "__main__":
    import typer

    app = typer.Typer()

    @app.command()
    def monitor(
        duration: int = typer.Option(300, help="Monitoring duration in seconds"),
        interval: int = typer.Option(10, help="Monitoring interval in seconds"),
        output: Optional[Path] = typer.Option(None, help="Output file for report")
    ):
        """Start performance monitoring"""

        monitor = PerformanceMonitor()

        async def run():
            await monitor.start_monitoring(duration, interval)

            if output:
                monitor.save_report(output)

        asyncio.run(run())

    app()
```

## Tool Integration

### IDE Configuration
```json
# .vscode/settings.json - VS Code configuration
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/node_modules": true,
    "**/dist": true,
    "**/build": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "eslint.workingDirectories": ["frontend"],
  "docker.defaultRegistryPath": "localhost:5000"
}
```

### Automation Workflows
```makefile
# Makefile - Development task automation
.PHONY: help dev test clean lint format build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start development environment
	@echo "🚀 Starting development environment..."
	@./scripts/dev-setup.sh
	@docker compose up -d api worker
	@echo "✅ Development environment ready!"

test: ## Run all tests
	@echo "🧪 Running tests..."
	@python scripts/run-tests.py

lint: ## Run linting
	@echo "🔍 Running linters..."
	@pre-commit run --all-files

format: ## Format code
	@echo "✨ Formatting code..."
	@black src/ tests/
	@isort src/ tests/
	@cd frontend && npm run format

build: ## Build production images
	@echo "🏗️ Building production images..."
	@docker compose -f docker-compose.prod.yml build

clean: ## Clean up development environment
	@echo "🧹 Cleaning up..."
	@docker compose down -v
	@docker system prune -f

reset-db: ## Reset database
	@echo "🗄️ Resetting database..."
	@python scripts/db-manager.py reset --yes

monitor: ## Start performance monitoring
	@echo "📊 Starting performance monitoring..."
	@python scripts/performance-monitor.py monitor --duration 600

generate-entity: ## Generate domain entity
	@read -p "Entity name: " name; \
	python scripts/generate-component.py entity $$name

generate-component: ## Generate React component
	@read -p "Component name: " name; \
	python scripts/generate-component.py react-component $$name
```

## Best Practices

### Tool Configuration
- **Consistency**: Use consistent tool configurations across team
- **Automation**: Automate repetitive development tasks
- **Integration**: Integrate tools with IDE and CI/CD pipeline
- **Documentation**: Document tool usage and configuration
- **Versioning**: Version control tool configurations

### Development Workflow
- **Environment Isolation**: Use containerized development environment
- **Quick Feedback**: Implement fast feedback loops for development
- **Quality Gates**: Enforce quality checks before code integration
- **Monitoring**: Monitor development environment performance
- **Backup**: Regular backup of development data and configurations

### Performance Monitoring
- **Continuous Monitoring**: Monitor performance throughout development
- **Baseline Establishment**: Establish performance baselines
- **Alert Thresholds**: Set up alerts for performance degradation
- **Historical Analysis**: Maintain historical performance data
- **Optimization Tracking**: Track performance improvements over time

## Related Documentation

- **[Development Guides](../guides/README.md)** - Development workflows and practices
- **[Architecture Patterns](../../architecture/README.md)** - Clean Architecture implementation
- **[Database Management](../../database/management/README.md)** - Database administration
- **[Deployment Tools](../../deployment/README.md)** - Production deployment utilities
- **[API Documentation](../../api/README.md)** - API development and testing tools
