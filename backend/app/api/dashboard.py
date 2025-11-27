from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.core.security import verify_admin_api_key 
# from app.models.schemas import SuccessResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats():
    """
    Get high-level statistics for the dashboard.
    """
    db = await get_db()
    
    async with db.acquire() as conn:
        # 1. Get latest scan for each repo to calculate live score
        latest_scans_query = """
            SELECT DISTINCT ON (repo_id) *
            FROM scans
            ORDER BY repo_id, created_at DESC
        """
        scans = await conn.fetch(latest_scans_query)
        
        total_repos = len(scans)
        total_violations = sum(s['total_violations'] or 0 for s in scans)
        critical_count = sum(s['critical_violations'] or 0 for s in scans)
        
        # Compliance Score: Simple heuristic (100 - penalties)
        base_score = 100
        # Heavy penalty for critical, light for others
        penalty = (critical_count * 15) + (total_violations * 2)
        compliance_score = max(0, base_score - penalty)
        
        # 2. Get pending review count
        pending_count = await conn.fetchval("SELECT COUNT(*) FROM violations WHERE status = 'pending'")
        
        # 3. Get Agent Activity (scans in last 24h)
        active_scans = await conn.fetchval("SELECT COUNT(*) FROM scans WHERE created_at > NOW() - INTERVAL '24 hours'")

    return {
        "compliance_score": compliance_score,
        "trend": -5, # TODO: Calculate real trend by comparing with previous day's snapshot
        "open_violations": total_violations,
        "critical_violations": critical_count,
        "repos_scanned": total_repos,
        "pending_reviews": pending_count,
        "active_agents_24h": active_scans
    }

@router.get("/activity")
async def get_recent_activity(limit: int = 10):
    """
    Get a unified feed of system activity (Scans, Violations).
    """
    db = await get_db()
    async with db.acquire() as conn:
        query = """
            SELECT 
                'scan' as type, 
                s.status, 
                r.full_name as source, 
                s.created_at,
                s.total_violations as details
            FROM scans s
            JOIN repos r ON s.repo_id = r.repo_id
            ORDER BY s.created_at DESC
            LIMIT $1
        """
        rows = await conn.fetch(query, limit)
        
    return [
        {
            "type": row['type'],
            "status": row['status'],
            "source": row['source'],
            "time": row['created_at'],
            "details": row['details']
        }
        for row in rows
    ]