"""Database connection and query services.

This module has been refactored to use the DatabaseAdapter pattern,
following the Dependency Inversion Principle - it depends on abstractions
(DatabaseAdapter) rather than concrete implementations.
"""

from typing import Any
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..adapters import ConnectionInfo, DatabaseAdapter, get_adapter_factory
from ..models import DatabaseConnection


def detect_database_type(url: str) -> str:
    """Detect database type from URL.
    
    Args:
        url: Database connection URL
        
    Returns:
        Database type identifier (e.g., 'postgresql', 'mysql')
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    
    # Map URL schemes to database types
    scheme_map = {
        "postgresql": "postgresql",
        "postgres": "postgresql",
        "mysql": "mysql",
        "mariadb": "mysql",
    }
    
    return scheme_map.get(scheme, "unknown")


async def test_connection(url: str, database_type: str) -> bool:
    """Test database connection using appropriate adapter.
    
    Args:
        url: Database connection URL
        database_type: Database type identifier
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        factory = get_adapter_factory()
        if not factory.is_supported(database_type):
            return False
        
        connection_info = ConnectionInfo.from_url(url)
        adapter = factory.create(database_type, connection_info)
        
        return await adapter.test_connection(connection_info)
    except Exception:
        return False


async def get_connection(
    session: AsyncSession, name: str
) -> DatabaseConnection | None:
    """Get a database connection by name.
    
    Args:
        session: Database session
        name: Connection name
        
    Returns:
        DatabaseConnection instance or None if not found
    """
    result = await session.execute(
        select(DatabaseConnection).where(DatabaseConnection.name == name)
    )
    return result.scalar_one_or_none()


async def save_connection(
    session: AsyncSession, name: str, url: str
) -> DatabaseConnection:
    """Save or update a database connection.
    
    Args:
        session: Database session
        name: Connection name
        url: Database connection URL
        
    Returns:
        DatabaseConnection instance
        
    Raises:
        ValueError: If database type is unsupported or connection fails
    """
    # Detect database type
    database_type = detect_database_type(url)
    
    factory = get_adapter_factory()
    if not factory.is_supported(database_type):
        raise ValueError(f"Unsupported database URL scheme: {urlparse(url).scheme}")
    
    # Test connection first
    if not await test_connection(url, database_type):
        raise ValueError("Failed to connect to database. Please check your connection settings.")
    
    # Check if connection exists
    existing = await get_connection(session, name)
    if existing:
        existing.url = url
        existing.database_type = database_type
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        db_conn = DatabaseConnection(
            name=name,
            url=url,
            database_type=database_type,
        )
        session.add(db_conn)
        await session.commit()
        await session.refresh(db_conn)
        return db_conn


async def list_connections(session: AsyncSession) -> list[DatabaseConnection]:
    """List all database connections.
    
    Args:
        session: Database session
        
    Returns:
        List of DatabaseConnection instances
    """
    result = await session.execute(select(DatabaseConnection))
    return list(result.scalars().all())


async def delete_connection(session: AsyncSession, name: str) -> bool:
    """Delete a database connection.
    
    Args:
        session: Database session
        name: Connection name
        
    Returns:
        True if deleted, False if not found
    """
    db_conn = await get_connection(session, name)
    if db_conn is None:
        return False
    
    await session.delete(db_conn)
    await session.commit()
    return True


async def execute_query(
    url: str, database_type: str, sql: str
) -> dict[str, Any]:
    """Execute a SQL query and return results using appropriate adapter.
    
    Args:
        url: Database connection URL
        database_type: Database type identifier
        sql: SQL SELECT query to execute
        
    Returns:
        Dictionary with columns, rows, and row_count
        
    Raises:
        ValueError: If database type is unsupported or query execution fails
    """
    factory = get_adapter_factory()
    adapter = factory.create(database_type)
    connection_info = ConnectionInfo.from_url(url)
    
    result = await adapter.execute_query(connection_info, sql)
    return result.to_dict()
