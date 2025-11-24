-- 1. Workspaces (SaaS Tenancy)
CREATE TABLE IF NOT EXISTS workspaces (
    workspace_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    owner_id VARCHAR(255) NOT NULL, -- Stack Auth User ID
    created_at TIMESTAMP DEFAULT NOW()
);

-- Link Installations to Workspaces (Optional if you want multi-tenant)
ALTER TABLE installations ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(workspace_id);

-- 2. Regulation Engine Tables

-- Source Documents (The "Physical" File or Web Page)
CREATE TABLE IF NOT EXISTS policy_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(512) NOT NULL,
    regulator VARCHAR(50) NOT NULL, -- RBI, SEBI
    doc_type VARCHAR(50) NOT NULL,  -- Master Direction, Circular, Press Release
    reference_number VARCHAR(100),  -- e.g. RBI/2023-24/101
    publish_date DATE,
    source_url TEXT,
    content_hash VARCHAR(64),       -- For duplicate detection
    status VARCHAR(50) DEFAULT 'draft', -- 'active', 'draft', 'archived', 'processing'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for duplicate detection on URL and Hash
CREATE INDEX idx_policy_docs_source_url ON policy_documents(source_url);
CREATE INDEX idx_policy_docs_hash ON policy_documents(content_hash);
CREATE INDEX idx_policy_docs_status ON policy_documents(status);

-- Atomic Rules (The "Logical" Requirement)
CREATE TABLE IF NOT EXISTS policy_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_code VARCHAR(100) NOT NULL, -- e.g. RBI-MD-IT-12.1
    document_id UUID REFERENCES policy_documents(document_id) ON DELETE CASCADE,
    
    -- Normalized Spec (JSONB for flexibility)
    spec JSONB NOT NULL,             -- {actor, action, object, constraint...}
    
    -- Metadata
    section_ref VARCHAR(255),
    severity VARCHAR(20),
    category TEXT[],                 -- Array of tags
    
    -- Versioning & Lifecycle
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    superseded_by UUID REFERENCES policy_rules(rule_id),
    valid_from DATE,
    valid_until DATE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate active versions of same rule code
    UNIQUE (rule_code, version)
);

-- Vector Embeddings (Search Index)
CREATE TABLE IF NOT EXISTS policy_vectors (
    vector_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID REFERENCES policy_rules(rule_id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW Index for fast similarity search
CREATE INDEX idx_policy_vectors_embedding ON policy_vectors USING hnsw (embedding vector_cosine_ops);