"""Tests for scheduled query execution."""

import pytest
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

from bot.services.scheduler import ScheduledQueryRunner
from bot.services.dune_client import QueryResult


class TestScheduledQueryRunner:
    """Test ScheduledQueryRunner class."""
    
    def test_calculate_next_execution_today(self):
        """Test calculating next execution time for today."""
        # Mock datetime.now to return a time before execution time
        with patch('bot.services.scheduler.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)  # 10:00 AM
            mock_datetime.combine = datetime.combine
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            dune_client = MagicMock()
            bot = MagicMock()
            
            runner = ScheduledQueryRunner(
                dune_client=dune_client,
                bot=bot,
                query_id=12345,
                execution_time="14:30",
                channel_id=999999,
            )
            
            next_exec = runner._calculate_next_execution()
            
            # Should be today at 14:30
            assert next_exec.hour == 14
            assert next_exec.minute == 30
            assert next_exec.date() == datetime(2024, 1, 1, 10, 0, 0).date()
    
    def test_calculate_next_execution_tomorrow(self):
        """Test calculating next execution time for tomorrow."""
        # Mock datetime.now to return a time after execution time
        with patch('bot.services.scheduler.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 15, 0, 0)  # 3:00 PM
            mock_datetime.combine = datetime.combine
            
            dune_client = MagicMock()
            bot = MagicMock()
            
            runner = ScheduledQueryRunner(
                dune_client=dune_client,
                bot=bot,
                query_id=12345,
                execution_time="14:30",
                channel_id=999999,
            )
            
            next_exec = runner._calculate_next_execution()
            
            # Should be tomorrow at 14:30
            assert next_exec.hour == 14
            assert next_exec.minute == 30
            assert next_exec.date() > datetime(2024, 1, 1, 15, 0, 0).date()
    
    def test_get_status(self):
        """Test getting scheduler status."""
        dune_client = MagicMock()
        bot = MagicMock()
        
        runner = ScheduledQueryRunner(
            dune_client=dune_client,
            bot=bot,
            query_id=12345,
            execution_time="14:30",
            channel_id=999999,
        )
        
        status = runner.get_status()
        
        assert status["query_id"] == "12345"
        assert status["execution_time"] == "14:30"
        assert status["channel_id"] == "999999"
        assert status["running"] == "False"
        assert status["last_execution"] is None
        assert status["next_execution"] is None
    
    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful query execution."""
        dune_client = MagicMock()
        bot = MagicMock()
        channel = AsyncMock()
        bot.get_channel.return_value = channel
        
        runner = ScheduledQueryRunner(
            dune_client=dune_client,
            bot=bot,
            query_id=12345,
            execution_time="14:30",
            channel_id=999999,
        )
        
        # Mock query result
        result = QueryResult(
            query_id=12345,
            execution_id="exec-1",
            rows=[
                {
                    "blockchain": "ethereum",
                    "project": "Uniswap",
                    "block_time": "2024-01-01T12:00:00",
                    "token_bought_symbol": "ETH",
                    "token_sold_symbol": "USDC",
                    "token_bought_amount": 1.5,
                    "token_sold_amount": 3000.0,
                    "amount_usd": 3000.0,
                    "tx_hash": "0x1234",
                }
            ],
            metadata={},
        )
        
        dune_client.execute_query_async = AsyncMock(return_value=result)
        
        await runner._execute_query()
        
        # Verify query was executed
        dune_client.execute_query_async.assert_called_once_with(
            query_id=12345,
            timeout=60,
        )
        
        # Verify channel.send was called
        assert channel.send.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_execute_query_channel_not_found(self):
        """Test query execution when channel is not found."""
        dune_client = MagicMock()
        bot = MagicMock()
        bot.get_channel.return_value = None
        
        runner = ScheduledQueryRunner(
            dune_client=dune_client,
            bot=bot,
            query_id=12345,
            execution_time="14:30",
            channel_id=999999,
        )
        
        await runner._execute_query()
        
        # Query should not be executed if channel not found
        assert not dune_client.execute_query_async.called
    
    @pytest.mark.asyncio
    async def test_execute_query_error_handling(self):
        """Test error handling during query execution."""
        dune_client = MagicMock()
        bot = MagicMock()
        channel = AsyncMock()
        bot.get_channel.return_value = channel
        
        runner = ScheduledQueryRunner(
            dune_client=dune_client,
            bot=bot,
            query_id=12345,
            execution_time="14:30",
            channel_id=999999,
        )
        
        # Mock query execution to raise an error
        dune_client.execute_query_async = AsyncMock(side_effect=Exception("Query failed"))
        
        await runner._execute_query()
        
        # Verify error embed was sent
        assert channel.send.call_count >= 1
        # Check that an error embed was sent (would contain "Error" in the embed)
        call_args = channel.send.call_args
        if call_args and len(call_args[1]) > 0:
            embed = call_args[1].get('embed')
            if embed:
                assert "Error" in embed.title or "error" in str(embed).lower()



