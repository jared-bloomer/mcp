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


@pytest.mark.asyncio
async def test_system_info_returns_data(mcp_server):
    """Test that system_info returns system information."""
    tools = await mcp_server.get_tools()
    result = tools["system_info"].fn()

    assert "platform" in result
    assert "release" in result
    assert "machine" in result
    assert "python_version" in result


@pytest.mark.asyncio
async def test_run_command_success(mcp_server):
    """Test running a successful command."""
    tools = await mcp_server.get_tools()
    result = tools["run_command"].fn(command="echo hello", timeout=5)

    assert result["returncode"] == 0
    assert "hello" in result["stdout"]
    assert result["stderr"] == ""


@pytest.mark.asyncio
async def test_run_command_with_stderr(mcp_server):
    """Test running a command that writes to stderr."""
    tools = await mcp_server.get_tools()
    result = tools["run_command"].fn(command="echo error >&2", timeout=5)

    assert "error" in result["stderr"]


@pytest.mark.asyncio
async def test_run_command_failure(mcp_server):
    """Test running a command that fails."""
    tools = await mcp_server.get_tools()
    result = tools["run_command"].fn(command="exit 1", timeout=5)

    assert result["returncode"] == 1


@pytest.mark.asyncio
async def test_run_command_timeout():
    """Test command timeout."""
    from mcp_server.tools.system import register
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    mcp = FastMCP("test")
    register(mcp)

    tools = await mcp.get_tools()
    with pytest.raises(ToolError, match="timed out"):
        tools["run_command"].fn(command="sleep 10", timeout=1)
