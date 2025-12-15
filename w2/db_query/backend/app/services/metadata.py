"""Metadata extraction and management services."""
import json
from typing import Any

import asyncpg
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DatabaseConnection, DatabaseMetadata
from .llm import convert_metadata_to_json


async def fetch_postgres_metadata(url: str) -> list[dict[str, Any]]:
    """Fetch metadata from PostgreSQL database."""
    conn = await asyncpg.connect(url)
    try:
        # Query for tables and views
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


async def get_metadata(
    session: AsyncSession, connection_name: str
) -> DatabaseMetadata | None:
    """Get stored metadata for a connection."""
    result = await session.execute(
        select(DatabaseMetadata)
        .where(DatabaseMetadata.connection_name == connection_name)
        .order_by(DatabaseMetadata.updated_at.desc())
    )
    return result.scalar_one_or_none()


async def save_metadata(
    session: AsyncSession, connection_name: str, metadata_json: dict[str, Any]
) -> DatabaseMetadata:
    """Save metadata to database."""
    # Check if metadata exists
    existing = await get_metadata(session, connection_name)
    if existing:
        existing.metadata_json = json.dumps(metadata_json)
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        new_metadata = DatabaseMetadata(
            connection_name=connection_name,
            metadata_json=json.dumps(metadata_json),
        )
        session.add(new_metadata)
        await session.commit()
        await session.refresh(new_metadata)
        return new_metadata


async def refresh_metadata(
    session: AsyncSession, connection_name: str
) -> DatabaseMetadata:
    """Refresh metadata for a connection."""
    db_conn_result = await session.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.name == connection_name
        )
    )
    db_conn = db_conn_result.scalar_one_or_none()
    if db_conn is None:
        raise ValueError(f"Connection {connection_name} not found")

    if db_conn.database_type.lower() == "postgresql":
        raw_metadata = await fetch_postgres_metadata(db_conn.url)
        # Convert to structured JSON using LLM
        structured_metadata = await convert_metadata_to_json(raw_metadata)
        return await save_metadata(session, connection_name, structured_metadata)
    else:
        raise ValueError(f"Unsupported database type: {db_conn.database_type}")

