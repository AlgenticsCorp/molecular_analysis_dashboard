import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Grid,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Download as DownloadIcon,
  ArrowBack as ArrowBackIcon,
  Description as FileIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { downloadFileById, formatFileSize } from '../utils/fileDownload';

interface FileMetadata {
  file_id: string;
  parameter_name: string;
  filename: string;
  size: number;
  content_type?: string;
  url: string;
  md5_hash?: string;
  sha256_hash?: string;
  uploaded_at?: string;
}

interface ExecutionResults {
  execution_id: string;
  task_id: string;
  display_name: string;
  status: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  neurosnap_results?: {
    binding_affinity?: number;
    top_poses_count?: number;
    computation_time?: number;
    status?: string;
  };
  input_files: FileMetadata[];
  output_files: FileMetadata[];
}

const TaskResults: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  const [results, setResults] = useState<ExecutionResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (executionId) {
      fetchResults();
    }
  }, [executionId]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(
        `/api/v1/tasks-unified/executions/${executionId}/results`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch results: ${response.statusText}`);
      }
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (file: FileMetadata) => {
    try {
      // Use API download endpoint
      await downloadFileById(file.file_id, file.filename);
    } catch (err) {
      console.error('Download failed:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to download file';
      alert(errorMessage);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'info' => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      default:
        return 'warning';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/job-manager')}>
          Back to Jobs
        </Button>
      </Box>
    );
  }

  if (!results) {
    return (
      <Box p={3}>
        <Alert severity="warning">No results found for this execution</Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/job-manager')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Task Results</Typography>
      </Box>

      {/* Execution Summary */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                {results.display_name}
              </Typography>
              <Chip
                label={results.status}
                color={getStatusColor(results.status)}
                icon={results.status === 'completed' ? <CheckCircleIcon /> : <ErrorIcon />}
                sx={{ mb: 1 }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                Execution ID
              </Typography>
              <Typography variant="body1" fontFamily="monospace">
                {results.execution_id}
              </Typography>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                Task ID
              </Typography>
              <Typography variant="body1">{results.task_id}</Typography>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                Created
              </Typography>
              <Typography variant="body1">
                {new Date(results.created_at).toLocaleString()}
              </Typography>
            </Grid>
            
            {results.started_at && (
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Started
                </Typography>
                <Typography variant="body1">
                  {new Date(results.started_at).toLocaleString()}
                </Typography>
              </Grid>
            )}
            
            {results.completed_at && (
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Completed
                </Typography>
                <Typography variant="body1">
                  {new Date(results.completed_at).toLocaleString()}
                </Typography>
              </Grid>
            )}
            
            {results.error_message && (
              <Grid item xs={12}>
                <Alert severity="error">{results.error_message}</Alert>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>

      {/* NeuroSnap Results */}
      {results.neurosnap_results && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Computation Results
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={2}>
              {results.neurosnap_results.binding_affinity !== undefined && (
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Binding Affinity
                  </Typography>
                  <Typography variant="h6">
                    {results.neurosnap_results.binding_affinity} kcal/mol
                  </Typography>
                </Grid>
              )}
              
              {results.neurosnap_results.top_poses_count !== undefined && (
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Poses Generated
                  </Typography>
                  <Typography variant="h6">
                    {results.neurosnap_results.top_poses_count}
                  </Typography>
                </Grid>
              )}
              
              {results.neurosnap_results.computation_time !== undefined && (
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Computation Time
                  </Typography>
                  <Typography variant="h6">
                    {formatDuration(results.neurosnap_results.computation_time)}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Input Files */}
      {results.input_files.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Input Files
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Parameter</TableCell>
                    <TableCell>Filename</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Uploaded</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results.input_files.map((file) => (
                    <TableRow key={file.file_id}>
                      <TableCell>{file.parameter_name}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <FileIcon sx={{ mr: 1, fontSize: 20 }} />
                          {file.filename}
                        </Box>
                      </TableCell>
                      <TableCell>{formatFileSize(file.size)}</TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {file.content_type || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {file.uploaded_at
                          ? new Date(file.uploaded_at).toLocaleString()
                          : 'N/A'}
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Download">
                          <IconButton
                            size="small"
                            onClick={() => handleDownload(file)}
                            color="primary"
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Output Files */}
      {results.output_files.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Output Files
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Result Type</TableCell>
                    <TableCell>Filename</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results.output_files.map((file) => (
                    <TableRow key={file.file_id}>
                      <TableCell>{file.parameter_name}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <FileIcon sx={{ mr: 1, fontSize: 20 }} />
                          {file.filename}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {file.size > 0 ? formatFileSize(file.size) : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {file.content_type || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Download Result">
                          <IconButton
                            size="small"
                            onClick={() => handleDownload(file)}
                            color="primary"
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* No Files Message */}
      {results.input_files.length === 0 && results.output_files.length === 0 && (
        <Alert severity="info">
          No input or output files available for this execution.
        </Alert>
      )}
    </Box>
  );
};

export default TaskResults;
