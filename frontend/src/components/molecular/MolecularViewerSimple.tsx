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
  const [viewerReady, setViewerReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const ensureScript = (): Promise<void> => {
      if (window.$3Dmol) {
        return Promise.resolve();
      }

      const scriptId = '3dmol-script';
      let script = document.getElementById(scriptId) as HTMLScriptElement | null;

      if (script) {
        return new Promise<void>((resolve, reject) => {
          const onLoad = () => {
            script?.removeEventListener('load', onLoad);
            script?.removeEventListener('error', onError);
            resolve();
          };
          const onError = (err: Event) => {
            script?.removeEventListener('load', onLoad);
            script?.removeEventListener('error', onError);
            reject(err);
          };

          script.addEventListener('load', onLoad);
          script.addEventListener('error', onError);
        });
      }

      script = document.createElement('script');
      script.id = scriptId;
      script.src = 'https://3Dmol.org/build/3Dmol-min.js';
      script.async = true;

      return new Promise<void>((resolve, reject) => {
        script!.onload = () => resolve();
        script!.onerror = (err) => reject(err);
        document.head.appendChild(script!);
      });
    };

    const initializeViewer = async () => {
      if (!viewerRef.current) {
        setLoading(false);
        return;
      }

      try {
        await ensureScript();

        if (!isMounted || !viewerRef.current) {
          return;
        }

        viewerInstanceRef.current = window.$3Dmol.createViewer(viewerRef.current, {
          backgroundColor: '#000000',
        });

        setViewerReady(true);
        setLoading(false);
      } catch (err) {
        console.error('Failed to load 3Dmol viewer script', err);
        if (isMounted) {
          setError('Failed to load 3D viewer');
          setLoading(false);
        }
      }
    };

    void initializeViewer();

    return () => {
      isMounted = false;
      if (viewerInstanceRef.current) {
        viewerInstanceRef.current.clear();
      }
    };
  }, []);

  useEffect(() => {
    if (!viewerReady) {
      return;
    }

    const viewer = viewerInstanceRef.current;
    if (!viewer) {
      return;
    }

    setError(null);

    if (!moleculeData) {
      viewer.removeAllModels();
      viewer.render();
      setLoading(false);
      return;
    }

    setLoading(true);

    try {
      viewer.removeAllModels();

      const normalizedFormat = normalizeFormat(format);
      const model = viewer.addModel(moleculeData, normalizedFormat);

      if (!model) {
        throw new Error('3Dmol returned an empty model');
      }

      const style = selectStyle(normalizedFormat);
      viewer.setStyle({}, style);
      viewer.zoomTo();
      viewer.render();
      setLoading(false);
    } catch (err) {
      console.error('Failed to load molecule into viewer', err);
      setError('Failed to load molecule');
      setLoading(false);
    }
  }, [viewerReady, moleculeData, format]);

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

const normalizeFormat = (rawFormat?: string): string => {
  const fmt = (rawFormat || 'pdb').toLowerCase();

  switch (fmt) {
    case 'mol':
    case 'mol2':
      return 'mol2';
    case 'sdf':
      return 'sdf';
    case 'pdbqt':
      return 'pdbqt';
    case 'xyz':
      return 'xyz';
    default:
      return 'pdb';
  }
};

const selectStyle = (format: string) => {
  const smallMoleculeFormats = new Set(['sdf', 'mol2', 'xyz']);

  if (smallMoleculeFormats.has(format)) {
    return {
      stick: {
        colorscheme: 'Jmol',
        radius: 0.15,
      },
      sphere: {
        colorscheme: 'Jmol',
        radius: 0.3,
        scale: 0.3,
      },
    };
  }

  return {
    cartoon: { color: 'spectrum' },
  };
};

export default MolecularViewer;
