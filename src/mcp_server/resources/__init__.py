"""MCP Resources."""

from fastmcp import FastMCP

from mcp_server.resources import files


def register_resources(mcp: FastMCP) -> None:
    """Register all resources with the MCP server."""
    files.register(mcp)
