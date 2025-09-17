import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Chip,
  Button,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  CardActions,
} from '@mui/material';
import {
  TrendingUp,
  Assignment,
  CheckCircle,
  Schedule,
  Error,
  PlayArrow,
  Analytics,
  Visibility,
  Build,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

// Types for API responses
interface DashboardStats {
  totalJobs: number;
  activeJobs: number;
  completedJobs: number;
  failedJobs: number;
}

interface RecentJob {
  id: string;
  name: string;
  status: 'SUCCEEDED' | 'FAILED' | 'RUNNING' | 'PENDING';
  runtime?: string;
  createdAt: string;
}

// Mock API functions (replace with actual API calls)
const fetchDashboardStats = async (): Promise<DashboardStats> => {
  // Mock data - replace with actual API call
  return {
    totalJobs: 152,
    activeJobs: 8,
    completedJobs: 144,
    failedJobs: 3,
  };
};

const fetchRecentJobs = async (): Promise<RecentJob[]> => {
  // Mock data - replace with actual API call
  return [
    { id: '1', name: 'AutoDock Vina - Protein Complex A', status: 'SUCCEEDED', runtime: '2h 34m', createdAt: '2025-09-10T10:30:00Z' },
    { id: '2', name: 'AutoDock 4 - Drug Screening', status: 'RUNNING', runtime: '1h 12m', createdAt: '2025-09-10T11:45:00Z' },
    { id: '3', name: 'Pipeline - Lead Optimization', status: 'PENDING', createdAt: '2025-09-10T12:15:00Z' },
    { id: '4', name: 'AutoDock Vina - Conformational Search', status: 'SUCCEEDED', runtime: '45m', createdAt: '2025-09-10T09:20:00Z' },
  ];
};

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  // TanStack Query for data fetching with proper error handling
  const { data: stats, error: statsError, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: fetchDashboardStats,
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 3,
  });

  const { data: recentJobs, error: jobsError, isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs', 'recent'],
    queryFn: fetchRecentJobs,
    refetchInterval: 15000, // Refresh every 15 seconds
    retry: 3,
  });

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'info' => {
    switch (status) {
      case 'SUCCEEDED': return 'success';
      case 'FAILED': return 'error';
      case 'RUNNING': return 'info';
      case 'PENDING': return 'warning';
      default: return 'info';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCEEDED': return <CheckCircle />;
      case 'FAILED': return <Error />;
      case 'RUNNING': return <PlayArrow />;
      case 'PENDING': return <Schedule />;
      default: return <Schedule />;
    }
  };

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'design-pipeline':
        navigate('/pipelines');
        break;
      case 'start-job':
        navigate('/tasks');
        break;
      case 'view-results':
        navigate('/jobs');
        break;
      default:
        break;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Dashboard
      </Typography>

      {/* Error notifications banner */}
      {(statsError || jobsError) && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load dashboard data. Please check your connection and try again.
        </Alert>
      )}

      {/* Main action cards - exactly as shown in specification */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', cursor: 'pointer' }} onClick={() => handleQuickAction('design-pipeline')}>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <Build sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Design Pipeline
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Create and configure molecular docking workflows
              </Typography>
            </CardContent>
            <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
              <Button variant="contained" startIcon={<Build />}>
                Get Started
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', cursor: 'pointer' }} onClick={() => handleQuickAction('start-job')}>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <PlayArrow sx={{ fontSize: 48, color: 'secondary.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Start Job
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Execute molecular docking tasks immediately
              </Typography>
            </CardContent>
            <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
              <Button variant="contained" color="secondary" startIcon={<PlayArrow />}>
                Execute Now
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', cursor: 'pointer' }} onClick={() => handleQuickAction('view-results')}>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <Analytics sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                View Results
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analyze completed docking experiments
              </Typography>
            </CardContent>
            <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
              <Button variant="contained" color="success" startIcon={<Visibility />}>
                Browse Results
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Assignment sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" color="textSecondary">
                  Total Jobs
                </Typography>
              </Box>
              {statsLoading ? (
                <LinearProgress />
              ) : (
                <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  {stats?.totalJobs || 0}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PlayArrow sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6" color="textSecondary">
                  Active Jobs
                </Typography>
              </Box>
              {statsLoading ? (
                <LinearProgress />
              ) : (
                <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
                  {stats?.activeJobs || 0}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CheckCircle sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6" color="textSecondary">
                  Completed
                </Typography>
              </Box>
              {statsLoading ? (
                <LinearProgress />
              ) : (
                <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                  {stats?.completedJobs || 0}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Error sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6" color="textSecondary">
                  Failed Jobs
                </Typography>
              </Box>
              {statsLoading ? (
                <LinearProgress />
              ) : (
                <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'error.main' }}>
                  {stats?.failedJobs || 0}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <TrendingUp sx={{ mr: 1 }} />
          Recent Activity
        </Typography>

        {jobsLoading ? (
          <LinearProgress />
        ) : recentJobs && recentJobs.length > 0 ? (
          <List>
            {recentJobs.map((job) => (
              <ListItem key={job.id} divider>
                <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                  {getStatusIcon(job.status)}
                </Box>
                <ListItemText
                  primary={job.name}
                  secondary={`${new Date(job.createdAt).toLocaleString()}${job.runtime ? ` • Runtime: ${job.runtime}` : ''}`}
                />
                <Chip
                  label={job.status}
                  color={getStatusColor(job.status)}
                  size="small"
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography color="text.secondary">
            No recent activity. Start your first molecular docking job to see results here.
          </Typography>
        )}
      </Paper>
    </Box>
  );
};
