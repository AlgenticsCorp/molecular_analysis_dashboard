/**
 * Jobs API service for managing docking jobs.
 */

import { apiClient } from './client';
import type { DockingJob, CreateJobRequest, DockingResult, PaginatedResponse } from '@/types/api';

export const jobsApi = {
  /**
   * Get paginated list of docking jobs.
   */
  async getJobs(page = 1, pageSize = 25): Promise<PaginatedResponse<DockingJob>> {
    const response = await apiClient.get<PaginatedResponse<DockingJob>>('/jobs', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Get recent jobs for dashboard.
   */
  async getRecentJobs(limit = 10): Promise<DockingJob[]> {
    const response = await apiClient.get<DockingJob[]>('/jobs/recent', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Get job by ID.
   */
  async getJob(jobId: string): Promise<DockingJob> {
    const response = await apiClient.get<DockingJob>(`/jobs/${jobId}`);
    return response.data;
  },

  /**
   * Create new docking job.
   */
  async createJob(jobData: CreateJobRequest): Promise<DockingJob> {
    const response = await apiClient.post<DockingJob>('/jobs', jobData);
    return response.data;
  },

  /**
   * Get job results.
   */
  async getJobResults(jobId: string): Promise<DockingResult[]> {
    const response = await apiClient.get<DockingResult[]>(`/jobs/${jobId}/results`);
    return response.data;
  },

  /**
   * Cancel running job.
   */
  async cancelJob(jobId: string): Promise<void> {
    await apiClient.post(`/jobs/${jobId}/cancel`);
  },

  /**
   * Delete job and its results.
   */
  async deleteJob(jobId: string): Promise<void> {
    await apiClient.delete(`/jobs/${jobId}`);
  },
};
