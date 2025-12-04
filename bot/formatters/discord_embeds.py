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

# Table formatting constants
MAX_COLUMNS_DISPLAY = 8
MAX_COLUMN_WIDTH = 30
MIN_COLUMN_WIDTH = 8


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
        color = discord.Color.from_rgb(88, 101, 242)  # Discord blurple
    
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
    if len(table_text) <= MAX_EMBED_DESCRIPTION - 10:
        embed.description = f"```\n{table_text}\n```"
    else:
        # Truncate and add indicator
        truncated = _truncate(table_text, MAX_EMBED_DESCRIPTION - 30)
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


def format_query_result_rows(
    result: QueryResult,
    title: str = "ALCX DEX Swap",
    color: discord.Color | None = None,
) -> list[discord.Embed]:
    """Format a Dune query result as a list of Discord embeds, one per row.
    
    Each embed represents a single row from the query results, with each column
    displayed as an embed field. This is useful for avoiding rate limits and
    providing better readability for individual records.
    
    Args:
        result: The QueryResult from Dune.
        title: Title for each embed (default: "ALCX DEX Swap").
        color: Optional color for the embeds.
        
    Returns:
        A list of Discord Embeds, one for each row in the result.
    """
    if color is None:
        color = discord.Color.from_rgb(88, 101, 242)  # Discord blurple
    
    if result.is_empty:
        # Return a single embed indicating no results
        embed = discord.Embed(
            title=_truncate(title, MAX_EMBED_TITLE),
            description="*No results returned*",
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text=f"Query ID: {result.query_id} | 0 rows")
        return [embed]
    
    # Define the columns we want to display
    desired_columns = [
        "blockchain",
        "project",
        "block_time",
        "token_bought_symbol",
        "token_sold_symbol",
        "token_bought_amount",
        "token_sold_amount",
        "amount_usd",
        "tx_hash",
    ]
    
    embeds = []
    total_rows = len(result.rows)
    
    for row_index, row in enumerate(result.rows, start=1):
        embed = discord.Embed(
            title=_truncate(title, MAX_EMBED_TITLE),
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        
        # Add each desired column as an embed field
        for column in desired_columns:
            if column in row:
                value = row[column]
                # Format the value for display
                formatted_value = _format_field_value(value)
                
                # Truncate field value if too long
                if len(formatted_value) > MAX_FIELD_VALUE:
                    formatted_value = _truncate(formatted_value, MAX_FIELD_VALUE)
                
                # Use column name as field name (capitalize and replace underscores)
                field_name = column.replace("_", " ").title()
                embed.add_field(
                    name=_truncate(field_name, MAX_FIELD_NAME),
                    value=formatted_value,
                    inline=True,
                )
        
        # Add footer with query ID and row information
        footer_text = f"Query ID: {result.query_id} | Row {row_index} of {total_rows}"
        embed.set_footer(text=footer_text)
        
        embeds.append(embed)
    
    return embeds


def _format_field_value(value: Any) -> str:
    """Format a field value for display in an embed field.
    
    Handles special formatting for dates, numbers, and other types.
    
    Args:
        value: The value to format.
        
    Returns:
        Formatted string representation.
    """
    if value is None:
        return "N/A"
    
    # Handle datetime objects
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    
    # Handle string datetime-like values (common in Dune results)
    if isinstance(value, str):
        # Try to detect and format ISO datetime strings
        if "T" in value or ("-" in value and ":" in value):
            try:
                # Try parsing various datetime formats
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M",
                ]:
                    try:
                        dt = datetime.strptime(value.split("+")[0].split("Z")[0], fmt)
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
            except Exception:
                pass  # Fall through to regular string formatting
    
    # Format numbers with appropriate precision
    if isinstance(value, float):
        # Use 2 decimal places for small numbers, scientific for very large
        if abs(value) < 0.01 and value != 0:
            return f"{value:.2e}"
        elif abs(value) >= 1000000:
            return f"{value:.2e}"
        else:
            return f"{value:.2f}".rstrip("0").rstrip(".")
    
    # Format integers
    if isinstance(value, int):
        return str(value)
    
    # Default: convert to string
    return str(value)


def _format_table(
    rows: list[dict[str, Any]],
    columns: list[str],
    max_rows: int = 25,
) -> str:
    """Format rows as a well-aligned text table with improved styling.
    
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
    display_columns = columns[:MAX_COLUMNS_DISPLAY]
    
    # Calculate column widths with better logic
    col_widths = {}
    for col in display_columns:
        # Start with column name width
        col_widths[col] = max(len(col), MIN_COLUMN_WIDTH)
        
        # Check all row values to determine optimal width
        for row in rows[:max_rows]:
            val = _format_cell_value(row.get(col, ""))
            # Allow more space but cap at MAX_COLUMN_WIDTH
            col_widths[col] = max(
                col_widths[col],
                min(len(val), MAX_COLUMN_WIDTH)
            )
    
    # Build header with better styling
    header_parts = []
    for col in display_columns:
        header_parts.append(col.ljust(col_widths[col]))
    header = " | ".join(header_parts)
    
    # Build separator with proper alignment
    separator_parts = []
    for col in display_columns:
        separator_parts.append("-" * col_widths[col])
    separator = "-+-".join(separator_parts)
    
    # Build rows
    table_rows = [header, separator]
    
    for i, row in enumerate(rows[:max_rows]):
        row_values = []
        for col in display_columns:
            val = _format_cell_value(row.get(col, ""))
            # Truncate if too long
            if len(val) > col_widths[col]:
                val = val[:col_widths[col] - 3] + "..."
            row_values.append(val.ljust(col_widths[col]))
        table_rows.append(" | ".join(row_values))
    
    # Add truncation indicators if needed
    if len(rows) > max_rows:
        table_rows.append(f"\n... and {len(rows) - max_rows} more row(s)")
    
    if len(columns) > len(display_columns):
        table_rows.append(f"(+ {len(columns) - len(display_columns)} more column(s) hidden)")
    
    return "\n".join(table_rows)


def _format_cell_value(value: Any) -> str:
    """Format a cell value for display in the table.
    
    Handles special formatting for dates, numbers, and other types.
    
    Args:
        value: The value to format.
        
    Returns:
        Formatted string representation.
    """
    if value is None:
        return ""
    
    # Handle datetime objects
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    
    # Handle string datetime-like values (common in Dune results)
    if isinstance(value, str):
        # Try to detect and format ISO datetime strings
        if "T" in value or ("-" in value and ":" in value):
            try:
                # Try parsing various datetime formats
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M",
                ]:
                    try:
                        dt = datetime.strptime(value.split("+")[0].split("Z")[0], fmt)
                        return dt.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        continue
            except Exception:
                pass  # Fall through to regular string formatting
    
    # Format numbers with appropriate precision
    if isinstance(value, float):
        # Use 2 decimal places for small numbers, scientific for very large
        if abs(value) < 0.01 and value != 0:
            return f"{value:.2e}"
        elif abs(value) >= 1000000:
            return f"{value:.2e}"
        else:
            return f"{value:.2f}".rstrip("0").rstrip(".")
    
    # Default: convert to string
    return str(value)


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

