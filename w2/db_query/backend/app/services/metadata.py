"""Metadata extraction and management services.

This module has been refactored to use the DatabaseAdapter pattern,
eliminating database-specific if/elif chains and following the Open-Closed Principle.
"""

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..adapters import ConnectionInfo, get_adapter_factory
from ..models import DatabaseConnection, DatabaseMetadata
from .llm import convert_metadata_to_json

logger = logging.getLogger(__name__)


async def get_metadata(
    session: AsyncSession, connection_name: str
) -> DatabaseMetadata | None:
    """Get stored metadata for a connection.
    
    Args:
        session: Database session
        connection_name: Connection name
        
    Returns:
        DatabaseMetadata instance or None if not found
    """
    result = await session.execute(
        select(DatabaseMetadata)
        .where(DatabaseMetadata.connection_name == connection_name)
        .order_by(DatabaseMetadata.updated_at.desc())
    )
    return result.scalar_one_or_none()


async def save_metadata(
    session: AsyncSession, connection_name: str, metadata_json: dict[str, Any]
) -> DatabaseMetadata:
    """Save metadata to database.
    
    Args:
        session: Database session
        connection_name: Connection name
        metadata_json: Metadata dictionary to save
        
    Returns:
        DatabaseMetadata instance
    """
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
    """Refresh metadata for a connection using appropriate adapter.
    
    This function now uses the DatabaseAdapter pattern, making it easy
    to add new database types without modifying this code.
    
    Args:
        session: Database session
        connection_name: Connection name
        
    Returns:
        DatabaseMetadata instance
        
    Raises:
        ValueError: If connection not found or database type unsupported
    """
    db_conn_result = await session.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.name == connection_name
        )
    )
    db_conn = db_conn_result.scalar_one_or_none()
    if db_conn is None:
        raise ValueError(f"Connection {connection_name} not found")

    try:
        # Use adapter factory to get appropriate adapter
        factory = get_adapter_factory()
        adapter = factory.create(db_conn.database_type)
        connection_info = ConnectionInfo.from_url(db_conn.url)
        
        logger.info(f"Fetching {adapter.database_type} metadata for {connection_name}")
        raw_metadata = await adapter.fetch_metadata(connection_info)
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
                logger.warning(
                    f"LLM conversion failed due to API balance issue, using raw metadata format: {error_str}"
                )
                    # Use raw metadata in a compatible format
                structured_metadata = _convert_raw_metadata_to_structured(raw_metadata, adapter.default_schema)
                else:
                    # For other errors, still try to use raw metadata format
                    logger.warning(f"LLM conversion failed, using raw metadata format: {error_str}")
                structured_metadata = _convert_raw_metadata_to_structured(raw_metadata, adapter.default_schema)
        
        return await save_metadata(session, connection_name, structured_metadata)
    except Exception as e:
        logger.error(f"Error refreshing metadata for {connection_name}: {str(e)}", exc_info=True)
        raise


def _convert_raw_metadata_to_structured(
    raw_metadata: list[dict[str, Any]], default_schema: str
) -> dict[str, Any]:
    """Convert raw metadata to structured format.
    
    Args:
        raw_metadata: Raw metadata from adapter
        default_schema: Default schema name for the database type
        
    Returns:
        Structured metadata dictionary
    """
    return {
                        "tables": [
                            {
                "name": f"{item.get('schema', default_schema)}.{item.get('name', '')}",
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
