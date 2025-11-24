import hashlib
import json
from datetime import date
from typing import Union, List, Optional
from uuid import UUID

from loguru import logger
from pydantic import ValidationError

from app.database import db
from app.services.llm import llm_service
from app.services.embeddings import embeddings_service
from app.models.regulation import AtomicRuleSpec, PolicyDocumentMetadata, RuleExtractionResult

# Prompt to turn raw text into structured "Rule Cards"
RULE_EXTRACTION_PROMPT = """
You are a legal analyst converting Indian Financial Regulations (RBI/SEBI) into atomic computing rules.

Input Text:
{text}

Context:
Document: {doc_title}
Regulator: {regulator}

Task:
1. Extract atomic rules. Split complex paragraphs into specific requirements.
2. Identify Actor, Action, Object, Constraints, and Exceptions.
3. CRITICAL: Determine if this is an AMENDMENT. Does it say "In partial modification of..." or "Reference Master Direction X"?
   If yes, extract the reference or the likely Rule Code it is modifying into the 'amendment_of' field.

Output JSON:
{{
  "rules": [
    {{
      "actor": "string",
      "action": "string",
      "object": "string",
      "condition": "string",
      "constraint": "string",
      "exception": "string",
      "full_text": "string"
    }}
  ],
  "amendment_of": "string or null", 
  "summary": "string"
}}
"""

class RegulationIngestionService:
    
    async def ingest_document(
        self, 
        content: Union[bytes, str], 
        filename: str, 
        metadata: dict
    ) -> UUID:
        """
        Ingests a document (HTML string or PDF bytes).
        1. Stores raw doc metadata.
        2. Extracts text.
        3. Calls LLM to normalize rules.
        4. Handles Amendments (Versioning).
        5. Stores Vectors.
        """
        logger.info(f"Ingesting document: {filename} ({metadata['status']})")

        # 1. Store Document Metadata
        content_hash = self._compute_hash(content)
        
        # Check for duplicates
        if await self._is_duplicate(content_hash, metadata.get('source_url')):
            logger.info(f"Duplicate document detected: {filename}")
            # If it's a draft scan, we might return existing ID, but for now just proceed
            # In a real app, we'd handle this more gracefully
        
        doc_id = await self._store_document(filename, metadata, content_hash)
        
        # 2. Text Extraction
        text_content = ""
        if isinstance(content, str):
            text_content = content # HTML content is already text
        else:
            text_content = self._extract_text_from_pdf(content)
            
        # 3. LLM Normalization (Chunking logic omitted for brevity, assuming manageable size for demo)
        # For a full Master Direction (50 pages), you would loop this chunk by chunk.
        # For Live RSS updates (circulars), the text is usually small enough for one context window.
        
        try:
            llm_response = await llm_service.generate(
                messages=[{"role": "user", "content": RULE_EXTRACTION_PROMPT.format(
                    text=text_content[:15000],  # Limit context for demo
                    doc_title=filename, 
                    regulator=metadata['regulator']
                )}],
                # In production, use response_format={"type": "json_object"} with GPT-4-Turbo
            )
            
            # Clean LLM response (sometimes it adds markdown code blocks)
            cleaned_json = llm_response.replace("```json", "").replace("```", "")
            data = json.loads(cleaned_json)
            extraction = RuleExtractionResult(**data)
            
            logger.info(f"Extracted {len(extraction.rules)} rules from {filename}")

            # 4. Store Rules & Vectors
            for i, rule_spec in enumerate(extraction.rules):
                # Generate a Rule Code
                # If it's an amendment, try to find the parent code, otherwise generate new
                rule_code = await self._determine_rule_code(
                    metadata['regulator'], 
                    extraction.amendment_of, 
                    i, 
                    rule_spec.action
                )
                
                # Version Logic
                version = 1
                prev_rule = await self._find_active_rule(rule_code)
                if prev_rule:
                    version = prev_rule['version'] + 1
                    logger.info(f"Creating version {version} for rule {rule_code}")

                # Store Rule
                rule_id = await self._store_rule(
                    doc_id, rule_code, rule_spec, version, metadata['status'] == 'active'
                )
                
                # Store Vector
                semantic_text = f"{rule_spec.actor} must {rule_spec.action} {rule_spec.object}. {rule_spec.constraint}"
                embedding = await embeddings_service.embed_text(semantic_text)
                await self._store_vector(rule_id, rule_spec.full_text, embedding)

                # Handle Superseding
                if prev_rule and metadata['status'] == 'active':
                    await self._mark_superseded(prev_rule['rule_id'], rule_id)
                    
        except Exception as e:
            logger.error(f"LLM Processing failed: {e}")
            # We still keep the document record, but maybe mark status as 'failed_processing'
            raise e

        return doc_id

    def _compute_hash(self, content: Union[bytes, str]) -> str:
        if isinstance(content, str):
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        return hashlib.sha256(content).hexdigest()

    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Simple pypdf extraction for demo."""
        import io
        from pypdf import PdfReader
        
        text = ""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PDF Extraction error: {e}")
            text = "Error extracting text from PDF."
        return text

    async def _is_duplicate(self, content_hash: str, source_url: Optional[str]) -> bool:
        if source_url:
            query = "SELECT 1 FROM policy_documents WHERE source_url = $1"
            async with db.acquire() as conn:
                res = await conn.fetchval(query, source_url)
                if res: return True
        
        query = "SELECT 1 FROM policy_documents WHERE content_hash = $1"
        async with db.acquire() as conn:
            res = await conn.fetchval(query, content_hash)
            return res is not None

    async def _store_document(self, title, meta, hash) -> UUID:
        query = """
            INSERT INTO policy_documents (title, regulator, doc_type, publish_date, source_url, content_hash, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING document_id
        """
        async with db.acquire() as conn:
            return await conn.fetchval(
                query, title, meta['regulator'], meta['type'], meta['date'], meta['source_url'], meta['status']
            )

    async def _determine_rule_code(self, regulator, amendment_ref, index, action_snippet):
        """
        Logic to generate rule codes.
        If LLM says it amends "RBI-MD-KYC", we reuse that.
        Else we generate "RBI-{Hash}"
        """
        if amendment_ref and "RBI-" in amendment_ref:
            # Simple heuristic: trust LLM if it looks like a code
            return amendment_ref.split()[0].strip()
        
        # Generate new code
        suffix = hashlib.md5(action_snippet.encode()).hexdigest()[:6].upper()
        return f"{regulator}-RULE-{suffix}"

    async def _find_active_rule(self, rule_code):
        query = "SELECT * FROM policy_rules WHERE rule_code = $1 AND is_active = true"
        async with db.acquire() as conn:
            return await conn.fetchrow(query, rule_code)

    async def _store_rule(self, doc_id, code, spec, ver, is_active) -> UUID:
        query = """
            INSERT INTO policy_rules (rule_code, document_id, spec, version, is_active)
            VALUES ($1, $2, $3, $4, $5) RETURNING rule_id
        """
        async with db.acquire() as conn:
            return await conn.fetchval(query, code, doc_id, spec.model_dump_json(), ver, is_active)

    async def _store_vector(self, rule_id, text, embedding):
        query = """
            INSERT INTO policy_vectors (rule_id, chunk_text, embedding)
            VALUES ($1, $2, $3)
        """
        async with db.acquire() as conn:
            await conn.execute(query, rule_id, text, embedding)

    async def _mark_superseded(self, old_rule_id, new_rule_id):
        query = """
            UPDATE policy_rules SET is_active = false, superseded_by = $2, valid_until = NOW()
            WHERE rule_id = $1
        """
        async with db.acquire() as conn:
            await conn.execute(query, old_rule_id, new_rule_id)

regulation_service = RegulationIngestionService()