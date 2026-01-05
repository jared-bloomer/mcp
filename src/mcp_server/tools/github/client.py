"""Async GitHub API client."""

from typing import Any

import httpx
from fastmcp.exceptions import ToolError

from mcp_server.config.loader import GitHubConfig


class GitHubClient:
    """Async client for GitHub REST API."""

    def __init__(self, config: GitHubConfig | None = None):
        self.config = config or GitHubConfig.load()
        self._client: httpx.AsyncClient | None = None

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.config.token}",
            "X-GitHub-Api-Version": self.config.api_version,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=self.headers,
                timeout=30.0,
            )
        return self._client

    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any] | list[Any]:
        """Make an API request with error handling."""
        client = await self._get_client()

        try:
            response = await client.request(method, endpoint, **kwargs)

            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "?")
                raise ToolError(f"Rate limited. Remaining: {remaining}")

            if response.status_code == 404:
                raise ToolError(f"Not found: {endpoint}")

            if response.status_code == 401:
                raise ToolError("Unauthorized. Check your GitHub token.")

            response.raise_for_status()

            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.HTTPStatusError as e:
            raise ToolError(f"GitHub API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise ToolError(f"Request failed: {e}")

    async def get(self, endpoint: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        return await self.request("POST", endpoint, **kwargs)

    async def patch(self, endpoint: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        return await self.request("PATCH", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        return await self.request("PUT", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        return await self.request("DELETE", endpoint, **kwargs)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


_client: GitHubClient | None = None


def get_client() -> GitHubClient:
    """Get or create GitHub client singleton."""
    global _client
    if _client is None:
        _client = GitHubClient()
    return _client
