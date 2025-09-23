/**
 * Task API Type Definitions
 *
 * TypeScript interfaces that match the backend API schemas exactly,
 * ensuring type safety for all task-related API communications.
 */

// Core task types matching backend schemas
export interface TaskTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  subcategory?: string;
  version: string;
  engine: string;
  status: string;
  tags: string[];
  parameters: TaskParameter[];
  outputs?: TaskOutput[];
  execution_time_estimate?: number;
  resource_requirements?: ResourceRequirements;
  created_at: string;
  updated_at: string;
}

export interface TaskParameter {
  name: string;
  type: 'string' | 'number' | 'integer' | 'boolean' | 'file' | 'select';
  required: boolean;
  default?: any;
  description: string;
  options?: string[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    file_types?: string[];
    max_size_mb?: number;
    allowed_values?: string[];
  };
}

export interface TaskOutput {
  name: string;
  type: string;
  description: string;
  file_pattern?: string;
}

export interface ResourceRequirements {
  cpu_cores: number;
  memory_gb: number;
  disk_gb: number;
}

// API response types
export interface TaskListResponse {
  tasks: TaskTemplate[];
  total_count: number;
  organization_id: string;
}

export interface TaskDetailResponse {
  task: TaskTemplate;
  api_specification: Record<string, any>;
  service_configuration: Record<string, any>;
}

export interface ErrorResponse {
  error: string;
  message: string;
  code: number;
  details?: Record<string, any>;
}

// API request parameters
export interface TaskListParams {
  org_id?: string;
  category?: string;
  engine?: string;
  status?: string;
  search?: string;
  offset?: number;
  limit?: number;
}

export interface TaskDetailParams {
  task_id: string;
  org_id?: string;
}

export interface TaskCategoriesParams {
  org_id?: string;
}

// Service configuration types
export interface TaskServiceConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  fallbackEnabled: boolean;
  organizationId?: string;
}

// Feature flag types
export interface FeatureFlags {
  useApiTasks: boolean;
  enableTaskCache: boolean;
  debugMode: boolean;
}

// Error types
export class TaskApiError extends Error {
  constructor(
    public override message: string,
    public status?: number,
    public code?: string,
    public details?: any,
  ) {
    super(message);
    this.name = 'TaskApiError';
  }
}

export class TaskServiceError extends Error {
  constructor(
    public override message: string,
    public override cause?: Error,
  ) {
    super(message);
    this.name = 'TaskServiceError';
  }
}

// Service response types
export interface ServiceResponse<T> {
  data: T;
  source: 'api' | 'fallback' | 'cache';
  timestamp: number;
  error?: string;
}

// Cache types
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expires: number;
}

export interface TaskCache {
  tasks: CacheEntry<TaskTemplate[]> | null;
  categories: CacheEntry<string[]> | null;
  details: Map<string, CacheEntry<TaskTemplate>>;
}

// UI state types
export interface TaskLoadingState {
  isLoading: boolean;
  error: string | null;
  source: 'api' | 'fallback' | 'cache' | null;
}

export interface TaskFilters {
  search: string;
  category: string;
  complexity: string;
  tags: string[];
}

// Constants
export const TASK_CATEGORIES = ['autodock_vina', 'autodock4', 'schrodinger', 'custom'] as const;

export const TASK_COMPLEXITIES = ['beginner', 'intermediate', 'advanced'] as const;

export const RESOURCE_REQUIREMENTS = ['low', 'medium', 'high'] as const;

export type TaskCategory = (typeof TASK_CATEGORIES)[number];
export type TaskComplexity = (typeof TASK_COMPLEXITIES)[number];
export type ResourceRequirement = (typeof RESOURCE_REQUIREMENTS)[number];
