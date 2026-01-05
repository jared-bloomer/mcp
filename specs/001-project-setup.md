# MCP Server Specification

## Overview

A local MCP (Model Context Protocol) server built with FastMCP and Python 3.14, packaged for distribution using UV.

## Goals

- Provide AI assistants (Claude Code, GitHub Copilot) with custom tools, resources, and prompts
- Run locally via stdio transport for seamless integration
- Package as distributable Python application (installable via `uvx`)
- Zero runtime dependencies for end users (UV handles everything)

## Technical Stack

| Component | Choice | Version | Notes |
|-----------|--------|---------|-------|
| Language | Python | 3.14.x | Latest stable |
| MCP Framework | FastMCP | <3.0 | Pin to v2 for stability |
| Package Manager | UV | Latest | By Astral |
| Build Backend | Hatchling | Latest | Standard Python builds |
| Transport | stdio | - | Local subprocess communication |

## Project Structure

```
mcp/
├── pyproject.toml          # Project config, dependencies, scripts
├── uv.lock                  # Locked dependencies
├── README.md                # Usage documentation
├── SPEC.md                  # This file
├── src/
│   └── mcp_server/
│       ├── __init__.py     # Package init, version
│       ├── server.py       # Main server entry point
│       ├── tools/          # Tool definitions
│       │   ├── __init__.py
│       │   └── *.py        # Individual tool modules
│       ├── resources/      # Resource definitions
│       │   ├── __init__.py
│       │   └── *.py        # Individual resource modules
│       └── prompts/        # Prompt definitions
│           ├── __init__.py
│           └── *.py        # Individual prompt modules
└── tests/
    ├── __init__.py
    ├── conftest.py         # Pytest fixtures
    ├── test_tools.py
    ├── test_resources.py
    └── test_prompts.py
```

## Configuration

### pyproject.toml

```toml
[project]
name = "jlbloomer-mcp-server"
version = "0.1.0"
description = "Personal MCP server for AI assistant integration"
readme = "README.md"
license = "MIT"
requires-python = ">=3.14"
authors = [
    { name = "Jared Bloomer", email = "your-email@example.com" }
]
keywords = ["mcp", "ai", "claude", "copilot", "fastmcp"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.14",
    "Topic :: Software Development :: Libraries",
]

dependencies = [
    "fastmcp>=2.0,<3",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.8",
    "mypy>=1.13",
]

[project.scripts]
jlbloomer-mcp = "mcp_server.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mcp_server"]

[tool.uv]
package = true

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.14"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

## Implementation

### Server Entry Point (`src/mcp_server/server.py`)

```python
"""Main MCP server entry point."""
from fastmcp import FastMCP

from mcp_server.tools import register_tools
from mcp_server.resources import register_resources
from mcp_server.prompts import register_prompts

mcp = FastMCP(
    name="jlbloomer-mcp",
    instructions="Personal MCP server providing custom tools and resources."
)

# Register all components
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
```

### Example Tool (`src/mcp_server/tools/system.py`)

```python
"""System-related tools."""
import platform
import subprocess
from typing import Annotated

from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError


def register(mcp: FastMCP) -> None:
    """Register system tools with the MCP server."""

    @mcp.tool(
        name="system_info",
        description="Get current system information",
        tags={"system", "info"}
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
        tags={"system", "shell"}
    )
    def run_command(
        command: Annotated[str, Field(description="Command to execute")],
        timeout: Annotated[int, Field(description="Timeout in seconds", ge=1, le=300)] = 30
    ) -> dict:
        """Execute a shell command and return output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
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
```

### Example Resource (`src/mcp_server/resources/files.py`)

```python
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
```

### Example Prompt (`src/mcp_server/prompts/code.py`)

```python
"""Code-related prompts."""
from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    """Register code prompts with the MCP server."""

    @mcp.prompt(
        name="code_review",
        description="Review code for issues and improvements"
    )
    def code_review(language: str, code: str) -> str:
        """Generate a code review prompt."""
        return f"""Review the following {language} code for:
- Bugs and potential issues
- Performance improvements
- Security vulnerabilities
- Code style and best practices

```{language}
{code}
```

Provide specific, actionable feedback."""

    @mcp.prompt(
        name="explain_code",
        description="Explain what code does"
    )
    def explain_code(language: str, code: str, audience: str = "developer") -> str:
        """Generate a code explanation prompt."""
        return f"""Explain the following {language} code to a {audience}:

```{language}
{code}
```

Break down what each part does and why."""
```

## Client Configuration

### Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "jlbloomer-mcp": {
      "command": "uvx",
      "args": ["jlbloomer-mcp-server"]
    }
  }
}
```

### Claude Code (Local Development)

```json
{
  "mcpServers": {
    "jlbloomer-mcp": {
      "command": "uv",
      "args": ["--directory", "/Users/jaredbloomer/git/jlbloomer/mcp", "run", "jlbloomer-mcp"]
    }
  }
}
```

### VS Code / Copilot

See [VS Code MCP Extension](https://marketplace.visualstudio.com/items?itemName=anthropics.mcp-extension) for configuration.

## Development Workflow

### Initial Setup

```bash
# Navigate to project
cd /Users/jaredbloomer/git/jlbloomer/mcp

# Initialize UV project (if not done)
uv init --package

# Install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev
```

### Running Locally

```bash
# Run server directly
uv run jlbloomer-mcp

# Or via Python
uv run python -m mcp_server.server

# Test with FastMCP CLI
uv run fastmcp dev src/mcp_server/server.py
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=mcp_server

# Run specific test
uv run pytest tests/test_tools.py -v
```

### Linting & Type Checking

```bash
# Lint
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy src/
```

### Building & Publishing

```bash
# Build package
uv build

# Test locally before publishing
uv run --with ./dist/jlbloomer_mcp_server-0.1.0-py3-none-any.whl -- jlbloomer-mcp

# Publish to PyPI (when ready)
uv publish
```

## Distribution Options

### Option 1: PyPI (Recommended for sharing)

1. Build: `uv build`
2. Publish: `uv publish`
3. Users install: `uvx jlbloomer-mcp-server`

### Option 2: Direct from Git

Users can run directly from the repository:

```json
{
  "mcpServers": {
    "jlbloomer-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jlbloomer/mcp", "jlbloomer-mcp"]
    }
  }
}
```

### Option 3: Local Development

For personal use without publishing:

```json
{
  "mcpServers": {
    "jlbloomer-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp", "run", "jlbloomer-mcp"]
    }
  }
}
```

## Security Considerations

- **Command Execution**: The `run_command` tool executes shell commands. Consider:
  - Restricting to specific allowed commands
  - Adding confirmation prompts for destructive operations
  - Logging all command executions

- **File Access**: File resources should:
  - Restrict access to specific directories
  - Prevent reading sensitive files (`.env`, credentials, etc.)
  - Validate paths to prevent directory traversal

- **Secrets**: Never expose:
  - API keys
  - Passwords
  - Private keys
  - Environment variables containing secrets

## Future Enhancements

- [ ] Add HTTP transport option for remote access
- [ ] Implement authentication for sensitive tools
- [ ] Add rate limiting
- [ ] Create tool for database queries
- [ ] Add git operations tools
- [ ] Integrate with external APIs (weather, news, etc.)
- [ ] Add caching for expensive operations
- [ ] Implement logging and metrics

## References

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [FastMCP Documentation](https://gofastmcp.com)
- [UV Documentation](https://docs.astral.sh/uv)
- [Python 3.14 What's New](https://docs.python.org/3/whatsnew/3.14.html)
