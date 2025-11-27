"""
User repository management endpoints.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from pydantic import BaseModel
from loguru import logger
from typing import Optional

from app.core.github_oauth import github_oauth
from app.database import get_db
from app.core.security import verify_admin_api_key
from app.api.auth import neon_query

router = APIRouter(prefix="/user", tags=["User Repositories"])


class GitHubAuthUrlRequest(BaseModel):
    redirect_uri: str
    state: Optional[str] = None


class GitHubAuthRequest(BaseModel):
    code: str
    redirect_uri: str


class RepoSelectionRequest(BaseModel):
    repo_ids: list[int]
    access_token: str


class UserRepoResponse(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    owner: dict
    description: Optional[str]
    html_url: str
    default_branch: str
    language: Optional[str]
    updated_at: str



@router.post("/auth/github/callback")
async def github_oauth_callback(request: GitHubAuthRequest):
    """
    Exchange GitHub OAuth code for access token and link to Stack Auth user.
    """
    from app.config import get_settings
    settings = get_settings()
    try:
        # Exchange code for token
        token_response = await github_oauth.exchange_code_for_token(
            code=request.code,
            redirect_uri=settings.github_oauth_redirect_uri
        )
        access_token = token_response.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        # Get user info
        user_info = await github_oauth.get_user_info(access_token)
        email = user_info.get("email")
        # If email is missing, fetch from /user/emails
        if not email:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )
                if resp.status_code == 200:
                    emails = resp.json()
                    # Find primary and verified email
                    primary_email = next((e["email"] for e in emails if e.get("primary") and e.get("verified")), None)
                    email = primary_email or (emails[0]["email"] if emails else None)
        if not email:
            raise HTTPException(status_code=400, detail="GitHub user email not found")
        # Update DB: store github_access_token for user
        sql = "UPDATE users SET github_access_token = $1 WHERE email = $2"
        neon_query(sql, [access_token, email])
        return {
            "access_token": access_token,
            "user": {
                "id": user_info.get("id"),
                "login": user_info.get("login"),
                "name": user_info.get("name"),
                "email": email,
                "avatar_url": user_info.get("avatar_url"),
            }
        }
    except Exception as e:
        logger.error(f"GitHub OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))




@router.get("/repos")
async def list_user_repositories(
    authorization: str = Header(None, description="Bearer {stack_auth_token or github_access_token}")
):
    """
    List all repositories accessible by the authenticated user.
    In development, skips Stack Auth validation and uses GitHub token directly.
    """
    from app.config import get_settings
    settings = get_settings()
    logger.info("[API] /repos called")
    try:
        if not authorization or not authorization.startswith("Bearer "):
            logger.warning("[API] Missing or invalid authorization header")
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        github_access_token = authorization.replace("Bearer ", "")
        logger.info(f"[API] Using GitHub token: {github_access_token[:6]}... (truncated)")
        repos = await github_oauth.list_user_repos(github_access_token)
        logger.info(f"[API] Fetched {len(repos)} raw repos from GitHub")
        formatted_repos = [
            UserRepoResponse(
                id=repo["id"],
                name=repo["name"],
                full_name=repo["full_name"],
                private=repo["private"],
                owner={
                    "login": repo["owner"]["login"],
                    "avatar_url": repo["owner"]["avatar_url"],
                },
                description=repo.get("description"),
                html_url=repo["html_url"],
                default_branch=repo.get("default_branch", "main"),
                language=repo.get("language"),
                updated_at=repo["updated_at"],
            )
            for repo in repos
        ]
        logger.info(f"[API] Returning {len(formatted_repos)} formatted repos to frontend")
        return {"repos": formatted_repos, "total": len(formatted_repos)}
    except Exception as e:
        logger.error(f"[API] Failed to list user repos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repos/index")
async def index_selected_repositories(
    request: RepoSelectionRequest,
    authorization: str = Header(..., description="Bearer {stack_auth_token}"),
    db=Depends(get_db)
):
    """
    Index selected repositories for compliance analysis.
    This triggers the code parsing, embedding, and storage pipeline.
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        github_access_token = authorization.replace("Bearer ", "")
        repo_ids = request.repo_ids
        # Get full repo list to find selected ones
        all_repos = await github_oauth.list_user_repos(github_access_token)
        selected_repos = [r for r in all_repos if r["id"] in repo_ids]
        
        if not selected_repos:
            raise HTTPException(status_code=404, detail="No matching repositories found")
        
        from app.workers.job_queue import job_queue
        indexed_repos = []
        job_ids = []
        for repo in selected_repos:
            logger.info(f"Queuing indexing job for: {repo['full_name']}")
            # Store repo metadata in database (requires installation_id = NULL for now)
            async with db.acquire() as conn:
                repo_row = await conn.fetchrow(
                    """
                    INSERT INTO repos (
                        github_id, repo_name, full_name, 
                        private, default_branch, installation_id
                    ) VALUES ($1, $2, $3, $4, $5, NULL)
                    ON CONFLICT (github_id) DO UPDATE SET
                        repo_name = EXCLUDED.repo_name,
                        updated_at = NOW()
                    RETURNING repo_id
                    """,
                    repo["id"],
                    repo["name"],
                    repo["full_name"],
                    repo["private"],
                    repo.get("default_branch", "main"),
                )
                repo_id = repo_row["repo_id"] if repo_row else None
            # Enqueue indexing job (installation_id is 0 for OAuth)
            from uuid import UUID
            if repo_id is None:
                raise HTTPException(status_code=500, detail="Failed to retrieve repo_id from database")
            if isinstance(repo_id, str):
                repo_uuid = UUID(repo_id)
            elif isinstance(repo_id, UUID):
                repo_uuid = repo_id
            else:
                # If repo_id is int, convert to string then UUID
                repo_uuid = UUID(str(repo_id))
            job_id = job_queue.enqueue_indexing_job(
                repo_id=repo_uuid,
                installation_id=0,  # Use 0 for OAuth/no installation
                full_name=repo["full_name"],
                commit_sha=None,
                oauth_token=github_access_token  # Pass OAuth token for cloning
            )
            job_ids.append(job_id)
            indexed_repos.append({
                "id": repo["id"],
                "full_name": repo["full_name"],
                "status": "queued",
                "job_id": job_id
            })
        return {
            "success": True,
            "message": f"Queued {len(indexed_repos)} repositories for indexing",
            "repos": indexed_repos,
            "job_ids": job_ids
        }
    
    except Exception as e:
        logger.error(f"Failed to index repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos/{repo_id}/status")
async def get_repository_indexing_status(
    repo_id: int,
        authorization: str = Header(..., description="Bearer {stack_auth_token}"),
    db=Depends(get_db)
):
    """
    Check indexing status of a repository.
    """
    try:
        async with db.acquire() as conn:
            repo = await conn.fetchrow(
                """
                SELECT r.*, 
                       COUNT(DISTINCT cc.id) as chunks_count,
                       MAX(cc.created_at) as last_indexed
                FROM repos r
                LEFT JOIN code_chunks cc ON cc.repo_id = r.id
                WHERE r.github_repo_id = $1
                GROUP BY r.id
                """,
                repo_id
            )
            if not repo:
                raise HTTPException(status_code=404, detail="Repository not found")
            return {
                "repo_id": repo["github_repo_id"],
                "full_name": repo["full_name"],
                "status": "indexed" if repo["chunks_count"] > 0 else "pending",
                "chunks_count": repo["chunks_count"],
                "last_indexed": repo["last_indexed"],
            }
    except Exception as e:
        logger.error(f"Failed to get repo status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
