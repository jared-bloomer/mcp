# jlbloomer-mcp-server

Personal MCP (Model Context Protocol) server for AI assistant integration.

## Requirements

- Python 3.14+
- [UV](https://docs.astral.sh/uv/) package manager

## Quick Start

```bash
# Clone and enter directory
cd /path/to/mcp

# Install dependencies
uv sync

# Run server
uv run jlbloomer-mcp
```

## Usage

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

### Claude Code

```bash
claude mcp add jlbloomer-mcp -- uv --directory /path/to/mcp run jlbloomer-mcp
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Type check
uv run mypy src/
```

## Project Structure

```
mcp/
├── src/mcp_server/     # Main package
│   ├── server.py       # Entry point
│   ├── tools/          # MCP tools
│   ├── resources/      # MCP resources
│   └── prompts/        # MCP prompts
├── tests/              # Test suite
└── specs/              # Specification docs
```

## License

MIT
