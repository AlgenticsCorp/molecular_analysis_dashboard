-- Migration: Extend execution_files table for File Manager support
-- Date: 2025-11-14
-- Purpose: Enable standalone file uploads independent of task executions
--          Add user ownership, categorization, and enhanced metadata

-- ============================================================================
-- STEP 1: Make execution_id nullable to support standalone files
-- ============================================================================

-- Drop the NOT NULL constraint on execution_id
ALTER TABLE execution_files 
    ALTER COLUMN execution_id DROP NOT NULL;

COMMENT ON COLUMN execution_files.execution_id IS 'Reference to task execution (NULL for standalone user-uploaded files)';

-- ============================================================================
-- STEP 2: Add new columns for file management
-- ============================================================================

-- User ownership and metadata
ALTER TABLE execution_files
    ADD COLUMN IF NOT EXISTS user_id UUID,
    ADD COLUMN IF NOT EXISTS file_category VARCHAR(50) DEFAULT 'molecular_structure',
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS tags TEXT[],
    ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS created_by VARCHAR(255);

-- Add comments for new columns
COMMENT ON COLUMN execution_files.user_id IS 'User who owns this file (for multi-user support)';
COMMENT ON COLUMN execution_files.file_category IS 'File category: molecular_structure, docking_result, analysis_output, etc.';
COMMENT ON COLUMN execution_files.description IS 'User-provided description of the file';
COMMENT ON COLUMN execution_files.tags IS 'Array of tags for categorization and search';
COMMENT ON COLUMN execution_files.is_public IS 'Whether file is publicly accessible (for sharing)';
COMMENT ON COLUMN execution_files.created_by IS 'Email or username of creator (for audit trail)';

-- ============================================================================
-- STEP 3: Update constraints and indexes
-- ============================================================================

-- Drop the old unique constraint
ALTER TABLE execution_files
    DROP CONSTRAINT IF EXISTS execution_files_execution_id_parameter_name_file_type_key;

-- Create partial unique index for execution-bound files
-- This allows multiple files with same parameter_name for different executions
CREATE UNIQUE INDEX IF NOT EXISTS idx_execution_files_execution_context 
    ON execution_files(execution_id, parameter_name, file_type) 
    WHERE execution_id IS NOT NULL;

-- Ensure standalone files have unique file_id (this is already enforced by PRIMARY KEY)
-- But add index for faster queries
CREATE INDEX IF NOT EXISTS idx_execution_files_standalone 
    ON execution_files(file_id) 
    WHERE execution_id IS NULL;

-- Add index for user queries (critical for file manager listing)
CREATE INDEX IF NOT EXISTS idx_execution_files_user_id 
    ON execution_files(user_id) 
    WHERE user_id IS NOT NULL;

-- Add index for category filtering
CREATE INDEX IF NOT EXISTS idx_execution_files_category 
    ON execution_files(file_category);

-- Add index for uploaded_at (for sorting by date)
CREATE INDEX IF NOT EXISTS idx_execution_files_uploaded_at 
    ON execution_files(uploaded_at DESC);

-- Add GIN index for full-text search on tags
CREATE INDEX IF NOT EXISTS idx_execution_files_tags 
    ON execution_files USING GIN(tags);

-- Add composite index for common file manager queries
CREATE INDEX IF NOT EXISTS idx_execution_files_user_category_uploaded 
    ON execution_files(user_id, file_category, uploaded_at DESC) 
    WHERE user_id IS NOT NULL;

-- ============================================================================
-- STEP 4: Add check constraints
-- ============================================================================

-- Ensure standalone files have proper metadata
ALTER TABLE execution_files
    ADD CONSTRAINT check_standalone_file_metadata 
    CHECK (
        -- If execution_id is NULL (standalone file), must have user_id
        (execution_id IS NOT NULL) OR 
        (execution_id IS NULL AND user_id IS NOT NULL)
    );

-- Ensure file_category is valid
ALTER TABLE execution_files
    ADD CONSTRAINT check_file_category 
    CHECK (
        file_category IN (
            'molecular_structure',
            'docking_result', 
            'analysis_output',
            'protein_structure',
            'ligand_structure',
            'trajectory',
            'simulation',
            'other'
        )
    );

-- ============================================================================
-- STEP 5: Create helper functions
-- ============================================================================

-- Function to get storage statistics for a user
CREATE OR REPLACE FUNCTION get_user_storage_stats(p_user_id UUID)
RETURNS TABLE (
    total_files BIGINT,
    total_size_bytes BIGINT,
    files_by_format JSONB,
    storage_by_format JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_files,
        COALESCE(SUM(size_bytes), 0)::BIGINT as total_size_bytes,
        jsonb_object_agg(
            COALESCE(
                CASE 
                    WHEN filename LIKE '%.pdb' THEN 'pdb'
                    WHEN filename LIKE '%.pdbqt' THEN 'pdbqt'
                    WHEN filename LIKE '%.sdf' THEN 'sdf'
                    WHEN filename LIKE '%.mol2' THEN 'mol2'
                    WHEN filename LIKE '%.xyz' THEN 'xyz'
                    ELSE 'other'
                END,
                'other'
            ),
            file_count
        ) as files_by_format,
        jsonb_object_agg(
            COALESCE(
                CASE 
                    WHEN filename LIKE '%.pdb' THEN 'pdb'
                    WHEN filename LIKE '%.pdbqt' THEN 'pdbqt'
                    WHEN filename LIKE '%.sdf' THEN 'sdf'
                    WHEN filename LIKE '%.mol2' THEN 'mol2'
                    WHEN filename LIKE '%.xyz' THEN 'xyz'
                    ELSE 'other'
                END,
                'other'
            ),
            total_size
        ) as storage_by_format
    FROM (
        SELECT 
            filename,
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size
        FROM execution_files
        WHERE user_id = p_user_id
        GROUP BY filename
    ) format_stats;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_storage_stats(UUID) IS 'Calculate storage statistics for a user including file counts and sizes by format';

-- Function to clean up orphaned files
CREATE OR REPLACE FUNCTION cleanup_orphaned_files(p_days_old INTEGER DEFAULT 30)
RETURNS TABLE (
    deleted_count INTEGER,
    freed_bytes BIGINT
) AS $$
DECLARE
    v_deleted_count INTEGER;
    v_freed_bytes BIGINT;
BEGIN
    -- Delete files that:
    -- 1. Have expires_at set and are expired
    -- 2. OR are orphaned (execution deleted, no user_id, older than p_days_old)
    WITH deleted_files AS (
        DELETE FROM execution_files
        WHERE 
            -- Expired files
            (expires_at IS NOT NULL AND expires_at < NOW())
            OR
            -- Orphaned files: no execution, no user, old
            (
                execution_id IS NULL 
                AND user_id IS NULL 
                AND uploaded_at < NOW() - INTERVAL '1 day' * p_days_old
            )
        RETURNING file_id, size_bytes
    )
    SELECT 
        COUNT(*)::INTEGER,
        COALESCE(SUM(size_bytes), 0)::BIGINT
    INTO v_deleted_count, v_freed_bytes
    FROM deleted_files;
    
    RETURN QUERY SELECT v_deleted_count, v_freed_bytes;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_orphaned_files(INTEGER) IS 'Clean up expired and orphaned files, returns count and bytes freed';

-- ============================================================================
-- STEP 6: Update existing data
-- ============================================================================

-- For existing execution-bound files, set category based on file_type
UPDATE execution_files
SET file_category = CASE 
    WHEN file_type = 'input' THEN 'molecular_structure'
    WHEN file_type = 'output' THEN 'docking_result'
    ELSE 'other'
END
WHERE file_category = 'molecular_structure'  -- Only update default values
  AND execution_id IS NOT NULL;  -- Only update execution-bound files

-- ============================================================================
-- STEP 7: Grant permissions
-- ============================================================================

-- Grant permissions to application role
GRANT EXECUTE ON FUNCTION get_user_storage_stats(UUID) TO molecular_analysis_app;
GRANT EXECUTE ON FUNCTION cleanup_orphaned_files(INTEGER) TO molecular_analysis_app;

-- ============================================================================
-- STEP 8: Verification and success message
-- ============================================================================

DO $$
DECLARE
    v_execution_files_count INTEGER;
    v_standalone_files_count INTEGER;
    v_indexes_count INTEGER;
BEGIN
    -- Count existing files
    SELECT COUNT(*) INTO v_execution_files_count
    FROM execution_files
    WHERE execution_id IS NOT NULL;
    
    SELECT COUNT(*) INTO v_standalone_files_count
    FROM execution_files
    WHERE execution_id IS NULL;
    
    -- Count new indexes
    SELECT COUNT(*) INTO v_indexes_count
    FROM pg_indexes
    WHERE tablename = 'execution_files'
      AND indexname LIKE 'idx_execution_files_%';
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 20251114_extend_execution_files_for_file_manager completed successfully';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes applied:';
    RAISE NOTICE '  ✓ execution_id is now nullable';
    RAISE NOTICE '  ✓ Added 6 new columns: user_id, file_category, description, tags, is_public, created_by';
    RAISE NOTICE '  ✓ Updated unique constraints for execution-bound files';
    RAISE NOTICE '  ✓ Created % indexes for performance', v_indexes_count;
    RAISE NOTICE '  ✓ Added check constraints for data integrity';
    RAISE NOTICE '  ✓ Created helper functions: get_user_storage_stats(), cleanup_orphaned_files()';
    RAISE NOTICE '';
    RAISE NOTICE 'Database state:';
    RAISE NOTICE '  • Execution-bound files: %', v_execution_files_count;
    RAISE NOTICE '  • Standalone files: %', v_standalone_files_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Create UserFileService in src/molecular_analysis_dashboard/services/';
    RAISE NOTICE '  2. Create file_validators.py for format validation';
    RAISE NOTICE '  3. Add /api/v1/files endpoints in presentation/api/routes/';
    RAISE NOTICE '  4. Update FileManager.tsx to use new APIs';
    RAISE NOTICE '';
    RAISE NOTICE 'Rollback: If needed, run 20251114_rollback_file_manager.sql';
    RAISE NOTICE '========================================';
END $$;
