"""
Compliance scanning orchestration service
Manages multi-agent compliance scans using LangGraph
"""
import json
from uuid import UUID, uuid4
from typing import Dict, Any, Optional, List
from loguru import logger

from app.services.langgraph_agents import ComplianceScanOrchestrator
from app.database import db


async def start_compliance_scan(repo_id: str, regulation_chunk: Dict[str, Any]) -> str:
    """
    Start a new compliance scan
    
    Args:
        repo_id: Repository UUID
        regulation_chunk: Regulation chunk to check compliance against
        
    Returns:
        scan_id: UUID of the scan
    """
    scan_id = str(uuid4())
    
    logger.info(f"Starting compliance scan {scan_id} for repo {repo_id}")
    
    # Create scan record
    async with db.acquire() as conn:
        await conn.execute("""
            INSERT INTO compliance_scans (
                scan_id, repo_id, regulation_id, status
            )
            VALUES ($1, $2, $3, $4)
        """, UUID(scan_id), UUID(repo_id), regulation_chunk.get("rule_id", "UNKNOWN"), "running")
    
    # Create orchestrator
    orchestrator = ComplianceScanOrchestrator(scan_id, repo_id, regulation_chunk)
    
    try:
        # Run scan (will pause at approval)
        final_state = await orchestrator.run_scan()
        
        # Save final state
        async with db.acquire() as conn:
            await conn.execute("""
                UPDATE compliance_scans SET
                    rule_plan = $1::jsonb,
                    matched_files = $2::jsonb,
                    investigation_result = $3::jsonb,
                    final_verdict = $4::jsonb,
                    remediation_tasks = $5::jsonb,
                    requires_user_action = $6,
                    status = $7
                WHERE scan_id = $8
            """,
                json.dumps(final_state.get("rule_plan")),
                json.dumps(final_state.get("matched_files")),
                json.dumps(final_state.get("investigation_result")),
                json.dumps(final_state.get("final_verdict")),
                json.dumps(final_state.get("remediation_tasks")),
                final_state.get("requires_approval", False),
                "waiting_approval" if final_state.get("requires_approval") else "completed",
                UUID(scan_id)
            )
        
        logger.info(f"Compliance scan {scan_id} completed with status: {final_state.get('final_verdict', {}).get('final_verdict')}")
        
    except Exception as e:
        logger.error(f"Compliance scan {scan_id} failed: {e}")
        async with db.acquire() as conn:
            await conn.execute("""
                UPDATE compliance_scans SET status = 'failed' WHERE scan_id = $1
            """, UUID(scan_id))
        raise
    
    return scan_id


async def get_scan_status(scan_id: str) -> Dict[str, Any]:
    """
    Get the current status of a compliance scan
    
    Args:
        scan_id: Scan UUID
        
    Returns:
        Scan status and results
    """
    async with db.acquire() as conn:
        scan = await conn.fetchrow("""
            SELECT * FROM compliance_scans WHERE scan_id = $1
        """, UUID(scan_id))
        
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        
        # Get agent executions
        executions = await conn.fetch("""
            SELECT * FROM agent_executions 
            WHERE scan_id = $1 
            ORDER BY started_at
        """, UUID(scan_id))
        
        return {
            "scan_id": str(scan["scan_id"]),
            "repo_id": str(scan["repo_id"]),
            "regulation_id": scan["regulation_id"],
            "status": scan["status"],
            "rule_plan": json.loads(scan["rule_plan"]) if scan["rule_plan"] else None,
            "matched_files": json.loads(scan["matched_files"]) if scan["matched_files"] else None,
            "investigation_result": json.loads(scan["investigation_result"]) if scan["investigation_result"] else None,
            "final_verdict": json.loads(scan["final_verdict"]) if scan["final_verdict"] else None,
            "remediation_tasks": json.loads(scan["remediation_tasks"]) if scan["remediation_tasks"] else None,
            "requires_user_action": scan["requires_user_action"],
            "user_decision": scan["user_decision"],
            "jira_ticket_ids": json.loads(scan["jira_ticket_ids"]) if scan["jira_ticket_ids"] else [],
            "started_at": scan["started_at"].isoformat() if scan["started_at"] else None,
            "completed_at": scan["completed_at"].isoformat() if scan["completed_at"] else None,
            "agent_executions": [
                {
                    "execution_id": str(e["execution_id"]),
                    "agent_name": e["agent_name"],
                    "status": e["status"],
                    "started_at": e["started_at"].isoformat() if e["started_at"] else None,
                    "completed_at": e["completed_at"].isoformat() if e["completed_at"] else None,
                    "output": json.loads(e["output"]) if e["output"] else None
                }
                for e in executions
            ]
        }


async def approve_remediation(scan_id: str, edited_issues: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Approve remediation tasks and create Jira tickets
    
    Args:
        scan_id: Scan UUID
        edited_issues: Optional list of edited remediation tasks
        
    Returns:
        Updated scan status with Jira ticket IDs
    """
    logger.info(f"Approving remediation for scan {scan_id}")
    
    # Get scan state
    async with db.acquire() as conn:
        scan = await conn.fetchrow("""
            SELECT * FROM compliance_scans WHERE scan_id = $1
        """, UUID(scan_id))
        
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        
        if scan["status"] != "waiting_approval":
            raise ValueError(f"Scan {scan_id} is not waiting for approval (status: {scan['status']})")
        
        # Recreate state
        remediation_tasks = json.loads(scan["remediation_tasks"]) if scan["remediation_tasks"] else {}
        
        state = {
            "scan_id": scan_id,
            "repo_id": str(scan["repo_id"]),
            "regulation_chunk": {},
            "remediation_tasks": remediation_tasks,
            "jira_ticket_ids": [],
            "rule_plan": None,
            "matched_files": None,
            "investigation_result": None,
            "final_verdict": None,
            "requires_approval": False,
            "user_decision": None,
            "started_at": "",
            "completed_at": None,
            "current_agent": None
        }
        
        # Create orchestrator
        orchestrator = ComplianceScanOrchestrator(scan_id, str(scan["repo_id"]), {})
        
        # Approve and create tickets
        final_state = await orchestrator.approve_and_create_tickets(state, edited_issues)
        
        # Update database
        await conn.execute("""
            UPDATE compliance_scans SET
                user_decision = 'approved',
                jira_ticket_ids = $1::jsonb,
                status = 'completed',
                completed_at = NOW()
            WHERE scan_id = $2
        """, json.dumps(final_state.get("jira_ticket_ids", [])), UUID(scan_id))
        
        logger.info(f"Created {len(final_state.get('jira_ticket_ids', []))} Jira tickets for scan {scan_id}")
        
        return {
            "scan_id": scan_id,
            "ticket_ids": final_state.get("jira_ticket_ids", []),
            "status": "completed"
        }


async def decline_remediation(scan_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Decline remediation tasks
    
    Args:
        scan_id: Scan UUID
        reason: Optional reason for declining
        
    Returns:
        Updated scan status
    """
    logger.info(f"Declining remediation for scan {scan_id}")
    
    async with db.acquire() as conn:
        await conn.execute("""
            UPDATE compliance_scans SET
                user_decision = 'declined',
                status = 'completed',
                completed_at = NOW()
            WHERE scan_id = $1
        """, UUID(scan_id))
    
    return {
        "scan_id": scan_id,
        "status": "declined",
        "reason": reason
    }


async def get_scan_logs(scan_id: str, start_index: int = 0) -> List[Dict[str, Any]]:
    """
    Get agent logs for a scan from Redis
    
    Args:
        scan_id: Scan UUID
        start_index: Starting index for logs
        
    Returns:
        List of log entries
    """
    from app.services.agents import get_scan_logs
    
    logs = await get_scan_logs(scan_id)
    return logs[start_index:] if start_index > 0 else logs
