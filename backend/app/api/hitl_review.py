"""
HITL (Human-in-the-Loop) Review API Endpoints
Provides tools for human reviewers to understand and act on findings
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from uuid import UUID
from typing import Optional

from app.models.schemas import (
    HITLExplainRequest,
    HITLExplainResponse,
    HITLSuggestFixRequest,
    HITLSuggestFixResponse,
    HITLReviewDecision,
    SuccessResponse
)
from app.services.hitl_reviewer import hitl_reviewer_service
from app.database import db


router = APIRouter(prefix="/hitl", tags=["HITL Review"])


@router.post("/explain", response_model=HITLExplainResponse)
async def explain_finding(request: HITLExplainRequest) -> HITLExplainResponse:
    """
    HITL Tool: Explain a compliance finding
    
    Provides detailed explanation of why a finding was flagged,
    including evidence, related rules, and reasoning.
    """
    try:
        logger.info(f"HITL explain: question='{request.question[:50]}...'")
        
        explanation = await hitl_reviewer_service.explain_finding(
            result_id=request.result_id,
            violation_id=request.violation_id,
            scan_id=request.scan_id,
            question=request.question
        )
        
        return explanation
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"HITL explain failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest_fix", response_model=HITLSuggestFixResponse)
async def suggest_fix(request: HITLSuggestFixRequest) -> HITLSuggestFixResponse:
    """
    HITL Tool: Suggest fix for a violation
    
    Generates actionable fix suggestions including code snippets,
    step-by-step instructions, and rationale.
    """
    try:
        logger.info(f"HITL suggest_fix: violation={request.violation_id}")
        
        suggestion = await hitl_reviewer_service.suggest_fix(
            violation_id=request.violation_id,
            context=request.context
        )
        
        return suggestion
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"HITL suggest_fix failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review_decision", response_model=SuccessResponse)
async def submit_review_decision(decision: HITLReviewDecision) -> SuccessResponse:
    """
    HITL Tool: Submit review decision
    
    Allows human reviewer to approve, reject, or request changes
    for compliance findings or remediation tasks.
    """
    try:
        logger.info(f"HITL review decision: {decision.decision} for {decision.item_id}")
        
        result = await hitl_reviewer_service.submit_decision(
            item_id=decision.item_id,
            decision=decision.decision,
            note=decision.note,
            changes=decision.changes
        )
        
        return SuccessResponse(
            message=f"Review decision '{decision.decision}' recorded",
            data=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"HITL review_decision failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending_reviews")
async def get_pending_reviews(limit: int = 50, offset: int = 0):
    """
    Get list of items pending human review
    """
    try:
        async with db.acquire() as conn:
            # Get pending violations
            violations = await conn.fetch("""
                SELECT 
                    v.violation_id,
                    v.rule_id,
                    v.verdict,
                    v.severity,
                    v.file_path,
                    v.explanation,
                    v.created_at,
                    r.full_name as repo_name
                FROM violations v
                JOIN scans s ON v.scan_id = s.scan_id
                JOIN repos r ON s.repo_id = r.repo_id
                WHERE v.status = 'pending'
                ORDER BY v.severity_score DESC, v.created_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)
            
            return {
                "pending_count": len(violations),
                "items": [dict(v) for v in violations]
            }
            
    except Exception as e:
        logger.error(f"Failed to get pending reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))
