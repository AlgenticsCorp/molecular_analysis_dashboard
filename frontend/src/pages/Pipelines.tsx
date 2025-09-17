import React from 'react';
import { Typography, Box } from '@mui/material';

export const Pipelines: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Pipelines
      </Typography>
      <Typography variant="body1">
        Create and manage molecular analysis pipelines.
      </Typography>
    </Box>
  );
};
