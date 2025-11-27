"""
Database model helpers and query builders.
"""
from datetime import datetime
from typing import Any, Optional, List
from uuid import UUID

from asyncpg import Record


def record_to_dict(record: Optional[Record]) -> Optional[dict[str, Any]]:
    """Convert asyncpg Record to dictionary."""
    if record is None:
        return None
    return dict(record)


def records_to_list(records: list[Record]) -> list[dict[str, Any]]:
    """Convert list of asyncpg Records to list of dictionaries."""
    return [dict(record) for record in records]


class InstallationQueries:
    """SQL queries for installations table."""

    @staticmethod
    async def upsert(conn, installation_data: dict[str, Any]) -> int:
        """Insert or update installation."""
        query = """
            INSERT INTO installations (
                installation_id, account_id, account_login, app_id,
                target_type, permissions, events, repositories
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (installation_id) DO UPDATE SET
                account_login = EXCLUDED.account_login,
                permissions = EXCLUDED.permissions,
                events = EXCLUDED.events,
                repositories = EXCLUDED.repositories,
                updated_at = NOW()
            RETURNING installation_id
        """
        return await conn.fetchval(
            query,
            installation_data["installation_id"],
            installation_data["account_id"],
            installation_data["account_login"],
            installation_data["app_id"],
            installation_data["target_type"],
            installation_data["permissions"],
            installation_data["events"],
            installation_data["repositories"],
        )

    @staticmethod
    async def get_by_id(conn, installation_id: int) -> Optional[dict[str, Any]]:
        """Get installation by ID."""
        query = "SELECT * FROM installations WHERE installation_id = $1"
        record = await conn.fetchrow(query, installation_id)
        return record_to_dict(record)

    @staticmethod
    async def list_all(conn, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """List all installations."""
        query = """
            SELECT * FROM installations
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        records = await conn.fetch(query, limit, offset)
        return records_to_list(records)

    @staticmethod
    async def delete(conn, installation_id: int) -> bool:
        """Delete installation."""
        query = "DELETE FROM installations WHERE installation_id = $1"
        result = await conn.execute(query, installation_id)
        return result == "DELETE 1"


class RepositoryQueries:
    """SQL queries for repos table."""

    @staticmethod
    async def upsert(conn, repo_data: dict[str, Any]) -> UUID:
        """Insert or update repository."""
        query = """
            INSERT INTO repos (
                installation_id, github_id, repo_name, full_name,
                private, default_branch, clone_url
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (github_id) DO UPDATE SET
                repo_name = EXCLUDED.repo_name,
                full_name = EXCLUDED.full_name,
                default_branch = EXCLUDED.default_branch,
                clone_url = EXCLUDED.clone_url,
                updated_at = NOW()
            RETURNING repo_id
        """
        return await conn.fetchval(
            query,
            repo_data["installation_id"],
            repo_data["github_id"],
            repo_data["repo_name"],
            repo_data["full_name"],
            repo_data["private"],
            repo_data.get("default_branch", "main"),
            repo_data.get("clone_url"),
        )

    @staticmethod
    async def get_by_id(conn, repo_id: UUID) -> Optional[dict[str, Any]]:
        """Get repository by UUID."""
        query = "SELECT * FROM repos WHERE repo_id = $1"
        record = await conn.fetchrow(query, repo_id)
        return record_to_dict(record)

    @staticmethod
    async def get_by_github_id(conn, github_id: int) -> Optional[dict[str, Any]]:
        """Get repository by GitHub ID."""
        query = "SELECT * FROM repos WHERE github_id = $1"
        record = await conn.fetchrow(query, github_id)
        return record_to_dict(record)

    @staticmethod
    async def update_sync_status(
        conn, repo_id: UUID, commit_sha: str, file_count: int, chunk_count: int
    ) -> None:
        """Update repository sync status."""
        query = """
            UPDATE repos SET
                last_synced_at = NOW(),
                last_commit_sha = $2,
                indexed_file_count = $3,
                total_chunks = $4
            WHERE repo_id = $1
        """
        await conn.execute(query, repo_id, commit_sha, file_count, chunk_count)


class CodeMapQueries:
    """SQL queries for code_map table."""

    @staticmethod
    async def insert_batch(conn, chunks: list[dict[str, Any]]) -> int:
        """Batch insert code map chunks."""
        import json
        
        query = """
            INSERT INTO code_map (
                repo_id, file_path, language, start_line, end_line,
                chunk_text, ast_node_type, file_hash, chunk_hash,
                embedding, nl_summary, metadata, call_links, variables, config_keys, semantic_tags, previous_hash, delta_type
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::vector, $11, $12::jsonb, $13::jsonb, $14::jsonb, $15::jsonb, $16::jsonb, $17, $18)
            ON CONFLICT (chunk_hash) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                nl_summary = EXCLUDED.nl_summary,
                call_links = EXCLUDED.call_links,
                variables = EXCLUDED.variables,
                config_keys = EXCLUDED.config_keys,
                semantic_tags = EXCLUDED.semantic_tags,
                previous_hash = EXCLUDED.previous_hash,
                delta_type = EXCLUDED.delta_type,
                updated_at = NOW()
        """
        
        def format_embedding(emb):
            """Convert Python list to PostgreSQL vector format."""
            if emb is None:
                return None
            if isinstance(emb, list):
                return f"[{','.join(map(str, emb))}]"
            return emb
        
        def format_jsonb(obj):
            """Convert Python dict/list to JSON string for JSONB."""
            if obj is None:
                return None
            return json.dumps(obj)
        
        async with conn.transaction():
            await conn.executemany(
                query,
                [
                    (
                        chunk["repo_id"],
                        chunk["file_path"],
                        chunk["language"],
                        chunk["start_line"],
                        chunk["end_line"],
                        chunk["chunk_text"],
                        chunk.get("ast_node_type"),
                        chunk["file_hash"],
                        chunk["chunk_hash"],
                        format_embedding(chunk.get("embedding")),
                        chunk.get("nl_summary"),
                        format_jsonb(chunk.get("metadata", {})),
                        format_jsonb(chunk.get("call_links", [])),
                        format_jsonb(chunk.get("variables", {})),
                        format_jsonb(chunk.get("config_keys", {})),
                        format_jsonb(chunk.get("semantic_tags", [])),
                        chunk.get("previous_hash"),
                        chunk.get("delta_type"),
                    )
                    for chunk in chunks
                ],
            )
        return len(chunks)

    @staticmethod
    async def get_by_repo(
        conn, repo_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get code map chunks for a repository."""
        query = """
            SELECT * FROM code_map
            WHERE repo_id = $1
            ORDER BY file_path, start_line
            LIMIT $2 OFFSET $3
        """
        records = await conn.fetch(query, repo_id, limit, offset)
        return records_to_list(records)

    @staticmethod
    async def search_similar(
        conn, embedding: list[float], repo_id: Optional[UUID], top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Find similar code map chunks using vector similarity."""
        if repo_id:
            query = """
                SELECT *,
                    (embedding <-> $1::vector) AS distance
                FROM code_map
                WHERE repo_id = $2
                ORDER BY embedding <-> $1::vector
                LIMIT $3
            """
            records = await conn.fetch(query, embedding, repo_id, top_k)
        else:
            query = """
                SELECT *,
                    (embedding <-> $1::vector) AS distance
                FROM code_map
                ORDER BY embedding <-> $1::vector
                LIMIT $2
            """
            records = await conn.fetch(query, embedding, top_k)
        return records_to_list(records)

class FlowGraphQueries:
    """SQL queries for flow_graph table."""

    @staticmethod
    async def insert(conn, graph_data: dict[str, Any]) -> UUID:
        query = """
            INSERT INTO flow_graph (
                repo_id, node_id, file_path, function_name, edges, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        return await conn.fetchval(
            query,
            graph_data["repo_id"],
            graph_data["node_id"],
            graph_data["file_path"],
            graph_data["function_name"],
            graph_data.get("edges", []),
            graph_data.get("metadata", {}),
        )

    @staticmethod
    async def get_by_repo(conn, repo_id: UUID) -> list[dict[str, Any]]:
        query = "SELECT * FROM flow_graph WHERE repo_id = $1"
        records = await conn.fetch(query, repo_id)
        return records_to_list(records)

class ComplianceEvidenceQueries:
    """SQL queries for compliance_evidence table."""

    @staticmethod
    async def insert(conn, evidence_data: dict[str, Any]) -> UUID:
        query = """
            INSERT INTO compliance_evidence (
                repo_id, rule_id, chunk_id, finding_text, severity, line_number
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        return await conn.fetchval(
            query,
            evidence_data["repo_id"],
            evidence_data["rule_id"],
            evidence_data["chunk_id"],
            evidence_data["finding_text"],
            evidence_data["severity"],
            evidence_data["line_number"],
        )

    @staticmethod
    async def get_by_repo(conn, repo_id: UUID) -> list[dict[str, Any]]:
        query = "SELECT * FROM compliance_evidence WHERE repo_id = $1"
        records = await conn.fetch(query, repo_id)
        return records_to_list(records)


class RegulationChunkQueries:
    """SQL queries for regulation_chunks table."""

    @staticmethod
    async def insert_batch(conn, chunks: list[dict[str, Any]]) -> int:
        """Batch insert regulation chunks."""
        query = """
            INSERT INTO regulation_chunks (
                rule_id, rule_section, source_document, chunk_text,
                chunk_index, chunk_hash, embedding, nl_summary, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (chunk_hash) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                nl_summary = EXCLUDED.nl_summary,
                updated_at = NOW()
        """
        async with conn.transaction():
            await conn.executemany(
                query,
                [
                    (
                        chunk["rule_id"],
                        chunk.get("rule_section"),
                        chunk.get("source_document"),
                        chunk["chunk_text"],
                        chunk["chunk_index"],
                        chunk["chunk_hash"],
                        chunk.get("embedding"),
                        chunk.get("nl_summary"),
                        chunk.get("metadata", {}),
                    )
                    for chunk in chunks
                ],
            )
        return len(chunks)

    @staticmethod
    async def get_by_rule_id(conn, rule_id: str) -> list[dict[str, Any]]:
        """Get all chunks for a rule."""
        query = """
            SELECT * FROM regulation_chunks
            WHERE rule_id = $1
            ORDER BY chunk_index
        """
        records = await conn.fetch(query, rule_id)
        return records_to_list(records)

    @staticmethod
    async def list_all_rules(conn) -> list[str]:
        """List all unique rule IDs."""
        query = "SELECT DISTINCT rule_id FROM regulation_chunks ORDER BY rule_id"
        records = await conn.fetch(query)
        return [record["rule_id"] for record in records]


class ScanQueries:
    """SQL queries for scans table."""

    @staticmethod
    async def create(conn, scan_data: dict[str, Any]) -> UUID:
        """Create a new scan."""
        query = """
            INSERT INTO scans (
                repo_id, scan_type, status, initiator, commit_sha, started_at
            ) VALUES ($1, $2, $3, $4, $5, NOW())
            RETURNING scan_id
        """
        return await conn.fetchval(
            query,
            scan_data["repo_id"],
            scan_data.get("scan_type", "full"),
            "running",
            scan_data.get("initiator"),
            scan_data.get("commit_sha"),
        )

    @staticmethod
    async def update_status(
        conn,
        scan_id: UUID,
        status: str,
        result: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update scan status."""
        query = """
            UPDATE scans SET
                status = $2,
                result = $3,
                error = $4,
                completed_at = CASE WHEN $2 IN ('completed', 'failed') THEN NOW() ELSE NULL END
            WHERE scan_id = $1
        """
        await conn.execute(query, scan_id, status, result, error)

    @staticmethod
    async def update_violation_counts(conn, scan_id: UUID) -> None:
        """Update violation count statistics."""
        query = """
            UPDATE scans SET
                total_violations = (
                    SELECT COUNT(*) FROM violations WHERE scan_id = $1
                ),
                critical_violations = (
                    SELECT COUNT(*) FROM violations WHERE scan_id = $1 AND severity = 'critical'
                ),
                high_violations = (
                    SELECT COUNT(*) FROM violations WHERE scan_id = $1 AND severity = 'high'
                ),
                medium_violations = (
                    SELECT COUNT(*) FROM violations WHERE scan_id = $1 AND severity = 'medium'
                ),
                low_violations = (
                    SELECT COUNT(*) FROM violations WHERE scan_id = $1 AND severity = 'low'
                )
            WHERE scan_id = $1
        """
        await conn.execute(query, scan_id)

    @staticmethod
    async def get_by_id(conn, scan_id: UUID) -> Optional[dict[str, Any]]:
        """Get scan by ID."""
        query = "SELECT * FROM scans WHERE scan_id = $1"
        record = await conn.fetchrow(query, scan_id)
        return record_to_dict(record)

class WebhookEventQueries:
    """SQL queries for webhook_events table."""

    @staticmethod
    async def insert(conn, event_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """Insert webhook event for idempotency."""
        query = """
            INSERT INTO webhook_events (
                event_id, event_type, installation_id, repository_id, payload
            ) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (event_id) DO NOTHING
        """
        await conn.execute(
            query,
            event_id,
            event_type,
            payload.get("installation", {}).get("id"),
            payload.get("repository", {}).get("id"),
            payload,
        )

    @staticmethod
    async def is_processed(conn, event_id: str) -> bool:
        """Check if event was already processed."""
        query = "SELECT processed FROM webhook_events WHERE event_id = $1"
        result = await conn.fetchval(query, event_id)
        return result is True

    @staticmethod
    async def mark_processed(conn, event_id: str) -> None:
        """Mark event as processed."""
        query = """
            UPDATE webhook_events SET processed = true, processed_at = NOW()
            WHERE event_id = $1
        """
        await conn.execute(query, event_id)

class ViolationQueries:
    """SQL queries for violations table."""

    @staticmethod
    async def insert_batch(conn, violations: list[dict[str, Any]]) -> int:
        """Batch insert violations."""
        # Added status default
        query = """
            INSERT INTO violations (
                scan_id, rule_id, code_chunk_id, regulation_chunk_id,
                verdict, severity, severity_score, explanation,
                evidence, remediation, file_path, start_line, end_line, 
                metadata, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 'pending')
        """
        async with conn.transaction():
            await conn.executemany(
                query,
                [
                    (
                        v["scan_id"],
                        v["rule_id"],
                        v["code_chunk_id"],
                        v.get("regulation_chunk_id"),
                        v["verdict"],
                        v["severity"],
                        v["severity_score"],
                        v["explanation"],
                        v.get("evidence"),
                        v.get("remediation"),
                        v["file_path"],
                        v["start_line"],
                        v["end_line"],
                        v.get("metadata", {}),
                    )
                    for v in violations
                ],
            )
        return len(violations)

    @staticmethod
    async def get_by_scan(
        conn, scan_id: UUID, severity: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get violations for a scan."""
        if severity:
            query = """
                SELECT * FROM violations
                WHERE scan_id = $1 AND severity = $2
                ORDER BY severity_score DESC, created_at DESC
            """
            records = await conn.fetch(query, scan_id, severity)
        else:
            query = """
                SELECT * FROM violations
                WHERE scan_id = $1
                ORDER BY severity_score DESC, created_at DESC
            """
            records = await conn.fetch(query, scan_id)
        return records_to_list(records)

    @staticmethod
    async def get_pending(conn, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Get pending violations across all scans."""
        query = """
            SELECT v.*, r.full_name as repo_name
            FROM violations v
            JOIN scans s ON v.scan_id = s.scan_id
            JOIN repos r ON s.repo_id = r.repo_id
            WHERE v.status = 'pending'
            ORDER BY v.severity_score DESC, v.created_at DESC
            LIMIT $1 OFFSET $2
        """
        records = await conn.fetch(query, limit, offset)
        return records_to_list(records)

    @staticmethod
    async def update_status(
        conn, 
        violation_id: UUID, 
        status: str, 
        note: Optional[str], 
        user_id: Optional[str]
    ) -> Optional[dict[str, Any]]:
        """Update violation status."""
        query = """
            UPDATE violations SET
                status = $2,
                reviewer_note = $3,
                reviewed_by = $4,
                reviewed_at = NOW()
            WHERE violation_id = $1
            RETURNING *
        """
        record = await conn.fetchrow(query, violation_id, status, note, user_id)
        return record_to_dict(record)

    @staticmethod
    async def update_jira_ticket(conn, violation_id: UUID, ticket_id: str) -> None:
        """Link Jira ticket to violation."""
        query = """
            UPDATE violations SET jira_ticket_id = $2
            WHERE violation_id = $1
        """
        await conn.execute(query, violation_id, ticket_id)