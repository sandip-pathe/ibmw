"""
GitHub webhook endpoints.
"""
import json

from fastapi import APIRouter, HTTPException, Request, status
from loguru import logger
from typing import Optional
from app.core.webhook_verifier import webhook_verifier
from app.database import get_db
from app.models.database import InstallationQueries, RepositoryQueries, WebhookEventQueries
from app.models.schemas import SuccessResponse
from app.workers.job_queue import job_queue

router = APIRouter(tags=["webhooks"])


@router.post("/webhook")
async def github_webhook(request: Request):
    """
    Handle GitHub App webhooks.

    Supported events:
    - installation (created, deleted)
    - installation_repositories (added, removed)
    - push (trigger indexing)
    - pull_request (optional)
    """
    # Verify webhook signature
    payload_bytes = await webhook_verifier.verify_request(request)
    payload = json.loads(payload_bytes)

    # Get event type
    event_type = request.headers.get("X-GitHub-Event") or ""
    delivery_id = request.headers.get("X-GitHub-Delivery") or ""

    logger.info(f"Received webhook: {event_type} (delivery: {delivery_id})")

    db = await get_db()

    # Check idempotency
    async with db.acquire() as conn:
        is_processed = await WebhookEventQueries.is_processed(conn, str(delivery_id))
        if is_processed:
            logger.info(f"Webhook {delivery_id} already processed (idempotent)")
            return SuccessResponse(message="Webhook already processed")

        # Store event
        await WebhookEventQueries.insert(conn, str(delivery_id), str(event_type), payload)

    # Handle event
    try:
        if event_type == "installation":
            await handle_installation_event(payload)

        elif event_type == "installation_repositories":
            await handle_installation_repositories_event(payload)

        elif event_type == "push":
            await handle_push_event(payload)

        elif event_type == "pull_request":
            await handle_pull_request_event(payload)

        else:
            logger.info(f"Ignoring unsupported event: {event_type}")

        # Mark as processed
        async with db.acquire() as conn:
            await WebhookEventQueries.mark_processed(conn, str(delivery_id))

        return SuccessResponse(message=f"Webhook {event_type} processed successfully")

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}",
        )


async def handle_installation_event(payload: dict) -> None:
    """Handle installation created/deleted events."""
    action = payload["action"]
    installation = payload["installation"]

    db = await get_db()

    if action == "created":
        # Store installation
        installation_data = {
            "installation_id": installation["id"],
            "account_id": installation["account"]["id"],
            "account_login": installation["account"]["login"],
            "app_id": installation["app_id"],
            "target_type": installation["target_type"],
            "permissions": installation.get("permissions", {}),
            "events": installation.get("events", []),
            "repositories": payload.get("repositories", []),
        }

        async with db.acquire() as conn:
            await InstallationQueries.upsert(conn, installation_data)

        logger.info(f"Installation created: {installation['id']} for {installation['account']['login']}")

        # Index all repositories
        for repo in payload.get("repositories", []):
            await _enqueue_repo_indexing(
                installation["id"],
                repo["id"],
                repo["name"],
                repo["full_name"],
            )

    elif action == "deleted":
        # Remove installation
        async with db.acquire() as conn:
            await InstallationQueries.delete(conn, installation["id"])

        logger.info(f"Installation deleted: {installation['id']}")


async def handle_installation_repositories_event(payload: dict) -> None:
    """Handle repositories added/removed from installation."""
    action = payload["action"]
    installation = payload["installation"]

    if action == "added":
        # Index new repositories
        for repo in payload.get("repositories_added", []):
            await _enqueue_repo_indexing(
                installation["id"],
                repo["id"],
                repo["name"],
                repo["full_name"],
            )

    elif action == "removed":
        logger.info(f"Repositories removed from installation {installation['id']}")


async def handle_push_event(payload: dict) -> None:
    """Handle push events (trigger re-indexing)."""
    repository = payload["repository"]
    installation = payload["installation"]
    ref = payload["ref"]

    # Only process pushes to default branch
    if not ref.endswith(repository.get("default_branch", "main")):
        logger.info(f"Ignoring push to non-default branch: {ref}")
        return

    commit_sha = payload.get("after")

    # Detect changed files from commits
    changed_files = set()
    for commit in payload.get("commits", []):
        changed_files.update(commit.get("added", []))
        changed_files.update(commit.get("modified", []))
        changed_files.update(commit.get("removed", []))

    # Get repo from database
    db = await get_db()
    async with db.acquire() as conn:
        repo = await RepositoryQueries.get_by_github_id(conn, repository["id"])

    if repo:
        # Enqueue selective re-indexing job for changed files
        # TODO: Implement selective re-indexing for changed files if needed
        job_queue.enqueue_indexing_job(
            repo_id=repo["repo_id"],
            installation_id=installation["id"],
            full_name=repository["full_name"],
            commit_sha=commit_sha,
        )
        logger.info(f"Enqueued selective re-indexing for {repository['full_name']} after push: {changed_files}")
    else:
        # First-time indexing
        await _enqueue_repo_indexing(
            installation["id"],
            repository["id"],
            repository["name"],
            repository["full_name"],
            commit_sha,
        )


async def handle_pull_request_event(payload: dict) -> None:
    """Handle pull request events (optional compliance check)."""
    action = payload["action"]
    pull_request = payload["pull_request"]

    if action in ["opened", "synchronize"]:
        logger.info(f"PR event: {action} for PR #{pull_request['number']}")
        # TODO: Implement PR-specific compliance check
        # This would analyze only changed files and post Check Run annotations


async def _enqueue_repo_indexing(
    installation_id: int,
    github_id: int,
    repo_name: str,
    full_name: str,
    commit_sha: Optional[str] = None,
) -> None:
    """Helper to store repo and enqueue indexing."""
    db = await get_db()

    # Store repository
    repo_data = {
        "installation_id": installation_id,
        "github_id": github_id,
        "repo_name": repo_name,
        "full_name": full_name,
        "private": True,  # Default assumption
        "default_branch": "main",
        "clone_url": f"https://github.com/{full_name}.git",
    }

    async with db.acquire() as conn:
        repo_id = await RepositoryQueries.upsert(conn, repo_data)

    # Enqueue indexing job
    job_queue.enqueue_indexing_job(
        repo_id=repo_id,
        installation_id=installation_id,
        full_name=full_name,
        commit_sha=commit_sha,
    )

    logger.info(f"Enqueued indexing job for {full_name}")
