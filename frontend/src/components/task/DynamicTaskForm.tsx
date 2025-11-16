import React from 'react';
import {
  Box,
  TextField,
  FormControl,
  FormHelperText,
  Switch,
  FormControlLabel,
  MenuItem,
  Select,
  InputLabel,
} from '@mui/material';
import { TaskParameter } from '../../types/tasks';
import { FileUploadField } from './FileUploadField';

export interface FormValues {
  [key: string]: any;
}

export interface FormErrors {
  [key: string]: string;
}

interface DynamicTaskFormProps {
  parameters: TaskParameter[];
  values: FormValues;
  onChange: (name: string, value: any) => void;
  errors?: FormErrors;
  allowFileUpload?: boolean;
}

export const DynamicTaskForm: React.FC<DynamicTaskFormProps> = ({
  parameters,
  values,
  onChange,
  errors = {},
  allowFileUpload = true,
}) => {
  const validateParameter = (parameter: TaskParameter, value: any): string | undefined => {
    // Required validation
    if (parameter.required && (value === undefined || value === null || value === '')) {
      return `${parameter.name} is required`;
    }

    // Skip validation if value is empty and not required
    if (!value && !parameter.required) {
      return undefined;
    }

    const validation = parameter.validation;
    if (!validation) return undefined;

    // Number range validation
    if (parameter.type === 'number' || parameter.type === 'integer') {
      const numValue = Number(value);
      if (validation.min !== undefined && numValue < validation.min) {
        return `Minimum value is ${validation.min}`;
      }
      if (validation.max !== undefined && numValue > validation.max) {
        return `Maximum value is ${validation.max}`;
      }
    }

    // String pattern validation
    if (parameter.type === 'string' && validation.pattern && value) {
      const regex = new RegExp(validation.pattern);
      if (!regex.test(value)) {
        return `Invalid format`;
      }
    }

    // Select/enum validation
    if (validation.allowed_values && value) {
      if (!validation.allowed_values.includes(value)) {
        return `Value must be one of: ${validation.allowed_values.join(', ')}`;
      }
    }

    return undefined;
  };

  const renderField = (parameter: TaskParameter) => {
    const value = values[parameter.name] ?? parameter.default;
    const error = errors[parameter.name] || validateParameter(parameter, value);

    switch (parameter.type) {
      case 'file':
        if (!allowFileUpload) {
          return null;
        }
        return (
          <FileUploadField
            key={parameter.name}
            parameter={parameter}
            value={value}
            onChange={(file) => onChange(parameter.name, file)}
            {...(error && { error })}
          />
        );

      case 'boolean':
        return (
          <FormControl key={parameter.name} fullWidth>
            <FormControlLabel
              control={
                <Switch
                  checked={Boolean(value)}
                  onChange={(e) => onChange(parameter.name, e.target.checked)}
                />
              }
              label={parameter.name}
            />
            {parameter.description && (
              <FormHelperText>{parameter.description}</FormHelperText>
            )}
            {error && <FormHelperText error>{error}</FormHelperText>}
          </FormControl>
        );

      case 'select':
        return (
          <FormControl key={parameter.name} fullWidth error={Boolean(error)}>
            <InputLabel>
              {parameter.name}
              {parameter.required && <span style={{ color: 'red' }}> *</span>}
            </InputLabel>
            <Select
              value={value || ''}
              onChange={(e) => onChange(parameter.name, e.target.value)}
              label={parameter.name + (parameter.required ? ' *' : '')}
            >
              {parameter.options?.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
            {parameter.description && !error && (
              <FormHelperText>{parameter.description}</FormHelperText>
            )}
            {error && <FormHelperText error>{error}</FormHelperText>}
          </FormControl>
        );

      case 'number':
      case 'integer':
        return (
          <TextField
            key={parameter.name}
            fullWidth
            type="number"
            label={parameter.name}
            value={value ?? ''}
            onChange={(e) => {
              const val = e.target.value;
              onChange(
                parameter.name,
                parameter.type === 'integer' ? parseInt(val, 10) : parseFloat(val)
              );
            }}
            required={parameter.required}
            error={Boolean(error)}
            helperText={error || parameter.description}
            inputProps={{
              min: parameter.validation?.min,
              max: parameter.validation?.max,
              step: parameter.type === 'integer' ? 1 : 'any',
            }}
          />
        );

      case 'string':
      default:
        const textFieldProps: any = {
          fullWidth: true,
          label: parameter.name,
          value: value ?? '',
          onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
            onChange(parameter.name, e.target.value),
          required: parameter.required,
          error: Boolean(error),
          helperText: error || parameter.description,
        };

        if (!parameter.validation?.pattern) {
          textFieldProps.multiline = false;
          textFieldProps.rows = 1;
        }

        if (parameter.name === 'sequences') {
          textFieldProps.multiline = true;
          textFieldProps.rows = Math.max(4, String(value ?? '').split('\n').length);
        }

        return <TextField key={parameter.name} {...textFieldProps} />;
    }
  };

  return (
    <Box
      component="form"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 3,
      }}
    >
      {parameters.map((parameter) => renderField(parameter))}
    </Box>
  );
};
