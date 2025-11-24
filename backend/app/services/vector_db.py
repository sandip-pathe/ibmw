# Stub for vector_db to resolve import errors


from app.models.database import CodeMapQueries

async def search_similar_chunks(conn, embedding, repo_id=None, top_k=10):
    """Search similar code map chunks using vector similarity."""
    return await CodeMapQueries.search_similar(conn, embedding, repo_id, top_k)

async def upsert_embeddings(conn, embeddings, repo_id):
    """Upsert code map embeddings."""
    # embeddings: list of dicts with all code_map fields
    return await CodeMapQueries.insert_batch(conn, embeddings)
