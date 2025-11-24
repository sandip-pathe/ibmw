from datetime import date
from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field

class AtomicRuleSpec(BaseModel):
    """Normalized Rule Card - The Brain of the System"""
    actor: str = Field(..., description="Who must act? e.g., 'Payment System Operator'")
    action: str = Field(..., description="What must be done? e.g., 'store data'")
    object: str = Field(..., description="Target of action? e.g., 'transaction data'")
    condition: Optional[str] = Field(None, description="When? e.g., 'at rest'")
    constraint: Optional[str] = Field(None, description="How? e.g., 'encrypted AES-256'")
    exception: Optional[str] = Field(None, description="Unless? e.g., 'processing abroad'")
    
    # Text for embedding generation
    full_text: str 

class RuleExtractionResult(BaseModel):
    """LLM Output Structure"""
    rules: List[AtomicRuleSpec]
    amendment_of: Optional[str] = Field(None, description="If this updates an existing rule, provide the Rule Code or Keywords")
    summary: str

class PolicyDocumentMetadata(BaseModel):
    regulator: str
    doc_type: str
    date: date
    title: str
    source_url: Optional[str] = None
    status: str = "draft"