"""Base database adapter protocol and data models.

This module defines the interface that all database adapters must implement,
following the Interface Segregation Principle (ISP) and Dependency Inversion Principle (DIP).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol

# sqlglot dialect can be a string or Dialect enum
DialectType = str | Any  # str or sqlglot.dialects.Dialect


@dataclass(frozen=True)
class ConnectionInfo:
    """Database connection information.
    
    This dataclass encapsulates connection parameters in a type-safe way,
    avoiding string parsing throughout the codebase.
    """
    
    url: str
    host: str
    port: int
    user: str
    password: str
    database: str | None = None
    schema: str | None = None
    
    @classmethod
    def from_url(cls, url: str) -> "ConnectionInfo":
        """Parse connection URL into ConnectionInfo.
        
        Args:
            url: Database connection URL (e.g., postgresql://user:pass@host:port/db)
            
        Returns:
            ConnectionInfo instance with parsed connection parameters
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        return cls(
            url=url,
            host=parsed.hostname or "localhost",
            port=parsed.port or cls._default_port(parsed.scheme),
            user=parsed.username or "",
            password=parsed.password or "",
            database=parsed.path.lstrip("/") if parsed.path else None,
        )
    
    @staticmethod
    def _default_port(scheme: str) -> int:
        """Get default port for database scheme."""
        defaults = {
            "postgresql": 5432,
            "postgres": 5432,
            "mysql": 3306,
            "mariadb": 3306,
        }
        return defaults.get(scheme.lower(), 5432)


@dataclass(frozen=True)
class QueryResult:
    """Query execution result.
    
    This provides a consistent structure for query results across all database types,
    following the Data Transfer Object (DTO) pattern.
    """
    
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for API responses."""
        return {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
        }


class DatabaseAdapter(Protocol):
    """Protocol defining the interface for database adapters.
    
    This protocol follows the Interface Segregation Principle - it defines
    only the essential operations needed for database interaction. Each
    database type implements this protocol with its specific logic.
    
    Using Protocol instead of ABC allows for structural typing and makes
    it easier to test and mock implementations.
    """
    
    @property
    def database_type(self) -> str:
        """Return the database type identifier (e.g., 'postgresql', 'mysql')."""
        ...
    
    @property
    def sqlglot_dialect(self) -> DialectType:
        """Return the sqlglot dialect for SQL parsing."""
        ...
    
    @property
    def default_schema(self) -> str:
        """Return the default schema name for this database type."""
        ...
    
    async def test_connection(self, connection_info: ConnectionInfo) -> bool:
        """Test database connection.
        
        Args:
            connection_info: Connection parameters
            
        Returns:
            True if connection successful, False otherwise
        """
        ...
    
    async def execute_query(
        self, connection_info: ConnectionInfo, sql: str
    ) -> QueryResult:
        """Execute a SQL SELECT query and return results.
        
        Args:
            connection_info: Connection parameters
            sql: SQL SELECT query to execute
            
        Returns:
            QueryResult containing columns, rows, and row count
            
        Raises:
            ValueError: If query execution fails
        """
        ...
    
    async def fetch_metadata(
        self, connection_info: ConnectionInfo
    ) -> list[dict[str, Any]]:
        """Fetch database metadata (tables, views, columns).
        
        Args:
            connection_info: Connection parameters
            
        Returns:
            List of dictionaries containing table/view metadata with columns
            
        Raises:
            ValueError: If metadata fetch fails
        """
        ...
    
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
        ...
    
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
        ...

