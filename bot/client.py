"""Discord bot client setup.

Provides the main Discord bot client with slash command support.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.config import Settings
from bot.utils.logging import get_logger, setup_logging
from bot.services.dune_client import DuneClient
from bot.services.scheduler import ScheduledQueryRunner


logger = get_logger("client")


class DuneBot(commands.Bot):
    """Main Discord bot class for Dune Analytics integration.
    
    This bot supports slash commands for querying Dune Analytics
    and displaying results in Discord.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the bot.
        
        Args:
            settings: Application settings containing tokens and config.
        """
        # Set up intents - we only need basic intents for slash commands
        intents = discord.Intents.default()
        intents.message_content = False  # Not needed for slash commands
        
        super().__init__(
            command_prefix="!",  # Fallback prefix, mainly using slash commands
            intents=intents,
            help_command=None,  # We'll use slash commands instead
        )
        
        self.settings = settings
        self._guild_id = settings.discord_guild_id
        self._scheduler: ScheduledQueryRunner | None = None
    
    async def setup_hook(self) -> None:
        """Called when the bot is starting up.
        
        This is where we sync slash commands with Discord.
        """
        logger.info("Setting up bot...")
        
        # Load command cogs/extensions here
        # await self.load_extension("bot.commands.dune_queries")
        
        # Sync commands
        if self._guild_id:
            # Sync to specific guild for faster updates during development
            guild = discord.Object(id=self._guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced commands to guild {self._guild_id}")
        else:
            # Sync globally (can take up to an hour to propagate)
            await self.tree.sync()
            logger.info("Synced commands globally")
    
    async def on_ready(self) -> None:
        """Called when the bot is fully connected and ready."""
        logger.info(f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Dune Analytics"
        )
        await self.change_presence(activity=activity)
        
        # Start scheduler if configured
        if (
            self.settings.scheduled_query_id
            and self.settings.scheduled_execution_time
            and self.settings.discord_channel_id
        ):
            dune_client = DuneClient(api_key=self.settings.dune_api_key)
            self._scheduler = ScheduledQueryRunner(
                dune_client=dune_client,
                bot=self,
                query_id=self.settings.scheduled_query_id,
                execution_time=self.settings.scheduled_execution_time,
                channel_id=self.settings.discord_channel_id,
                embed_delay_seconds=self.settings.embed_delay_seconds,
                sums_query_id=self.settings.alcx_sums_query_id,
            )
            self._scheduler.start()
            logger.info("Scheduled query runner started")
    
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError
    ) -> None:
        """Global error handler for prefix commands."""
        logger.error(f"Command error: {error}", exc_info=error)
        
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        await ctx.send(f"An error occurred: {error}")


def create_bot(settings: Settings) -> DuneBot:
    """Create and configure the Discord bot.
    
    Args:
        settings: Application settings.
        
    Returns:
        Configured DuneBot instance.
    """
    bot = DuneBot(settings)
    
    # Register the /ping command directly on the bot's command tree
    @bot.tree.command(name="ping", description="Check if the bot is responsive")
    async def ping(interaction: discord.Interaction) -> None:
        """Health check command."""
        latency_ms = round(bot.latency * 1000)
        await interaction.response.send_message(
            f"🏓 Pong! Latency: {latency_ms}ms",
            ephemeral=True
        )
    
    # Register the /status command
    @bot.tree.command(name="status", description="Check bot status and scheduled query info")
    async def status(interaction: discord.Interaction) -> None:
        """Status check command."""
        status_info = []
        status_info.append(f"**Bot Status:** Online")
        status_info.append(f"**Latency:** {round(bot.latency * 1000)}ms")
        status_info.append(f"**Guilds:** {len(bot.guilds)}")
        
        if bot._scheduler:
            scheduler_status = bot._scheduler.get_status()
            status_info.append(f"\n**Scheduled Query:**")
            status_info.append(f"- Query ID: {scheduler_status['query_id']}")
            status_info.append(f"- Execution Time: {scheduler_status['execution_time']}")
            status_info.append(f"- Channel ID: {scheduler_status['channel_id']}")
            if scheduler_status['last_execution']:
                status_info.append(f"- Last Execution: {scheduler_status['last_execution']}")
            if scheduler_status['next_execution']:
                status_info.append(f"- Next Execution: {scheduler_status['next_execution']}")
            status_info.append(f"- Running: {scheduler_status['running']}")
        else:
            status_info.append(f"\n**Scheduled Query:** Not configured")
        
        await interaction.response.send_message(
            "\n".join(status_info),
            ephemeral=True
        )
    
    return bot


async def run_bot(settings: Settings) -> None:
    """Run the Discord bot.
    
    Args:
        settings: Application settings containing the bot token.
    """
    # Set up logging
    setup_logging()
    
    logger.info("Starting Dune Discord Bot...")
    
    bot = create_bot(settings)
    
    try:
        await bot.start(settings.discord_bot_token)
    except discord.LoginFailure:
        logger.error("Failed to login - check your DISCORD_BOT_TOKEN")
        raise
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        raise
    finally:
        # Stop scheduler if running
        if bot._scheduler:
            bot._scheduler.stop()
        
        if not bot.is_closed():
            await bot.close()

