"""Dune query commands for the Discord bot.

Provides slash commands for executing Dune Analytics queries
and displaying results.
"""

from __future__ import annotations

import discord
from discord import app_commands

from bot.services.dune_client import (
    DuneClient,
    DuneQueryError,
    DuneTimeoutError,
)
from bot.formatters.discord_embeds import (
    format_query_result,
    format_error_embed,
)
from bot.utils.logging import get_logger


logger = get_logger("commands.dune")


class DuneCommands:
    """Dune query command handlers.
    
    This class provides methods that can be registered as slash commands
    for the Discord bot.
    """
    
    def __init__(self, dune_client: DuneClient):
        """Initialize the Dune commands.
        
        Args:
            dune_client: The Dune client for executing queries.
        """
        self.dune_client = dune_client
    
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
            
            # Format and send the result
            embed = format_query_result(result)
            await interaction.followup.send(embed=embed)
            
            logger.info(
                f"Query {query_id} completed with {result.row_count} rows "
                f"for user {interaction.user}"
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
            
            embed = format_query_result(
                result,
                title=f"Latest Results: Query #{query_id}",
            )
            await interaction.followup.send(embed=embed)
            
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
) -> DuneCommands:
    """Register Dune commands on the command tree.
    
    Args:
        tree: The Discord command tree to register commands on.
        dune_client: The Dune client for executing queries.
        
    Returns:
        The DuneCommands instance.
    """
    commands = DuneCommands(dune_client)
    
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

