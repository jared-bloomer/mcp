"""Issue tool for GitHub."""

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from mcp_server.tools.github.client import get_client


def register(mcp: FastMCP) -> None:
    """Register the github_issue tool."""

    @mcp.tool(
        name="github_issue",
        description="Manage GitHub issues. Actions: list, get, create, update, close, comment",
        tags={"github", "issues"},
    )
    async def github_issue(
        action: Annotated[
            Literal["list", "get", "create", "update", "close", "comment"],
            Field(description="Action: list, get, create, update, close, comment"),
        ],
        owner: Annotated[str, Field(description="Repository owner")],
        repo: Annotated[str, Field(description="Repository name")],
        issue_number: Annotated[
            int | None,
            Field(description="Issue number. Required for get/update/close/comment"),
        ] = None,
        title: Annotated[
            str | None,
            Field(description="Issue title (for 'create'/'update' actions)"),
        ] = None,
        body: Annotated[
            str | None,
            Field(description="Issue body or comment text"),
        ] = None,
        labels: Annotated[
            list[str] | None,
            Field(description="Labels to apply (for 'create'/'update' actions)"),
        ] = None,
        assignees: Annotated[
            list[str] | None,
            Field(description="Usernames to assign (for 'create'/'update' actions)"),
        ] = None,
        state: Annotated[
            str | None,
            Field(description="Filter by state: open, closed, all (for 'list' action)"),
        ] = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Execute issue operations."""
        client = get_client()

        match action:
            case "list":
                params: dict[str, Any] = {"per_page": client.config.per_page}
                if state:
                    params["state"] = state
                issues = await client.get(f"/repos/{owner}/{repo}/issues", params=params)
                return [
                    {
                        "number": i["number"],
                        "title": i["title"],
                        "state": i["state"],
                        "user": i["user"]["login"],
                        "labels": [l["name"] for l in i["labels"]],
                        "url": i["html_url"],
                        "created_at": i["created_at"],
                    }
                    for i in issues
                ]

            case "get":
                if issue_number is None:
                    raise ToolError("'issue_number' is required for 'get' action")
                return await client.get(f"/repos/{owner}/{repo}/issues/{issue_number}")

            case "create":
                if not title:
                    raise ToolError("'title' is required for 'create' action")
                data: dict[str, Any] = {"title": title}
                if body:
                    data["body"] = body
                if labels:
                    data["labels"] = labels
                if assignees:
                    data["assignees"] = assignees
                return await client.post(f"/repos/{owner}/{repo}/issues", json=data)

            case "update":
                if issue_number is None:
                    raise ToolError("'issue_number' is required for 'update' action")
                data = {}
                if title:
                    data["title"] = title
                if body:
                    data["body"] = body
                if labels:
                    data["labels"] = labels
                if state:
                    data["state"] = state
                return await client.patch(f"/repos/{owner}/{repo}/issues/{issue_number}", json=data)

            case "close":
                if issue_number is None:
                    raise ToolError("'issue_number' is required for 'close' action")
                return await client.patch(
                    f"/repos/{owner}/{repo}/issues/{issue_number}",
                    json={"state": "closed"},
                )

            case "comment":
                if issue_number is None:
                    raise ToolError("'issue_number' is required for 'comment' action")
                if not body:
                    raise ToolError("'body' is required for 'comment' action")
                return await client.post(
                    f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
                    json={"body": body},
                )

            case _:
                raise ToolError(f"Unknown action: {action}")
