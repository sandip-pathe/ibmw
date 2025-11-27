"""
Tools available to the Agentic System.
"""
from typing import List, Optional
from uuid import UUID
from langchain_core.tools import tool
from loguru import logger

from app.database import db
from app.models.database import CodeMapQueries
from app.services.embeddings import embeddings_service
# from app.services.storage import storage_service # Optional: if using blob storage

@tool
async def search_codebase(query: str, repo_id: str) -> str:
    """
    Search the codebase for snippets relevant to the query using semantic vector search.
    Use this to find relevant files or code blocks.
    """
    try:
        repo_uuid = UUID(repo_id)
        embedding = await embeddings_service.embed_text(query)
        
        # Ensure DB connection
        if not db.pool:
            await db.connect()
            
        async with db.acquire() as conn:
            chunks = await CodeMapQueries.search_similar(
                conn, embedding, repo_uuid, top_k=5
            )
            
        if not chunks:
            return "No relevant code chunks found."
            
        results = []
        for chunk in chunks:
            results.append(
                f"File: {chunk['file_path']}\n"
                f"Lines: {chunk['start_line']}-{chunk['end_line']}\n"
                f"Content:\n{chunk['chunk_text']}\n"
                f"---"
            )
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"Tool search_codebase error: {e}")
        return f"Error searching codebase: {str(e)}"

@tool
async def read_file_content(file_path: str, repo_id: str) -> str:
    """
    Read the full content of a specific file. 
    Use this when you need more context than the search results provide.
    """
    try:
        repo_uuid = UUID(repo_id)
        if not db.pool:
            await db.connect()
            
        # Fallback: fetch all chunks for this file from DB to reconstruct if blob storage isn't active
        async with db.acquire() as conn:
            # This assumes we store chunks. In a real app, use storage_service.download_file
            query = """
                SELECT chunk_text, start_line FROM code_map 
                WHERE repo_id = $1 AND file_path = $2
                ORDER BY start_line ASC
            """
            rows = await conn.fetch(query, repo_uuid, file_path)
            
        if not rows:
            return f"File {file_path} not found or empty."
            
        content = "\n".join([r['chunk_text'] for r in rows])
        return content
        
    except Exception as e:
        return f"Error reading file: {str(e)}"

COMPLIANCE_TOOLS = [search_codebase, read_file_content]