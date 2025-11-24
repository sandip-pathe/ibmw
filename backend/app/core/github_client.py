"""
GitHub API client for repository operations.
"""
from datetime import datetime
from typing import Any, Optional

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import GitHubAuthError
from app.core.github_auth import github_auth

settings = get_settings()


class GitHubClient:
    """Async GitHub API client with authentication."""

    def __init__(self):
        self.base_url = settings.github_api_url
        self.timeout = httpx.Timeout(30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        token: str,
        json_data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make authenticated GitHub API request with retry.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            token: Authentication token (JWT or installation token)
            json_data: JSON payload
            params: Query parameters
            
        Returns:
            Response JSON
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method, url, headers=headers, json=json_data, params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
                raise GitHubAuthError(f"GitHub API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"GitHub API request failed: {e}")
                raise

    async def get_installation_token(self, installation_id: int) -> str:
        """
        Exchange JWT for installation access token.
        
        Args:
            installation_id: GitHub App installation ID
            
        Returns:
            Installation access token
        """
        # Check cache first
        cached_token = github_auth.get_installation_token(installation_id)
        if cached_token:
            return cached_token

        # Create JWT
        jwt_token = github_auth.create_jwt()

        # Request installation token
        endpoint = f"/app/installations/{installation_id}/access_tokens"
        response = await self._request("POST", endpoint, jwt_token)

        token = response["token"]
        expires_at = datetime.fromisoformat(response["expires_at"].replace("Z", "+00:00"))

        # Cache token
        github_auth.cache_installation_token(installation_id, token, expires_at)

        logger.info(f"Obtained installation token for {installation_id}")
        return token

    async def get_repository(self, installation_id: int, owner: str, repo: str) -> dict[str, Any]:
        """
        Get repository details.
        
        Args:
            installation_id: GitHub App installation ID
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository data
        """
        token = await self.get_installation_token(installation_id)
        endpoint = f"/repos/{owner}/{repo}"
        return await self._request("GET", endpoint, token)

    async def get_repository_tree(
        self, installation_id: int, owner: str, repo: str, sha: str = "HEAD", recursive: bool = True
    ) -> dict[str, Any]:
        """
        Get repository file tree.
        
        Args:
            installation_id: GitHub App installation ID
            owner: Repository owner
            repo: Repository name
            sha: Git SHA or branch name
            recursive: Fetch recursive tree
            
        Returns:
            Tree data with files
        """
        token = await self.get_installation_token(installation_id)
        endpoint = f"/repos/{owner}/{repo}/git/trees/{sha}"
        params = {"recursive": "1" if recursive else "0"}
        return await self._request("GET", endpoint, token, params=params)

    async def get_file_content(
        self, installation_id: int, owner: str, repo: str, path: str, ref: str = "HEAD"
    ) -> str:
        """
        Get file content from repository.
        
        Args:
            installation_id: GitHub App installation ID
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git ref (branch, tag, SHA)
            
        Returns:
            File content as string
        """
        token = await self.get_installation_token(installation_id)
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref}
        response = await self._request("GET", endpoint, token, params=params)

        # Decode base64 content
        import base64

        content = base64.b64decode(response["content"]).decode("utf-8")
        return content

    async def create_check_run(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        name: str,
        head_sha: str,
        status: str = "completed",
        conclusion: Optional[str] = None,
        output: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create GitHub Check Run (requires checks:write permission).
        
        Args:
            installation_id: GitHub App installation ID
            owner: Repository owner
            repo: Repository name
            name: Check run name
            head_sha: Commit SHA
            status: 'queued', 'in_progress', 'completed'
            conclusion: 'success', 'failure', 'neutral', 'cancelled', etc.
            output: Check run output (title, summary, annotations)
            
        Returns:
            Check run data
        """
        if not settings.enable_github_checks:
            logger.warning("GitHub Checks disabled - skipping check run creation")
            return {}

        token = await self.get_installation_token(installation_id)
        endpoint = f"/repos/{owner}/{repo}/check-runs"

        payload: dict[str, Any] = {
            "name": name,
            "head_sha": head_sha,
            "status": status,
        }

        if conclusion:
            payload["conclusion"] = conclusion

        if output:
            payload["output"] = output

        return await self._request("POST", endpoint, token, json_data=payload)


# Global client instance
github_client = GitHubClient()
