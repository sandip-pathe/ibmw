-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Installations table (GitHub App installations)
CREATE TABLE IF NOT EXISTS installations (
    installation_id BIGINT PRIMARY KEY,
    account_id BIGINT NOT NULL,
    account_login VARCHAR(255) NOT NULL,
    app_id BIGINT NOT NULL,
    target_type VARCHAR(50) NOT NULL, -- 'User' or 'Organization'
    permissions JSONB NOT NULL DEFAULT '{}'::jsonb,
    events JSONB NOT NULL DEFAULT '[]'::jsonb,
    repositories JSONB NOT NULL DEFAULT '[]'::jsonb,
    suspended_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_installations_account ON installations(account_id);
CREATE INDEX idx_installations_created ON installations(created_at DESC);

-- Repositories table
CREATE TABLE IF NOT EXISTS repos (
    repo_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id BIGINT NOT NULL REFERENCES installations(installation_id) ON DELETE CASCADE,
    github_id BIGINT UNIQUE NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    full_name VARCHAR(512) NOT NULL,
    private BOOLEAN NOT NULL DEFAULT true,
    default_branch VARCHAR(255) DEFAULT 'main',
    clone_url TEXT,
    last_synced_at TIMESTAMP,
    last_commit_sha VARCHAR(40),
    indexed_file_count INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_repos_installation ON repos(installation_id);
CREATE INDEX idx_repos_github_id ON repos(github_id);
CREATE INDEX idx_repos_synced ON repos(last_synced_at DESC NULLS LAST);

-- Regulation chunks table
CREATE TABLE IF NOT EXISTS regulation_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id VARCHAR(255) NOT NULL,
    rule_section VARCHAR(500),
    source_document VARCHAR(500),
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_hash VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(1536),
    nl_summary TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_regulation_rule ON regulation_chunks(rule_id);
CREATE INDEX idx_regulation_hash ON regulation_chunks(chunk_hash);
CREATE INDEX idx_regulation_embedding ON regulation_chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- Code chunks table
CREATE TABLE IF NOT EXISTS code_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id UUID NOT NULL REFERENCES repos(repo_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    ast_node_type VARCHAR(100),
    file_hash VARCHAR(64) NOT NULL,
    chunk_hash VARCHAR(64) NOT NULL,
    embedding VECTOR(1536),
    nl_summary TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_code_repo ON code_chunks(repo_id);
CREATE INDEX idx_code_file_path ON code_chunks(repo_id, file_path);
CREATE INDEX idx_code_hash ON code_chunks(chunk_hash);
CREATE INDEX idx_code_language ON code_chunks(language);
CREATE INDEX idx_code_embedding ON code_chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- Scans table (compliance scan runs)
CREATE TABLE IF NOT EXISTS scans (
    scan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id UUID NOT NULL REFERENCES repos(repo_id) ON DELETE CASCADE,
    scan_type VARCHAR(50) NOT NULL DEFAULT 'full', -- 'full', 'incremental', 'pr'
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    initiator VARCHAR(255),
    commit_sha VARCHAR(40),
    total_violations INTEGER DEFAULT 0,
    critical_violations INTEGER DEFAULT 0,
    high_violations INTEGER DEFAULT 0,
    medium_violations INTEGER DEFAULT 0,
    low_violations INTEGER DEFAULT 0,
    result JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scans_repo ON scans(repo_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_created ON scans(created_at DESC);

-- Violations table
CREATE TABLE IF NOT EXISTS violations (
    violation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    rule_id VARCHAR(255) NOT NULL,
    code_chunk_id UUID NOT NULL REFERENCES code_chunks(chunk_id) ON DELETE CASCADE,
    regulation_chunk_id UUID REFERENCES regulation_chunks(chunk_id) ON DELETE SET NULL,
    verdict VARCHAR(50) NOT NULL, -- 'compliant', 'non_compliant', 'partial', 'unknown'
    severity VARCHAR(20) NOT NULL, -- 'critical', 'high', 'medium', 'low'
    severity_score DECIMAL(3,1) CHECK (severity_score >= 0 AND severity_score <= 10),
    explanation TEXT NOT NULL,
    evidence TEXT,
    remediation TEXT,
    file_path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_violations_scan ON violations(scan_id);
CREATE INDEX idx_violations_rule ON violations(rule_id);
CREATE INDEX idx_violations_severity ON violations(severity);
CREATE INDEX idx_violations_code_chunk ON violations(code_chunk_id);

-- Webhook events table (idempotency)
CREATE TABLE IF NOT EXISTS webhook_events (
    event_id VARCHAR(255) PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    installation_id BIGINT,
    repository_id BIGINT,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_webhook_processed ON webhook_events(processed, created_at);
CREATE INDEX idx_webhook_installation ON webhook_events(installation_id);

-- Job queue metadata (for RQ tracking)
CREATE TABLE IF NOT EXISTS jobs (
    job_id VARCHAR(255) PRIMARY KEY,
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    repo_id UUID REFERENCES repos(repo_id) ON DELETE CASCADE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB,
    error TEXT,
    retries INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_jobs_status ON jobs(status, created_at);
CREATE INDEX idx_jobs_repo ON jobs(repo_id);

-- Embedding cache metadata (track Redis cache)
CREATE TABLE IF NOT EXISTS embedding_cache_stats (
    cache_key VARCHAR(64) PRIMARY KEY,
    cache_type VARCHAR(50) NOT NULL, -- 'code_chunk', 'regulation_chunk', 'nl_summary'
    hit_count INTEGER DEFAULT 0,
    last_hit_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_installations_updated_at BEFORE UPDATE ON installations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repos_updated_at BEFORE UPDATE ON repos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_regulation_chunks_updated_at BEFORE UPDATE ON regulation_chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_chunks_updated_at BEFORE UPDATE ON code_chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- Add review status and workflow fields to violations table
ALTER TABLE violations 
ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'ignored'
ADD COLUMN IF NOT EXISTS reviewer_note TEXT,
ADD COLUMN IF NOT EXISTS jira_ticket_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(255);

-- Index for fast filtering of pending items
CREATE INDEX IF NOT EXISTS idx_violations_status ON violations(status);
CREATE INDEX IF NOT EXISTS idx_violations_jira ON violations(jira_ticket_id);