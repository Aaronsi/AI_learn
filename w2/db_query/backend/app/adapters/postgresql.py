"""PostgreSQL database adapter implementation."""

import logging
from typing import Any

import asyncpg
from sqlglot import dialects

from .base import DialectType

from .base import ConnectionInfo, DatabaseAdapter, QueryResult

logger = logging.getLogger(__name__)


class PostgreSQLAdapter:
    """PostgreSQL database adapter.
    
    This adapter implements the DatabaseAdapter protocol for PostgreSQL databases,
    using asyncpg for async database operations.
    """
    
    def __init__(self, connection_info: ConnectionInfo | None = None) -> None:
        """Initialize PostgreSQL adapter.
        
        Args:
            connection_info: Optional connection info (not required for stateless adapter)
        """
        self._connection_info = connection_info
    
    @property
    def database_type(self) -> str:
        """Return database type identifier."""
        return "postgresql"
    
    @property
    def sqlglot_dialect(self) -> DialectType:
        """Return sqlglot dialect for PostgreSQL."""
        return dialects.Dialects.POSTGRES
    
    @property
    def default_schema(self) -> str:
        """Return default schema name."""
        return "public"
    
    async def test_connection(self, connection_info: ConnectionInfo) -> bool:
        """Test PostgreSQL database connection.
        
        Args:
            connection_info: Connection parameters
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            conn = await asyncpg.connect(connection_info.url)
            await conn.close()
            return True
        except Exception as e:
            logger.debug(f"PostgreSQL connection test failed: {e}")
            return False
    
    async def execute_query(
        self, connection_info: ConnectionInfo, sql: str
    ) -> QueryResult:
        """Execute a SQL SELECT query on PostgreSQL.
        
        Args:
            connection_info: Connection parameters
            sql: SQL SELECT query to execute
            
        Returns:
            QueryResult containing columns, rows, and row count
            
        Raises:
            ValueError: If query execution fails
        """
        try:
            conn = await asyncpg.connect(connection_info.url)
            try:
                rows = await conn.fetch(sql)
                
                if not rows:
                    return QueryResult(columns=[], rows=[], row_count=0)
                
                columns = list(rows[0].keys())
                rows_data = [list(row.values()) for row in rows]
                
                return QueryResult(
                    columns=columns,
                    rows=rows_data,
                    row_count=len(rows_data),
                )
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"PostgreSQL query execution failed: {e}")
            raise ValueError(f"Query execution failed: {str(e)}") from e
    
    async def fetch_metadata(
        self, connection_info: ConnectionInfo
    ) -> list[dict[str, Any]]:
        """Fetch PostgreSQL database metadata.
        
        Args:
            connection_info: Connection parameters
            
        Returns:
            List of dictionaries containing table/view metadata with columns
        """
        conn = await asyncpg.connect(connection_info.url)
        try:
            query = """
            SELECT 
                t.table_schema,
                t.table_name,
                t.table_type,
                json_agg(
                    json_build_object(
                        'column_name', c.column_name,
                        'data_type', c.data_type,
                        'is_nullable', c.is_nullable,
                        'column_default', c.column_default
                    ) ORDER BY c.ordinal_position
                ) as columns
            FROM information_schema.tables t
            LEFT JOIN information_schema.columns c 
                ON t.table_schema = c.table_schema 
                AND t.table_name = c.table_name
            WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
            GROUP BY t.table_schema, t.table_name, t.table_type
            ORDER BY t.table_schema, t.table_name;
            """
            rows = await conn.fetch(query)
            
            metadata = []
            for row in rows:
                metadata.append(
                    {
                        "schema": row["table_schema"],
                        "name": row["table_name"],
                        "type": "table" if row["table_type"] == "BASE TABLE" else "view",
                        "columns": row["columns"] or [],
                    }
                )
            
            return metadata
        finally:
            await conn.close()
    
    async def fetch_tables(
        self, connection_info: ConnectionInfo, schema: str | None = None
    ) -> list[dict[str, Any]]:
        """Fetch list of tables/views for a schema.
        
        Args:
            connection_info: Connection parameters
            schema: Optional schema name to filter by
            
        Returns:
            List of dictionaries with table/view information
        """
        metadata = await self.fetch_metadata(connection_info)
        
        if schema:
            metadata = [t for t in metadata if t.get("schema") == schema]
        
        return [
            {
                "name": item["name"],
                "type": item["type"],
                "schema": item["schema"],
            }
            for item in metadata
        ]
    
    async def fetch_table_columns(
        self, connection_info: ConnectionInfo, schema: str, table: str
    ) -> list[dict[str, Any]]:
        """Fetch column information for a specific table.
        
        Args:
            connection_info: Connection parameters
            schema: Schema name
            table: Table name
            
        Returns:
            List of dictionaries with column information
        """
        conn = await asyncpg.connect(connection_info.url)
        try:
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position;
            """
            rows = await conn.fetch(query, schema, table)
            
            return [
                {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"],
                    "position": row["ordinal_position"],
                }
                for row in rows
            ]
        finally:
            await conn.close()

