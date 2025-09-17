/**
 * Dashboard API service for fetching dashboard statistics and data.
 */

import { apiClient } from './client';
import type { DashboardStats } from '@/types/api';

export const dashboardApi = {
  /**
   * Get dashboard statistics including job counts and metrics.
   */
  async getStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },

  /**
   * Get system health status.
   */
  async getHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await apiClient.get<{ status: string; timestamp: string }>('/health');
    return response.data;
  },
};
