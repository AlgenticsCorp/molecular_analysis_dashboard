import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import { ArrowBack, ArrowForward, PlayArrow } from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { taskService } from '../services/taskService';
import { TaskTemplate } from '../types/tasks';
import { DynamicTaskForm, FormValues, FormErrors } from '../components/task/DynamicTaskForm';

export const ExecuteTasks: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const taskId = searchParams.get('task');

  const [task, setTask] = useState<TaskTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formValues, setFormValues] = useState<FormValues>({});
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [activeStep, setActiveStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);

  // Load task details
  useEffect(() => {
    const loadTask = async () => {
      if (!taskId) {
        setError('No task specified');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await taskService.getTaskDetail({ task_id: taskId });
        setTask(response.data);

        // Initialize form with default values
        const defaults: FormValues = {};
        response.data.parameters.forEach((param) => {
          if (param.default !== undefined) {
            defaults[param.name] = param.default;
          }
        });
        setFormValues(defaults);
        setError(null);
      } catch (err) {
        console.error('Failed to load task:', err);
        setError(err instanceof Error ? err.message : 'Failed to load task details');
      } finally {
        setLoading(false);
      }
    };

    loadTask();
  }, [taskId]);

  const handleFormChange = (name: string, value: any) => {
    setFormValues((prev) => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (formErrors[name]) {
      setFormErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    if (!task) return false;

    const errors: FormErrors = {};
    task.parameters.forEach((param) => {
      const value = formValues[param.name];

      // Required validation
      if (param.required && (value === undefined || value === null || value === '')) {
        errors[param.name] = `${param.name} is required`;
      }
    });

    // Task-specific validation: DynamicBind requires at least one ligand source
    if (task.id === 'neurosnap-dynamicbind') {
      const ligandFile = formValues['ligand_file'];
      const ligandEntries = formValues['ligand_entries_json'];
      const hasLigandFile = ligandFile instanceof File;
      const hasLigandEntries = typeof ligandEntries === 'string'
        ? ligandEntries.trim().length > 0
        : Array.isArray(ligandEntries) && ligandEntries.length > 0;

      if (!hasLigandFile && !hasLigandEntries) {
        const message = 'Provide a ligand file or ligand_entries_json';
        errors['ligand_file'] = message;
        errors['ligand_entries_json'] = message;
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (activeStep === 0) {
      // Validate parameters before moving to review
      if (validateForm()) {
        setActiveStep(1);
      }
    } else {
      setActiveStep(activeStep + 1);
    }
  };

  const handleBack = () => {
    if (activeStep === 0) {
      navigate('/task-library');
    } else {
      setActiveStep(activeStep - 1);
    }
  };

  const handleExecute = async () => {
    if (!task || !taskId) return;

    setSubmitting(true);
    try {
      const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');

      // Prepare form data
      const formData = new FormData();

      task.parameters.forEach((param) => {
        const value = formValues[param.name];
        if (value !== undefined && value !== null) {
          if (param.type === 'file' && value instanceof File) {
            formData.append(param.name, value);
          } else {
            formData.append(param.name, String(value));
          }
        }
      });

      // Submit to API
      const response = await fetch(`${apiBase}/tasks-unified/${taskId}/execute`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const detail =
          errorData?.detail ||
          errorData?.message ||
          errorData?.error ||
          errorData?.errors?.[0]?.msg;
        const message = detail || `HTTP ${response.status}: ${response.statusText}`;
        throw new Error(message);
      }

      const result = await response.json();
      setExecutionId(result.id || result.execution_id);
      setActiveStep(2); // Move to success step
    } catch (err) {
      console.error('Failed to execute task:', err);
      setError(err instanceof Error ? err.message : 'Failed to execute task');
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewMonitor = () => {
    if (executionId) {
      navigate('/job-manager', { 
        state: { 
          newJobId: executionId,
          message: 'Task submitted successfully! Your job is now running.' 
        } 
      });
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '400px',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error && !task) {
    return (
      <Box sx={{ maxWidth: 1280, mx: 'auto', p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button variant="outlined" onClick={() => navigate('/task-library')}>
          Back to Task Library
        </Button>
      </Box>
    );
  }

  if (!task) {
    return (
      <Box sx={{ maxWidth: 1280, mx: 'auto', p: 3 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            Select a Task
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Choose a molecular analysis task from the Task Library to begin configuration.
          </Typography>
          <Button variant="contained" onClick={() => navigate('/task-library')} size="large">
            Go to Task Library
          </Button>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1280, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" component="h1" sx={{ fontWeight: 600, mb: 1 }}>
          {task.name}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {task.description}
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Stepper */}
      <Paper sx={{ borderRadius: 3, boxShadow: 2, p: 4 }}>
        <Stepper activeStep={activeStep} orientation="vertical">
          {/* Step 1: Configure Parameters */}
          <Step>
            <StepLabel>
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                Configure Parameters
              </Typography>
            </StepLabel>
            <StepContent>
              <Box sx={{ mt: 2 }}>
                <DynamicTaskForm
                  parameters={task.parameters}
                  values={formValues}
                  onChange={handleFormChange}
                  errors={formErrors}
                  allowFileUpload={true}
                />

                {/* Navigation */}
                <Box sx={{ display: 'flex', gap: 2, mt: 4 }}>
                  <Button
                    variant="outlined"
                    onClick={handleBack}
                    startIcon={<ArrowBack />}
                    sx={{ textTransform: 'uppercase', fontWeight: 500 }}
                  >
                    Back
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleNext}
                    endIcon={<ArrowForward />}
                    sx={{ textTransform: 'uppercase', fontWeight: 500 }}
                  >
                    Next
                  </Button>
                </Box>
              </Box>
            </StepContent>
          </Step>

          {/* Step 2: Review & Execute */}
          <Step>
            <StepLabel>
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                Review & Execute
              </Typography>
            </StepLabel>
            <StepContent>
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 500 }}>
                  Parameters Summary
                </Typography>
                <Paper sx={{ p: 3, backgroundColor: 'grey.50', mb: 3 }}>
                  {task.parameters.map((param) => {
                    const value = formValues[param.name];
                    if (value === undefined || value === null) return null;

                    return (
                      <Box key={param.name} sx={{ mb: 1 }}>
                        <Typography variant="body2" component="span" sx={{ fontWeight: 500 }}>
                          {param.name}:
                        </Typography>{' '}
                        <Typography variant="body2" component="span">
                          {param.type === 'file' && value instanceof File
                            ? value.name
                            : String(value)}
                        </Typography>
                      </Box>
                    );
                  })}
                </Paper>

                {/* Navigation */}
                <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
                  <Button
                    variant="outlined"
                    onClick={handleBack}
                    startIcon={<ArrowBack />}
                    sx={{ textTransform: 'uppercase', fontWeight: 500 }}
                    disabled={submitting}
                  >
                    Back
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleExecute}
                    endIcon={<PlayArrow />}
                    sx={{ textTransform: 'uppercase', fontWeight: 500 }}
                    disabled={submitting}
                  >
                    {submitting ? 'Submitting...' : 'Execute Task'}
                  </Button>
                </Box>
              </Box>
            </StepContent>
          </Step>

          {/* Step 3: Success */}
          <Step>
            <StepLabel>
              <Typography variant="h6" sx={{ fontWeight: 500, color: 'success.main' }}>
                Task Submitted Successfully!
              </Typography>
            </StepLabel>
            <StepContent>
              <Box sx={{ mt: 2, textAlign: 'center', py: 4 }}>
                <Typography variant="h5" gutterBottom color="success.main">
                  ✓ Your task has been submitted
                </Typography>
                {executionId && (
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                    Execution ID: {executionId}
                  </Typography>
                )}
                {task.execution_time_estimate && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                    Estimated completion time: {Math.ceil(task.execution_time_estimate / 60)}{' '}
                    minutes
                  </Typography>
                )}

                <Button
                  variant="contained"
                  onClick={handleViewMonitor}
                  size="large"
                  sx={{ mr: 2 }}
                >
                  View in Job Manager
                </Button>
              </Box>
            </StepContent>
          </Step>
        </Stepper>
      </Paper>
    </Box>
  );
};
