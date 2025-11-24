"""
Pydantic schemas for API request/response models.
"""
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# GitHub Webhook Payloads
class GitHubRepository(BaseModel):
    """GitHub repository model."""
    id: int
    name: str
    full_name: str
    private: bool
    clone_url: str
    default_branch: str = "main"


class GitHubInstallation(BaseModel):
    """GitHub installation model."""
    id: int
    account: dict[str, Any]
    app_id: int
    target_type: str
    permissions: dict[str, str]
    events: list[str]


class WebhookInstallationEvent(BaseModel):
    """Installation webhook event."""
    action: Literal["created", "deleted", "suspend", "unsuspend"]
    installation: GitHubInstallation
    repositories: Optional[list[GitHubRepository]] = None


class WebhookPushEvent(BaseModel):
    """Push webhook event."""
    ref: str
    before: str
    after: str
    repository: GitHubRepository
    installation: dict[str, Any]
    commits: list[dict[str, Any]]


# Installation Responses
class InstallationResponse(BaseModel):
    """Installation API response."""
    installation_id: int
    account_login: str
    account_id: int
    target_type: str
    repositories_count: int
    created_at: datetime
    updated_at: datetime


class RepositoryResponse(BaseModel):
    """Repository API response."""
    repo_id: UUID
    installation_id: int
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


# Code Analysis

class CodeMapResponse(BaseModel):
    """Code map chunk response."""
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


class ViolationResponse(BaseModel):
    """Violation response."""
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
    created_at: datetime


class ScanResponse(BaseModel):
    """Scan response."""
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
    """Detailed scan response with violations."""
    violations: list[ViolationResponse] = []


# Analysis Requests
class AnalyzeRuleRequest(BaseModel):
    """Request to analyze code against a specific rule."""
    rule_text: str = Field(..., description="Natural language compliance rule")
    repo_id: UUID = Field(..., description="Repository to analyze")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of similar chunks")
    severity_threshold: Optional[Literal["critical", "high", "medium", "low"]] = None



class AnalyzeRuleResponse(BaseModel):
    """Response for rule analysis."""
    rule_text: str
    repo_id: UUID
    matched_chunks: list[CodeMapResponse]
    violations: list[ViolationResponse]
    summary: str


class FullScanRequest(BaseModel):
    """Request for full repository scan."""
    repo_id: UUID
    initiator: Optional[str] = None
    commit_sha: Optional[str] = None
    rule_ids: Optional[list[str]] = None  # If None, scan all rules


# ...existing code...
# Flow Graph
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

# Compliance Evidence
class ComplianceEvidenceResponse(BaseModel):
    id: UUID
    repo_id: UUID
    rule_id: str
    chunk_id: UUID
    finding_text: str
    severity: str
    line_number: int
    created_at: datetime


# Job Status
class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    job_type: str
    status: Literal["queued", "running", "completed", "failed"]
    repo_id: Optional[UUID] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Health Check
class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime
    services: dict[str, bool] = Field(
        default_factory=lambda: {
            "database": False,
            "redis": False,
            "embeddings": False,
            "llm": False,
        }
    )


# Generic Responses
class ErrorResponse(BaseModel):
    """Generic error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Generic success response."""
    message: str
    data: Optional[dict[str, Any]] = None
