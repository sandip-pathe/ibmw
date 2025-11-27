"""
Compliance analysis endpoints.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from loguru import logger

from app.core.security import verify_admin_api_key
from app.database import get_db
from app.models.database import (
    CodeMapQueries,
    RepositoryQueries,
    ScanQueries,
    ViolationQueries,
)
from app.models.schemas import (
    AnalyzeRuleRequest,
    AnalyzeRuleResponse,
    CodeMapResponse,
    FullScanRequest,
    ScanDetailResponse,
    ScanResponse,
    ViolationResponse,
)
from app.services.embeddings import embeddings_service
from app.services.llm import llm_service
from app.workers.job_queue import job_queue

# Multi-agent compliance scanning
from app.services.compliance_scanner import (
    start_compliance_scan,
    get_scan_status,
    approve_remediation,
    decline_remediation,
    get_scan_logs
)
from app.services.preloaded_regulations import preloaded_regulation_service

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("/rule", dependencies=[Depends(verify_admin_api_key)])
async def analyze_rule(request: AnalyzeRuleRequest) -> AnalyzeRuleResponse:
    """
    Analyze code against a specific compliance rule.
    
    This endpoint:
    1. Embeds the rule text
    2. Finds similar code chunks via vector search
    3. Uses LLM to determine compliance for each chunk
    4. Returns matched chunks and violations
    """
    db = await get_db()

    # Verify repo exists
    async with db.acquire() as conn:
        repo = await RepositoryQueries.get_by_id(conn, request.repo_id)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {request.repo_id} not found",
            )

    # Embed rule text
    rule_embedding = await embeddings_service.embed_text(request.rule_text)

    # Find similar code chunks
    async with db.acquire() as conn:
        similar_chunks = await CodeMapQueries.search_similar(
            conn, rule_embedding, request.repo_id, top_k=request.top_k
        )

    logger.info(f"Found {len(similar_chunks)} similar chunks for rule analysis")

    # Analyze each chunk with LLM
    violations = []
    matched_chunks = []

    for chunk in similar_chunks:
        similarity_score = 1.0 - chunk.get("distance", 1.0)

        matched_chunks.append(
            CodeMapResponse(
            chunk_id=chunk["chunk_id"],
            file_path=chunk["file_path"],
            language=chunk["language"],
            start_line=chunk["start_line"],
            end_line=chunk["end_line"],
            chunk_text=chunk["chunk_text"],
            ast_node_type=chunk.get("ast_node_type"),
            nl_summary=chunk.get("nl_summary"),
            similarity_score=similarity_score,
            )
        )

        # Analyze compliance
        try:
            analysis = await llm_service.analyze_compliance(
                rule_text=request.rule_text,
                code_text=chunk["chunk_text"],
                file_path=chunk["file_path"],
                start_line=chunk["start_line"],
                end_line=chunk["end_line"],
                language=chunk["language"],
            )

            # Add to violations if non-compliant
            if analysis["verdict"] in ["non_compliant", "partial"]:
                # Check severity filter
                if request.severity_threshold:
                    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
                    if severity_order.get(analysis["severity"], 0) < severity_order.get(
                        request.severity_threshold, 0
                    ):
                        continue

                violations.append(
                    ViolationResponse(
                        violation_id=chunk["chunk_id"],  # Temp ID
                        rule_id="custom_rule",
                        verdict=analysis["verdict"],
                        severity=analysis["severity"],
                        severity_score=analysis["severity_score"],
                        explanation=analysis["explanation"],
                        evidence=analysis.get("evidence"),
                        remediation=analysis.get("remediation"),
                        file_path=chunk["file_path"],
                        start_line=chunk["start_line"],
                        end_line=chunk["end_line"],
                        created_at=chunk["created_at"],
                        status=analysis.get("status", "detected")
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to analyze chunk {chunk['chunk_id']}: {e}")

    # Generate summary
    summary = f"Analyzed {len(similar_chunks)} code chunks. Found {len(violations)} violations."

    return AnalyzeRuleResponse(
        rule_text=request.rule_text,
        repo_id=request.repo_id,
        matched_chunks=matched_chunks,
        violations=violations,
        summary=summary,
    )


@router.post("/repo/{repo_id}/scan", dependencies=[Depends(verify_admin_api_key)])
async def full_repo_scan(repo_id: UUID, request: FullScanRequest) -> ScanResponse:
    """
    Trigger full compliance scan for a repository.
    
    This creates a scan record and enqueues an async analysis job.
    """
    db = await get_db()

    # Verify repo exists
    async with db.acquire() as conn:
        repo = await RepositoryQueries.get_by_id(conn, repo_id)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {repo_id} not found",
            )

        # Create scan record
        scan_data = {
            "repo_id": repo_id,
            "scan_type": "full",
            "initiator": request.initiator,
            "commit_sha": request.commit_sha or repo["last_commit_sha"],
        }

        scan_id = await ScanQueries.create(conn, scan_data)

    # Enqueue analysis job
    job_id = job_queue.enqueue_analysis_job(
        scan_id=scan_id,
        repo_id=repo_id,
        rule_ids=request.rule_ids,
    )

    logger.info(f"Created scan {scan_id} and enqueued job {job_id}")

    return ScanResponse(
        scan_id=scan_id,
        repo_id=repo_id,
        scan_type="full",
        status="pending",
        total_violations=0,
        critical_violations=0,
        high_violations=0,
        medium_violations=0,
        low_violations=0,
        created_at=repo["created_at"],
    )


@router.get("/scan/{scan_id}", dependencies=[Depends(verify_admin_api_key)])
async def get_scan_results(
    scan_id: UUID, include_violations: bool = True
) -> ScanDetailResponse:
    """Get scan results with optional violations."""
    db = await get_db()

    async with db.acquire() as conn:
        scan = await ScanQueries.get_by_id(conn, scan_id)

        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan {scan_id} not found",
            )

        violations = []
        if include_violations and scan["status"] == "completed":
            violation_records = await ViolationQueries.get_by_scan(conn, scan_id)
            violations = [
                ViolationResponse(
                    violation_id=v["violation_id"],
                    rule_id=v["rule_id"],
                    verdict=v["verdict"],
                    severity=v["severity"],
                    severity_score=v["severity_score"],
                    explanation=v["explanation"],
                    evidence=v.get("evidence"),
                    remediation=v.get("remediation"),
                    file_path=v["file_path"],
                    start_line=v["start_line"],
                    end_line=v["end_line"],
                    created_at=v["created_at"],
                    status=v.get("status", "detected"),
                )
                for v in violation_records
            ]

    return ScanDetailResponse(
        scan_id=scan["scan_id"],
        repo_id=scan["repo_id"],
        scan_type=scan["scan_type"],
        status=scan["status"],
        total_violations=scan["total_violations"],
        critical_violations=scan["critical_violations"],
        high_violations=scan["high_violations"],
        medium_violations=scan["medium_violations"],
        low_violations=scan["low_violations"],
        started_at=scan["started_at"],
        completed_at=scan["completed_at"],
        created_at=scan["created_at"],
        violations=violations,
    )


# ============================================================================
# MULTI-AGENT COMPLIANCE SCANNING ENDPOINTS
# ============================================================================

class ApproveRemediationRequest(BaseModel):
    """Request body for approving remediation"""
    decision: str  # 'approve' or 'decline'
    edited_issues: list[dict] | None = None
    reason: str | None = None


@router.post("/scan/{repo_id}/compliance")
async def trigger_compliance_scan(
    repo_id: str,
    dependencies=[Depends(verify_admin_api_key)]
):
    """
    Trigger multi-agent compliance scan for a repository
    
    This endpoint:
    1. Gets the first regulation chunk from preloaded regulations
    2. Starts a multi-agent compliance scan
    3. Returns scan_id for tracking
    
    The scan will execute agents sequentially:
    - RulePlanner: Converts regulation to engineering tasks
    - CodeNavigator: Finds relevant code using vector search
    - CodeInvestigator: Analyzes code for compliance
    - ConsistencyChecker: Validates findings and produces verdict
    - JiraBot: Generates remediation tasks (pauses for approval)
    """
    try:
        # Get first regulation chunk
        chunks = await preloaded_regulation_service.get_regulation_chunks(limit=1)
        if not chunks:
            raise HTTPException(404, "No regulation loaded. Please preload a regulation first.")
        
        regulation_chunk = chunks[0]
        
        # Start compliance scan
        scan_id = await start_compliance_scan(repo_id, regulation_chunk)
        
        return {
            "success": True,
            "scan_id": scan_id,
            "status": "running",
            "message": "Multi-agent compliance scan started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start compliance scan: {e}")
        raise HTTPException(500, f"Failed to start compliance scan: {str(e)}")


@router.get("/scan/{scan_id}/agents")
async def get_agent_execution_status(scan_id: str):
    """
    Get agent execution timeline and status for a compliance scan
    
    Returns:
    - Scan metadata (status, timestamps, verdict)
    - Agent execution timeline with status for each agent
    - Current agent being executed
    - Whether scan requires user approval
    """
    try:
        status_data = await get_scan_status(scan_id)
        return {
            "success": True,
            "data": status_data
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to get scan status: {e}")
        raise HTTPException(500, f"Failed to get scan status: {str(e)}")


@router.get("/scan/{scan_id}/logs")
async def get_agent_logs(scan_id: str, start_index: int = 0):
    """
    Get streaming agent logs for a compliance scan
    
    Logs are stored in Redis and include:
    - Agent name
    - Timestamp
    - Log message
    - Log level
    
    Use start_index for pagination
    """
    try:
        logs = await get_scan_logs(scan_id, start_index)
        return {
            "success": True,
            "scan_id": scan_id,
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Failed to get scan logs: {e}")
        raise HTTPException(500, f"Failed to get scan logs: {str(e)}")


@router.patch("/scan/{scan_id}/approve")
async def approve_scan_remediation(
    scan_id: str,
    request: ApproveRemediationRequest,
    dependencies=[Depends(verify_admin_api_key)]
):
    """
    Approve or decline remediation tasks
    
    If decision == 'approve':
    - Creates Jira tickets for remediation tasks
    - Updates scan status to 'completed'
    - Returns ticket IDs
    
    If decision == 'decline':
    - Marks scan as declined
    - No tickets created
    
    Optional:
    - edited_issues: List of modified remediation tasks
    - reason: Reason for declining (if declined)
    """
    try:
        if request.decision == "approve":
            result = await approve_remediation(scan_id, request.edited_issues)
            return {
                "success": True,
                "decision": "approved",
                "data": result
            }
        elif request.decision == "decline":
            result = await decline_remediation(scan_id, request.reason)
            return {
                "success": True,
                "decision": "declined",
                "data": result
            }
        else:
            raise HTTPException(400, "Decision must be 'approve' or 'decline'")
            
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to process approval: {e}")
        raise HTTPException(500, f"Failed to process approval: {str(e)}")
