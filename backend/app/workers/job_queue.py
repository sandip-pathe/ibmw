"""
Job queue management using Redis and RQ.
"""
import json
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as aioredis
from loguru import logger
from redis import Redis
from rq import Queue

from app.config import get_settings

settings = get_settings()


class JobQueue:
    """Redis-based job queue manager."""

    # (Duplicate __init__ and related methods removed)

    async def get_cached_embedding(self, text_hash: str) -> Optional[Any]:
        """Get cached embedding from Redis."""
        if self.async_redis is None:
            await self.connect_async()
        key = f"embedding:{text_hash}"
        if self.async_redis is None:
            raise RuntimeError("Redis client not initialized")
        value = await self.async_redis.get(key)
        if value is not None:
            try:
                return json.loads(value)
            except Exception:
                return value
        return None

    async def cache_embedding(self, text_hash: str, embedding: Any) -> None:
        """Cache embedding in Redis."""
        if self.async_redis is None:
            await self.connect_async()
        key = f"embedding:{text_hash}"
        if self.async_redis is None:
            raise RuntimeError("Redis client not initialized")
        await self.async_redis.set(key, json.dumps(embedding), ex=604800)

    async def get_cached_nl_summary(self, chunk_hash: str) -> Optional[str]:
        """Get cached NL summary from Redis."""
        if self.async_redis is None:
            await self.connect_async()
        key = f"nl_summary:{chunk_hash}"
        if self.async_redis is None:
            raise RuntimeError("Redis client not initialized")
        value = await self.async_redis.get(key)
        if value is not None:
            return value
        return None

    async def cache_nl_summary(self, chunk_hash: str, summary: str) -> None:
        """Cache NL summary in Redis."""
        if self.async_redis is None:
            await self.connect_async()
        key = f"nl_summary:{chunk_hash}"
        if self.async_redis is None:
            raise RuntimeError("Redis client not initialized")
        await self.async_redis.set(key, summary, ex=604800)

    def __init__(self):
        self.redis_url = settings.redis_url
        self.queue_name = settings.queue_name
        
        # Sync Redis for RQ
        self.sync_redis = Redis.from_url(self.redis_url, decode_responses=False)
        self.queue = Queue(name=self.queue_name, connection=self.sync_redis)
        
        # Async Redis for caching
        self.async_redis: Optional[aioredis.Redis] = None
        
        logger.info(f"Initialized job queue: {self.queue_name}")

    async def connect_async(self) -> None:
        """Connect async Redis client."""
        if self.async_redis is None:
            import redis.asyncio
            self.async_redis = redis.asyncio.Redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Connected async Redis client")

    async def disconnect_async(self) -> None:
        """Disconnect async Redis client."""
        if self.async_redis:
            await self.async_redis.close()
            self.async_redis = None
            logger.info("Disconnected async Redis client")

    def enqueue_indexing_job(
        self,
        repo_id: UUID,
        installation_id: int,
        full_name: str,
        commit_sha: Optional[str] = None,
        oauth_token: Optional[str] = None,
    ) -> str:
        """
        Enqueue repository indexing job.
        Args:
            repo_id: Repository UUID
            installation_id: GitHub installation ID
            full_name: Repository full name (owner/repo)
            commit_sha: Specific commit SHA
            oauth_token: GitHub OAuth token (for user repos when installation_id=0)
        Returns:
            Job ID
        """
        from app.workers.indexing_worker import index_repository

        job = self.queue.enqueue(
            index_repository,
            repo_id=str(repo_id),
            installation_id=installation_id,
            full_name=full_name,
            commit_sha=commit_sha,
            oauth_token=oauth_token,
            job_timeout=settings.job_timeout,
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=604800,  # Keep failures for 7 days
        )

        logger.info(f"Enqueued indexing job {job.id} for {full_name}")
        return job.id

    def enqueue_analysis_job(
        self,
        scan_id: UUID,
        repo_id: UUID,
        rule_ids: Optional[list[str]] = None,
    ) -> str:
        """
        Enqueue compliance analysis job.
        Args:
            scan_id: Scan UUID
            repo_id: Repository UUID
            rule_ids: Specific rules to check (None = all rules)
        Returns:
            Job ID
        """
        from app.workers.indexing_worker import analyze_compliance

        job = self.queue.enqueue(
            analyze_compliance,
            scan_id=str(scan_id),
            repo_id=str(repo_id),
            rule_ids=rule_ids,
            job_timeout=settings.job_timeout,
            result_ttl=86400,
        )

        logger.info(f"Enqueued analysis job {job.id} for scan {scan_id}")
        return job.id

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get job status from RQ."""
        from rq.job import Job
        job = Job.fetch(job_id, connection=self.sync_redis)
        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "exc_info": job.exc_info,
        }

job_queue = JobQueue()
