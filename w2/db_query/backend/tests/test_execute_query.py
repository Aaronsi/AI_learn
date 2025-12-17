"""Tests for execute_query function."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.database import execute_query


class TestExecuteQuery:
    """Test execute_query functionality."""

    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful query execution."""
        mock_rows = [
            MagicMock(keys=lambda: ["id", "name"], values=lambda: [1, "test"]),
            MagicMock(keys=lambda: ["id", "name"], values=lambda: [2, "test2"]),
        ]
        
        with patch("app.services.database.asyncpg.connect", new_callable=AsyncMock) as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=mock_rows)
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn
            
            result = await execute_query("postgresql://test:test@localhost:5432/test", "postgresql", "SELECT * FROM users")
            
            assert result["columns"] == ["id", "name"]
            assert len(result["rows"]) == 2
            assert result["row_count"] == 2
            mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_empty_result(self):
        """Test query execution with empty result."""
        with patch("app.services.database.asyncpg.connect", new_callable=AsyncMock) as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn
            
            result = await execute_query("postgresql://test:test@localhost:5432/test", "postgresql", "SELECT * FROM users WHERE 1=0")
            
            assert result["columns"] == []
            assert result["rows"] == []
            assert result["row_count"] == 0

    @pytest.mark.asyncio
    async def test_execute_query_unsupported_database(self):
        """Test query execution with unsupported database type."""
        with pytest.raises(ValueError, match="Unsupported database type"):
            await execute_query("mysql://test:test@localhost:3306/test", "mysql", "SELECT * FROM users")

    @pytest.mark.asyncio
    async def test_execute_query_connection_error(self):
        """Test query execution with connection error."""
        with patch("app.services.database.asyncpg.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                await execute_query("postgresql://invalid:invalid@localhost:5432/test", "postgresql", "SELECT * FROM users")

