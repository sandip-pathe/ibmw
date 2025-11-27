-- Agent execution tracking for multi-agent compliance system
-- Migration: 006_agent_execution.sql

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent execution tracking
CREATE TABLE IF NOT EXISTS agent_executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'running', 'completed', 'failed', 'waiting_approval'
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    output JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_exec_scan ON agent_executions(scan_id);
CREATE INDEX IF NOT EXISTS idx_agent_exec_status ON agent_executions(status);

-- Agent logs for streaming
CREATE TABLE IF NOT EXISTS agent_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES agent_executions(execution_id) ON DELETE CASCADE,
    scan_id UUID NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    level VARCHAR(20) DEFAULT 'info',
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_scan ON agent_logs(scan_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON agent_logs(timestamp);

-- Compliance scans table
CREATE TABLE IF NOT EXISTS compliance_scans (
    scan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id UUID NOT NULL REFERENCES repos(repo_id) ON DELETE CASCADE,
    regulation_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    
    -- Agent outputs
    rule_plan JSONB,
    matched_files JSONB,
    investigation_result JSONB,
    final_verdict JSONB,
    remediation_tasks JSONB,
    
    -- Approval workflow
    requires_user_action BOOLEAN DEFAULT FALSE,
    user_decision VARCHAR(20), -- 'approved', 'declined'
    jira_ticket_ids JSONB DEFAULT '[]'::jsonb,
    
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_compliance_scans_repo ON compliance_scans(repo_id);
CREATE INDEX IF NOT EXISTS idx_compliance_scans_status ON compliance_scans(status);
