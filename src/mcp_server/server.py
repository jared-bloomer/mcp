"""Main MCP server entry point."""

from fastmcp import FastMCP

from mcp_server.tools import register_tools
from mcp_server.resources import register_resources
from mcp_server.prompts import register_prompts

mcp = FastMCP(
    name="jlbloomer-mcp",
    instructions="Personal MCP server providing custom tools and resources.",
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
