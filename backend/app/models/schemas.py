# --- NEW REGULATION CHUNK SCHEMA ---
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

class RegulationChunkResponse(BaseModel):
    chunk_id: str
    rule_id: str
    rule_section: str | None = None
    source_document: str | None = None
    chunk_text: str
    chunk_index: int
    nl_summary: str | None = None
    created_at: datetime

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


# --- COMPLIANCE RESULT SCHEMAS ---

class ComplianceResult(BaseModel):
    """Structured compliance result from Rule Matcher agent."""
    result_id: Optional[UUID] = None
    rule_id: str
    repo_id: UUID
    file_path: str
    start_line: int
    end_line: int
    verdict: Literal["compliant", "non_compliant", "partial", "unclear"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    reasoning: str
    remediation_suggestion: Optional[str] = None
    severity: Literal["critical", "high", "medium", "low"] = "medium"
    tags: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class ComplianceResultBatch(BaseModel):
    """Batch of compliance results."""
    results: List[ComplianceResult]
    total_checked: int
    compliant_count: int
    non_compliant_count: int
    partial_count: int
    unclear_count: int


# --- AUDIT CASE SCHEMAS ---

class AuditCaseState(BaseModel):
    """Complete audit case state for orchestration."""
    case_id: UUID
    repo_id: UUID
    regulation_ids: List[str]
    status: Literal["pending", "running", "waiting_approval", "completed", "failed", "paused"]
    current_step: Optional[str] = None
    steps_completed: List[str] = Field(default_factory=list)
    steps_pending: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    # Agent outputs
    rule_ingestion_result: Optional[dict[str, Any]] = None
    code_scan_result: Optional[dict[str, Any]] = None
    compliance_check_result: Optional[dict[str, Any]] = None
    report_data: Optional[dict[str, Any]] = None
    
    # HITL
    requires_approval: bool = False
    approval_items: List[dict[str, Any]] = Field(default_factory=list)
    user_decision: Optional[str] = None
    
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class AuditCaseCreate(BaseModel):
    """Request to create audit case."""
    repo_id: UUID
    regulation_ids: List[str]
    options: dict[str, Any] = Field(default_factory=dict)


class AuditCaseResponse(BaseModel):
    """Audit case response."""
    case_id: UUID
    repo_id: UUID
    status: str
    current_step: Optional[str] = None
    progress: float = Field(ge=0.0, le=100.0)
    message: Optional[str] = None


# --- MCP SERVER SCHEMAS ---

class MCPRunAuditRequest(BaseModel):
    """MCP request to run audit."""
    repo_id: UUID
    regulators: List[str] = Field(description="List of regulator IDs: RBI, SEBI, etc.")
    options: dict[str, Any] = Field(default_factory=dict)


class MCPRunAuditResponse(BaseModel):
    """MCP response for run audit."""
    case_id: UUID
    status: str
    message: str


class MCPResumeAuditRequest(BaseModel):
    """MCP request to resume paused audit."""
    case_id: UUID


class MCPSyncRegulationRequest(BaseModel):
    """MCP request to sync regulation."""
    regulator: str
    document_type: str
    document_url: Optional[str] = None
    document_data: Optional[dict[str, Any]] = None


class MCPIndexRepoRequest(BaseModel):
    """MCP request to index repository."""
    repo_id: UUID
    force_refresh: bool = False


class MCPCheckRuleRequest(BaseModel):
    """MCP request to check single rule against repo."""
    rule_id: str
    repo_id: UUID


# --- HITL REVIEW SCHEMAS ---

class HITLExplainRequest(BaseModel):
    """Request to explain a finding."""
    result_id: Optional[UUID] = None
    violation_id: Optional[UUID] = None
    scan_id: Optional[UUID] = None
    question: str = Field(description="Specific question about the finding")


class HITLExplainResponse(BaseModel):
    """Response with explanation."""
    explanation: str
    evidence: List[str] = Field(default_factory=list)
    related_rules: List[str] = Field(default_factory=list)
    confidence: float


class HITLSuggestFixRequest(BaseModel):
    """Request fix suggestion for violation."""
    violation_id: UUID
    context: Optional[str] = None


class HITLSuggestFixResponse(BaseModel):
    """Fix suggestion response."""
    suggested_fix: str
    code_snippet: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    rationale: str
    confidence: float


class HITLReviewDecision(BaseModel):
    """Human review decision."""
    item_id: UUID
    decision: Literal["approve", "reject", "request_changes"]
    note: Optional[str] = None
    changes: Optional[dict[str, Any]] = None


# --- REPORT SCHEMAS ---

class ReportOutline(BaseModel):
    """Report structure outline."""
    sections: List[dict[str, Any]]
    coverage_summary: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportValidationResult(BaseModel):
    """Report validation result."""
    is_valid: bool
    missing_sections: List[str] = Field(default_factory=list)
    missing_rules: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class GenerateReportRequest(BaseModel):
    """Request to generate report."""
    case_id: UUID
    format: Literal["html", "pdf", "json"] = "html"
    template: Optional[str] = None


class GenerateReportResponse(BaseModel):
    """Generated report response."""
    report_id: UUID
    case_id: UUID
    format: str
    download_url: Optional[str] = None
    content: Optional[str] = None