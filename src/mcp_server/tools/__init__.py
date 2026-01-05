"""MCP Tools."""

from fastmcp import FastMCP

from mcp_server.tools import system
from mcp_server.tools import github


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    system.register(mcp)
    github.register(mcp)
