"""
Tests for GitHub authentication.
"""
import pytest
from datetime import datetime, timedelta

from app.core.github_auth import GitHubAppAuth


def test_create_jwt():
    """Test JWT creation."""
    auth = GitHubAppAuth()
    token = auth.create_jwt(expiration_seconds=300)

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_cache_installation_token():
    """Test installation token caching."""
    auth = GitHubAppAuth()

    installation_id = 12345
    token = "test-token"
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Cache token
    auth.cache_installation_token(installation_id, token, expires_at)

    # Retrieve cached token
    cached_token = auth.get_installation_token(installation_id, cached=True)

    assert cached_token == token


def test_get_expired_token():
    """Test that expired tokens are not returned."""
    auth = GitHubAppAuth()

    installation_id = 12345
    token = "test-token"
    expires_at = datetime.utcnow() - timedelta(hours=1)  # Already expired

    # Cache expired token
    auth.cache_installation_token(installation_id, token, expires_at)

    # Should return None for expired token
    cached_token = auth.get_installation_token(installation_id, cached=True)

    assert cached_token is None


def test_invalidate_token():
    """Test token invalidation."""
    auth = GitHubAppAuth()

    installation_id = 12345
    token = "test-token"
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Cache token
    auth.cache_installation_token(installation_id, token, expires_at)

    # Invalidate
    auth.invalidate_installation_token(installation_id)

    # Should return None after invalidation
    cached_token = auth.get_installation_token(installation_id, cached=True)

    assert cached_token is None
