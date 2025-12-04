import React, { useCallback, useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Chip,
  Alert,
  Paper,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  InsertDriveFile as FileIcon,
} from '@mui/icons-material';
import { TaskParameter } from '../../types/tasks';

interface FileUploadFieldProps {
  parameter: TaskParameter;
  value: File | null;
  onChange: (file: File | null) => void;
  error?: string;
}

export const FileUploadField: React.FC<FileUploadFieldProps> = ({
  parameter,
  value,
  onChange,
  error,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const allowedTypes = parameter.validation?.file_types || [];
  const maxSizeMB = parameter.validation?.max_size_mb || 100;

  const validateFile = (file: File): string | null => {
    // Check file type
    if (allowedTypes.length > 0) {
      const fileExt = `.${file.name.split('.').pop()?.toLowerCase()}`;
      if (!allowedTypes.some(type => type.toLowerCase() === fileExt)) {
        return `Invalid file type. Allowed types: ${allowedTypes.join(', ')}`;
      }
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSizeMB) {
      return `File too large. Maximum size: ${maxSizeMB}MB`;
    }

    return null;
  };

  const handleFile = (file: File) => {
    const error = validateFile(file);
    if (error) {
      setValidationError(error);
      onChange(null);
      return;
    }

    setValidationError(null);
    onChange(file);
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleRemove = () => {
    onChange(null);
    setValidationError(null);
  };

  const formatFileSize = (bytes: number): string => {
    const mb = bytes / (1024 * 1024);
    if (mb < 1) {
      return `${(bytes / 1024).toFixed(2)} KB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="body2" gutterBottom>
        {parameter.name}
        {parameter.required && <span style={{ color: 'red' }}> *</span>}
      </Typography>

      {parameter.description && (
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
          {parameter.description}
        </Typography>
      )}

      {!value ? (
        <Paper
          variant="outlined"
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          sx={{
            border: '2px dashed',
            borderColor: dragActive ? 'primary.main' : 'divider',
            borderRadius: 2,
            p: 3,
            textAlign: 'center',
            cursor: 'pointer',
            bgcolor: dragActive ? 'action.hover' : 'background.paper',
            transition: 'all 0.3s',
            '&:hover': {
              borderColor: 'primary.main',
              bgcolor: 'action.hover',
            },
          }}
        >
          <input
            type="file"
            id={`file-upload-${parameter.name}`}
            accept={allowedTypes.join(',')}
            onChange={handleChange}
            style={{ display: 'none' }}
          />
          <label htmlFor={`file-upload-${parameter.name}`} style={{ cursor: 'pointer' }}>
            <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
              <UploadIcon sx={{ fontSize: 48, color: 'text.secondary' }} />
              <Box>
                <Typography variant="body2" color="text.primary">
                  Drag and drop file here, or{' '}
                  <span style={{ color: '#1976d2', textDecoration: 'underline' }}>browse</span>
                </Typography>
                {allowedTypes.length > 0 && (
                  <Typography variant="caption" color="text.secondary" display="block">
                    Supported: {allowedTypes.join(', ')}
                  </Typography>
                )}
                <Typography variant="caption" color="text.secondary">
                  Maximum size: {maxSizeMB}MB
                </Typography>
              </Box>
            </Box>
          </label>
        </Paper>
      ) : (
        <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <FileIcon color="primary" />
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="body2" noWrap>
                {value.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatFileSize(value.size)}
              </Typography>
            </Box>
            <IconButton onClick={handleRemove} size="small" color="error">
              <DeleteIcon />
            </IconButton>
          </Box>
        </Paper>
      )}

      {(validationError || error) && (
        <Alert severity="error" sx={{ mt: 1 }}>
          {validationError || error}
        </Alert>
      )}

      {allowedTypes.length > 0 && !value && (
        <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {allowedTypes.map(type => (
            <Chip key={type} label={type} size="small" variant="outlined" />
          ))}
        </Box>
      )}
    </Box>
  );
};
