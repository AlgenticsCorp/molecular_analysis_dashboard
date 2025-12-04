import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Chip,
  Collapse,
  Divider,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  CloudDownload,
  CloudUpload,
  Description,
  Download,
  ExpandLess,
  ExpandMore,
  Folder,
  FolderOpen,
} from '@mui/icons-material';

export interface JobFile {
  name: string;
  size: string;
  sizeBytes?: number;
  url?: string;
  fileId?: string;
  parameterName?: string;
  storageBackend?: string;
  contentType?: string;
}

interface JobFilesTreeJob {
  id: string;
  name: string;
  status: string;
  endTime?: string;
  inputFiles: JobFile[];
  outputFiles: JobFile[];
}

export interface SelectedJobFile {
  nodeId: string;
  jobId: string;
  jobName: string;
  fileType: 'input' | 'output';
  file: JobFile;
}

interface JobFilesTreeProps {
  jobs: JobFilesTreeJob[];
  onSelectFile: (selection: SelectedJobFile) => void;
  onDownloadFile: (file: JobFile) => void;
  selectedNodeId?: string | null;
}

const formatCompletedAt = (endTime?: string): string | undefined => {
  if (!endTime) {
    return undefined;
  }

  const date = new Date(endTime);
  if (Number.isNaN(date.getTime())) {
    return undefined;
  }

  return date.toLocaleString();
};

export const JobFilesTree: React.FC<JobFilesTreeProps> = ({
  jobs,
  onSelectFile,
  onDownloadFile,
  selectedNodeId,
}) => {
  const jobsWithFiles = useMemo(
    () => jobs.filter((job) => job.inputFiles.length > 0 || job.outputFiles.length > 0),
    [jobs],
  );

  const [expandedNodes, setExpandedNodes] = useState<string[]>([]);

  useEffect(() => {
    if (jobsWithFiles.length === 0) {
      setExpandedNodes([]);
      return;
    }

    const firstJob = jobsWithFiles[0];
    if (!firstJob) {
      return;
    }

    // Expand the first job node by default when data changes
    setExpandedNodes((prev) => {
      if (prev.length === 0) {
        return [`job-${firstJob.id}`];
      }
      return prev;
    });
  }, [jobsWithFiles]);

  const isExpanded = (nodeId: string): boolean => expandedNodes.includes(nodeId);

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) =>
      prev.includes(nodeId) ? prev.filter((id) => id !== nodeId) : [...prev, nodeId],
    );
  };

  if (jobsWithFiles.length === 0) {
    return (
      <Box sx={{ py: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Completed jobs with files will appear here once available.
        </Typography>
      </Box>
    );
  }

  return (
    <List disablePadding sx={{ width: '100%' }}>
      {jobsWithFiles.map((job, jobIndex) => {
        const jobNodeId = `job-${job.id}`;
        const inputNodeId = `${jobNodeId}-inputs`;
        const outputNodeId = `${jobNodeId}-outputs`;
        const completedLabel = formatCompletedAt(job.endTime);

        return (
          <Box key={job.id}>
            <ListItemButton onClick={() => toggleNode(jobNodeId)} sx={{ borderRadius: 1 }}>
              <ListItemIcon sx={{ minWidth: 36 }}>
                {isExpanded(jobNodeId) ? <FolderOpen color="primary" /> : <Folder color="primary" />}
              </ListItemIcon>
              <ListItemText
                primary={job.name}
                secondary={completedLabel ? `Completed ${completedLabel}` : undefined}
              />
              <Chip
                label={job.status}
                size="small"
                sx={{ mr: 1, textTransform: 'capitalize' }}
                color={job.status === 'completed' ? 'success' : job.status === 'failed' ? 'error' : 'default'}
              />
              {isExpanded(jobNodeId) ? <ExpandLess /> : <ExpandMore />}
            </ListItemButton>
            <Collapse in={isExpanded(jobNodeId)} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {job.inputFiles.length > 0 && (
                  <>
                    <ListItemButton sx={{ pl: 4 }} onClick={() => toggleNode(inputNodeId)}>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <CloudUpload fontSize="small" color="info" />
                      </ListItemIcon>
                      <ListItemText primary="Input Files" />
                      {isExpanded(inputNodeId) ? <ExpandLess /> : <ExpandMore />}
                    </ListItemButton>
                    <Collapse in={isExpanded(inputNodeId)} timeout="auto" unmountOnExit>
                      <List component="div" disablePadding>
                        {job.inputFiles.map((file, index) => {
                          const nodeId = `${jobNodeId}-input-${index}`;
                          return (
                            <ListItemButton
                              key={nodeId}
                              sx={{ pl: 6 }}
                              selected={selectedNodeId === nodeId}
                              onClick={() =>
                                onSelectFile({
                                  nodeId,
                                  jobId: job.id,
                                  jobName: job.name,
                                  fileType: 'input',
                                  file,
                                })
                              }
                            >
                              <ListItemIcon sx={{ minWidth: 36 }}>
                                <Description fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary={file.name} secondary={file.size} />
                              <Tooltip title="Download file">
                                <span>
                                  <IconButton
                                    size="small"
                                    onClick={(event) => {
                                      event.stopPropagation();
                                      onDownloadFile(file);
                                    }}
                                    disabled={!file.fileId && !file.url}
                                  >
                                    <Download fontSize="small" />
                                  </IconButton>
                                </span>
                              </Tooltip>
                            </ListItemButton>
                          );
                        })}
                      </List>
                    </Collapse>
                  </>
                )}
                {job.outputFiles.length > 0 && (
                  <>
                    <ListItemButton sx={{ pl: 4 }} onClick={() => toggleNode(outputNodeId)}>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <CloudDownload fontSize="small" color="success" />
                      </ListItemIcon>
                      <ListItemText primary="Output Files" />
                      {isExpanded(outputNodeId) ? <ExpandLess /> : <ExpandMore />}
                    </ListItemButton>
                    <Collapse in={isExpanded(outputNodeId)} timeout="auto" unmountOnExit>
                      <List component="div" disablePadding>
                        {job.outputFiles.map((file, index) => {
                          const nodeId = `${jobNodeId}-output-${index}`;
                          return (
                            <ListItemButton
                              key={nodeId}
                              sx={{ pl: 6 }}
                              selected={selectedNodeId === nodeId}
                              onClick={() =>
                                onSelectFile({
                                  nodeId,
                                  jobId: job.id,
                                  jobName: job.name,
                                  fileType: 'output',
                                  file,
                                })
                              }
                            >
                              <ListItemIcon sx={{ minWidth: 36 }}>
                                <Description fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary={file.name} secondary={file.size} />
                              <Tooltip title="Download file">
                                <span>
                                  <IconButton
                                    size="small"
                                    onClick={(event) => {
                                      event.stopPropagation();
                                      onDownloadFile(file);
                                    }}
                                    disabled={!file.fileId && !file.url}
                                  >
                                    <Download fontSize="small" />
                                  </IconButton>
                                </span>
                              </Tooltip>
                            </ListItemButton>
                          );
                        })}
                      </List>
                    </Collapse>
                  </>
                )}
              </List>
            </Collapse>
            {jobIndex < jobsWithFiles.length - 1 && <Divider sx={{ my: 1 }} />}
          </Box>
        );
      })}
    </List>
  );
};

export default JobFilesTree;
