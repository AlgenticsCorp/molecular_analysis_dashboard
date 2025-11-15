import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Assessment,
  Delete,
  Download,
  InsertDriveFile,
  Refresh,
  Upload,
  Visibility,
} from '@mui/icons-material';
import MolecularViewer from '../components/molecular/MolecularViewerSimple';
import { useAuth } from '@/contexts/AuthContext';
import { fileManagerApi } from '@/services/api/fileManager';
import type { StorageStats, UserFileRecord } from '@/types/fileManager';
import { formatFileSize } from '@/utils/fileDownload';

const PREVIEWABLE_FORMATS = new Set(['pdb', 'pdbqt', 'sdf', 'mol2', 'xyz']);

type ChipColor = 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'info';

const getFormatColor = (format?: string | null): ChipColor => {
  switch ((format || '').toLowerCase()) {
    case 'pdb':
      return 'primary';
    case 'pdbqt':
      return 'secondary';
    case 'sdf':
      return 'success';
    case 'mol2':
      return 'warning';
    case 'xyz':
      return 'info';
    default:
      return 'default';
  }
};

export const FileManager: React.FC = () => {
  const { user, isLoading: authLoading } = useAuth();
  const userId = user?.user_id ?? '';

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [files, setFiles] = useState<UserFileRecord[]>([]);
  const [stats, setStats] = useState<StorageStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState<boolean>(false);
  const [previewFile, setPreviewFile] = useState<UserFileRecord | null>(null);
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const hasFiles = files.length > 0;

  const fetchData = useCallback(async () => {
    if (!userId) {
      setFiles([]);
      setStats(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [filesResponse, statsResponse] = await Promise.all([
        fileManagerApi.listFiles({ userId, limit: 200 }),
        fileManagerApi.getStorageStats(userId),
      ]);

      setFiles(filesResponse.files);
      setStats(statsResponse);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load files';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (!authLoading) {
      void fetchData();
    }
  }, [authLoading, fetchData]);

  const handleFileSelection = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const list = event.target.files;
    if (!list || list.length === 0 || !userId) {
      return;
    }

    setUploading(true);
    setError(null);

    try {
      for (const file of Array.from(list)) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', userId);
        formData.append('name', file.name);

        try {
          await fileManagerApi.uploadFile(formData);
        } catch (uploadError) {
          const message =
            uploadError instanceof Error ? uploadError.message : `Failed to upload ${file.name}`;
          setError(message);
          break;
        }
      }

      await fetchData();
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const handleDelete = async (file: UserFileRecord) => {
    if (!userId) {
      return;
    }

    const confirmed = window.confirm(`Delete ${file.filename}? This action cannot be undone.`);
    if (!confirmed) {
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await fileManagerApi.deleteFile(file.file_id, userId);
      await fetchData();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete file';
      setError(message);
      setLoading(false);
    }
  };

  const handleDownload = async (file: UserFileRecord) => {
    try {
      await fileManagerApi.downloadFile(file.file_id, file.filename);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to download file';
      setError(message);
    }
  };

  const supportsPreview = useCallback((file: UserFileRecord): boolean => {
    const format = file.file_format || '';
    return PREVIEWABLE_FORMATS.has(format.toLowerCase());
  }, []);

  const handlePreview = async (file: UserFileRecord) => {
    setPreviewFile(file);
    setPreviewOpen(true);
    setPreviewContent(null);
    setPreviewError(null);

    if (!supportsPreview(file)) {
      setPreviewError('Preview is not available for this file format.');
      return;
    }

    setPreviewLoading(true);

    try {
      const content = await fileManagerApi.fetchFileContent(file.file_id);
      setPreviewContent(content);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load file preview';
      setPreviewError(message);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setPreviewFile(null);
    setPreviewContent(null);
    setPreviewError(null);
  };

  const formatBreakdown = useMemo(() => {
    if (!stats) {
      return [];
    }
    return Object.entries(stats.files_by_format).sort((a, b) => b[1] - a[1]);
  }, [stats]);

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        File Manager
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 4 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center">
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <Upload sx={{ mr: 1 }} />
              Upload Molecular Files
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Supported formats: PDB, PDBQT, SDF, MOL2, XYZ
            </Typography>
          </Box>

          <Box>
            <input
              ref={fileInputRef}
              type="file"
              hidden
              multiple
              onChange={handleFileSelection}
            />
            <Button
              variant="contained"
              startIcon={<Upload />}
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading || !userId}
            >
              {uploading ? 'Uploading...' : 'Choose Files'}
            </Button>
            <Tooltip title="Refresh file list">
              <span>
                <Button
                  sx={{ ml: 1 }}
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={() => void fetchData()}
                  disabled={loading}
                >
                  Refresh
                </Button>
              </span>
            </Tooltip>
          </Box>
        </Stack>
      </Paper>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <Assessment sx={{ mr: 1 }} />
          Storage Overview
        </Typography>

        {stats ? (
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Files
              </Typography>
              <Typography variant="h5">{stats.total_files}</Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Size
              </Typography>
              <Typography variant="h5">{formatFileSize(stats.total_size_bytes)}</Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Categories
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 1, rowGap: 1 }}>
                {Object.entries(stats.files_by_category).length === 0 && (
                  <Chip size="small" label="None" />
                )}
                {Object.entries(stats.files_by_category).map(([category, info]) => (
                  <Chip
                    key={category}
                    size="small"
                    label={`${category}: ${info.file_count}`}
                  />
                ))}
              </Stack>
            </Grid>

            {formatBreakdown.length > 0 && (
              <Grid size={{ xs: 12 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Files by Format
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 1, rowGap: 1 }}>
                  {formatBreakdown.map(([format, count]) => (
                    <Chip
                      key={format}
                      label={`${format.toUpperCase()}: ${count}`}
                      size="small"
                      color={getFormatColor(format)}
                    />
                  ))}
                </Stack>
              </Grid>
            )}
          </Grid>
        ) : (
          <Typography variant="body2" color="text.secondary">
            {userId ? 'No storage data available yet.' : 'Sign in to view your storage usage.'}
          </Typography>
        )}
      </Paper>

      <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
        Uploaded Files
      </Typography>

      {loading ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress />
        </Box>
      ) : hasFiles ? (
        <Grid container spacing={3}>
          {files.map((file) => (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={file.file_id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <InsertDriveFile sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="h6" sx={{ fontWeight: 500 }}>
                      {file.filename}
                    </Typography>
                  </Box>

                  <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                    <Chip
                      label={(file.file_format || 'unknown').toUpperCase()}
                      color={getFormatColor(file.file_format)}
                      size="small"
                    />
                    <Chip label={formatFileSize(file.size_bytes)} variant="outlined" size="small" />
                  </Stack>

                  {file.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {file.description}
                    </Typography>
                  )}

                  {file.tags.length > 0 && (
                    <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 1, rowGap: 1 }}>
                      {file.tags.map((tag) => (
                        <Chip key={tag} label={tag} size="small" variant="outlined" />
                      ))}
                    </Stack>
                  )}

                  <Typography variant="caption" color="text.secondary">
                    Uploaded {new Date(file.uploaded_at).toLocaleString()}
                  </Typography>
                </CardContent>

                <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
                  <Tooltip title={supportsPreview(file) ? 'Preview in 3D viewer' : 'Preview not available'}>
                    <span>
                      <Button
                        size="small"
                        startIcon={<Visibility />}
                        onClick={() => void handlePreview(file)}
                        disabled={!supportsPreview(file)}
                      >
                        Preview
                      </Button>
                    </span>
                  </Tooltip>
                  <Box>
                    <Button
                      size="small"
                      startIcon={<Download />}
                      onClick={() => void handleDownload(file)}
                    >
                      Download
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Delete />}
                      color="error"
                      onClick={() => void handleDelete(file)}
                    >
                      Delete
                    </Button>
                  </Box>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="body1" gutterBottom>
            {userId
              ? 'No files uploaded yet. Use the button above to upload your first molecule.'
              : 'Sign in to view and manage your molecular files.'}
          </Typography>
          {userId && (
            <Button variant="contained" startIcon={<Upload />} onClick={() => fileInputRef.current?.click()}>
              Upload a File
            </Button>
          )}
        </Paper>
      )}

      <Dialog
        open={previewOpen}
        onClose={handleClosePreview}
        maxWidth="lg"
        fullWidth
        PaperProps={{ sx: { height: '80vh' } }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <InsertDriveFile sx={{ mr: 1 }} />
              {previewFile?.filename}
            </Box>
            <Chip
              label={(previewFile?.file_format || 'unknown').toUpperCase()}
              color={getFormatColor(previewFile?.file_format)}
              size="small"
            />
          </Box>
        </DialogTitle>

        <DialogContent sx={{ p: 2, display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
          {previewLoading && (
            <Box display="flex" justifyContent="center" alignItems="center" flexGrow={1}>
              <CircularProgress />
            </Box>
          )}

          {!previewLoading && previewError && (
            <Alert severity="warning">{previewError}</Alert>
          )}

          {!previewLoading && previewContent && previewFile && (
            <Box sx={{ flexGrow: 1, minHeight: 400 }}>
              <MolecularViewer
                moleculeData={previewContent}
                format={(previewFile.file_format || 'pdb').toLowerCase()}
                height={500}
                showControls
              />
            </Box>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClosePreview}>Close</Button>
          {previewFile && (
            <Button
              variant="contained"
              startIcon={<Download />}
              onClick={() => void handleDownload(previewFile)}
            >
              Download
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};
