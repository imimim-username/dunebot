"""Tests for configuration loading."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from bot.config import Settings, DuneQueryConfig, load_settings


class TestSettings:
    """Test Settings dataclass and loading."""
    
    def test_from_env_with_required_vars(self, monkeypatch):
        """Test loading settings with required environment variables."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token-123")
        monkeypatch.setenv("DUNE_API_KEY", "test-dune-key-456")
        
        # Use a non-existent .env file path to avoid loading real .env
        settings = Settings.from_env("/nonexistent/.env")
        
        assert settings.discord_bot_token == "test-token-123"
        assert settings.dune_api_key == "test-dune-key-456"
        assert settings.discord_guild_id is None
        assert settings.embed_delay_seconds == 10  # Default value
    
    def test_from_env_with_optional_guild_id(self, monkeypatch):
        """Test loading settings with optional guild ID."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("DISCORD_GUILD_ID", "123456789")
        
        # Use a non-existent .env file path to avoid loading real .env
        settings = Settings.from_env("/nonexistent/.env")
        
        assert settings.discord_guild_id == 123456789
    
    def test_from_env_with_embed_delay(self, monkeypatch):
        """Test loading settings with custom embed delay."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("EMBED_DELAY_SECONDS", "5")
        
        # Use a non-existent .env file path to avoid loading real .env
        settings = Settings.from_env("/nonexistent/.env")
        
        assert settings.embed_delay_seconds == 5
    
    def test_from_env_embed_delay_default(self, monkeypatch):
        """Test that embed delay defaults to 10 if not set."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.delenv("EMBED_DELAY_SECONDS", raising=False)
        
        # Use a non-existent .env file path to avoid loading real .env
        settings = Settings.from_env("/nonexistent/.env")
        
        assert settings.embed_delay_seconds == 10
    
    def test_from_env_embed_delay_invalid(self, monkeypatch):
        """Test that invalid embed delay raises ValueError."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("EMBED_DELAY_SECONDS", "invalid")
        
        # Use a non-existent .env file path to avoid loading real .env
        with pytest.raises(ValueError, match="EMBED_DELAY_SECONDS"):
            Settings.from_env("/nonexistent/.env")
    
    def test_from_env_embed_delay_negative(self, monkeypatch):
        """Test that negative embed delay raises ValueError."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("EMBED_DELAY_SECONDS", "-1")
        
        # Use a non-existent .env file path to avoid loading real .env
        with pytest.raises(ValueError, match="EMBED_DELAY_SECONDS"):
            Settings.from_env("/nonexistent/.env")
    
    def test_from_env_scheduled_settings(self, monkeypatch):
        """Test loading scheduled execution settings."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("SCHEDULED_QUERY_ID", "12345")
        monkeypatch.setenv("SCHEDULED_EXECUTION_TIME", "14:30")
        monkeypatch.setenv("DISCORD_CHANNEL_ID", "999999")
        
        # Use a non-existent .env file path to avoid loading real .env
        settings = Settings.from_env("/nonexistent/.env")
        
        assert settings.scheduled_query_id == 12345
        assert settings.scheduled_execution_time == "14:30"
        assert settings.discord_channel_id == 999999
    
    def test_from_env_alcx_sums_query_id(self, monkeypatch):
        """Test loading ALCX sums query ID."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("ALCX_SUMS_QUERY_ID", "98765")
        
        # Use a non-existent .env file path to avoid loading real .env
        settings = Settings.from_env("/nonexistent/.env")
        
        assert settings.alcx_sums_query_id == 98765
    
    def test_from_env_alcx_sums_query_id_not_set(self, monkeypatch):
        """Test that ALCX sums query ID defaults to None if not set."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.delenv("ALCX_SUMS_QUERY_ID", raising=False)
        
        # Use a non-existent .env file path to avoid loading real .env
        settings = Settings.from_env("/nonexistent/.env")
        
        assert settings.alcx_sums_query_id is None
    
    def test_from_env_scheduled_time_invalid_format(self, monkeypatch):
        """Test that invalid time format raises ValueError."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("SCHEDULED_EXECUTION_TIME", "invalid")
        
        # Use a non-existent .env file path to avoid loading real .env
        with pytest.raises(ValueError, match="SCHEDULED_EXECUTION_TIME"):
            Settings.from_env("/nonexistent/.env")
    
    def test_from_env_scheduled_time_invalid_hour(self, monkeypatch):
        """Test that invalid hour raises ValueError."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("SCHEDULED_EXECUTION_TIME", "25:00")
        
        # Use a non-existent .env file path to avoid loading real .env
        with pytest.raises(ValueError, match="Hour must be between"):
            Settings.from_env("/nonexistent/.env")
    
    def test_from_env_scheduled_time_invalid_minute(self, monkeypatch):
        """Test that invalid minute raises ValueError."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("SCHEDULED_EXECUTION_TIME", "14:60")
        
        # Use a non-existent .env file path to avoid loading real .env
        with pytest.raises(ValueError, match="Minute must be between"):
            Settings.from_env("/nonexistent/.env")
    
    def test_from_env_missing_discord_token(self, monkeypatch):
        """Test that missing DISCORD_BOT_TOKEN raises ValueError."""
        monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        
        # Use a non-existent .env file path to avoid loading real .env
        with pytest.raises(ValueError, match="DISCORD_BOT_TOKEN"):
            Settings.from_env("/nonexistent/.env")
    
    def test_from_env_missing_dune_key(self, monkeypatch):
        """Test that missing DUNE_API_KEY raises ValueError."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.delenv("DUNE_API_KEY", raising=False)
        
        # Use a non-existent .env file path to avoid loading real .env
        with pytest.raises(ValueError, match="DUNE_API_KEY"):
            Settings.from_env("/nonexistent/.env")
    
    def test_from_env_with_dotenv_file(self, monkeypatch):
        """Test loading from a .env file."""
        # Clear environment first
        monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
        monkeypatch.delenv("DUNE_API_KEY", raising=False)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("DISCORD_BOT_TOKEN=file-token\n")
            f.write("DUNE_API_KEY=file-key\n")
            env_path = f.name
        
        try:
            settings = Settings.from_env(env_path)
            assert settings.discord_bot_token == "file-token"
            assert settings.dune_api_key == "file-key"
        finally:
            os.unlink(env_path)


class TestQueryLoading:
    """Test YAML query configuration loading."""
    
    def test_load_queries_from_yaml(self, monkeypatch):
        """Test loading query mappings from YAML file."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        
        yaml_content = {
            "queries": {
                "tvl": {
                    "id": 1234567,
                    "description": "Total Value Locked",
                    "result_type": "table"
                },
                "volume": {
                    "id": 7654321,
                    "description": "Trading Volume",
                    "result_type": "summary",
                    "params": {"days": 7}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            yaml_path = f.name
        
        try:
            # Use a non-existent .env file path to avoid loading real .env
            settings = Settings.from_env("/nonexistent/.env")
            settings.load_queries(yaml_path)
            
            assert len(settings.queries) == 2
            
            tvl = settings.get_query_by_name("tvl")
            assert tvl is not None
            assert tvl.id == 1234567
            assert tvl.description == "Total Value Locked"
            assert tvl.result_type == "table"
            
            volume = settings.get_query_by_name("volume")
            assert volume is not None
            assert volume.id == 7654321
            assert volume.params == {"days": 7}
        finally:
            os.unlink(yaml_path)
    
    def test_load_queries_missing_file(self, monkeypatch):
        """Test that missing YAML file doesn't raise an error."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        
        # Use a non-existent .env file path to avoid loading real .env
        settings = Settings.from_env("/nonexistent/.env")
        settings.load_queries("/nonexistent/path/queries.yaml")
        
        assert settings.queries == {}
    
    def test_load_queries_empty_file(self, monkeypatch):
        """Test loading from empty YAML file."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            yaml_path = f.name
        
        try:
            # Use a non-existent .env file path to avoid loading real .env
            settings = Settings.from_env("/nonexistent/.env")
            settings.load_queries(yaml_path)
            assert settings.queries == {}
        finally:
            os.unlink(yaml_path)
    
    def test_get_query_by_name_not_found(self, monkeypatch):
        """Test get_query_by_name returns None for unknown query."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        
        # Use a non-existent .env file path to avoid loading real .env
        settings = Settings.from_env("/nonexistent/.env")
        
        assert settings.get_query_by_name("nonexistent") is None


class TestDuneQueryConfig:
    """Test DuneQueryConfig dataclass."""
    
    def test_default_values(self):
        """Test default values for DuneQueryConfig."""
        config = DuneQueryConfig(id=12345)
        
        assert config.id == 12345
        assert config.description == ""
        assert config.result_type == "table"
        assert config.params == {}
    
    def test_with_all_values(self):
        """Test DuneQueryConfig with all values specified."""
        config = DuneQueryConfig(
            id=99999,
            description="Test query",
            result_type="summary",
            params={"chain": "ethereum"}
        )
        
        assert config.id == 99999
        assert config.description == "Test query"
        assert config.result_type == "summary"
        assert config.params == {"chain": "ethereum"}


class TestLoadSettings:
    """Test the convenience load_settings function."""
    
    def test_load_settings_convenience(self, monkeypatch):
        """Test load_settings loads both env and queries."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        
        yaml_content = {
            "queries": {
                "test_query": {
                    "id": 111,
                    "description": "Test"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            yaml_path = f.name
        
        try:
            # Use a non-existent .env file path to avoid loading real .env
            settings = load_settings(env_path="/nonexistent/.env", queries_path=yaml_path)
            
            assert settings.discord_bot_token == "test-token"
            assert settings.dune_api_key == "test-key"
            assert "test_query" in settings.queries
        finally:
            os.unlink(yaml_path)


