"""Logging utilities for Dune Discord Bot.

Provides standardized logging setup with optional YAML configuration.
"""

from __future__ import annotations

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

import yaml

from bot.config import PROJECT_ROOT, CONFIG_DIR


# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    config_path: Path | str | None = None,
    level: int | str = logging.INFO,
    log_to_file: bool = False,
) -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        config_path: Optional path to logging.yaml config file.
                    If None, uses default location or falls back to basic config.
        level: Default log level if no config file is found.
        log_to_file: Whether to also log to a file (only used with basic config).
        
    Returns:
        The root logger for the bot.
    """
    if config_path is None:
        config_path = CONFIG_DIR / "logging.yaml"
    
    config_path = Path(config_path)
    
    if config_path.exists():
        _setup_from_yaml(config_path)
    else:
        _setup_basic_logging(level, log_to_file)
    
    return logging.getLogger("bot")


def _setup_from_yaml(config_path: Path) -> None:
    """Set up logging from YAML configuration file.
    
    Args:
        config_path: Path to the logging.yaml file.
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f) or {}
    
    # Ensure log directory exists if file handler is configured
    _ensure_log_directories(config)
    
    # Only apply config if it has the required 'version' key
    if config.get("version"):
        logging.config.dictConfig(config)


def _ensure_log_directories(config: dict[str, Any]) -> None:
    """Ensure directories exist for any file handlers.
    
    Args:
        config: The logging configuration dictionary.
    """
    handlers = config.get("handlers", {})
    
    for handler_config in handlers.values():
        if not isinstance(handler_config, dict):
            continue
            
        filename = handler_config.get("filename")
        if filename:
            log_path = PROJECT_ROOT / filename
            log_path.parent.mkdir(parents=True, exist_ok=True)
            # Update config to use absolute path
            handler_config["filename"] = str(log_path)


def _setup_basic_logging(level: int | str, log_to_file: bool) -> None:
    """Set up basic logging without YAML configuration.
    
    Args:
        level: The logging level.
        log_to_file: Whether to also log to a file.
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    handlers: list[logging.Handler] = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)
    )
    handlers.append(console_handler)
    
    # File handler (optional)
    if log_to_file:
        log_dir = PROJECT_ROOT / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / "bot.log",
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)
        )
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("dune_client").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name, prefixed with 'bot'.
    
    Args:
        name: The logger name (will be prefixed with 'bot.' if not already).
        
    Returns:
        A configured logger instance.
    """
    if not name.startswith("bot."):
        name = f"bot.{name}"
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class that provides a logger property.
    
    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.logger.info("Something happened")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get a logger for this class."""
        return get_logger(self.__class__.__module__)
