"""Tests for Discord embed formatters."""

import pytest
import discord

from bot.formatters.discord_embeds import (
    format_query_result,
    format_error_embed,
    format_loading_embed,
    _format_table,
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
        assert embed.color == discord.Color.blue()
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
        assert "more columns" in table


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

