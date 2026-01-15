"""Unit tests for data models"""

import pytest
from pg_mcp.models.schema import ColumnInfo, TableInfo, SchemaInfo, DatabaseInfo
from pg_mcp.models.query import QueryRequest, QueryResponse, SQLGenerationResult
from pg_mcp.models.errors import ErrorCode, PgMcpError


def test_column_info_serialization():
    """Test ColumnInfo serialization"""
    col = ColumnInfo(
        name="id",
        data_type="integer",
        nullable=False,
        is_primary_key=True,
    )
    assert col.name == "id"
    assert col.data_type == "integer"
    assert col.nullable is False
    assert col.is_primary_key is True

    # Test serialization
    data = col.model_dump()
    assert data["name"] == "id"
    assert data["is_primary_key"] is True


def test_query_request_validation():
    """Test QueryRequest validation"""
    req = QueryRequest(
        query="查询所有用户",
        database="main",
        schema="public",  # Use alias
        return_type="result",
        max_rows=100,
        page=1,
        page_size=50,
    )
    assert req.query == "查询所有用户"
    assert req.database == "main"
    assert req.return_type == "result"
    assert req.max_rows == 100
    assert req.schema_name == "public"  # Internal field name

    # Test default values
    req_default = QueryRequest(query="test")
    assert req_default.schema_name == "public"  # Internal field name
    # Also test alias access
    assert req_default.model_dump(by_alias=True)["schema"] == "public"
    assert req_default.return_type == "result"
    assert req_default.page == 1
    assert req_default.page_size == 100


def test_error_code_enum():
    """Test ErrorCode enum"""
    assert ErrorCode.DATABASE_CONNECTION_ERROR == "E001"
    assert ErrorCode.SECURITY_VIOLATION == "E005"
    assert isinstance(ErrorCode.DATABASE_CONNECTION_ERROR, str)


def test_pg_mcp_error():
    """Test PgMcpError exception"""
    error = PgMcpError(
        code=ErrorCode.DATABASE_CONNECTION_ERROR,
        message="Connection failed",
        details={"host": "localhost"},
        retryable=True,
        suggestion="Check network",
    )
    assert error.code == ErrorCode.DATABASE_CONNECTION_ERROR
    assert error.message == "Connection failed"
    assert error.retryable is True
    assert error.suggestion == "Check network"
    assert error.details["host"] == "localhost"

