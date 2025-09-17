import React from 'react';
import { Typography, Box } from '@mui/material';

export const FileManager: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        File Manager
      </Typography>
      <Typography variant="body1">
        Upload, organize, and manage molecular structure files.
      </Typography>
    </Box>
  );
};
