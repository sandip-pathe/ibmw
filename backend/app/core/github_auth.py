"""
GitHub App JWT authentication and installation token management.
"""
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from loguru import logger

from app.config import get_settings
from app.core.exceptions import GitHubAuthError

settings = get_settings()


class GitHubAppAuth:
    """GitHub App authentication manager."""

    def __init__(self):
        self.app_id = settings.github_app_id
        self.private_key = self._load_private_key(settings.github_private_key_path)
        self._installation_tokens: dict[int, tuple[str, datetime]] = {}

    def _load_private_key(self, key_path: Path) -> bytes:
        """Load GitHub App private key from file."""
        try:
            with open(key_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend(),
                )
            # Convert to PEM bytes
            return private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        except Exception as e:
            logger.error(f"Failed to load GitHub private key: {e}")
            raise GitHubAuthError(f"Failed to load private key: {e}")

    def create_jwt(self, expiration_seconds: int = 600) -> str:
        """
        Create GitHub App JWT token.
        
        Args:
            expiration_seconds: Token expiration time (max 600 seconds)
            
        Returns:
            JWT token string
        """
        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued 60 seconds in the past to allow for clock drift
            "exp": now + expiration_seconds,
            "iss": self.app_id,
        }

        try:
            token = jwt.encode(payload, self.private_key, algorithm="RS256")
            logger.debug(f"Created GitHub App JWT (expires in {expiration_seconds}s)")
            return token
        except Exception as e:
            logger.error(f"Failed to create JWT: {e}")
            raise GitHubAuthError(f"Failed to create JWT: {e}")

    def get_installation_token(
        self, installation_id: int, cached: bool = True
    ) -> Optional[str]:
        """
        Get cached installation token if valid.
        
        Args:
            installation_id: GitHub App installation ID
            cached: Whether to use cached token
            
        Returns:
            Installation token or None if not cached/expired
        """
        if not cached:
            return None

        if installation_id in self._installation_tokens:
            token, expires_at = self._installation_tokens[installation_id]
            # Return token if it expires more than 5 minutes from now
            if expires_at > datetime.utcnow() + timedelta(minutes=5):
                logger.debug(f"Using cached installation token for {installation_id}")
                return token

        return None

    def cache_installation_token(
        self, installation_id: int, token: str, expires_at: datetime
    ) -> None:
        """
        Cache installation token.
        
        Args:
            installation_id: GitHub App installation ID
            token: Installation access token
            expires_at: Token expiration datetime
        """
        self._installation_tokens[installation_id] = (token, expires_at)
        logger.debug(
            f"Cached installation token for {installation_id} (expires: {expires_at})"
        )

    def invalidate_installation_token(self, installation_id: int) -> None:
        """Invalidate cached installation token."""
        if installation_id in self._installation_tokens:
            del self._installation_tokens[installation_id]
            logger.debug(f"Invalidated cached token for installation {installation_id}")


# Global auth instance
github_auth = GitHubAppAuth()
