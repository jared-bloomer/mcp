"""Tests for MCP resources."""

import pytest
from pathlib import Path
import tempfile


@pytest.mark.asyncio
async def test_file_resource_exists(mcp_server):
    """Test that file resource is registered."""
    templates = await mcp_server.get_resource_templates()
    assert "file://{filepath*}" in templates


@pytest.mark.asyncio
async def test_dir_resource_exists(mcp_server):
    """Test that directory resource is registered."""
    templates = await mcp_server.get_resource_templates()
    assert "dir://{dirpath*}" in templates


@pytest.mark.asyncio
async def test_read_file_resource(mcp_server):
    """Test reading a file resource."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        templates = await mcp_server.get_resource_templates()
        file_template = templates["file://{filepath*}"]
        result = file_template.fn(temp_path)
        assert result == "test content"
    finally:
        Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_read_file_not_found(mcp_server):
    """Test reading a non-existent file raises error."""
    from fastmcp.exceptions import ResourceError

    templates = await mcp_server.get_resource_templates()
    file_template = templates["file://{filepath*}"]

    with pytest.raises(ResourceError, match="File not found"):
        file_template.fn("/nonexistent/path/file.txt")


@pytest.mark.asyncio
async def test_read_file_not_a_file(mcp_server):
    """Test reading a directory as file raises error."""
    from fastmcp.exceptions import ResourceError

    templates = await mcp_server.get_resource_templates()
    file_template = templates["file://{filepath*}"]

    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ResourceError, match="Not a file"):
            file_template.fn(temp_dir)


@pytest.mark.asyncio
async def test_list_directory_resource(mcp_server):
    """Test listing a directory resource."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        Path(temp_dir, "file1.txt").touch()
        Path(temp_dir, "file2.txt").touch()

        templates = await mcp_server.get_resource_templates()
        dir_template = templates["dir://{dirpath*}"]
        result = dir_template.fn(temp_dir)

        assert len(result) == 2
        assert any("file1.txt" in str(p) for p in result)
        assert any("file2.txt" in str(p) for p in result)


@pytest.mark.asyncio
async def test_list_directory_not_found(mcp_server):
    """Test listing a non-existent directory raises error."""
    from fastmcp.exceptions import ResourceError

    templates = await mcp_server.get_resource_templates()
    dir_template = templates["dir://{dirpath*}"]

    with pytest.raises(ResourceError, match="Directory not found"):
        dir_template.fn("/nonexistent/path")


@pytest.mark.asyncio
async def test_list_directory_not_a_directory(mcp_server):
    """Test listing a file as directory raises error."""
    from fastmcp.exceptions import ResourceError

    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name

    try:
        templates = await mcp_server.get_resource_templates()
        dir_template = templates["dir://{dirpath*}"]

        with pytest.raises(ResourceError, match="Not a directory"):
            dir_template.fn(temp_path)
    finally:
        Path(temp_path).unlink()
