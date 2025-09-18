/**
 * Task Library Page
 *
 * Displays and manages molecular analysis pipelines and tasks.
 * Allows users to view, create, edit, and delete analysis pipelines.
 */

import React, { useState } from 'react';
import {
  Box,
  Grid,
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
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Type definitions for task library
interface TaskTemplate {
  id: string;
  name: string;
  description: string;
  category: 'autodock_vina' | 'autodock4' | 'schrodinger' | 'custom';
  version: string;
  complexity: 'beginner' | 'intermediate' | 'advanced';
  estimatedRuntime: string;
  cpuRequirement: 'low' | 'medium' | 'high';
  memoryRequirement: 'low' | 'medium' | 'high';
  requiredFiles: string[];
  parameters: TaskParameter[];
  compatibility: string[];
  tags: string[];
  documentation?: string;
  examples?: string[];
  isBuiltIn?: boolean;
}

interface TaskParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'file' | 'select';
  required: boolean;
  default?: string | number | boolean | undefined;
  description: string;
  options?: string[];
}

// Mock task library data
const taskTemplates: TaskTemplate[] = [
  {
    id: 'autodock_vina_basic',
    name: 'AutoDock Vina',
    description:
      'Fast molecular docking using AutoDock Vina algorithm for protein-ligand binding prediction',
    category: 'autodock_vina',
    version: '1.2.0',
    complexity: 'beginner',
    estimatedRuntime: '1-10 minutes',
    cpuRequirement: 'high',
    memoryRequirement: 'medium',
    requiredFiles: ['receptor.pdbqt', 'ligand.pdbqt'],
    isBuiltIn: true,
    parameters: [
      {
        name: 'center_x',
        type: 'number',
        required: true,
        default: 0,
        description: 'X coordinate of search space center',
      },
      {
        name: 'center_y',
        type: 'number',
        required: true,
        default: 0,
        description: 'Y coordinate of search space center',
      },
      {
        name: 'center_z',
        type: 'number',
        required: true,
        default: 0,
        description: 'Z coordinate of search space center',
      },
      {
        name: 'size_x',
        type: 'number',
        required: true,
        default: 20,
        description: 'Search space size in X dimension',
      },
      {
        name: 'size_y',
        type: 'number',
        required: true,
        default: 20,
        description: 'Search space size in Y dimension',
      },
      {
        name: 'size_z',
        type: 'number',
        required: true,
        default: 20,
        description: 'Search space size in Z dimension',
      },
      {
        name: 'exhaustiveness',
        type: 'number',
        required: false,
        default: 8,
        description: 'Exhaustiveness of search',
      },
    ],
    compatibility: ['linux', 'macos', 'windows'],
    tags: ['docking', 'vina', 'basic', 'tutorial'],
    documentation: 'Standard AutoDock Vina workflow for molecular docking',
  },
  {
    id: 'autodock_vina_advanced',
    name: 'AutoDock Vina - Advanced',
    description: 'Advanced AutoDock Vina docking with custom parameters and multiple conformations',
    category: 'autodock_vina',
    version: '1.2.0',
    complexity: 'advanced',
    estimatedRuntime: '1-4 hours',
    cpuRequirement: 'high',
    memoryRequirement: 'high',
    requiredFiles: ['receptor.pdbqt', 'ligand.pdbqt', 'config.txt'],
    isBuiltIn: true,
    parameters: [
      {
        name: 'num_modes',
        type: 'number',
        required: false,
        default: 9,
        description: 'Number of binding modes to generate',
      },
      {
        name: 'energy_range',
        type: 'number',
        required: false,
        default: 3,
        description: 'Maximum energy difference between best and worst mode',
      },
      {
        name: 'seed',
        type: 'number',
        required: false,
        description: 'Random seed for reproducible results',
      },
      {
        name: 'cpu',
        type: 'number',
        required: false,
        default: 1,
        description: 'Number of CPUs to use',
      },
    ],
    compatibility: ['linux', 'macos'],
    tags: ['docking', 'vina', 'advanced', 'multi-conformation'],
    documentation: 'Advanced AutoDock Vina with detailed parameter control',
  },
  {
    id: 'autodock4_basic',
    name: 'AutoDock 4',
    description:
      'Classic molecular docking using AutoDock 4 algorithm for protein-ligand binding prediction',
    category: 'autodock4',
    version: '4.2.6',
    complexity: 'intermediate',
    estimatedRuntime: '5-30 minutes',
    cpuRequirement: 'medium',
    memoryRequirement: 'low',
    requiredFiles: ['receptor.pdbqt', 'ligand.pdbqt', 'grid.gpf'],
    isBuiltIn: true,
    parameters: [
      {
        name: 'ga_runs',
        type: 'number',
        required: false,
        default: 10,
        description: 'Number of genetic algorithm runs',
      },
      {
        name: 'ga_pop_size',
        type: 'number',
        required: false,
        default: 150,
        description: 'Population size for genetic algorithm',
      },
      {
        name: 'ga_num_evals',
        type: 'number',
        required: false,
        default: 2500000,
        description: 'Maximum number of energy evaluations',
      },
    ],
    compatibility: ['linux', 'macos'],
    tags: ['docking', 'autodock4', 'genetic-algorithm', 'protein-ligand'],
    documentation: 'Traditional AutoDock 4 workflow with genetic algorithm optimization',
  },
  {
    id: 'virtual_screening',
    name: 'Virtual Screening Pipeline',
    description: 'High-throughput virtual screening of compound libraries',
    category: 'custom',
    version: '2.1.0',
    complexity: 'advanced',
    estimatedRuntime: '12-48 hours',
    cpuRequirement: 'high',
    memoryRequirement: 'high',
    requiredFiles: ['receptor.pdbqt', 'ligand_library.sdf'],
    isBuiltIn: false,
    parameters: [
      {
        name: 'library_size',
        type: 'number',
        required: true,
        description: 'Number of compounds in library',
      },
      {
        name: 'scoring_function',
        type: 'select',
        required: true,
        options: ['vina', 'autodock4', 'glide'],
        description: 'Scoring function to use',
      },
      {
        name: 'filter_druglike',
        type: 'boolean',
        required: false,
        default: true,
        description: 'Apply drug-like filters',
      },
    ],
    compatibility: ['linux'],
    tags: ['screening', 'high-throughput', 'pipeline', 'drug-discovery'],
    documentation: 'Automated virtual screening of large compound libraries',
  },
];

export const TaskLibrary: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [complexityFilter, setComplexityFilter] = useState<string>('all');
  const [cpuFilter, setCpuFilter] = useState<string>('all');
  const [memoryFilter, setMemoryFilter] = useState<string>('all');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [selectedTask, setSelectedTask] = useState<TaskTemplate | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Filter tasks based on search and filters
  const filteredTasks = taskTemplates.filter((task) => {
    const matchesSearch =
      task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.tags.some((tag) => tag.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesCategory = categoryFilter === 'all' || task.category === categoryFilter;
    const matchesComplexity = complexityFilter === 'all' || task.complexity === complexityFilter;
    const matchesCpu = cpuFilter === 'all' || task.cpuRequirement === cpuFilter;
    const matchesMemory = memoryFilter === 'all' || task.memoryRequirement === memoryFilter;

    return matchesSearch && matchesCategory && matchesComplexity && matchesCpu && matchesMemory;
  });

  const getComplexityColor = (complexity: string): 'success' | 'warning' | 'error' => {
    switch (complexity) {
      case 'beginner':
        return 'success';
      case 'intermediate':
        return 'warning';
      case 'advanced':
        return 'error';
      default:
        return 'success';
    }
  };

  const getRequirementColor = (requirement: string): 'success' | 'warning' | 'error' => {
    switch (requirement) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      default:
        return 'success';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'autodock_vina':
        return <Science />;
      case 'autodock4':
        return <Settings />;
      case 'schrodinger':
        return <Speed />;
      case 'custom':
        return <Category />;
      default:
        return <Science />;
    }
  };

  const handleExecuteTask = (task: TaskTemplate) => {
    navigate('/execute-tasks', { state: { selectedTemplate: task } });
  };

  const handleViewDetails = (task: TaskTemplate) => {
    setSelectedTask(task);
    setDetailsOpen(true);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Task Library
      </Typography>

      {/* Search and Filters */}
      <Box sx={{ mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search tasks, descriptions, or tags..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="all">All Categories</MenuItem>
                <MenuItem value="autodock_vina">AutoDock Vina</MenuItem>
                <MenuItem value="autodock4">AutoDock 4</MenuItem>
                <MenuItem value="schrodinger">Schrödinger</MenuItem>
                <MenuItem value="custom">Custom Pipelines</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Complexity</InputLabel>
              <Select
                value={complexityFilter}
                label="Complexity"
                onChange={(e) => setComplexityFilter(e.target.value)}
              >
                <MenuItem value="all">All Levels</MenuItem>
                <MenuItem value="beginner">Beginner</MenuItem>
                <MenuItem value="intermediate">Intermediate</MenuItem>
                <MenuItem value="advanced">Advanced</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Advanced Filters */}
        <Accordion
          sx={{ mt: 2 }}
          expanded={showAdvancedFilters}
          onChange={() => setShowAdvancedFilters(!showAdvancedFilters)}
        >
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
              Advanced Filters
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>CPU Requirement</InputLabel>
                  <Select
                    value={cpuFilter}
                    label="CPU Requirement"
                    onChange={(e) => setCpuFilter(e.target.value)}
                  >
                    <MenuItem value="all">All CPU Requirements</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Memory Requirement</InputLabel>
                  <Select
                    value={memoryFilter}
                    label="Memory Requirement"
                    onChange={(e) => setMemoryFilter(e.target.value)}
                  >
                    <MenuItem value="all">All Memory Requirements</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Box>

      {/* Task Cards */}
      <Grid container spacing={3}>
        {filteredTasks.map((task) => (
          <Grid item xs={12} md={6} lg={4} key={task.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
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
                  <Chip
                    label={task.complexity}
                    color={getComplexityColor(task.complexity)}
                    size="small"
                    sx={{ mr: 1, mb: 1 }}
                  />
                  {task.isBuiltIn && (
                    <Chip label="Built-in" variant="outlined" size="small" sx={{ mr: 1, mb: 1 }} />
                  )}
                  <Chip
                    label={task.category.replace('_', ' ')}
                    variant="outlined"
                    size="small"
                    sx={{ mr: 1, mb: 1 }}
                  />
                  <Chip label={`v${task.version}`} variant="outlined" size="small" sx={{ mb: 1 }} />
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Schedule sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary">
                    Duration: {task.estimatedRuntime}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Speed sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                    CPU: {task.cpuRequirement}
                  </Typography>
                  <Chip
                    label={task.cpuRequirement}
                    color={getRequirementColor(task.cpuRequirement)}
                    size="small"
                    variant="outlined"
                  />
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Memory sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                    Memory: {task.memoryRequirement}
                  </Typography>
                  <Chip
                    label={task.memoryRequirement}
                    color={getRequirementColor(task.memoryRequirement)}
                    size="small"
                    variant="outlined"
                  />
                </Box>

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
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
                    <Chip
                      label={`+${task.tags.length - 3}`}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }}
                    />
                  )}
                </Box>
              </CardContent>

              <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
                <Button size="small" startIcon={<Info />} onClick={() => handleViewDetails(task)}>
                  Details
                </Button>
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<PlayArrow />}
                  onClick={() => handleExecuteTask(task)}
                >
                  Execute
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {filteredTasks.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No tasks found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your search terms or filters
          </Typography>
        </Box>
      )}

      {/* Task Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        {selectedTask && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {getCategoryIcon(selectedTask.category)}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {selectedTask.name}
                </Typography>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" paragraph>
                {selectedTask.description}
              </Typography>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Requirements
              </Typography>
              <List dense>
                {selectedTask.requiredFiles.map((file, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckCircle color="success" />
                    </ListItemIcon>
                    <ListItemText primary={file} />
                  </ListItem>
                ))}
              </List>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Parameters
              </Typography>
              {selectedTask.parameters.map((param) => (
                <Accordion key={param.name}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <Typography sx={{ fontWeight: 500, mr: 1 }}>{param.name}</Typography>
                      {param.required && <Chip label="Required" color="error" size="small" />}
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                        {param.type}
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" paragraph>
                      {param.description}
                    </Typography>
                    {param.default !== undefined && (
                      <Typography variant="body2" color="text.secondary">
                        Default: {String(param.default)}
                      </Typography>
                    )}
                    {param.options && (
                      <Typography variant="body2" color="text.secondary">
                        Options: {param.options.join(', ')}
                      </Typography>
                    )}
                  </AccordionDetails>
                </Accordion>
              ))}

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Compatibility
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                {selectedTask.compatibility.map((platform) => (
                  <Chip key={platform} label={platform} variant="outlined" size="small" />
                ))}
              </Box>

              <Typography variant="h6" gutterBottom>
                Tags
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {selectedTask.tags.map((tag) => (
                  <Chip key={tag} label={tag} variant="outlined" size="small" />
                ))}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailsOpen(false)}>Close</Button>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={() => {
                  setDetailsOpen(false);
                  handleExecuteTask(selectedTask);
                }}
              >
                Execute Task
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export type Pipeline = {
  pipeline_id: string;
  name: string;
  description?: string;
  engine: 'vina' | 'smina' | 'gnina';
  parameters: Record<string, unknown>;
  is_active: boolean;
  org_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
};
