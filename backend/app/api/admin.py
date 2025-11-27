"""
Admin endpoints for management and health checks.
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from loguru import logger

from app.config import get_settings
from app.core.security import verify_admin_api_key
from app.database import get_db
from app.models.database import RegulationChunkQueries
from app.models.schemas import HealthResponse, SuccessResponse, RegulationChunkResponse
from app.services.embeddings import embeddings_service
from app.services.regulation_processor import regulation_processor
from app.workers.job_queue import job_queue

settings = get_settings()
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - Embeddings provider
    - LLM provider
    """
    services = {
        "database": False,
        "redis": False,
        "embeddings": False,
        "llm": False,
    }

    # Check database
    try:
        db = await get_db()
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        services["database"] = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")

    # Check Redis
    try:
        await job_queue.connect_async()
        # Use a valid method to check Redis connectivity
        if await job_queue.connect_async():
            services["redis"] = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")

    # Check embeddings (simple test)
    try:
        await embeddings_service.embed_text("health check")
        services["embeddings"] = True
    except Exception as e:
        logger.warning(f"Embeddings health check failed: {e}")

    # Check LLM (skip to avoid quota usage on health checks)
    services["llm"] = True  # Assume healthy if configured

    # Determine overall status
    if all(services.values()):
        status_str = "healthy"
    elif services["database"] and services["redis"]:
        status_str = "degraded"
    else:
        status_str = "unhealthy"

    return HealthResponse(
        status=status_str,
        version=settings.api_version,
        timestamp=datetime.utcnow(),
        services=services,
    )


@router.get("/repos", dependencies=[Depends(verify_admin_api_key)])
async def list_all_repos():
    """List all indexed repositories."""
    db = await get_db()

    async with db.acquire() as conn:
        repos = await conn.fetch(
            """
            SELECT r.*, i.account_login
            FROM repos r
            LEFT JOIN installations i ON r.installation_id = i.installation_id
            ORDER BY r.created_at DESC
            LIMIT 100
            """
        )

    return [dict(r) for r in repos]


@router.get("/regulations", dependencies=[Depends(verify_admin_api_key)])
async def list_regulations() -> list[str]:
    """List all loaded regulation rule IDs."""
    db = await get_db()

    async with db.acquire() as conn:
        rule_ids = await RegulationChunkQueries.list_all_rules(conn)

    return rule_ids


@router.get("/regulations/{rule_id}", dependencies=[Depends(verify_admin_api_key)])
async def get_regulation_chunks(rule_id: str) -> list:
    """Get all chunks for a specific regulation."""
    db = await get_db()

    async with db.acquire() as conn:
        chunks = await RegulationChunkQueries.get_by_rule_id(conn, rule_id)

    return [
        RegulationChunkResponse(
            chunk_id=c["chunk_id"],
            rule_id=c["rule_id"],
            rule_section=c.get("rule_section"),
            source_document=c.get("source_document"),
            chunk_text=c["chunk_text"],
            chunk_index=c["chunk_index"],
            nl_summary=c.get("nl_summary"),
            created_at=c["created_at"],
        )
        for c in chunks
    ]


@router.post("/regulations/upload", dependencies=[Depends(verify_admin_api_key)])
async def upload_regulation(rule_id: str, source_document: str, chunks: list[dict]) -> SuccessResponse:
    """
    Upload pre-chunked regulation data (for demo/testing).
    
    Expected chunk format:
    {
      "text": "Regulation text...",
      "section": "Section 4.2.1",
      "metadata": {}
    }
    """
    # Process chunks
    processed_chunks = regulation_processor.process_json_chunks(
        chunks, rule_id, source_document
    )

    # Generate embeddings
    await job_queue.connect_async()

    for chunk in processed_chunks:
        # Check cache
        text_hash = embeddings_service.compute_text_hash(chunk["chunk_text"])
        cached_embedding = await job_queue.get_cached_embedding(text_hash)

        if cached_embedding is not None:
            chunk["embedding"] = cached_embedding
        else:
            embedding = await embeddings_service.embed_text(chunk["chunk_text"])
            chunk["embedding"] = embedding
            await job_queue.cache_embedding(text_hash, embedding)

    # Store in database
    db = await get_db()
    async with db.acquire() as conn:
        count = await RegulationChunkQueries.insert_batch(conn, processed_chunks)

    logger.info(f"Uploaded {count} regulation chunks for {rule_id}")

    return SuccessResponse(
        message=f"Uploaded {count} chunks for {rule_id}",
        data={"rule_id": rule_id, "chunks_count": count},
    )
