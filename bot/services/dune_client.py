"""Dune Analytics client wrapper.

Provides a thin wrapper around the official dune-client SDK for executing
Dune queries and retrieving results.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from dune_client.client import DuneClient as DuneSDKClient
from dune_client.query import QueryBase
from dune_client.types import QueryParameter

from bot.utils.logging import get_logger


logger = get_logger("services.dune")


class DuneQueryError(Exception):
    """Exception raised when a Dune query fails."""
    
    def __init__(self, message: str, query_id: int | None = None):
        self.query_id = query_id
        super().__init__(message)


class DuneTimeoutError(DuneQueryError):
    """Exception raised when a Dune query times out."""
    pass


@dataclass
class QueryResult:
    """Represents the result of a Dune query execution."""
    
    query_id: int
    execution_id: str
    rows: list[dict[str, Any]]
    metadata: dict[str, Any]
    
    @property
    def row_count(self) -> int:
        """Return the number of rows in the result."""
        return len(self.rows)
    
    @property
    def column_names(self) -> list[str]:
        """Return the column names from the first row."""
        if self.rows:
            return list(self.rows[0].keys())
        return []
    
    @property
    def is_empty(self) -> bool:
        """Return True if the result has no rows."""
        return len(self.rows) == 0


class DuneClient:
    """Wrapper around the official Dune Analytics SDK.
    
    This class provides a simplified interface for executing Dune queries
    and handling results, with proper error handling and logging.
    """
    
    def __init__(self, api_key: str):
        """Initialize the Dune client.
        
        Args:
            api_key: The Dune Analytics API key.
        """
        self._client = DuneSDKClient(api_key=api_key)
        logger.info("Dune client initialized")
    
    def execute_query(
        self,
        query_id: int,
        parameters: dict[str, Any] | None = None,
        timeout: int = 60,
    ) -> QueryResult:
        """Execute a Dune query and wait for results.
        
        This is a synchronous method that blocks until the query completes
        or times out.
        
        Args:
            query_id: The Dune query ID to execute.
            parameters: Optional dictionary of query parameters.
            timeout: Maximum time to wait for results in seconds.
            
        Returns:
            QueryResult containing the query results.
            
        Raises:
            DuneQueryError: If the query fails.
            DuneTimeoutError: If the query times out.
        """
        logger.info(f"Executing Dune query {query_id} with timeout={timeout}s")
        
        try:
            # Build the query
            query = QueryBase(query_id=query_id)
            
            # Add parameters if provided
            if parameters:
                query_params = self._build_parameters(parameters)
                query = QueryBase(query_id=query_id, params=query_params)
            
            # Execute and get results
            # The SDK's run_query method handles execution and waiting
            results = self._client.run_query(
                query=query,
                performance="medium",  # Use medium performance tier
            )
            
            logger.info(
                f"Query {query_id} completed with "
                f"{len(results.result.rows)} rows"
            )
            
            return QueryResult(
                query_id=query_id,
                execution_id=results.execution_id or "",
                rows=results.result.rows,
                metadata={
                    "state": str(results.state),
                    "submitted_at": str(results.submitted_at) if results.submitted_at else None,
                    "execution_started_at": str(results.execution_started_at) if results.execution_started_at else None,
                    "execution_ended_at": str(results.execution_ended_at) if results.execution_ended_at else None,
                },
            )
            
        except TimeoutError as e:
            logger.error(f"Query {query_id} timed out after {timeout}s")
            raise DuneTimeoutError(
                f"Query {query_id} timed out after {timeout} seconds",
                query_id=query_id,
            ) from e
            
        except Exception as e:
            logger.error(f"Query {query_id} failed: {e}")
            raise DuneQueryError(
                f"Query {query_id} failed: {str(e)}",
                query_id=query_id,
            ) from e
    
    async def execute_query_async(
        self,
        query_id: int,
        parameters: dict[str, Any] | None = None,
        timeout: int = 60,
    ) -> QueryResult:
        """Execute a Dune query asynchronously.
        
        This method runs the synchronous execute_query in a thread pool
        to avoid blocking the event loop.
        
        Args:
            query_id: The Dune query ID to execute.
            parameters: Optional dictionary of query parameters.
            timeout: Maximum time to wait for results in seconds.
            
        Returns:
            QueryResult containing the query results.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute_query(query_id, parameters, timeout)
        )
    
    def get_latest_results(self, query_id: int) -> QueryResult:
        """Get the latest cached results for a query without re-executing.
        
        Args:
            query_id: The Dune query ID.
            
        Returns:
            QueryResult containing the cached results.
            
        Raises:
            DuneQueryError: If fetching results fails.
        """
        logger.info(f"Fetching latest results for query {query_id}")
        
        try:
            results = self._client.get_latest_result(query_id)
            
            return QueryResult(
                query_id=query_id,
                execution_id=results.execution_id or "",
                rows=results.result.rows,
                metadata={
                    "state": str(results.state),
                },
            )
            
        except Exception as e:
            logger.error(f"Failed to get latest results for query {query_id}: {e}")
            raise DuneQueryError(
                f"Failed to get latest results for query {query_id}: {str(e)}",
                query_id=query_id,
            ) from e
    
    async def get_latest_results_async(self, query_id: int) -> QueryResult:
        """Get the latest cached results asynchronously.
        
        Args:
            query_id: The Dune query ID.
            
        Returns:
            QueryResult containing the cached results.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.get_latest_results(query_id)
        )
    
    def _build_parameters(
        self,
        params: dict[str, Any]
    ) -> list[QueryParameter]:
        """Build QueryParameter list from a dictionary.
        
        Args:
            params: Dictionary of parameter names to values.
            
        Returns:
            List of QueryParameter objects.
        """
        query_params = []
        
        for name, value in params.items():
            if isinstance(value, bool):
                # Boolean parameters aren't directly supported, use text
                query_params.append(
                    QueryParameter.text_type(name=name, value=str(value).lower())
                )
            elif isinstance(value, (int, float)):
                query_params.append(
                    QueryParameter.number_type(name=name, value=value)
                )
            elif isinstance(value, str):
                query_params.append(
                    QueryParameter.text_type(name=name, value=value)
                )
            else:
                # Default to text for other types
                query_params.append(
                    QueryParameter.text_type(name=name, value=str(value))
                )
        
        return query_params

