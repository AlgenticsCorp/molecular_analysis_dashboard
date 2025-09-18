import React, { useState } from 'react';
import {
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  InsertDriveFile,
  Visibility,
  Download,
  Delete,
  Upload,
  Science,
} from '@mui/icons-material';
import MolecularViewer from '../components/molecular/MolecularViewerSimple';

// Sample molecular data for demonstration
const SAMPLE_PDB_DATA = `ATOM      1  N   ALA A   1      20.154  16.967  25.810  1.00 11.72           N
ATOM      2  CA  ALA A   1      19.030  16.522  26.645  1.00 11.85           C
ATOM      3  C   ALA A   1      17.923  17.573  26.803  1.00 11.99           C
ATOM      4  O   ALA A   1      18.101  18.705  27.238  1.00 12.12           O
ATOM      5  CB  ALA A   1      19.534  16.074  28.012  1.00 11.77           C
ATOM      6  N   GLY A   2      16.746  17.250  26.367  1.00 12.15           N
ATOM      7  CA  GLY A   2      15.606  18.159  26.441  1.00 12.43           C
ATOM      8  C   GLY A   2      14.401  17.555  27.124  1.00 12.34           C
ATOM      9  O   GLY A   2      14.181  16.351  27.103  1.00 12.44           O
ATOM     10  N   VAL A   3      13.595  18.326  27.801  1.00 12.25           N
END`;

interface MolecularFile {
  id: string;
  name: string;
  format: string;
  size: string;
  uploadDate: string;
  description: string;
  data?: string;
}

const sampleFiles: MolecularFile[] = [
  {
    id: '1',
    name: 'sample_protein.pdb',
    format: 'PDB',
    size: '2.3 MB',
    uploadDate: '2025-09-15',
    description: 'Sample protein structure for demonstration',
    data: SAMPLE_PDB_DATA,
  },
  {
    id: '2',
    name: 'ligand_compound.sdf',
    format: 'SDF',
    size: '15.2 KB',
    uploadDate: '2025-09-14',
    description: 'Small molecule ligand structure',
  },
  {
    id: '3',
    name: 'receptor_binding_site.pdbqt',
    format: 'PDBQT',
    size: '1.8 MB',
    uploadDate: '2025-09-13',
    description: 'Receptor structure prepared for AutoDock',
  },
  {
    id: '4',
    name: 'docking_results.pdbqt',
    format: 'PDBQT',
    size: '892 KB',
    uploadDate: '2025-09-12',
    description: 'AutoDock Vina docking results',
  },
];

export const FileManager: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<MolecularFile | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const handlePreview = (file: MolecularFile) => {
    setSelectedFile(file);
    setPreviewOpen(true);
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setSelectedFile(null);
  };

  const getFormatColor = (format: string) => {
    switch (format.toLowerCase()) {
      case 'pdb':
        return 'primary';
      case 'pdbqt':
        return 'secondary';
      case 'sdf':
        return 'success';
      case 'mol2':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        File Manager
      </Typography>

      {/* Upload Section */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <Upload sx={{ mr: 1 }} />
          Upload Molecular Files
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Supported formats: PDB, PDBQT, SDF, MOL2, XYZ
        </Typography>
        <Button variant="contained" startIcon={<Upload />}>
          Choose Files
        </Button>
      </Paper>

      {/* 3D Viewer Demo Section */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <Science sx={{ mr: 1 }} />
          3D Molecular Viewer Demo
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Interactive 3D visualization of molecular structures using 3Dmol.js
        </Typography>
        <Box sx={{ height: 400, border: '1px solid #e0e0e0', borderRadius: 1 }}>
          <MolecularViewer
            moleculeData={SAMPLE_PDB_DATA}
            format="pdb"
            height={398}
            showControls={true}
          />
        </Box>
      </Paper>

      {/* File List */}
      <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
        Uploaded Files
      </Typography>

      <Grid container spacing={3}>
        {sampleFiles.map((file) => (
          <Grid item xs={12} md={6} lg={4} key={file.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <InsertDriveFile sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="h6" sx={{ fontWeight: 500 }}>
                    {file.name}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Chip
                    label={file.format}
                    color={getFormatColor(file.format) as any}
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <Chip label={file.size} variant="outlined" size="small" />
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {file.description}
                </Typography>

                <Typography variant="caption" color="text.secondary">
                  Uploaded: {new Date(file.uploadDate).toLocaleDateString()}
                </Typography>
              </CardContent>

              <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
                <Button
                  size="small"
                  startIcon={<Visibility />}
                  onClick={() => handlePreview(file)}
                  disabled={!file.data}
                >
                  Preview
                </Button>
                <Box>
                  <Button size="small" startIcon={<Download />}>
                    Download
                  </Button>
                  <Button size="small" startIcon={<Delete />} color="error">
                    Delete
                  </Button>
                </Box>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={handleClosePreview}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '80vh' },
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <InsertDriveFile sx={{ mr: 1 }} />
              {selectedFile?.name}
            </Box>
            <Chip
              label={selectedFile?.format}
              color={getFormatColor(selectedFile?.format || '') as any}
              size="small"
            />
          </Box>
        </DialogTitle>

        <DialogContent sx={{ p: 0, display: 'flex', flexDirection: 'column' }}>
          {selectedFile && selectedFile.data && (
            <MolecularViewer
              moleculeData={selectedFile.data}
              format={selectedFile.format.toLowerCase()}
              height={500}
              showControls={true}
            />
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClosePreview}>Close</Button>
          <Button variant="contained" startIcon={<Download />}>
            Download
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
