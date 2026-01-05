"""MCP Prompts."""

from fastmcp import FastMCP

from mcp_server.prompts import code


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the MCP server."""
    code.register(mcp)
