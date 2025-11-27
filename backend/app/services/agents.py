"""
Service for logging agent 'thoughts' and actions to Redis for frontend streaming.
"""
import json
import time
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from loguru import logger

from app.workers.job_queue import job_queue

AgentType = Literal["PLANNER", "NAVIGATOR", "INVESTIGATOR", "JUDGE", "JIRA"]

class AgentLogger:
    """
    Streams agent logs to a Redis list for real-time UI updates.
    Keys are expirable to prevent memory leaks.
    """
    
    def __init__(self, scan_id: str | UUID, ttl_seconds: int = 3600):
        self.scan_id = str(scan_id)
        self.ttl = ttl_seconds
        self.redis_key = f"scan:{self.scan_id}:logs"

    async def log(self, agent: AgentType, message: str):
        """
        Push a log entry to the scan's Redis list.
        """
        entry = {
            "agent": agent,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "ts_epoch": time.time()
        }
        
        try:
            if job_queue.async_redis is None:
                await job_queue.connect_async()
            redis = job_queue.async_redis
            import redis.asyncio
            if not isinstance(redis, redis.asyncio.Redis):
                raise RuntimeError("Async Redis client is not an instance of redis.asyncio.Redis")

            # Push to right end of list (append)
            await redis.rpush(self.redis_key, json.dumps(entry))

            # Set expiration on first log if key doesn't have one
            ttl = await redis.ttl(self.redis_key)
            if isinstance(ttl, int) and ttl == -1:
                await redis.expire(self.redis_key, self.ttl)

            logger.debug(f"[{agent}] {message}")

        except Exception as e:
            logger.error(f"Failed to stream agent log: {e}")

    async def get_logs(self, start_index: int = 0) -> list[dict]:
        """
        Retrieve logs from Redis.
        """
        try:
            if job_queue.async_redis is None:
                await job_queue.connect_async()
            redis = job_queue.async_redis
            import redis.asyncio
            if not isinstance(redis, redis.asyncio.Redis):
                raise RuntimeError("Async Redis client is not an instance of redis.asyncio.Redis")

            raw_logs = await redis.lrange(self.redis_key, start_index, -1)
            return [json.loads(log) for log in raw_logs]
        except Exception as e:
            logger.error(f"Failed to fetch logs: {e}")
            return []

# Helper to get logs statically if needed
async def get_scan_logs(scan_id: str) -> list[dict]:
    agent = AgentLogger(scan_id)
    return await agent.get_logs()