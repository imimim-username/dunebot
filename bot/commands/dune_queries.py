"""Dune query commands for the Discord bot.

Provides slash commands for executing Dune Analytics queries
and displaying results.
"""

from __future__ import annotations

import asyncio

import discord
from discord import app_commands

from bot.services.dune_client import (
    DuneClient,
    DuneQueryError,
    DuneTimeoutError,
)
from bot.formatters.discord_embeds import (
    format_query_result_rows,
    format_error_embed,
)
from bot.utils.logging import get_logger


logger = get_logger("commands.dune")


class DuneCommands:
    """Dune query command handlers.
    
    This class provides methods that can be registered as slash commands
    for the Discord bot.
    """
    
    def __init__(self, dune_client: DuneClient, embed_delay_seconds: int = 10):
        """Initialize the Dune commands.
        
        Args:
            dune_client: The Dune client for executing queries.
            embed_delay_seconds: Delay in seconds between sending embeds (default: 10).
        """
        self.dune_client = dune_client
        self.embed_delay_seconds = embed_delay_seconds
    
    async def execute_query(
        self,
        interaction: discord.Interaction,
        query_id: int,
    ) -> None:
        """Execute a Dune query and display results.
        
        Args:
            interaction: The Discord interaction.
            query_id: The Dune query ID to execute.
        """
        logger.info(f"User {interaction.user} executing query {query_id}")
        
        # Defer the response since queries can take time
        await interaction.response.defer(thinking=True)
        
        try:
            # Execute the query asynchronously
            result = await self.dune_client.execute_query_async(
                query_id=query_id,
                timeout=60,
            )
            
            # Format results as multiple embeds (one per row)
            embeds = format_query_result_rows(result)
            
            if not embeds:
                # This shouldn't happen, but handle it gracefully
                await interaction.followup.send(
                    content="Query completed but no results to display."
                )
                return
            
            # Send embeds with delay between them
            if len(embeds) > 1:
                # Send progress message first
                await interaction.followup.send(
                    content=f"*Sending {len(embeds)} results with {self.embed_delay_seconds}s delay between each...*"
                )
                
                # Send all embeds with delay
                for i, embed in enumerate(embeds, start=1):
                    if i > 1:  # Wait before sending (except for the first one)
                        await asyncio.sleep(self.embed_delay_seconds)
                    try:
                        await interaction.followup.send(embed=embed)
                    except Exception as e:
                        logger.error(
                            f"Error sending embed {i}/{len(embeds)} for query {query_id}: {e}"
                        )
                        # Continue sending remaining embeds even if one fails
            else:
                # Single embed, send it normally
                await interaction.followup.send(embed=embeds[0])
            
            logger.info(
                f"Query {query_id} completed with {result.row_count} rows "
                f"({len(embeds)} embeds) for user {interaction.user}"
            )
            
        except DuneTimeoutError as e:
            logger.warning(f"Query {query_id} timed out: {e}")
            embed = format_error_embed(
                "The query timed out. This usually happens with complex queries. "
                "Try again later or check the query on Dune directly.",
                query_id=query_id,
                title="Query Timeout",
            )
            await interaction.followup.send(embed=embed)
            
        except DuneQueryError as e:
            logger.error(f"Query {query_id} failed: {e}")
            embed = format_error_embed(
                str(e),
                query_id=query_id,
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.exception(f"Unexpected error executing query {query_id}")
            embed = format_error_embed(
                "An unexpected error occurred. Please try again later.",
                query_id=query_id,
            )
            await interaction.followup.send(embed=embed)
    
    async def get_latest_results(
        self,
        interaction: discord.Interaction,
        query_id: int,
    ) -> None:
        """Get the latest cached results for a query.
        
        Args:
            interaction: The Discord interaction.
            query_id: The Dune query ID.
        """
        logger.info(f"User {interaction.user} fetching latest results for {query_id}")
        
        await interaction.response.defer(thinking=True)
        
        try:
            result = await self.dune_client.get_latest_results_async(query_id)
            
            # Format results as multiple embeds (one per row)
            embeds = format_query_result_rows(result)
            
            if not embeds:
                # This shouldn't happen, but handle it gracefully
                await interaction.followup.send(
                    content="Query completed but no results to display."
                )
                return
            
            # Send embeds with delay between them
            if len(embeds) > 1:
                # Send progress message first
                await interaction.followup.send(
                    content=f"*Sending {len(embeds)} results with {self.embed_delay_seconds}s delay between each...*"
                )
                
                # Send all embeds with delay
                for i, embed in enumerate(embeds, start=1):
                    if i > 1:  # Wait before sending (except for the first one)
                        await asyncio.sleep(self.embed_delay_seconds)
                    try:
                        await interaction.followup.send(embed=embed)
                    except Exception as e:
                        logger.error(
                            f"Error sending embed {i}/{len(embeds)} for query {query_id}: {e}"
                        )
                        # Continue sending remaining embeds even if one fails
            else:
                # Single embed, send it normally
                await interaction.followup.send(embed=embeds[0])
            
        except DuneQueryError as e:
            logger.error(f"Failed to get latest results for {query_id}: {e}")
            embed = format_error_embed(
                str(e),
                query_id=query_id,
            )
            await interaction.followup.send(embed=embed)


def register_dune_commands(
    tree: app_commands.CommandTree,
    dune_client: DuneClient,
    embed_delay_seconds: int = 10,
) -> DuneCommands:
    """Register Dune commands on the command tree.
    
    Args:
        tree: The Discord command tree to register commands on.
        dune_client: The Dune client for executing queries.
        embed_delay_seconds: Delay in seconds between sending embeds (default: 10).
        
    Returns:
        The DuneCommands instance.
    """
    commands = DuneCommands(dune_client, embed_delay_seconds=embed_delay_seconds)
    
    @tree.command(
        name="dune",
        description="Execute a Dune Analytics query by ID"
    )
    @app_commands.describe(
        query_id="The Dune query ID (found in the URL of your query)"
    )
    async def dune_command(
        interaction: discord.Interaction,
        query_id: int,
    ) -> None:
        """Execute a Dune query."""
        await commands.execute_query(interaction, query_id)
    
    @tree.command(
        name="dune_latest",
        description="Get the latest cached results for a Dune query"
    )
    @app_commands.describe(
        query_id="The Dune query ID"
    )
    async def dune_latest_command(
        interaction: discord.Interaction,
        query_id: int,
    ) -> None:
        """Get latest cached results."""
        await commands.get_latest_results(interaction, query_id)
    
    logger.info("Dune commands registered")
    return commands


