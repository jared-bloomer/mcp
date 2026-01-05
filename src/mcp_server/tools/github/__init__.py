"""GitHub MCP tools."""

from fastmcp import FastMCP

from mcp_server.tools.github import repos, issues, pulls, commits


def register(mcp: FastMCP) -> None:
    """Register all GitHub tools with the MCP server."""
    repos.register(mcp)
    issues.register(mcp)
    pulls.register(mcp)
    commits.register(mcp)
