-- GNINA Task Framework Integration Seed
-- Seeds the database with GNINA task definition for task framework integration

-- Insert demo organization if not exists (for testing)
INSERT INTO organizations (org_id, name, description, is_active, created_at)
VALUES (
    '12345678-1234-1234-1234-123456789012'::uuid,
    'Demo Organization', 
    'Demo organization for task framework testing',
    true,
    NOW()
) ON CONFLICT (org_id) DO NOTHING;

-- Insert GNINA molecular docking task definition
INSERT INTO task_definitions (
    task_definition_id,
    task_id, 
    org_id, 
    version, 
    task_metadata, 
    interface_spec, 
    service_config, 
    is_active, 
    is_system,
    created_at
) VALUES (
    gen_random_uuid(),
    'gnina-molecular-docking',
    '12345678-1234-1234-1234-123456789012'::uuid,
    '1.0.0',
    '{
        "name": "GNINA Molecular Docking",
        "description": "Neural network-guided molecular docking using GNINA via NeuroSnap API. GNINA combines traditional physics-based scoring with deep learning to provide accurate protein-ligand binding predictions.",
        "category": "molecular_docking",
        "subcategory": "protein_ligand",
        "engine": "gnina",
        "tags": ["docking", "neural-network", "protein-ligand", "gnina", "neurosnap", "ai-powered"],
        "execution_time_estimate": 1200,
        "resource_requirements": {
            "cpu_cores": 2,
            "memory_gb": 4,
            "disk_gb": 2
        },
        "provider": "neurosnap",
        "output_types": ["docked_poses", "binding_scores", "interaction_analysis"],
        "supported_formats": {
            "receptor": ["pdb"],
            "ligand": ["sdf"]
        },
        "capabilities": [
            "Multi-pose generation",
            "Neural network scoring",
            "Interaction analysis",
            "Binding affinity prediction"
        ]
    }'::jsonb,
    '{
        "openapi": "3.0.0",
        "info": {
            "title": "GNINA Molecular Docking",
            "version": "1.0.0",
            "description": "Neural network-guided molecular docking via NeuroSnap"
        },
        "paths": {
            "/execute": {
                "post": {
                    "summary": "Execute GNINA molecular docking",
                    "description": "Submit a molecular docking job using GNINA engine",
                    "requestBody": {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
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
                                            "description": "Descriptive name for the docking job",
                                            "example": "EGFR_erlotinib_docking"
                                        },
                                        "note": {
                                            "type": "string",
                                            "description": "Optional notes about the docking experiment"
                                        }
                                    },
                                    "required": ["receptor_file", "ligand_file", "job_name"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Docking job submitted successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "execution_id": {"type": "string"},
                                            "job_id": {"type": "string"},
                                            "status": {"type": "string"},
                                            "task_id": {"type": "string"},
                                            "created_at": {"type": "string", "format": "date-time"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }'::jsonb,
    '{
        "engine": "gnina",
        "provider": "neurosnap", 
        "timeout": 3600,
        "retry_count": 3,
        "source": "framework",
        "api_version": "v1",
        "max_file_size": "50MB"
    }'::jsonb,
    true,
    true,
    NOW()
) ON CONFLICT (task_id, org_id) DO UPDATE SET
    task_metadata = EXCLUDED.task_metadata,
    interface_spec = EXCLUDED.interface_spec,
    service_config = EXCLUDED.service_config,
    version = EXCLUDED.version,
    updated_at = NOW();

-- Verify the insertion
SELECT 
    task_id,
    task_metadata->>'name' as name,
    task_metadata->>'description' as description,
    version,
    is_active
FROM task_definitions 
WHERE task_id = 'gnina-molecular-docking';