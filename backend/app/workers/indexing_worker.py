from fastapi import APIRouter, Query
from app.services.agents import get_scan_logs

# API router for scan logs
router = APIRouter(prefix="/analyze", tags=["analyze"])

@router.get("/scan/{scan_id}/logs")
async def get_scan_agent_logs(scan_id: str, start: int = Query(0)):
    """
    Get agent logs for a scan (for frontend progress display).
    """
    logs = await get_scan_logs(scan_id)
    return {"logs": logs[start:]}
"""
RQ worker for background indexing and analysis jobs.
"""
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from uuid import UUID


from loguru import logger
from app.models.database import (
    CodeMapQueries,
    RegulationChunkQueries,
    RepositoryQueries,
    ScanQueries,
    ViolationQueries,
)
from app.models.job_status import JobStatus

from typing import Optional, Dict
async def update_job_status(job_id: str, status: str, repo_id: Optional[str] = None, result: Optional[Dict] = None, error: Optional[str] = None):
    """Update job status in jobs table."""
    async with db.acquire() as conn:
        await conn.execute(
            """
            UPDATE jobs SET status = $2, result = $3, error = $4,
                started_at = CASE WHEN $2 = 'running' THEN NOW() ELSE started_at END,
                completed_at = CASE WHEN $2 IN ('completed', 'failed') THEN NOW() ELSE completed_at END
            WHERE job_id = $1
            """,
            job_id, status, result, error
        )

from app.config import get_settings
from app.core.github_client import github_client
from app.database import db
from app.models.database import (
    CodeMapQueries,
    RegulationChunkQueries,
    RepositoryQueries,
    ScanQueries,
    ViolationQueries,
)
from app.services.chunker import code_chunker
from app.services.embeddings import embeddings_service
from app.services.llm import llm_service
from app.workers.job_queue import job_queue
from app.services.agents import AgentLogger 

settings = get_settings()


async def reindex_changed_files(repo_id: str, installation_id: int, full_name: str, commit_sha: str, changed_files: list):
    """
    Re-chunk, re-embed, and update only changed files in vector DB.
    """
    repo_uuid = UUID(repo_id)
    owner, repo_name = full_name.split("/")
    # Clone repo to temp dir (reuse logic from _async_index_repository)
    temp_dir = tempfile.mkdtemp(dir=settings.temp_clone_path)
    clone_path = Path(temp_dir) / repo_name
    try:
        token = await github_client.get_installation_token(installation_id)
        clone_url = f"https://x-access-token:{token}@github.com/{full_name}.git"
        branch = commit_sha if commit_sha else "HEAD"
        subprocess.run([
            "git", "clone", "--depth=1", "--single-branch", "--branch", branch, clone_url, str(clone_path)
        ], check=True, capture_output=True, timeout=300)
        # For each changed file, re-chunk and re-embed
        for rel_path in changed_files:
            file_path = clone_path / rel_path
            if not file_path.exists():
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            chunks = code_chunker.chunk_file(str(rel_path), content, repo_uuid)
            for chunk in chunks:
                text_hash = embeddings_service.compute_text_hash(chunk["chunk_text"])
                embedding = await embeddings_service.embed_text(chunk["chunk_text"])
                chunk["embedding"] = embedding
                summary = await llm_service.generate_code_summary(
                    chunk["chunk_text"], chunk["language"], chunk["file_path"])
                chunk["nl_summary"] = summary
            # Store updated chunks in DB
            async with db.acquire() as conn:
                await CodeMapQueries.insert_batch(conn, chunks)
        logger.info(f"Reindexed changed files for repo {full_name}: {changed_files}")
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


async def _async_index_repository(
    repo_id: str, installation_id: int, full_name: str, commit_sha: Optional[str], oauth_token: Optional[str] = None
) -> dict:
    """Async implementation of repository indexing."""
    repo_uuid = UUID(repo_id)
    owner, repo_name = full_name.split("/")

    logger.info(f"Starting indexing job for {full_name} (repo_id: {repo_id})")

    try:
        # Connect to database
        await db.connect()

        # Clone repository to temp directory
        temp_dir = tempfile.mkdtemp(dir=settings.temp_clone_path)
        clone_path = Path(temp_dir) / repo_name

        try:
            # Get token: either from GitHub App installation or OAuth
            if installation_id == 0 and oauth_token:
                # Use OAuth token for user repos
                token = oauth_token
                logger.info(f"Using OAuth token for {full_name}")
            else:
                # Get installation token from GitHub App
                token = await github_client.get_installation_token(installation_id)

            # Clone repo (shallow, single branch)
            clone_url = f"https://x-access-token:{token}@github.com/{full_name}.git"
            
            # Use specific commit SHA if provided, otherwise clone default branch
            if commit_sha:
                # Clone entire repo first, then checkout specific commit
                subprocess.run(
                    ["git", "clone", "--depth=50", clone_url, str(clone_path)],
                    check=True,
                    capture_output=True,
                    timeout=300,
                )
                subprocess.run(
                    ["git", "checkout", commit_sha],
                    cwd=clone_path,
                    check=True,
                    capture_output=True,
                    timeout=60,
                )
            else:
                # Clone default branch (don't specify --branch to use repo's default)
                subprocess.run(
                    ["git", "clone", "--depth=1", clone_url, str(clone_path)],
                    check=True,
                    capture_output=True,
                    timeout=300,
                )

            logger.info(f"Cloned {full_name} to {clone_path}")

            # Get commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=clone_path,
                check=True,
                capture_output=True,
                text=True,
            )
            actual_commit_sha = result.stdout.strip()

            # Process files
            all_chunks = []
            file_count = 0

            for ext in [".py", ".js", ".ts", ".java", ".go"]:
                for file_path in clone_path.rglob(f"*{ext}"):
                    if ".git" in file_path.parts or "node_modules" in file_path.parts:
                        continue

                    try:
                        # Read file
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Check file size
                        if len(content) > settings.max_file_size_mb * 1024 * 1024:
                            logger.warning(f"Skipping large file: {file_path}")
                            continue

                        # Chunk file
                        relative_path = file_path.relative_to(clone_path)
                        chunks = code_chunker.chunk_file(
                            str(relative_path), content, repo_uuid
                        )

                        all_chunks.extend(chunks)
                        file_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to process {file_path}: {e}")

            logger.info(f"Chunked {file_count} files into {len(all_chunks)} chunks")

            # Generate embeddings and NL summaries
            await job_queue.connect_async()
            # Process chunks in parallel batches for speed
            import asyncio
            
            async def process_chunk(chunk):
                """Process a single chunk: embedding + summary in parallel"""
                # Check cache for embedding
                text_hash = embeddings_service.compute_text_hash(chunk["chunk_text"])
                cached_embedding = await job_queue.get_cached_embedding(text_hash)

                # Check cache for NL summary
                cached_summary = await job_queue.get_cached_nl_summary(chunk["chunk_hash"])

                # Run embedding and summary generation in parallel if not cached
                tasks = []
                
                if not cached_embedding:
                    tasks.append(embeddings_service.embed_text(chunk["chunk_text"]))
                else:
                    tasks.append(asyncio.sleep(0))  # Dummy task
                
                if not cached_summary:
                    tasks.append(llm_service.generate_code_summary(
                        chunk["chunk_text"],
                        chunk["language"],
                        chunk["file_path"],
                    ))
                else:
                    tasks.append(asyncio.sleep(0))  # Dummy task
                
                # Execute both in parallel
                try:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Handle embedding result
                    if not cached_embedding:
                        if isinstance(results[0], Exception):
                            logger.warning(f"Embedding generation failed: {results[0]}")
                            chunk["embedding"] = None
                        else:
                            chunk["embedding"] = results[0]
                            await job_queue.cache_embedding(text_hash, results[0])
                    else:
                        chunk["embedding"] = cached_embedding
                    
                    # Handle summary result
                    if not cached_summary:
                        if isinstance(results[1], Exception):
                            logger.warning(f"NL summary generation failed: {results[1]}")
                            chunk["nl_summary"] = None
                        else:
                            chunk["nl_summary"] = results[1]
                            await job_queue.cache_nl_summary(chunk["chunk_hash"], results[1])
                    else:
                        chunk["nl_summary"] = cached_summary
                        
                except Exception as e:
                    logger.warning(f"Failed to process chunk: {e}")
                    chunk["embedding"] = cached_embedding
                    chunk["nl_summary"] = cached_summary
                
                return chunk
            
            # Process chunks in batches of 10 to avoid overwhelming APIs
            batch_size = 10
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i + batch_size]
                await asyncio.gather(*[process_chunk(chunk) for chunk in batch])
                logger.info(f"Processed {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} chunks")

            # Store chunks in database
            async with db.acquire() as conn:
                inserted = await CodeMapQueries.insert_batch(conn, all_chunks)
                await RepositoryQueries.update_sync_status(
                    conn, repo_uuid, actual_commit_sha, file_count, len(all_chunks)
                )

            logger.info(f"Inserted {inserted} chunks for {full_name}")

            return {
                "status": "success",
                "repo_id": repo_id,
                "commit_sha": actual_commit_sha,
                "files_processed": file_count,
                "chunks_created": len(all_chunks),
            }

        finally:
            # Cleanup temp directory
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"Indexing job failed for {full_name}: {e}")
        return {
            "status": "failed",
            "repo_id": repo_id,
            "error": str(e),
        }


def index_repository(
    repo_id: str, installation_id: int, full_name: str, commit_sha: Optional[str] = None, oauth_token: Optional[str] = None
) -> dict:
    """
    RQ job: Index repository code.

    Args:
        repo_id: Repository UUID (string)
        installation_id: GitHub installation ID (use 0 for OAuth)
        full_name: Repository full name (owner/repo)
        commit_sha: Specific commit SHA
        oauth_token: GitHub OAuth token (for user repos when installation_id=0)

    Returns:
        Job result dictionary
    """
    import os
    job_id = os.environ.get('RQ_JOB_ID')
    logger.info(f"[WORKER] Job received: repo_id={repo_id}, installation_id={installation_id}, full_name={full_name}, commit_sha={commit_sha}, job_id={job_id}")
    if job_id:
        asyncio.run(update_job_status(job_id, "running", repo_id=repo_id))
    try:
        logger.info(f"[WORKER] Starting indexing job for repo: {full_name} (repo_id: {repo_id})")
        result = asyncio.run(
            _async_index_repository(repo_id, installation_id, full_name, commit_sha, oauth_token)
        )
        logger.info(f"[WORKER] Finished indexing job for repo: {full_name} (repo_id: {repo_id}) | Result: {result}")
        if job_id:
            status = "completed" if result.get("status") == "success" else "failed"
            asyncio.run(update_job_status(job_id, status, repo_id=repo_id, result=result, error=result.get("error")))
        return result
    except Exception as e:
        logger.error(f"[WORKER] Error indexing repo {full_name}: {e}")
        if job_id:
            asyncio.run(update_job_status(job_id, "failed", repo_id=repo_id, error=str(e)))
        raise


async def _async_analyze_compliance(
    scan_id: str, repo_id: str, rule_ids: Optional[list[str]]
) -> dict:
    """Async implementation of compliance analysis with Agent Logging."""
    scan_uuid = UUID(scan_id)
    repo_uuid = UUID(repo_id)
    
    # Initialize Agent Logger
    agent = AgentLogger(scan_id)

    await agent.log("PLANNER", f"Starting compliance analysis for scan {scan_id}")

    try:
        await db.connect()
        await job_queue.connect_async()

        async with db.acquire() as conn:
            # Step 1: Plan
            await agent.log("PLANNER", "Identifying relevant regulations...")
            if rule_ids:
                regulation_chunks = []
                for rule_id in rule_ids:
                    chunks = await RegulationChunkQueries.get_by_rule_id(conn, rule_id)
                    regulation_chunks.extend(chunks)
                await agent.log("PLANNER", f"Scoped to {len(rule_ids)} specific rules.")
            else:
                all_rule_ids = await RegulationChunkQueries.list_all_rules(conn)
                regulation_chunks = []
                for rule_id in all_rule_ids:
                    chunks = await RegulationChunkQueries.get_by_rule_id(conn, rule_id)
                    regulation_chunks.extend(chunks)
                await agent.log("PLANNER", f"Full scan loaded {len(regulation_chunks)} regulation clauses.")

            violations = []

            # Step 2: Scout (Vector Search)
            for reg_chunk in regulation_chunks:
                rule_id = reg_chunk["rule_id"]
                
                if not reg_chunk.get("embedding"):
                    continue

                await agent.log("NAVIGATOR", f"Searching codebase for Rule {rule_id} context...")
                
                # Vector similarity search
                similar_chunks = await CodeMapQueries.search_similar(
                    conn,
                    reg_chunk["embedding"],
                    repo_uuid,
                    top_k=5
                )
                
                if not similar_chunks:
                    await agent.log("NAVIGATOR", f"No relevant code found for {rule_id}. Skipping.")
                    continue
                    
                await agent.log("NAVIGATOR", f"Found {len(similar_chunks)} potential matches for {rule_id}.")

                # Step 3: Investigate (LLM Analysis)
                for code_chunk in similar_chunks:
                    # Skip if similarity too low
                    if code_chunk.get("distance", 1.0) > (1.0 - settings.similarity_threshold):
                        continue

                    await agent.log("INVESTIGATOR", f"Analyzing {code_chunk['file_path']} against {rule_id}...")
                    
                    try:
                        analysis = await llm_service.analyze_compliance(
                            rule_text=reg_chunk["chunk_text"],
                            code_text=code_chunk["chunk_text"],
                            file_path=code_chunk["file_path"],
                            start_line=code_chunk["start_line"],
                            end_line=code_chunk["end_line"],
                            language=code_chunk["language"],
                        )

                        if analysis["verdict"] in ["non_compliant", "partial"]:
                            await agent.log("JUDGE", f"VIOLATION DETECTED: {rule_id} in {code_chunk['file_path']}")
                            violations.append(
                                {
                                    "scan_id": scan_uuid,
                                    "rule_id": reg_chunk["rule_id"],
                                    "code_chunk_id": code_chunk["chunk_id"],
                                    "regulation_chunk_id": reg_chunk["chunk_id"],
                                    "verdict": analysis["verdict"],
                                    "severity": analysis["severity"],
                                    "severity_score": analysis["severity_score"],
                                    "explanation": analysis["explanation"],
                                    "evidence": analysis.get("evidence"),
                                    "remediation": analysis.get("remediation"),
                                    "file_path": code_chunk["file_path"],
                                    "start_line": code_chunk["start_line"],
                                    "end_line": code_chunk["end_line"],
                                }
                            )
                        else:
                            # Optional: Log compliance
                            # await agent.log("JUDGE", f"Compliant: {code_chunk['file_path']}")
                            pass

                    except Exception as e:
                        logger.warning(f"Failed to analyze chunk: {e}")
                        await agent.log("INVESTIGATOR", f"Analysis error: {str(e)}")

            # Step 4: Finalize
            if violations:
                await agent.log("JUDGE", f"Committing {len(violations)} violations to database...")
                await ViolationQueries.insert_batch(conn, violations)
            else:
                await agent.log("JUDGE", "No violations found. Codebase is compliant.")

            # Update scan status
            await ScanQueries.update_violation_counts(conn, scan_uuid)
            await ScanQueries.update_status(
                conn,
                scan_uuid,
                "completed",
                {"violations_found": len(violations)},
            )

            await agent.log("PLANNER", "Scan completed successfully.")

            return {
                "status": "success",
                "scan_id": scan_id,
                "violations_found": len(violations),
            }

    except Exception as e:
        logger.error(f"Compliance analysis failed: {e}")
        await agent.log("PLANNER", f"CRITICAL ERROR: {str(e)}")

        async with db.acquire() as conn:
            await ScanQueries.update_status(conn, scan_uuid, "failed", error=str(e))

        return {
            "status": "failed",
            "scan_id": scan_id,
            "error": str(e),
        }

def analyze_compliance(
    scan_id: str, repo_id: str, rule_ids: Optional[list[str]] = None
) -> dict:
    """
    RQ job: Analyze repository compliance.

    Args:
        scan_id: Scan UUID (string)
        repo_id: Repository UUID (string)
        rule_ids: Specific rules to check

    Returns:
        Job result dictionary
    """
    import os
    job_id = os.environ.get('RQ_JOB_ID')
    if job_id:
        asyncio.run(update_job_status(job_id, "running", repo_id=repo_id))
    result = asyncio.run(_async_analyze_compliance(scan_id, repo_id, rule_ids))
    if job_id:
        status = "completed" if result.get("status") == "success" else "failed"
        asyncio.run(update_job_status(job_id, status, repo_id=repo_id, result=result, error=result.get("error")))
    return result


# Worker entry point
if __name__ == "__main__":
    import sys
    from rq import Worker
    from rq.worker import SimpleWorker

    logger.info("[WORKER] Indexing worker started and listening for jobs.")

    # Use SimpleWorker on Windows (no fork support)
    worker_class = SimpleWorker if sys.platform == "win32" else Worker
    
    worker = worker_class(
        queues=[settings.queue_name],  # Use queue name string, e.g., 'compliance:jobs'
        connection=job_queue.sync_redis,
        log_job_description=True,
    )

    worker.work(with_scheduler=True)
