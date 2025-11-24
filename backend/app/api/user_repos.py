"""
User repository management endpoints.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from pydantic import BaseModel
from loguru import logger
from typing import Optional

from app.core.github_oauth import github_oauth
from app.core.security import verify_admin_api_key
from app.database import get_db

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


@router.post("/auth/github/authorize")
async def get_github_authorization_url(request: GitHubAuthUrlRequest):
    """
    Generate GitHub OAuth authorization URL.
    
    Frontend redirects user to this URL to authorize the app.
    """
    try:
        auth_url = github_oauth.get_authorization_url(
            redirect_uri=request.redirect_uri,
            state=request.state
        )
        
        return {"authorization_url": auth_url}
    
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/github/callback")
async def github_oauth_callback(request: GitHubAuthRequest):
    """
    Exchange GitHub OAuth code for access token.
    
    Frontend calls this after user authorizes on GitHub.
    """
    try:
        # Exchange code for token
        token_response = await github_oauth.exchange_code_for_token(
            code=request.code,
            redirect_uri=request.redirect_uri
        )
        
        access_token = token_response.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Get user info
        user_info = await github_oauth.get_user_info(access_token)
        
        return {
            "access_token": access_token,
            "user": {
                "id": user_info.get("id"),
                "login": user_info.get("login"),
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "avatar_url": user_info.get("avatar_url"),
            }
        }
    
    except Exception as e:
        logger.error(f"GitHub OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/repos")
async def list_user_repositories(
    authorization: str = Header(..., description="Bearer {access_token}")
):
    """
    List all repositories accessible by the authenticated user.
    
    Requires: Authorization: Bearer {github_access_token}
    """
    try:
        # Extract token from Bearer header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        access_token = authorization.replace("Bearer ", "")
        
        # Fetch repos from GitHub
        repos = await github_oauth.list_user_repos(access_token)
        
        # Format response
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
        
        return {"repos": formatted_repos, "total": len(formatted_repos)}
    
    except Exception as e:
        logger.error(f"Failed to list user repos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repos/index")
async def index_selected_repositories(
    request: RepoSelectionRequest,
    db=Depends(get_db)
):
    """
    Index selected repositories for compliance analysis.
    
    This triggers the code parsing, embedding, and storage pipeline.
    """
    try:
        access_token = request.access_token
        repo_ids = request.repo_ids
        
        # Get full repo list to find selected ones
        all_repos = await github_oauth.list_user_repos(access_token)
        selected_repos = [r for r in all_repos if r["id"] in repo_ids]
        
        if not selected_repos:
            raise HTTPException(status_code=404, detail="No matching repositories found")
        
        # TODO: Queue indexing jobs for each repo
        # This will be implemented in the indexing worker
        
        indexed_repos = []
        for repo in selected_repos:
            logger.info(f"Queuing indexing job for: {repo['full_name']}")
            
            # Store repo metadata in database (requires installation_id = NULL for now)
            async with db.acquire() as conn:
                # For OAuth-based repos, we don't have installation_id yet
                # Set to NULL, will be linked when GitHub App is installed
                await conn.execute(
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
            
            indexed_repos.append({
                "id": repo["id"],
                "full_name": repo["full_name"],
                "status": "queued"
            })
        
        return {
            "success": True,
            "message": f"Queued {len(indexed_repos)} repositories for indexing",
            "repos": indexed_repos
        }
    
    except Exception as e:
        logger.error(f"Failed to index repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos/{repo_id}/status")
async def get_repository_indexing_status(
    repo_id: int,
    authorization: str = Header(..., description="Bearer {access_token}"),
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
