from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field

class JobStatus(BaseModel):
    job_id: str
    job_type: str
    status: str  # 'queued', 'running', 'completed', 'failed'
    repo_id: Optional[UUID] = None
    payload: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
