/**
 * Task Service with API Client and Fallback Mechanism
 *
 * Provides a unified interface for accessing task data with automatic
 * fallback to static data when the API is unavailable. Includes caching,
 * error handling, and retry logic.
 */

import {
  TaskTemplate,
  TaskListResponse,
  TaskDetailResponse,
  TaskListParams,
  TaskDetailParams,
  TaskCategoriesParams,
  TaskServiceConfig,
  TaskApiError,
  TaskServiceError,
  ServiceResponse,
  TaskCache,
  CacheEntry,
} from '../types/tasks';
import { featureFlagService } from './featureFlags';

// Static fallback data
import { getStaticTaskTemplates, getStaticTaskCategories } from './staticTaskData';

export class TaskService {
  private config: TaskServiceConfig;
  private cache: TaskCache;
  private abortController: AbortController | null = null;

  constructor(config?: Partial<TaskServiceConfig>) {
    this.config = {
      baseUrl: '/api/v1/tasks',
      timeout: 10000,
      retries: 3,
      fallbackEnabled: true,
      ...config,
    };

    this.cache = {
      tasks: null,
      categories: null,
      details: new Map(),
    };
  }

  /**
   * Get list of tasks with fallback support.
   */
  async getTasks(params?: TaskListParams): Promise<ServiceResponse<TaskTemplate[]>> {
    // Try cache first if enabled
    if (featureFlagService.isCacheEnabled()) {
      const cached = this.getFromCache<TaskTemplate[]>('tasks');
      if (cached) {
        return {
          data: cached,
          source: 'cache',
          timestamp: Date.now(),
        };
      }
    }

    // Try API if enabled
    if (featureFlagService.shouldUseApiTasks()) {
      try {
        const apiResponse = await this.fetchTasksFromApi(params);

        // Cache successful response
        if (featureFlagService.isCacheEnabled()) {
          this.setCache('tasks', apiResponse.tasks);
        }

        return {
          data: apiResponse.tasks,
          source: 'api',
          timestamp: Date.now(),
        };
      } catch (error) {
        console.warn('API request failed, falling back to static data:', error);

        if (!this.config.fallbackEnabled) {
          throw new TaskServiceError('API failed and fallback disabled', error as Error);
        }
      }
    }

    // Fallback to static data
    const staticTasks = getStaticTaskTemplates(params);
    return {
      data: staticTasks,
      source: 'fallback',
      timestamp: Date.now(),
    };
  }

  /**
   * Get task details with fallback support.
   */
  async getTaskDetail(params: TaskDetailParams): Promise<ServiceResponse<TaskTemplate>> {
    // Try cache first if enabled
    if (featureFlagService.isCacheEnabled()) {
      const cached = this.getFromCache<TaskTemplate>('details', params.task_id);
      if (cached) {
        return {
          data: cached,
          source: 'cache',
          timestamp: Date.now(),
        };
      }
    }

    // Try API if enabled
    if (featureFlagService.shouldUseApiTasks()) {
      try {
        const apiResponse = await this.fetchTaskDetailFromApi(params);

        // Cache successful response
        if (featureFlagService.isCacheEnabled()) {
          this.setCache('details', apiResponse.task, params.task_id);
        }

        return {
          data: apiResponse.task,
          source: 'api',
          timestamp: Date.now(),
        };
      } catch (error) {
        console.warn('API request failed, falling back to static data:', error);

        if (!this.config.fallbackEnabled) {
          throw new TaskServiceError('API failed and fallback disabled', error as Error);
        }
      }
    }

    // Fallback to static data
    const staticTask = getStaticTaskTemplates().find(
      (task: TaskTemplate) => task.id === params.task_id,
    );

    if (!staticTask) {
      throw new TaskServiceError(`Task not found: ${params.task_id}`);
    }

    return {
      data: staticTask,
      source: 'fallback',
      timestamp: Date.now(),
    };
  }

  /**
   * Get task categories with fallback support.
   */
  async getTaskCategories(params?: TaskCategoriesParams): Promise<ServiceResponse<string[]>> {
    // Try cache first if enabled
    if (featureFlagService.isCacheEnabled()) {
      const cached = this.getFromCache<string[]>('categories');
      if (cached) {
        return {
          data: cached,
          source: 'cache',
          timestamp: Date.now(),
        };
      }
    }

    // Try API if enabled
    if (featureFlagService.shouldUseApiTasks()) {
      try {
        const apiResponse = await this.fetchCategoriesFromApi(params);

        // Cache successful response
        if (featureFlagService.isCacheEnabled()) {
          this.setCache('categories', apiResponse);
        }

        return {
          data: apiResponse,
          source: 'api',
          timestamp: Date.now(),
        };
      } catch (error) {
        console.warn('API request failed, falling back to static data:', error);

        if (!this.config.fallbackEnabled) {
          throw new TaskServiceError('API failed and fallback disabled', error as Error);
        }
      }
    }

    // Fallback to static data
    const staticCategories = getStaticTaskCategories();
    return {
      data: staticCategories,
      source: 'fallback',
      timestamp: Date.now(),
    };
  }

  /**
   * Fetch tasks from API with retry logic.
   */
  private async fetchTasksFromApi(params?: TaskListParams): Promise<TaskListResponse> {
    const url = new URL(this.config.baseUrl, window.location.origin);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return this.fetchWithRetry(url.toString());
  }

  /**
   * Fetch task detail from API.
   */
  private async fetchTaskDetailFromApi(params: TaskDetailParams): Promise<TaskDetailResponse> {
    const url = new URL(`${this.config.baseUrl}/${params.task_id}`, window.location.origin);

    if (params.org_id) {
      url.searchParams.append('org_id', params.org_id);
    }

    return this.fetchWithRetry(url.toString());
  }

  /**
   * Fetch categories from API.
   */
  private async fetchCategoriesFromApi(params?: TaskCategoriesParams): Promise<string[]> {
    const url = new URL(`${this.config.baseUrl}/categories`, window.location.origin);

    if (params?.org_id) {
      url.searchParams.append('org_id', params.org_id);
    }

    return this.fetchWithRetry(url.toString());
  }

  /**
   * Fetch with retry logic and timeout.
   */
  private async fetchWithRetry<T>(url: string, attempt = 1): Promise<T> {
    this.abortController = new AbortController();

    const timeoutId = setTimeout(() => {
      this.abortController?.abort();
    }, this.config.timeout);

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        signal: this.abortController.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new TaskApiError(
          errorData?.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData?.code,
          errorData,
        );
      }

      const data = await response.json();

      if (featureFlagService.isDebugMode()) {
        console.log('API response:', { url, attempt, data });
      }

      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof TaskApiError) {
        throw error;
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new TaskApiError('Request timeout', 408);
      }

      // Retry on network errors
      if (attempt < this.config.retries && this.isRetryableError(error as Error)) {
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
        await new Promise((resolve) => setTimeout(resolve, delay));
        return this.fetchWithRetry(url, attempt + 1);
      }

      throw new TaskApiError(
        error instanceof Error ? error.message : 'Network error',
        0,
        'NETWORK_ERROR',
        error,
      );
    }
  }

  /**
   * Check if error is retryable.
   */
  private isRetryableError(error: Error): boolean {
    // Retry on network errors, but not on 4xx client errors
    return !(
      error instanceof TaskApiError &&
      error.status &&
      error.status >= 400 &&
      error.status < 500
    );
  }

  /**
   * Get data from cache.
   */
  private getFromCache<T>(type: 'tasks' | 'categories'): T | null;
  private getFromCache<T>(type: 'details', key: string): T | null;
  private getFromCache<T>(type: 'tasks' | 'categories' | 'details', key?: string): T | null {
    const now = Date.now();

    if (type === 'details' && key) {
      const entry = this.cache.details.get(key);
      if (entry && entry.expires > now) {
        return entry.data as T;
      }
      return null;
    }

    const entry = this.cache[type as 'tasks' | 'categories'];
    if (entry && entry.expires > now) {
      return entry.data as T;
    }

    return null;
  }

  /**
   * Set data in cache.
   */
  private setCache(type: 'tasks', data: TaskTemplate[]): void;
  private setCache(type: 'categories', data: string[]): void;
  private setCache(type: 'details', data: TaskTemplate, key: string): void;
  private setCache(type: 'tasks' | 'categories' | 'details', data: any, key?: string): void {
    const now = Date.now();
    const expires = now + 5 * 60 * 1000; // 5 minutes cache

    if (type === 'details' && key) {
      const entry: CacheEntry<TaskTemplate> = {
        data: data as TaskTemplate,
        timestamp: now,
        expires,
      };
      this.cache.details.set(key, entry);
      return;
    }

    const entry = {
      data,
      timestamp: now,
      expires,
    };

    (this.cache as any)[type] = entry;
  }

  /**
   * Clear cache.
   */
  clearCache(): void {
    this.cache = {
      tasks: null,
      categories: null,
      details: new Map(),
    };
  }

  /**
   * Cancel any pending requests.
   */
  cancelRequests(): void {
    this.abortController?.abort();
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<TaskServiceConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get current configuration.
   */
  getConfig(): TaskServiceConfig {
    return { ...this.config };
  }

  /**
   * Health check for API availability.
   */
  async healthCheck(): Promise<{ available: boolean; latency?: number; error?: string }> {
    const start = Date.now();

    try {
      await this.fetchWithRetry(`${this.config.baseUrl}/../health`);
      return {
        available: true,
        latency: Date.now() - start,
      };
    } catch (error) {
      return {
        available: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}

// Global service instance
export const taskService = new TaskService();
