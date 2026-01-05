"""Configuration loader with environment variable resolution."""

import os
import tomllib
from pathlib import Path

from pydantic_settings import BaseSettings


class GitHubConfig(BaseSettings):
    """GitHub configuration with env var resolution."""

    token_env: str = "GITHUB_TOKEN"
    api_version: str = "2022-11-28"
    base_url: str = "https://api.github.com"
    default_owner: str = ""
    per_page: int = 30
    respect_rate_limits: bool = True
    retry_on_rate_limit: bool = True
    max_retries: int = 3

    @property
    def token(self) -> str:
        """Resolve token from environment variable."""
        token = os.environ.get(self.token_env)
        if not token:
            raise ValueError(
                f"GitHub token not found. Set {self.token_env} environment variable."
            )
        return token

    @classmethod
    def load(cls, config_path: Path | None = None) -> "GitHubConfig":
        """Load config from TOML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "github.toml"

        if not config_path.exists():
            return cls()

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        return cls(**data.get("github", {}))
