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