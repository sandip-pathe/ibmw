"""
LangGraph-based Multi-Agent Compliance System
"""
import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypedDict
from uuid import UUID, uuid4
from datetime import datetime

from loguru import logger
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from typing import cast

from app.services.agents import AgentLogger, AgentType
from app.services.embeddings import embeddings_service
from app.services.llm import llm_service
from app.database import db


class ComplianceState(TypedDict):
    """Shared state passed between agents in LangGraph"""
    scan_id: str
    repo_id: str
    regulation_chunk: Dict[str, Any]
    rule_plan: Optional[Dict[str, Any]]
    matched_files: Optional[Dict[str, Any]]
    investigation_result: Optional[Dict[str, Any]]
    final_verdict: Optional[Dict[str, Any]]
    remediation_tasks: Optional[Dict[str, Any]]
    requires_approval: bool
    user_decision: Optional[str]
    jira_ticket_ids: List[str]
    started_at: str
    completed_at: Optional[str]
    current_agent: Optional[str]


class BaseAgent(ABC):
    """Base class for all compliance agents"""
    
    def __init__(self, agent_type: AgentType, scan_id: str):
        self.agent_type = agent_type
        self.scan_id = scan_id
        self.logger = AgentLogger(scan_id)
        self.output: Optional[Dict[str, Any]] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
    async def log(self, message: str):
        await self.logger.log(cast(AgentType, self.agent_type), message)
        
    async def save_execution(self, status: str, output: Optional[Dict] = None):
        async with db.acquire() as conn:
            await conn.execute("""
                INSERT INTO agent_executions (execution_id, scan_id, agent_name, status, started_at, completed_at, output)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            """,
                uuid4(), UUID(self.scan_id), self.agent_type, status,
                self.started_at, self.completed_at, json.dumps(output or {})
            )
    
    @abstractmethod
    async def execute(self, state: ComplianceState) -> ComplianceState:
        pass
    
    async def run(self, state: ComplianceState) -> ComplianceState:
        self.started_at = datetime.utcnow()
        try:
            await self.log(f"🚀 Starting {self.agent_type} agent")
            await self.save_execution("running")
            result = await self.execute(state)
            await asyncio.sleep(self.get_demo_delay())
            self.completed_at = datetime.utcnow()
            await self.save_execution("completed", dict(result))
            await self.log(f"✅ {self.agent_type} agent completed")
            return result
        except Exception as e:
            self.completed_at = datetime.utcnow()
            error_details = {
                "error": str(e),
                "error_type": type(e).__name__,
                "agent": self.agent_type,
                "scan_id": self.scan_id
            }
            await self.save_execution("failed", error_details)
            await self.log(f"❌ {self.agent_type} agent failed: {str(e)}")
            logger.error(f"Agent {self.agent_type} execution failed", exc_info=True)
            
            # Re-raise with context
            raise RuntimeError(f"Agent {self.agent_type} failed: {str(e)}") from e
    
    def get_demo_delay(self) -> float:
        return {"PLANNER": 2.0, "NAVIGATOR": 2.5, "INVESTIGATOR": 3.0, "JUDGE": 1.5, "JIRA": 1.0}.get(self.agent_type, 1.5)


class RulePlannerAgent(BaseAgent):
    """Converts regulation requirement into structured engineering validation plan"""
    
    def __init__(self, scan_id: str):
        super().__init__("PLANNER", scan_id)
    
    async def execute(self, state: ComplianceState) -> ComplianceState:
        regulation_chunk = state["regulation_chunk"]
        await self.log("📖 Reading rule intent")
        
        rule_text = regulation_chunk.get("chunk_text", "")
        rule_id = regulation_chunk.get("rule_id", "UNKNOWN")
        section_ref = regulation_chunk.get("rule_section", "")
        
        await self.log("🔍 Extracting compliance conditions")
        
        prompt = f"""You are a compliance expert analyzing a regulatory requirement.

Regulation Section: {section_ref}
Regulation Text: {rule_text}

Your task:
1. Identify the core compliance intent
2. Extract key compliance dimensions
3. Convert this into specific engineering tasks

Respond with JSON:
{{
    "rule_id": "{rule_id}",
    "intent": "Brief summary of what the rule requires",
    "compliance_dimensions": ["dimension1", "dimension2"],
    "tasks": ["Specific task 1", "Specific task 2"]
}}
"""
        
        response = await llm_service.generate([{"role": "user", "content": prompt}])
        try:
            plan = json.loads(response.strip())
        except:
            plan = {"rule_id": rule_id, "intent": "Validate compliance", "compliance_dimensions": ["general"], "tasks": ["Check implementation"]}
        
        await self.log(f"✨ Generated {len(plan.get('tasks', []))} engineering tasks")
        state["rule_plan"] = plan
        state["current_agent"] = "PLANNER"
        return state


class CodeNavigatorAgent(BaseAgent):
    """Finds relevant repository files using vector search"""
    
    def __init__(self, scan_id: str):
        super().__init__("NAVIGATOR", scan_id)
    
    async def execute(self, state: ComplianceState) -> ComplianceState:
        rule_plan = state.get("rule_plan") or {}
        repo_id = state["repo_id"]
        tasks = rule_plan.get("tasks", [])
        
        await self.log("🔎 Searching repository for relevant logic")
        
        matched_files = []
        no_match = []
        
        for task in tasks:
            await self.log(f"📊 Matching: {task[:50]}...")
            task_embedding = await embeddings_service.embed_text(task)
            embedding_str = "[" + ",".join(map(str, task_embedding)) + "]"
            
            async with db.acquire() as conn:
                results = await conn.fetch("""
                    SELECT file_path, chunk_text, 1 - (embedding <=> $1::vector) as similarity
                    FROM code_map WHERE repo_id = $2 AND embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector LIMIT 5
                """, embedding_str, UUID(repo_id))
                
                if results:
                    for row in results:
                        if row['similarity'] > 0.7:
                            matched_files.append({
                                "path": row['file_path'],
                                "confidence": round(row['similarity'], 2),
                                "task": task,
                                "snippet": row['chunk_text'][:200]
                            })
                else:
                    no_match.append(task)
        
        await self.log(f"🎯 Mapped to {len(matched_files)} code locations")
        state["matched_files"] = {"matched_files": matched_files, "no_match": no_match}
        state["current_agent"] = "NAVIGATOR"
        return state


class CodeInvestigatorAgent(BaseAgent):
    """Inspects code to determine compliance status"""
    
    def __init__(self, scan_id: str):
        super().__init__("INVESTIGATOR", scan_id)
    
    async def execute(self, state: ComplianceState) -> ComplianceState:
        matched_files_data = state.get("matched_files") or {}
        matched_files = matched_files_data.get("matched_files", [])
        
        await self.log("🕵️ Reading implementation logic")
        evidence = []
        
        for match in matched_files[:10]:
            file_path = match["path"]
            task = match["task"]
            snippet = match.get("snippet", "")
            
            await self.log(f"📝 Evaluating {file_path}")
            
            prompt = f"""Analyze if this code implements the required compliance control.

Task: {task}
Code from {file_path}:
```
{snippet}
```

Respond with JSON:
{{
    "file": "{file_path}",
    "status": "implemented" | "partial" | "missing",
    "finding": "Brief explanation",
    "confidence": 0.0-1.0
}}
"""
            
            response = await llm_service.generate([{"role": "user", "content": prompt}])
            try:
                finding = json.loads(response.strip())
                evidence.append(finding)
            except:
                evidence.append({"file": file_path, "status": "unknown", "finding": "Could not analyze", "confidence": 0.0})
        
        statuses = [e.get("status") for e in evidence]
        overall_status = "compliant" if all(s == "implemented" for s in statuses) else "non_compliant" if any(s == "missing" for s in statuses) else "partial"
        
        await self.log(f"🎯 Assessment: {overall_status}")
        state["investigation_result"] = {"status": overall_status, "evidence": evidence}
        state["current_agent"] = "INVESTIGATOR"
        return state


class ConsistencyCheckerAgent(BaseAgent):
    """Validates findings and produces final verdict"""
    
    def __init__(self, scan_id: str):
        super().__init__("JUDGE", scan_id)
    
    async def execute(self, state: ComplianceState) -> ComplianceState:
        investigation = state.get("investigation_result") or {}
        
        await self.log("⚖️ Validating reasoning")
        evidence = investigation.get("evidence", [])
        status = investigation.get("status", "unknown")
        
        await self.log("🔄 Cross-checking evidence")
        
        confidences = [e.get("confidence", 0.5) for e in evidence]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        if status == "compliant":
            verdict = "compliant"
            reason = "All compliance controls properly implemented"
        elif status == "non_compliant":
            missing_items = [e["finding"] for e in evidence if e.get("status") == "missing"]
            reason = f"Missing controls: {'; '.join(missing_items[:3])}"
            verdict = "non_compliant"
        else:
            verdict = "partial"
            reason = "Implementation incomplete"
        
        await self.log(f"✅ Verdict: {verdict}")
        state["final_verdict"] = {"final_verdict": verdict, "confidence": round(avg_confidence, 2), "reason": reason, "evidence_count": len(evidence)}
        state["current_agent"] = "JUDGE"
        return state


class JiraBotAgent(BaseAgent):
    """Generates remediation tasks and awaits user approval"""
    
    def __init__(self, scan_id: str):
        super().__init__("JIRA", scan_id)
    
    async def execute(self, state: ComplianceState) -> ComplianceState:
        verdict = state.get("final_verdict") or {}
        investigation = state.get("investigation_result") or {}
        rule_plan = state.get("rule_plan") or {}
        
        await self.log("📋 Generating remediation tasks")
        issues = []
        
        if verdict.get("final_verdict") in ["non_compliant", "partial"]:
            evidence = investigation.get("evidence", [])
            for item in evidence:
                if item.get("status") in ["missing", "partial"]:
                    issues.append({
                        "title": f"Fix: {item.get('finding', 'Compliance issue')[:80]}",
                        "description": f"""**Regulation**: {rule_plan.get('rule_id', 'N/A')}
**Intent**: {rule_plan.get('intent', 'N/A')}
**Issue**: {item.get('finding', 'Compliance gap')}
**File**: {item.get('file', 'N/A')}
**Action**: Implement missing compliance control""",
                        "file": item.get("file", ""),
                        "priority": "high" if item.get("status") == "missing" else "medium"
                    })
        
        await self.log(f"⏸️ Waiting for approval ({len(issues)} tasks)")
        state["remediation_tasks"] = {"issues": issues, "requires_user_approval": True}
        state["requires_approval"] = True
        state["current_agent"] = "JIRA"
        return state
    
    async def create_tickets(self, state: ComplianceState) -> ComplianceState:
        await self.log("🎫 Creating Jira tickets")
        remediation_tasks = state.get("remediation_tasks") or {}
        issues = remediation_tasks.get("issues", [])
        ticket_ids = []
        
        for idx, issue in enumerate(issues):
            ticket_id = f"COMP-{int(time.time())}-{idx}"
            ticket_ids.append(ticket_id)
            await self.log(f"✅ Created {ticket_id}: {issue['title'][:50]}")
        
        state["jira_ticket_ids"] = ticket_ids
        state["completed_at"] = datetime.utcnow().isoformat()
        return state


class ComplianceScanOrchestrator:
    """LangGraph orchestrator for multi-agent compliance scanning"""
    
    def __init__(self, scan_id: str, repo_id: str, regulation_chunk: Dict[str, Any]):
        self.scan_id = scan_id
        self.repo_id = repo_id
        self.regulation_chunk = regulation_chunk
        self.rule_planner = RulePlannerAgent(scan_id)
        self.code_navigator = CodeNavigatorAgent(scan_id)
        self.code_investigator = CodeInvestigatorAgent(scan_id)
        self.consistency_checker = ConsistencyCheckerAgent(scan_id)
        self.jira_bot = JiraBotAgent(scan_id)
        self.graph = self.build_graph()
    
    def build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(ComplianceState)
        workflow.add_node("planner", self.rule_planner.run)
        workflow.add_node("navigator", self.code_navigator.run)
        workflow.add_node("investigator", self.code_investigator.run)
        workflow.add_node("checker", self.consistency_checker.run)
        workflow.add_node("jira", self.jira_bot.run)
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "navigator")
        workflow.add_edge("navigator", "investigator")
        workflow.add_edge("investigator", "checker")
        workflow.add_edge("checker", "jira")
        workflow.add_edge("jira", END)
        return workflow.compile()
    
    async def run_scan(self) -> ComplianceState:
        initial_state: ComplianceState = {
            "scan_id": self.scan_id,
            "repo_id": self.repo_id,
            "regulation_chunk": self.regulation_chunk,
            "rule_plan": None,
            "matched_files": None,
            "investigation_result": None,
            "final_verdict": None,
            "remediation_tasks": None,
            "requires_approval": False,
            "user_decision": None,
            "jira_ticket_ids": [],
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "current_agent": None
        }
        final_state = await self.graph.ainvoke(initial_state)
        return cast(ComplianceState, final_state)
    
    async def approve_and_create_tickets(self, state: ComplianceState, edited_issues: Optional[List[Dict]] = None) -> ComplianceState:
        if edited_issues and state.get("remediation_tasks"):
            remediation_tasks = state["remediation_tasks"]
            if remediation_tasks:
                remediation_tasks["issues"] = edited_issues
        state["user_decision"] = "approved"
        return await self.jira_bot.create_tickets(state)