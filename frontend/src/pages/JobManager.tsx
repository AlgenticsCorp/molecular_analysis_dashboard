import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  Search,
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Visibility,
  Download,
  Delete,
  Schedule,
  CheckCircle,
  Error,
  Add,
  GetApp,
  Memory,
  Speed,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { taskService } from '../services/taskService';

// Types for job management
interface Job {
  id: string;
  name: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  startTime?: string;
  endTime?: string;
  runtime?: string;
  priority: 'low' | 'medium' | 'high';
  taskType: string;
  parameters: Record<string, unknown>;
  inputFiles: Array<{ name: string; size: string; url?: string }>;
  outputFiles: Array<{ name: string; size: string; url?: string }>;
  logs: string[];
  errorMessage?: string;
  resourceUsage?: {
    cpu: number;
    memory: number;
    diskSpace: number;
  };
}

interface JobFilter {
  status: string;
  taskType: string;
  priority: string;
  searchTerm: string;
}

// Fetch jobs with error handling and fallback
const fetchJobs = async (filters: JobFilter): Promise<{ jobs: Job[], source: 'api' | 'fallback' }> => {
  try {
    // Fetch real executions from API
    const executionsData = await taskService.listExecutions();
    const executions = executionsData.executions || [];
    
    // Transform API data to Job interface
    const jobs: Job[] = await Promise.all(executions.map(async (exec: any) => {
      // Calculate runtime
      let runtime: string | undefined;
      if (exec.started_at) {
        const start = new Date(exec.started_at);
        const end = exec.completed_at ? new Date(exec.completed_at) : new Date();
        const durationMs = end.getTime() - start.getTime();
        const hours = Math.floor(durationMs / (1000 * 60 * 60));
        const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
        runtime = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
      }

      // Fetch file information from results endpoint if completed
      let inputFiles: Array<{ name: string; size: string; url?: string }> = [];
      let outputFiles: Array<{ name: string; size: string; url?: string }> = [];
      
      if (exec.status === 'completed' || exec.status === 'failed') {
        try {
          const results = await taskService.getExecutionResults(exec.execution_id);
          
          // Parse input files from raw_data
          if (results.raw_data?.in) {
            inputFiles = results.raw_data.in.map(([name, size]: [string, string]) => ({
              name,
              size,
              url: results.download_urls?.[name] || undefined
            }));
          }
          
          // Parse output files from raw_data
          if (results.raw_data?.out) {
            outputFiles = results.raw_data.out.map(([name, size]: [string, string]) => ({
              name,
              size,
              url: results.download_urls?.[name] || undefined
            }));
          }
        } catch (error) {
          console.warn(`Failed to fetch results for execution ${exec.execution_id}:`, error);
        }
      }

      return {
        id: exec.execution_id,
        name: exec.display_name || `Task ${exec.task_id}`,
        description: `Execution ID: ${exec.execution_id}`,
        status: exec.status.toLowerCase(), // Convert to lowercase to match Job interface
        progress: exec.progress_percentage || 0,
        startTime: exec.created_at,
        endTime: exec.completed_at,
        runtime,
        priority: 'medium' as const, // Default priority since not in API
        taskType: exec.task_id || 'unknown',
        parameters: exec.input_data || {},
        inputFiles,
        outputFiles,
        logs: exec.error_message ? [exec.error_message] : ['Job execution in progress...'],
        errorMessage: exec.error_message,
      };
    }));

    // Apply filters
    const filteredJobs = jobs.filter((job) => {
      const matchesStatus = filters.status === 'all' || job.status === filters.status;
      const matchesType = filters.taskType === 'all' || job.taskType === filters.taskType;
      const matchesPriority = filters.priority === 'all' || job.priority === filters.priority;
      const matchesSearch =
        filters.searchTerm === '' ||
        job.name.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
        job.description?.toLowerCase().includes(filters.searchTerm.toLowerCase());

      return matchesStatus && matchesType && matchesPriority && matchesSearch;
    });

    return { jobs: filteredJobs, source: 'api' };
  } catch (error) {
    console.error('Error fetching jobs:', error);
    
    // Return fallback mock data on error
    const mockJobs: Job[] = [
      {
        id: 'mock-1',
        name: 'Sample Docking Job (Offline Mode)',
        description: 'This is sample data - API is unavailable',
        status: 'completed',
        progress: 100,
        startTime: new Date(Date.now() - 3600000).toISOString(),
        endTime: new Date().toISOString(),
        runtime: '1h 0m',
        priority: 'medium',
        taskType: 'gnina-molecular-docking',
        parameters: {},
        inputFiles: [],
        outputFiles: [],
        logs: ['Sample job - API offline'],
      },
    ];

    // Apply filters to mock data
    const filteredJobs = mockJobs.filter((job) => {
      const matchesStatus = filters.status === 'all' || job.status === filters.status;
      const matchesType = filters.taskType === 'all' || job.taskType === filters.taskType;
      const matchesPriority = filters.priority === 'all' || job.priority === filters.priority;
      const matchesSearch =
        filters.searchTerm === '' ||
        job.name.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
        job.description?.toLowerCase().includes(filters.searchTerm.toLowerCase());

      return matchesStatus && matchesType && matchesPriority && matchesSearch;
    });

    return { jobs: filteredJobs, source: 'fallback' };
  }
};

export const JobManager: React.FC = () => {
  const [filters, setFilters] = useState<JobFilter>({
    status: 'all',
    taskType: 'all',
    priority: 'all',
    searchTerm: '',
  });
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [dataSource, setDataSource] = useState<'api' | 'fallback'>('api');

  // TanStack Query for job data
  const {
    data: jobsData,
    error,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: async () => {
      const result = await fetchJobs(filters);
      setDataSource(result.source);
      return result.jobs;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
    retry: 3,
  });

  const jobs = jobsData || [];

  // Real-time updates disabled - using polling with refetchInterval instead
  // WebSocket functionality can be re-enabled when backend WebSocket support is added

  // Job actions
  const pauseJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      // Mock API call
      console.warn('Pausing job:', jobId);
      await new Promise((resolve) => setTimeout(resolve, 1000));
    },
    onSuccess: () => {
      refetch();
    },
  });

  const stopJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      // Mock API call
      console.warn('Stopping job:', jobId);
      await new Promise((resolve) => setTimeout(resolve, 1000));
    },
    onSuccess: () => {
      refetch();
    },
  });

  const deleteJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      // Mock API call
      console.warn('Deleting job:', jobId);
      await new Promise((resolve) => setTimeout(resolve, 1000));
    },
    onSuccess: () => {
      refetch();
    },
  });

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'info' | 'default' => {
    const lowerStatus = status.toLowerCase();
    switch (lowerStatus) {
      case 'completed':
      case 'succeeded':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      case 'pending':
        return 'warning';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    const lowerStatus = status.toLowerCase();
    switch (lowerStatus) {
      case 'completed':
      case 'succeeded':
        return <CheckCircle />;
      case 'failed':
        return <Error />;
      case 'running':
        return <PlayArrow />;
      case 'pending':
        return <Schedule />;
      case 'cancelled':
        return <Stop />;
      default:
        return <Schedule />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const handleJobAction = (action: string, jobId: string) => {
    switch (action) {
      case 'pause':
        pauseJobMutation.mutate(jobId);
        break;
      case 'stop':
        stopJobMutation.mutate(jobId);
        break;
      case 'delete':
        deleteJobMutation.mutate(jobId);
        break;
      default:
        break;
    }
  };

  const handleViewDetails = (job: Job) => {
    setSelectedJob(job);
    setDetailsOpen(true);
  };

  const renderJobsTable = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Job Name</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Progress</TableCell>
            <TableCell>Priority</TableCell>
            <TableCell>Runtime</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {jobs.map((job) => (
            <TableRow key={job.id} hover>
              <TableCell>
                <Box>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {job.name}
                  </Typography>
                  {job.description && (
                    <Typography variant="body2" color="text.secondary">
                      {job.description}
                    </Typography>
                  )}
                </Box>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {getStatusIcon(job.status)}
                  <Chip
                    label={job.status}
                    color={getStatusColor(job.status)}
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Box>
              </TableCell>
              <TableCell>
                <Box sx={{ width: 100 }}>
                  <LinearProgress
                    variant="determinate"
                    value={job.progress}
                    color={job.status === 'failed' ? 'error' : 'primary'}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {job.progress}%
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Chip
                  label={job.priority}
                  color={
                    getPriorityColor(job.priority) as 'error' | 'warning' | 'success' | 'default'
                  }
                  size="small"
                  variant="outlined"
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2">{job.runtime || '-'}</Typography>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="View Details">
                    <IconButton size="small" onClick={() => handleViewDetails(job)}>
                      <Visibility />
                    </IconButton>
                  </Tooltip>
                  {job.status === 'running' && (
                    <Tooltip title="Pause Job">
                      <IconButton
                        size="small"
                        onClick={() => handleJobAction('pause', job.id)}
                        disabled={pauseJobMutation.isPending}
                      >
                        <Pause />
                      </IconButton>
                    </Tooltip>
                  )}
                  {(job.status === 'running' || job.status === 'pending') && (
                    <Tooltip title="Stop Job">
                      <IconButton
                        size="small"
                        onClick={() => handleJobAction('stop', job.id)}
                        disabled={stopJobMutation.isPending}
                        color="error"
                      >
                        <Stop />
                      </IconButton>
                    </Tooltip>
                  )}
                  <Tooltip title="Delete Job">
                    <IconButton
                      size="small"
                      onClick={() => handleJobAction('delete', job.id)}
                      disabled={deleteJobMutation.isPending}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </Tooltip>
                  {job.outputFiles.length > 0 && (
                    <Tooltip title="Download Results">
                      <IconButton size="small" color="primary">
                        <Download />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 600 }}>
            Job Manager
          </Typography>
          {dataSource === 'fallback' && (
            <Chip
              label="Offline Mode"
              color="warning"
              size="small"
              icon={<Error />}
            />
          )}
          {dataSource === 'api' && (
            <Chip
              label="Live Data"
              color="success"
              size="small"
              icon={<CheckCircle />}
            />
          )}
        </Box>
        <Button variant="contained" startIcon={<Add />} href="/tasks">
          New Job
        </Button>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Using offline mode - API unavailable. Showing sample data.
        </Alert>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search jobs..."
                value={filters.searchTerm}
                onChange={(e) => setFilters({ ...filters, searchTerm: e.target.value })}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.status}
                  label="Status"
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="PENDING">Pending</MenuItem>
                  <MenuItem value="RUNNING">Running</MenuItem>
                  <MenuItem value="SUCCEEDED">Succeeded</MenuItem>
                  <MenuItem value="FAILED">Failed</MenuItem>
                  <MenuItem value="CANCELLED">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Task Type</InputLabel>
                <Select
                  value={filters.taskType}
                  label="Task Type"
                  onChange={(e) => setFilters({ ...filters, taskType: e.target.value })}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="autodock_vina">AutoDock Vina</MenuItem>
                  <MenuItem value="autodock4">AutoDock 4</MenuItem>
                  <MenuItem value="pipeline">Pipeline</MenuItem>
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={filters.priority}
                  label="Priority"
                  onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
                >
                  <MenuItem value="all">All Priorities</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={() => refetch()}
                disabled={isLoading}
                fullWidth
              >
                Refresh
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Jobs Table */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <LinearProgress sx={{ width: '50%' }} />
        </Box>
      ) : jobs.length === 0 ? (
        <Paper sx={{ p: 8, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No jobs found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create your first molecular docking job to get started
          </Typography>
          <Button variant="contained" sx={{ mt: 2 }} href="/tasks">
            Create New Job
          </Button>
        </Paper>
      ) : (
        renderJobsTable()
      )}

      {/* Job Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="lg" fullWidth>
        {selectedJob && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6">{selectedJob.name}</Typography>
                <Chip
                  label={selectedJob.status}
                  color={getStatusColor(selectedJob.status)}
                  sx={{ ml: 2 }}
                />
              </Box>
            </DialogTitle>
            <DialogContent>
              <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
                <Tab label="Overview" />
                <Tab label="Parameters" />
                <Tab label="Files" />
                <Tab label="Logs" />
                <Tab label="Resources" />
              </Tabs>

              <Box sx={{ mt: 3 }}>
                {tabValue === 0 && (
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="h6" gutterBottom>
                        Job Information
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemText primary="Job ID" secondary={selectedJob.id} />
                        </ListItem>
                        <ListItem>
                          <ListItemText primary="Task Type" secondary={selectedJob.taskType} />
                        </ListItem>
                        <ListItem>
                          <ListItemText primary="Priority" secondary={selectedJob.priority} />
                        </ListItem>
                        <ListItem>
                          <ListItemText primary="Progress" secondary={`${selectedJob.progress}%`} />
                        </ListItem>
                        {selectedJob.runtime && (
                          <ListItem>
                            <ListItemText primary="Runtime" secondary={selectedJob.runtime} />
                          </ListItem>
                        )}
                      </List>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      {selectedJob.description && (
                        <>
                          <Typography variant="h6" gutterBottom>
                            Description
                          </Typography>
                          <Typography variant="body2" paragraph>
                            {selectedJob.description}
                          </Typography>
                        </>
                      )}
                      {selectedJob.errorMessage && (
                        <Alert severity="error" sx={{ mt: 2 }}>
                          {selectedJob.errorMessage}
                        </Alert>
                      )}
                    </Grid>
                  </Grid>
                )}

                {tabValue === 1 && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Parameters
                    </Typography>
                    <pre style={{ backgroundColor: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                      {JSON.stringify(selectedJob.parameters, null, 2)}
                    </pre>
                  </Box>
                )}

                {tabValue === 2 && (
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="h6" gutterBottom>
                        Input Files
                      </Typography>
                      <List dense>
                        {selectedJob.inputFiles.map((file, index) => (
                          <ListItem key={index}>
                            <ListItemText 
                              primary={file.name} 
                              secondary={file.size}
                            />
                            {file.url && (
                              <IconButton 
                                size="small" 
                                component="a" 
                                href={file.url} 
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <Download />
                              </IconButton>
                            )}
                          </ListItem>
                        ))}
                      </List>
                      {selectedJob.inputFiles.length === 0 && (
                        <Typography variant="body2" color="text.secondary">
                          No input files available
                        </Typography>
                      )}
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="h6" gutterBottom>
                        Output Files
                      </Typography>
                      <List dense>
                        {selectedJob.outputFiles.map((file, index) => (
                          <ListItem key={index}>
                            <ListItemText 
                              primary={file.name} 
                              secondary={file.size}
                            />
                            {file.url && (
                              <IconButton 
                                size="small" 
                                component="a" 
                                href={file.url} 
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <Download />
                              </IconButton>
                            )}
                          </ListItem>
                        ))}
                      </List>
                      {selectedJob.outputFiles.length === 0 && (
                        <Typography variant="body2" color="text.secondary">
                          No output files generated yet
                        </Typography>
                      )}
                    </Grid>
                  </Grid>
                )}

                {tabValue === 3 && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Job Logs
                    </Typography>
                    <Paper
                      sx={{ p: 2, backgroundColor: '#f8f9fa', maxHeight: 400, overflow: 'auto' }}
                    >
                      {selectedJob.logs.map((log, index) => (
                        <Typography
                          key={index}
                          variant="body2"
                          sx={{ fontFamily: 'monospace', mb: 1 }}
                        >
                          {log}
                        </Typography>
                      ))}
                    </Paper>
                  </Box>
                )}

                {tabValue === 4 && selectedJob.resourceUsage && (
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={4}>
                      <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Speed sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                          <Typography variant="h6">CPU Usage</Typography>
                          <Typography variant="h4" color="primary">
                            {selectedJob.resourceUsage.cpu}%
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Memory sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                          <Typography variant="h6">Memory</Typography>
                          <Typography variant="h4" color="warning.main">
                            {selectedJob.resourceUsage.memory} MB
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                          <GetApp sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                          <Typography variant="h6">Disk Usage</Typography>
                          <Typography variant="h4" color="success.main">
                            {selectedJob.resourceUsage.diskSpace} MB
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                )}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailsOpen(false)}>Close</Button>
              {selectedJob.outputFiles.length > 0 && (
                <Button variant="contained" startIcon={<Download />}>
                  Download Results
                </Button>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};
