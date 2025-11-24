"""
Tests for embeddings service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.embeddings import embeddings_service


@pytest.mark.asyncio
async def test_embed_text():
    """Test single text embedding."""
    with patch.object(embeddings_service.client.embeddings, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)]
        )

        embedding = await embeddings_service.embed_text("test text")

        assert len(embedding) == 1536
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_embed_batch():
    """Test batch text embedding."""
    texts = ["text 1", "text 2", "text 3"]

    with patch.object(embeddings_service.client.embeddings, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = MagicMock(
            data=[
                MagicMock(embedding=[0.1] * 1536),
                MagicMock(embedding=[0.2] * 1536),
                MagicMock(embedding=[0.3] * 1536),
            ]
        )

        embeddings = await embeddings_service.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 1536 for e in embeddings)


def test_compute_text_hash():
    """Test text hash computation."""
    text = "test text"
    hash1 = embeddings_service.compute_text_hash(text)
    hash2 = embeddings_service.compute_text_hash(text)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex
