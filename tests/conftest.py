"""Pytest configuration and fixtures."""

import pytest
from fastmcp import FastMCP


@pytest.fixture
def mcp_server() -> FastMCP:
    """Create a fresh MCP server instance for testing."""
    from mcp_server.server import mcp

    return mcp
