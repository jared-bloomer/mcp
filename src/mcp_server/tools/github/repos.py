"""Repository tool for GitHub."""

from typing import Annotated, Any, Literal

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
            Field(description="Action: list, get, create, delete, branches, contents"),
        ],
        owner: Annotated[
            str | None,
            Field(description="Repository owner. Uses authenticated user for 'list' if not provided"),
        ] = None,
        repo: Annotated[
            str | None,
            Field(description="Repository name. Required for get/delete/branches/contents"),
        ] = None,
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
        path: Annotated[
            str | None,
            Field(description="File or directory path (for 'contents' action)"),
        ] = None,
        ref: Annotated[
            str | None,
            Field(description="Branch or commit ref (for 'contents' action)"),
        ] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
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
