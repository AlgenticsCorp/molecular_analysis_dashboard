-- Migration: Add execution_files table for proper file storage
-- Date: 2025-11-13
-- Purpose: Separate file storage from input_data JSONB to fix database bloat and enable scalable file handling

-- Create execution_files table
CREATE TABLE IF NOT EXISTS execution_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES task_framework_executions(execution_id) ON DELETE CASCADE,
    
    -- File classification
    parameter_name VARCHAR(100) NOT NULL,  -- e.g., 'receptor_file', 'ligand_file'
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('input', 'output')),
    
    -- File metadata
    filename VARCHAR(255) NOT NULL,
    size_bytes BIGINT NOT NULL,
    content_type VARCHAR(100),
    
    -- Storage location
    storage_backend VARCHAR(50) NOT NULL,  -- 'local', 's3', 'minio', 'neurosnap_cloud'
    storage_path TEXT NOT NULL,            -- e.g., '/uploads/{org_id}/{exec_id}/receptor.pdb'
    download_url TEXT,                     -- For external files (NeuroSnap results)
    
    -- Checksums for integrity verification
    md5_hash VARCHAR(32),
    sha256_hash VARCHAR(64),
    
    -- Timestamps
    uploaded_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,                  -- For temporary files and cleanup policies
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure no duplicate file entries per execution
    UNIQUE(execution_id, parameter_name, file_type)
);

-- Indexes for performance
CREATE INDEX idx_execution_files_execution ON execution_files(execution_id);
CREATE INDEX idx_execution_files_type ON execution_files(execution_id, file_type);
CREATE INDEX idx_execution_files_expires ON execution_files(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_execution_files_storage_backend ON execution_files(storage_backend);

-- Add comments for documentation
COMMENT ON TABLE execution_files IS 'Stores metadata and references for input/output files associated with task executions. Actual file content is stored in the configured storage backend (local/S3/MinIO).';
COMMENT ON COLUMN execution_files.file_id IS 'Unique identifier for the file record';
COMMENT ON COLUMN execution_files.execution_id IS 'Reference to the task execution this file belongs to';
COMMENT ON COLUMN execution_files.parameter_name IS 'Name of the parameter from task definition (e.g., receptor_file, ligand_file)';
COMMENT ON COLUMN execution_files.file_type IS 'Whether this is an input file (user upload) or output file (result)';
COMMENT ON COLUMN execution_files.storage_backend IS 'Storage system where file is stored: local (nginx), s3 (AWS S3), minio, or neurosnap_cloud (external)';
COMMENT ON COLUMN execution_files.storage_path IS 'Path to file in storage backend, e.g., /uploads/org-id/exec-id/filename';
COMMENT ON COLUMN execution_files.download_url IS 'Direct download URL for external files (NeuroSnap results)';
COMMENT ON COLUMN execution_files.md5_hash IS 'MD5 checksum for file integrity verification';
COMMENT ON COLUMN execution_files.sha256_hash IS 'SHA256 checksum for enhanced security and integrity';
COMMENT ON COLUMN execution_files.expires_at IS 'When to delete this file (NULL = keep forever)';

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_execution_files_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic updated_at
CREATE TRIGGER execution_files_updated_at_trigger
    BEFORE UPDATE ON execution_files
    FOR EACH ROW
    EXECUTE FUNCTION update_execution_files_updated_at();

-- Grant permissions (adjust role names as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON execution_files TO molecular_analysis_app;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 20251113_execution_files_table completed successfully';
    RAISE NOTICE 'Created execution_files table with indexes and triggers';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Update unified_task_service.py to use FileStorageAdapter';
    RAISE NOTICE '  2. Update neurosnap_task_adapter.py to fetch files from execution_files';
    RAISE NOTICE '  3. Remove base64 encoding from input_data JSONB';
END $$;
