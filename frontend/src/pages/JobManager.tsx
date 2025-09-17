import React, { useState, useEffect } from 'react';
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
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Types for job management
interface Job {
  id: string;
  name: string;
  description?: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED';
  progress: number;
  startTime?: string;
  endTime?: string;
  runtime?: string;
  priority: 'low' | 'medium' | 'high';
  taskType: string;
  parameters: Record<string, unknown>;
  inputFiles: string[];
  outputFiles: string[];
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

// Mock WebSocket connection for real-time updates
class JobWebSocket {
  private ws: WebSocket | null = null;
  private onUpdate: (job: Job) => void;

  constructor(onUpdate: (job: Job) => void) {
    this.onUpdate = onUpdate;
    this.connect();
  }

  private connect() {
    // In real implementation, this would connect to actual WebSocket
    console.warn('WebSocket connection established');

    // Simulate real-time updates
    setInterval(() => {
      if (Math.random() > 0.8) {
        this.simulateJobUpdate();
      }
    }, 5000);
  }

  private simulateJobUpdate() {
    const mockJob: Job = {
      id: 'job-' + Date.now(),
      name: 'AutoDock Vina - Real-time Update',
      status: 'RUNNING',
      progress: Math.floor(Math.random() * 100),
      taskType: 'autodock_vina',
      priority: 'medium',
      parameters: {},
      inputFiles: [],
      outputFiles: [],
      logs: ['Processing...'],
    };
    this.onUpdate(mockJob);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Mock API functions
const fetchJobs = async (filters: JobFilter): Promise<Job[]> => {
  // Mock data - replace with actual API call
  const mockJobs: Job[] = [
    {
      id: '1',
      name: 'AutoDock Vina - Protein Complex A',
      description: 'Molecular docking analysis for drug target identification',
      status: 'SUCCEEDED',
      progress: 100,
      startTime: '2025-09-10T10:30:00Z',
      endTime: '2025-09-10T12:04:00Z',
      runtime: '1h 34m',
      priority: 'high',
      taskType: 'autodock_vina',
      parameters: { exhaustiveness: 8, num_modes: 9 },
      inputFiles: ['receptor.pdbqt', 'ligand.pdbqt'],
      outputFiles: ['output.pdbqt', 'log.txt'],
      logs: ['Job started', 'Processing docking...', 'Job completed successfully'],
      resourceUsage: { cpu: 85, memory: 2048, diskSpace: 512 },
    },
    {
      id: '2',
      name: 'Virtual Screening Pipeline',
      description: 'High-throughput screening of compound library',
      status: 'RUNNING',
      progress: 67,
      startTime: '2025-09-10T11:45:00Z',
      runtime: '2h 15m',
      priority: 'medium',
      taskType: 'pipeline',
      parameters: { library_size: 10000, scoring_function: 'vina' },
      inputFiles: ['receptor.pdbqt', 'library.sdf'],
      outputFiles: [],
      logs: ['Job started', 'Processing compound 6,700 of 10,000...'],
      resourceUsage: { cpu: 92, memory: 4096, diskSpace: 2048 },
    },
    {
      id: '3',
      name: 'AutoDock 4 - Advanced Parameters',
      status: 'FAILED',
      progress: 45,
      startTime: '2025-09-10T09:20:00Z',
      endTime: '2025-09-10T10:15:00Z',
      runtime: '55m',
      priority: 'low',
      taskType: 'autodock4',
      parameters: { ga_runs: 50, ga_pop_size: 300 },
      inputFiles: ['receptor.pdbqt', 'ligand.pdbqt', 'grid.gpf'],
      outputFiles: [],
      logs: ['Job started', 'Error: Invalid grid file format'],
      errorMessage: 'Grid file format validation failed',
      resourceUsage: { cpu: 45, memory: 1024, diskSpace: 256 },
    },
    {
      id: '4',
      name: 'Conformational Analysis',
      status: 'PENDING',
      progress: 0,
      priority: 'medium',
      taskType: 'custom',
      parameters: { conformer_count: 100 },
      inputFiles: ['molecule.sdf'],
      outputFiles: [],
      logs: ['Job queued'],
    },
  ];

  // Apply filters
  return mockJobs.filter((job) => {
    const matchesStatus = filters.status === 'all' || job.status === filters.status;
    const matchesType = filters.taskType === 'all' || job.taskType === filters.taskType;
    const matchesPriority = filters.priority === 'all' || job.priority === filters.priority;
    const matchesSearch =
      filters.searchTerm === '' ||
      job.name.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
      job.description?.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
      '';

    return matchesStatus && matchesType && matchesPriority && matchesSearch;
  });
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
  const [, setWsConnection] = useState<JobWebSocket | null>(null);

  const queryClient = useQueryClient();

  // TanStack Query for job data
  const {
    data: jobs = [],
    error,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => fetchJobs(filters),
    refetchInterval: 10000, // Refresh every 10 seconds
    retry: 3,
  });

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new JobWebSocket((updatedJob: Job) => {
      queryClient.setQueryData(['jobs', filters], (oldJobs: Job[] | undefined) => {
        if (!oldJobs) return [updatedJob];
        const existingIndex = oldJobs.findIndex((job) => job.id === updatedJob.id);
        if (existingIndex >= 0) {
          const newJobs = [...oldJobs];
          newJobs[existingIndex] = updatedJob;
          return newJobs;
        }
        return [updatedJob, ...oldJobs];
      });
    });
    setWsConnection(ws);

    return () => {
      ws.disconnect();
    };
  }, [queryClient, filters]);

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
    switch (status) {
      case 'SUCCEEDED':
        return 'success';
      case 'FAILED':
        return 'error';
      case 'RUNNING':
        return 'info';
      case 'PENDING':
        return 'warning';
      case 'CANCELLED':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCEEDED':
        return <CheckCircle />;
      case 'FAILED':
        return <Error />;
      case 'RUNNING':
        return <PlayArrow />;
      case 'PENDING':
        return <Schedule />;
      case 'CANCELLED':
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
                    color={job.status === 'FAILED' ? 'error' : 'primary'}
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
                  {job.status === 'RUNNING' && (
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
                  {(job.status === 'RUNNING' || job.status === 'PENDING') && (
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
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Job Manager
        </Typography>
        <Button variant="contained" startIcon={<Add />} href="/tasks">
          New Job
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load jobs. Please check your connection and try again.
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
                            <ListItemText primary={file} />
                          </ListItem>
                        ))}
                      </List>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="h6" gutterBottom>
                        Output Files
                      </Typography>
                      <List dense>
                        {selectedJob.outputFiles.map((file, index) => (
                          <ListItem key={index}>
                            <ListItemText primary={file} />
                            <IconButton size="small">
                              <Download />
                            </IconButton>
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
