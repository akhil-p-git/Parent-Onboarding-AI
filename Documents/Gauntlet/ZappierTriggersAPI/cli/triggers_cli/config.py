"""
CLI Configuration Management.

Handles configuration loading from environment, config files, and CLI options.
"""

import os
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CliConfig(BaseSettings):
    """CLI configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="TRIGGERS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    api_url: str = Field(
        default="http://localhost:8000",
        description="Triggers API base URL",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authentication",
    )

    # Output Configuration
    output_format: str = Field(
        default="table",
        description="Default output format: table, json, yaml",
    )
    no_color: bool = Field(
        default=False,
        description="Disable colored output",
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose output",
    )

    # Timeout Configuration
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
    )

    # Streaming Configuration
    reconnect_delay: int = Field(
        default=5,
        description="Delay between reconnection attempts for streaming",
    )
    max_reconnects: int = Field(
        default=10,
        description="Maximum reconnection attempts",
    )

    @property
    def api_base_url(self) -> str:
        """Get the API base URL with /api/v1 suffix."""
        base = self.api_url.rstrip("/")
        if not base.endswith("/api/v1"):
            base = f"{base}/api/v1"
        return base


# Global config instance
_config: CliConfig | None = None


def get_config() -> CliConfig:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = CliConfig()
    return _config


def set_config(**kwargs: Any) -> CliConfig:
    """Set config values and return the updated config."""
    global _config
    current = get_config()

    # Create new config with updated values
    config_dict = current.model_dump()
    config_dict.update({k: v for k, v in kwargs.items() if v is not None})

    _config = CliConfig(**config_dict)
    return _config


def get_config_path() -> Path:
    """Get the path to the config file."""
    # Check for config in order of precedence
    paths = [
        Path.cwd() / ".triggers.env",
        Path.home() / ".triggers" / "config",
        Path.home() / ".config" / "triggers" / "config",
    ]

    for path in paths:
        if path.exists():
            return path

    # Default to home directory
    return Path.home() / ".triggers" / "config"


def save_config(config: CliConfig) -> None:
    """Save config to file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        f.write(f"TRIGGERS_API_URL={config.api_url}\n")
        if config.api_key:
            f.write(f"TRIGGERS_API_KEY={config.api_key}\n")
        f.write(f"TRIGGERS_OUTPUT_FORMAT={config.output_format}\n")
        f.write(f"TRIGGERS_TIMEOUT={config.timeout}\n")
