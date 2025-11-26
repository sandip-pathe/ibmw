"""
Pydantic schemas for API request/response models.
"""
from datetime import datetime
from typing import Any, Literal, Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# --- EXISTING SCHEMAS (Retained) ---

# GitHub Webhook Payloads
class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    clone_url: str
    default_branch: str = "main"

class GitHubInstallation(BaseModel):
    id: int
    account: dict[str, Any]
    app_id: int
    target_type: str
    permissions: dict[str, str]
    events: list[str]

class WebhookInstallationEvent(BaseModel):
    action: Literal["created", "deleted", "suspend", "unsuspend"]
    installation: GitHubInstallation
    repositories: Optional[list[GitHubRepository]] = None

class WebhookPushEvent(BaseModel):
    ref: str
    before: str
    after: str
    repository: GitHubRepository
    installation: dict[str, Any]
    commits: list[dict[str, Any]]

class InstallationResponse(BaseModel):
    installation_id: int
    account_login: str
    account_id: int
    target_type: str
    repositories_count: int
    created_at: datetime
    updated_at: datetime

class RepositoryResponse(BaseModel):
    repo_id: UUID
    installation_id: Optional[int]
    github_id: int
    repo_name: str
    full_name: str
    private: bool
    default_branch: str
    last_synced_at: Optional[datetime] = None
    last_commit_sha: Optional[str] = None
    indexed_file_count: int
    total_chunks: int
    created_at: datetime

class CodeMapResponse(BaseModel):
    chunk_id: UUID
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_text: str
    ast_node_type: Optional[str] = None
    nl_summary: Optional[str] = None
    call_links: list[Any] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)
    config_keys: dict[str, Any] = Field(default_factory=dict)
    semantic_tags: list[str] = Field(default_factory=list)
    previous_hash: Optional[str] = None
    delta_type: Optional[str] = None
    similarity_score: Optional[float] = None

# --- UPDATED VIOLATION SCHEMAS ---

class ViolationResponse(BaseModel):
    """Violation response including review status."""
    violation_id: UUID
    rule_id: str
    verdict: Literal["compliant", "non_compliant", "partial", "unknown"]
    severity: Literal["critical", "high", "medium", "low"]
    severity_score: float
    explanation: str
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    file_path: str
    start_line: int
    end_line: int
    
    # New fields
    status: Literal["pending", "approved", "rejected", "ignored"]
    reviewer_note: Optional[str] = None
    jira_ticket_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    
    created_at: datetime

class ViolationUpdate(BaseModel):
    """Request model for updating a violation."""
    status: Literal["pending", "approved", "rejected", "ignored"]
    note: Optional[str] = None

class JiraSyncRequest(BaseModel):
    violation_id: UUID
    project_key: str = "COMP" # Default project key
    issue_type: str = "Bug"

class JiraSyncResponse(BaseModel):
    ticket_id: str
    ticket_url: str

# --- EXISTING SCAN SCHEMAS (Retained) ---

class ScanResponse(BaseModel):
    scan_id: UUID
    repo_id: UUID
    scan_type: str
    status: Literal["pending", "running", "completed", "failed"]
    total_violations: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

class ScanDetailResponse(ScanResponse):
    violations: list[ViolationResponse] = []

class AnalyzeRuleRequest(BaseModel):
    rule_text: str = Field(..., description="Natural language compliance rule")
    repo_id: UUID = Field(..., description="Repository to analyze")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of similar chunks")
    severity_threshold: Optional[Literal["critical", "high", "medium", "low"]] = None

class AnalyzeRuleResponse(BaseModel):
    rule_text: str
    repo_id: UUID
    matched_chunks: list[CodeMapResponse]
    violations: list[ViolationResponse]
    summary: str

class FullScanRequest(BaseModel):
    repo_id: UUID
    initiator: Optional[str] = None
    commit_sha: Optional[str] = None
    rule_ids: Optional[list[str]] = None

class FlowGraphNode(BaseModel):
    node_id: str
    file_path: str
    function_name: str
    edges: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FlowGraphResponse(BaseModel):
    id: UUID
    repo_id: UUID
    nodes: list[FlowGraphNode]
    created_at: datetime

class ComplianceEvidenceResponse(BaseModel):
    id: UUID
    repo_id: UUID
    rule_id: str
    chunk_id: UUID
    finding_text: str
    severity: str
    line_number: int
    created_at: datetime

class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: Literal["queued", "running", "completed", "failed"]
    repo_id: Optional[UUID] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime
    services: dict[str, bool]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict[str, Any]] = None