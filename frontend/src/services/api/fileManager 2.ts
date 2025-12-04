import type { AxiosRequestConfig } from 'axios';
import { apiClient } from './client';
import type {
  PaginatedFilesResponse,
  StorageStats,
  UploadUserFileResponse,
} from '@/types/fileManager';

export interface ListFilesParams {
  userId: string;
  format?: string;
  category?: string;
  search?: string;
  tags?: string[];
  sortBy?: string;
  order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

const tasksUnifiedDownloadPath = (fileId: string): string =>
  `/tasks-unified/files/${fileId}/download`;

export const fileManagerApi = {
  async listFiles(params: ListFilesParams): Promise<PaginatedFilesResponse> {
    const { userId, tags, sortBy, order, ...rest } = params;

    const queryParams: Record<string, unknown> = {
      user_id: userId,
      ...rest,
    };

    if (tags && tags.length) {
      queryParams['tags'] = tags.join(',');
    }

    if (sortBy) {
      queryParams['sort_by'] = sortBy;
    }

    if (order) {
      queryParams['order'] = order;
    }

    const response = await apiClient.get<PaginatedFilesResponse>('/files', {
      params: queryParams,
    });
    return response.data;
  },

  async getStorageStats(userId: string): Promise<StorageStats> {
    const response = await apiClient.get<StorageStats>('/files/stats', {
      params: { user_id: userId },
    });
    return response.data;
  },

  async uploadFile(formData: FormData, config?: AxiosRequestConfig): Promise<UploadUserFileResponse> {
    const response = await apiClient.upload<UploadUserFileResponse>('/files', formData, config);
    return response.data;
  },

  async deleteFile(fileId: string, userId: string): Promise<void> {
    await apiClient.delete(`/files/${fileId}`, {
      params: { user_id: userId },
    });
  },

  async downloadFile(fileId: string, filename: string): Promise<void> {
    const response = await apiClient.download(tasksUnifiedDownloadPath(fileId));
    const blob = response.data;
    const downloadUrl = window.URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  },

  async fetchFileContent(fileId: string): Promise<string> {
    const response = await apiClient.download(tasksUnifiedDownloadPath(fileId), {
      headers: { Accept: 'text/plain' },
    });

    return response.data.text();
  },
};
