"""
Installation management endpoints.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.core.security import verify_admin_api_key
from app.database import get_db
from app.models.database import InstallationQueries, RepositoryQueries
from app.models.schemas import InstallationResponse, RepositoryResponse, SuccessResponse
from app.workers.job_queue import job_queue

router = APIRouter(prefix="/installations", tags=["installations"])


@router.get("", dependencies=[Depends(verify_admin_api_key)])
async def list_installations(
    limit: int = 100, offset: int = 0
) -> list[InstallationResponse]:
    """List all GitHub App installations."""
    db = await get_db()

    async with db.acquire() as conn:
        installations = await InstallationQueries.list_all(conn, limit, offset)

    return [
        InstallationResponse(
            installation_id=i["installation_id"],
            account_login=i["account_login"],
            account_id=i["account_id"],
            target_type=i["target_type"],
            repositories_count=len(i.get("repositories", [])),
            created_at=i["created_at"],
            updated_at=i["updated_at"],
        )
        for i in installations
    ]


@router.get("/{installation_id}", dependencies=[Depends(verify_admin_api_key)])
async def get_installation(installation_id: int) -> InstallationResponse:
    """Get installation details."""
    db = await get_db()

    async with db.acquire() as conn:
        installation = await InstallationQueries.get_by_id(conn, installation_id)

    if not installation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Installation {installation_id} not found",
        )

    return InstallationResponse(
        installation_id=installation["installation_id"],
        account_login=installation["account_login"],
        account_id=installation["account_id"],
        target_type=installation["target_type"],
        repositories_count=len(installation.get("repositories", [])),
        created_at=installation["created_at"],
        updated_at=installation["updated_at"],
    )


@router.post("/{installation_id}/sync", dependencies=[Depends(verify_admin_api_key)])
async def sync_installation(installation_id: int) -> SuccessResponse:
    """
    Manually trigger sync for all repositories in an installation.
    
    This will enqueue indexing jobs for all repos in the installation.
    """
    db = await get_db()

    async with db.acquire() as conn:
        installation = await InstallationQueries.get_by_id(conn, installation_id)

        if not installation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Installation {installation_id} not found",
            )

        # Get all repos for this installation
        repos = await conn.fetch(
            "SELECT * FROM repos WHERE installation_id = $1",
            installation_id,
        )

    # Enqueue jobs
    job_ids = []
    for repo in repos:
        job_id = job_queue.enqueue_indexing_job(
            repo_id=repo["repo_id"],
            installation_id=installation_id,
            full_name=repo["full_name"],
        )
        job_ids.append(job_id)

    logger.info(f"Enqueued {len(job_ids)} indexing jobs for installation {installation_id}")

    return SuccessResponse(
        message=f"Enqueued {len(job_ids)} indexing jobs",
        data={"job_ids": job_ids},
    )


@router.get("/{installation_id}/repos", dependencies=[Depends(verify_admin_api_key)])
async def list_installation_repos(
    installation_id: int,
    limit: int = 100,
    offset: int = 0,
) -> list[RepositoryResponse]:
    """List repositories for an installation."""
    db = await get_db()

    async with db.acquire() as conn:
        repos = await conn.fetch(
            """
            SELECT * FROM repos
            WHERE installation_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            installation_id,
            limit,
            offset,
        )

    return [
        RepositoryResponse(
            repo_id=r["repo_id"],
            installation_id=r["installation_id"],
            github_id=r["github_id"],
            repo_name=r["repo_name"],
            full_name=r["full_name"],
            private=r["private"],
            default_branch=r["default_branch"],
            last_synced_at=r["last_synced_at"],
            last_commit_sha=r["last_commit_sha"],
            indexed_file_count=r["indexed_file_count"],
            total_chunks=r["total_chunks"],
            created_at=r["created_at"],
        )
        for r in repos
    ]

