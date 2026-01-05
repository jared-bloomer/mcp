# GitHub Integration Specification

## Overview

MCP tools for interacting with GitHub repositories via the REST API (v2022-11-28).

## Goals

- Provide AI assistants with GitHub repository management capabilities
- Support common workflows: repos, issues, PRs, branches, commits
- Secure credential management via environment variables
- No secrets in repository - config files reference env vars only

## Security Model

### Credential Storage

```
┌─────────────────────────────────────────────────────────────┐
│                     NOT in Git                              │
│  ~/.config/jlbloomer-mcp/secrets.env                        │
│  Contains: GITHUB_TOKEN=ghp_xxxx...                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     IN Git (safe)                           │
│  config/github.toml                                         │
│  Contains: token_env = "GITHUB_TOKEN"                       │
│  (references env var name, not the value)                   │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Files

**`config/github.toml`** (committed to git - safe):
```toml
[github]
# Environment variable name containing the token (NOT the token itself)
token_env = "GITHUB_TOKEN"

# API configuration
api_version = "2022-11-28"
base_url = "https://api.github.com"

# Default settings
default_owner = ""  # Optional: your GitHub username
per_page = 30       # Results per page (max 100)

# Rate limiting
respect_rate_limits = true
retry_on_rate_limit = true
max_retries = 3
```

**`config/github.example.toml`** (committed - template):
```toml
# Copy to github.toml and configure
# DO NOT put actual tokens in this file

[github]
token_env = "GITHUB_TOKEN"
api_version = "2022-11-28"
base_url = "https://api.github.com"
default_owner = ""
per_page = 30
respect_rate_limits = true
retry_on_rate_limit = true
max_retries = 3
```

**`.gitignore`** additions:
```gitignore
# Local configuration (may contain sensitive paths)
config/github.toml

# Never commit secrets
*.env
.env*
secrets.*
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | Personal Access Token (PAT) or Fine-grained token | Yes |
| `GITHUB_API_URL` | Override API base URL (for GitHub Enterprise) | No |

### Token Permissions (Fine-grained PAT)

Minimum required permissions:
- **Repository access**: All repositories (or select specific ones)
- **Permissions**:
  - Contents: Read and write
  - Issues: Read and write
  - Pull requests: Read and write
  - Metadata: Read-only (automatic)

## Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    "fastmcp>=2.0,<3",
    "httpx>=0.27",           # Async HTTP client
    "pydantic-settings>=2",  # Settings management
]
```

## Design Constraint: VS Code Tool Limit

VS Code has a limit of **128 tools** active at any time. To maximize available slots for future integrations (Docker, Proxmox, etc.), we consolidate GitHub operations into **4 action-based tools** instead of 17+ individual tools.

### Consolidation Pattern

Each tool handles multiple operations via an `action` parameter:

| Tool | Actions | Description |
|------|---------|-------------|
| `github_repo` | `list`, `get`, `create`, `delete`, `branches`, `contents` | Repository operations |
| `github_issue` | `list`, `get`, `create`, `update`, `close`, `comment` | Issue management |
| `github_pull` | `list`, `get`, `create`, `update`, `merge`, `files`, `reviews` | Pull request operations |
| `github_commit` | `list`, `get`, `compare`, `status` | Commit operations |

**Total: 4 tools** (vs 17+ with individual tools)

## Project Structure

```
src/mcp_server/
├── tools/
│   ├── __init__.py
│   ├── github/
│   │   ├── __init__.py      # Register all GitHub tools (4 tools)
│   │   ├── client.py        # GitHub API client
│   │   ├── repos.py         # github_repo tool
│   │   ├── issues.py        # github_issue tool
│   │   ├── pulls.py         # github_pull tool
│   │   └── commits.py       # github_commit tool
│   └── system.py
├── config/
│   ├── __init__.py
│   └── loader.py            # Generic config loader
config/
├── github.example.toml      # Template (committed)
└── github.toml              # Actual config (gitignored)
```

## Implementation

### Configuration Loader (`src/mcp_server/config/loader.py`)

```python
"""Configuration loader with environment variable resolution."""

import os
from pathlib import Path
from typing import Any

import tomllib
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class GitHubConfig(BaseSettings):
    """GitHub configuration with env var resolution."""

    token_env: str = "GITHUB_TOKEN"
    api_version: str = "2022-11-28"
    base_url: str = "https://api.github.com"
    default_owner: str = ""
    per_page: int = 30
    respect_rate_limits: bool = True
    retry_on_rate_limit: bool = True
    max_retries: int = 3

    @property
    def token(self) -> str:
        """Resolve token from environment variable."""
        token = os.environ.get(self.token_env)
        if not token:
            raise ValueError(
                f"GitHub token not found. Set {self.token_env} environment variable."
            )
        return token

    @classmethod
    def load(cls, config_path: Path | None = None) -> "GitHubConfig":
        """Load config from TOML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "github.toml"

        if not config_path.exists():
            # Fall back to defaults with env vars
            return cls()

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        return cls(**data.get("github", {}))
```

### GitHub API Client (`src/mcp_server/tools/github/client.py`)

```python
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
        **kwargs,
    ) -> dict[str, Any] | list[Any]:
        """Make an API request with error handling."""
        client = await self._get_client()

        try:
            response = await client.request(method, endpoint, **kwargs)

            # Handle rate limiting
            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "?")
                raise ToolError(f"Rate limited. Remaining: {remaining}")

            if response.status_code == 404:
                raise ToolError(f"Not found: {endpoint}")

            response.raise_for_status()

            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.HTTPStatusError as e:
            raise ToolError(f"GitHub API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise ToolError(f"Request failed: {e}")

    async def get(self, endpoint: str, **kwargs) -> dict[str, Any] | list[Any]:
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> dict[str, Any]:
        return await self.request("POST", endpoint, **kwargs)

    async def patch(self, endpoint: str, **kwargs) -> dict[str, Any]:
        return await self.request("PATCH", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> dict[str, Any]:
        return await self.request("DELETE", endpoint, **kwargs)

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
_client: GitHubClient | None = None


def get_client() -> GitHubClient:
    """Get or create GitHub client singleton."""
    global _client
    if _client is None:
        _client = GitHubClient()
    return _client
```

## Tool Definitions (Consolidated)

### `github_repo` - Repository Operations

```python
github_repo(
    action: Literal["list", "get", "create", "delete", "branches", "contents"],
    # Common params
    owner: str | None = None,      # Repository owner (uses authenticated user if None for list)
    repo: str | None = None,       # Repository name (required for most actions)
    # Action-specific params
    name: str | None = None,       # For create: new repo name
    description: str | None = None,# For create: repo description
    private: bool = False,         # For create: private repo
    path: str | None = None,       # For contents: file/directory path
    ref: str | None = None,        # For contents/branches: branch or commit ref
)
```

| Action | Required Params | Optional Params | Returns |
|--------|-----------------|-----------------|---------|
| `list` | - | `owner`, `type`, `sort` | List of repos |
| `get` | `owner`, `repo` | - | Repo details |
| `create` | `name` | `description`, `private` | Created repo |
| `delete` | `owner`, `repo` | - | Success status |
| `branches` | `owner`, `repo` | - | List of branches |
| `contents` | `owner`, `repo`, `path` | `ref` | File/dir contents |

### `github_issue` - Issue Management

```python
github_issue(
    action: Literal["list", "get", "create", "update", "close", "comment"],
    owner: str,
    repo: str,
    # Action-specific params
    issue_number: int | None = None,  # Required for get/update/close/comment
    title: str | None = None,          # For create/update
    body: str | None = None,           # For create/update/comment
    labels: list[str] | None = None,   # For create/update
    assignees: list[str] | None = None,# For create/update
    state: str | None = None,          # For list: open/closed/all
)
```

| Action | Required Params | Optional Params | Returns |
|--------|-----------------|-----------------|---------|
| `list` | `owner`, `repo` | `state`, `labels` | List of issues |
| `get` | `owner`, `repo`, `issue_number` | - | Issue details |
| `create` | `owner`, `repo`, `title` | `body`, `labels`, `assignees` | Created issue |
| `update` | `owner`, `repo`, `issue_number` | `title`, `body`, `labels`, `state` | Updated issue |
| `close` | `owner`, `repo`, `issue_number` | - | Closed issue |
| `comment` | `owner`, `repo`, `issue_number`, `body` | - | Created comment |

### `github_pull` - Pull Request Operations

```python
github_pull(
    action: Literal["list", "get", "create", "update", "merge", "files", "reviews"],
    owner: str,
    repo: str,
    # Action-specific params
    pull_number: int | None = None,   # Required for get/update/merge/files/reviews
    title: str | None = None,          # For create/update
    body: str | None = None,           # For create/update
    head: str | None = None,           # For create: source branch
    base: str | None = None,           # For create/list: target branch
    merge_method: str | None = None,   # For merge: merge/squash/rebase
    state: str | None = None,          # For list: open/closed/all
)
```

| Action | Required Params | Optional Params | Returns |
|--------|-----------------|-----------------|---------|
| `list` | `owner`, `repo` | `state`, `base`, `head` | List of PRs |
| `get` | `owner`, `repo`, `pull_number` | - | PR details |
| `create` | `owner`, `repo`, `title`, `head`, `base` | `body` | Created PR |
| `update` | `owner`, `repo`, `pull_number` | `title`, `body`, `state` | Updated PR |
| `merge` | `owner`, `repo`, `pull_number` | `merge_method` | Merge result |
| `files` | `owner`, `repo`, `pull_number` | - | Changed files |
| `reviews` | `owner`, `repo`, `pull_number` | - | PR reviews |

### `github_commit` - Commit Operations

```python
github_commit(
    action: Literal["list", "get", "compare", "status"],
    owner: str,
    repo: str,
    # Action-specific params
    ref: str | None = None,           # Commit SHA or branch name
    base: str | None = None,          # For compare: base ref
    head: str | None = None,          # For compare: head ref
    path: str | None = None,          # For list: filter by file path
    per_page: int = 30,               # Results per page
)
```

| Action | Required Params | Optional Params | Returns |
|--------|-----------------|-----------------|---------|
| `list` | `owner`, `repo` | `ref`, `path`, `per_page` | List of commits |
| `get` | `owner`, `repo`, `ref` | - | Commit details |
| `compare` | `owner`, `repo`, `base`, `head` | - | Comparison diff |
| `status` | `owner`, `repo`, `ref` | - | CI/CD status |

## Example Tool Implementation

```python
"""Repository tool for GitHub - consolidated actions."""

from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from mcp_server.tools.github.client import get_client


def register(mcp: FastMCP) -> None:
    """Register the github_repo tool."""

    @mcp.tool(
        name="github_repo",
        description="Manage GitHub repositories. Actions: list, get, create, delete, branches, contents",
        tags={"github", "repos"},
    )
    async def github_repo(
        action: Annotated[
            Literal["list", "get", "create", "delete", "branches", "contents"],
            Field(description="Action to perform"),
        ],
        owner: Annotated[
            str | None,
            Field(description="Repository owner. Uses authenticated user for 'list' if not provided"),
        ] = None,
        repo: Annotated[
            str | None,
            Field(description="Repository name. Required for get/delete/branches/contents"),
        ] = None,
        # Create params
        name: Annotated[
            str | None,
            Field(description="New repository name (for 'create' action)"),
        ] = None,
        description: Annotated[
            str | None,
            Field(description="Repository description (for 'create' action)"),
        ] = None,
        private: Annotated[
            bool,
            Field(description="Make repository private (for 'create' action)"),
        ] = False,
        # Contents params
        path: Annotated[
            str | None,
            Field(description="File or directory path (for 'contents' action)"),
        ] = None,
        ref: Annotated[
            str | None,
            Field(description="Branch or commit ref (for 'contents' action)"),
        ] = None,
    ) -> dict | list:
        """Execute repository operations."""
        client = get_client()

        match action:
            case "list":
                if owner:
                    endpoint = f"/users/{owner}/repos"
                else:
                    endpoint = "/user/repos"
                repos = await client.get(endpoint, params={"per_page": client.config.per_page})
                return [
                    {
                        "name": r["name"],
                        "full_name": r["full_name"],
                        "description": r["description"],
                        "private": r["private"],
                        "url": r["html_url"],
                        "default_branch": r["default_branch"],
                    }
                    for r in repos
                ]

            case "get":
                if not owner or not repo:
                    raise ToolError("'owner' and 'repo' are required for 'get' action")
                return await client.get(f"/repos/{owner}/{repo}")

            case "create":
                if not name:
                    raise ToolError("'name' is required for 'create' action")
                return await client.post(
                    "/user/repos",
                    json={"name": name, "description": description or "", "private": private},
                )

            case "delete":
                if not owner or not repo:
                    raise ToolError("'owner' and 'repo' are required for 'delete' action")
                await client.delete(f"/repos/{owner}/{repo}")
                return {"status": "deleted", "repo": f"{owner}/{repo}"}

            case "branches":
                if not owner or not repo:
                    raise ToolError("'owner' and 'repo' are required for 'branches' action")
                return await client.get(f"/repos/{owner}/{repo}/branches")

            case "contents":
                if not owner or not repo or not path:
                    raise ToolError("'owner', 'repo', and 'path' are required for 'contents' action")
                params = {"ref": ref} if ref else {}
                return await client.get(f"/repos/{owner}/{repo}/contents/{path}", params=params)

            case _:
                raise ToolError(f"Unknown action: {action}")
```

## Testing Strategy

### Unit Tests

```python
"""Tests for GitHub tools."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_github_client():
    """Mock GitHub client for testing."""
    with patch("mcp_server.tools.github.client.get_client") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.mark.asyncio
async def test_list_repos(mcp_server, mock_github_client):
    """Test listing repositories."""
    mock_github_client.get.return_value = [
        {"name": "test-repo", "full_name": "user/test-repo", ...}
    ]

    # Call tool and verify
```

### Integration Tests

- Require `GITHUB_TOKEN` env var
- Use a dedicated test repository
- Mark with `@pytest.mark.integration`
- Skip in CI unless token available

## Setup Instructions

1. **Create GitHub Token**:
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Create token with required permissions (see Token Permissions above)

2. **Set Environment Variable**:
   ```bash
   # Add to ~/.zshrc or ~/.bashrc
   export GITHUB_TOKEN="ghp_your_token_here"

   # Or use a secrets file (not in git)
   echo 'GITHUB_TOKEN=ghp_your_token_here' >> ~/.config/jlbloomer-mcp/secrets.env
   ```

3. **Create Config File**:
   ```bash
   cp config/github.example.toml config/github.toml
   # Edit config/github.toml if needed (optional - defaults work)
   ```

4. **Verify Setup**:
   ```bash
   uv run python -c "from mcp_server.tools.github.client import get_client; print('OK')"
   ```

## Error Handling

| Error | Handling |
|-------|----------|
| Missing token | Clear error message pointing to setup instructions |
| Rate limited | Report remaining quota, suggest waiting |
| 404 Not found | Indicate resource doesn't exist or no access |
| 401 Unauthorized | Token invalid or expired |
| Network error | Retry with backoff, then fail gracefully |

## Future Enhancements

- [ ] GitHub Actions workflow management
- [ ] Gist support
- [ ] Release management
- [ ] Webhook configuration
- [ ] Code search
- [ ] GitHub Enterprise support (custom base_url)
- [ ] Caching for frequently accessed data

## References

- [GitHub REST API Docs](https://docs.github.com/en/rest?apiVersion=2022-11-28)
- [Fine-grained PAT Docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
