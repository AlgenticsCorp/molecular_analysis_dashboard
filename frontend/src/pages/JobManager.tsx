import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Grid from '@mui/material/GridLegacy';
import {
  Box,
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
  DialogContentText,
  DialogActions,
  LinearProgress,
  CircularProgress,
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
  Error as ErrorIcon,
  Add,
  GetApp,
  Memory,
  Speed,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { taskService } from '../services/taskService';
import { JobFilesTree, type JobFile, type SelectedJobFile } from '../components/jobs/JobFilesTree';
import MolecularViewer from '../components/molecular/MolecularViewerSimple';
import { downloadFileById, formatFileSize, getFileExtension } from '@/utils/fileDownload';

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
  inputFiles: JobFile[];
  outputFiles: JobFile[];
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

type PreviewData =
  | { kind: 'molecule'; content: string; format: string }
  | { kind: 'text'; content: string }
  | { kind: 'unsupported' };

const MOLECULE_EXTENSIONS = new Set(['pdb', 'sdf', 'mol2', 'pdbqt', 'xyz']);
const TEXT_EXTENSIONS = new Set(['txt', 'log', 'json', 'csv', 'tsv', 'yaml', 'yml']);

const formatJobFileSize = (value: number | string | undefined): string => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return formatFileSize(value);
  }

  if (typeof value === 'string' && value.trim().length > 0) {
    return value;
  }

  return '-';
};

const mapExecutionFile = (file: any): JobFile => {
  const mapped: JobFile = {
    name: file?.filename || file?.name || 'Unnamed file',
    size: formatJobFileSize(file?.size ?? file?.size_bytes),
    sizeBytes:
      typeof file?.size === 'number' && Number.isFinite(file.size)
        ? file.size
        : typeof file?.size_bytes === 'number' && Number.isFinite(file.size_bytes)
          ? file.size_bytes
          : undefined,
    fileId: file?.file_id,
    parameterName: file?.parameter_name,
    storageBackend: file?.storage_backend,
    contentType: file?.content_type,
  };

  const derivedUrl = file?.file_id
    ? `/api/v1/tasks-unified/files/${file.file_id}/download`
    : file?.url;
  if (derivedUrl) {
    mapped.url = derivedUrl;
  }

  return mapped;
};

const mapLegacyFile = (name: string, size: string, url?: string): JobFile => {
  const mapped: JobFile = {
    name,
    size: formatJobFileSize(size),
  };

  if (url) {
    mapped.url = url;
  }

  return mapped;
};

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
      let inputFiles: JobFile[] = [];
      let outputFiles: JobFile[] = [];
      
      // Only fetch results for completed jobs (failed jobs may not have results)
      if (exec.status === 'completed') {
        try {
          const results = await taskService.getExecutionResults(exec.execution_id);

          if (Array.isArray(results?.input_files) && results.input_files.length > 0) {
            inputFiles = results.input_files.map((file: any) => mapExecutionFile(file));
          } else if (results?.raw_data?.in) {
            inputFiles = results.raw_data.in.map(([name, size]: [string, string]) =>
              mapLegacyFile(name, size, results?.download_urls?.[name]),
            );
          }

          if (Array.isArray(results?.output_files) && results.output_files.length > 0) {
            outputFiles = results.output_files.map((file: any) => mapExecutionFile(file));
          } else if (results?.raw_data?.out) {
            outputFiles = results.raw_data.out.map(([name, size]: [string, string]) =>
              mapLegacyFile(name, size, results?.download_urls?.[name]),
            );
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
  const location = useLocation();
  const navigate = useNavigate();
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
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [selectedFileNode, setSelectedFileNode] = useState<SelectedJobFile | null>(null);
  const [selectedFileNodeId, setSelectedFileNodeId] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const previewCacheRef = useRef<Map<string, PreviewData>>(new Map());
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [jobPendingDeletion, setJobPendingDeletion] = useState<Job | null>(null);

  // Show success message from navigation state
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      // Clear the state to prevent showing again on refresh
      window.history.replaceState({}, document.title);
    }
  }, [location]);

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
  const selectedJobHasFiles =
    !!selectedJob && (selectedJob.inputFiles.length > 0 || selectedJob.outputFiles.length > 0);

  useEffect(() => {
    if (!selectedFileNode) {
      return;
    }

    const job = jobs.find((item) => item.id === selectedFileNode.jobId);
    if (!job) {
      setSelectedFileNode(null);
      setSelectedFileNodeId(null);
      setPreviewData(null);
      setPreviewError(null);
      return;
    }

    const candidateFiles =
      selectedFileNode.fileType === 'input' ? job.inputFiles : job.outputFiles;

    const stillExists = candidateFiles.some((file) =>
      selectedFileNode.file.fileId
        ? file.fileId === selectedFileNode.file.fileId
        : file.name === selectedFileNode.file.name,
    );

    if (!stillExists) {
      setSelectedFileNode(null);
      setSelectedFileNodeId(null);
      setPreviewData(null);
      setPreviewError(null);
    }
  }, [jobs, selectedFileNode]);

  useEffect(() => {
    if (!detailsOpen) {
      setSelectedFileNode(null);
      setSelectedFileNodeId(null);
      setPreviewData(null);
      setPreviewError(null);
      return;
    }

    if (!selectedJob) {
      setSelectedFileNode(null);
      setSelectedFileNodeId(null);
      setPreviewData(null);
      setPreviewError(null);
      return;
    }

    if (selectedFileNode && selectedFileNode.jobId !== selectedJob.id) {
      setSelectedFileNode(null);
      setSelectedFileNodeId(null);
      setPreviewData(null);
      setPreviewError(null);
    }
  }, [detailsOpen, selectedJob, selectedFileNode]);

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
      await taskService.deleteExecution(jobId);
    },
    onSuccess: () => {
      refetch();
    },
    onSettled: () => {
      setDeleteDialogOpen(false);
      setJobPendingDeletion(null);
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
        return <ErrorIcon />;
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
        {
          const job = jobs.find((item) => item.id === jobId);
          if (job) {
            setJobPendingDeletion(job);
            setDeleteDialogOpen(true);
          }
        }
        break;
      default:
        break;
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setJobPendingDeletion(null);
  };

  const handleConfirmDelete = () => {
    if (!jobPendingDeletion) {
      return;
    }
    deleteJobMutation.mutate(jobPendingDeletion.id);
  };

  const loadPreview = useCallback(async (file: JobFile) => {
    if (!file.url) {
      setPreviewData(null);
      setPreviewError('Preview not available for this file');
      setPreviewLoading(false);
      return;
    }

    const extension = getFileExtension(file.name);
    const cacheKey = `${file.url}|${extension}`;
    const cached = previewCacheRef.current.get(cacheKey);

    if (cached) {
      setPreviewData(cached);
      setPreviewError(null);
      setPreviewLoading(false);
      return;
    }

    if (!MOLECULE_EXTENSIONS.has(extension) && !TEXT_EXTENSIONS.has(extension)) {
      const unsupported: PreviewData = { kind: 'unsupported' };
      previewCacheRef.current.set(cacheKey, unsupported);
      setPreviewData(unsupported);
      setPreviewError(null);
      setPreviewLoading(false);
      return;
    }

    setPreviewLoading(true);
    setPreviewError(null);
    setPreviewData(null);

    try {
      const requestOptions: RequestInit = { credentials: 'include' };

      if (TEXT_EXTENSIONS.has(extension) || MOLECULE_EXTENSIONS.has(extension)) {
        requestOptions.headers = { Accept: 'text/plain' };
      }

      const response = await fetch(file.url, requestOptions);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const textContent = await response.text();

      if (MOLECULE_EXTENSIONS.has(extension)) {
        const data: PreviewData = { kind: 'molecule', content: textContent, format: extension };
        previewCacheRef.current.set(cacheKey, data);
        setPreviewData(data);
      } else {
        const truncated =
          textContent.length > 10000
            ? `${textContent.slice(0, 10000)}\n\n… truncated for display …`
            : textContent;
        const data: PreviewData = { kind: 'text', content: truncated };
        previewCacheRef.current.set(cacheKey, data);
        setPreviewData(data);
      }
    } catch (error) {
      console.error('File preview error', error);
      setPreviewData(null);
      setPreviewError('Failed to load file preview');
    } finally {
      setPreviewLoading(false);
    }
  }, []);

  const handleSelectFile = useCallback(
    (selection: SelectedJobFile) => {
      setSelectedFileNode(selection);
      setSelectedFileNodeId(selection.nodeId);
      setPreviewError(null);
      setPreviewData(null);
      void loadPreview(selection.file);
    },
    [loadPreview],
  );

  const handleDownloadFile = useCallback(async (file: JobFile) => {
    try {
      if (file.fileId) {
        await downloadFileById(file.fileId, file.name);
      } else if (file.url) {
        window.open(file.url, '_blank', 'noopener,noreferrer');
      } else {
        alert('Download not available for this file.');
      }
    } catch (error) {
      console.error('File download failed', error);
      const message = error instanceof Error ? error.message : 'Failed to download file';
      alert(message);
    }
  }, []);

  const renderPreview = () => {
    if (!selectedFileNode) {
      return (
        <Box sx={{ py: 6, textAlign: 'center', color: 'text.secondary' }}>
          <Typography variant="body2">Select a job file to see its preview.</Typography>
        </Box>
      );
    }

    if (previewLoading) {
      return (
        <Box sx={{ py: 6, display: 'flex', justifyContent: 'center' }}>
          <CircularProgress size={32} />
        </Box>
      );
    }

    if (previewError) {
      return (
        <Alert severity="error">
          <Typography variant="body2">{previewError}</Typography>
        </Alert>
      );
    }

    if (!previewData) {
      return (
        <Alert severity="info">
          <Typography variant="body2">
            Preview not available for this file. Use the download button to open it locally.
          </Typography>
        </Alert>
      );
    }

    const fileMeta = selectedFileNode.file;
    const contextLabel = `${selectedFileNode.jobName} • ${
      selectedFileNode.fileType === 'input' ? 'Input' : 'Output'
    } file`;

    const header = (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 2,
          gap: 2,
          flexWrap: 'wrap',
        }}
      >
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="subtitle2" noWrap title={fileMeta.name}>
            {fileMeta.name}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {contextLabel}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {fileMeta.size && fileMeta.size !== '-' && (
            <Chip label={fileMeta.size} size="small" variant="outlined" />
          )}
          <Tooltip title="Download file">
            <span>
              <Button
                variant="outlined"
                size="small"
                startIcon={<Download />}
                onClick={() => handleDownloadFile(fileMeta)}
                disabled={!fileMeta.fileId && !fileMeta.url}
              >
                Download
              </Button>
            </span>
          </Tooltip>
        </Box>
      </Box>
    );

    if (previewData.kind === 'molecule') {
      return (
        <Box>
          {header}
          <MolecularViewer moleculeData={previewData.content} format={previewData.format} height={320} />
        </Box>
      );
    }

    if (previewData.kind === 'text') {
      const isTruncated = previewData.content.includes('… truncated for display …');
      return (
        <Box>
          {header}
          <Box
            component="pre"
            sx={{
              maxHeight: 320,
              overflow: 'auto',
              backgroundColor: 'grey.900',
              color: 'grey.100',
              borderRadius: 1,
              p: 2,
              fontSize: 12,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {previewData.content}
          </Box>
          {isTruncated && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Showing first 10k characters. Download for the full file.
            </Typography>
          )}
        </Box>
      );
    }

    return (
      <Box>
        {header}
        <Alert severity="info">
          <Typography variant="body2">
            Preview not supported for this file type. Download to inspect it locally.
          </Typography>
        </Alert>
      </Box>
    );
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
                  {job.status === 'completed' && (
                    <Tooltip title="View Results">
                      <Button
                        size="small"
                        variant="contained"
                        color="primary"
                        onClick={() => navigate(`/task-results/${job.id}`)}
                        sx={{ minWidth: 'auto', px: 1.5 }}
                      >
                        Results
                      </Button>
                    </Tooltip>
                  )}
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
      {successMessage && (
        <Alert 
          severity="success" 
          onClose={() => setSuccessMessage(null)}
          sx={{ mb: 3 }}
        >
          {successMessage}
        </Alert>
      )}

      <Dialog
        open={deleteDialogOpen}
        onClose={deleteJobMutation.isPending ? undefined : handleCancelDelete}
      >
        <DialogTitle>Delete Job</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {jobPendingDeletion
              ? `Are you sure you want to delete "${jobPendingDeletion.name}" and permanently remove all associated files?`
              : 'Are you sure you want to delete this job and its files?'}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete} disabled={deleteJobMutation.isPending}>
            Cancel
          </Button>
          <Button
            color="error"
            onClick={handleConfirmDelete}
            disabled={deleteJobMutation.isPending}
          >
            {deleteJobMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
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
              icon={<ErrorIcon />}
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
              <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
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
                  selectedJobHasFiles ? (
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={5}>
                        <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                          <Typography variant="h6" gutterBottom>
                            Job Files
                          </Typography>
                          <JobFilesTree
                            jobs={[selectedJob]}
                            onSelectFile={handleSelectFile}
                            onDownloadFile={handleDownloadFile}
                            selectedNodeId={selectedFileNodeId}
                          />
                        </Paper>
                      </Grid>
                      <Grid item xs={12} md={7}>
                        <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                          <Typography variant="h6" gutterBottom>
                            File Preview
                          </Typography>
                          {renderPreview()}
                        </Paper>
                      </Grid>
                    </Grid>
                  ) : (
                    <Alert severity="info">
                      <Typography variant="body2">
                        This execution has no files available yet. Check back after the job
                        completes or generates outputs.
                      </Typography>
                    </Alert>
                  )
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
