-- Rollback Migration: Revert execution_files table extensions for File Manager
-- Date: 2025-11-14
-- Purpose: Rollback changes from 20251114_extend_execution_files_for_file_manager.sql

-- WARNING: This will remove all standalone files (where execution_id IS NULL)
-- Backup your data before running this rollback!

-- ============================================================================
-- STEP 1: Safety check - Count standalone files
-- ============================================================================

DO $$
DECLARE
    v_standalone_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_standalone_count
    FROM execution_files
    WHERE execution_id IS NULL;
    
    IF v_standalone_count > 0 THEN
        RAISE WARNING 'WARNING: % standalone files will be deleted by this rollback!', v_standalone_count;
        RAISE WARNING 'To proceed, you must manually delete them or comment out this check.';
        -- Uncomment the next line to allow rollback even with standalone files
        -- RAISE NOTICE 'Proceeding with rollback...';
        RAISE EXCEPTION 'Rollback aborted to prevent data loss. Backup your data first!';
    ELSE
        RAISE NOTICE 'No standalone files found. Safe to proceed with rollback.';
    END IF;
END $$;

-- ============================================================================
-- STEP 2: Drop helper functions
-- ============================================================================

DROP FUNCTION IF EXISTS get_user_storage_stats(UUID);
DROP FUNCTION IF EXISTS cleanup_orphaned_files(INTEGER);

-- ============================================================================
-- STEP 3: Drop new indexes
-- ============================================================================

DROP INDEX IF EXISTS idx_execution_files_user_category_uploaded;
DROP INDEX IF EXISTS idx_execution_files_tags;
DROP INDEX IF EXISTS idx_execution_files_uploaded_at;
DROP INDEX IF EXISTS idx_execution_files_category;
DROP INDEX IF EXISTS idx_execution_files_user_id;
DROP INDEX IF EXISTS idx_execution_files_standalone;
DROP INDEX IF EXISTS idx_execution_files_execution_context;

-- ============================================================================
-- STEP 4: Drop check constraints
-- ============================================================================

ALTER TABLE execution_files
    DROP CONSTRAINT IF EXISTS check_file_category;

ALTER TABLE execution_files
    DROP CONSTRAINT IF EXISTS check_standalone_file_metadata;

-- ============================================================================
-- STEP 5: Remove new columns
-- ============================================================================

ALTER TABLE execution_files
    DROP COLUMN IF EXISTS created_by,
    DROP COLUMN IF EXISTS is_public,
    DROP COLUMN IF EXISTS tags,
    DROP COLUMN IF EXISTS description,
    DROP COLUMN IF EXISTS file_category,
    DROP COLUMN IF EXISTS user_id;

-- ============================================================================
-- STEP 6: Delete standalone files (if any slipped through)
-- ============================================================================

DELETE FROM execution_files
WHERE execution_id IS NULL;

-- ============================================================================
-- STEP 7: Restore execution_id NOT NULL constraint
-- ============================================================================

ALTER TABLE execution_files
    ALTER COLUMN execution_id SET NOT NULL;

-- ============================================================================
-- STEP 8: Restore original unique constraint
-- ============================================================================

ALTER TABLE execution_files
    ADD CONSTRAINT execution_files_execution_id_parameter_name_file_type_key 
    UNIQUE (execution_id, parameter_name, file_type);

-- ============================================================================
-- STEP 9: Update column comment
-- ============================================================================

COMMENT ON COLUMN execution_files.execution_id IS 'Reference to the task execution this file belongs to';

-- ============================================================================
-- STEP 10: Success message
-- ============================================================================

DO $$
DECLARE
    v_file_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_file_count
    FROM execution_files;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Rollback 20251114_rollback_file_manager completed successfully';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes reverted:';
    RAISE NOTICE '  ✓ Removed user_id, file_category, description, tags, is_public, created_by columns';
    RAISE NOTICE '  ✓ Restored execution_id NOT NULL constraint';
    RAISE NOTICE '  ✓ Restored original unique constraint';
    RAISE NOTICE '  ✓ Dropped new indexes';
    RAISE NOTICE '  ✓ Removed check constraints';
    RAISE NOTICE '  ✓ Deleted helper functions';
    RAISE NOTICE '';
    RAISE NOTICE 'Database state:';
    RAISE NOTICE '  • Remaining files: %', v_file_count;
    RAISE NOTICE '';
    RAISE NOTICE 'execution_files table restored to pre-migration state';
    RAISE NOTICE '========================================';
END $$;
