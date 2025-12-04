-- Pipeline Builder Schema Migration
-- Date: 2025-11-12
-- Purpose: Add pipeline templates and executions for visual workflow builder

-- Pipeline Templates (Visual Workflows)
CREATE TABLE IF NOT EXISTS pipeline_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Template Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'Custom',
    
    -- Workflow Definition
    workflow_definition JSONB NOT NULL,  -- React Flow graph (nodes, edges)
    nextflow_script TEXT,                -- Generated Nextflow DSL
    
    -- Template Metadata
    tags VARCHAR(255)[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT FALSE,     -- Share across orgs
    is_active BOOLEAN DEFAULT TRUE,
    version VARCHAR(50) DEFAULT '1.0.0',
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    
    CONSTRAINT unique_template_version UNIQUE(org_id, name, version)
);

-- Pipeline Executions (Workflow Runs)
CREATE TABLE IF NOT EXISTS pipeline_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES pipeline_templates(template_id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Execution State
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    
    -- Input/Output
    input_parameters JSONB NOT NULL,
    execution_metadata JSONB DEFAULT '{}',
    results JSONB,
    error_message TEXT,
    
    -- Nextflow Integration
    nextflow_run_id VARCHAR(255),        -- Nextflow session ID
    nextflow_work_dir VARCHAR(500),      -- Work directory path
    
    -- Timing
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    estimated_completion TIMESTAMPTZ,
    
    CONSTRAINT valid_execution_status CHECK (
        status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled')
    )
);

-- Pipeline Step Results (Individual task outputs within workflow)
CREATE TABLE IF NOT EXISTS pipeline_step_results (
    step_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES pipeline_executions(execution_id) ON DELETE CASCADE,
    
    -- Step Info
    step_id VARCHAR(100) NOT NULL,       -- Node ID from React Flow
    task_id VARCHAR(100) NOT NULL,       -- Framework task identifier
    step_name VARCHAR(255),
    
    -- Execution
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Results
    output_data JSONB,
    error_message TEXT,
    external_job_id VARCHAR(255),        -- If task uses external service
    
    CONSTRAINT valid_step_status CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'skipped')
    )
);

-- Indexes for Performance
CREATE INDEX idx_pipeline_templates_org ON pipeline_templates(org_id);
CREATE INDEX idx_pipeline_templates_public ON pipeline_templates(is_public, is_active);
CREATE INDEX idx_pipeline_templates_category ON pipeline_templates(category);

CREATE INDEX idx_pipeline_executions_org ON pipeline_executions(org_id);
CREATE INDEX idx_pipeline_executions_user ON pipeline_executions(user_id);
CREATE INDEX idx_pipeline_executions_status ON pipeline_executions(status);
CREATE INDEX idx_pipeline_executions_template ON pipeline_executions(template_id);
CREATE INDEX idx_pipeline_executions_submitted ON pipeline_executions(submitted_at DESC);

CREATE INDEX idx_pipeline_step_results_execution ON pipeline_step_results(execution_id);
CREATE INDEX idx_pipeline_step_results_status ON pipeline_step_results(status);

-- Comments for Documentation
COMMENT ON TABLE pipeline_templates IS 'Visual workflow templates created by users via Pipeline Builder';
COMMENT ON TABLE pipeline_executions IS 'Execution history of pipeline workflows (org-isolated)';
COMMENT ON TABLE pipeline_step_results IS 'Individual task results within multi-step pipeline executions';

COMMENT ON COLUMN pipeline_templates.workflow_definition IS 'React Flow graph: {nodes: [...], edges: [...], viewport: {...}}';
COMMENT ON COLUMN pipeline_templates.nextflow_script IS 'Auto-generated Nextflow DSL for backend execution';
COMMENT ON COLUMN pipeline_executions.nextflow_run_id IS 'Nextflow session UUID for tracking workflow execution';
COMMENT ON COLUMN pipeline_step_results.step_id IS 'React Flow node ID to correlate UI with execution';
