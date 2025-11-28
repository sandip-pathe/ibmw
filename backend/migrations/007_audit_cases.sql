-- Audit Cases table for robust orchestration
-- Migration: 007_audit_cases.sql

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Audit cases table for orchestration
CREATE TABLE IF NOT EXISTS audit_cases (
    case_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id UUID NOT NULL REFERENCES repos(repo_id) ON DELETE CASCADE,
    regulation_ids TEXT[] NOT NULL,
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    current_step VARCHAR(50),
    steps_completed TEXT[] DEFAULT '{}',
    steps_pending TEXT[] DEFAULT '{}',
    error_message TEXT,
    
    -- Agent outputs
    rule_ingestion_result JSONB,
    code_scan_result JSONB,
    compliance_check_result JSONB,
    report_data JSONB,
    
    -- HITL approval
    requires_approval BOOLEAN DEFAULT FALSE,
    approval_items JSONB DEFAULT '[]'::jsonb,
    user_decision VARCHAR(20),
    
    -- Options and metadata
    options JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_cases_repo ON audit_cases(repo_id);
CREATE INDEX IF NOT EXISTS idx_audit_cases_status ON audit_cases(status);
CREATE INDEX IF NOT EXISTS idx_audit_cases_started ON audit_cases(started_at DESC);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_audit_cases_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_cases_updated_at
BEFORE UPDATE ON audit_cases
FOR EACH ROW
EXECUTE FUNCTION update_audit_cases_updated_at();
