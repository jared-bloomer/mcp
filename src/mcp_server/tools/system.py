"""System-related tools."""

import platform
import subprocess
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field


def register(mcp: FastMCP) -> None:
    """Register system tools with the MCP server."""

    @mcp.tool(
        name="system_info",
        description="Get current system information",
        tags={"system", "info"},
    )
    def system_info() -> dict:
        """Return system information."""
        return {
            "platform": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        }

    @mcp.tool(
        name="run_command",
        description="Execute a shell command (use with caution)",
        tags={"system", "shell"},
    )
    def run_command(
        command: Annotated[str, Field(description="Command to execute")],
        timeout: Annotated[int, Field(description="Timeout in seconds", ge=1, le=300)] = 30,
    ) -> dict:
        """Execute a shell command and return output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            raise ToolError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise ToolError(f"Command failed: {e}")
