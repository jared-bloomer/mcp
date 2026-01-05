"""Tests for MCP tools."""

import pytest


@pytest.mark.asyncio
async def test_system_info_tool_exists(mcp_server):
    """Test that system_info tool is registered."""
    tools = await mcp_server.get_tools()
    assert "system_info" in tools
    assert tools["system_info"].description == "Get current system information"
    assert "system" in tools["system_info"].tags


@pytest.mark.asyncio
async def test_run_command_tool_exists(mcp_server):
    """Test that run_command tool is registered."""
    tools = await mcp_server.get_tools()
    assert "run_command" in tools
    assert "shell" in tools["run_command"].tags
