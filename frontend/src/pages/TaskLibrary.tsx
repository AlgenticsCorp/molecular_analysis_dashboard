/**
 * Task Library Page
 *
 * Displays and manages molecular analysis pipelines and tasks.
 * Allows users to view, create, edit, and delete analysis pipelines.
 * Now uses TaskService with API and fallback capabilities.
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
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
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Skeleton,
  Tooltip,
  LinearProgress,
  Grid,
} from '@mui/material';
import {
  Search,
  Science,
  PlayArrow,
  Info,
  Category,
  Schedule,
  Memory,
  Settings,
  ExpandMore,
  CheckCircle,
  Speed,
  Refresh,
  CloudOff,
  Cloud,
  Storage,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Import TaskService types and hooks
import { TaskTemplate, TaskListParams } from '../types/tasks';
import { useTasks, useTaskCategories, useTaskServiceHealth } from '../hooks/useTasks';
import { useFeatureFlags } from '../services/featureFlags';

export const TaskLibrary: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedTask, setSelectedTask] = useState<TaskTemplate | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Feature flags and service hooks
  const featureFlags = useFeatureFlags();
  const health = useTaskServiceHealth();

  // Task data hooks - memoize params to prevent unnecessary re-renders
  const taskParams: TaskListParams = useMemo(() => {
    const params: TaskListParams = {};
    if (searchTerm) params.search = searchTerm;
    if (categoryFilter !== 'all') params.category = categoryFilter;
    return params;
  }, [searchTerm, categoryFilter]);

  const {
    tasks: taskTemplates,
    loading: tasksLoading,
    error: tasksError,
    source: tasksSource,
    refetch: refetchTasks,
    isStale,
  } = useTasks(taskParams, false); // Disable auto-refresh to prevent performance issues

  const { categories, loading: categoriesLoading, error: categoriesError } = useTaskCategories();

  // Helper functions
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'docking':
        return <Science />;
      case 'preparation':
        return <Settings />;
      case 'analysis':
        return <Speed />;
      default:
        return <Category />;
    }
  };

  const getSourceIcon = () => {
    switch (tasksSource) {
      case 'api':
        return <Cloud fontSize="small" />;
      case 'cache':
        return <Storage fontSize="small" />;
      case 'fallback':
        return <CloudOff fontSize="small" />;
      default:
        return null;
    }
  };

  const handleTaskSelect = (task: TaskTemplate) => {
    setSelectedTask(task);
    setDetailsOpen(true);
  };

  const handleTaskRun = (task: TaskTemplate) => {
    navigate(`/jobs/create?template=${task.id}`);
  };

  const handleRefresh = () => {
    refetchTasks();
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header with Status Indicator */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Task Library
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Data Source Indicator */}
          <Tooltip title={`Data source: ${tasksSource || 'loading'}`}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {getSourceIcon()}
              <Typography variant="body2" color="text.secondary">
                {tasksSource?.toUpperCase()}
              </Typography>
            </Box>
          </Tooltip>

          {/* Feature Flag Status */}
          {featureFlags.isDebugMode() && (
            <Chip
              label={featureFlags.shouldUseApiTasks() ? 'API ON' : 'API OFF'}
              color={featureFlags.shouldUseApiTasks() ? 'success' : 'warning'}
              size="small"
            />
          )}

          {/* Health Status */}
          <Tooltip title={`API ${health.available ? 'available' : 'unavailable'}`}>
            <Chip
              icon={health.available ? <CheckCircle /> : <CloudOff />}
              label={health.available ? 'Healthy' : 'Offline'}
              color={health.available ? 'success' : 'error'}
              size="small"
            />
          </Tooltip>

          {/* Refresh Button */}
          <Button
            variant="outlined"
            onClick={handleRefresh}
            startIcon={<Refresh />}
            disabled={tasksLoading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Error Alerts */}
      {tasksError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load tasks: {tasksError}
        </Alert>
      )}

      {categoriesError && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Failed to load categories: {categoriesError}
        </Alert>
      )}

      {/* Stale Data Warning */}
      {isStale && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Data may be outdated. Click refresh to get the latest tasks.
        </Alert>
      )}

      {/* Loading Indicator */}
      {tasksLoading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Search and Filters */}
      <Box sx={{ mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search Tasks"
              variant="outlined"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              placeholder="Search by name, description, or tags..."
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
                disabled={categoriesLoading}
              >
                <MenuItem value="all">All Categories</MenuItem>
                {categories.map((category) => (
                  <MenuItem key={category} value={category}>
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <Typography variant="body2" color="text.secondary">
              {taskTemplates.length} task{taskTemplates.length !== 1 ? 's' : ''} found
            </Typography>
          </Grid>
        </Grid>
      </Box>

      {/* Task Cards */}
      <Grid container spacing={3}>
        {tasksLoading
          ? // Loading skeletons
            Array.from({ length: 6 }).map((_, index) => (
              <Grid item xs={12} md={6} lg={4} key={index}>
                <Card>
                  <CardContent>
                    <Skeleton variant="text" width="60%" height={32} />
                    <Skeleton variant="text" width="100%" height={20} />
                    <Skeleton variant="text" width="80%" height={20} />
                    <Skeleton variant="rectangular" width="100%" height={60} sx={{ mt: 2 }} />
                  </CardContent>
                </Card>
              </Grid>
            ))
          : taskTemplates.map((task) => (
              <Grid item xs={12} md={6} lg={4} key={task.id}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: (theme) => theme.shadows[8],
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      {getCategoryIcon(task.category)}
                      <Typography variant="h6" sx={{ ml: 1, fontWeight: 600 }}>
                        {task.name}
                      </Typography>
                    </Box>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {task.description}
                    </Typography>

                    <Box sx={{ mb: 2 }}>
                      <Chip label={task.category} size="small" sx={{ mr: 1, mb: 1 }} />
                      <Chip
                        label={`v${task.version}`}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 1, mb: 1 }}
                      />
                      <Chip label={task.engine} size="small" color="primary" sx={{ mb: 1 }} />
                    </Box>

                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                      {task.tags.slice(0, 3).map((tag) => (
                        <Chip
                          key={tag}
                          label={tag}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      ))}
                      {task.tags.length > 3 && (
                        <Typography variant="caption" color="text.secondary">
                          +{task.tags.length - 3} more
                        </Typography>
                      )}
                    </Box>

                    <Grid container spacing={1} sx={{ mb: 2 }}>
                      <Grid item xs={6}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Schedule sx={{ fontSize: 16, mr: 0.5 }} />
                          <Typography variant="caption">
                            ~{Math.round((task.execution_time_estimate || 300) / 60)}min
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Memory sx={{ fontSize: 16, mr: 0.5 }} />
                          <Typography variant="caption">
                            {task.resource_requirements?.memory_gb || 4}GB RAM
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>

                  <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                    <Button
                      size="small"
                      startIcon={<Info />}
                      onClick={() => handleTaskSelect(task)}
                    >
                      Details
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<PlayArrow />}
                      onClick={() => handleTaskRun(task)}
                    >
                      Run Task
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
      </Grid>

      {/* No Results */}
      {!tasksLoading && taskTemplates.length === 0 && (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 8,
          }}
        >
          <Science sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No tasks found
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Try adjusting your search terms or filters to find the tasks you're looking for.
          </Typography>
        </Box>
      )}

      {/* Task Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {selectedTask && getCategoryIcon(selectedTask.category)}
            <Typography variant="h6" sx={{ ml: 1 }}>
              {selectedTask?.name}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedTask && (
            <Box>
              <Typography variant="body1" paragraph>
                {selectedTask.description}
              </Typography>

              <Divider sx={{ my: 2 }} />

              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Category
                  </Typography>
                  <Typography variant="body2">{selectedTask.category}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Version
                  </Typography>
                  <Typography variant="body2">{selectedTask.version}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Engine
                  </Typography>
                  <Typography variant="body2">{selectedTask.engine}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Status
                  </Typography>
                  <Chip
                    label={selectedTask.status}
                    size="small"
                    color={selectedTask.status === 'active' ? 'success' : 'default'}
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Tags
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 3 }}>
                {selectedTask.tags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" variant="outlined" />
                ))}
              </Box>

              <Typography variant="subtitle2" gutterBottom>
                Parameters ({selectedTask.parameters.length})
              </Typography>
              <List dense>
                {selectedTask.parameters.slice(0, 5).map((param) => (
                  <ListItem key={param.name}>
                    <ListItemIcon>
                      <Settings fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={param.name}
                      secondary={
                        <Box>
                          <Typography variant="caption" component="div">
                            {param.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Type: {param.type} | Required: {param.required ? 'Yes' : 'No'}
                            {param.default !== undefined && ` | Default: ${param.default}`}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
                {selectedTask.parameters.length > 5 && (
                  <ListItem>
                    <ListItemText
                      primary={
                        <Typography variant="body2" color="text.secondary">
                          ... and {selectedTask.parameters.length - 5} more parameters
                        </Typography>
                      }
                    />
                  </ListItem>
                )}
              </List>

              {selectedTask.resource_requirements && (
                <Accordion sx={{ mt: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="subtitle2">Resource Requirements</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={4}>
                        <Typography variant="body2" gutterBottom>
                          CPU Cores
                        </Typography>
                        <Typography variant="h6">
                          {selectedTask.resource_requirements.cpu_cores}
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" gutterBottom>
                          Memory (GB)
                        </Typography>
                        <Typography variant="h6">
                          {selectedTask.resource_requirements.memory_gb}
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" gutterBottom>
                          Disk (GB)
                        </Typography>
                        <Typography variant="h6">
                          {selectedTask.resource_requirements.disk_gb}
                        </Typography>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={() => {
              if (selectedTask) {
                handleTaskRun(selectedTask);
                setDetailsOpen(false);
              }
            }}
          >
            Run Task
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaskLibrary;
