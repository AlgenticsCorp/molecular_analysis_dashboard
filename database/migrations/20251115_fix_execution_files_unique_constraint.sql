-- Migration: Restore unique constraint for execution-bound execution files
-- Date: 2025-11-15
-- Purpose: Ensure ON CONFLICT clauses targeting (execution_id, parameter_name, file_type)
--          reference a real UNIQUE constraint while still permitting standalone files

BEGIN;

-- Remove the partial unique index introduced for file-manager support so we can
-- rely on a standard UNIQUE constraint (which already treats NULL execution_ids
-- as distinct, allowing standalone files).
DROP INDEX IF EXISTS idx_execution_files_execution_context;

-- Re-establish the original unique constraint used by execution file upserts.
ALTER TABLE execution_files
    ADD CONSTRAINT execution_files_execution_id_parameter_name_file_type_key
    UNIQUE (execution_id, parameter_name, file_type);

COMMIT;
