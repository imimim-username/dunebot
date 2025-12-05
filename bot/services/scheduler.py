"""Scheduled query execution scheduler.

Provides functionality to execute Dune queries on a 24-hour schedule.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING

from bot.utils.logging import get_logger

if TYPE_CHECKING:
    import discord

    from bot.services.dune_client import DuneClient

logger = get_logger("services.scheduler")


class ScheduledQueryRunner:
    """Manages scheduled execution of Dune queries.
    
    Executes a query every 24 hours at a specified local time and posts
    results to a Discord channel.
    """
    
    def __init__(
        self,
        dune_client: DuneClient,
        bot: discord.Client,
        query_id: int,
        execution_time: str,  # HH:MM format
        channel_id: int,
        embed_delay_seconds: int = 10,
        sums_query_id: int | None = None,
    ):
        """Initialize the scheduled query runner.
        
        Args:
            dune_client: The Dune client for executing queries.
            bot: The Discord bot client.
            query_id: The Dune query ID to execute.
            execution_time: Local time to execute (HH:MM format, 24-hour).
            channel_id: Discord channel ID to post results to.
            embed_delay_seconds: Delay between sending embeds (default: 10).
            sums_query_id: Optional query ID for 24h ALCX buy/sell totals.
        """
        self.dune_client = dune_client
        self.bot = bot
        self.query_id = query_id
        self.execution_time = execution_time
        self.channel_id = channel_id
        self.embed_delay_seconds = embed_delay_seconds
        self.sums_query_id = sums_query_id
        
        # Parse execution time
        time_parts = execution_time.split(":")
        self.execution_hour = int(time_parts[0])
        self.execution_minute = int(time_parts[1])
        
        self._task: asyncio.Task | None = None
        self._last_execution: datetime | None = None
        self._next_execution: datetime | None = None
        self._running = False
    
    def start(self) -> None:
        """Start the scheduler task."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info(
            f"Scheduled query runner started: query_id={self.query_id}, "
            f"time={self.execution_time}, channel_id={self.channel_id}"
        )
    
    def stop(self) -> None:
        """Stop the scheduler task."""
        self._running = False
        if self._task:
            self._task.cancel()
            logger.info("Scheduled query runner stopped")
    
    def get_status(self) -> dict[str, str | None]:
        """Get current scheduler status.
        
        Returns:
            Dictionary with status information.
        """
        return {
            "query_id": str(self.query_id),
            "execution_time": self.execution_time,
            "channel_id": str(self.channel_id),
            "last_execution": (
                self._last_execution.isoformat() if self._last_execution else None
            ),
            "next_execution": (
                self._next_execution.isoformat() if self._next_execution else None
            ),
            "running": str(self._running),
        }
    
    async def _run_scheduler(self) -> None:
        """Main scheduler loop."""
        try:
            while self._running:
                # Calculate next execution time
                next_time = self._calculate_next_execution()
                self._next_execution = next_time
                
                # Wait until execution time
                wait_seconds = (next_time - datetime.now()).total_seconds()
                logger.info(
                    f"Next scheduled execution at {next_time.isoformat()} "
                    f"(in {wait_seconds:.0f} seconds)"
                )
                
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                
                # Execute query if still running
                if self._running:
                    await self._execute_query()
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled")
        except Exception as e:
            logger.exception(f"Scheduler error: {e}")
            self._running = False
    
    def _calculate_next_execution(self) -> datetime:
        """Calculate the next execution time.
        
        Returns:
            Next execution datetime.
        """
        now = datetime.now()
        execution_time = time(self.execution_hour, self.execution_minute)
        
        # Try today first
        next_execution = datetime.combine(now.date(), execution_time)
        
        # If time has passed today, schedule for tomorrow
        if next_execution <= now:
            next_execution += timedelta(days=1)
        
        return next_execution
    
    async def _execute_query(self) -> None:
        """Execute the scheduled query and post results."""
        logger.info(f"Executing scheduled query {self.query_id}")
        self._last_execution = datetime.now()
        
        try:
            # Get the channel
            channel = self.bot.get_channel(self.channel_id)
            if channel is None:
                logger.error(f"Channel {self.channel_id} not found")
                return
            
            # Execute the query
            result = await self.dune_client.execute_query_async(
                query_id=self.query_id,
                timeout=60,
            )
            
            # Format results as multiple embeds (one per row)
            from bot.formatters.discord_embeds import format_query_result_rows
            
            embeds = format_query_result_rows(result)
            
            if not embeds:
                await channel.send("Query completed but no results to display.")
                return
            
            # Send embeds with delay between them
            if len(embeds) > 1:
                # Send progress message first
                await channel.send(
                    f"*Sending {len(embeds)} results with {self.embed_delay_seconds}s delay between each...*"
                )
                
                # Send all embeds with delay
                for i, embed in enumerate(embeds, start=1):
                    if i > 1:  # Wait before sending (except for the first one)
                        await asyncio.sleep(self.embed_delay_seconds)
                    try:
                        await channel.send(embed=embed)
                    except Exception as e:
                        logger.error(
                            f"Error sending embed {i}/{len(embeds)} for query {self.query_id}: {e}"
                        )
                        # Continue sending remaining embeds even if one fails
            else:
                # Single embed, send it normally
                await channel.send(embed=embeds[0])
            
            logger.info(
                f"Scheduled query {self.query_id} completed with {result.row_count} rows "
                f"({len(embeds)} embeds)"
            )
            
            # Execute ALCX sums query if configured
            if self.sums_query_id:
                await self._execute_sums_query(channel)
            
        except Exception as e:
            logger.exception(f"Error executing scheduled query {self.query_id}: {e}")
            
            # Send error embed to channel
            try:
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    from bot.formatters.discord_embeds import format_error_embed
                    
                    error_embed = format_error_embed(
                        f"Error executing scheduled query: {str(e)}",
                        query_id=self.query_id,
                        title="Scheduled Query Error",
                    )
                    await channel.send(embed=error_embed)
            except Exception as send_error:
                logger.error(f"Failed to send error embed: {send_error}")
    
    async def _execute_sums_query(self, channel) -> None:
        """Execute the ALCX sums query and post results.
        
        Args:
            channel: The Discord channel to post results to.
        """
        logger.info(f"Executing ALCX sums query {self.sums_query_id}")
        
        try:
            # Execute the sums query
            result = await self.dune_client.execute_query_async(
                query_id=self.sums_query_id,
                timeout=60,
            )
            
            # Format and send the sums embed
            from bot.formatters.discord_embeds import format_alcx_sums_embed
            
            sums_embed = format_alcx_sums_embed(result)
            await channel.send(embed=sums_embed)
            
            logger.info(f"ALCX sums query {self.sums_query_id} completed")
            
        except Exception as e:
            logger.exception(f"Error executing ALCX sums query {self.sums_query_id}: {e}")
            
            # Send error embed
            try:
                from bot.formatters.discord_embeds import format_error_embed
                
                error_embed = format_error_embed(
                    f"Error executing ALCX sums query: {str(e)}",
                    query_id=self.sums_query_id,
                    title="ALCX Sums Query Error",
                )
                await channel.send(embed=error_embed)
            except Exception as send_error:
                logger.error(f"Failed to send sums error embed: {send_error}")



