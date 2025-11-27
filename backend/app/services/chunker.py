"""
Code chunking service - splits code into semantic units for embedding.
"""
import hashlib
from typing import Any, Optional
from uuid import UUID

from loguru import logger

from app.config import get_settings
from app.services.code_parser import code_parser

settings = get_settings()


class CodeChunker:
    """AST-aware code chunker."""

    def __init__(self):
        self.max_tokens = settings.max_chunk_tokens
        self.min_tokens = settings.min_chunk_tokens

    @staticmethod
    def compute_file_hash(content: str) -> str:
        """Compute SHA256 hash of file content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_chunk_hash(text: str) -> str:
        """Compute SHA256 hash of chunk text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return len(text) // 4

    def chunk_file(
        self, file_path: str, content: str, repo_id: UUID
    ) -> list[dict[str, Any]]:
        """
        Chunk file into semantic units.

        Args:
            file_path: File path
            content: File content
            repo_id: Repository UUID

        Returns:
            List of chunk dictionaries
        """
        language = code_parser.get_language_from_extension(file_path)
        if not language:
            logger.debug(f"Unsupported file type: {file_path}")
            return []

        file_hash = self.compute_file_hash(content)
        chunks = []

        # Try AST-based chunking
        try:
            ast_chunks = code_parser.extract_functions_fallback(content, language)

            if ast_chunks:
                for ast_chunk in ast_chunks:
                    chunk_text = ast_chunk["text"]
                    token_count = self.estimate_tokens(chunk_text)

                    # Skip tiny chunks
                    if token_count < self.min_tokens:
                        continue

                    # Split large chunks
                    if token_count > self.max_tokens:
                        split_chunks = self._split_large_chunk(
                            chunk_text,
                            ast_chunk["start_line"],
                            language,
                            repo_id,
                            file_path,
                            file_hash,
                        )
                        chunks.extend(split_chunks)
                    else:
                        chunks.append(
                            {
                                "repo_id": repo_id,
                                "file_path": file_path,
                                "language": language,
                                "start_line": ast_chunk["start_line"],
                                "end_line": ast_chunk["end_line"],
                                "chunk_text": chunk_text,
                                "ast_node_type": ast_chunk["type"],
                                "file_hash": file_hash,
                                "chunk_hash": self.compute_chunk_hash(chunk_text),
                                "metadata": {"name": ast_chunk.get("name", "")},
                            }
                        )

                logger.debug(f"Chunked {file_path}: {len(chunks)} chunks (AST)")
                return chunks

        except Exception as e:
            logger.warning(f"AST chunking failed for {file_path}: {e}")

        # Fallback: text-based chunking
        text_chunks = self._chunk_by_lines(content, language)
        for i, (start_line, end_line, text) in enumerate(text_chunks):
            chunks.append(
                {
                    "repo_id": repo_id,
                    "file_path": file_path,
                    "language": language,
                    "start_line": start_line,
                    "end_line": end_line,
                    "chunk_text": text,
                    "ast_node_type": None,
                    "file_hash": file_hash,
                    "chunk_hash": self.compute_chunk_hash(text),
                    "metadata": {"chunk_index": i},
                }
            )

        logger.debug(f"Chunked {file_path}: {len(chunks)} chunks (fallback)")
        return chunks

    def _split_large_chunk(
        self, text: str, start_line: int, language: str, repo_id: UUID, file_path: str, file_hash: str
    ) -> list[dict[str, Any]]:
        """Split large chunk into smaller pieces."""
        lines = text.split("\n")
        max_lines = self.max_tokens // 4  # Rough heuristic

        sub_chunks = []
        for i in range(0, len(lines), max_lines):
            chunk_lines = lines[i : i + max_lines]
            chunk_text = "\n".join(chunk_lines)

            sub_chunks.append(
                {
                    "repo_id": repo_id,
                    "file_path": file_path,
                    "language": language,
                    "start_line": start_line + i,
                    "end_line": start_line + i + len(chunk_lines),
                    "chunk_text": chunk_text,
                    "ast_node_type": None,
                    "file_hash": file_hash,
                    "chunk_hash": self.compute_chunk_hash(chunk_text),
                    "metadata": {"split_chunk": True},
                }
            )

        return sub_chunks

    def _chunk_by_lines(
        self, content: str, language: str, lines_per_chunk: int = 50
    ) -> list[tuple[int, int, str]]:
        """Fallback line-based chunking."""
        lines = content.split("\n")
        chunks = []

        for i in range(0, len(lines), lines_per_chunk):
            chunk_lines = lines[i : i + lines_per_chunk]
            chunk_text = "\n".join(chunk_lines)
            token_count = self.estimate_tokens(chunk_text)

            if token_count >= self.min_tokens:
                chunks.append((i + 1, i + len(chunk_lines), chunk_text))

        return chunks


# Global chunker instance
code_chunker = CodeChunker()

