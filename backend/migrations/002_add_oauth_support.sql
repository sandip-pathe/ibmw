-- Make installation_id nullable for OAuth-based repositories
-- OAuth repos don't have installation initially until GitHub App is installed

ALTER TABLE repos 
ALTER COLUMN installation_id DROP NOT NULL;

-- Add index for NULL installation_id to find OAuth-only repos
CREATE INDEX idx_repos_no_installation ON repos(github_id) WHERE installation_id IS NULL;

-- Add user_repos table to track which user selected which repos
CREATE TABLE IF NOT EXISTS user_repos (
    user_repo_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,  -- From Stack Auth
    repo_id UUID NOT NULL REFERENCES repos(repo_id) ON DELETE CASCADE,
    github_access_token TEXT,  -- Encrypted user's GitHub token
    is_selected BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, repo_id)
);

CREATE INDEX idx_user_repos_user ON user_repos(user_id);
CREATE INDEX idx_user_repos_repo ON user_repos(repo_id);
CREATE INDEX idx_user_repos_selected ON user_repos(is_selected) WHERE is_selected = true;

-- Add users table for OAuth user info
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,  -- From Stack Auth
    github_user_id BIGINT UNIQUE,
    github_login VARCHAR(255),
    github_access_token TEXT,  -- Encrypted
    github_token_expires_at TIMESTAMP,
    email VARCHAR(500),
    name VARCHAR(500),
    avatar_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_github_id ON users(github_user_id);
CREATE INDEX idx_users_created ON users(created_at DESC);
