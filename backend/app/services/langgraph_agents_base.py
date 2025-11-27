# LangGraph Multi-Agent System - Base Classes
import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypedDict
from uuid import UUID, uuid4
from datetime import datetime
from loguru import logger

from app.services.agents import AgentLogger, AgentType
from app.database import db


class ComplianceState(TypedDict):
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
    def __init__(self, agent_type: AgentType, scan_id: str):
        self.agent_type = agent_type
        self.scan_id = scan_id
        self.logger = AgentLogger(scan_id)
        self.output: Optional[Dict[str, Any]] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
    async def log(self, message: str):
        await self.logger.log(self.agent_type, message)
        
    async def save_execution(self, status: str, output: Optional[Dict] = None):
        async with db.acquire() as conn:
            await conn.execute(
                """INSERT INTO agent_executions (execution_id, scan_id, agent_name, status, started_at, completed_at, output)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)""",
                uuid4(), UUID(self.scan_id), self.agent_type, status, self.started_at, self.completed_at, json.dumps(output or {})
            )
    
    @abstractmethod
    async def execute(self, state: ComplianceState) -> ComplianceState:
        pass
    
    async def run(self, state: ComplianceState) -> ComplianceState:
        self.started_at = datetime.utcnow()
        try:
            await self.log(f'Starting {self.agent_type} agent')
            await self.save_execution('running')
            result = await self.execute(state)
            await asyncio.sleep(self.get_demo_delay())
            self.completed_at = datetime.utcnow()
            self.output = result
            await self.save_execution('completed', result)
            await self.log(f'{self.agent_type} agent completed')
            return result
        except Exception as e:
            self.completed_at = datetime.utcnow()
            await self.save_execution('failed', {'error': str(e)})
            await self.log(f'{self.agent_type} agent failed: {str(e)}')
            raise
    
    def get_demo_delay(self) -> float:
        delays = {'PLANNER': 2.0, 'NAVIGATOR': 2.5, 'INVESTIGATOR': 3.0, 'JUDGE': 1.5, 'JIRA': 1.0}
        return delays.get(self.agent_type, 1.5)
