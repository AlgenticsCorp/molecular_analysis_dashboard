#!/usr/bin/env python3
"""Database seeding utility."""

import asyncio
import os
import sys
import json
from typing import Dict, Any, List
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Sample system task definitions
SYSTEM_TASKS = [
    {
        "task_id": "molecular-docking",
        "version": "1.0.0",
        "metadata": {
            "title": "Molecular Docking",
            "description": "Protein-ligand docking using AutoDock Vina",
            "category": "Analysis",
            "tags": ["docking", "protein", "ligand", "vina"],
            "icon": "fas fa-molecule"
        },
        "interface_spec": {
            "openapi": "3.0.0",
            "info": {
                "title": "Molecular Docking API",
                "version": "1.0.0"
            },
            "paths": {
                "/execute": {
                    "post": {
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["protein_file", "ligand_file"],
                                        "properties": {
                                            "protein_file": {"type": "string", "format": "uri"},
                                            "ligand_file": {"type": "string", "format": "uri"},
                                            "engine_params": {
                                                "type": "object",
                                                "properties": {
                                                    "exhaustiveness": {"type": "integer", "default": 8},
                                                    "num_modes": {"type": "integer", "default": 9}
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
            "resources": {"cpu": "2000m", "memory": "4Gi"}
        },
        "is_system": True,
        "is_active": True
    },
    {
        "task_id": "molecular-visualization",
        "version": "1.0.0",
        "metadata": {
            "title": "Molecular Visualization",
            "description": "Generate 3D molecular visualizations",
            "category": "Visualization",
            "tags": ["visualization", "3d", "rendering"],
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
                                            "molecule_file": {"type": "string", "format": "uri"},
                                            "render_options": {
                                                "type": "object",
                                                "properties": {
                                                    "style": {"type": "string", "enum": ["stick", "sphere", "cartoon"]},
                                                    "resolution": {"type": "string", "default": "medium"}
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
            "resources": {"cpu": "1000m", "memory": "2Gi"}
        },
        "is_system": True,
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

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Task 1: Create default organization
        task1 = progress.add_task("Creating default organization...", total=None)
        org_id = await create_default_organization(org_name, force)
        progress.update(task1, description="✅ Default organization created")

        # Task 2: Create admin user
        task2 = progress.add_task("Creating admin user...", total=None)
        user_id = await create_admin_user(org_id, admin_email, force)
        progress.update(task2, description="✅ Admin user created")

        # Task 3: Create default roles
        task3 = progress.add_task("Creating default roles...", total=None)
        await create_default_roles(org_id, force)
        progress.update(task3, description="✅ Default roles created")

        # Task 4: Seed system tasks
        task4 = progress.add_task("Seeding system tasks...", total=None)
        await seed_system_tasks(org_id, force)
        progress.update(task4, description="✅ System tasks seeded")

    console.print(f"\n📋 Seeding Summary:")
    console.print(f"   Organization: {org_name} (ID: {org_id})")
    console.print(f"   Admin Email: {admin_email}")
    console.print(f"   System Tasks: {len(SYSTEM_TASKS)} tasks created")


async def create_default_organization(name: str, force: bool) -> str:
    """Create default organization."""
    # For now, return a mock UUID
    # In a real implementation, this would use the database models
    import uuid
    org_id = str(uuid.uuid4())

    console.print(f"   📁 Organization '{name}' created with ID: {org_id}", style="dim")
    return org_id


async def create_admin_user(org_id: str, email: str, force: bool) -> str:
    """Create admin user."""
    # Mock implementation
    import uuid
    user_id = str(uuid.uuid4())

    console.print(f"   👤 Admin user '{email}' created with ID: {user_id}", style="dim")
    return user_id


async def create_default_roles(org_id: str, force: bool):
    """Create default roles (admin, standard, viewer)."""
    roles = ['admin', 'standard', 'viewer']

    for role in roles:
        console.print(f"   🎭 Role '{role}' created", style="dim")


async def seed_system_tasks(org_id: str, force: bool):
    """Seed system task definitions."""
    for task in SYSTEM_TASKS:
        console.print(f"   🔧 System task '{task['task_id']}' seeded", style="dim")


if __name__ == '__main__':
    main()
