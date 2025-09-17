import React, { useState, useContext, createContext } from 'react';
import {
  Box,
  Grid,
  Typography,
  Button,
  TextField,
  FormControl,
  Select,
  MenuItem,
  Paper,
  Chip,
  FormHelperText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import { HelpOutline, ExpandMore, ArrowBack, ArrowForward, PlayArrow } from '@mui/icons-material';
import { useForm, Controller, Control, FieldError } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useLocation } from 'react-router-dom';

// Types
interface DockingParams {
  xSize: number;
  ySize: number;
  zSize: number;
  gaRuns: number;
  outputFormat: string;
  energyEvals?: number;
}

interface UploadedFiles {
  [key: string]: File;
}

interface WizardContextType {
  params: DockingParams | null;
  setParams: (params: DockingParams) => void;
  activeStep: number;
  setActiveStep: (step: number) => void;
  uploadedFiles: UploadedFiles;
  setUploadedFiles: (files: UploadedFiles) => void;
}

// Validation schema
const schema = z.object({
  xSize: z.number().min(1, 'X size must be at least 1'),
  ySize: z.number().min(1, 'Y size must be at least 1'),
  zSize: z.number().min(1, 'Z size must be at least 1'),
  gaRuns: z.number().min(1, 'GA runs must be at least 1'),
  outputFormat: z.string().min(1, 'Output format is required'),
  energyEvals: z.number().optional(),
});

type FormValues = z.infer<typeof schema>;

const defaultParams: FormValues = {
  xSize: 22.5,
  ySize: 22.5,
  zSize: 22.5,
  gaRuns: 10,
  outputFormat: 'pdbqt',
  energyEvals: 2500000,
};

// Context
const WizardContext = createContext<WizardContextType | undefined>(undefined);

const useWizard = () => {
  const context = useContext(WizardContext);
  if (!context) {
    throw new Error('useWizard must be used within a WizardProvider');
  }
  return context;
};

// Parameter Field Component
interface ParameterFieldProps {
  name: keyof FormValues;
  control: Control<FormValues>;
  label: string;
  tooltip: string;
  error?: FieldError;
}

const ParameterField: React.FC<ParameterFieldProps> = ({
  name,
  control,
  label,
  tooltip,
  error,
}) => (
  <Controller
    name={name}
    control={control}
    render={({ field }) => (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" component="label" sx={{ fontWeight: 500 }}>
            {label}
          </Typography>
          <Tooltip title={tooltip}>
            <IconButton size="small" sx={{ ml: 0.5, p: 0.25 }}>
              <HelpOutline sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
        </Box>
        <TextField
          {...field}
          type="number"
          fullWidth
          size="small"
          error={!!error}
          onChange={(e) => field.onChange(Number(e.target.value))}
        />
        <FormHelperText error={!!error}>{error?.message || tooltip}</FormHelperText>
      </Box>
    )}
  />
);

// Main Integrated Wizard Component
const IntegratedWizard: React.FC = () => {
  const navigate = useNavigate();
  const { params, setParams, activeStep, setActiveStep, uploadedFiles, setUploadedFiles } =
    useWizard();
  const [submitting, setSubmitting] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: params ?? defaultParams,
    mode: 'onBlur',
  });

  const handleNext = () => {
    setActiveStep(activeStep + 1);
  };

  const handleBack = () => {
    if (activeStep === 0) {
      navigate(-1);
    } else {
      setActiveStep(activeStep - 1);
    }
  };

  const onParametersSubmit = (values: FormValues) => {
    setParams(values);
    handleNext();
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>, fileType: string) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFiles({ ...uploadedFiles, [fileType]: file });
    }
  };

  const handleFilesNext = () => {
    if (uploadedFiles.receptor && uploadedFiles.ligand) {
      handleNext();
    } else {
      console.warn('Please upload both receptor and ligand files before proceeding.');
    }
  };

  const handleExecute = async () => {
    setSubmitting(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    handleNext();
    setSubmitting(false);
  };

  const handleViewJobs = () => {
    navigate('/job-manager');
  };

  return (
    <Box sx={{ maxWidth: 1280, mx: 'auto', p: 3 }}>
      {/* Header Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" component="h1" sx={{ fontWeight: 600, mb: 2 }}>
          Classic molecular docking using AutoDock 4 algorithm for protein-ligand binding prediction
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {['Docking', 'v4.2.6', 'CPU: medium', 'Duration: 5–30 minutes'].map((tag) => (
            <Chip
              key={tag}
              label={tag}
              size="small"
              sx={{
                backgroundColor: 'grey.100',
                fontSize: '0.75rem',
                height: 24,
              }}
            />
          ))}
        </Box>
      </Box>

      {/* Integrated Stepper with Content */}
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
                <form onSubmit={handleSubmit(onParametersSubmit)}>
                  {/* Required Parameters */}
                  <Box sx={{ border: 1, borderColor: 'grey.300', borderRadius: 2, p: 3, mb: 3 }}>
                    <Typography
                      variant="subtitle2"
                      sx={{ mb: 3, fontWeight: 500, color: 'text.secondary' }}
                    >
                      Required Parameters
                    </Typography>

                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6} md={3}>
                        <ParameterField
                          name="xSize"
                          control={control}
                          label="Search Space X Size*"
                          tooltip="Size of the search space in the X dimension (Angstroms)"
                          error={errors.xSize}
                        />
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <ParameterField
                          name="ySize"
                          control={control}
                          label="Search Space Y Size*"
                          tooltip="Size of the search space in the Y dimension (Angstroms)"
                          error={errors.ySize}
                        />
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <ParameterField
                          name="zSize"
                          control={control}
                          label="Search Space Z Size*"
                          tooltip="Size of the search space in the Z dimension (Angstroms)"
                          error={errors.zSize}
                        />
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <ParameterField
                          name="gaRuns"
                          control={control}
                          label="GA Runs*"
                          tooltip="Number of genetic algorithm runs"
                          error={errors.gaRuns}
                        />
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <Controller
                          name="outputFormat"
                          control={control}
                          render={({ field }) => (
                            <Box>
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <Typography
                                  variant="body2"
                                  component="label"
                                  sx={{ fontWeight: 500 }}
                                >
                                  Output Format*
                                </Typography>
                                <Tooltip title="Format for the output files">
                                  <IconButton size="small" sx={{ ml: 0.5, p: 0.25 }}>
                                    <HelpOutline sx={{ fontSize: 16 }} />
                                  </IconButton>
                                </Tooltip>
                              </Box>
                              <FormControl fullWidth size="small" error={!!errors.outputFormat}>
                                <Select {...field} displayEmpty>
                                  <MenuItem value="pdbqt">pdbqt</MenuItem>
                                </Select>
                                <FormHelperText>
                                  {errors.outputFormat?.message || 'Format for the output files'}
                                </FormHelperText>
                              </FormControl>
                            </Box>
                          )}
                        />
                      </Grid>
                    </Grid>
                  </Box>

                  {/* Advanced Parameters */}
                  <Accordion
                    defaultExpanded
                    sx={{
                      mb: 4,
                      border: 1,
                      borderColor: 'grey.300',
                      '&:before': { display: 'none' },
                    }}
                  >
                    <AccordionSummary
                      expandIcon={<ExpandMore />}
                      sx={{ minHeight: 48, '&.Mui-expanded': { minHeight: 48 } }}
                    >
                      <Typography
                        variant="subtitle2"
                        sx={{ fontWeight: 500, color: 'text.secondary' }}
                      >
                        Advanced Parameters (1)
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={4}>
                          <ParameterField
                            name="energyEvals"
                            control={control}
                            label="Energy Evaluations"
                            tooltip="Maximum number of energy evaluations"
                            error={errors.energyEvals}
                          />
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>

                  {/* Navigation */}
                  <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
                    <Button
                      variant="outlined"
                      onClick={handleBack}
                      startIcon={<ArrowBack />}
                      sx={{ textTransform: 'uppercase', fontWeight: 500 }}
                    >
                      Back
                    </Button>
                    <Button
                      type="submit"
                      variant="contained"
                      endIcon={<ArrowForward />}
                      sx={{ textTransform: 'uppercase', fontWeight: 500 }}
                    >
                      Next
                    </Button>
                  </Box>
                </form>
              </Box>
            </StepContent>
          </Step>

          {/* Step 2: Upload Files */}
          <Step>
            <StepLabel>
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                Upload Files
              </Typography>
            </StepLabel>
            <StepContent>
              <Box sx={{ mt: 2 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 500 }}>
                        Receptor File (PDB/PDBQT) *
                      </Typography>
                      <Button
                        variant="outlined"
                        component="label"
                        fullWidth
                        sx={{ mb: 1, justifyContent: 'flex-start', p: 2 }}
                      >
                        {uploadedFiles.receptor
                          ? uploadedFiles.receptor.name
                          : 'Choose Receptor File'}
                        <input
                          type="file"
                          hidden
                          accept=".pdb,.pdbqt"
                          onChange={(e) => handleFileUpload(e, 'receptor')}
                        />
                      </Button>
                      {uploadedFiles.receptor && (
                        <Chip label="File uploaded" color="success" size="small" />
                      )}
                    </Box>

                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 500 }}>
                        Ligand File (PDB/PDBQT/SDF) *
                      </Typography>
                      <Button
                        variant="outlined"
                        component="label"
                        fullWidth
                        sx={{ mb: 1, justifyContent: 'flex-start', p: 2 }}
                      >
                        {uploadedFiles.ligand ? uploadedFiles.ligand.name : 'Choose Ligand File'}
                        <input
                          type="file"
                          hidden
                          accept=".pdb,.pdbqt,.sdf"
                          onChange={(e) => handleFileUpload(e, 'ligand')}
                        />
                      </Button>
                      {uploadedFiles.ligand && (
                        <Chip label="File uploaded" color="success" size="small" />
                      )}
                    </Box>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Box sx={{ p: 3, backgroundColor: 'grey.50', borderRadius: 2 }}>
                      <Typography variant="h6" gutterBottom>
                        File Requirements
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        • Receptor: PDB or PDBQT format
                        <br />
                        • Ligand: PDB, PDBQT, or SDF format
                        <br />• Files should be properly prepared with correct coordinates
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {/* Navigation */}
                <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
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
                    onClick={handleFilesNext}
                    endIcon={<ArrowForward />}
                    sx={{ textTransform: 'uppercase', fontWeight: 500 }}
                  >
                    Next
                  </Button>
                </Box>
              </Box>
            </StepContent>
          </Step>

          {/* Step 3: Review & Execute */}
          <Step>
            <StepLabel>
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                Review & Execute
              </Typography>
            </StepLabel>
            <StepContent>
              <Box sx={{ mt: 2 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 500 }}>
                        Parameters
                      </Typography>
                      <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                        <Typography variant="body2">
                          X Size: {params?.xSize} Å<br />Y Size: {params?.ySize} Å<br />Z Size:{' '}
                          {params?.zSize} Å<br />
                          GA Runs: {params?.gaRuns}
                          <br />
                          Output Format: {params?.outputFormat}
                          <br />
                          Energy Evaluations: {params?.energyEvals?.toLocaleString()}
                        </Typography>
                      </Paper>
                    </Box>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 500 }}>
                        Files
                      </Typography>
                      <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                        <Typography variant="body2">
                          Receptor: {uploadedFiles.receptor?.name || 'Not uploaded'}
                          <br />
                          Ligand: {uploadedFiles.ligand?.name || 'Not uploaded'}
                        </Typography>
                      </Paper>
                    </Box>
                  </Grid>
                </Grid>

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
                    {submitting ? 'Submitting...' : 'Execute Job'}
                  </Button>
                </Box>
              </Box>
            </StepContent>
          </Step>

          {/* Step 4: Monitor Progress */}
          <Step>
            <StepLabel>
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                Job Submitted Successfully!
              </Typography>
            </StepLabel>
            <StepContent>
              <Box sx={{ mt: 2, textAlign: 'center', py: 4 }}>
                <Typography variant="h5" gutterBottom color="success.main">
                  ✓ Your docking job has been submitted
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  Job ID: JOB-{Date.now().toString().slice(-8)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                  Estimated completion time: 15-30 minutes
                </Typography>

                <Button
                  variant="contained"
                  onClick={handleViewJobs}
                  size="large"
                  startIcon={<PlayArrow />}
                >
                  Monitor Job Progress
                </Button>
              </Box>
            </StepContent>
          </Step>
        </Stepper>
      </Paper>
    </Box>
  );
};

// Wizard Provider Component
const WizardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [params, setParams] = useState<DockingParams | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFiles>({});

  return (
    <WizardContext.Provider
      value={{
        params,
        setParams,
        activeStep,
        setActiveStep,
        uploadedFiles,
        setUploadedFiles,
      }}
    >
      {children}
    </WizardContext.Provider>
  );
};

// Main ExecuteTasks component
export const ExecuteTasks: React.FC = () => {
  const location = useLocation();
  const selectedTemplate = location.state?.selectedTemplate;

  if (
    selectedTemplate &&
    (selectedTemplate.name?.includes('AutoDock') ||
      selectedTemplate.id?.includes('autodock') ||
      selectedTemplate.category === 'autodock_vina' ||
      selectedTemplate.category === 'autodock4')
  ) {
    return (
      <WizardProvider>
        <IntegratedWizard />
      </WizardProvider>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Execute Tasks
      </Typography>

      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          Select a Task Template
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Choose a molecular analysis task from the Task Library to begin configuration.
        </Typography>
        <Button variant="contained" onClick={() => window.history.back()} size="large">
          Go to Task Library
        </Button>
      </Paper>
    </Box>
  );
};
