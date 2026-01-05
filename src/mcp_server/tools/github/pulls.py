"""Pull request tool for GitHub."""

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from mcp_server.tools.github.client import get_client


def register(mcp: FastMCP) -> None:
    """Register the github_pull tool."""

    @mcp.tool(
        name="github_pull",
        description="Manage GitHub pull requests. Actions: list, get, create, update, merge, files, reviews",
        tags={"github", "pulls"},
    )
    async def github_pull(
        action: Annotated[
            Literal["list", "get", "create", "update", "merge", "files", "reviews"],
            Field(description="Action: list, get, create, update, merge, files, reviews"),
        ],
        owner: Annotated[str, Field(description="Repository owner")],
        repo: Annotated[str, Field(description="Repository name")],
        pull_number: Annotated[
            int | None,
            Field(description="PR number. Required for get/update/merge/files/reviews"),
        ] = None,
        title: Annotated[
            str | None,
            Field(description="PR title (for 'create'/'update' actions)"),
        ] = None,
        body: Annotated[
            str | None,
            Field(description="PR description (for 'create'/'update' actions)"),
        ] = None,
        head: Annotated[
            str | None,
            Field(description="Source branch (for 'create' action)"),
        ] = None,
        base: Annotated[
            str | None,
            Field(description="Target branch (for 'create'/'list' actions)"),
        ] = None,
        merge_method: Annotated[
            str | None,
            Field(description="Merge method: merge, squash, rebase (for 'merge' action)"),
        ] = None,
        state: Annotated[
            str | None,
            Field(description="Filter by state: open, closed, all (for 'list' action)"),
        ] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Execute pull request operations."""
        client = get_client()

        match action:
            case "list":
                params: dict[str, Any] = {"per_page": client.config.per_page}
                if state:
                    params["state"] = state
                if base:
                    params["base"] = base
                pulls = await client.get(f"/repos/{owner}/{repo}/pulls", params=params)
                return [
                    {
                        "number": p["number"],
                        "title": p["title"],
                        "state": p["state"],
                        "user": p["user"]["login"],
                        "head": p["head"]["ref"],
                        "base": p["base"]["ref"],
                        "url": p["html_url"],
                        "created_at": p["created_at"],
                    }
                    for p in pulls
                ]

            case "get":
                if pull_number is None:
                    raise ToolError("'pull_number' is required for 'get' action")
                return await client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}")

            case "create":
                if not title or not head or not base:
                    raise ToolError("'title', 'head', and 'base' are required for 'create' action")
                data: dict[str, Any] = {"title": title, "head": head, "base": base}
                if body:
                    data["body"] = body
                return await client.post(f"/repos/{owner}/{repo}/pulls", json=data)

            case "update":
                if pull_number is None:
                    raise ToolError("'pull_number' is required for 'update' action")
                data = {}
                if title:
                    data["title"] = title
                if body:
                    data["body"] = body
                if state:
                    data["state"] = state
                return await client.patch(f"/repos/{owner}/{repo}/pulls/{pull_number}", json=data)

            case "merge":
                if pull_number is None:
                    raise ToolError("'pull_number' is required for 'merge' action")
                data = {}
                if merge_method:
                    data["merge_method"] = merge_method
                return await client.put(f"/repos/{owner}/{repo}/pulls/{pull_number}/merge", json=data)

            case "files":
                if pull_number is None:
                    raise ToolError("'pull_number' is required for 'files' action")
                return await client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}/files")

            case "reviews":
                if pull_number is None:
                    raise ToolError("'pull_number' is required for 'reviews' action")
                return await client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews")

            case _:
                raise ToolError(f"Unknown action: {action}")
