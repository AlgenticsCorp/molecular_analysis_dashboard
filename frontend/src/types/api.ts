/**
 * Type definitions for API responses and requests.
 *
 * This file contains all TypeScript interfaces and types used for
 * communication with the backend API, ensuring type safety throughout
 * the application.
 */

export interface User {
  user_id: string;
  email: string;
  org_id: string;
  roles: string[];
  created_at: string;
  updated_at: string;
}

export interface Organization {
  org_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Molecule {
  molecule_id: string;
  name: string;
  format: 'pdb' | 'sdf' | 'mol2' | 'pdbqt';
  uri: string;
  size_bytes: number;
  org_id: string;
  uploaded_by: string;
  created_at: string;
  updated_at: string;
}

export interface Pipeline {
  pipeline_id: string;
  name: string;
  description?: string;
  engine: 'vina' | 'smina' | 'gnina';
  parameters: Record<string, unknown>;
  is_active: boolean;
  org_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface DockingJob {
  job_id: string;
  pipeline_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  ligand_id: string;
  protein_id: string;
  parameters?: Record<string, unknown>;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  cache?: {
    hit: boolean;
    canonical_job_id?: string;
    confidence_score?: number;
  };
  org_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface DockingResult {
  result_id: string;
  job_id: string;
  binding_affinity: number;
  rmsd_lower_bound: number;
  rmsd_upper_bound: number;
  pose_rank: number;
  output_file_uri?: string;
  additional_metrics?: Record<string, unknown>;
  created_at: string;
}

export interface CreateJobRequest {
  pipeline_id: string;
  ligand_id: string;
  protein_id: string;
  parameters?: Record<string, unknown>;
}

export interface CreatePipelineRequest {
  name: string;
  description?: string;
  engine: 'vina' | 'smina' | 'gnina';
  parameters: Record<string, unknown>;
}

export interface UploadMoleculeRequest {
  name: string;
  format: 'pdb' | 'sdf' | 'mol2' | 'pdbqt';
  file: File;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  errors?: string[];
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HealthCheck {
  status: 'healthy' | 'unhealthy';
  database: 'connected' | 'disconnected';
  redis: 'connected' | 'disconnected';
  timestamp: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  org_id: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
  expires_in: number;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// UI-specific types
export interface TableColumn<T> {
  field: keyof T;
  headerName: string;
  width?: number;
  sortable?: boolean;
  filterable?: boolean;
  renderCell?: (value: T[keyof T], row: T) => React.ReactNode;
}

export interface FilterOption {
  value: string;
  label: string;
}

export interface DashboardStats {
  total_jobs: number;
  active_jobs: number;
  completed_jobs_today: number;
  failed_jobs_today: number;
  total_molecules: number;
  total_pipelines: number;
}

export type JobStatus = DockingJob['status'];
export type MoleculeFormat = Molecule['format'];
export type DockingEngine = Pipeline['engine'];
