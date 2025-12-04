"""Tests for logging utilities."""

import logging
import tempfile
from pathlib import Path

import pytest
import yaml

from bot.utils.logging import (
    setup_logging,
    get_logger,
    LoggerMixin,
    DEFAULT_FORMAT,
)


class TestSetupLogging:
    """Test logging setup functionality."""
    
    def test_setup_basic_logging(self):
        """Test basic logging setup without config file."""
        logger = setup_logging(
            config_path="/nonexistent/path.yaml",
            level=logging.DEBUG
        )
        
        assert logger is not None
        assert logger.name == "bot"
    
    def test_setup_logging_with_yaml(self):
        """Test logging setup from YAML config file."""
        yaml_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout"
                }
            },
            "root": {
                "level": "DEBUG",
                "handlers": ["console"]
            }
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            yaml.dump(yaml_config, f)
            config_path = f.name
        
        try:
            logger = setup_logging(config_path=config_path)
            assert logger is not None
        finally:
            Path(config_path).unlink()
    
    def test_setup_logging_with_file_handler(self):
        """Test logging setup with file handler creates directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "logs" / "test.log"
            
            yaml_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "handlers": {
                    "file": {
                        "class": "logging.FileHandler",
                        "level": "DEBUG",
                        "filename": str(log_file)
                    }
                },
                "root": {
                    "level": "DEBUG",
                    "handlers": ["file"]
                }
            }
            
            config_file = Path(tmpdir) / "logging.yaml"
            with open(config_file, "w") as f:
                yaml.dump(yaml_config, f)
            
            # This should create the logs directory
            setup_logging(config_path=config_file)
            
            # Log something to trigger file creation
            logging.getLogger().info("Test message")
    
    def test_setup_logging_level_string(self):
        """Test that string log levels work."""
        logger = setup_logging(
            config_path="/nonexistent/path.yaml",
            level="DEBUG"
        )
        
        assert logger is not None


class TestGetLogger:
    """Test get_logger function."""
    
    def test_get_logger_with_prefix(self):
        """Test get_logger adds 'bot.' prefix."""
        logger = get_logger("commands")
        assert logger.name == "bot.commands"
    
    def test_get_logger_already_prefixed(self):
        """Test get_logger doesn't double-prefix."""
        logger = get_logger("bot.services")
        assert logger.name == "bot.services"
    
    def test_get_logger_similar_prefix(self):
        """Test get_logger correctly prefixes names that start with 'bot' but not 'bot.'"""
        # Names like "botnet" or "bot_helpers" should still get the "bot." prefix
        logger = get_logger("botnet")
        assert logger.name == "bot.botnet"
        
        logger2 = get_logger("bot_helpers")
        assert logger2.name == "bot.bot_helpers"
    
    def test_get_logger_returns_logger_instance(self):
        """Test get_logger returns a Logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)


class TestLoggerMixin:
    """Test LoggerMixin class."""
    
    def test_mixin_provides_logger(self):
        """Test that LoggerMixin provides a logger property."""
        
        class TestClass(LoggerMixin):
            pass
        
        obj = TestClass()
        logger = obj.logger
        
        assert isinstance(logger, logging.Logger)
        assert "bot" in logger.name
    
    def test_mixin_logger_can_log(self, caplog):
        """Test that the mixin logger can actually log messages."""
        
        class TestClass(LoggerMixin):
            def do_something(self):
                self.logger.info("Test log message")
        
        obj = TestClass()
        
        with caplog.at_level(logging.INFO):
            obj.do_something()
        
        assert "Test log message" in caplog.text

