"""
Tests for API endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health endpoint."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_admin_health_endpoint(client, admin_headers):
    """Test detailed admin health endpoint."""
    with patch("app.api.admin.get_db", new_callable=AsyncMock):
        response = await client.get("/admin/health", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data


@pytest.mark.asyncio
async def test_admin_endpoint_requires_auth(client):
    """Test admin endpoints require API key."""
    response = await client.get("/admin/repos")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoint_with_invalid_key(client):
    """Test admin endpoints reject invalid API key."""
    response = await client.get(
        "/admin/repos",
        headers={"X-API-Key": "invalid-key"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_installations(client, admin_headers):
    """Test listing installations."""
    with patch("app.api.installations.get_db", new_callable=AsyncMock):
        response = await client.get(
            "/installations",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)