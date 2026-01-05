"""File-related resources."""

from pathlib import Path

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError


def register(mcp: FastMCP) -> None:
    """Register file resources with the MCP server."""

    @mcp.resource("file://{filepath*}")
    def read_file(filepath: str) -> str:
        """Read contents of a file."""
        path = Path(filepath)
        if not path.exists():
            raise ResourceError(f"File not found: {filepath}")
        if not path.is_file():
            raise ResourceError(f"Not a file: {filepath}")
        return path.read_text()

    @mcp.resource("dir://{dirpath*}")
    def list_directory(dirpath: str) -> list[str]:
        """List contents of a directory."""
        path = Path(dirpath)
        if not path.exists():
            raise ResourceError(f"Directory not found: {dirpath}")
        if not path.is_dir():
            raise ResourceError(f"Not a directory: {dirpath}")
        return [str(p) for p in path.iterdir()]
