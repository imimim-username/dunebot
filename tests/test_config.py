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
        
        settings = Settings.from_env()
        
        assert settings.discord_bot_token == "test-token-123"
        assert settings.dune_api_key == "test-dune-key-456"
        assert settings.discord_guild_id is None
    
    def test_from_env_with_optional_guild_id(self, monkeypatch):
        """Test loading settings with optional guild ID."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        monkeypatch.setenv("DISCORD_GUILD_ID", "123456789")
        
        settings = Settings.from_env()
        
        assert settings.discord_guild_id == 123456789
    
    def test_from_env_missing_discord_token(self, monkeypatch):
        """Test that missing DISCORD_BOT_TOKEN raises ValueError."""
        monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        
        with pytest.raises(ValueError, match="DISCORD_BOT_TOKEN"):
            Settings.from_env()
    
    def test_from_env_missing_dune_key(self, monkeypatch):
        """Test that missing DUNE_API_KEY raises ValueError."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.delenv("DUNE_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="DUNE_API_KEY"):
            Settings.from_env()
    
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
            settings = Settings.from_env()
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
        
        settings = Settings.from_env()
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
            settings = Settings.from_env()
            settings.load_queries(yaml_path)
            assert settings.queries == {}
        finally:
            os.unlink(yaml_path)
    
    def test_get_query_by_name_not_found(self, monkeypatch):
        """Test get_query_by_name returns None for unknown query."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
        monkeypatch.setenv("DUNE_API_KEY", "test-key")
        
        settings = Settings.from_env()
        
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
            settings = load_settings(queries_path=yaml_path)
            
            assert settings.discord_bot_token == "test-token"
            assert settings.dune_api_key == "test-key"
            assert "test_query" in settings.queries
        finally:
            os.unlink(yaml_path)

