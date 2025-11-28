"""
Regulation Sync Service
Handles syncing regulations from various sources (PDF, JSON, API)
"""
import hashlib
import json
from typing import Dict, Any, Optional, List
from loguru import logger

from app.services.regulation_processor import regulation_processor
from app.services.embeddings import embeddings_service
from app.database import db


class RegulationSyncService:
    """
    Service for syncing and updating regulations
    
    Supports:
    - JSON pre-chunked data
    - PDF documents (via Azure Document Intelligence)
    - API endpoints
    """
    
    async def sync_regulation(
        self,
        regulator: str,
        document_type: str,
        document_url: Optional[str] = None,
        document_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sync regulation from source
        
        Args:
            regulator: Regulator identifier (RBI, SEBI, etc.)
            document_type: Document type identifier
            document_url: Optional URL to fetch document
            document_data: Optional pre-processed document data
            
        Returns:
            Sync result with chunk count
        """
        rule_id = f"{regulator}_{document_type}"
        logger.info(f"Syncing regulation: {rule_id}")
        
        try:
            # Process document
            if document_data:
                chunks = await self._process_json_data(rule_id, document_data, regulator)
            elif document_url:
                chunks = await self._process_from_url(rule_id, document_url, regulator)
            else:
                raise ValueError("Either document_data or document_url must be provided")
            
            # Generate embeddings
            chunks_with_embeddings = await self._generate_embeddings(chunks)
            
            # Store in database
            chunks_stored = await self._store_chunks(chunks_with_embeddings)
            
            logger.info(f"Synced {chunks_stored} chunks for {rule_id}")
            
            return {
                "rule_id": rule_id,
                "chunks_processed": chunks_stored,
                "regulator": regulator,
                "document_type": document_type
            }
            
        except Exception as e:
            logger.error(f"Failed to sync regulation {rule_id}: {e}")
            raise
    
    async def _process_json_data(
        self,
        rule_id: str,
        data: Dict[str, Any],
        regulator: str
    ) -> List[Dict[str, Any]]:
        """Process pre-chunked JSON data"""
        chunks_list = data.get("chunks", [])
        
        processed = regulation_processor.process_json_chunks(
            chunks_data=chunks_list,
            rule_id=rule_id,
            source_document=f"{regulator} regulations"
        )
        
        return processed
    
    async def _process_from_url(
        self,
        rule_id: str,
        url: str,
        regulator: str
    ) -> List[Dict[str, Any]]:
        """Fetch and process document from URL"""
        # TODO: Implement URL fetching and processing
        # For now, raise not implemented
        raise NotImplementedError("URL-based regulation sync not yet implemented")
    
    async def _generate_embeddings(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for chunks"""
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        for chunk in chunks:
            text = chunk.get("chunk_text", "")
            if text:
                embedding = await embeddings_service.embed_text(text)
                chunk["embedding"] = embedding
        
        return chunks
    
    async def _store_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Store chunks in database"""
        if not chunks:
            return 0
        
        async with db.acquire() as conn:
            for chunk in chunks:
                embedding = chunk.get("embedding")
                embedding_str = None
                if embedding:
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                
                await conn.execute("""
                    INSERT INTO regulation_chunks (
                        rule_id, rule_section, source_document, chunk_text,
                        chunk_index, chunk_hash, embedding, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7::vector, $8::jsonb)
                    ON CONFLICT (chunk_hash) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        updated_at = NOW()
                """,
                    chunk["rule_id"],
                    chunk.get("rule_section"),
                    chunk.get("source_document"),
                    chunk["chunk_text"],
                    chunk["chunk_index"],
                    chunk["chunk_hash"],
                    embedding_str,
                    json.dumps(chunk.get("metadata", {}))
                )
        
        return len(chunks)


# Global service instance
sync_regulation_service = RegulationSyncService()
