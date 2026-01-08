"""Tests for GitHub API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
    from mcp_server.config.loader import GitHubConfig

    with patch.object(GitHubConfig, "token", "test-token"):
        config = GitHubConfig()
        yield config


@pytest.mark.asyncio
async def test_client_headers(mock_config):
    """Test client generates correct headers."""
    from mcp_server.tools.github.client import GitHubClient

    client = GitHubClient(config=mock_config)

    headers = client.headers
    assert headers["Accept"] == "application/vnd.github+json"
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["X-GitHub-Api-Version"] == "2022-11-28"


@pytest.mark.asyncio
async def test_client_get_request(mock_config):
    """Test client GET request."""
    from mcp_server.tools.github.client import GitHubClient

    client = GitHubClient(config=mock_config)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response
        mock_get_client.return_value = mock_http_client

        result = await client.get("/test")

        assert result == {"key": "value"}
        mock_http_client.request.assert_called_with("GET", "/test")


@pytest.mark.asyncio
async def test_client_post_request(mock_config):
    """Test client POST request."""
    from mcp_server.tools.github.client import GitHubClient

    client = GitHubClient(config=mock_config)

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 1}

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response
        mock_get_client.return_value = mock_http_client

        result = await client.post("/test", json={"data": "value"})

        assert result == {"id": 1}


@pytest.mark.asyncio
async def test_client_patch_request(mock_config):
    """Test client PATCH request."""
    from mcp_server.tools.github.client import GitHubClient

    client = GitHubClient(config=mock_config)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"updated": True}

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response
        mock_get_client.return_value = mock_http_client

        result = await client.patch("/test", json={"data": "value"})

        assert result == {"updated": True}


@pytest.mark.asyncio
async def test_client_put_request(mock_config):
    """Test client PUT request."""
    from mcp_server.tools.github.client import GitHubClient

    client = GitHubClient(config=mock_config)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"merged": True}

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response
        mock_get_client.return_value = mock_http_client

        result = await client.put("/test", json={"data": "value"})

        assert result == {"merged": True}


@pytest.mark.asyncio
async def test_client_delete_request(mock_config):
    """Test client DELETE request."""
    from mcp_server.tools.github.client import GitHubClient

    client = GitHubClient(config=mock_config)

    mock_response = MagicMock()
    mock_response.status_code = 204

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response
        mock_get_client.return_value = mock_http_client

        result = await client.delete("/test")

        assert result == {}


@pytest.mark.asyncio
async def test_client_404_error(mock_config):
    """Test client handles 404 errors."""
    from mcp_server.tools.github.client import GitHubClient
    from fastmcp.exceptions import ToolError

    client = GitHubClient(config=mock_config)

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response
        mock_get_client.return_value = mock_http_client

        with pytest.raises(ToolError, match="Not found"):
            await client.get("/nonexistent")


@pytest.mark.asyncio
async def test_client_401_error(mock_config):
    """Test client handles 401 unauthorized errors."""
    from mcp_server.tools.github.client import GitHubClient
    from fastmcp.exceptions import ToolError

    client = GitHubClient(config=mock_config)

    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response
        mock_get_client.return_value = mock_http_client

        with pytest.raises(ToolError, match="Unauthorized"):
            await client.get("/test")


@pytest.mark.asyncio
async def test_client_403_rate_limit(mock_config):
    """Test client handles 403 rate limit errors."""
    from mcp_server.tools.github.client import GitHubClient
    from fastmcp.exceptions import ToolError

    client = GitHubClient(config=mock_config)

    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.headers = {"X-RateLimit-Remaining": "0"}

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response
        mock_get_client.return_value = mock_http_client

        with pytest.raises(ToolError, match="Rate limited"):
            await client.get("/test")


@pytest.mark.asyncio
async def test_client_http_status_error(mock_config):
    """Test client handles HTTP status errors."""
    from mcp_server.tools.github.client import GitHubClient
    from fastmcp.exceptions import ToolError

    client = GitHubClient(config=mock_config)

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response
    )

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response
        mock_get_client.return_value = mock_http_client

        with pytest.raises(ToolError, match="GitHub API error"):
            await client.get("/test")


@pytest.mark.asyncio
async def test_client_request_error(mock_config):
    """Test client handles request errors."""
    from mcp_server.tools.github.client import GitHubClient
    from fastmcp.exceptions import ToolError

    client = GitHubClient(config=mock_config)

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = AsyncMock()
        mock_http_client.request.side_effect = httpx.RequestError("Connection failed")
        mock_get_client.return_value = mock_http_client

        with pytest.raises(ToolError, match="Request failed"):
            await client.get("/test")


@pytest.mark.asyncio
async def test_client_close(mock_config):
    """Test client close method."""
    from mcp_server.tools.github.client import GitHubClient

    client = GitHubClient(config=mock_config)
    mock_http_client = AsyncMock()
    client._client = mock_http_client

    await client.close()

    mock_http_client.aclose.assert_called_once()
    assert client._client is None


@pytest.mark.asyncio
async def test_client_close_when_not_initialized(mock_config):
    """Test client close when not initialized."""
    from mcp_server.tools.github.client import GitHubClient

    client = GitHubClient(config=mock_config)
    # Should not raise
    await client.close()


def test_get_client_singleton():
    """Test get_client returns singleton."""
    from mcp_server.tools.github.client import get_client, _client
    import mcp_server.tools.github.client as client_module

    # Reset singleton
    client_module._client = None

    with patch.dict("os.environ", {"GITHUB_TOKEN": "test"}):
        client1 = get_client()
        client2 = get_client()

        assert client1 is client2

    # Cleanup
    client_module._client = None
