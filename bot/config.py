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
    
    # Scheduled execution settings (optional)
    scheduled_query_id: int | None = None
    scheduled_execution_time: str | None = None  # HH:MM format (24-hour)
    discord_channel_id: int | None = None
    
    # ALCX sums query (optional - displays 24h buy/sell totals after scheduled embeds)
    alcx_sums_query_id: int | None = None
    
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
        
        # Get scheduled execution settings (optional)
        scheduled_query_id_str = os.getenv("SCHEDULED_QUERY_ID")
        scheduled_query_id = int(scheduled_query_id_str) if scheduled_query_id_str else None
        
        scheduled_execution_time = os.getenv("SCHEDULED_EXECUTION_TIME")
        if scheduled_execution_time:
            # Validate time format (HH:MM)
            try:
                parts = scheduled_execution_time.split(":")
                if len(parts) != 2:
                    raise ValueError("SCHEDULED_EXECUTION_TIME must be in HH:MM format")
                hour = int(parts[0])
                minute = int(parts[1])
                if not (0 <= hour <= 23):
                    raise ValueError("Hour must be between 0 and 23")
                if not (0 <= minute <= 59):
                    raise ValueError("Minute must be between 0 and 59")
            except ValueError as e:
                raise ValueError(f"Invalid SCHEDULED_EXECUTION_TIME format: {e}") from e
        
        discord_channel_id_str = os.getenv("DISCORD_CHANNEL_ID")
        discord_channel_id = int(discord_channel_id_str) if discord_channel_id_str else None
        
        # Get ALCX sums query ID (optional)
        alcx_sums_query_id_str = os.getenv("ALCX_SUMS_QUERY_ID")
        alcx_sums_query_id = int(alcx_sums_query_id_str) if alcx_sums_query_id_str else None
        
        return cls(
            discord_bot_token=discord_token,
            discord_guild_id=guild_id,
            dune_api_key=dune_api_key,
            embed_delay_seconds=embed_delay,
            scheduled_query_id=scheduled_query_id,
            scheduled_execution_time=scheduled_execution_time,
            discord_channel_id=discord_channel_id,
            alcx_sums_query_id=alcx_sums_query_id,
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

