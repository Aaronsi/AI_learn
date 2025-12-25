"""MySQL database adapter implementation."""

import logging
from typing import Any
from urllib.parse import urlparse

import aiomysql
from sqlglot import dialects

from .base import DialectType

from .base import ConnectionInfo, DatabaseAdapter, QueryResult

logger = logging.getLogger(__name__)


class MySQLAdapter:
    """MySQL database adapter.
    
    This adapter implements the DatabaseAdapter protocol for MySQL/MariaDB databases,
    using aiomysql for async database operations.
    """
    
    def __init__(self, connection_info: ConnectionInfo | None = None) -> None:
        """Initialize MySQL adapter.
        
        Args:
            connection_info: Optional connection info (not required for stateless adapter)
        """
        self._connection_info = connection_info
    
    @property
    def database_type(self) -> str:
        """Return database type identifier."""
        return "mysql"
    
    @property
    def sqlglot_dialect(self) -> DialectType:
        """Return sqlglot dialect for MySQL."""
        return dialects.Dialects.MYSQL
    
    @property
    def default_schema(self) -> str:
        """Return default schema name (empty for MySQL)."""
        return ""
    
    def _parse_url(self, url: str) -> ConnectionInfo:
        """Parse MySQL URL into connection parameters.
        
        MySQL URLs need special handling because aiomysql doesn't accept
        URLs directly like asyncpg does.
        
        Args:
            url: MySQL connection URL
            
        Returns:
            ConnectionInfo with parsed parameters
        """
        parsed = urlparse(url)
        return ConnectionInfo(
            url=url,
            host=parsed.hostname or "localhost",
            port=parsed.port or 3306,
            user=parsed.username or "root",
            password=parsed.password or "",
            database=parsed.path.lstrip("/") if parsed.path else None,
        )
    
    async def _get_connection(self, connection_info: ConnectionInfo) -> aiomysql.Connection:
        """Create MySQL connection.
        
        Args:
            connection_info: Connection parameters
            
        Returns:
            aiomysql.Connection instance
        """
        return await aiomysql.connect(
            host=connection_info.host,
            port=connection_info.port,
            user=connection_info.user,
            password=connection_info.password,
            db=connection_info.database,
            charset="utf8mb4",
        )
    
    async def test_connection(self, connection_info: ConnectionInfo) -> bool:
        """Test MySQL database connection.
        
        Args:
            connection_info: Connection parameters
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            conn = await self._get_connection(connection_info)
            conn.close()
            await conn.ensure_closed()
            return True
        except Exception as e:
            logger.debug(f"MySQL connection test failed: {e}")
            return False
    
    async def execute_query(
        self, connection_info: ConnectionInfo, sql: str
    ) -> QueryResult:
        """Execute a SQL SELECT query on MySQL.
        
        Args:
            connection_info: Connection parameters
            sql: SQL SELECT query to execute
            
        Returns:
            QueryResult containing columns, rows, and row count
            
        Raises:
            ValueError: If query execution fails
        """
        try:
            conn = await self._get_connection(connection_info)
            try:
                cur = await conn.cursor(aiomysql.DictCursor)
                await cur.execute(sql)
                rows = await cur.fetchall()
                await cur.close()
                
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
                conn.close()
                await conn.ensure_closed()
        except Exception as e:
            logger.error(f"MySQL query execution failed: {e}")
            raise ValueError(f"Query execution failed: {str(e)}") from e
    
    async def fetch_metadata(
        self, connection_info: ConnectionInfo
    ) -> list[dict[str, Any]]:
        """Fetch MySQL database metadata.
        
        Args:
            connection_info: Connection parameters
            
        Returns:
            List of dictionaries containing table/view metadata with columns
        """
        conn = await self._get_connection(connection_info)
        try:
            cur = await conn.cursor(aiomysql.DictCursor)
            
            # Query for tables and views
            query = """
            SELECT 
                t.table_schema,
                t.table_name,
                t.table_type
            FROM information_schema.tables t
            WHERE t.table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
            ORDER BY t.table_schema, t.table_name;
            """
            
            await cur.execute(query)
            rows = await cur.fetchall()
            
            metadata = []
            for row in rows:
                # Handle case where DictCursor might return uppercase keys
                table_schema = row.get("table_schema") or row.get("TABLE_SCHEMA", "")
                table_name = row.get("table_name") or row.get("TABLE_NAME", "")
                table_type = row.get("table_type") or row.get("TABLE_TYPE", "BASE TABLE")
                
                if not table_schema or not table_name:
                    continue
                
                # Fetch columns separately for each table
                columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    ordinal_position
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
                """
                await cur.execute(columns_query, (table_schema, table_name))
                column_rows = await cur.fetchall()
                
                columns = [
                    {
                        "column_name": col.get("column_name") or col.get("COLUMN_NAME", ""),
                        "data_type": col.get("data_type") or col.get("DATA_TYPE", ""),
                        "is_nullable": col.get("is_nullable") or col.get("IS_NULLABLE", "NO"),
                        "column_default": col.get("column_default") or col.get("COLUMN_DEFAULT"),
                    }
                    for col in column_rows
                ]
                
                metadata.append(
                    {
                        "schema": table_schema,
                        "name": table_name,
                        "type": "table" if table_type == "BASE TABLE" else "view",
                        "columns": columns,
                    }
                )
            
            await cur.close()
            return metadata
        finally:
            conn.close()
            await conn.ensure_closed()
    
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
                "name": item.get("name", ""),
                "type": item.get("type", "table"),
                "schema": item.get("schema", self.default_schema),
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
        conn = await self._get_connection(connection_info)
        try:
            cur = await conn.cursor(aiomysql.DictCursor)
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
            """
            await cur.execute(query, (schema, table))
            rows = await cur.fetchall()
            await cur.close()
            
            if not rows:
                return []
            
            # Handle case where DictCursor might return different key formats
            return [
                {
                    "name": row.get("column_name") or row.get("COLUMN_NAME", ""),
                    "type": row.get("data_type") or row.get("DATA_TYPE", ""),
                    "nullable": (row.get("is_nullable") or row.get("IS_NULLABLE", "NO")) == "YES",
                    "default": row.get("column_default") or row.get("COLUMN_DEFAULT"),
                    "position": row.get("ordinal_position") or row.get("ORDINAL_POSITION", 0),
                }
                for row in rows
            ]
        finally:
            conn.close()
            await conn.ensure_closed()

