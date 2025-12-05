"""Tests for Discord embed formatters."""

import pytest
import discord
from datetime import datetime, timezone

from bot.formatters.discord_embeds import (
    format_query_result,
    format_query_result_rows,
    format_alcx_sums_embed,
    format_error_embed,
    format_loading_embed,
    _format_table,
    _format_field_value,
    _format_discord_timestamp,
    _format_tx_link,
    _format_alcx_amount,
    _truncate,
    MAX_EMBED_DESCRIPTION,
)
from bot.services.dune_client import QueryResult


class TestFormatQueryResult:
    """Test format_query_result function."""
    
    def test_basic_result(self):
        """Test formatting a basic query result."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {"name": "Alice", "value": 100},
                {"name": "Bob", "value": 200},
            ],
            metadata={},
        )
        
        embed = format_query_result(result)
        
        assert isinstance(embed, discord.Embed)
        assert "12345" in embed.title
        # Default color is Discord blurple (88, 101, 242)
        assert embed.color is not None
        assert "Alice" in embed.description
        assert "Bob" in embed.description
    
    def test_empty_result(self):
        """Test formatting an empty result."""
        result = QueryResult(
            query_id=99999,
            execution_id="exec-empty",
            rows=[],
            metadata={},
        )
        
        embed = format_query_result(result)
        
        assert "No results" in embed.description
        assert "0 rows" in embed.footer.text
    
    def test_custom_title_and_color(self):
        """Test with custom title and color."""
        result = QueryResult(
            query_id=11111,
            execution_id="exec-1",
            rows=[{"a": 1}],
            metadata={},
        )
        
        embed = format_query_result(
            result,
            title="Custom Title",
            color=discord.Color.green(),
        )
        
        assert embed.title == "Custom Title"
        assert embed.color == discord.Color.green()
    
    def test_footer_shows_row_count(self):
        """Test that footer shows correct row count."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[{"x": i} for i in range(5)],
            metadata={},
        )
        
        embed = format_query_result(result)
        
        assert "5 row(s)" in embed.footer.text
        assert "12345" in embed.footer.text


class TestFormatErrorEmbed:
    """Test format_error_embed function."""
    
    def test_basic_error(self):
        """Test formatting a basic error."""
        embed = format_error_embed("Something went wrong")
        
        assert isinstance(embed, discord.Embed)
        assert "Error" in embed.title
        assert "Something went wrong" in embed.description
        assert embed.color == discord.Color.red()
    
    def test_error_with_query_id(self):
        """Test error with query ID in footer."""
        embed = format_error_embed(
            "Query failed",
            query_id=54321,
        )
        
        assert "54321" in embed.footer.text
    
    def test_custom_title(self):
        """Test error with custom title."""
        embed = format_error_embed(
            "Timed out",
            title="Timeout Error",
        )
        
        assert "Timeout Error" in embed.title


class TestFormatLoadingEmbed:
    """Test format_loading_embed function."""
    
    def test_loading_embed(self):
        """Test loading embed."""
        embed = format_loading_embed(query_id=77777)
        
        assert "Executing" in embed.title
        assert "77777" in embed.description
        assert embed.color == discord.Color.gold()


class TestFormatTable:
    """Test _format_table helper function."""
    
    def test_simple_table(self):
        """Test formatting a simple table."""
        rows = [
            {"col1": "a", "col2": "b"},
            {"col1": "c", "col2": "d"},
        ]
        columns = ["col1", "col2"]
        
        table = _format_table(rows, columns)
        
        assert "col1" in table
        assert "col2" in table
        assert "a" in table
        assert "d" in table
    
    def test_empty_table(self):
        """Test formatting empty table."""
        table = _format_table([], [])
        assert "No data" in table
    
    def test_truncates_long_values(self):
        """Test that long values are truncated."""
        rows = [{"col": "a" * 50}]
        columns = ["col"]
        
        table = _format_table(rows, columns, max_rows=10)
        
        # Value should be truncated with ".."
        assert ".." in table
    
    def test_max_rows_limit(self):
        """Test max_rows limit."""
        rows = [{"x": i} for i in range(100)]
        columns = ["x"]
        
        table = _format_table(rows, columns, max_rows=5)
        
        assert "more row(s)" in table
    
    def test_max_columns_limit(self):
        """Test that too many columns are truncated."""
        rows = [{f"col{i}": i for i in range(10)}]
        columns = [f"col{i}" for i in range(10)]
        
        table = _format_table(rows, columns)
        
        # Should show "more columns" indicator
        assert "more column" in table.lower()


class TestTruncate:
    """Test _truncate helper function."""
    
    def test_no_truncation_needed(self):
        """Test text shorter than max."""
        result = _truncate("short text", 100)
        assert result == "short text"
    
    def test_exact_length(self):
        """Test text at exact max length."""
        text = "x" * 10
        result = _truncate(text, 10)
        assert result == text
    
    def test_truncation_with_ellipsis(self):
        """Test truncation adds ellipsis."""
        text = "a" * 20
        result = _truncate(text, 10)
        
        assert len(result) == 10
        assert result.endswith("...")
    
    def test_empty_string(self):
        """Test empty string."""
        result = _truncate("", 10)
        assert result == ""


class TestFormatQueryResultRows:
    """Test format_query_result_rows function."""
    
    def test_single_row_alcx_bought(self):
        """Test formatting a single row result with ALCX bought."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "blockchain": "ethereum",
                    "project": "Uniswap",
                    "block_time": "2024-01-01T12:00:00",
                    "token_bought_symbol": "ALCX",
                    "token_sold_symbol": "ETH",
                    "token_bought_amount": 100.5,
                    "token_sold_amount": 1.0,
                    "amount_usd": 3000.0,
                    "tx_hash": "0x1234abcd",
                }
            ],
            metadata={},
        )
        
        embeds = format_query_result_rows(result)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "ALCX Dex Swap"
        assert embed.color is not None
        
        # Check the slim field layout (4 fields)
        field_names = [field.name for field in embed.fields]
        assert "Block Time" in field_names
        assert "ALCX Bought" in field_names
        assert "Amount USD" in field_names
        assert "Txn" in field_names
        assert len(embed.fields) == 4
        
        # Check Block Time uses Discord timestamp format
        block_time_field = next(f for f in embed.fields if f.name == "Block Time")
        assert block_time_field.value.startswith("<t:")
        
        # Check Txn is a clickable link with tx_hash as text
        txn_field = next(f for f in embed.fields if f.name == "Txn")
        assert "[0x1234abcd](https://etherscan.io/tx/0x1234abcd)" == txn_field.value
        
        assert "Query ID: 12345 | Row 1 of 1" in embed.footer.text
    
    def test_single_row_alcx_sold(self):
        """Test formatting a single row result with ALCX sold."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "blockchain": "optimism",
                    "block_time": "2024-01-01T12:00:00",
                    "token_bought_symbol": "ETH",
                    "token_sold_symbol": "ALCX",
                    "token_bought_amount": 1.0,
                    "token_sold_amount": 50.25,
                    "amount_usd": 1500.0,
                    "tx_hash": "0x5678efgh",
                }
            ],
            metadata={},
        )
        
        embeds = format_query_result_rows(result)
        
        assert len(embeds) == 1
        embed = embeds[0]
        
        field_names = [field.name for field in embed.fields]
        assert "ALCX Sold" in field_names
        assert "ALCX Bought" not in field_names
        
        # Check Txn links to Optimism explorer
        txn_field = next(f for f in embed.fields if f.name == "Txn")
        assert "optimistic.etherscan.io" in txn_field.value
    
    def test_multiple_rows(self):
        """Test formatting multiple rows."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "blockchain": "ethereum",
                    "block_time": "2024-01-01T12:00:00",
                    "token_bought_symbol": "ALCX",
                    "token_sold_symbol": "ETH",
                    "token_bought_amount": 100.0,
                    "token_sold_amount": 1.0,
                    "amount_usd": 3000.0,
                    "tx_hash": "0x1234",
                },
                {
                    "blockchain": "arbitrum",
                    "block_time": "2024-01-01T13:00:00",
                    "token_bought_symbol": "ETH",
                    "token_sold_symbol": "ALCX",
                    "token_bought_amount": 1.0,
                    "token_sold_amount": 50.0,
                    "amount_usd": 1500.0,
                    "tx_hash": "0x5678",
                },
            ],
            metadata={},
        )
        
        embeds = format_query_result_rows(result)
        
        assert len(embeds) == 2
        # Check first embed - ALCX Bought
        assert embeds[0].title == "ALCX Dex Swap"
        assert "Row 1 of 2" in embeds[0].footer.text
        field_names_0 = [f.name for f in embeds[0].fields]
        assert "ALCX Bought" in field_names_0
        
        # Check second embed - ALCX Sold, Arbitrum link
        assert embeds[1].title == "ALCX Dex Swap"
        assert "Row 2 of 2" in embeds[1].footer.text
        field_names_1 = [f.name for f in embeds[1].fields]
        assert "ALCX Sold" in field_names_1
        txn_field = next(f for f in embeds[1].fields if f.name == "Txn")
        assert "arbiscan.io" in txn_field.value
    
    def test_empty_result(self):
        """Test formatting an empty result."""
        result = QueryResult(
            query_id=99999,
            execution_id="exec-empty",
            rows=[],
            metadata={},
        )
        
        embeds = format_query_result_rows(result)
        
        assert len(embeds) == 1
        embed = embeds[0]
        assert embed.title == "ALCX Dex Swap"
        assert "No results returned" in embed.description
        assert "0 rows" in embed.footer.text
    
    def test_unknown_blockchain(self):
        """Test unknown blockchain shows 'unknown' for Txn."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "blockchain": "polygon",
                    "block_time": "2024-01-01T12:00:00",
                    "token_bought_symbol": "ALCX",
                    "token_sold_symbol": "MATIC",
                    "token_bought_amount": 100.0,
                    "token_sold_amount": 500.0,
                    "amount_usd": 1000.0,
                    "tx_hash": "0x1234",
                }
            ],
            metadata={},
        )
        
        embeds = format_query_result_rows(result)
        
        assert len(embeds) == 1
        txn_field = next(f for f in embeds[0].fields if f.name == "Txn")
        assert txn_field.value == "unknown"
    
    def test_custom_title_and_color(self):
        """Test with custom title and color."""
        result = QueryResult(
            query_id=11111,
            execution_id="exec-1",
            rows=[{
                "blockchain": "ethereum",
                "block_time": "2024-01-01T12:00:00",
                "token_bought_symbol": "ALCX",
                "token_sold_symbol": "ETH",
                "token_bought_amount": 10.0,
                "token_sold_amount": 1.0,
                "amount_usd": 500.0,
                "tx_hash": "0x1234",
            }],
            metadata={},
        )
        
        embeds = format_query_result_rows(
            result,
            title="Custom Title",
            color=discord.Color.green(),
        )
        
        assert embeds[0].title == "Custom Title"
        assert embeds[0].color == discord.Color.green()
    
    def test_none_values(self):
        """Test that None values are handled correctly."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "blockchain": None,
                    "block_time": None,
                    "token_bought_symbol": "ALCX",
                    "token_sold_symbol": "ETH",
                    "token_bought_amount": 100.0,
                    "token_sold_amount": 1.0,
                    "amount_usd": None,
                    "tx_hash": "0x1234",
                }
            ],
            metadata={},
        )
        
        embeds = format_query_result_rows(result)
        
        assert len(embeds) == 1
        embed = embeds[0]
        
        # Block Time should be N/A
        block_time_field = next(f for f in embed.fields if f.name == "Block Time")
        assert block_time_field.value == "N/A"
        
        # Amount USD should be N/A
        amount_field = next(f for f in embed.fields if f.name == "Amount USD")
        assert amount_field.value == "N/A"
        
        # Txn should be unknown (blockchain is None)
        txn_field = next(f for f in embed.fields if f.name == "Txn")
        assert txn_field.value == "unknown"
    
    def test_no_alcx_in_transaction(self):
        """Test transaction with no ALCX - should still have 3 fields."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "blockchain": "ethereum",
                    "block_time": "2024-01-01T12:00:00",
                    "token_bought_symbol": "ETH",
                    "token_sold_symbol": "USDC",
                    "token_bought_amount": 1.0,
                    "token_sold_amount": 3000.0,
                    "amount_usd": 3000.0,
                    "tx_hash": "0x1234",
                }
            ],
            metadata={},
        )
        
        embeds = format_query_result_rows(result)
        
        assert len(embeds) == 1
        embed = embeds[0]
        
        # Should have 3 fields (no ALCX Bought/Sold)
        field_names = [f.name for f in embed.fields]
        assert "Block Time" in field_names
        assert "Amount USD" in field_names
        assert "Txn" in field_names
        assert "ALCX Bought" not in field_names
        assert "ALCX Sold" not in field_names
        assert len(embed.fields) == 3


class TestFormatFieldValue:
    """Test _format_field_value helper function."""
    
    def test_none_value(self):
        """Test None value returns N/A."""
        result = _format_field_value(None)
        assert result == "N/A"
    
    def test_string_value(self):
        """Test string value."""
        result = _format_field_value("test")
        assert result == "test"
    
    def test_integer_value(self):
        """Test integer value."""
        result = _format_field_value(123)
        assert result == "123"
    
    def test_float_value(self):
        """Test float value formatting."""
        result = _format_field_value(123.456)
        assert "123.46" in result or "123.45" in result
    
    def test_datetime_string(self):
        """Test datetime string formatting."""
        result = _format_field_value("2024-01-01T12:00:00")
        assert "2024-01-01" in result
        assert "12:00:00" in result


class TestFormatDiscordTimestamp:
    """Test _format_discord_timestamp helper function."""
    
    def test_none_value(self):
        """Test None value returns N/A."""
        result = _format_discord_timestamp(None)
        assert result == "N/A"
    
    def test_iso_datetime_string(self):
        """Test ISO format datetime string."""
        result = _format_discord_timestamp("2024-01-01T12:00:00")
        # Should return Discord timestamp format <t:UNIX:f>
        assert result.startswith("<t:")
        assert result.endswith(":f>")
        # Verify the unix timestamp is reasonable (2024-01-01 12:00:00 UTC)
        assert "1704110400" in result
    
    def test_pandas_timestamp(self):
        """Test pandas Timestamp input."""
        pd = pytest.importorskip("pandas")
        ts = pd.Timestamp("2024-01-01 12:00:00", tz="UTC")
        result = _format_discord_timestamp(ts)
        assert result.startswith("<t:")
        assert result.endswith(":f>")
        assert "1704110400" in result
    
    def test_numpy_datetime64(self):
        """Test numpy datetime64 input."""
        np = pytest.importorskip("numpy")
        dt64 = np.datetime64("2024-01-01T12:00:00")
        result = _format_discord_timestamp(dt64)
        assert result.startswith("<t:")
        assert result.endswith(":f>")
        assert "1704110400" in result
    
    def test_iso_datetime_with_microseconds(self):
        """Test ISO format with microseconds."""
        result = _format_discord_timestamp("2024-01-01T12:00:00.123456")
        assert result.startswith("<t:")
        assert result.endswith(":f>")
    
    def test_iso_datetime_with_timezone(self):
        """Test ISO format with timezone suffix."""
        result = _format_discord_timestamp("2024-01-01T12:00:00+00:00")
        assert result.startswith("<t:")
        assert result.endswith(":f>")
    
    def test_iso_datetime_with_z_suffix(self):
        """Test ISO format with Z suffix."""
        result = _format_discord_timestamp("2024-01-01T12:00:00Z")
        assert result.startswith("<t:")
        assert result.endswith(":f>")
    
    def test_dune_utc_format(self):
        """Test Dune's actual datetime format with ' UTC' suffix."""
        result = _format_discord_timestamp("2025-12-04 21:58:11.000 UTC")
        assert result.startswith("<t:")
        assert result.endswith(":f>")
        # Verify the unix timestamp is correct (2025-12-04 21:58:11 UTC)
        assert "1764885491" in result
    
    def test_datetime_object(self):
        """Test datetime object input."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = _format_discord_timestamp(dt)
        assert result.startswith("<t:")
        assert result.endswith(":f>")
        assert "1704110400" in result
    
    def test_datetime_object_naive(self):
        """Test naive datetime object (no timezone)."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = _format_discord_timestamp(dt)
        assert result.startswith("<t:")
        assert result.endswith(":f>")
    
    def test_invalid_string(self):
        """Test invalid string returns N/A."""
        result = _format_discord_timestamp("not a date")
        assert result == "N/A"


class TestFormatTxLink:
    """Test _format_tx_link helper function."""
    
    def test_ethereum_link(self):
        """Test Ethereum transaction link."""
        result = _format_tx_link("ethereum", "0x1234abcd")
        assert result == "[0x1234abcd](https://etherscan.io/tx/0x1234abcd)"
    
    def test_optimism_link(self):
        """Test Optimism transaction link."""
        result = _format_tx_link("optimism", "0x5678efgh")
        assert result == "[0x5678efgh](https://optimistic.etherscan.io/tx/0x5678efgh)"
    
    def test_arbitrum_link(self):
        """Test Arbitrum transaction link."""
        result = _format_tx_link("arbitrum", "0x9abcijkl")
        assert result == "[0x9abcijkl](https://arbiscan.io/tx/0x9abcijkl)"
    
    def test_unknown_blockchain(self):
        """Test unknown blockchain returns 'unknown'."""
        result = _format_tx_link("polygon", "0x1234")
        assert result == "unknown"
    
    def test_none_blockchain(self):
        """Test None blockchain returns 'unknown'."""
        result = _format_tx_link(None, "0x1234")
        assert result == "unknown"
    
    def test_none_tx_hash(self):
        """Test None tx_hash returns 'unknown'."""
        result = _format_tx_link("ethereum", None)
        assert result == "unknown"
    
    def test_case_insensitive(self):
        """Test blockchain name is case insensitive."""
        result = _format_tx_link("ETHEREUM", "0x1234")
        assert "etherscan.io" in result
        
        result = _format_tx_link("Optimism", "0x1234")
        assert "optimistic.etherscan.io" in result


class TestFormatAlcxSumsEmbed:
    """Test format_alcx_sums_embed function."""
    
    def test_basic_sums(self):
        """Test formatting basic ALCX sums result."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "alcx_bought_usd": 15000.50,
                    "alcx_sold_usd": 8500.25,
                }
            ],
            metadata={},
        )
        
        embed = format_alcx_sums_embed(result)
        
        assert isinstance(embed, discord.Embed)
        assert embed.title == "ALCX 24h Summary"
        assert embed.color is not None
        
        # Check fields
        field_names = [field.name for field in embed.fields]
        assert "ALCX Bought (USD)" in field_names
        assert "ALCX Sold (USD)" in field_names
        assert len(embed.fields) == 2
        
        # Check values are formatted as USD
        bought_field = next(f for f in embed.fields if f.name == "ALCX Bought (USD)")
        assert "$15,000.50" in bought_field.value
        
        sold_field = next(f for f in embed.fields if f.name == "ALCX Sold (USD)")
        assert "$8,500.25" in sold_field.value
        
        assert "Query ID: 12345" in embed.footer.text
        assert "24h Totals" in embed.footer.text
    
    def test_empty_result(self):
        """Test formatting empty result."""
        result = QueryResult(
            query_id=99999,
            execution_id="exec-empty",
            rows=[],
            metadata={},
        )
        
        embed = format_alcx_sums_embed(result)
        
        assert "No data available" in embed.description
        assert "Query ID: 99999" in embed.footer.text
    
    def test_none_values(self):
        """Test handling None values."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "alcx_bought_usd": None,
                    "alcx_sold_usd": None,
                }
            ],
            metadata={},
        )
        
        embed = format_alcx_sums_embed(result)
        
        bought_field = next(f for f in embed.fields if f.name == "ALCX Bought (USD)")
        assert bought_field.value == "N/A"
        
        sold_field = next(f for f in embed.fields if f.name == "ALCX Sold (USD)")
        assert sold_field.value == "N/A"
    
    def test_missing_columns(self):
        """Test handling missing columns."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "other_column": 123,
                }
            ],
            metadata={},
        )
        
        embed = format_alcx_sums_embed(result)
        
        bought_field = next(f for f in embed.fields if f.name == "ALCX Bought (USD)")
        assert bought_field.value == "N/A"
        
        sold_field = next(f for f in embed.fields if f.name == "ALCX Sold (USD)")
        assert sold_field.value == "N/A"
    
    def test_large_values(self):
        """Test formatting large USD values."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "alcx_bought_usd": 1234567.89,
                    "alcx_sold_usd": 9876543.21,
                }
            ],
            metadata={},
        )
        
        embed = format_alcx_sums_embed(result)
        
        bought_field = next(f for f in embed.fields if f.name == "ALCX Bought (USD)")
        assert "$1,234,567.89" in bought_field.value
        
        sold_field = next(f for f in embed.fields if f.name == "ALCX Sold (USD)")
        assert "$9,876,543.21" in sold_field.value
    
    def test_custom_title_and_color(self):
        """Test with custom title and color."""
        result = QueryResult(
            query_id=11111,
            execution_id="exec-1",
            rows=[{"alcx_bought_usd": 100, "alcx_sold_usd": 200}],
            metadata={},
        )
        
        embed = format_alcx_sums_embed(
            result,
            title="Custom Title",
            color=discord.Color.green(),
        )
        
        assert embed.title == "Custom Title"
        assert embed.color == discord.Color.green()
    
    def test_string_numeric_values(self):
        """Test handling string representations of numbers."""
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "alcx_bought_usd": "5000.00",
                    "alcx_sold_usd": "3000.50",
                }
            ],
            metadata={},
        )
        
        embed = format_alcx_sums_embed(result)
        
        bought_field = next(f for f in embed.fields if f.name == "ALCX Bought (USD)")
        assert "$5,000.00" in bought_field.value
        
        sold_field = next(f for f in embed.fields if f.name == "ALCX Sold (USD)")
        assert "$3,000.50" in sold_field.value


class TestFormatAlcxAmount:
    """Test _format_alcx_amount helper function."""
    
    def test_alcx_bought(self):
        """Test ALCX bought scenario."""
        row = {
            "token_bought_symbol": "ALCX",
            "token_sold_symbol": "ETH",
            "token_bought_amount": 100.5,
            "token_sold_amount": 1.0,
        }
        field_name, amount = _format_alcx_amount(row)
        assert field_name == "ALCX Bought"
        assert "100.5" in amount
    
    def test_alcx_sold(self):
        """Test ALCX sold scenario."""
        row = {
            "token_bought_symbol": "ETH",
            "token_sold_symbol": "ALCX",
            "token_bought_amount": 1.0,
            "token_sold_amount": 50.25,
        }
        field_name, amount = _format_alcx_amount(row)
        assert field_name == "ALCX Sold"
        assert "50.25" in amount
    
    def test_alcx_sold_priority(self):
        """Test ALCX Sold takes priority when both are ALCX."""
        row = {
            "token_bought_symbol": "ALCX",
            "token_sold_symbol": "ALCX",
            "token_bought_amount": 100.0,
            "token_sold_amount": 200.0,
        }
        field_name, amount = _format_alcx_amount(row)
        assert field_name == "ALCX Sold"
        assert "200" in amount
    
    def test_no_alcx(self):
        """Test no ALCX in transaction."""
        row = {
            "token_bought_symbol": "ETH",
            "token_sold_symbol": "USDC",
            "token_bought_amount": 1.0,
            "token_sold_amount": 3000.0,
        }
        field_name, amount = _format_alcx_amount(row)
        assert field_name is None
        assert amount is None
    
    def test_missing_symbols(self):
        """Test missing token symbols."""
        row = {
            "token_bought_amount": 1.0,
            "token_sold_amount": 100.0,
        }
        field_name, amount = _format_alcx_amount(row)
        assert field_name is None
        assert amount is None
    
    def test_none_amount(self):
        """Test None amount is handled."""
        row = {
            "token_bought_symbol": "ALCX",
            "token_sold_symbol": "ETH",
            "token_bought_amount": None,
            "token_sold_amount": 1.0,
        }
        field_name, amount = _format_alcx_amount(row)
        assert field_name == "ALCX Bought"
        assert amount == "N/A"

