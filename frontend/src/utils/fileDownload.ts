/**
 * Utility functions for handling file downloads
 */

/**
 * Download a file using the API endpoint
 * @param fileId - The file_id from the database
 * @param filename - The filename to save as
 */
export const downloadFileById = async (fileId: string, filename: string): Promise<void> => {
  try {
    const response = await fetch(`/api/v1/tasks-unified/files/${fileId}/download`);
    
    if (!response.ok) {
      // Check if it's a 400 error (likely expired NeuroSnap URL)
      if (response.status === 400) {
        throw new Error('File download link has expired. Please re-run the job to generate fresh results.');
      }
      throw new Error(`Failed to download file: ${response.statusText} (${response.status})`);
    }

    const blob = await response.blob();
    
    // Check if the blob is empty or very small (error response)
    if (blob.size < 100) {
      const text = await blob.text();
      if (text.includes('Unknown job ID') || text.includes('expired')) {
        throw new Error('File download link has expired. Please re-run the job to generate fresh results.');
      }
    }
    
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('Error downloading file:', error);
    throw error;
  }
};

/**
 * Download a file from a URL (legacy method - use downloadFileById instead)
 * Handles both local storage URLs and external URLs (like NeuroSnap)
 */
export const downloadFile = async (url: string, filename: string): Promise<void> => {
  try {
    // For external URLs (NeuroSnap), open in new tab
    if (url.startsWith('https://neurosnap.ai')) {
      window.open(url, '_blank', 'noopener,noreferrer');
      return;
    }

    // For local files, fetch and trigger download
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('Error downloading file:', error);
    throw error;
  }
};

/**
 * Format file size from bytes to human-readable format
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

/**
 * Get file extension from filename
 */
export const getFileExtension = (filename: string): string => {
  const parts = filename.split('.');
  const lastPart = parts[parts.length - 1];
  return parts.length > 1 && lastPart ? lastPart.toLowerCase() : '';
};

/**
 * Determine if file is viewable in browser
 */
export const isViewableFile = (filename: string): boolean => {
  const viewableExtensions = ['txt', 'csv', 'json', 'xml', 'html', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg'];
  const ext = getFileExtension(filename);
  return viewableExtensions.includes(ext);
};

/**
 * Convert internal storage URL to gateway URL for frontend access
 */
export const convertStorageUrl = (url: string): string => {
  // If URL starts with http://storage:8080, convert to use gateway
  if (url.startsWith('http://storage:8080')) {
    return url.replace('http://storage:8080', '');
  }
  return url;
};
