"""Database connection and query services."""
from typing import Any
from urllib.parse import urlparse

import asyncpg
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DatabaseConnection


def detect_database_type(url: str) -> str:
    """Detect database type from URL."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme in ("postgresql", "postgres"):
        return "postgresql"
    elif scheme in ("mysql", "mariadb"):
        return "mysql"
    else:
        return "unknown"


async def test_connection(url: str, database_type: str) -> bool:
    """Test database connection."""
    try:
        if database_type.lower() == "postgresql":
            # Parse connection string and test
            conn = await asyncpg.connect(url)
            await conn.close()
            return True
        else:
            # For unsupported types, return False instead of raising
            # This allows graceful handling in save_connection
            return False
    except Exception:
        return False


async def get_connection(
    session: AsyncSession, name: str
) -> DatabaseConnection | None:
    """Get a database connection by name."""
    result = await session.execute(
        select(DatabaseConnection).where(DatabaseConnection.name == name)
    )
    return result.scalar_one_or_none()


async def save_connection(
    session: AsyncSession, name: str, url: str
) -> DatabaseConnection:
    """Save or update a database connection."""
    # Detect database type
    database_type = detect_database_type(url)
    
    if database_type == "unknown":
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
    """List all database connections."""
    result = await session.execute(select(DatabaseConnection))
    return list(result.scalars().all())


async def delete_connection(session: AsyncSession, name: str) -> bool:
    """Delete a database connection."""
    db_conn = await get_connection(session, name)
    if db_conn is None:
        return False

    await session.delete(db_conn)
    await session.commit()
    return True


async def execute_query(
    url: str, database_type: str, sql: str
) -> dict[str, Any]:
    """Execute a SQL query and return results."""
    if database_type.lower() == "postgresql":
        conn = await asyncpg.connect(url)
        try:
            rows = await conn.fetch(sql)
            if not rows:
                return {"columns": [], "rows": [], "row_count": 0}

            columns = list(rows[0].keys())
            rows_data = [list(row.values()) for row in rows]
            return {
                "columns": columns,
                "rows": rows_data,
                "row_count": len(rows_data),
            }
        finally:
            await conn.close()
    else:
        raise ValueError(f"Unsupported database type: {database_type}")

