"""
Tests for code chunker.
"""
import pytest
from uuid import uuid4

from app.services.chunker import code_chunker


def test_chunk_python_file(sample_code_python):
    """Test chunking Python file."""
    repo_id = uuid4()
    file_path = "src/banking.py"

    chunks = code_chunker.chunk_file(file_path, sample_code_python, repo_id)

    assert len(chunks) > 0

    # Check chunk structure
    for chunk in chunks:
        assert "repo_id" in chunk
        assert "file_path" in chunk
        assert "language" in chunk
        assert "start_line" in chunk
        assert "end_line" in chunk
        assert "chunk_text" in chunk
        assert "file_hash" in chunk
        assert "chunk_hash" in chunk

        assert chunk["language"] == "python"
        assert chunk["repo_id"] == repo_id


def test_chunk_javascript_file(sample_code_javascript):
    """Test chunking JavaScript file."""
    repo_id = uuid4()
    file_path = "src/payment.js"

    chunks = code_chunker.chunk_file(file_path, sample_code_javascript, repo_id)

    assert len(chunks) > 0

    for chunk in chunks:
        assert chunk["language"] == "javascript"


def test_chunk_unsupported_file():
    """Test chunking unsupported file type."""
    repo_id = uuid4()
    file_path = "README.md"
    content = "# This is markdown"

    chunks = code_chunker.chunk_file(file_path, content, repo_id)

    assert len(chunks) == 0


def test_compute_hashes(sample_code_python):
    """Test hash computation."""
    file_hash = code_chunker.compute_file_hash(sample_code_python)
    chunk_hash = code_chunker.compute_chunk_hash(sample_code_python)

    assert len(file_hash) == 64  # SHA256 hex
    assert len(chunk_hash) == 64


def test_estimate_tokens():
    """Test token estimation."""
    text = "a" * 400  # 400 characters
    tokens = code_chunker.estimate_tokens(text)

    assert tokens == 100  # 400 / 4
