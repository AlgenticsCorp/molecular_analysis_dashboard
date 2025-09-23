/**
 * React hooks for TaskService integration
 *
 * Provides React hooks that integrate with the TaskService for state management,
 * caching, and error handling in React components.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  TaskTemplate,
  TaskListParams,
  TaskDetailParams,
  TaskCategoriesParams,
  ServiceResponse,
  TaskServiceError,
} from '../types/tasks';
import { taskService } from '../services/taskService';
import { featureFlagService } from '../services/featureFlags';

// Hook state interfaces
export interface UseTasksState {
  tasks: TaskTemplate[];
  loading: boolean;
  error: string | null;
  source: 'api' | 'cache' | 'fallback' | null;
  lastUpdated: number | null;
}

export interface UseTaskDetailState {
  task: TaskTemplate | null;
  loading: boolean;
  error: string | null;
  source: 'api' | 'cache' | 'fallback' | null;
  lastUpdated: number | null;
}

export interface UseTaskCategoriesState {
  categories: string[];
  loading: boolean;
  error: string | null;
  source: 'api' | 'cache' | 'fallback' | null;
  lastUpdated: number | null;
}

/**
 * Hook for fetching tasks list with automatic refresh and caching
 */
export function useTasks(params?: TaskListParams, autoRefresh = false) {
  const [state, setState] = useState<UseTasksState>({
    tasks: [],
    loading: true,
    error: null,
    source: null,
    lastUpdated: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const paramsRef = useRef(params);
  paramsRef.current = params;

  const fetchTasks = useCallback(async (force = false) => {
    // Cancel previous request
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    setState((prev) => {
      // Check cache without causing re-render dependency
      if (!force && prev.source === 'cache' && Date.now() - (prev.lastUpdated || 0) < 60000) {
        return prev; // Use cached data if less than 1 minute old
      }
      return { ...prev, loading: true, error: null };
    });

    try {
      const response: ServiceResponse<TaskTemplate[]> = await taskService.getTasks(
        paramsRef.current,
      );

      setState({
        tasks: response.data,
        loading: false,
        error: null,
        source: response.source,
        lastUpdated: response.timestamp,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof TaskServiceError ? error.message : 'Failed to fetch tasks',
      }));
    }
  }, []); // Remove state dependencies to prevent infinite loops

  const refreshTasks = useCallback(() => {
    fetchTasks(true);
  }, [fetchTasks]);

  // Initial fetch
  useEffect(() => {
    fetchTasks();

    // Cleanup on unmount
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [fetchTasks]);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh || !featureFlagService.shouldUseApiTasks()) return;

    const interval = setInterval(
      () => {
        // Only refresh if data is stale (more than 5 minutes old)
        setState((prev) => {
          if (prev.lastUpdated && Date.now() - prev.lastUpdated > 5 * 60 * 1000) {
            fetchTasks();
          }
          return prev;
        });
      },
      5 * 60 * 1000,
    ); // Check every 5 minutes

    return () => clearInterval(interval);
  }, [autoRefresh]); // Only depend on autoRefresh flag

  // Feature flag change effect
  useEffect(() => {
    const unsubscribe = featureFlagService.subscribe(() => {
      if (featureFlagService.shouldUseApiTasks()) {
        fetchTasks(true); // Force refresh when API is enabled
      }
    });

    return unsubscribe;
  }, [fetchTasks]);

  return {
    ...state,
    refetch: refreshTasks,
    isStale: state.lastUpdated && Date.now() - state.lastUpdated > 5 * 60 * 1000,
  };
}

/**
 * Hook for fetching task details
 */
export function useTaskDetail(params: TaskDetailParams | null) {
  const [state, setState] = useState<UseTaskDetailState>({
    task: null,
    loading: false,
    error: null,
    source: null,
    lastUpdated: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchTaskDetail = useCallback(async (taskParams: TaskDetailParams) => {
    // Cancel previous request
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response: ServiceResponse<TaskTemplate> = await taskService.getTaskDetail(taskParams);

      setState({
        task: response.data,
        loading: false,
        error: null,
        source: response.source,
        lastUpdated: response.timestamp,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof TaskServiceError ? error.message : 'Failed to fetch task detail',
      }));
    }
  }, []);

  // Fetch when params change
  useEffect(() => {
    if (params) {
      fetchTaskDetail(params);
    } else {
      setState({
        task: null,
        loading: false,
        error: null,
        source: null,
        lastUpdated: null,
      });
    }

    // Cleanup on unmount
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [params, fetchTaskDetail]);

  // Feature flag change effect
  useEffect(() => {
    const unsubscribe = featureFlagService.subscribe(() => {
      if (featureFlagService.shouldUseApiTasks() && params) {
        fetchTaskDetail(params); // Re-fetch when API is enabled
      }
    });

    return unsubscribe;
  }, [params]); // Remove fetchTaskDetail dependency

  return {
    ...state,
    refetch: params ? () => fetchTaskDetail(params) : undefined,
  };
}

/**
 * Hook for fetching task categories
 */
export function useTaskCategories(params?: TaskCategoriesParams) {
  const [state, setState] = useState<UseTaskCategoriesState>({
    categories: [],
    loading: true,
    error: null,
    source: null,
    lastUpdated: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchCategories = useCallback(async () => {
    // Cancel previous request
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response: ServiceResponse<string[]> = await taskService.getTaskCategories(params);

      setState({
        categories: response.data,
        loading: false,
        error: null,
        source: response.source,
        lastUpdated: response.timestamp,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof TaskServiceError ? error.message : 'Failed to fetch categories',
      }));
    }
  }, [params]); // Only depend on params, not changing state

  // Initial fetch
  useEffect(() => {
    fetchCategories();

    // Cleanup on unmount
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [fetchCategories]);

  // Feature flag change effect
  useEffect(() => {
    const unsubscribe = featureFlagService.subscribe(() => {
      if (featureFlagService.shouldUseApiTasks()) {
        fetchCategories(); // Re-fetch when API is enabled
      }
    });

    return unsubscribe;
  }, []); // Remove fetchCategories dependency

  return {
    ...state,
    refetch: fetchCategories,
  };
}

/**
 * Hook for TaskService health monitoring
 */
export function useTaskServiceHealth() {
  const [health, setHealth] = useState<{
    available: boolean;
    latency?: number | undefined;
    error?: string | undefined;
    lastChecked: number | null;
  }>({
    available: false,
    lastChecked: null,
  });

  const checkHealth = useCallback(async () => {
    try {
      const result = await taskService.healthCheck();
      setHealth({
        available: result.available,
        latency: result.latency,
        error: result.error,
        lastChecked: Date.now(),
      });
    } catch (error) {
      setHealth({
        available: false,
        error: error instanceof Error ? error.message : 'Health check failed',
        lastChecked: Date.now(),
      });
    }
  }, []);

  // Check health on mount and periodically
  useEffect(() => {
    checkHealth();

    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [checkHealth]);

  return {
    ...health,
    checkHealth,
  };
}

/**
 * Hook for managing TaskService configuration
 */
export function useTaskServiceConfig() {
  const [config, setConfigState] = useState(taskService.getConfig());

  const updateConfig = useCallback((newConfig: Partial<typeof config>) => {
    taskService.updateConfig(newConfig);
    setConfigState(taskService.getConfig());
  }, []);

  const clearCache = useCallback(() => {
    taskService.clearCache();
  }, []);

  const cancelRequests = useCallback(() => {
    taskService.cancelRequests();
  }, []);

  return {
    config,
    updateConfig,
    clearCache,
    cancelRequests,
  };
}
