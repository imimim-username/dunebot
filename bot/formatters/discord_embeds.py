"""Discord embed formatters for Dune query results.

Provides functions to format Dune query results as Discord embeds
with proper truncation for large results.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import discord

from bot.services.dune_client import QueryResult
from bot.utils.logging import get_logger


logger = get_logger("formatters")

# Discord embed limits
MAX_EMBED_TITLE = 256
MAX_EMBED_DESCRIPTION = 4096
MAX_FIELD_NAME = 256
MAX_FIELD_VALUE = 1024
MAX_TOTAL_EMBED = 6000
MAX_FIELDS = 25


def format_query_result(
    result: QueryResult,
    title: str | None = None,
    color: discord.Color | None = None,
) -> discord.Embed:
    """Format a Dune query result as a Discord embed.
    
    Args:
        result: The QueryResult from Dune.
        title: Optional custom title for the embed.
        color: Optional color for the embed.
        
    Returns:
        A Discord Embed with the formatted results.
    """
    if color is None:
        color = discord.Color.blue()
    
    if title is None:
        title = f"Dune Query #{result.query_id}"
    
    embed = discord.Embed(
        title=_truncate(title, MAX_EMBED_TITLE),
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    
    if result.is_empty:
        embed.description = "*No results returned*"
        embed.set_footer(text=f"Query ID: {result.query_id} | 0 rows")
        return embed
    
    # Format the data as a table-like structure
    table_text = _format_table(result.rows, result.column_names)
    
    # Check if we need to truncate
    if len(table_text) <= MAX_EMBED_DESCRIPTION:
        embed.description = f"```\n{table_text}\n```"
    else:
        # Truncate and add indicator
        truncated = _truncate(table_text, MAX_EMBED_DESCRIPTION - 20)
        embed.description = f"```\n{truncated}\n...(truncated)\n```"
    
    # Add footer with metadata
    footer_text = f"Query ID: {result.query_id} | {result.row_count} row(s)"
    if result.row_count > len(result.rows):
        footer_text += " (showing partial)"
    embed.set_footer(text=footer_text)
    
    return embed


def format_error_embed(
    error_message: str,
    query_id: int | None = None,
    title: str = "Query Error",
) -> discord.Embed:
    """Format an error message as a Discord embed.
    
    Args:
        error_message: The error message to display.
        query_id: Optional query ID for context.
        title: Title for the error embed.
        
    Returns:
        A Discord Embed with the error information.
    """
    embed = discord.Embed(
        title=f"❌ {title}",
        description=_truncate(error_message, MAX_EMBED_DESCRIPTION),
        color=discord.Color.red(),
        timestamp=datetime.now(timezone.utc),
    )
    
    if query_id is not None:
        embed.set_footer(text=f"Query ID: {query_id}")
    
    return embed


def format_loading_embed(query_id: int) -> discord.Embed:
    """Format a loading/in-progress embed.
    
    Args:
        query_id: The query ID being executed.
        
    Returns:
        A Discord Embed indicating the query is running.
    """
    return discord.Embed(
        title="⏳ Executing Query...",
        description=f"Running Dune query #{query_id}\nThis may take up to 60 seconds.",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc),
    )


def _format_table(
    rows: list[dict[str, Any]],
    columns: list[str],
    max_rows: int = 20,
) -> str:
    """Format rows as a simple text table.
    
    Args:
        rows: List of row dictionaries.
        columns: List of column names.
        max_rows: Maximum number of rows to include.
        
    Returns:
        Formatted table string.
    """
    if not rows or not columns:
        return "No data"
    
    # Limit columns to avoid overly wide tables
    display_columns = columns[:6]  # Max 6 columns
    
    # Calculate column widths
    col_widths = {}
    for col in display_columns:
        col_widths[col] = len(col)
        for row in rows[:max_rows]:
            val = str(row.get(col, ""))
            col_widths[col] = max(col_widths[col], min(len(val), 20))
    
    # Build header
    header = " | ".join(
        col[:col_widths[col]].ljust(col_widths[col])
        for col in display_columns
    )
    separator = "-+-".join("-" * col_widths[col] for col in display_columns)
    
    # Build rows
    table_rows = [header, separator]
    
    for i, row in enumerate(rows[:max_rows]):
        row_values = []
        for col in display_columns:
            val = str(row.get(col, ""))
            if len(val) > col_widths[col]:
                val = val[:col_widths[col] - 2] + ".."
            row_values.append(val.ljust(col_widths[col]))
        table_rows.append(" | ".join(row_values))
    
    # Add truncation indicator if needed
    if len(rows) > max_rows:
        table_rows.append(f"... and {len(rows) - max_rows} more row(s)")
    
    if len(columns) > len(display_columns):
        table_rows.append(f"(+ {len(columns) - len(display_columns)} more columns)")
    
    return "\n".join(table_rows)


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to maximum length.
    
    Args:
        text: Text to truncate.
        max_length: Maximum allowed length.
        
    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

