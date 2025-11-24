"""
Security utilities: API key validation, rate limiting.
"""
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Header, status
from loguru import logger

from app.config import get_settings

settings = get_settings()


async def verify_admin_api_key(x_api_key: str = Header(...)) -> None:
    """
    Verify admin API key from X-API-Key header.
    
    Args:
        x_api_key: API key from header
        
    Raises:
        HTTPException: If API key is invalid
    """
    if x_api_key != settings.admin_api_key:
        logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )


def require_admin_key(func: Callable) -> Callable:
    """
    Decorator to require admin API key for endpoints.
    
    Usage:
        @router.get("/admin/endpoint")
        @require_admin_key
        async def admin_endpoint():
            ...
    """

    @wraps(func)
    async def wrapper(*args, x_api_key: str = Header(...), **kwargs):
        await verify_admin_api_key(x_api_key)
        return await func(*args, **kwargs)

    return wrapper
