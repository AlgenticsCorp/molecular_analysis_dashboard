/**
 * MolecularViewer Component
 *
 * A reusable 3D molecular structure viewer using 3Dmol.js
 * Supports PDB, PDBQT, SDF, and other molecular file formats
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Box,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Paper,
  ButtonGroup,
  Typography,
  FormControl,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  Refresh,
  Fullscreen,
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';

// 3Dmol types (since @types/3dmol doesn't exist, we'll define minimal types)
declare global {
  interface Window {
    $3Dmol: any;
  }
}

export interface MolecularViewerProps {
  /** Molecular structure data (PDB, PDBQT, SDF format) */
  moleculeData?: string;
  /** Data format ('pdb', 'pdbqt', 'sdf', 'mol2', 'xyz') */
  format?: string;
  /** URL to fetch molecular data from */
  dataUrl?: string;
  /** Viewer height in pixels */
  height?: number;
  /** Viewer width (auto-fits container by default) */
  width?: string | number;
  /** Show control panel */
  showControls?: boolean;
  /** Initial visualization style */
  initialStyle?: 'cartoon' | 'stick' | 'sphere' | 'line' | 'surface';
  /** Background color */
  backgroundColor?: string;
  /** Callback when molecule is loaded */
  onMoleculeLoaded?: (success: boolean) => void;
  /** Callback when atoms are selected */
  onSelectionChange?: (selection: any) => void;
  /** Enable selection mode */
  enableSelection?: boolean;
  /** Custom styling */
  sx?: any;
}

export interface ViewerStyle {
  name: string;
  label: string;
  config: any;
}

const VIEWER_STYLES: ViewerStyle[] = [
  {
    name: 'cartoon',
    label: 'Cartoon',
    config: { cartoon: { color: 'spectrum' } },
  },
  {
    name: 'stick',
    label: 'Stick',
    config: { stick: { radius: 0.2 } },
  },
  {
    name: 'sphere',
    label: 'Sphere',
    config: { sphere: { radius: 1.0 } },
  },
  {
    name: 'line',
    label: 'Line',
    config: { line: {} },
  },
  {
    name: 'surface',
    label: 'Surface',
    config: { surface: { opacity: 0.8 } },
  },
  {
    name: 'cartoon_stick',
    label: 'Cartoon + Stick',
    config: { cartoon: { color: 'spectrum' }, stick: { radius: 0.15 } },
  },
];

export const MolecularViewer: React.FC<MolecularViewerProps> = ({
  moleculeData,
  format = 'pdb',
  dataUrl,
  height = 400,
  width = '100%',
  showControls = true,
  initialStyle = 'cartoon',
  backgroundColor = '#000000',
  onMoleculeLoaded,
  onSelectionChange,
  enableSelection = false,
  sx = {},
}) => {
  const viewerRef = useRef<HTMLDivElement>(null);
  const viewerInstanceRef = useRef<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStyle, setCurrentStyle] = useState(initialStyle);
  const [showSideChains, setShowSideChains] = useState(true);

  // Initialize 3Dmol viewer
  const initializeViewer = useCallback(async () => {
    if (!viewerRef.current) return;

    try {
      // Wait for 3Dmol to load if not already loaded
      if (!window.$3Dmol) {
        const script = document.createElement('script');
        script.src = 'https://3Dmol.org/build/3Dmol-min.js';
        script.onload = () => initializeViewer();
        document.head.appendChild(script);
        return;
      }

      // Create viewer instance
      const config = {
        backgroundColor: backgroundColor,
        antialias: true,
      };

      viewerInstanceRef.current = window.$3Dmol.createViewer(viewerRef.current, config);

      // Load molecular data
      await loadMolecule();
    } catch (err) {
      console.error('Failed to initialize 3Dmol viewer:', err);
      setError('Failed to initialize molecular viewer');
      setLoading(false);
      onMoleculeLoaded?.(false);
    }
  }, [backgroundColor, onMoleculeLoaded]);

  // Load molecule data into viewer
  const loadMolecule = useCallback(async () => {
    if (!viewerInstanceRef.current) return;

    try {
      setLoading(true);
      setError(null);

      let data: string;

      if (dataUrl) {
        // Fetch data from URL
        const response = await fetch(dataUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch molecular data: ${response.statusText}`);
        }
        data = await response.text();
      } else if (moleculeData) {
        data = moleculeData;
      } else {
        throw new Error('No molecular data provided');
      }

      // Clear existing models
      viewerInstanceRef.current.removeAllModels();

      // Add model to viewer
      const model = viewerInstanceRef.current.addModel(data, format);

      if (!model) {
        throw new Error('Failed to parse molecular data');
      }

      // Apply initial styling
      applyStyle(currentStyle);

      // Zoom to fit
      viewerInstanceRef.current.zoomTo();

      // Render the scene
      viewerInstanceRef.current.render();

      // Setup selection handling if enabled
      if (enableSelection) {
        viewerInstanceRef.current.setClickable({}, true, (atom: any) => {
          onSelectionChange?.(atom);
        });
      }

      setLoading(false);
      onMoleculeLoaded?.(true);
    } catch (err) {
      console.error('Failed to load molecule:', err);
      setError(err instanceof Error ? err.message : 'Failed to load molecular structure');
      setLoading(false);
      onMoleculeLoaded?.(false);
    }
  }, [
    moleculeData,
    dataUrl,
    format,
    currentStyle,
    enableSelection,
    onSelectionChange,
    onMoleculeLoaded,
  ]);

  // Apply visualization style
  const applyStyle = (styleName: string) => {
    if (!viewerInstanceRef.current) return;

    const style = VIEWER_STYLES.find((s) => s.name === styleName);
    if (!style) return;

    // Clear existing styles
    viewerInstanceRef.current.setStyle({}, {});

    // Apply new style
    viewerInstanceRef.current.setStyle({}, style.config);

    // Render changes
    viewerInstanceRef.current.render();

    setCurrentStyle(styleName);
  };

  // Control functions
  const handleStyleChange = (event: SelectChangeEvent) => {
    const newStyle = event.target.value;
    applyStyle(newStyle);
  };

  const handleZoomIn = () => {
    if (viewerInstanceRef.current) {
      viewerInstanceRef.current.zoom(1.2);
      viewerInstanceRef.current.render();
    }
  };

  const handleZoomOut = () => {
    if (viewerInstanceRef.current) {
      viewerInstanceRef.current.zoom(0.8);
      viewerInstanceRef.current.render();
    }
  };

  const handleCenter = () => {
    if (viewerInstanceRef.current) {
      viewerInstanceRef.current.zoomTo();
      viewerInstanceRef.current.render();
    }
  };

  const handleRefresh = () => {
    loadMolecule();
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      viewerRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  const toggleSideChains = () => {
    if (!viewerInstanceRef.current) return;

    setShowSideChains(!showSideChains);

    // Toggle side chain visibility
    const selector = showSideChains ? { not: { atom: 'CA,C,N,O' } } : {};
    viewerInstanceRef.current.setStyle(selector, { stick: { hidden: showSideChains } });
    viewerInstanceRef.current.render();
  };

  // Initialize viewer on mount
  useEffect(() => {
    initializeViewer();

    // Cleanup function
    return () => {
      if (viewerInstanceRef.current) {
        viewerInstanceRef.current.clear();
      }
    };
  }, [initializeViewer]);

  // Reload when data changes
  useEffect(() => {
    if (viewerInstanceRef.current && (moleculeData || dataUrl)) {
      loadMolecule();
    }
  }, [moleculeData, dataUrl, format, loadMolecule]);

  if (error) {
    return (
      <Paper sx={{ p: 2, height, display: 'flex', alignItems: 'center', ...sx }}>
        <Alert severity="error" sx={{ width: '100%' }}>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Paper>
    );
  }

  return (
    <Paper sx={{ position: 'relative', height, width, ...sx }}>
      {/* Loading spinner */}
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

      {/* Control panel */}
      {showControls && !loading && !error && (
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            zIndex: 3,
            display: 'flex',
            flexDirection: 'column',
            gap: 1,
          }}
        >
          {/* Style selector */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <Select
              value={currentStyle}
              onChange={handleStyleChange}
              sx={{
                backgroundColor: 'rgba(255,255,255,0.9)',
                fontSize: '0.875rem',
              }}
            >
              {VIEWER_STYLES.map((style) => (
                <MenuItem key={style.name} value={style.name}>
                  {style.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Action buttons */}
          <ButtonGroup orientation="vertical" size="small">
            <Tooltip title="Zoom In">
              <IconButton onClick={handleZoomIn} sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}>
                <ZoomIn />
              </IconButton>
            </Tooltip>

            <Tooltip title="Zoom Out">
              <IconButton onClick={handleZoomOut} sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}>
                <ZoomOut />
              </IconButton>
            </Tooltip>

            <Tooltip title="Center View">
              <IconButton onClick={handleCenter} sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}>
                <CenterFocusStrong />
              </IconButton>
            </Tooltip>

            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh} sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}>
                <Refresh />
              </IconButton>
            </Tooltip>

            <Tooltip title={showSideChains ? 'Hide Side Chains' : 'Show Side Chains'}>
              <IconButton
                onClick={toggleSideChains}
                sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}
              >
                {showSideChains ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </Tooltip>

            <Tooltip title="Fullscreen">
              <IconButton
                onClick={toggleFullscreen}
                sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}
              >
                <Fullscreen />
              </IconButton>
            </Tooltip>
          </ButtonGroup>
        </Box>
      )}

      {/* 3D Viewer container */}
      <div
        ref={viewerRef}
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: backgroundColor,
        }}
      />
    </Paper>
  );
};

export default MolecularViewer;
