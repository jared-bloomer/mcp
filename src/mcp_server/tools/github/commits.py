"""Commit tool for GitHub."""

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from mcp_server.tools.github.client import get_client


def register(mcp: FastMCP) -> None:
    """Register the github_commit tool."""

    @mcp.tool(
        name="github_commit",
        description="View GitHub commits. Actions: list, get, compare, status",
        tags={"github", "commits"},
    )
    async def github_commit(
        action: Annotated[
            Literal["list", "get", "compare", "status"],
            Field(description="Action: list, get, compare, status"),
        ],
        owner: Annotated[str, Field(description="Repository owner")],
        repo: Annotated[str, Field(description="Repository name")],
        ref: Annotated[
            str | None,
            Field(description="Commit SHA or branch name"),
        ] = None,
        base: Annotated[
            str | None,
            Field(description="Base ref for comparison (for 'compare' action)"),
        ] = None,
        head: Annotated[
            str | None,
            Field(description="Head ref for comparison (for 'compare' action)"),
        ] = None,
        path: Annotated[
            str | None,
            Field(description="Filter commits by file path (for 'list' action)"),
        ] = None,
        per_page: Annotated[
            int,
            Field(description="Results per page", ge=1, le=100),
        ] = 30,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Execute commit operations."""
        client = get_client()

        match action:
            case "list":
                params: dict[str, Any] = {"per_page": per_page}
                if ref:
                    params["sha"] = ref
                if path:
                    params["path"] = path
                commits = await client.get(f"/repos/{owner}/{repo}/commits", params=params)
                return [
                    {
                        "sha": c["sha"][:7],
                        "full_sha": c["sha"],
                        "message": c["commit"]["message"].split("\n")[0],
                        "author": c["commit"]["author"]["name"],
                        "date": c["commit"]["author"]["date"],
                        "url": c["html_url"],
                    }
                    for c in commits
                ]

            case "get":
                if not ref:
                    raise ToolError("'ref' is required for 'get' action")
                return await client.get(f"/repos/{owner}/{repo}/commits/{ref}")

            case "compare":
                if not base or not head:
                    raise ToolError("'base' and 'head' are required for 'compare' action")
                result = await client.get(f"/repos/{owner}/{repo}/compare/{base}...{head}")
                return {
                    "status": result["status"],
                    "ahead_by": result["ahead_by"],
                    "behind_by": result["behind_by"],
                    "total_commits": result["total_commits"],
                    "commits": [
                        {
                            "sha": c["sha"][:7],
                            "message": c["commit"]["message"].split("\n")[0],
                            "author": c["commit"]["author"]["name"],
                        }
                        for c in result["commits"]
                    ],
                    "files_changed": len(result.get("files", [])),
                }

            case "status":
                if not ref:
                    raise ToolError("'ref' is required for 'status' action")
                return await client.get(f"/repos/{owner}/{repo}/commits/{ref}/status")

            case _:
                raise ToolError(f"Unknown action: {action}")
