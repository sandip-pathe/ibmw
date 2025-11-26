"""
API endpoints for managing compliance violations (Review Queue).
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from app.database import get_db
from app.models.database import ViolationQueries
from app.models.schemas import ViolationResponse, ViolationUpdate, SuccessResponse
# from app.core.security import verify_auth  # Assuming generic auth exists

router = APIRouter(prefix="/violations", tags=["violations"])

@router.get("/pending", response_model=list[ViolationResponse])
async def get_pending_violations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all pending violations needing review.
    """
    db = await get_db()
    async with db.acquire() as conn:
        violations = await ViolationQueries.get_pending(conn, limit, offset)
        
    return [
        ViolationResponse(
            violation_id=v["violation_id"],
            rule_id=v["rule_id"],
            verdict=v["verdict"],
            severity=v["severity"],
            severity_score=float(v["severity_score"]) if v["severity_score"] else 0.0,
            explanation=v["explanation"],
            evidence=v["evidence"],
            remediation=v["remediation"],
            file_path=v["file_path"],
            start_line=v["start_line"],
            end_line=v["end_line"],
            status=v["status"],
            reviewer_note=v["reviewer_note"],
            jira_ticket_id=v["jira_ticket_id"],
            reviewed_at=v["reviewed_at"],
            reviewed_by=v["reviewed_by"],
            created_at=v["created_at"]
        )
        for v in violations
    ]

@router.patch("/{violation_id}", response_model=ViolationResponse)
async def update_violation_status(
    violation_id: UUID,
    update: ViolationUpdate,
    x_user_id: str = Header("admin", description="User ID performing review") 
):
    """
    Review a violation (Approve/Reject/Ignore).
    """
    db = await get_db()
    
    async with db.acquire() as conn:
        updated = await ViolationQueries.update_status(
            conn, 
            violation_id, 
            update.status, 
            update.note, 
            x_user_id
        )
        
    if not updated:
        raise HTTPException(status_code=404, detail="Violation not found")
        
    return ViolationResponse(
        violation_id=updated["violation_id"],
        rule_id=updated["rule_id"],
        verdict=updated["verdict"],
        severity=updated["severity"],
        severity_score=float(updated["severity_score"]) if updated["severity_score"] else 0.0,
        explanation=updated["explanation"],
        evidence=updated["evidence"],
        remediation=updated["remediation"],
        file_path=updated["file_path"],
        start_line=updated["start_line"],
        end_line=updated["end_line"],
        status=updated["status"],
        reviewer_note=updated["reviewer_note"],
        jira_ticket_id=updated["jira_ticket_id"],
        reviewed_at=updated["reviewed_at"],
        reviewed_by=updated["reviewed_by"],
        created_at=updated["created_at"]
    )