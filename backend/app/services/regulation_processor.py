from .llm import macro_compliance_prompt
async def analyze_flow(rule, chunks, llm, required_keywords=None, required_sequence=None):
    """
    Macro compliance analyzer: multi-chunk context reasoning.
    - Summarize top relevant chunks
    - Combine summaries
    - Reason about order, missing steps, flow
    """
    # Step 1: Get top 3-5 relevant chunks (assume chunks are pre-filtered)
    summaries = []
    for chunk in chunks:
        summary = await llm.summarize_code_chunk(chunk)
        summaries.append(summary)
    context_block = "\n---\n".join(summaries)
    # Step 2: Missing-step detection
    missing_steps = []
    explanation = ""
    if required_keywords:
        found = any(any(kw.lower() in s.lower() for kw in required_keywords) for s in summaries)
        if not found:
            missing_steps.append(f"Missing required keyword(s): {required_keywords}")
    if required_sequence:
        seq_found = False
        seq_str = " ".join(required_sequence)
        if seq_str.lower() in context_block.lower():
            seq_found = True
        if not seq_found:
            missing_steps.append(f"Missing required sequence: {required_sequence}")
    # Step 3: Macro compliance LLM prompt
    prompt = macro_compliance_prompt(rule.text, context_block)
    verdict = await llm.complete(prompt)
    if missing_steps:
        explanation = f"Violation: {', '.join(missing_steps)}"
    return {
        "verdict": verdict,
        "missing_steps": missing_steps,
        "summaries": summaries,
        "explanation": explanation,
    }
from app.models.rule_model import normalize_rule_text, Rule
def store_normalized_rule(rule_text: str, db):
    """Normalizes and stores rule in DB."""
    rule = normalize_rule_text(rule_text)
    db.execute(
        """INSERT INTO rules (condition, actor, object, action, outcome, raw_text, keywords)
        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (rule.condition, rule.actor, rule.object, rule.action, rule.outcome, rule.raw_text, ','.join(rule.keywords))
    )
    return rule
import numpy as np
from .vector_db import search_similar_chunks
from .code_parser import detect_function_calls
async def multi_hop_reason(rule, chunks, llm, top_k=5):
    """
    Multi-hop reasoning pipeline:
    1. Select top-K chunks via embeddings.
    2. Expand neighborhood via call graph or filename similarity.
    3. Perform second LLM reasoning pass.
    """
    # Step 1: Embedding similarity
    rule_embedding = await llm.embed(rule.text)
    top_chunks = await search_similar_chunks(rule_embedding, top_k)
    # Step 2: Neighborhood expansion
    expanded_chunks = set(top_chunks)
    for chunk in top_chunks:
        calls = detect_function_calls(chunk.code)
        for func_calls in calls.values():
            for call in func_calls:
                for c in chunks:
                    if call in c.code and c not in expanded_chunks:
                        expanded_chunks.add(c)
        # Filename similarity
        for c in chunks:
            if c.file_path == chunk.file_path and c not in expanded_chunks:
                expanded_chunks.add(c)
    # Step 3: Second LLM pass
    results = []
    for chunk in expanded_chunks:
        prompt = f"Does this code comply with the rule: '{rule.text}'?\nCode:\n{chunk.code}"
        result = await llm.complete(prompt)
        results.append((chunk.file_path, result))
    return results
from .code_parser import (
    extract_constants_from_code,
    extract_config_from_file,
    detect_function_calls,
    find_hardcoded_thresholds,
    detect_overrides_across_files,
    detect_missing_error_handling,
)
def merge_static_and_semantic_facts(chunk, embedding_facts):
    """Merges static facts (constants, configs) with semantic embedding-based facts."""
    static_facts = extract_constants_from_code(chunk.code)
    config_facts = {}
    if chunk.file_path.endswith(('.json', '.yaml', '.yml', '.env')):
        config_facts = extract_config_from_file(chunk.file_path)
    merged = {**static_facts, **config_facts, **embedding_facts}
    return merged
def audit_chunk_for_compliance(chunk, rules):
    """Utility to check for hardcoded thresholds, overrides, and missing error handling."""
    constants = extract_constants_from_code(chunk.code)
    thresholds = find_hardcoded_thresholds(constants)
    missing_error_handling = detect_missing_error_handling(chunk.code)
    return {
        "thresholds": thresholds,
        "missing_error_handling": missing_error_handling,
    }
"""
Regulation document processing service (stubbed for hackathon demo).
Full Azure Document Intelligence integration can be enabled via feature flag.
"""
from typing import Any, Optional

from loguru import logger

from app.config import get_settings
from app.core.exceptions import StorageError

settings = get_settings()


class RegulationProcessor:
    """Process regulation PDFs into structured chunks."""

    def __init__(self):
        self.doc_intelligence_enabled = settings.enable_doc_intelligence

        if self.doc_intelligence_enabled:
            # In production, initialize Azure Document Intelligence client
            # from azure.ai.formrecognizer.aio import DocumentAnalysisClient
            # from azure.core.credentials import AzureKeyCredential
            #
            # self.client = DocumentAnalysisClient(
            #     endpoint=settings.azure_document_intelligence_endpoint,
            #     credential=AzureKeyCredential(settings.azure_document_intelligence_key)
            # )
            logger.info("Azure Document Intelligence enabled (not fully implemented in demo)")
        else:
            logger.info("Regulation processing: using pre-chunked JSON (demo mode)")

    async def process_pdf(
        self, pdf_bytes: bytes, rule_id: str, source_document: str
    ) -> list[dict[str, Any]]:
        """
        Process PDF and extract regulation chunks.

        Args:
            pdf_bytes: PDF file bytes
            rule_id: Rule identifier
            source_document: Source document name

        Returns:
            List of regulation chunks
            
        Raises:
            NotImplementedError: If Azure DI not configured
            ValueError: If PDF is invalid
        """
        if not pdf_bytes:
            raise ValueError("PDF bytes cannot be empty")
        
        if self.doc_intelligence_enabled:
            return await self._process_with_doc_intelligence(
                pdf_bytes, rule_id, source_document
            )
        else:
            # Demo: return placeholder structure
            logger.warning("PDF processing stubbed - use pre-chunked JSON for demo")
            return []

    async def _process_with_doc_intelligence(
        self, pdf_bytes: bytes, rule_id: str, source_document: str
    ) -> list[dict[str, Any]]:
        """Process PDF using Azure Document Intelligence (production implementation)."""
        # TODO: Implement full Azure Document Intelligence integration
        #
        # poller = await self.client.begin_analyze_document(
        #     "prebuilt-layout", document=pdf_bytes
        # )
        # result = await poller.result()
        #
        # chunks = []
        # for page in result.pages:
        #     for section in self._extract_sections(page):
        #         chunks.append({
        #             "rule_id": rule_id,
        #             "rule_section": section["heading"],
        #             "source_document": source_document,
        #             "chunk_text": section["text"],
        #             "chunk_index": len(chunks),
        #             "metadata": {"page": page.page_number}
        #         })
        #
        # return chunks

        raise NotImplementedError("Azure Document Intelligence integration not yet implemented")

    def process_json_chunks(
        self, chunks_data: list[dict[str, Any]], rule_id: str, source_document: str
    ) -> list[dict[str, Any]]:
        """
        Process pre-chunked regulation JSON (for demo/testing).

        Args:
            chunks_data: Pre-chunked regulation data
            rule_id: Rule identifier
            source_document: Source document name

        Returns:
            Processed regulation chunks
            
        Raises:
            ValueError: If chunks_data is invalid
        """
        if not chunks_data:
            raise ValueError("chunks_data cannot be empty")
        
        if not isinstance(chunks_data, list):
            raise ValueError("chunks_data must be a list")
        
        import hashlib

        processed_chunks = []

        try:
            for i, chunk in enumerate(chunks_data):
                chunk_text = chunk.get("text", chunk.get("chunk_text", ""))
                
                if not chunk_text:
                    logger.warning(f"Skipping empty chunk at index {i}")
                    continue
                
                chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

                processed_chunks.append(
                    {
                        "rule_id": rule_id,
                        "rule_section": chunk.get("section", chunk.get("rule_section")),
                        "source_document": source_document,
                        "chunk_text": chunk_text,
                        "chunk_index": i,
                        "chunk_hash": chunk_hash,
                        "metadata": chunk.get("metadata", {}),
                    }
                )

            logger.info(f"Processed {len(processed_chunks)} regulation chunks for {rule_id}")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Failed to process JSON chunks: {e}")
            raise ValueError(f"Invalid chunk data: {str(e)}") from e


# Global processor instance
regulation_processor = RegulationProcessor()
