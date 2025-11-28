"""
MCP (Model Context Protocol) Server Endpoints
Provides agent orchestration entry points for external MCP clients
"""
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from uuid import UUID
from typing import Optional

from app.models.schemas import (
    MCPRunAuditRequest,
    MCPRunAuditResponse,
    MCPResumeAuditRequest,
    MCPSyncRegulationRequest,
    MCPIndexRepoRequest,
    MCPCheckRuleRequest,
    AuditCaseResponse,
    AuditCaseState,
    SuccessResponse,
)
from app.services.orchestrator import audit_orchestrator
from app.services.regulation_sync import sync_regulation_service
from app.database import db


router = APIRouter(prefix="/mcp", tags=["MCP Server"])


@router.post("/run_audit", response_model=MCPRunAuditResponse)
async def run_audit(request: MCPRunAuditRequest) -> MCPRunAuditResponse:
    """
    MCP Entry Point: Start a full compliance audit
    
    Orchestrates:
    1. Rule ingestion for selected regulators
    2. Repository code scanning
    3. Compliance checking
    4. Report generation (pauses for approval)
    """
    try:
        logger.info(f"MCP run_audit: repo={request.repo_id}, regulators={request.regulators}")
        
        # Validate repo exists
        async with db.acquire() as conn:
            repo = await conn.fetchrow(
                "SELECT repo_id, full_name FROM repos WHERE repo_id = $1",
                request.repo_id
            )
            if not repo:
                raise HTTPException(status_code=404, detail=f"Repository {request.repo_id} not found")
        
        # Start audit case
        case_id = await audit_orchestrator.start_audit(
            repo_id=request.repo_id,
            regulation_ids=request.regulators,
            options=request.options
        )
        
        return MCPRunAuditResponse(
            case_id=case_id,
            status="running",
            message=f"Audit started for {repo['full_name']} against {', '.join(request.regulators)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP run_audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume_audit", response_model=AuditCaseResponse)
async def resume_audit(request: MCPResumeAuditRequest) -> AuditCaseResponse:
    """
    MCP Entry Point: Resume a paused audit case
    """
    try:
        logger.info(f"MCP resume_audit: case_id={request.case_id}")
        
        result = await audit_orchestrator.resume_audit(request.case_id)
        
        return AuditCaseResponse(
            case_id=result["case_id"],
            repo_id=result["repo_id"],
            status=result["status"],
            current_step=result.get("current_step"),
            progress=result.get("progress", 0.0),
            message=result.get("message")
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"MCP resume_audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit_status/{case_id}", response_model=AuditCaseState)
async def get_audit_status(case_id: UUID) -> AuditCaseState:
    """
    MCP Entry Point: Get current status of an audit case
    """
    try:
        state = await audit_orchestrator.get_case_state(case_id)
        return state
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"MCP get_audit_status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync_regulation", response_model=SuccessResponse)
async def sync_regulation(request: MCPSyncRegulationRequest) -> SuccessResponse:
    """
    MCP Entry Point: Sync regulation documents
    
    Agent 1 - Rule Reader entry point
    """
    try:
        logger.info(f"MCP sync_regulation: {request.regulator}/{request.document_type}")
        
        result = await sync_regulation_service.sync_regulation(
            regulator=request.regulator,
            document_type=request.document_type,
            document_url=request.document_url,
            document_data=request.document_data
        )
        
        return SuccessResponse(
            message=f"Synced {result['chunks_processed']} chunks for {request.regulator}",
            data=result
        )
        
    except Exception as e:
        logger.error(f"MCP sync_regulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index_repo", response_model=SuccessResponse)
async def index_repo(request: MCPIndexRepoRequest) -> SuccessResponse:
    """
    MCP Entry Point: Index or refresh repository code map
    
    Agent 2 - Code Scanner entry point
    """
    try:
        logger.info(f"MCP index_repo: repo={request.repo_id}, force={request.force_refresh}")
        
        # Get repo details
        async with db.acquire() as conn:
            repo = await conn.fetchrow("""
                SELECT installation_id, full_name, last_commit_sha
                FROM repos WHERE repo_id = $1
            """, request.repo_id)
            
            if not repo:
                raise HTTPException(status_code=404, detail=f"Repository {request.repo_id} not found")
        
        # Queue indexing job
        from app.workers.job_queue import job_queue
        
        job = await job_queue.enqueue_async(
            "app.workers.indexing_worker.index_repository",
            str(request.repo_id),
            repo["installation_id"] or 0,
            repo["full_name"],
            repo["last_commit_sha"]
        )
        
        return SuccessResponse(
            message=f"Indexing job queued for {repo['full_name']}",
            data={"job_id": job.id, "repo_id": str(request.repo_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP index_repo failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check_rule", response_model=SuccessResponse)
async def check_rule_against_repo(request: MCPCheckRuleRequest) -> SuccessResponse:
    """
    MCP Entry Point: Check single rule against repository
    
    Agent 3 - Rule Matcher entry point
    """
    try:
        logger.info(f"MCP check_rule: rule={request.rule_id}, repo={request.repo_id}")
        
        from app.services.rule_matcher import rule_matcher_service
        
        result = await rule_matcher_service.check_rule(
            rule_id=request.rule_id,
            repo_id=request.repo_id
        )
        
        return SuccessResponse(
            message=f"Rule check completed: {result['verdict']}",
            data=result
        )
        
    except Exception as e:
        logger.error(f"MCP check_rule failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
