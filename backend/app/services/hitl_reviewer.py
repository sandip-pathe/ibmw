"""
HITL Reviewer Service
Provides explanation and suggestion tools for human reviewers
"""
import json
from typing import Dict, Any, Optional
from uuid import UUID
from loguru import logger

from app.services.llm import llm_service
from app.services.embeddings import embeddings_service
from app.database import db
from app.models.schemas import HITLExplainResponse, HITLSuggestFixResponse


class HITLReviewerService:
    """
    HITL 1: Human Reviewer Assistant
    
    Helps human reviewers understand findings and make decisions
    """
    
    async def explain_finding(
        self,
        result_id: Optional[UUID] = None,
        violation_id: Optional[UUID] = None,
        scan_id: Optional[UUID] = None,
        question: str = ""
    ) -> HITLExplainResponse:
        """
        Explain a compliance finding to a human reviewer
        
        Args:
            result_id: Compliance result ID
            violation_id: Violation ID
            scan_id: Scan ID
            question: Specific question about the finding
            
        Returns:
            Detailed explanation
        """
        logger.info(f"Explaining finding: violation={violation_id}, question='{question[:50]}'")
        
        # Get finding data
        finding_data = await self._get_finding_data(
            result_id=result_id,
            violation_id=violation_id,
            scan_id=scan_id
        )
        
        if not finding_data:
            raise ValueError("No finding data found")
        
        # Build explanation using LLM
        explanation = await self._generate_explanation(finding_data, question)
        
        return explanation
    
    async def suggest_fix(
        self,
        violation_id: UUID,
        context: Optional[str] = None
    ) -> HITLSuggestFixResponse:
        """
        Generate fix suggestion for a violation
        
        Args:
            violation_id: Violation UUID
            context: Additional context from reviewer
            
        Returns:
            Fix suggestion with code and steps
        """
        logger.info(f"Generating fix suggestion for violation {violation_id}")
        
        # Get violation details
        async with db.acquire() as conn:
            violation = await conn.fetchrow("""
                SELECT * FROM violations WHERE violation_id = $1
            """, violation_id)
            
            if not violation:
                raise ValueError(f"Violation {violation_id} not found")
            
            violation_data = dict(violation)
        
        # Generate fix using LLM
        suggestion = await self._generate_fix_suggestion(violation_data, context)
        
        return suggestion
    
    async def submit_decision(
        self,
        item_id: UUID,
        decision: str,
        note: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit human review decision
        
        Args:
            item_id: Item being reviewed (violation_id, etc.)
            decision: approve, reject, request_changes
            note: Reviewer note
            changes: Requested changes
            
        Returns:
            Updated item state
        """
        logger.info(f"Review decision: {decision} for {item_id}")
        
        # For now, assume item_id is a violation_id
        async with db.acquire() as conn:
            # Update violation status based on decision
            status_map = {
                "approve": "approved",
                "reject": "rejected",
                "request_changes": "pending"
            }
            
            new_status = status_map.get(decision, "pending")
            
            await conn.execute("""
                UPDATE violations
                SET status = $2, reviewer_note = $3, reviewed_at = NOW()
                WHERE violation_id = $1
            """, item_id, new_status, note)
        
        return {
            "item_id": str(item_id),
            "decision": decision,
            "new_status": new_status
        }
    
    async def _get_finding_data(
        self,
        result_id: Optional[UUID] = None,
        violation_id: Optional[UUID] = None,
        scan_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """Get finding data from various sources"""
        async with db.acquire() as conn:
            if violation_id:
                violation = await conn.fetchrow("""
                    SELECT v.*, r.full_name as repo_name
                    FROM violations v
                    JOIN scans s ON v.scan_id = s.scan_id
                    JOIN repos r ON s.repo_id = r.repo_id
                    WHERE v.violation_id = $1
                """, violation_id)
                
                if violation:
                    return dict(violation)
            
            if scan_id:
                # Get scan summary
                scan = await conn.fetchrow("""
                    SELECT * FROM scans WHERE scan_id = $1
                """, scan_id)
                
                if scan:
                    return dict(scan)
        
        return None
    
    async def _generate_explanation(
        self,
        finding_data: Dict[str, Any],
        question: str
    ) -> HITLExplainResponse:
        """Generate detailed explanation using LLM"""
        prompt = f"""You are a compliance expert helping a human reviewer understand a finding.

Finding Details:
- Rule: {finding_data.get('rule_id', 'N/A')}
- Verdict: {finding_data.get('verdict', 'N/A')}
- Severity: {finding_data.get('severity', 'N/A')}
- File: {finding_data.get('file_path', 'N/A')}
- Explanation: {finding_data.get('explanation', 'N/A')}
- Evidence: {finding_data.get('evidence', 'N/A')}

Reviewer Question: {question}

Provide a clear, detailed explanation that:
1. Explains WHY this was flagged
2. What the regulation requires
3. What the code is doing (or not doing)
4. Related compliance concepts

Respond in JSON:
{{
    "explanation": "Detailed explanation addressing the question",
    "evidence": ["Evidence point 1", "Evidence point 2"],
    "related_rules": ["Related rule 1", "Related rule 2"],
    "confidence": 0.0-1.0
}}
"""
        
        response = await llm_service.generate([{"role": "user", "content": prompt}])
        
        try:
            result = json.loads(response.strip())
            return HITLExplainResponse(**result)
        except:
            return HITLExplainResponse(
                explanation="Unable to generate explanation",
                evidence=[],
                related_rules=[],
                confidence=0.0
            )
    
    async def _generate_fix_suggestion(
        self,
        violation_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> HITLSuggestFixResponse:
        """Generate fix suggestion using LLM"""
        prompt = f"""You are a compliance remediation expert. Suggest how to fix this violation.

Violation:
- Rule: {violation_data.get('rule_id', 'N/A')}
- File: {violation_data.get('file_path', 'N/A')}
- Lines: {violation_data.get('start_line')}-{violation_data.get('end_line')}
- Issue: {violation_data.get('explanation', 'N/A')}
- Evidence: {violation_data.get('evidence', 'N/A')}

{f"Additional Context: {context}" if context else ""}

Provide a practical fix suggestion in JSON:
{{
    "suggested_fix": "High-level description of the fix",
    "code_snippet": "Example code snippet (if applicable)",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "rationale": "Why this fix addresses the compliance requirement",
    "confidence": 0.0-1.0
}}
"""
        
        response = await llm_service.generate([{"role": "user", "content": prompt}])
        
        try:
            result = json.loads(response.strip())
            return HITLSuggestFixResponse(**result)
        except:
            return HITLSuggestFixResponse(
                suggested_fix="Unable to generate fix suggestion",
                code_snippet=None,
                steps=[],
                rationale="",
                confidence=0.0
            )


# Global service instance
hitl_reviewer_service = HITLReviewerService()
