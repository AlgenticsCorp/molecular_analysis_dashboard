import React from 'react';
import { Typography, Box } from '@mui/material';

export const Settings: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1">Configure application preferences and user settings.</Typography>
    </Box>
  );
};
