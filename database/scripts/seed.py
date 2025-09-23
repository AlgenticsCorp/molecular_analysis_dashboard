#!/usr/bin/env python3
"""Database seeding utility."""

import asyncio
import os
import sys
import json
from typing import Dict, Any, List
from uuid import uuid4, UUID
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add database models to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from models.base import DatabaseManager
    from models.metadata import Organization, User, Role, TaskDefinition
    from sqlalchemy.exc import IntegrityError
except ImportError as e:
    console = Console()
    console.print(f"❌ Failed to import database models: {e}", style="red")
    console.print("Make sure you're running this from the database directory", style="yellow")
    sys.exit(1)

console = Console()

# Demo task definitions that match frontend TaskTemplate structure
DEMO_TASKS = [
    {
        "task_id": "autodock_vina_basic",
        "version": "1.2.0",
        "task_metadata": {
            "name": "AutoDock Vina",
            "description": "Fast molecular docking using AutoDock Vina algorithm for protein-ligand binding prediction",
            "category": "autodock_vina",
            "complexity": "beginner",
            "estimatedRuntime": "1-10 minutes",
            "cpuRequirement": "high",
            "memoryRequirement": "medium",
            "requiredFiles": ["receptor.pdbqt", "ligand.pdbqt"],
            "compatibility": ["linux", "macos", "windows"],
            "tags": ["docking", "vina", "basic", "tutorial"],
            "documentation": "Standard AutoDock Vina workflow for molecular docking",
            "isBuiltIn": True
        },
        "interface_spec": {
            "openapi": "3.0.0",
            "info": {
                "title": "AutoDock Vina API",
                "version": "1.2.0",
                "description": "Fast molecular docking using AutoDock Vina algorithm"
            },
            "paths": {
                "/execute": {
                    "post": {
                        "summary": "Execute AutoDock Vina docking",
                        "description": "Submit a molecular docking job using AutoDock Vina",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["receptor_file", "ligand_file"],
                                        "properties": {
                                            "receptor_file": {
                                                "type": "string",
                                                "format": "binary",
                                                "description": "Receptor protein file (.pdbqt)"
                                            },
                                            "ligand_file": {
                                                "type": "string",
                                                "format": "binary",
                                                "description": "Ligand molecule file (.pdbqt)"
                                            },
                                            "center_x": {"type": "number", "default": 0, "description": "X coordinate of search space center"},
                                            "center_y": {"type": "number", "default": 0, "description": "Y coordinate of search space center"},
                                            "center_z": {"type": "number", "default": 0, "description": "Z coordinate of search space center"},
                                            "size_x": {"type": "number", "default": 20, "description": "Search space size in X dimension"},
                                            "size_y": {"type": "number", "default": 20, "description": "Search space size in Y dimension"},
                                            "size_z": {"type": "number", "default": 20, "description": "Search space size in Z dimension"},
                                            "exhaustiveness": {"type": "number", "default": 8, "description": "Exhaustiveness of search"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "202": {
                                "description": "Job submitted successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "job_id": {"type": "string", "format": "uuid"},
                                                "status": {"type": "string", "enum": ["PENDING", "RUNNING", "COMPLETED", "FAILED"]},
                                                "estimated_duration": {"type": "string"},
                                                "created_at": {"type": "string", "format": "date-time"}
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
                        "summary": "Get job status",
                        "parameters": [
                            {
                                "name": "job_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string", "format": "uuid"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Job status information",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "job_id": {"type": "string"},
                                                "status": {"type": "string"},
                                                "progress": {"type": "number", "minimum": 0, "maximum": 100},
                                                "started_at": {"type": "string", "format": "date-time"},
                                                "completed_at": {"type": "string", "format": "date-time"},
                                                "error_message": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/results/{job_id}": {
                    "get": {
                        "summary": "Get job results",
                        "parameters": [
                            {
                                "name": "job_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string", "format": "uuid"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Docking results",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "job_id": {"type": "string"},
                                                "status": {"type": "string"},
                                                "results": {
                                                    "type": "object",
                                                    "properties": {
                                                        "best_score": {"type": "number"},
                                                        "poses": {
                                                            "type": "array",
                                                            "items": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "score": {"type": "number"},
                                                                    "rmsd": {"type": "number"},
                                                                    "pose_file": {"type": "string", "format": "uri"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                },
                                                "output_files": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "filename": {"type": "string"},
                                                            "url": {"type": "string", "format": "uri"},
                                                            "size": {"type": "integer"},
                                                            "type": {"type": "string"}
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
            "components": {
                "schemas": {
                    "JobStatus": {
                        "type": "string",
                        "enum": ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
                    },
                    "ErrorResponse": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "message": {"type": "string"},
                            "code": {"type": "integer"}
                        }
                    }
                }
            },
            "parameters": [
                {
                    "name": "center_x",
                    "type": "number",
                    "required": True,
                    "default": 0,
                    "description": "X coordinate of search space center"
                },
                {
                    "name": "center_y",
                    "type": "number",
                    "required": True,
                    "default": 0,
                    "description": "Y coordinate of search space center"
                },
                {
                    "name": "center_z",
                    "type": "number",
                    "required": True,
                    "default": 0,
                    "description": "Z coordinate of search space center"
                },
                {
                    "name": "size_x",
                    "type": "number",
                    "required": True,
                    "default": 20,
                    "description": "Search space size in X dimension"
                },
                {
                    "name": "size_y",
                    "type": "number",
                    "required": True,
                    "default": 20,
                    "description": "Search space size in Y dimension"
                },
                {
                    "name": "size_z",
                    "type": "number",
                    "required": True,
                    "default": 20,
                    "description": "Search space size in Z dimension"
                },
                {
                    "name": "exhaustiveness",
                    "type": "number",
                    "required": False,
                    "default": 8,
                    "description": "Exhaustiveness of search"
                }
            ]
        },
        "service_config": {
            "docker_image": "algentics/autodock-vina:1.2.0",
            "resources": {"cpu": "2000m", "memory": "4Gi"}
        },
        "is_system": False,
        "is_active": True
    },
    {
        "task_id": "autodock_vina_advanced",
        "version": "1.2.0",
        "task_metadata": {
            "name": "AutoDock Vina - Advanced",
            "description": "Advanced AutoDock Vina docking with custom parameters and multiple conformations",
            "category": "autodock_vina",
            "complexity": "advanced",
            "estimatedRuntime": "1-4 hours",
            "cpuRequirement": "high",
            "memoryRequirement": "high",
            "requiredFiles": ["receptor.pdbqt", "ligand.pdbqt", "config.txt"],
            "compatibility": ["linux", "macos"],
            "tags": ["docking", "vina", "advanced", "multi-conformation"],
            "documentation": "Advanced AutoDock Vina with detailed parameter control",
            "isBuiltIn": True
        },
        "interface_spec": {
            "openapi": "3.0.0",
            "info": {
                "title": "AutoDock Vina Advanced API",
                "version": "1.2.0",
                "description": "Advanced AutoDock Vina docking with custom parameters"
            },
            "parameters": [
                {
                    "name": "num_modes",
                    "type": "number",
                    "required": False,
                    "default": 9,
                    "description": "Number of binding modes to generate"
                },
                {
                    "name": "energy_range",
                    "type": "number",
                    "required": False,
                    "default": 3,
                    "description": "Maximum energy difference between best and worst mode"
                },
                {
                    "name": "seed",
                    "type": "number",
                    "required": False,
                    "description": "Random seed for reproducible results"
                },
                {
                    "name": "cpu",
                    "type": "number",
                    "required": False,
                    "default": 1,
                    "description": "Number of CPUs to use"
                }
            ]
        },
        "service_config": {
            "docker_image": "algentics/autodock-vina:1.2.0-advanced",
            "resources": {"cpu": "4000m", "memory": "8Gi"}
        },
        "is_system": False,
        "is_active": True
    },
    {
        "task_id": "autodock4_basic",
        "version": "4.2.6",
        "task_metadata": {
            "name": "AutoDock 4",
            "description": "Classic molecular docking using AutoDock 4 algorithm for protein-ligand binding prediction",
            "category": "autodock4",
            "complexity": "intermediate",
            "estimatedRuntime": "5-30 minutes",
            "cpuRequirement": "medium",
            "memoryRequirement": "low",
            "requiredFiles": ["receptor.pdbqt", "ligand.pdbqt", "grid.gpf"],
            "compatibility": ["linux", "macos"],
            "tags": ["docking", "autodock4", "genetic-algorithm", "protein-ligand"],
            "documentation": "Traditional AutoDock 4 workflow with genetic algorithm optimization",
            "isBuiltIn": True
        },
        "interface_spec": {
            "openapi": "3.0.0",
            "info": {
                "title": "AutoDock 4 API",
                "version": "4.2.6",
                "description": "Classic molecular docking using AutoDock 4 algorithm"
            },
            "parameters": [
                {
                    "name": "ga_runs",
                    "type": "number",
                    "required": False,
                    "default": 10,
                    "description": "Number of genetic algorithm runs"
                },
                {
                    "name": "ga_pop_size",
                    "type": "number",
                    "required": False,
                    "default": 150,
                    "description": "Population size for genetic algorithm"
                },
                {
                    "name": "ga_num_evals",
                    "type": "number",
                    "required": False,
                    "default": 2500000,
                    "description": "Maximum number of energy evaluations"
                }
            ]
        },
        "service_config": {
            "docker_image": "algentics/autodock4:4.2.6",
            "resources": {"cpu": "1000m", "memory": "2Gi"}
        },
        "is_system": False,
        "is_active": True
    },
    {
        "task_id": "virtual_screening",
        "version": "2.1.0",
        "task_metadata": {
            "name": "Virtual Screening Pipeline",
            "description": "High-throughput virtual screening of compound libraries",
            "category": "custom",
            "complexity": "advanced",
            "estimatedRuntime": "12-48 hours",
            "cpuRequirement": "high",
            "memoryRequirement": "high",
            "requiredFiles": ["receptor.pdbqt", "ligand_library.sdf"],
            "compatibility": ["linux"],
            "tags": ["screening", "high-throughput", "pipeline", "drug-discovery"],
            "documentation": "Automated virtual screening of large compound libraries",
            "isBuiltIn": False
        },
        "interface_spec": {
            "openapi": "3.0.0",
            "info": {
                "title": "Virtual Screening Pipeline API",
                "version": "2.1.0",
                "description": "High-throughput virtual screening of compound libraries"
            },
            "parameters": [
                {
                    "name": "library_size",
                    "type": "number",
                    "required": True,
                    "description": "Number of compounds in library"
                },
                {
                    "name": "scoring_function",
                    "type": "select",
                    "required": True,
                    "options": ["vina", "autodock4", "glide"],
                    "description": "Scoring function to use"
                },
                {
                    "name": "filter_druglike",
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Apply drug-like filters"
                }
            ]
        },
        "service_config": {
            "docker_image": "algentics/virtual-screening:2.1.0",
            "resources": {"cpu": "8000m", "memory": "16Gi"}
        },
        "is_system": False,
        "is_active": True
    }
]


@click.command()
@click.option('--force', is_flag=True, help='Force reseed (replace existing data)')
@click.option('--org-name', default='Algentics Demo', help='Default organization name')
@click.option('--admin-email', default='admin@algentics.com', help='Admin user email')
def main(force, org_name, admin_email):
    """Database seeding utility."""

    try:
        asyncio.run(run_seeding(force, org_name, admin_email))
        console.print("✅ Database seeding completed successfully!", style="green")
    except Exception as e:
        console.print(f"❌ Seeding failed: {e}", style="red")
        sys.exit(1)


async def run_seeding(force: bool, org_name: str, admin_email: str):
    """Run the database seeding process."""
    console.print("🌱 Starting database seeding...", style="blue")

    # Initialize database manager
    db_manager = DatabaseManager()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Task 1: Create default organization
        task1 = progress.add_task("Creating default organization...", total=None)
        org_id = await create_default_organization(db_manager, org_name, force)
        progress.update(task1, description="✅ Default organization created")

        # Task 2: Create admin user
        task2 = progress.add_task("Creating admin user...", total=None)
        user_id = await create_admin_user(db_manager, org_id, admin_email, force)
        progress.update(task2, description="✅ Admin user created")

        # Task 3: Create default roles
        task3 = progress.add_task("Creating default roles...", total=None)
        await create_default_roles(db_manager, org_id, force)
        progress.update(task3, description="✅ Default roles created")

        # Task 4: Seed demo tasks
        task4 = progress.add_task("Seeding demo tasks...", total=None)
        await seed_demo_tasks(db_manager, org_id, force)
        progress.update(task4, description="✅ Demo tasks seeded")

    # Close database connections
    await db_manager.close_all()

    console.print(f"\n📋 Seeding Summary:")
    console.print(f"   Organization: {org_name} (ID: {org_id})")
    console.print(f"   Admin Email: {admin_email}")
    console.print(f"   Demo Tasks: {len(DEMO_TASKS)} tasks created")


async def create_default_organization(db_manager: DatabaseManager, name: str, force: bool) -> str:
    """Create default organization."""
    async for session in db_manager.get_metadata_session():
        try:
            # Check if organization already exists
            from sqlalchemy import select
            stmt = select(Organization).where(Organization.name == name)
            result = await session.execute(stmt)
            existing_org = result.scalar_one_or_none()

            if existing_org and not force:
                console.print(f"   📁 Organization '{name}' already exists (ID: {existing_org.org_id})", style="dim")
                return str(existing_org.org_id)
            elif existing_org and force:
                # Delete existing and recreate
                await session.delete(existing_org)
                await session.commit()

            # Create new organization
            org = Organization(
                name=name,
                status="active",
                quotas={"max_jobs": 1000, "max_storage_gb": 100},
                settings={"timezone": "UTC", "notifications_enabled": True}
            )
            session.add(org)
            await session.commit()

            console.print(f"   📁 Organization '{name}' created with ID: {org.org_id}", style="dim")
            return str(org.org_id)

        except Exception as e:
            console.print(f"   ❌ Failed to create organization: {e}", style="red")
            await session.rollback()
            raise


async def create_admin_user(db_manager: DatabaseManager, org_id: str, email: str, force: bool) -> str:
    """Create admin user."""
    async for session in db_manager.get_metadata_session():
        try:
            from sqlalchemy import select

            # Check if user already exists
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user and not force:
                console.print(f"   👤 Admin user '{email}' already exists (ID: {existing_user.user_id})", style="dim")
                return str(existing_user.user_id)
            elif existing_user and force:
                await session.delete(existing_user)
                await session.commit()

            # Create new user
            user = User(
                email=email,
                enabled=True,
                profile={
                    "username": "admin",
                    "display_name": "System Administrator",
                    "auth_data": {"auth_type": "local", "password_hash": "demo_hash"},
                    "settings": {"language": "en", "theme": "light"}
                }
            )
            session.add(user)
            await session.commit()

            console.print(f"   👤 Admin user '{email}' created with ID: {user.user_id}", style="dim")
            return str(user.user_id)

        except Exception as e:
            console.print(f"   ❌ Failed to create admin user: {e}", style="red")
            await session.rollback()
            raise


async def create_default_roles(db_manager: DatabaseManager, org_id: str, force: bool):
    """Create default roles (admin, standard, viewer)."""
    roles_data = [
        {
            "name": "admin",
            "permissions": ["read", "write", "delete", "admin"],
            "description": "Full system administration access"
        },
        {
            "name": "standard",
            "permissions": ["read", "write"],
            "description": "Standard user with read/write access"
        },
        {
            "name": "viewer",
            "permissions": ["read"],
            "description": "Read-only access"
        }
    ]

    async for session in db_manager.get_metadata_session():
        try:
            from sqlalchemy import select

            for role_data in roles_data:
                # Check if role already exists
                stmt = select(Role).where(
                    Role.name == role_data["name"],
                    Role.org_id == UUID(org_id)
                )
                result = await session.execute(stmt)
                existing_role = result.scalar_one_or_none()

                if existing_role and not force:
                    console.print(f"   🎭 Role '{role_data['name']}' already exists", style="dim")
                    continue
                elif existing_role and force:
                    await session.delete(existing_role)

                # Create new role
                role = Role(
                    org_id=UUID(org_id),
                    name=role_data["name"],
                    description=role_data["description"]
                )
                session.add(role)
                console.print(f"   🎭 Role '{role_data['name']}' created", style="dim")

            await session.commit()

        except Exception as e:
            console.print(f"   ❌ Failed to create roles: {e}", style="red")
            await session.rollback()
            raise


async def seed_demo_tasks(db_manager: DatabaseManager, org_id: str, force: bool):
    """Seed demo task definitions that match frontend TaskTemplate structure."""
    async for session in db_manager.get_metadata_session():
        try:
            from sqlalchemy import select

            for task_data in DEMO_TASKS:
                # Check if task already exists
                stmt = select(TaskDefinition).where(
                    TaskDefinition.task_id == task_data["task_id"],
                    TaskDefinition.org_id == UUID(org_id)
                )
                result = await session.execute(stmt)
                existing_task = result.scalar_one_or_none()

                if existing_task and not force:
                    console.print(f"   🔧 Demo task '{task_data['task_id']}' already exists", style="dim")
                    continue
                elif existing_task and force:
                    await session.delete(existing_task)

                # Create new task definition
                task = TaskDefinition(
                    org_id=UUID(org_id),
                    task_id=task_data["task_id"],
                    version=task_data["version"],
                    task_metadata=task_data["task_metadata"],
                    interface_spec=task_data["interface_spec"],
                    service_config=task_data["service_config"],
                    is_system=task_data["is_system"],
                    is_active=task_data["is_active"]
                )
                session.add(task)
                console.print(f"   🔧 Demo task '{task_data['task_id']}' seeded", style="dim")

            await session.commit()

        except Exception as e:
            console.print(f"   ❌ Failed to seed demo tasks: {e}", style="red")
            await session.rollback()
            raise


if __name__ == '__main__':
    main()
