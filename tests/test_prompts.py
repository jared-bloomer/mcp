"""Tests for MCP prompts."""

import pytest


@pytest.mark.asyncio
async def test_code_review_prompt_exists(mcp_server):
    """Test that code_review prompt is registered."""
    prompts = await mcp_server.get_prompts()
    assert "code_review" in prompts
    assert prompts["code_review"].description == "Review code for issues and improvements"


@pytest.mark.asyncio
async def test_explain_code_prompt_exists(mcp_server):
    """Test that explain_code prompt is registered."""
    prompts = await mcp_server.get_prompts()
    assert "explain_code" in prompts
    assert prompts["explain_code"].description == "Explain what code does"


@pytest.mark.asyncio
async def test_code_review_prompt_content(mcp_server):
    """Test code_review prompt generates correct content."""
    prompt = await mcp_server.get_prompt("code_review")
    content = prompt.fn(language="python", code="def hello(): pass")

    assert "python" in content
    assert "def hello(): pass" in content
    assert "Bugs" in content
    assert "Performance" in content
    assert "Security" in content


@pytest.mark.asyncio
async def test_explain_code_prompt_content(mcp_server):
    """Test explain_code prompt generates correct content."""
    prompt = await mcp_server.get_prompt("explain_code")
    content = prompt.fn(language="javascript", code="const x = 1;")

    assert "javascript" in content
    assert "const x = 1;" in content
    assert "developer" in content  # default audience


@pytest.mark.asyncio
async def test_explain_code_prompt_with_audience(mcp_server):
    """Test explain_code prompt with custom audience."""
    prompt = await mcp_server.get_prompt("explain_code")
    content = prompt.fn(
        language="python",
        code="x = [i**2 for i in range(10)]",
        audience="beginner",
    )

    assert "beginner" in content
    assert "python" in content
