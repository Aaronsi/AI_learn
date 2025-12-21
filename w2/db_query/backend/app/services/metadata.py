"""Metadata extraction and management services."""
import json
from typing import Any
from urllib.parse import urlparse

import aiomysql
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


async def fetch_mysql_metadata(url: str) -> list[dict[str, Any]]:
    """Fetch metadata from MySQL database."""
    # Parse URL to extract connection parameters
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 3306
    user = parsed.username or "root"
    password = parsed.password or ""
    database = parsed.path.lstrip("/") if parsed.path else None
    
    conn = await aiomysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        db=database,
        charset="utf8mb4",
    )
    try:
        cur = await conn.cursor(aiomysql.DictCursor)
        
        # Query for tables and views
        # MySQL uses information_schema similar to PostgreSQL
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
            await cur.execute(columns_query, (row["table_schema"], row["table_name"]))
            column_rows = await cur.fetchall()
            
            columns = [
                {
                    "column_name": col["column_name"],
                    "data_type": col["data_type"],
                    "is_nullable": col["is_nullable"],
                    "column_default": col["column_default"],
                }
                for col in column_rows
            ]
            
            metadata.append(
                {
                    "schema": row["table_schema"],
                    "name": row["table_name"],
                    "type": "table" if row["table_type"] == "BASE TABLE" else "view",
                    "columns": columns,
                }
            )
        
        await cur.close()
        return metadata
    finally:
        conn.close()
        await conn.ensure_closed()


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
    import logging
    
    logger = logging.getLogger(__name__)
    
    db_conn_result = await session.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.name == connection_name
        )
    )
    db_conn = db_conn_result.scalar_one_or_none()
    if db_conn is None:
        raise ValueError(f"Connection {connection_name} not found")

    try:
        raw_metadata = None
        if db_conn.database_type.lower() == "postgresql":
            logger.info(f"Fetching PostgreSQL metadata for {connection_name}")
            raw_metadata = await fetch_postgres_metadata(db_conn.url)
        elif db_conn.database_type.lower() == "mysql":
            logger.info(f"Fetching MySQL metadata for {connection_name}")
            raw_metadata = await fetch_mysql_metadata(db_conn.url)
        else:
            raise ValueError(f"Unsupported database type: {db_conn.database_type}")
        
        logger.info(f"Fetched {len(raw_metadata)} tables/views")
        
        # Try to convert to structured JSON using LLM
        # If LLM conversion fails (e.g., insufficient balance), use raw metadata as fallback
        try:
            logger.info("Converting metadata using LLM")
            structured_metadata = await convert_metadata_to_json(raw_metadata)
            logger.info("Metadata conversion successful")
        except Exception as llm_error:
            error_str = str(llm_error)
            # Check if it's a balance/API error
            if "402" in error_str or "Insufficient Balance" in error_str or "balance" in error_str.lower():
                logger.warning(f"LLM conversion failed due to API balance issue, using raw metadata format: {error_str}")
                # Use raw metadata in a compatible format
                structured_metadata = {
                    "tables": [
                        {
                            "name": f"{item.get('schema', 'public')}.{item.get('name', '')}",
                            "type": item.get("type", "table"),
                            "columns": [
                                {
                                    "name": col.get("column_name", ""),
                                    "type": col.get("data_type", ""),
                                    "nullable": col.get("is_nullable", "NO") == "YES",
                                    "default": col.get("column_default"),
                                }
                                for col in (item.get("columns") or [])
                            ],
                        }
                        for item in raw_metadata
                    ]
                }
            else:
                # For other errors, still try to use raw metadata format
                logger.warning(f"LLM conversion failed, using raw metadata format: {error_str}")
                structured_metadata = {
                    "tables": [
                        {
                            "name": f"{item.get('schema', 'public')}.{item.get('name', '')}",
                            "type": item.get("type", "table"),
                            "columns": [
                                {
                                    "name": col.get("column_name", ""),
                                    "type": col.get("data_type", ""),
                                    "nullable": col.get("is_nullable", "NO") == "YES",
                                    "default": col.get("column_default"),
                                }
                                for col in (item.get("columns") or [])
                            ],
                        }
                        for item in raw_metadata
                    ]
                }
        
        return await save_metadata(session, connection_name, structured_metadata)
    except Exception as e:
        logger.error(f"Error refreshing metadata for {connection_name}: {str(e)}", exc_info=True)
        raise

