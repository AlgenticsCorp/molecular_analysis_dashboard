import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Button,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';

const steps = ['Select Molecules', 'Choose Pipeline', 'Configure Parameters', 'Execute Job'];

export const ExecuteService: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedLigand, setSelectedLigand] = useState('');
  const [selectedProtein, setSelectedProtein] = useState('');
  const [selectedPipeline, setSelectedPipeline] = useState('');

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Select Ligand
                  </Typography>
                  <FormControl fullWidth>
                    <InputLabel>Ligand Molecule</InputLabel>
                    <Select
                      value={selectedLigand}
                      onChange={(e) => setSelectedLigand(e.target.value)}
                    >
                      <MenuItem value="ligand1">Sample Ligand 1</MenuItem>
                      <MenuItem value="ligand2">Sample Ligand 2</MenuItem>
                    </Select>
                  </FormControl>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Select Protein
                  </Typography>
                  <FormControl fullWidth>
                    <InputLabel>Protein Target</InputLabel>
                    <Select
                      value={selectedProtein}
                      onChange={(e) => setSelectedProtein(e.target.value)}
                    >
                      <MenuItem value="protein1">Sample Protein 1</MenuItem>
                      <MenuItem value="protein2">Sample Protein 2</MenuItem>
                    </Select>
                  </FormControl>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        );
      case 1:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Choose Analysis Pipeline
              </Typography>
              <FormControl fullWidth>
                <InputLabel>Pipeline</InputLabel>
                <Select
                  value={selectedPipeline}
                  onChange={(e) => setSelectedPipeline(e.target.value)}
                >
                  <MenuItem value="vina">AutoDock Vina</MenuItem>
                  <MenuItem value="smina">Smina</MenuItem>
                  <MenuItem value="gnina">Gnina</MenuItem>
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        );
      case 2:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configure Parameters
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Pipeline parameters will be shown here based on selected pipeline.
              </Typography>
            </CardContent>
          </Card>
        );
      case 3:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Job Summary
              </Typography>
              <Typography variant="body2">Ligand: {selectedLigand || 'Not selected'}</Typography>
              <Typography variant="body2">Protein: {selectedProtein || 'Not selected'}</Typography>
              <Typography variant="body2">
                Pipeline: {selectedPipeline || 'Not selected'}
              </Typography>
            </CardContent>
          </Card>
        );
      default:
        return <Typography>Unknown step</Typography>;
    }
  };

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Execute Molecular Analysis Service
      </Typography>

      <Paper sx={{ p: 3 }}>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ mb: 4 }}>{renderStepContent(activeStep)}</Box>

        <Box sx={{ display: 'flex', flexDirection: 'row', pt: 2 }}>
          <Button color="inherit" disabled={activeStep === 0} onClick={handleBack} sx={{ mr: 1 }}>
            Back
          </Button>
          <Box sx={{ flex: '1 1 auto' }} />
          <Button
            onClick={handleNext}
            variant="contained"
            disabled={activeStep === steps.length - 1}
          >
            {activeStep === steps.length - 1 ? 'Execute Job' : 'Next'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};
