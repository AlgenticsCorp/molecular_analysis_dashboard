/**
 * MolecularViewer Component
 *
 * A reusable 3D molecular structure viewer using 3Dmol.js
 */

import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, Alert, Typography } from '@mui/material';

// Global type for 3Dmol
declare global {
  interface Window {
    $3Dmol: any;
  }
}

export interface MolecularViewerProps {
  moleculeData?: string;
  format?: string;
  height?: number;
  showControls?: boolean;
}

export const MolecularViewer: React.FC<MolecularViewerProps> = ({
  moleculeData,
  format = 'pdb',
  height = 400,
  showControls: _showControls = true,
}) => {
  const viewerRef = useRef<HTMLDivElement>(null);
  const viewerInstanceRef = useRef<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadScript = () => {
      if (window.$3Dmol) {
        initializeViewer();
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://3Dmol.org/build/3Dmol-min.js';
      script.onload = initializeViewer;
      script.onerror = () => setError('Failed to load 3Dmol.js');
      document.head.appendChild(script);
    };

    const initializeViewer = () => {
      if (!viewerRef.current) return;

      try {
        const config = { backgroundColor: '#000000' };
        viewerInstanceRef.current = window.$3Dmol.createViewer(viewerRef.current, config);

        if (moleculeData) {
          loadMolecule();
        } else {
          setLoading(false);
        }
      } catch {
        setError('Failed to initialize viewer');
        setLoading(false);
      }
    };

    const loadMolecule = () => {
      if (!viewerInstanceRef.current || !moleculeData) return;

      try {
        viewerInstanceRef.current.removeAllModels();
        const model = viewerInstanceRef.current.addModel(moleculeData, format);

        if (model) {
          viewerInstanceRef.current.setStyle({}, { cartoon: { color: 'spectrum' } });
          viewerInstanceRef.current.zoomTo();
          viewerInstanceRef.current.render();
          setLoading(false);
        } else {
          setError('Failed to parse molecular data');
          setLoading(false);
        }
      } catch {
        setError('Failed to load molecule');
        setLoading(false);
      }
    };

    loadScript();

    return () => {
      if (viewerInstanceRef.current) {
        viewerInstanceRef.current.clear();
      }
    };
  }, [moleculeData, format]);

  if (error) {
    return (
      <Box sx={{ p: 2, height, display: 'flex', alignItems: 'center' }}>
        <Alert severity="error" sx={{ width: '100%' }}>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ position: 'relative', height, width: '100%' }}>
      {loading && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 2,
          }}
        >
          <CircularProgress color="primary" />
        </Box>
      )}

      <div
        ref={viewerRef}
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: '#000000',
        }}
      />
    </Box>
  );
};

export default MolecularViewer;
