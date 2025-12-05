"""Entry point for running the Dune Discord Bot.

Usage:
    python -m scripts.run_bot
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.config import load_settings
from bot.client import run_bot
from bot.utils.logging import setup_logging, get_logger


def main() -> None:
    """Main entry point for the bot."""
    # Set up logging first
    setup_logging()
    logger = get_logger("main")
    
    try:
        # Load settings from environment
        logger.info("Loading configuration...")
        settings = load_settings()
        logger.info("Configuration loaded successfully")
        
        # Run the bot
        asyncio.run(run_bot(settings))
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nConfiguration error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        print("See .env.example for reference.")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\nBot stopped.")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()




