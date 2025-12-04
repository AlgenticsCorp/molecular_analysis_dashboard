# 🧬 GNINA Task Definition for Task Registry

## Task Registration Data

```python
# database/scripts/gnina_task_definition.py
GNINA_TASK_DEFINITION = {
    "task_id": "gnina-molecular-docking",
    "version": "1.0.0",
    "task_metadata": {
        "title": "GNINA Molecular Docking",
        "description": "Neural network-guided molecular docking using GNINA engine via NeuroSnap Cloud",
        "category": "molecular_docking",
        "provider": "neurosnap",
        "engine": "gnina",
        "computational_requirements": {
            "cpu": "medium",
            "memory": "low",
            "estimated_runtime": "10-30 minutes",
            "cost_estimate": "0.00025 credits"
        },
        "tags": ["docking", "gnina", "neurosnap", "cloud", "neural-network"]
    },
    "interface_spec": {
        "openapi": "3.0.0",
        "info": {
            "title": "GNINA Molecular Docking Task",
            "version": "1.0.0"
        },
        "paths": {
            "/execute": {
                "post": {
                    "summary": "Execute GNINA molecular docking",
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
                                            "description": "Protein receptor structure in PDB format"
                                        },
                                        "ligand_file": {
                                            "type": "string", 
                                            "format": "binary",
                                            "description": "Ligand molecule structure in SDF format"
                                        },
                                        "job_name": {
                                            "type": "string",
                                            "default": "GNINA Docking",
                                            "description": "Human-readable name for the docking job"
                                        },
                                        "note": {
                                            "type": "string",
                                            "default": "Docking analysis",
                                            "description": "Additional notes for the job"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Task execution started successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "execution_id": {"type": "string"},
                                            "job_id": {"type": "string"},
                                            "status": {"type": "string"},
                                            "task_id": {"type": "string"}
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
        "provider": "neurosnap",
        "service_type": "cloud_api", 
        "endpoint": "/api/v1/providers/neurosnap/docking/submit",
        "adapter_class": "NeuroSnapDockingAdapter",
        "timeout": 30,
        "retry_policy": {
            "max_retries": 3,
            "backoff_factor": 2
        }
    },
    "is_system": True,
    "is_active": True
}
```

## Database Seeding Script

```python
# database/scripts/seed_gnina_task.py
async def seed_gnina_task(db_manager, org_id: str):
    """Seed GNINA task definition into task registry."""
    
    async for session in db_manager.get_metadata_session():
        try:
            # Check if task already exists
            stmt = select(TaskDefinition).where(
                TaskDefinition.task_id == GNINA_TASK_DEFINITION["task_id"],
                TaskDefinition.org_id == UUID(org_id)
            )
            result = await session.execute(stmt)
            existing_task = result.scalar_one_or_none()

            if existing_task:
                console.print("✅ GNINA task already registered", style="green")
                return

            # Create new task definition
            task = TaskDefinition(
                org_id=UUID(org_id),
                **GNINA_TASK_DEFINITION
            )

            session.add(task)
            await session.commit()
            
            console.print("🚀 GNINA task registered successfully", style="green")
            
        except Exception as e:
            console.print(f"❌ Failed to seed GNINA task: {e}", style="red")
            await session.rollback()
            raise
```