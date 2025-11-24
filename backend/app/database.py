"""
Database connection and session management using asyncpg.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from asyncpg import Pool, create_pool
from loguru import logger

from app.config import get_settings

settings = get_settings()


class Database:
    """Database connection manager."""

    def __init__(self):
        self.pool: Pool | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Create database connection pool to Neon."""
        async with self._lock:
            if self.pool is not None:
                logger.warning("Database pool already exists")
                return

            try:
                db_url = settings.database_url
                self.pool = await create_pool(
                    db_url,
                    min_size=5,
                    max_size=20,
                    command_timeout=60,
                    server_settings={
                        "application_name": settings.app_name,
                    },
                )
                logger.info("Neon database connection pool created")

                # Verify pgvector extension in Neon
                async with self.pool.acquire() as conn:
                    result = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                    )
                    if not result:
                        logger.warning("pgvector extension not found in Neon - vector operations will fail")
                    else:
                        logger.info("pgvector extension verified in Neon")

            except Exception as e:
                logger.error(f"Failed to create Neon database pool: {e}")
                raise

    async def disconnect(self) -> None:
        """Close database connection pool."""
        async with self._lock:
            if self.pool is not None:
                await self.pool.close()
                self.pool = None
                logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator:
        """Acquire a connection from the pool."""
        if self.pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args) -> str:
        """Execute a query and return status."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """Fetch multiple rows."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch a single row."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch a single value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)


# Global database instance
db = Database()


async def get_db() -> Database:
    """Dependency for FastAPI endpoints."""
    return db
