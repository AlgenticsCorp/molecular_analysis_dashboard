import React from 'react';
import { Typography, Box } from '@mui/material';

export const AdminPanel: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Admin Panel
      </Typography>
      <Typography variant="body1">
        Administrative settings and user management.
      </Typography>
    </Box>
  );
};
