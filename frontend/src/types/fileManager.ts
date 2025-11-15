export interface FileValidationSummary {
  is_valid: boolean;
  has_mol_block?: boolean;
  has_atom_count?: boolean;
  molecule_count?: number;
  atom_count?: number;
  bond_count?: number;
  has_coordinates?: boolean;
  has_m_end?: boolean;
  format?: string;
  errors?: string[];
  warnings?: string[];
}

export interface UserFileRecord {
  file_id: string;
  filename: string;
  size_bytes: number;
  content_type: string | null;
  storage_backend: string;
  storage_path: string;
  md5_hash: string;
  sha256_hash: string;
  uploaded_at: string;
  description: string | null;
  tags: string[];
  file_category: string;
  is_public: boolean;
  created_by: string | null;
  user_id: string | null;
  download_url?: string | null;
  original_filename?: string | null;
  file_format?: string | null;
  validation?: FileValidationSummary | null;
}

export interface PaginatedFilesResponse {
  total_files: number;
  page: number;
  limit: number;
  total_pages: number;
  files: UserFileRecord[];
}

export interface StorageStats {
  total_files: number;
  total_size_bytes: number;
  files_by_format: Record<string, number>;
  storage_by_format: Record<string, number>;
  files_by_category: Record<string, { file_count: number; total_size_bytes: number }>;
}

export interface UploadUserFileResponse {
  success: boolean;
  message?: string;
  file: UserFileRecord;
}
