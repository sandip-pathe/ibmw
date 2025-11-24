"""
GitHub OAuth integration for user repo access.
"""
import httpx
from loguru import logger
from fastapi import HTTPException, status

from app.config import get_settings

settings = get_settings()


class GitHubOAuth:
    """Handle GitHub OAuth flow for user authentication."""
    
    def __init__(self):
        self.client_id = settings.github_oauth_client_id
        self.client_secret = settings.github_oauth_client_secret
        self.authorize_url = "https://github.com/login/oauth/authorize"
        self.token_url = "https://github.com/login/oauth/access_token"
        self.api_base = "https://api.github.com"
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """
        Generate GitHub OAuth authorization URL.
        
        Args:
            redirect_uri: Callback URL after authorization
            state: Random state for CSRF protection
            
        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "repo read:user user:email",
            "state": state,
        }
        
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorize_url}?{query}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from GitHub
            redirect_uri: Callback URL used in authorization
            
        Returns:
            Token response with access_token
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to exchange code: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> dict:
        """
        Get user information from GitHub.
        
        Args:
            access_token: User's GitHub access token
            
        Returns:
            User information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get user info: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token"
                )
            
            return response.json()
    
    async def list_user_repos(self, access_token: str) -> list[dict]:
        """
        List all repositories accessible by the user.
        
        Args:
            access_token: User's GitHub access token
            
        Returns:
            List of repositories
        """
        repos = []
        page = 1
        per_page = 100
        
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"{self.api_base}/user/repos",
                    params={
                        "visibility": "all",
                        "affiliation": "owner,collaborator,organization_member",
                        "sort": "updated",
                        "per_page": per_page,
                        "page": page,
                    },
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to list repos: {response.text}")
                    break
                
                page_repos = response.json()
                if not page_repos:
                    break
                
                repos.extend(page_repos)
                
                if len(page_repos) < per_page:
                    break
                
                page += 1
        
        logger.info(f"Found {len(repos)} repositories for user")
        return repos
    
    async def get_repo_content(
        self, access_token: str, owner: str, repo: str, path: str = ""
    ) -> list[dict]:
        """
        Get repository content at specified path.
        
        Args:
            access_token: User's GitHub access token
            owner: Repository owner
            repo: Repository name
            path: Path within repository
            
        Returns:
            List of files/directories
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/repos/{owner}/{repo}/contents/{path}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get repo content: {response.text}")
                return []
            
            return response.json()


# Global OAuth instance
github_oauth = GitHubOAuth()
