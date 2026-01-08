"""Tests for configuration loading."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch


def test_github_config_defaults():
    """Test GitHubConfig has correct defaults."""
    from mcp_server.config.loader import GitHubConfig

    config = GitHubConfig()

    assert config.token_env == "GITHUB_TOKEN"
    assert config.api_version == "2022-11-28"
    assert config.base_url == "https://api.github.com"
    assert config.default_owner == ""
    assert config.per_page == 30
    assert config.respect_rate_limits is True
    assert config.retry_on_rate_limit is True
    assert config.max_retries == 3


def test_github_config_token_from_env():
    """Test token resolution from environment variable."""
    from mcp_server.config.loader import GitHubConfig

    with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token-123"}):
        config = GitHubConfig()
        assert config.token == "test-token-123"


def test_github_config_token_missing():
    """Test error when token env var is not set."""
    from mcp_server.config.loader import GitHubConfig

    with patch.dict(os.environ, {}, clear=True):
        # Remove GITHUB_TOKEN if it exists
        os.environ.pop("GITHUB_TOKEN", None)
        config = GitHubConfig()

        with pytest.raises(ValueError, match="GitHub token not found"):
            _ = config.token


def test_github_config_custom_token_env():
    """Test using a custom token environment variable name."""
    from mcp_server.config.loader import GitHubConfig

    with patch.dict(os.environ, {"MY_GH_TOKEN": "custom-token"}):
        config = GitHubConfig(token_env="MY_GH_TOKEN")
        assert config.token == "custom-token"


def test_github_config_load_from_toml():
    """Test loading config from TOML file."""
    from mcp_server.config.loader import GitHubConfig

    toml_content = """
[github]
token_env = "CUSTOM_TOKEN"
api_version = "2023-01-01"
base_url = "https://github.example.com/api"
default_owner = "myorg"
per_page = 50
respect_rate_limits = false
retry_on_rate_limit = false
max_retries = 5
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        config_path = Path(f.name)

    try:
        config = GitHubConfig.load(config_path)

        assert config.token_env == "CUSTOM_TOKEN"
        assert config.api_version == "2023-01-01"
        assert config.base_url == "https://github.example.com/api"
        assert config.default_owner == "myorg"
        assert config.per_page == 50
        assert config.respect_rate_limits is False
        assert config.retry_on_rate_limit is False
        assert config.max_retries == 5
    finally:
        config_path.unlink()


def test_github_config_load_missing_file():
    """Test loading config when file doesn't exist returns defaults."""
    from mcp_server.config.loader import GitHubConfig

    config = GitHubConfig.load(Path("/nonexistent/config.toml"))

    # Should return defaults
    assert config.token_env == "GITHUB_TOKEN"
    assert config.api_version == "2022-11-28"


def test_github_config_load_empty_github_section():
    """Test loading config with empty github section."""
    from mcp_server.config.loader import GitHubConfig

    toml_content = """
[other]
key = "value"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        config_path = Path(f.name)

    try:
        config = GitHubConfig.load(config_path)
        # Should use defaults when github section is missing
        assert config.token_env == "GITHUB_TOKEN"
    finally:
        config_path.unlink()
