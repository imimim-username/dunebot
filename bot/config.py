"""Configuration loader for Dune Discord Bot.

Loads settings from environment variables and YAML configuration files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


@dataclass
class DuneQueryConfig:
    """Configuration for a single Dune query mapping."""
    
    id: int
    description: str = ""
    result_type: str = "table"  # "table" or "summary"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    
    # Required settings (no defaults)
    discord_bot_token: str
    dune_api_key: str
    
    # Optional settings (with defaults)
    discord_guild_id: int | None = None
    embed_delay_seconds: int = 10
    
    # Query mappings (loaded from YAML)
    queries: dict[str, DuneQueryConfig] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls, env_path: Path | str | None = None) -> Settings:
        """Load settings from environment variables.
        
        Args:
            env_path: Optional path to .env file. If None, looks for .env in project root.
            
        Returns:
            Settings instance with loaded configuration.
            
        Raises:
            ValueError: If required environment variables are missing.
        """
        # Load .env file if it exists
        if env_path is None:
            env_path = PROJECT_ROOT / ".env"
        
        if Path(env_path).exists():
            load_dotenv(env_path)
        
        # Get required settings
        discord_token = os.getenv("DISCORD_BOT_TOKEN")
        if not discord_token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
        
        dune_api_key = os.getenv("DUNE_API_KEY")
        if not dune_api_key:
            raise ValueError("DUNE_API_KEY environment variable is required")
        
        # Get optional settings
        guild_id_str = os.getenv("DISCORD_GUILD_ID")
        guild_id = int(guild_id_str) if guild_id_str else None
        
        # Get embed delay setting (default 10 seconds)
        embed_delay_str = os.getenv("EMBED_DELAY_SECONDS", "10")
        try:
            embed_delay = int(embed_delay_str)
            if embed_delay < 0:
                raise ValueError("EMBED_DELAY_SECONDS must be >= 0")
        except ValueError as e:
            if "must be" in str(e):
                raise ValueError(f"EMBED_DELAY_SECONDS must be >= 0") from e
            raise ValueError(f"EMBED_DELAY_SECONDS must be a valid integer, got: {embed_delay_str}") from e
        
        return cls(
            discord_bot_token=discord_token,
            discord_guild_id=guild_id,
            dune_api_key=dune_api_key,
            embed_delay_seconds=embed_delay,
        )
    
    def load_queries(self, yaml_path: Path | str | None = None) -> None:
        """Load query mappings from YAML configuration file.
        
        Args:
            yaml_path: Optional path to YAML file. If None, uses default location.
        """
        if yaml_path is None:
            yaml_path = CONFIG_DIR / "dune_queries.yaml"
        
        yaml_path = Path(yaml_path)
        
        if not yaml_path.exists():
            # No queries config file - that's okay, just use empty dict
            return
        
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f) or {}
        
        queries_data = config.get("queries", {})
        
        for name, query_config in queries_data.items():
            if not isinstance(query_config, dict):
                continue
                
            query_id = query_config.get("id")
            if query_id is None:
                continue
            
            self.queries[name] = DuneQueryConfig(
                id=int(query_id),
                description=query_config.get("description", ""),
                result_type=query_config.get("result_type", "table"),
                params=query_config.get("params", {}),
            )
    
    def get_query_by_name(self, name: str) -> DuneQueryConfig | None:
        """Get a query configuration by its name.
        
        Args:
            name: The query name as defined in dune_queries.yaml
            
        Returns:
            DuneQueryConfig if found, None otherwise.
        """
        return self.queries.get(name)


def load_settings(env_path: Path | str | None = None, 
                  queries_path: Path | str | None = None) -> Settings:
    """Convenience function to load all settings.
    
    Args:
        env_path: Optional path to .env file.
        queries_path: Optional path to dune_queries.yaml file.
        
    Returns:
        Fully configured Settings instance.
    """
    settings = Settings.from_env(env_path)
    settings.load_queries(queries_path)
    return settings

