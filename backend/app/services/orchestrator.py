"""
Audit Case Orchestrator (Agent 0)
Manages complete audit workflow with state tracking and resumability
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from loguru import logger

from app.database import db
from app.models.schemas import AuditCaseState, ComplianceResult


class AuditOrchestrator:
    """
    Agent 0: Case Orchestrator
    
    Responsibilities:
    - Manage audit case lifecycle
    - Track state and progress
    - Coordinate other agents
    - Handle errors and resumability
    """
    
    def __init__(self):
        self.workflow_steps = [
            "rule_ingestion",
            "code_scanning", 
            "compliance_checking",
            "report_generation"
        ]
    
    async def start_audit(
        self,
        repo_id: UUID,
        regulation_ids: List[str],
        options: Dict[str, Any] = None
    ) -> UUID:
        """
        Start a new audit case
        
        Args:
            repo_id: Repository UUID
            regulation_ids: List of regulation identifiers
            options: Additional options
            
        Returns:
            case_id: UUID of the audit case
        """
        case_id = uuid4()
        options = options or {}
        
        logger.info(f"Starting audit case {case_id} for repo {repo_id}")
        
        # Create case record
        async with db.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_cases (
                    case_id, repo_id, regulation_ids, status, 
                    current_step, steps_completed, steps_pending, options
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
            """,
                case_id,
                repo_id,
                regulation_ids,
                "running",
                self.workflow_steps[0],
                [],
                self.workflow_steps,
                json.dumps(options)
            )
        
        # Start workflow asynchronously
        # In production, use background task or queue
        try:
            await self._execute_workflow(case_id)
        except Exception as e:
            logger.error(f"Audit case {case_id} failed: {e}")
            await self._update_case_status(case_id, "failed", error_message=str(e))
            raise
        
        return case_id
    
    async def _execute_workflow(self, case_id: UUID) -> None:
        """Execute the audit workflow steps"""
        logger.info(f"Executing workflow for case {case_id}")
        
        try:
            # Step 1: Rule Ingestion
            await self._step_rule_ingestion(case_id)
            
            # Step 2: Code Scanning
            await self._step_code_scanning(case_id)
            
            # Step 3: Compliance Checking
            await self._step_compliance_checking(case_id)
            
            # Step 4: Report Generation (pauses for approval)
            await self._step_report_generation(case_id)
            
        except Exception as e:
            logger.error(f"Workflow execution failed for case {case_id}: {e}")
            raise
    
    async def _step_rule_ingestion(self, case_id: UUID) -> None:
        """Step 1: Ingest regulation rules"""
        logger.info(f"Case {case_id}: Starting rule ingestion")
        
        case_data = await self._get_case_data(case_id)
        regulation_ids = case_data["regulation_ids"]
        
        # Get or sync regulation chunks
        async with db.acquire() as conn:
            chunks_processed = 0
            for reg_id in regulation_ids:
                chunks = await conn.fetch("""
                    SELECT chunk_id, rule_id, chunk_text, embedding
                    FROM regulation_chunks
                    WHERE rule_id = $1
                """, reg_id)
                chunks_processed += len(chunks)
            
            logger.info(f"Case {case_id}: Processed {chunks_processed} regulation chunks")
        
        # Update case
        await self._mark_step_complete(
            case_id,
            "rule_ingestion",
            result={"chunks_processed": chunks_processed, "regulation_ids": regulation_ids}
        )
    
    async def _step_code_scanning(self, case_id: UUID) -> None:
        """Step 2: Scan repository code"""
        logger.info(f"Case {case_id}: Starting code scanning")
        
        case_data = await self._get_case_data(case_id)
        repo_id = case_data["repo_id"]
        
        # Check if repo is already indexed
        async with db.acquire() as conn:
            repo = await conn.fetchrow("""
                SELECT repo_id, total_chunks, last_synced_at
                FROM repos
                WHERE repo_id = $1
            """, repo_id)
            
            chunks_count = repo["total_chunks"] or 0
            
            # If not indexed or stale, trigger indexing
            if chunks_count == 0:
                from app.services.indexing_worker import index_repository
                result = await index_repository(repo_id)
                chunks_count = result.get("chunks_created", 0)
            
            logger.info(f"Case {case_id}: Code map has {chunks_count} chunks")
        
        await self._mark_step_complete(
            case_id,
            "code_scanning",
            result={"chunks_indexed": chunks_count, "repo_id": str(repo_id)}
        )
    
    async def _step_compliance_checking(self, case_id: UUID) -> None:
        """Step 3: Check compliance against rules"""
        logger.info(f"Case {case_id}: Starting compliance checking")
        
        case_data = await self._get_case_data(case_id)
        repo_id = case_data["repo_id"]
        regulation_ids = case_data["regulation_ids"]
        
        # Run compliance checks for each regulation
        from app.services.compliance_scanner import start_compliance_scan
        
        scan_results = []
        for reg_id in regulation_ids:
            # Get regulation chunks
            async with db.acquire() as conn:
                chunks = await conn.fetch("""
                    SELECT chunk_id, rule_id, rule_section, chunk_text
                    FROM regulation_chunks
                    WHERE rule_id = $1
                    LIMIT 5
                """, reg_id)
            
            # Run scans
            for chunk in chunks:
                scan_id = await start_compliance_scan(
                    repo_id=str(repo_id),
                    regulation_chunk=dict(chunk)
                )
                scan_results.append(scan_id)
        
        logger.info(f"Case {case_id}: Completed {len(scan_results)} compliance scans")
        
        await self._mark_step_complete(
            case_id,
            "compliance_checking",
            result={"scans_completed": len(scan_results), "scan_ids": scan_results}
        )
    
    async def _step_report_generation(self, case_id: UUID) -> None:
        """Step 4: Generate report and pause for approval"""
        logger.info(f"Case {case_id}: Starting report generation")
        
        case_data = await self._get_case_data(case_id)
        
        # Collect all scan results
        compliance_check_result = case_data.get("compliance_check_result") or {}
        scan_ids = compliance_check_result.get("scan_ids", [])
        
        # Build report outline
        from app.services.report_generator import build_report_outline
        
        outline = await build_report_outline(case_id, scan_ids)
        
        # Pause for approval
        await self._update_case_status(
            case_id,
            "waiting_approval",
            current_step="report_generation"
        )
        
        async with db.acquire() as conn:
            await conn.execute("""
                UPDATE audit_cases
                SET requires_approval = TRUE,
                    report_data = $2::jsonb
                WHERE case_id = $1
            """, case_id, json.dumps(outline))
        
        logger.info(f"Case {case_id}: Paused for approval")
    
    async def resume_audit(self, case_id: UUID) -> Dict[str, Any]:
        """Resume a paused audit case"""
        logger.info(f"Resuming audit case {case_id}")
        
        case_data = await self._get_case_data(case_id)
        
        if case_data["status"] != "waiting_approval":
            raise ValueError(f"Case {case_id} cannot be resumed (status: {case_data['status']})")
        
        # Complete report generation
        await self._finalize_report(case_id)
        
        return {
            "case_id": str(case_id),
            "repo_id": str(case_data["repo_id"]),
            "status": "completed",
            "message": "Audit completed successfully"
        }
    
    async def _finalize_report(self, case_id: UUID) -> None:
        """Finalize and generate report"""
        logger.info(f"Finalizing report for case {case_id}")
        
        from app.services.report_generator import generate_html_report
        
        report_html = await generate_html_report(case_id)
        
        await self._mark_step_complete(
            case_id,
            "report_generation",
            result={"report_generated": True, "format": "html"}
        )
        
        await self._update_case_status(case_id, "completed")
    
    async def get_case_state(self, case_id: UUID) -> AuditCaseState:
        """Get current state of audit case"""
        case_data = await self._get_case_data(case_id)
        
        # Calculate progress
        total_steps = len(self.workflow_steps)
        completed_steps = len(case_data.get("steps_completed", []))
        progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return AuditCaseState(
            case_id=case_data["case_id"],
            repo_id=case_data["repo_id"],
            regulation_ids=case_data["regulation_ids"],
            status=case_data["status"],
            current_step=case_data.get("current_step"),
            steps_completed=case_data.get("steps_completed", []),
            steps_pending=case_data.get("steps_pending", []),
            error_message=case_data.get("error_message"),
            rule_ingestion_result=case_data.get("rule_ingestion_result"),
            code_scan_result=case_data.get("code_scan_result"),
            compliance_check_result=case_data.get("compliance_check_result"),
            report_data=case_data.get("report_data"),
            requires_approval=case_data.get("requires_approval", False),
            approval_items=case_data.get("approval_items", []),
            user_decision=case_data.get("user_decision"),
            started_at=case_data["started_at"],
            updated_at=case_data["updated_at"],
            completed_at=case_data.get("completed_at")
        )
    
    async def _get_case_data(self, case_id: UUID) -> Dict[str, Any]:
        """Get case data from database"""
        async with db.acquire() as conn:
            case = await conn.fetchrow("""
                SELECT * FROM audit_cases WHERE case_id = $1
            """, case_id)
            
            if not case:
                raise ValueError(f"Audit case {case_id} not found")
            
            return dict(case)
    
    async def _update_case_status(
        self,
        case_id: UUID,
        status: str,
        current_step: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update case status"""
        async with db.acquire() as conn:
            if status == "completed":
                await conn.execute("""
                    UPDATE audit_cases
                    SET status = $2, current_step = $3, error_message = $4,
                        completed_at = NOW(), updated_at = NOW()
                    WHERE case_id = $1
                """, case_id, status, current_step, error_message)
            else:
                await conn.execute("""
                    UPDATE audit_cases
                    SET status = $2, current_step = $3, error_message = $4,
                        updated_at = NOW()
                    WHERE case_id = $1
                """, case_id, status, current_step, error_message)
    
    async def _mark_step_complete(
        self,
        case_id: UUID,
        step_name: str,
        result: Dict[str, Any]
    ) -> None:
        """Mark a workflow step as complete"""
        logger.info(f"Case {case_id}: Completed step '{step_name}'")
        
        async with db.acquire() as conn:
            # Get current state
            case = await conn.fetchrow("""
                SELECT steps_completed, steps_pending FROM audit_cases
                WHERE case_id = $1
            """, case_id)
            
            steps_completed = list(case["steps_completed"] or [])
            steps_pending = list(case["steps_pending"] or [])
            
            # Update steps
            if step_name not in steps_completed:
                steps_completed.append(step_name)
            if step_name in steps_pending:
                steps_pending.remove(step_name)
            
            # Determine next step
            next_step = None
            for step in self.workflow_steps:
                if step not in steps_completed:
                    next_step = step
                    break
            
            # Update case
            result_field = f"{step_name}_result"
            await conn.execute(f"""
                UPDATE audit_cases
                SET steps_completed = $2,
                    steps_pending = $3,
                    current_step = $4,
                    {result_field} = $5::jsonb,
                    updated_at = NOW()
                WHERE case_id = $1
            """, case_id, steps_completed, steps_pending, next_step, json.dumps(result))


# Global orchestrator instance
audit_orchestrator = AuditOrchestrator()
