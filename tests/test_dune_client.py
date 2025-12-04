"""Tests for Dune client wrapper."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import Any

from bot.services.dune_client import (
    DuneClient,
    DuneQueryError,
    DuneTimeoutError,
    QueryResult,
)


# Mock response classes to simulate dune-client SDK responses
@dataclass
class MockResultRows:
    rows: list[dict[str, Any]]


@dataclass  
class MockExecutionResult:
    execution_id: str
    state: str
    result: MockResultRows
    submitted_at: str | None = None
    execution_started_at: str | None = None
    execution_ended_at: str | None = None


class TestQueryResult:
    """Test QueryResult dataclass."""
    
    def test_row_count(self):
        """Test row_count property."""
        result = QueryResult(
            query_id=123,
            execution_id="exec-1",
            rows=[{"a": 1}, {"a": 2}, {"a": 3}],
            metadata={},
        )
        assert result.row_count == 3
    
    def test_row_count_empty(self):
        """Test row_count with empty rows."""
        result = QueryResult(
            query_id=123,
            execution_id="exec-1",
            rows=[],
            metadata={},
        )
        assert result.row_count == 0
    
    def test_column_names(self):
        """Test column_names property."""
        result = QueryResult(
            query_id=123,
            execution_id="exec-1",
            rows=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            metadata={},
        )
        assert result.column_names == ["name", "age"]
    
    def test_column_names_empty(self):
        """Test column_names with empty rows."""
        result = QueryResult(
            query_id=123,
            execution_id="exec-1",
            rows=[],
            metadata={},
        )
        assert result.column_names == []
    
    def test_is_empty(self):
        """Test is_empty property."""
        empty_result = QueryResult(
            query_id=123,
            execution_id="exec-1",
            rows=[],
            metadata={},
        )
        assert empty_result.is_empty is True
        
        non_empty_result = QueryResult(
            query_id=123,
            execution_id="exec-1",
            rows=[{"a": 1}],
            metadata={},
        )
        assert non_empty_result.is_empty is False


class TestDuneClient:
    """Test DuneClient wrapper class."""
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_init(self, mock_sdk_client):
        """Test client initialization."""
        client = DuneClient(api_key="test-key")
        mock_sdk_client.assert_called_once_with(api_key="test-key")
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_execute_query_success(self, mock_sdk_client):
        """Test successful query execution."""
        # Set up mock
        mock_instance = Mock()
        mock_sdk_client.return_value = mock_instance
        
        mock_result = MockExecutionResult(
            execution_id="exec-123",
            state="QUERY_STATE_COMPLETED",
            result=MockResultRows(rows=[{"col1": "val1"}, {"col1": "val2"}]),
            submitted_at="2024-01-01T00:00:00Z",
            execution_started_at="2024-01-01T00:00:01Z",
            execution_ended_at="2024-01-01T00:00:05Z",
        )
        mock_instance.run_query.return_value = mock_result
        
        # Execute
        client = DuneClient(api_key="test-key")
        result = client.execute_query(query_id=12345)
        
        # Assert
        assert result.query_id == 12345
        assert result.execution_id == "exec-123"
        assert result.row_count == 2
        assert result.rows == [{"col1": "val1"}, {"col1": "val2"}]
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_execute_query_with_parameters(self, mock_sdk_client):
        """Test query execution with parameters."""
        mock_instance = Mock()
        mock_sdk_client.return_value = mock_instance
        
        mock_result = MockExecutionResult(
            execution_id="exec-456",
            state="QUERY_STATE_COMPLETED",
            result=MockResultRows(rows=[{"data": "filtered"}]),
        )
        mock_instance.run_query.return_value = mock_result
        
        client = DuneClient(api_key="test-key")
        result = client.execute_query(
            query_id=12345,
            parameters={"chain": "ethereum", "days": 7}
        )
        
        assert result.row_count == 1
        # Verify run_query was called with a query object
        mock_instance.run_query.assert_called_once()
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_execute_query_failure(self, mock_sdk_client):
        """Test query execution failure raises DuneQueryError."""
        mock_instance = Mock()
        mock_sdk_client.return_value = mock_instance
        mock_instance.run_query.side_effect = Exception("API Error")
        
        client = DuneClient(api_key="test-key")
        
        with pytest.raises(DuneQueryError) as exc_info:
            client.execute_query(query_id=12345)
        
        assert exc_info.value.query_id == 12345
        assert "API Error" in str(exc_info.value)
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_execute_query_timeout(self, mock_sdk_client):
        """Test query timeout raises DuneTimeoutError."""
        mock_instance = Mock()
        mock_sdk_client.return_value = mock_instance
        mock_instance.run_query.side_effect = TimeoutError("Query timed out")
        
        client = DuneClient(api_key="test-key")
        
        with pytest.raises(DuneTimeoutError) as exc_info:
            client.execute_query(query_id=12345, timeout=30)
        
        assert exc_info.value.query_id == 12345
        assert "timed out" in str(exc_info.value)
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_get_latest_results(self, mock_sdk_client):
        """Test getting latest cached results."""
        mock_instance = Mock()
        mock_sdk_client.return_value = mock_instance
        
        mock_result = MockExecutionResult(
            execution_id="exec-789",
            state="QUERY_STATE_COMPLETED",
            result=MockResultRows(rows=[{"cached": "data"}]),
        )
        mock_instance.get_latest_result.return_value = mock_result
        
        client = DuneClient(api_key="test-key")
        result = client.get_latest_results(query_id=12345)
        
        assert result.query_id == 12345
        assert result.rows == [{"cached": "data"}]
        mock_instance.get_latest_result.assert_called_once_with(12345)
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_get_latest_results_failure(self, mock_sdk_client):
        """Test get_latest_results failure raises DuneQueryError."""
        mock_instance = Mock()
        mock_sdk_client.return_value = mock_instance
        mock_instance.get_latest_result.side_effect = Exception("Not found")
        
        client = DuneClient(api_key="test-key")
        
        with pytest.raises(DuneQueryError) as exc_info:
            client.get_latest_results(query_id=99999)
        
        assert exc_info.value.query_id == 99999


class TestBuildParameters:
    """Test parameter building functionality."""
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_build_string_parameter(self, mock_sdk_client):
        """Test building string parameter."""
        client = DuneClient(api_key="test-key")
        params = client._build_parameters({"name": "test"})
        
        assert len(params) == 1
        # QueryParameter objects are created correctly
        assert params[0] is not None
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_build_number_parameter(self, mock_sdk_client):
        """Test building number parameter."""
        client = DuneClient(api_key="test-key")
        params = client._build_parameters({"count": 42, "ratio": 3.14})
        
        assert len(params) == 2
    
    @patch('bot.services.dune_client.DuneSDKClient')
    def test_build_mixed_parameters(self, mock_sdk_client):
        """Test building mixed type parameters."""
        client = DuneClient(api_key="test-key")
        params = client._build_parameters({
            "chain": "ethereum",
            "days": 30,
            "active": True,
        })
        
        assert len(params) == 3


class TestDuneQueryError:
    """Test custom exceptions."""
    
    def test_dune_query_error(self):
        """Test DuneQueryError exception."""
        error = DuneQueryError("Test error", query_id=123)
        
        assert str(error) == "Test error"
        assert error.query_id == 123
    
    def test_dune_timeout_error(self):
        """Test DuneTimeoutError exception."""
        error = DuneTimeoutError("Timeout", query_id=456)
        
        assert isinstance(error, DuneQueryError)
        assert error.query_id == 456


@pytest.mark.asyncio
class TestAsyncMethods:
    """Test async methods of DuneClient."""
    
    @patch('bot.services.dune_client.DuneSDKClient')
    async def test_execute_query_async(self, mock_sdk_client):
        """Test async query execution."""
        mock_instance = Mock()
        mock_sdk_client.return_value = mock_instance
        
        mock_result = MockExecutionResult(
            execution_id="exec-async",
            state="QUERY_STATE_COMPLETED",
            result=MockResultRows(rows=[{"async": "result"}]),
        )
        mock_instance.run_query.return_value = mock_result
        
        client = DuneClient(api_key="test-key")
        result = await client.execute_query_async(query_id=12345)
        
        assert result.query_id == 12345
        assert result.rows == [{"async": "result"}]
    
    @patch('bot.services.dune_client.DuneSDKClient')
    async def test_get_latest_results_async(self, mock_sdk_client):
        """Test async get latest results."""
        mock_instance = Mock()
        mock_sdk_client.return_value = mock_instance
        
        mock_result = MockExecutionResult(
            execution_id="exec-cached",
            state="QUERY_STATE_COMPLETED",
            result=MockResultRows(rows=[{"cached": "async"}]),
        )
        mock_instance.get_latest_result.return_value = mock_result
        
        client = DuneClient(api_key="test-key")
        result = await client.get_latest_results_async(query_id=12345)
        
        assert result.rows == [{"cached": "async"}]

