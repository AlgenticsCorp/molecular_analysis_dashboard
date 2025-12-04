# GNINA Task Integration Frontend Components

## 1. GNINA Task Wizard Component

Create a React component specifically for GNINA molecular docking execution:

```tsx
// frontend/src/components/tasks/GninaDockingWizard.tsx

import React, { useState, useCallback } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  TextField,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Divider
} from '@mui/material';
import { CloudUpload, Science, Timeline } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { TaskTemplate } from '../../types/tasks';
import { taskService } from '../../services/taskService';

interface GninaDockingWizardProps {
  task: TaskTemplate;
  onJobSubmitted?: (jobId: string) => void;
  onCancel?: () => void;
}

interface FileUpload {
  file: File;
  preview?: string;
  error?: string;
}

export const GninaDockingWizard: React.FC<GninaDockingWizardProps> = ({
  task,
  onJobSubmitted,
  onCancel
}) => {
  const [receptorFile, setReceptorFile] = useState<FileUpload | null>(null);
  const [ligandFile, setLigandFile] = useState<FileUpload | null>(null);
  const [jobName, setJobName] = useState('');
  const [note, setNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Dropzone for receptor file
  const onDropReceptor = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdb')) {
        setError('Receptor file must be in PDB format (.pdb)');
        return;
      }
      setReceptorFile({ file });
      setError(null);
    }
  }, []);

  // Dropzone for ligand file  
  const onDropLigand = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.sdf')) {
        setError('Ligand file must be in SDF format (.sdf)');
        return;
      }
      setLigandFile({ file });
      setError(null);
    }
  }, []);

  const receptorDropzone = useDropzone({
    onDrop: onDropReceptor,
    accept: {
      'chemical/x-pdb': ['.pdb']
    },
    maxFiles: 1
  });

  const ligandDropzone = useDropzone({
    onDrop: onDropLigand,
    accept: {
      'chemical/x-mdl-sdfile': ['.sdf']
    },
    maxFiles: 1
  });

  const handleSubmit = async () => {
    if (!receptorFile || !ligandFile || !jobName.trim()) {
      setError('Please provide receptor file, ligand file, and job name');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('receptor_file', receptorFile.file);
      formData.append('ligand_file', ligandFile.file);
      formData.append('job_name', jobName.trim());
      if (note.trim()) {
        formData.append('note', note.trim());
      }

      // Call unified task API
      const response = await fetch(`/api/v1/tasks-unified/${task.id}/execute`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Execution failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (onJobSubmitted) {
        onJobSubmitted(result.execution_id);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Paper elevation={2} sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Science sx={{ mr: 2, color: 'primary.main' }} />
          <Typography variant="h5">{task.name}</Typography>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {task.description}
        </Typography>

        <Divider sx={{ mb: 3 }} />

        {/* File Upload Section */}
        <Grid container spacing={3}>
          {/* Receptor Upload */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Receptor Structure
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Upload protein receptor file (PDB format)
                </Typography>
                
                <Box
                  {...receptorDropzone.getRootProps()}
                  sx={{
                    border: 2,
                    borderColor: receptorDropzone.isDragActive ? 'primary.main' : 'grey.300',
                    borderStyle: 'dashed',
                    borderRadius: 2,
                    p: 3,
                    textAlign: 'center',
                    cursor: 'pointer',
                    transition: 'border-color 0.2s',
                    '&:hover': {
                      borderColor: 'primary.main'
                    }
                  }}
                >
                  <input {...receptorDropzone.getInputProps()} />
                  <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                  
                  {receptorFile ? (
                    <Box>
                      <Typography variant="subtitle2">{receptorFile.file.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(receptorFile.file.size / 1024).toFixed(1)} KB
                      </Typography>
                      <Chip 
                        label="PDB" 
                        size="small" 
                        color="success" 
                        sx={{ ml: 1 }} 
                      />
                    </Box>
                  ) : (
                    <Typography variant="body2">
                      Drop PDB file here or click to select
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Ligand Upload */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Ligand Structure
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Upload ligand molecule file (SDF format)
                </Typography>
                
                <Box
                  {...ligandDropzone.getRootProps()}
                  sx={{
                    border: 2,
                    borderColor: ligandDropzone.isDragActive ? 'primary.main' : 'grey.300',
                    borderStyle: 'dashed',
                    borderRadius: 2,
                    p: 3,
                    textAlign: 'center',
                    cursor: 'pointer',
                    transition: 'border-color 0.2s',
                    '&:hover': {
                      borderColor: 'primary.main'
                    }
                  }}
                >
                  <input {...ligandDropzone.getInputProps()} />
                  <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                  
                  {ligandFile ? (
                    <Box>
                      <Typography variant="subtitle2">{ligandFile.file.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(ligandFile.file.size / 1024).toFixed(1)} KB
                      </Typography>
                      <Chip 
                        label="SDF" 
                        size="small" 
                        color="success" 
                        sx={{ ml: 1 }} 
                      />
                    </Box>
                  ) : (
                    <Typography variant="body2">
                      Drop SDF file here or click to select
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Job Configuration */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Job Configuration
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Job Name"
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                placeholder="e.g., EGFR_erlotinib_docking"
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Notes (Optional)"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Add any notes about this docking run..."
              />
            </Grid>
          </Grid>
        </Box>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {/* Estimated Time */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <Timeline sx={{ mr: 1, verticalAlign: 'middle' }} />
            Estimated Execution Time: {Math.floor(task.execution_time_estimate / 60)} minutes
          </Typography>
        </Box>

        {/* Action Buttons */}
        <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
          
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!receptorFile || !ligandFile || !jobName.trim() || isSubmitting}
            startIcon={isSubmitting ? <CircularProgress size={20} /> : <Science />}
          >
            {isSubmitting ? 'Submitting...' : 'Start Docking'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};
```

## 2. Task Service Extension

Update the task service to call unified task endpoints:

```typescript
// Add to frontend/src/services/taskService.ts

export interface TaskExecution {
  execution_id: string;
  job_id?: string;
  status: string;
  task_id: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  results?: any;
  error_message?: string;
}

export const taskService = {
  // ... existing methods

  // New unified task methods
  async getUnifiedTasks(): Promise<TaskTemplate[]> {
    try {
      const response = await fetch('/api/v1/tasks-unified/');
      if (!response.ok) {
        throw new Error('Failed to fetch unified tasks');
      }
      return await response.json();
    } catch (error) {
      console.warn('Unified tasks not available, using fallback');
      return this.getTasks(); // Fallback to existing method
    }
  },

  async executeUnifiedTask(
    taskId: string, 
    files: Record<string, File>, 
    parameters: Record<string, any>
  ): Promise<TaskExecution> {
    const formData = new FormData();
    
    // Add files
    Object.entries(files).forEach(([key, file]) => {
      formData.append(key, file);
    });
    
    // Add parameters
    Object.entries(parameters).forEach(([key, value]) => {
      formData.append(key, String(value));
    });

    const response = await fetch(`/api/v1/tasks-unified/${taskId}/execute`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Execution failed: ${response.statusText}`);
    }

    return response.json();
  },

  async getExecutionStatus(executionId: string): Promise<TaskExecution> {
    const response = await fetch(`/api/v1/tasks-unified/executions/${executionId}/status`);
    
    if (!response.ok) {
      throw new Error(`Failed to get execution status: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getExecutionResults(executionId: string): Promise<any> {
    const response = await fetch(`/api/v1/tasks-unified/executions/${executionId}/results`);
    
    if (!response.ok) {
      throw new Error(`Failed to get execution results: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getUserExecutions(): Promise<TaskExecution[]> {
    const response = await fetch('/api/v1/tasks-unified/executions');
    
    if (!response.ok) {
      throw new Error(`Failed to get user executions: ${response.statusText}`);
    }
    
    return response.json();
  }
};
```

## 3. Task Library Integration

Update TaskLibrary to show GNINA tasks:

```typescript
// Modify frontend/src/pages/TaskLibrary.tsx

import { GninaDockingWizard } from '../components/tasks/GninaDockingWizard';

// Add to component state
const [showGninaWizard, setShowGninaWizard] = useState(false);
const [selectedGninaTask, setSelectedGninaTask] = useState<TaskTemplate | null>(null);

// Update the task card click handler
const handleTaskClick = (task: TaskTemplate) => {
  if (task.id === 'gnina-molecular-docking') {
    setSelectedGninaTask(task);
    setShowGninaWizard(true);
  } else {
    navigate(`/tasks/execute/${task.id}`);
  }
};

// Add to JSX before closing component
{showGninaWizard && selectedGninaTask && (
  <GninaDockingWizard
    task={selectedGninaTask}
    onJobSubmitted={(jobId) => {
      setShowGninaWizard(false);
      navigate(`/job-manager?execution=${jobId}`);
    }}
    onCancel={() => setShowGninaWizard(false)}
  />
)}
```

## 4. Job Manager Integration

Update JobManager to show unified executions:

```typescript
// Add to frontend/src/pages/JobManager.tsx

import { taskService, TaskExecution } from '../services/taskService';

// Add state for unified executions
const [unifiedExecutions, setUnifiedExecutions] = useState<TaskExecution[]>([]);

// Add fetch function
const fetchUnifiedExecutions = async () => {
  try {
    const executions = await taskService.getUserExecutions();
    setUnifiedExecutions(executions);
  } catch (error) {
    console.warn('Could not fetch unified executions:', error);
  }
};

// Update useEffect to fetch both types
useEffect(() => {
  fetchJobs();
  fetchUnifiedExecutions();
}, []);

// Add unified executions to job list rendering
const allJobs = [
  ...jobs,
  ...unifiedExecutions.map(exec => ({
    job_id: exec.execution_id,
    job_name: exec.job_id || exec.execution_id.slice(0, 8),
    status: exec.status,
    created_at: exec.created_at,
    type: 'task-framework',
    task_id: exec.task_id
  }))
];
```

## 5. Database Seeding Script

Create a seed script for GNINA task:

```sql
-- database/seeds/gnina_task_seed.sql

-- Insert demo organization if not exists
INSERT INTO organizations (org_id, name, description, is_active, created_at)
VALUES (
    'demo-org-id'::uuid,
    'Demo Organization', 
    'Demo organization for task framework testing',
    true,
    NOW()
) ON CONFLICT (org_id) DO NOTHING;

-- Insert GNINA task definition
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
    'demo-org-id'::uuid,
    '1.0.0',
    '{
        "name": "GNINA Molecular Docking",
        "description": "Neural network-guided molecular docking using GNINA via NeuroSnap API",
        "category": "molecular_docking",
        "engine": "gnina",
        "tags": ["docking", "neural-network", "protein-ligand", "gnina", "neurosnap"],
        "execution_time_estimate": 1200,
        "resource_requirements": {
            "cpu_cores": 2,
            "memory_gb": 4,
            "disk_gb": 2
        },
        "provider": "neurosnap",
        "output_types": ["docked_poses", "binding_scores", "interaction_analysis"]
    }'::jsonb,
    '{
        "openapi": "3.0.0",
        "info": {
            "title": "GNINA Molecular Docking",
            "version": "1.0.0",
            "description": "Neural network-guided molecular docking"
        },
        "paths": {
            "/execute": {
                "post": {
                    "summary": "Execute GNINA docking",
                    "requestBody": {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "receptor_file": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": "Protein receptor in PDB format"
                                        },
                                        "ligand_file": {
                                            "type": "string", 
                                            "format": "binary",
                                            "description": "Ligand molecule in SDF format"
                                        },
                                        "job_name": {
                                            "type": "string",
                                            "description": "Name for the docking job"
                                        },
                                        "note": {
                                            "type": "string",
                                            "description": "Optional notes for the job"
                                        }
                                    },
                                    "required": ["receptor_file", "ligand_file", "job_name"]
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
        "source": "framework"
    }'::jsonb,
    true,
    true,
    NOW()
) ON CONFLICT (task_id, org_id) DO NOTHING;
```

This comprehensive integration plan will seamlessly add GNINA molecular docking to your existing dashboard with unified task management, real-time job monitoring, and consistent user experience!