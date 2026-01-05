"""MCP Tools."""

from fastmcp import FastMCP

from mcp_server.tools import system


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    system.register(mcp)
