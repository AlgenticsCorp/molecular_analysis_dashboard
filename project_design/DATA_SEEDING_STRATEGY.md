# Data Seeding Strategy

## Overview

This document outlines the data seeding strategy for the Molecular Analysis Dashboard, focusing on **system task definitions**, initial organization setup, and reference data that enables the dynamic task system to function properly.

## Seeding Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Seeding Strategy                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │ System Tasks    │    │      Reference Data                 │  │
│  │                 │    │                                     │  │
│  │ • Molecular     │    │ • Default Organizations            │  │
│  │   Docking       │    │ • Admin Users                      │  │
│  │ • Visualization │    │ • Standard Roles                   │  │
│  │ • Analysis      │    │ • Pipeline Templates               │  │
│  │ • File Process  │    │ • Default Settings                 │  │
│  └─────────────────┘    └─────────────────────────────────────┘  │
│           │                            │                        │
│           ▼                            ▼                        │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │ Task Registry   │    │     Metadata DB                    │  │
│  │  (Database)     │    │    (Shared)                        │  │
│  └─────────────────┘    └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Seeding Categories

### 1. System Task Definitions

**Core Molecular Analysis Tasks** - These are essential tasks that every organization should have access to:

#### 1.1 Molecular Docking Task
```python
MOLECULAR_DOCKING_TASK = {
    "task_id": "molecular-docking",
    "version": "1.0.0",
    "metadata": {
        "title": "Molecular Docking",
        "description": "Protein-ligand docking using AutoDock Vina engine",
        "category": "Analysis",
        "tags": ["docking", "protein", "ligand", "vina"],
        "icon": "fas fa-molecule",
        "documentation_url": "https://docs.algentics.com/tasks/molecular-docking"
    },
    "interface_spec": {
        "openapi": "3.0.0",
        "info": {
            "title": "Molecular Docking API",
            "version": "1.0.0",
            "description": "Perform protein-ligand docking analysis"
        },
        "paths": {
            "/execute": {
                "post": {
                    "summary": "Execute molecular docking",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["protein_file", "ligand_file"],
                                    "properties": {
                                        "protein_file": {
                                            "type": "string",
                                            "format": "uri",
                                            "description": "URL to protein PDB file"
                                        },
                                        "ligand_file": {
                                            "type": "string",
                                            "format": "uri",
                                            "description": "URL to ligand SDF file"
                                        },
                                        "engine_params": {
                                            "type": "object",
                                            "properties": {
                                                "exhaustiveness": {
                                                    "type": "integer",
                                                    "minimum": 1,
                                                    "maximum": 32,
                                                    "default": 8,
                                                    "description": "Thoroughness of search"
                                                },
                                                "num_modes": {
                                                    "type": "integer",
                                                    "minimum": 1,
                                                    "maximum": 20,
                                                    "default": 9,
                                                    "description": "Number of binding modes"
                                                },
                                                "center": {
                                                    "type": "object",
                                                    "properties": {
                                                        "x": {"type": "number"},
                                                        "y": {"type": "number"},
                                                        "z": {"type": "number"}
                                                    },
                                                    "required": ["x", "y", "z"],
                                                    "description": "Center of search space"
                                                },
                                                "size": {
                                                    "type": "object",
                                                    "properties": {
                                                        "x": {"type": "number", "minimum": 1},
                                                        "y": {"type": "number", "minimum": 1},
                                                        "z": {"type": "number", "minimum": 1}
                                                    },
                                                    "required": ["x", "y", "z"],
                                                    "description": "Size of search space"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Docking task submitted successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "job_id": {"type": "string"},
                                            "status": {"type": "string"},
                                            "estimated_duration": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/status/{job_id}": {
                "get": {
                    "summary": "Get docking job status",
                    "parameters": [
                        {
                            "name": "job_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Job status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "progress": {"type": "number"},
                                            "results": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "pose": {"type": "integer"},
                                                        "affinity": {"type": "number"},
                                                        "rmsd_lb": {"type": "number"},
                                                        "rmsd_ub": {"type": "number"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "service_config": {
        "docker_image": "algentics/molecular-docking:v1.0.0",
        "resources": {
            "cpu": "2000m",
            "memory": "4Gi",
            "ephemeral_storage": "10Gi"
        },
        "environment": {
            "VINA_BINARY": "/usr/local/bin/vina",
            "PYTHONPATH": "/app"
        },
        "health_check": {
            "path": "/health",
            "interval": "30s",
            "timeout": "10s",
            "retries": 3
        },
        "ports": {
            "http": 8080
        }
    },
    "is_system": True,
    "is_active": True
}
```

#### 1.2 Molecular Visualization Task
```python
MOLECULAR_VISUALIZATION_TASK = {
    "task_id": "molecular-visualization",
    "version": "1.0.0",
    "metadata": {
        "title": "Molecular Visualization",
        "description": "Generate 3D molecular visualizations and images",
        "category": "Visualization",
        "tags": ["visualization", "3d", "rendering", "images"],
        "icon": "fas fa-eye"
    },
    "interface_spec": {
        "openapi": "3.0.0",
        "info": {
            "title": "Molecular Visualization API",
            "version": "1.0.0"
        },
        "paths": {
            "/execute": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["molecule_file"],
                                    "properties": {
                                        "molecule_file": {
                                            "type": "string",
                                            "format": "uri",
                                            "description": "URL to molecule file (PDB, SDF, MOL2)"
                                        },
                                        "render_options": {
                                            "type": "object",
                                            "properties": {
                                                "style": {
                                                    "type": "string",
                                                    "enum": ["stick", "sphere", "cartoon", "surface"],
                                                    "default": "stick"
                                                },
                                                "resolution": {
                                                    "type": "string",
                                                    "enum": ["low", "medium", "high", "ultra"],
                                                    "default": "medium"
                                                },
                                                "background_color": {
                                                    "type": "string",
                                                    "pattern": "^#[0-9A-Fa-f]{6}$",
                                                    "default": "#FFFFFF"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "service_config": {
        "docker_image": "algentics/molecular-viz:v1.0.0",
        "resources": {
            "cpu": "1000m",
            "memory": "2Gi"
        }
    },
    "is_system": True,
    "is_active": True
}
```

#### 1.3 Additional System Tasks
```python
SYSTEM_TASKS = [
    MOLECULAR_DOCKING_TASK,
    MOLECULAR_VISUALIZATION_TASK,
    {
        "task_id": "file-converter",
        "metadata": {
            "title": "File Format Converter",
            "description": "Convert between molecular file formats (PDB, SDF, MOL2, etc.)",
            "category": "Processing"
        },
        # ... OpenAPI specification
    },
    {
        "task_id": "property-calculator",
        "metadata": {
            "title": "Molecular Property Calculator",
            "description": "Calculate molecular descriptors and properties",
            "category": "Analysis"
        },
        # ... OpenAPI specification
    }
]
```

### 2. Reference Data Seeding

#### 2.1 Default Organizations
```python
DEFAULT_ORGANIZATIONS = [
    {
        "name": "Algentics Demo",
        "status": "active",
        "quotas": {
            "max_jobs_per_month": 1000,
            "max_storage_gb": 100,
            "max_concurrent_jobs": 10
        },
        "settings": {
            "storage_bucket": "algentics-demo-data",
            "default_timeout": 3600,
            "enable_caching": True
        }
    }
]
```

#### 2.2 Default Roles and Permissions
```python
DEFAULT_ROLES = [
    {
        "name": "admin",
        "permissions": [
            "task.create", "task.read", "task.update", "task.delete",
            "pipeline.create", "pipeline.read", "pipeline.update", "pipeline.delete",
            "job.create", "job.read", "job.cancel",
            "user.invite", "user.manage",
            "org.settings"
        ]
    },
    {
        "name": "standard",
        "permissions": [
            "task.read", "task.execute",
            "pipeline.read", "pipeline.execute",
            "job.create", "job.read", "job.cancel_own",
            "molecule.upload", "molecule.read_own"
        ]
    },
    {
        "name": "viewer",
        "permissions": [
            "task.read",
            "pipeline.read",
            "job.read_own",
            "molecule.read_own"
        ]
    }
]
```

## Seeding Implementation

### 1. Seeding Scripts Location
```
scripts/
├── seed_data.py                 # Main seeding orchestrator
├── seeders/
│   ├── __init__.py
│   ├── system_tasks.py         # System task definitions
│   ├── organizations.py        # Default organizations
│   ├── roles_permissions.py    # RBAC setup
│   └── pipeline_templates.py   # Default pipeline templates
└── data/
    ├── system_tasks.json       # Task definitions in JSON
    └── pipeline_templates.json # Pipeline templates
```

### 2. Seeding Orchestrator
```python
# scripts/seed_data.py
import asyncio
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.molecular_analysis_dashboard.infrastructure.database import get_database_url
from src.molecular_analysis_dashboard.adapters.database.task_registry import TaskRegistryAdapter
from seeders.system_tasks import SystemTaskSeeder
from seeders.organizations import OrganizationSeeder
from seeders.roles_permissions import RolePermissionSeeder

logger = logging.getLogger(__name__)

class DataSeeder:
    """Orchestrates all data seeding operations."""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def seed_all(self, force: bool = False) -> None:
        """Seed all reference data and system tasks."""
        async with self.session_factory() as session:
            try:
                logger.info("Starting data seeding process...")

                # 1. Seed organizations first (required for task scoping)
                org_seeder = OrganizationSeeder(session)
                demo_org_id = await org_seeder.seed_default_organization()

                # 2. Seed roles and permissions
                role_seeder = RolePermissionSeeder(session)
                await role_seeder.seed_default_roles(demo_org_id)

                # 3. Seed system tasks
                task_seeder = SystemTaskSeeder(session)
                await task_seeder.seed_system_tasks(demo_org_id, force=force)

                # 4. Commit all changes
                await session.commit()
                logger.info("Data seeding completed successfully")

            except Exception as e:
                await session.rollback()
                logger.error(f"Data seeding failed: {e}")
                raise

    async def cleanup(self):
        """Clean up database connections."""
        await self.engine.dispose()

async def main():
    """Main seeding function."""
    database_url = get_database_url("metadata")
    seeder = DataSeeder(database_url)

    try:
        await seeder.seed_all(force=False)
    finally:
        await seeder.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. System Task Seeder
```python
# scripts/seeders/system_tasks.py
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.molecular_analysis_dashboard.domain.entities.task_definition import TaskDefinition
from src.molecular_analysis_dashboard.adapters.database.task_registry import TaskRegistryAdapter

class SystemTaskSeeder:
    """Seeds system task definitions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_registry = TaskRegistryAdapter(session)

    async def seed_system_tasks(self, org_id: str, force: bool = False) -> None:
        """Seed all system task definitions."""
        for task_data in SYSTEM_TASKS:
            existing_task = await self._check_existing_task(
                org_id, task_data["task_id"], task_data["version"]
            )

            if existing_task and not force:
                logger.info(f"System task {task_data['task_id']} already exists, skipping")
                continue

            # Create task definition entity
            task_definition = TaskDefinition(
                org_id=org_id,
                task_id=task_data["task_id"],
                version=task_data["version"],
                metadata=task_data["metadata"],
                interface_spec=task_data["interface_spec"],
                service_config=task_data["service_config"],
                is_system=task_data.get("is_system", True),
                is_active=task_data.get("is_active", True)
            )

            # Save to database
            await self.task_registry.create_task_definition(task_definition)
            logger.info(f"Seeded system task: {task_data['task_id']}")

    async def _check_existing_task(self, org_id: str, task_id: str, version: str) -> bool:
        """Check if task already exists."""
        existing = await self.task_registry.get_task_definition(
            org_id, task_id, version
        )
        return existing is not None
```

## Seeding Execution Strategy

### 1. Development Environment
```bash
# Run during Stage 1 migration
docker compose up -d postgres
python scripts/seed_data.py

# Or integrate with Alembic migration
ALEMBIC_BRANCH=metadata alembic upgrade head
```

### 2. Production Environment
```bash
# Production seeding with backups
./scripts/backup_database.sh
python scripts/seed_data.py --environment=production
./scripts/validate_seeding.sh
```

### 3. Testing Environment
```bash
# Seed test data with additional test tasks
python scripts/seed_data.py --environment=test --include-test-tasks
```

## Seeding Validation

### 1. Validation Scripts
```python
# scripts/validate_seeding.py
async def validate_system_tasks():
    """Validate all system tasks are properly seeded."""
    task_registry = TaskRegistryAdapter(session)

    for expected_task in SYSTEM_TASKS:
        task = await task_registry.get_task_definition(
            org_id, expected_task["task_id"], expected_task["version"]
        )
        assert task is not None, f"System task {expected_task['task_id']} not found"
        assert task.is_system == True, f"Task {expected_task['task_id']} not marked as system"

    logger.info("✅ All system tasks validated successfully")
```

### 2. Health Checks
```python
# Add to /ready endpoint
async def check_system_tasks_seeded():
    """Health check for system task seeding."""
    required_tasks = ["molecular-docking", "molecular-visualization"]

    for task_id in required_tasks:
        exists = await task_registry.task_exists(task_id)
        if not exists:
            return False, f"Required system task {task_id} not found"

    return True, "All system tasks properly seeded"
```

## Migration Integration

### 1. Post-Migration Seeding
```python
# alembic/versions/metadata/007_seed_system_tasks.py
"""Seed system task definitions

Revision ID: 007_meta
Revises: 006_meta
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
import asyncio

def upgrade():
    """Run system task seeding after schema is ready."""
    # Import seeding function
    from scripts.seeders.system_tasks import seed_system_tasks_sync

    # Get database connection
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # Run seeding operation
        seed_system_tasks_sync(session)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def downgrade():
    """Remove system tasks (optional - usually keep for safety)."""
    # Usually we don't remove system tasks in downgrade
    pass
```

This comprehensive data seeding strategy ensures that:

1. **System tasks are available immediately** after database setup
2. **Organizations have proper default configurations**
3. **RBAC is properly initialized** with standard roles
4. **Seeding is idempotent** and can be run multiple times safely
5. **Validation ensures data integrity** across environments
6. **Integration with migrations** for automated deployment

The seeding system provides a solid foundation for the dynamic task system to function properly from day one.
