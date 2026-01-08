"""Tests for GitHub tools."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_github_client():
    """Mock GitHub client for testing."""
    with patch("mcp_server.tools.github.client._client", None):
        with patch("mcp_server.tools.github.client.GitHubClient") as mock_cls:
            client = AsyncMock()
            client.config = MagicMock()
            client.config.per_page = 30
            mock_cls.return_value = client
            yield client


# Repository tool tests


@pytest.mark.asyncio
async def test_github_repo_tool_exists(mcp_server):
    """Test that github_repo tool is registered."""
    tools = await mcp_server.get_tools()
    assert "github_repo" in tools
    assert "github" in tools["github_repo"].tags


@pytest.mark.asyncio
async def test_list_repos(mock_github_client):
    """Test listing repositories."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = [
        {
            "name": "test-repo",
            "full_name": "user/test-repo",
            "description": "A test repo",
            "private": False,
            "html_url": "https://github.com/user/test-repo",
            "default_branch": "main",
        }
    ]

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_repo"].fn(action="list")

    assert len(result) == 1
    assert result[0]["name"] == "test-repo"
    assert result[0]["full_name"] == "user/test-repo"


@pytest.mark.asyncio
async def test_get_repo(mock_github_client):
    """Test getting a specific repository."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = {
        "name": "test-repo",
        "full_name": "owner/test-repo",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_repo"].fn(action="get", owner="owner", repo="test-repo")

    assert result["name"] == "test-repo"
    mock_github_client.get.assert_called_with("/repos/owner/test-repo")


@pytest.mark.asyncio
async def test_get_repo_missing_params():
    """Test get action requires owner and repo."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'owner' and 'repo' are required"):
        await tools["github_repo"].fn(action="get")


# Issue tool tests


@pytest.mark.asyncio
async def test_github_issue_tool_exists(mcp_server):
    """Test that github_issue tool is registered."""
    tools = await mcp_server.get_tools()
    assert "github_issue" in tools
    assert "github" in tools["github_issue"].tags


@pytest.mark.asyncio
async def test_list_issues(mock_github_client):
    """Test listing issues."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = [
        {
            "number": 1,
            "title": "Test issue",
            "state": "open",
            "user": {"login": "testuser"},
            "labels": [{"name": "bug"}],
            "html_url": "https://github.com/owner/repo/issues/1",
            "created_at": "2024-01-01T00:00:00Z",
        }
    ]

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_issue"].fn(action="list", owner="owner", repo="repo")

    assert len(result) == 1
    assert result[0]["number"] == 1
    assert result[0]["title"] == "Test issue"
    assert result[0]["labels"] == ["bug"]


@pytest.mark.asyncio
async def test_create_issue(mock_github_client):
    """Test creating an issue."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP

    mock_github_client.post.return_value = {
        "number": 2,
        "title": "New issue",
        "state": "open",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_issue"].fn(
        action="create",
        owner="owner",
        repo="repo",
        title="New issue",
        body="Issue body",
    )

    assert result["number"] == 2
    mock_github_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_create_issue_missing_title():
    """Test create action requires title."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'title' is required"):
        await tools["github_issue"].fn(action="create", owner="owner", repo="repo")


# Pull request tool tests


@pytest.mark.asyncio
async def test_github_pull_tool_exists(mcp_server):
    """Test that github_pull tool is registered."""
    tools = await mcp_server.get_tools()
    assert "github_pull" in tools
    assert "github" in tools["github_pull"].tags


@pytest.mark.asyncio
async def test_list_pulls(mock_github_client):
    """Test listing pull requests."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = [
        {
            "number": 1,
            "title": "Test PR",
            "state": "open",
            "user": {"login": "testuser"},
            "head": {"ref": "feature"},
            "base": {"ref": "main"},
            "html_url": "https://github.com/owner/repo/pull/1",
            "created_at": "2024-01-01T00:00:00Z",
        }
    ]

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_pull"].fn(action="list", owner="owner", repo="repo")

    assert len(result) == 1
    assert result[0]["number"] == 1
    assert result[0]["head"] == "feature"
    assert result[0]["base"] == "main"


@pytest.mark.asyncio
async def test_create_pull(mock_github_client):
    """Test creating a pull request."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP

    mock_github_client.post.return_value = {
        "number": 2,
        "title": "New PR",
        "state": "open",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_pull"].fn(
        action="create",
        owner="owner",
        repo="repo",
        title="New PR",
        head="feature",
        base="main",
    )

    assert result["number"] == 2
    mock_github_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_merge_pull(mock_github_client):
    """Test merging a pull request."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP

    mock_github_client.put.return_value = {"merged": True}

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_pull"].fn(
        action="merge",
        owner="owner",
        repo="repo",
        pull_number=1,
        merge_method="squash",
    )

    assert result["merged"] is True


# Commit tool tests


@pytest.mark.asyncio
async def test_github_commit_tool_exists(mcp_server):
    """Test that github_commit tool is registered."""
    tools = await mcp_server.get_tools()
    assert "github_commit" in tools
    assert "github" in tools["github_commit"].tags


@pytest.mark.asyncio
async def test_list_commits(mock_github_client):
    """Test listing commits."""
    from mcp_server.tools.github.commits import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = [
        {
            "sha": "abc1234567890",
            "commit": {
                "message": "Test commit\n\nWith body",
                "author": {"name": "Test User", "date": "2024-01-01T00:00:00Z"},
            },
            "html_url": "https://github.com/owner/repo/commit/abc1234",
        }
    ]

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_commit"].fn(action="list", owner="owner", repo="repo")

    assert len(result) == 1
    assert result[0]["sha"] == "abc1234"
    assert result[0]["message"] == "Test commit"
    assert result[0]["author"] == "Test User"


@pytest.mark.asyncio
async def test_compare_commits(mock_github_client):
    """Test comparing commits."""
    from mcp_server.tools.github.commits import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = {
        "status": "ahead",
        "ahead_by": 3,
        "behind_by": 0,
        "total_commits": 3,
        "commits": [
            {
                "sha": "abc1234567890",
                "commit": {
                    "message": "Commit 1",
                    "author": {"name": "User"},
                },
            }
        ],
        "files": [{"filename": "file1.py"}, {"filename": "file2.py"}],
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_commit"].fn(
        action="compare",
        owner="owner",
        repo="repo",
        base="main",
        head="feature",
    )

    assert result["status"] == "ahead"
    assert result["ahead_by"] == 3
    assert result["files_changed"] == 2


@pytest.mark.asyncio
async def test_compare_commits_missing_params():
    """Test compare action requires base and head."""
    from mcp_server.tools.github.commits import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'base' and 'head' are required"):
        await tools["github_commit"].fn(action="compare", owner="owner", repo="repo")


# Additional repository action tests


@pytest.mark.asyncio
async def test_list_repos_with_owner(mock_github_client):
    """Test listing repositories for a specific owner."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = [
        {
            "name": "repo1",
            "full_name": "other/repo1",
            "description": "Desc",
            "private": False,
            "html_url": "https://github.com/other/repo1",
            "default_branch": "main",
        }
    ]

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    await tools["github_repo"].fn(action="list", owner="other")

    mock_github_client.get.assert_called_with(
        "/users/other/repos", params={"per_page": 30}
    )


@pytest.mark.asyncio
async def test_create_repo(mock_github_client):
    """Test creating a repository."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP

    mock_github_client.post.return_value = {
        "name": "new-repo",
        "full_name": "user/new-repo",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_repo"].fn(
        action="create",
        name="new-repo",
        description="A new repo",
        private=True,
    )

    assert result["name"] == "new-repo"
    mock_github_client.post.assert_called_with(
        "/user/repos",
        json={"name": "new-repo", "description": "A new repo", "private": True},
    )


@pytest.mark.asyncio
async def test_create_repo_missing_name():
    """Test create action requires name."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'name' is required"):
        await tools["github_repo"].fn(action="create")


@pytest.mark.asyncio
async def test_delete_repo(mock_github_client):
    """Test deleting a repository."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP

    mock_github_client.delete.return_value = {}

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_repo"].fn(action="delete", owner="owner", repo="repo")

    assert result["status"] == "deleted"
    assert result["repo"] == "owner/repo"
    mock_github_client.delete.assert_called_with("/repos/owner/repo")


@pytest.mark.asyncio
async def test_delete_repo_missing_params():
    """Test delete action requires owner and repo."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'owner' and 'repo' are required"):
        await tools["github_repo"].fn(action="delete")


@pytest.mark.asyncio
async def test_list_branches(mock_github_client):
    """Test listing branches."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = [
        {"name": "main"},
        {"name": "develop"},
    ]

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_repo"].fn(action="branches", owner="owner", repo="repo")

    assert len(result) == 2
    mock_github_client.get.assert_called_with("/repos/owner/repo/branches")


@pytest.mark.asyncio
async def test_branches_missing_params():
    """Test branches action requires owner and repo."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'owner' and 'repo' are required"):
        await tools["github_repo"].fn(action="branches")


@pytest.mark.asyncio
async def test_get_contents(mock_github_client):
    """Test getting file contents."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = {
        "name": "README.md",
        "content": "SGVsbG8gV29ybGQ=",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_repo"].fn(
        action="contents", owner="owner", repo="repo", path="README.md", ref="main"
    )

    assert result["name"] == "README.md"
    mock_github_client.get.assert_called_with(
        "/repos/owner/repo/contents/README.md", params={"ref": "main"}
    )


@pytest.mark.asyncio
async def test_contents_missing_params():
    """Test contents action requires owner, repo, and path."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'owner', 'repo', and 'path' are required"):
        await tools["github_repo"].fn(action="contents", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_unknown_repo_action():
    """Test unknown action raises error."""
    from mcp_server.tools.github.repos import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="Unknown action"):
        await tools["github_repo"].fn(action="invalid", owner="owner", repo="repo")


# Additional issue action tests


@pytest.mark.asyncio
async def test_get_issue(mock_github_client):
    """Test getting a specific issue."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = {
        "number": 1,
        "title": "Test issue",
        "state": "open",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_issue"].fn(
        action="get", owner="owner", repo="repo", issue_number=1
    )

    assert result["number"] == 1
    mock_github_client.get.assert_called_with("/repos/owner/repo/issues/1")


@pytest.mark.asyncio
async def test_get_issue_missing_number():
    """Test get action requires issue_number."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'issue_number' is required"):
        await tools["github_issue"].fn(action="get", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_update_issue(mock_github_client):
    """Test updating an issue."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP

    mock_github_client.patch.return_value = {
        "number": 1,
        "title": "Updated title",
        "state": "open",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_issue"].fn(
        action="update",
        owner="owner",
        repo="repo",
        issue_number=1,
        title="Updated title",
        body="Updated body",
        labels=["bug"],
        state="open",
    )

    assert result["title"] == "Updated title"
    mock_github_client.patch.assert_called_once()


@pytest.mark.asyncio
async def test_update_issue_missing_number():
    """Test update action requires issue_number."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'issue_number' is required"):
        await tools["github_issue"].fn(action="update", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_close_issue(mock_github_client):
    """Test closing an issue."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP

    mock_github_client.patch.return_value = {
        "number": 1,
        "state": "closed",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_issue"].fn(
        action="close", owner="owner", repo="repo", issue_number=1
    )

    assert result["state"] == "closed"
    mock_github_client.patch.assert_called_with(
        "/repos/owner/repo/issues/1", json={"state": "closed"}
    )


@pytest.mark.asyncio
async def test_close_issue_missing_number():
    """Test close action requires issue_number."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'issue_number' is required"):
        await tools["github_issue"].fn(action="close", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_comment_on_issue(mock_github_client):
    """Test adding a comment to an issue."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP

    mock_github_client.post.return_value = {
        "id": 123,
        "body": "This is a comment",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_issue"].fn(
        action="comment",
        owner="owner",
        repo="repo",
        issue_number=1,
        body="This is a comment",
    )

    assert result["body"] == "This is a comment"
    mock_github_client.post.assert_called_with(
        "/repos/owner/repo/issues/1/comments", json={"body": "This is a comment"}
    )


@pytest.mark.asyncio
async def test_comment_missing_number():
    """Test comment action requires issue_number."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'issue_number' is required"):
        await tools["github_issue"].fn(
            action="comment", owner="owner", repo="repo", body="comment"
        )


@pytest.mark.asyncio
async def test_comment_missing_body():
    """Test comment action requires body."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'body' is required"):
        await tools["github_issue"].fn(
            action="comment", owner="owner", repo="repo", issue_number=1
        )


@pytest.mark.asyncio
async def test_list_issues_with_state(mock_github_client):
    """Test listing issues with state filter."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = []

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    await tools["github_issue"].fn(
        action="list", owner="owner", repo="repo", state="closed"
    )

    mock_github_client.get.assert_called_with(
        "/repos/owner/repo/issues", params={"per_page": 30, "state": "closed"}
    )


@pytest.mark.asyncio
async def test_create_issue_with_labels_assignees(mock_github_client):
    """Test creating issue with labels and assignees."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP

    mock_github_client.post.return_value = {"number": 1}

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    await tools["github_issue"].fn(
        action="create",
        owner="owner",
        repo="repo",
        title="New issue",
        labels=["bug", "urgent"],
        assignees=["user1"],
    )

    call_args = mock_github_client.post.call_args
    assert call_args[1]["json"]["labels"] == ["bug", "urgent"]
    assert call_args[1]["json"]["assignees"] == ["user1"]


@pytest.mark.asyncio
async def test_unknown_issue_action():
    """Test unknown action raises error."""
    from mcp_server.tools.github.issues import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="Unknown action"):
        await tools["github_issue"].fn(action="invalid", owner="owner", repo="repo")


# Additional pull request action tests


@pytest.mark.asyncio
async def test_get_pull(mock_github_client):
    """Test getting a specific pull request."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = {
        "number": 1,
        "title": "Test PR",
        "state": "open",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_pull"].fn(
        action="get", owner="owner", repo="repo", pull_number=1
    )

    assert result["number"] == 1
    mock_github_client.get.assert_called_with("/repos/owner/repo/pulls/1")


@pytest.mark.asyncio
async def test_get_pull_missing_number():
    """Test get action requires pull_number."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'pull_number' is required"):
        await tools["github_pull"].fn(action="get", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_create_pull_missing_params():
    """Test create action requires title, head, and base."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'title', 'head', and 'base' are required"):
        await tools["github_pull"].fn(action="create", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_update_pull(mock_github_client):
    """Test updating a pull request."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP

    mock_github_client.patch.return_value = {
        "number": 1,
        "title": "Updated PR",
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_pull"].fn(
        action="update",
        owner="owner",
        repo="repo",
        pull_number=1,
        title="Updated PR",
        body="Updated body",
        state="closed",
    )

    assert result["title"] == "Updated PR"
    mock_github_client.patch.assert_called_once()


@pytest.mark.asyncio
async def test_update_pull_missing_number():
    """Test update action requires pull_number."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'pull_number' is required"):
        await tools["github_pull"].fn(action="update", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_merge_pull_missing_number():
    """Test merge action requires pull_number."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'pull_number' is required"):
        await tools["github_pull"].fn(action="merge", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_get_pull_files(mock_github_client):
    """Test getting pull request files."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = [
        {"filename": "file1.py", "status": "modified"},
        {"filename": "file2.py", "status": "added"},
    ]

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_pull"].fn(
        action="files", owner="owner", repo="repo", pull_number=1
    )

    assert len(result) == 2
    mock_github_client.get.assert_called_with("/repos/owner/repo/pulls/1/files")


@pytest.mark.asyncio
async def test_get_pull_files_missing_number():
    """Test files action requires pull_number."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'pull_number' is required"):
        await tools["github_pull"].fn(action="files", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_get_pull_reviews(mock_github_client):
    """Test getting pull request reviews."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = [
        {"id": 1, "state": "APPROVED", "user": {"login": "reviewer"}},
    ]

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_pull"].fn(
        action="reviews", owner="owner", repo="repo", pull_number=1
    )

    assert len(result) == 1
    assert result[0]["state"] == "APPROVED"
    mock_github_client.get.assert_called_with("/repos/owner/repo/pulls/1/reviews")


@pytest.mark.asyncio
async def test_get_pull_reviews_missing_number():
    """Test reviews action requires pull_number."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'pull_number' is required"):
        await tools["github_pull"].fn(action="reviews", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_list_pulls_with_filters(mock_github_client):
    """Test listing pulls with state and base filters."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = []

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    await tools["github_pull"].fn(
        action="list", owner="owner", repo="repo", state="closed", base="main"
    )

    mock_github_client.get.assert_called_with(
        "/repos/owner/repo/pulls",
        params={"per_page": 30, "state": "closed", "base": "main"},
    )


@pytest.mark.asyncio
async def test_unknown_pull_action():
    """Test unknown action raises error."""
    from mcp_server.tools.github.pulls import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="Unknown action"):
        await tools["github_pull"].fn(action="invalid", owner="owner", repo="repo")


# Additional commit action tests


@pytest.mark.asyncio
async def test_get_commit(mock_github_client):
    """Test getting a specific commit."""
    from mcp_server.tools.github.commits import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = {
        "sha": "abc1234567890",
        "commit": {"message": "Test commit"},
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_commit"].fn(
        action="get", owner="owner", repo="repo", ref="abc1234"
    )

    assert result["sha"] == "abc1234567890"
    mock_github_client.get.assert_called_with("/repos/owner/repo/commits/abc1234")


@pytest.mark.asyncio
async def test_get_commit_missing_ref():
    """Test get action requires ref."""
    from mcp_server.tools.github.commits import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'ref' is required"):
        await tools["github_commit"].fn(action="get", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_get_commit_status(mock_github_client):
    """Test getting commit status."""
    from mcp_server.tools.github.commits import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = {
        "state": "success",
        "statuses": [{"context": "ci", "state": "success"}],
    }

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    result = await tools["github_commit"].fn(
        action="status", owner="owner", repo="repo", ref="abc1234"
    )

    assert result["state"] == "success"
    mock_github_client.get.assert_called_with("/repos/owner/repo/commits/abc1234/status")


@pytest.mark.asyncio
async def test_get_commit_status_missing_ref():
    """Test status action requires ref."""
    from mcp_server.tools.github.commits import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="'ref' is required"):
        await tools["github_commit"].fn(action="status", owner="owner", repo="repo")


@pytest.mark.asyncio
async def test_list_commits_with_filters(mock_github_client):
    """Test listing commits with ref and path filters."""
    from mcp_server.tools.github.commits import register
    from fastmcp import FastMCP

    mock_github_client.get.return_value = []

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    await tools["github_commit"].fn(
        action="list",
        owner="owner",
        repo="repo",
        ref="main",
        path="src/",
        per_page=10,
    )

    mock_github_client.get.assert_called_with(
        "/repos/owner/repo/commits",
        params={"per_page": 10, "sha": "main", "path": "src/"},
    )


@pytest.mark.asyncio
async def test_unknown_commit_action():
    """Test unknown action raises error."""
    from mcp_server.tools.github.commits import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="Unknown action"):
        await tools["github_commit"].fn(action="invalid", owner="owner", repo="repo")
