import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Stepper,
  Step,
  StepLabel,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  CloudUpload,
  PlayArrow,
  CheckCircle,
  ExpandMore,
  ViewInAr,
  FileUpload,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useLocation } from 'react-router-dom';

// 3D molecular viewer component (would use 3Dmol.js)
interface MolecularViewerProps {
  pdbData?: string;
  searchSpace?: {
    center_x: number;
    center_y: number;
    center_z: number;
    size_x: number;
    size_y: number;
    size_z: number;
    autoDetect: boolean;
  };
}

const MolecularViewer: React.FC<MolecularViewerProps> = ({ pdbData, searchSpace }) => {
  const viewerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 3Dmol.js integration would go here
    if (viewerRef.current && pdbData) {
      // Initialize 3Dmol viewer
      console.log('3D Viewer would be initialized here with:', pdbData);
    }
  }, [pdbData]);

  return (
    <Box
      ref={viewerRef}
      sx={{
        width: '100%',
        height: 400,
        border: '1px solid #ddd',
        borderRadius: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f8f9fa',
      }}
    >
      <Box sx={{ textAlign: 'center' }}>
        <ViewInAr sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" color="primary">
          3D Molecular Viewer
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Upload a PDB file to visualize structure
        </Typography>
        {searchSpace && (
          <Chip label="Search space configured" color="success" sx={{ mt: 1 }} />
        )}
      </Box>
    </Box>
  );
};

// Form validation schemas
const fileUploadSchema = z.object({
  receptorFile: z.any().refine((file) => file && file.length > 0, 'Receptor file is required'),
  ligandFile: z.any().refine((file) => file && file.length > 0, 'Ligand file is required'),
  configFile: z.any().optional(),
});

const searchSpaceSchema = z.object({
  center_x: z.number().min(-1000).max(1000),
  center_y: z.number().min(-1000).max(1000),
  center_z: z.number().min(-1000).max(1000),
  size_x: z.number().min(1).max(100),
  size_y: z.number().min(1).max(100),
  size_z: z.number().min(1).max(100),
  autoDetect: z.boolean(),
});

const parametersSchema = z.object({
  exhaustiveness: z.number().min(1).max(32).default(8),
  num_modes: z.number().min(1).max(20).default(9),
  energy_range: z.number().min(1).max(10).default(3),
  seed: z.number().optional(),
  cpu: z.number().min(1).max(64).default(1),
});

const jobConfigSchema = z.object({
  jobName: z.string().min(1, 'Job name is required'),
  description: z.string().optional(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  notifications: z.boolean().default(true),
});

const steps = [
  'File Upload',
  'Search Space',
  'Parameters',
  'Job Configuration',
  'Review & Submit'
];

export const ExecuteTasks: React.FC = () => {
  const location = useLocation();
  const selectedTemplate = location.state?.selectedTemplate;

  const [activeStep, setActiveStep] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState<{[key: string]: File}>({});
  const [pdbData, setPdbData] = useState<string>('');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form instances for each step
  const fileForm = useForm({
    resolver: zodResolver(fileUploadSchema),
  });

  const searchSpaceForm = useForm({
    resolver: zodResolver(searchSpaceSchema),
    defaultValues: {
      center_x: 0,
      center_y: 0,
      center_z: 0,
      size_x: 20,
      size_y: 20,
      size_z: 20,
      autoDetect: false,
    }
  });

  const parametersForm = useForm({
    resolver: zodResolver(parametersSchema),
    defaultValues: {
      exhaustiveness: 8,
      num_modes: 9,
      energy_range: 3,
      cpu: 1,
    }
  });

  const jobConfigForm = useForm({
    resolver: zodResolver(jobConfigSchema),
    defaultValues: {
      jobName: selectedTemplate ? `${selectedTemplate.name} - ${new Date().toISOString().split('T')[0]}` : '',
      priority: 'medium' as const,
      notifications: true,
    }
  });

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>, fileType: string) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFiles(prev => ({ ...prev, [fileType]: file }));

      // If it's a PDB file, read for preview
      if (fileType === 'receptorFile' && file.name.endsWith('.pdb')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setPdbData(e.target?.result as string);
        };
        reader.readAsText(file);
      }
    }
  };

  const handleNext = async () => {
    let isValid = false;

    switch (activeStep) {
      case 0:
        isValid = await fileForm.trigger();
        break;
      case 1:
        isValid = await searchSpaceForm.trigger();
        break;
      case 2:
        isValid = await parametersForm.trigger();
        break;
      case 3:
        isValid = await jobConfigForm.trigger();
        break;
      default:
        isValid = true;
    }

    if (isValid) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);

    // Collect all form data
    const allData = {
      files: uploadedFiles,
      searchSpace: searchSpaceForm.getValues(),
      parameters: parametersForm.getValues(),
      jobConfig: jobConfigForm.getValues(),
      template: selectedTemplate,
    };

    try {
      // Submit to API (mock)
      console.log('Submitting job with data:', allData);
      await new Promise(resolve => setTimeout(resolve, 2000)); // Mock API call

      // Navigate to job manager or show success
      alert('Job submitted successfully!');
    } catch (error) {
      console.error('Job submission failed:', error);
      alert('Job submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Upload Required Files
                  </Typography>

                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Receptor File (PDB/PDBQT) *
                    </Typography>
                    <Button
                      variant="outlined"
                      component="label"
                      startIcon={<CloudUpload />}
                      fullWidth
                      sx={{ mb: 1 }}
                    >
                      Choose Receptor File
                      <input
                        type="file"
                        hidden
                        accept=".pdb,.pdbqt"
                        onChange={(e) => handleFileUpload(e, 'receptorFile')}
                      />
                    </Button>
                    {uploadedFiles.receptorFile && (
                      <Chip
                        label={uploadedFiles.receptorFile.name}
                        color="success"
                        size="small"
                      />
                    )}
                  </Box>

                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Ligand File (PDB/PDBQT/SDF) *
                    </Typography>
                    <Button
                      variant="outlined"
                      component="label"
                      startIcon={<CloudUpload />}
                      fullWidth
                      sx={{ mb: 1 }}
                    >
                      Choose Ligand File
                      <input
                        type="file"
                        hidden
                        accept=".pdb,.pdbqt,.sdf"
                        onChange={(e) => handleFileUpload(e, 'ligandFile')}
                      />
                    </Button>
                    {uploadedFiles.ligandFile && (
                      <Chip
                        label={uploadedFiles.ligandFile.name}
                        color="success"
                        size="small"
                      />
                    )}
                  </Box>

                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Configuration File (Optional)
                    </Typography>
                    <Button
                      variant="outlined"
                      component="label"
                      startIcon={<CloudUpload />}
                      fullWidth
                      sx={{ mb: 1 }}
                    >
                      Choose Config File
                      <input
                        type="file"
                        hidden
                        accept=".txt,.conf,.cfg"
                        onChange={(e) => handleFileUpload(e, 'configFile')}
                      />
                    </Button>
                    {uploadedFiles.configFile && (
                      <Chip
                        label={uploadedFiles.configFile.name}
                        color="success"
                        size="small"
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    File Requirements
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Receptor Structure"
                        secondary="PDB or PDBQT format"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Ligand Structure"
                        secondary="PDB, PDBQT, or SDF format"
                      />
                    </ListItem>
                  </List>

                  <Alert severity="info" sx={{ mt: 2 }}>
                    Make sure your files are properly prepared with correct atomic coordinates and bond information.
                  </Alert>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        );

      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Define Search Space
                  </Typography>

                  <FormControlLabel
                    control={
                      <Controller
                        name="autoDetect"
                        control={searchSpaceForm.control}
                        render={({ field }) => (
                          <Switch {...field} checked={field.value} />
                        )}
                      />
                    }
                    label="Auto-detect binding site"
                    sx={{ mb: 3 }}
                  />

                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom>
                        Search Center Coordinates (Å)
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Controller
                        name="center_x"
                        control={searchSpaceForm.control}
                        render={({ field, fieldState }) => (
                          <TextField
                            {...field}
                            label="Center X"
                            type="number"
                            fullWidth
                            error={!!fieldState.error}
                            helperText={fieldState.error?.message}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <Controller
                        name="center_y"
                        control={searchSpaceForm.control}
                        render={({ field, fieldState }) => (
                          <TextField
                            {...field}
                            label="Center Y"
                            type="number"
                            fullWidth
                            error={!!fieldState.error}
                            helperText={fieldState.error?.message}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <Controller
                        name="center_z"
                        control={searchSpaceForm.control}
                        render={({ field, fieldState }) => (
                          <TextField
                            {...field}
                            label="Center Z"
                            type="number"
                            fullWidth
                            error={!!fieldState.error}
                            helperText={fieldState.error?.message}
                          />
                        )}
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                        Search Space Dimensions (Å)
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Controller
                        name="size_x"
                        control={searchSpaceForm.control}
                        render={({ field, fieldState }) => (
                          <TextField
                            {...field}
                            label="Size X"
                            type="number"
                            fullWidth
                            error={!!fieldState.error}
                            helperText={fieldState.error?.message}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <Controller
                        name="size_y"
                        control={searchSpaceForm.control}
                        render={({ field, fieldState }) => (
                          <TextField
                            {...field}
                            label="Size Y"
                            type="number"
                            fullWidth
                            error={!!fieldState.error}
                            helperText={fieldState.error?.message}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <Controller
                        name="size_z"
                        control={searchSpaceForm.control}
                        render={({ field, fieldState }) => (
                          <TextField
                            {...field}
                            label="Size Z"
                            type="number"
                            fullWidth
                            error={!!fieldState.error}
                            helperText={fieldState.error?.message}
                          />
                        )}
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    3D Structure Preview
                  </Typography>
                  <MolecularViewer
                    pdbData={pdbData}
                    searchSpace={searchSpaceForm.getValues()}
                  />
                  <Button
                    variant="outlined"
                    startIcon={<ViewInAr />}
                    onClick={() => setPreviewOpen(true)}
                    fullWidth
                    sx={{ mt: 2 }}
                  >
                    Full Screen Preview
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        );

      case 2:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Docking Parameters
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="exhaustiveness"
                    control={parametersForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="Exhaustiveness"
                        type="number"
                        fullWidth
                        helperText={fieldState.error?.message || "Higher values = more thorough search"}
                        error={!!fieldState.error}
                        sx={{ mb: 2 }}
                      />
                    )}
                  />

                  <Controller
                    name="num_modes"
                    control={parametersForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="Number of Modes"
                        type="number"
                        fullWidth
                        helperText={fieldState.error?.message || "Number of binding modes to generate"}
                        error={!!fieldState.error}
                        sx={{ mb: 2 }}
                      />
                    )}
                  />

                  <Controller
                    name="energy_range"
                    control={parametersForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="Energy Range (kcal/mol)"
                        type="number"
                        fullWidth
                        helperText={fieldState.error?.message || "Maximum energy difference between modes"}
                        error={!!fieldState.error}
                        sx={{ mb: 2 }}
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Controller
                    name="cpu"
                    control={parametersForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="CPU Cores"
                        type="number"
                        fullWidth
                        helperText={fieldState.error?.message || "Number of CPU cores to use"}
                        error={!!fieldState.error}
                        sx={{ mb: 2 }}
                      />
                    )}
                  />

                  <Controller
                    name="seed"
                    control={parametersForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="Random Seed (Optional)"
                        type="number"
                        fullWidth
                        helperText={fieldState.error?.message || "For reproducible results"}
                        error={!!fieldState.error}
                        sx={{ mb: 2 }}
                      />
                    )}
                  />

                  <Alert severity="info">
                    <Typography variant="body2">
                      <strong>Estimated Runtime:</strong> 15-45 minutes based on current parameters
                    </Typography>
                  </Alert>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        );

      case 3:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Job Configuration
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="jobName"
                    control={jobConfigForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="Job Name"
                        fullWidth
                        error={!!fieldState.error}
                        helperText={fieldState.error?.message}
                        sx={{ mb: 2 }}
                      />
                    )}
                  />

                  <Controller
                    name="description"
                    control={jobConfigForm.control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Description (Optional)"
                        multiline
                        rows={3}
                        fullWidth
                        sx={{ mb: 2 }}
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Controller
                    name="priority"
                    control={jobConfigForm.control}
                    render={({ field }) => (
                      <FormControl fullWidth sx={{ mb: 2 }}>
                        <InputLabel>Priority</InputLabel>
                        <Select {...field} label="Priority">
                          <MenuItem value="low">Low</MenuItem>
                          <MenuItem value="medium">Medium</MenuItem>
                          <MenuItem value="high">High</MenuItem>
                        </Select>
                      </FormControl>
                    )}
                  />

                  <FormControlLabel
                    control={
                      <Controller
                        name="notifications"
                        control={jobConfigForm.control}
                        render={({ field }) => (
                          <Switch {...field} checked={field.value} />
                        )}
                      />
                    }
                    label="Email notifications"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        );

      case 4:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review & Submit
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="subtitle1">Files</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {Object.entries(uploadedFiles).map(([key, file]) => (
                        <ListItem key={key}>
                          <ListItemIcon>
                            <FileUpload />
                          </ListItemIcon>
                          <ListItemText primary={file.name} secondary={key} />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="subtitle1">Search Space</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {JSON.stringify(searchSpaceForm.getValues(), null, 2)}
                  </AccordionDetails>
                </Accordion>
              </Grid>

              <Grid item xs={12} md={6}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="subtitle1">Parameters</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {JSON.stringify(parametersForm.getValues(), null, 2)}
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="subtitle1">Job Configuration</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {JSON.stringify(jobConfigForm.getValues(), null, 2)}
                  </AccordionDetails>
                </Accordion>
              </Grid>
            </Grid>
          </Box>
        );

      default:
        return 'Unknown step';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Execute Task
        {selectedTemplate && (
          <Chip
            label={selectedTemplate.name}
            color="primary"
            sx={{ ml: 2 }}
          />
        )}
      </Typography>

      <Paper sx={{ p: 3 }}>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {renderStepContent(activeStep)}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            disabled={activeStep === 0}
            onClick={handleBack}
          >
            Back
          </Button>

          <Box sx={{ display: 'flex', gap: 2 }}>
            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={submitting}
                startIcon={submitting ? undefined : <PlayArrow />}
              >
                {submitting ? (
                  <>
                    <LinearProgress sx={{ width: 100, mr: 1 }} />
                    Submitting...
                  </>
                ) : (
                  'Submit Job'
                )}
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleNext}
              >
                Next
              </Button>
            )}
          </Box>
        </Box>
      </Paper>

      {/* 3D Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>3D Structure Preview</DialogTitle>
        <DialogContent>
          <Box sx={{ height: 600 }}>
            <MolecularViewer
              pdbData={pdbData}
              searchSpace={searchSpaceForm.getValues()}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
