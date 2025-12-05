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

# Blockchain explorer URLs
BLOCKCHAIN_EXPLORERS = {
    "ethereum": "https://etherscan.io/tx/",
    "optimism": "https://optimistic.etherscan.io/tx/",
    "arbitrum": "https://arbiscan.io/tx/",
}


def _format_discord_timestamp(block_time: str | datetime | None) -> str:
    """Convert a UTC datetime to Discord's timestamp format for local time display.
    
    Discord's timestamp format <t:UNIX:f> displays the time in each user's local
    timezone automatically.
    
    Args:
        block_time: UTC datetime string (ISO format), datetime object,
                    pandas Timestamp, or numpy datetime64.
        
    Returns:
        Discord timestamp string like "<t:1704110400:f>" or "N/A" if parsing fails.
    """
    if block_time is None:
        return "N/A"
    
    # Handle pandas Timestamp (has .timestamp() method and isn't a plain datetime)
    # Check this before datetime since pandas.Timestamp inherits from datetime
    if hasattr(block_time, 'timestamp') and not isinstance(block_time, datetime):
        try:
            unix_ts = int(block_time.timestamp())
            return f"<t:{unix_ts}:f>"
        except (ValueError, TypeError, OSError):
            pass
    
    # Handle numpy datetime64 (has .astype() method)
    if hasattr(block_time, 'astype') and not isinstance(block_time, (datetime, str)):
        try:
            # Convert numpy datetime64 to unix timestamp
            unix_ts = int(block_time.astype('datetime64[s]').astype('int64'))
            return f"<t:{unix_ts}:f>"
        except (ValueError, TypeError):
            pass
    
    # If already a datetime object (includes pandas.Timestamp which inherits from datetime)
    if isinstance(block_time, datetime):
        # Ensure it's UTC
        if block_time.tzinfo is None:
            block_time = block_time.replace(tzinfo=timezone.utc)
        unix_ts = int(block_time.timestamp())
        return f"<t:{unix_ts}:f>"
    
    # Parse string datetime
    if isinstance(block_time, str):
        # Try various datetime formats
        for fmt in [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M",
        ]:
            try:
                # Remove timezone suffix if present (handles " UTC", "+00:00", "Z")
                clean_time = block_time.replace(" UTC", "").split("+")[0].split("Z")[0]
                dt = datetime.strptime(clean_time, fmt)
                dt = dt.replace(tzinfo=timezone.utc)
                unix_ts = int(dt.timestamp())
                return f"<t:{unix_ts}:f>"
            except ValueError:
                continue
    
    return "N/A"


def _format_tx_link(blockchain: str | None, tx_hash: str | None) -> str:
    """Format a transaction hash as a clickable link based on blockchain.
    
    Args:
        blockchain: The blockchain name (ethereum, optimism, arbitrum).
        tx_hash: The transaction hash.
        
    Returns:
        Markdown link like "[0x1234...](https://etherscan.io/tx/0x...)" or "unknown".
    """
    if tx_hash is None:
        return "unknown"
    
    if blockchain is None:
        return "unknown"
    
    # Normalize blockchain name to lowercase
    blockchain_lower = blockchain.lower()
    
    if blockchain_lower in BLOCKCHAIN_EXPLORERS:
        url = f"{BLOCKCHAIN_EXPLORERS[blockchain_lower]}{tx_hash}"
        return f"[{tx_hash}]({url})"
    
    return "unknown"


def _format_alcx_amount(row: dict[str, Any]) -> tuple[str | None, str | None]:
    """Determine ALCX amount display based on token symbols.
    
    Priority: ALCX Sold takes precedence if both bought and sold are ALCX.
    
    Args:
        row: The row dictionary containing token symbols and amounts.
        
    Returns:
        Tuple of (field_name, formatted_amount) or (None, None) if no ALCX.
    """
    token_sold_symbol = row.get("token_sold_symbol")
    token_bought_symbol = row.get("token_bought_symbol")
    
    # ALCX Sold takes priority
    if token_sold_symbol == "ALCX":
        amount = row.get("token_sold_amount")
        formatted = _format_field_value(amount)
        return ("ALCX Sold", formatted)
    
    if token_bought_symbol == "ALCX":
        amount = row.get("token_bought_amount")
        formatted = _format_field_value(amount)
        return ("ALCX Bought", formatted)
    
    return (None, None)


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
    title: str = "ALCX Dex Swap",
    color: discord.Color | None = None,
) -> list[discord.Embed]:
    """Format a Dune query result as a list of Discord embeds, one per row.
    
    Each embed represents a single ALCX swap with a slim, focused layout:
    - Block Time (displayed in user's local timezone via Discord)
    - ALCX Bought or ALCX Sold (conditional based on token symbols)
    - Amount USD
    - Txn (clickable link to block explorer)
    
    Args:
        result: The QueryResult from Dune.
        title: Title for each embed (default: "ALCX Dex Swap").
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
    
    embeds = []
    total_rows = len(result.rows)
    
    for row_index, row in enumerate(result.rows, start=1):
        embed = discord.Embed(
            title=_truncate(title, MAX_EMBED_TITLE),
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        
        # Block Time - displayed in user's local timezone
        block_time = row.get("block_time")
        embed.add_field(
            name="Block Time",
            value=_format_discord_timestamp(block_time),
            inline=True,
        )
        
        # ALCX Bought or ALCX Sold - conditional based on token symbols
        alcx_field_name, alcx_amount = _format_alcx_amount(row)
        if alcx_field_name and alcx_amount:
            embed.add_field(
                name=alcx_field_name,
                value=alcx_amount,
                inline=True,
            )
        
        # Amount USD
        amount_usd = row.get("amount_usd")
        embed.add_field(
            name="Amount USD",
            value=_format_field_value(amount_usd),
            inline=True,
        )
        
        # Transaction link - blockchain-specific
        blockchain = row.get("blockchain")
        tx_hash = row.get("tx_hash")
        embed.add_field(
            name="Txn",
            value=_format_tx_link(blockchain, tx_hash),
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

