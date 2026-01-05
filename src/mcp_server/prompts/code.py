"""Code-related prompts."""

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    """Register code prompts with the MCP server."""

    @mcp.prompt(
        name="code_review",
        description="Review code for issues and improvements",
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
        description="Explain what code does",
    )
    def explain_code(language: str, code: str, audience: str = "developer") -> str:
        """Generate a code explanation prompt."""
        return f"""Explain the following {language} code to a {audience}:

```{language}
{code}
```

Break down what each part does and why."""
