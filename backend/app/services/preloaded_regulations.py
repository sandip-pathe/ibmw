"""
Preloaded Regulation Service for Hackathon Demo.

⚠️ DEMO MODE ACTIVE
This service manages a single hardcoded RBI Payment Aggregator regulation PDF.
Upload functionality is disabled - all regulations are preloaded.

File: Master Direction on Regulation of Payment Aggregator (PA).pdf
Location: C:\\Users\\sandi\\Downloads
"""

from pathlib import Path
from typing import Optional, Dict, List
from uuid import uuid4
import hashlib
import json
from loguru import logger

from app.services.pdf_processor import PDFProcessor
from app.services.embeddings import embeddings_service
from app.database import db


class PreloadedRegulationService:
    """
    Manages the preloaded Payment Aggregator regulation for demo.
    
    Responsibilities:
    - Check if regulation is already loaded
    - Process PDF if not loaded
    - Generate embeddings for regulation chunks
    - Store in database with proper schema
    """
    
    # ==========================================
    # DEMO CONFIGURATION
    # ==========================================
    DEMO_REGULATION = {
        "rule_id": "RBI-PA-MD-2020",
        "title": "Master Direction on Regulation of Payment Aggregator",
        "category": "payment_aggregator",
        "regulatory_body": "RBI",
        "effective_date": "2020-03-17",
        "compliance_tag": "RBI-Payment-Aggregator",
        "file_path": Path(r"C:\Users\sandi\Downloads\Master Direction on Regulation of Payment Aggregator (PA).pdf")
    }
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
    
    async def ensure_regulation_loaded(self) -> Dict:
        """
        Idempotent operation to ensure demo regulation is in database.
        
        Workflow:
        1. Check if regulation exists (by rule_id)
        2. If yes, return metadata
        3. If no, process PDF and store
        
        Returns:
            dict: Regulation metadata with load status
        """
        rule_id = self.DEMO_REGULATION["rule_id"]
        
        # Step 1: Check if already loaded
        async with db.acquire() as conn:
            existing = await conn.fetchrow("""
                SELECT rule_code, spec, 
                       (SELECT COUNT(*) FROM regulation_chunks WHERE rule_id = $1) as chunk_count
                FROM policy_rules 
                WHERE rule_code = $1
                LIMIT 1
            """, rule_id)
            
            if existing and existing['chunk_count'] > 0:
                spec = existing['spec']
                title = spec.get('title', self.DEMO_REGULATION['title']) if isinstance(spec, dict) else self.DEMO_REGULATION['title']
                logger.info(
                    f"✅ Regulation {rule_id} already loaded with "
                    f"{existing['chunk_count']} chunks"
                )
                return {
                    "rule_id": existing["rule_code"],
                    "title": title,
                    "chunk_count": existing["chunk_count"],
                    "status": "already_loaded"
                }
        
        # Step 2: Not loaded - process the PDF
        logger.info(f"📄 Processing regulation PDF: {self.DEMO_REGULATION['file_path']}")
        
        file_path = self.DEMO_REGULATION["file_path"]
        
        if not file_path.exists():
            error_msg = (
                f"Demo regulation PDF not found at: {file_path}\n"
                f"Please ensure the file exists at the specified location."
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Step 3: Process and store
        result = await self._process_and_store_regulation(file_path)
        
        logger.info(
            f"✅ Successfully loaded regulation {rule_id} with "
            f"{result['chunk_count']} chunks"
        )
        
        return {
            **result,
            "status": "newly_loaded"
        }
    
    async def _process_and_store_regulation(self, file_path: Path) -> Dict:
        """
        Process PDF and store all chunks in database.
        
        Steps:
        1. Extract text from PDF
        2. Structure into sections
        3. Chunk sections
        4. Generate embeddings
        5. Store in regulation_chunks table
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            dict: Processing result with chunk count
        """
        # Step 1: Extract text
        raw_text = self.pdf_processor.extract_text(file_path)
        
        # Step 2: Structure sections
        sections = self.pdf_processor.structure_sections(raw_text)
        
        # Step 3: Chunk sections
        chunks = self.pdf_processor.chunk_sections(sections, max_chunk_size=1000)
        
        logger.info(f"Created {len(chunks)} chunks from PDF")
        
        # Step 4 & 5: Generate embeddings and store
        async with db.acquire() as conn:
            # Insert regulation metadata into policy_rules table
            rule_uuid = uuid4()
            
            await conn.execute("""
                INSERT INTO policy_rules (
                    rule_id, rule_code, spec, category, 
                    severity, is_active, version
                )
                VALUES ($1, $2, $3::jsonb, $4::text[], $5, $6, $7)
                ON CONFLICT (rule_code, version) DO UPDATE SET
                    spec = EXCLUDED.spec
            """,
                rule_uuid,
                self.DEMO_REGULATION["rule_id"],
                json.dumps({
                    "title": self.DEMO_REGULATION["title"],
                    "regulatory_body": self.DEMO_REGULATION["regulatory_body"],
                    "effective_date": self.DEMO_REGULATION["effective_date"],
                    "file_path": str(file_path)
                }),
                [self.DEMO_REGULATION["category"]],  # Array format
                "high",
                True,
                1
            )
            
            # Process chunks in batches for efficiency
            inserted_count = 0
            
            for idx, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = await embeddings_service.embed_text(chunk["text"])
                    
                    # Format embedding for PostgreSQL vector type
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                    
                    # Create unique chunk hash
                    chunk_hash = hashlib.sha256(
                        f"{self.DEMO_REGULATION['rule_id']}-{idx}-{chunk['text'][:100]}".encode()
                    ).hexdigest()[:16]
                    
                    # Insert chunk into regulation_chunks table
                    await conn.execute("""
                        INSERT INTO regulation_chunks (
                            chunk_id,
                            rule_id,
                            chunk_text,
                            chunk_hash,
                            chunk_index,
                            embedding,
                            rule_section,
                            metadata
                        )
                        VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8::jsonb)
                    """,
                        uuid4(),
                        self.DEMO_REGULATION["rule_id"],
                        chunk["text"],
                        chunk_hash,
                        idx,
                        embedding_str,
                        f"{chunk['section_number']} {chunk['section_title']}",
                        json.dumps({
                            "section_number": chunk["section_number"],
                            "section_title": chunk["section_title"],
                            "chunk_index": chunk["chunk_index"],
                            "compliance_tag": self.DEMO_REGULATION["compliance_tag"]
                        })
                    )
                    
                    inserted_count += 1
                    
                    if (inserted_count % 10 == 0):
                        logger.info(f"Processed {inserted_count}/{len(chunks)} chunks")
                
                except Exception as e:
                    logger.warning(f"Failed to process chunk {idx}: {e}")
                    continue
        
        logger.info(f"✅ Stored {inserted_count} regulation chunks in database")
        
        return {
            "rule_id": self.DEMO_REGULATION["rule_id"],
            "title": self.DEMO_REGULATION["title"],
            "chunk_count": inserted_count
        }
    
    async def get_regulation_metadata(self) -> Optional[Dict]:
        """
        Get metadata for the demo regulation.
        
        Returns:
            dict or None: Regulation metadata if loaded
        """
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT rule_code, spec, category, severity,
                       (SELECT COUNT(*) FROM regulation_chunks WHERE rule_id = $1) as chunk_count
                FROM policy_rules
                WHERE rule_code = $1
            """, self.DEMO_REGULATION["rule_id"])
            
            if not row:
                return None
            
            spec = row['spec'] if isinstance(row['spec'], dict) else json.loads(row['spec'])
            
            return {
                "rule_id": row["rule_code"],
                "title": spec.get("title", self.DEMO_REGULATION["title"]),
                "category": row["category"],
                "severity": row["severity"],
                "chunk_count": row["chunk_count"],
                "regulatory_body": spec.get("regulatory_body", "RBI")
            }
    
    async def get_regulation_chunks(
        self, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get regulation chunks from database.
        
        Args:
            limit: Maximum chunks to return
            offset: Number of chunks to skip
            
        Returns:
            list: Regulation chunks
        """
        async with db.acquire() as conn:
            query = """
                SELECT chunk_id, chunk_text, rule_section, 
                       chunk_index, metadata
                FROM regulation_chunks
                WHERE rule_id = $1
                ORDER BY chunk_index
            """
            
            params = [self.DEMO_REGULATION["rule_id"]]
            
            if limit:
                query += f" LIMIT ${len(params) + 1}"
                params.append(limit)
            
            if offset:
                query += f" OFFSET ${len(params) + 1}"
                params.append(offset)
            
            rows = await conn.fetch(query, *params)
            
            return [dict(row) for row in rows]


# Global instance
preloaded_regulation_service = PreloadedRegulationService()
