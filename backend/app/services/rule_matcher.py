"""
Rule Matcher Service (Agent 3)
Matches compliance rules against code using RAG
"""
from typing import Dict, Any
from uuid import UUID
from loguru import logger

from app.services.embeddings import embeddings_service
from app.services.llm import llm_service
from app.database import db


class RuleMatcherService:
    """
    Agent 3: Rule Matcher
    
    Core compliance engine - matches rules to code using RAG
    """
    
    async def check_rule(
        self,
        rule_id: str,
        repo_id: UUID,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Check a single rule against a repository
        
        Args:
            rule_id: Regulation rule identifier
            repo_id: Repository UUID
            top_k: Number of similar code chunks to analyze
            
        Returns:
            Compliance check result
        """
        logger.info(f"Checking rule {rule_id} against repo {repo_id}")
        
        try:
            # Get rule text
            rule_text = await self._get_rule_text(rule_id)
            
            # Find relevant code chunks using RAG
            relevant_chunks = await self._search_code_for_rule(
                rule_text, repo_id, top_k
            )
            
            # Analyze each chunk for compliance
            findings = []
            for chunk in relevant_chunks:
                finding = await self._analyze_chunk_compliance(
                    rule_text, chunk
                )
                findings.append(finding)
            
            # Aggregate verdict
            verdict = self._aggregate_verdict(findings)
            
            return {
                "rule_id": rule_id,
                "repo_id": str(repo_id),
                "verdict": verdict,
                "findings_count": len(findings),
                "findings": findings[:5]  # Return top 5
            }
            
        except Exception as e:
            logger.error(f"Rule check failed for {rule_id}: {e}")
            raise
    
    async def _get_rule_text(self, rule_id: str) -> str:
        """Get rule text from database"""
        async with db.acquire() as conn:
            chunk = await conn.fetchrow("""
                SELECT chunk_text FROM regulation_chunks
                WHERE rule_id = $1
                ORDER BY chunk_index
                LIMIT 1
            """, rule_id)
            
            if not chunk:
                raise ValueError(f"Rule {rule_id} not found")
            
            return chunk["chunk_text"]
    
    async def _search_code_for_rule(
        self,
        rule_text: str,
        repo_id: UUID,
        top_k: int
    ) -> list:
        """Use RAG to find relevant code chunks"""
        # Generate embedding for rule
        rule_embedding = await embeddings_service.embed_text(rule_text)
        embedding_str = "[" + ",".join(map(str, rule_embedding)) + "]"
        
        # Search for similar code chunks
        async with db.acquire() as conn:
            chunks = await conn.fetch("""
                SELECT 
                    chunk_id, file_path, chunk_text, start_line, end_line,
                    1 - (embedding <=> $1::vector) as similarity
                FROM code_map
                WHERE repo_id = $2 AND embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT $3
            """, embedding_str, repo_id, top_k)
        
        return [dict(chunk) for chunk in chunks]
    
    async def _analyze_chunk_compliance(
        self,
        rule_text: str,
        chunk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze if code chunk complies with rule"""
        prompt = f"""Analyze if this code complies with the regulation requirement.

Regulation Requirement:
{rule_text}

Code from {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']}):
```
{chunk['chunk_text']}
```

Provide analysis in JSON format:
{{
    "verdict": "compliant" | "non_compliant" | "partial" | "unclear",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "evidence": "Specific code reference"
}}
"""
        
        response = await llm_service.generate([{"role": "user", "content": prompt}])
        
        try:
            import json
            analysis = json.loads(response.strip())
            analysis["file_path"] = chunk["file_path"]
            analysis["start_line"] = chunk["start_line"]
            analysis["end_line"] = chunk["end_line"]
            analysis["similarity"] = chunk.get("similarity", 0.0)
            return analysis
        except:
            return {
                "verdict": "unclear",
                "confidence": 0.0,
                "reasoning": "Failed to analyze",
                "evidence": "",
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"]
            }
    
    def _aggregate_verdict(self, findings: list) -> str:
        """Aggregate individual findings into overall verdict"""
        if not findings:
            return "unclear"
        
        verdicts = [f.get("verdict") for f in findings]
        
        # If any non-compliant, overall is non-compliant
        if "non_compliant" in verdicts:
            return "non_compliant"
        
        # If all compliant, overall is compliant
        if all(v == "compliant" for v in verdicts):
            return "compliant"
        
        # Otherwise partial
        return "partial"


# Global service instance
rule_matcher_service = RuleMatcherService()
