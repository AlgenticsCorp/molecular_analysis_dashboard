-- Database initialization script
-- Creates required extensions and optimizations

-- Create UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create full-text search extension
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create additional extensions for performance
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set some basic optimizations
ALTER DATABASE mad SET shared_preload_libraries = 'pg_stat_statements';
ALTER DATABASE mad SET log_statement = 'all';
ALTER DATABASE mad SET log_duration = on;
