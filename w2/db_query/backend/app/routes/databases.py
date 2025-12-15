"""Database connection and query routes."""
import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas import (
    DatabaseConnectionRequest,
    DatabaseConnectionResponse,
    DatabaseListResponse,
    MetadataResponse,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
    SqlQueryRequest,
    SqlQueryResponse,
)
from ..services.database import execute_query, get_connection, list_connections, save_connection
from ..services.metadata import get_metadata as get_metadata_service, refresh_metadata
from ..services.sql_parser import add_limit_if_needed, validate_sql

router = APIRouter()


@router.get(
    "/api/v1/dbs",
    response_model=DatabaseListResponse,
    summary="Get all databases",
    description="Retrieve all stored database connections",
)
async def list_dbs(session: AsyncSession = Depends(get_session)) -> DatabaseListResponse:
    """Get all database connections."""
    connections = await list_connections(session)
    return DatabaseListResponse(
        databases=[
            DatabaseConnectionResponse.model_validate(conn) for conn in connections
        ]
    )


@router.put(
    "/api/v1/dbs/{name}",
    response_model=DatabaseConnectionResponse,
    summary="Add or update database",
    description="Add a new database connection or update an existing one",
)
async def put_db(
    name: str,
    request: DatabaseConnectionRequest,
    session: AsyncSession = Depends(get_session),
) -> DatabaseConnectionResponse:
    """Add or update a database connection."""
    try:
        db_conn = await save_connection(session, name, request.url)

        # Trigger metadata refresh asynchronously (don't wait)
        asyncio.create_task(refresh_metadata(session, name))

        return DatabaseConnectionResponse.model_validate(db_conn)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "connection_failed", "message": str(e), "details": None}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "internal_error", "message": str(e), "details": None}},
        )


@router.get(
    "/api/v1/dbs/{name}",
    response_model=MetadataResponse,
    summary="Get database metadata",
    description="Retrieve metadata (tables and views) for a database connection",
)
async def get_db_metadata(
    name: str, session: AsyncSession = Depends(get_session)
) -> MetadataResponse:
    """Get database metadata."""
    # Check if connection exists
    db_conn = await get_connection(session, name)
    if db_conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "connection_not_found", "message": f"Database connection '{name}' not found", "details": None}},
        )

    # Get metadata
    metadata_obj = await get_metadata_service(session, name)
    if metadata_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "metadata_not_found", "message": f"Metadata for database '{name}' not found. Please refresh metadata first.", "details": None}},
        )

    import json

    return MetadataResponse(
        name=name,
        metadata=json.loads(metadata_obj.metadata_json),
    )


@router.post(
    "/api/v1/dbs/{name}/query",
    response_model=SqlQueryResponse,
    summary="Execute SQL query",
    description="Execute a SQL SELECT query on the specified database",
)
async def query_db(
    name: str,
    request: SqlQueryRequest,
    session: AsyncSession = Depends(get_session),
) -> SqlQueryResponse:
    """Execute SQL query."""
    # Get database connection
    db_conn = await get_connection(session, name)
    if db_conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "connection_not_found", "message": f"Database connection '{name}' not found", "details": None}},
        )

    # Validate SQL
    is_valid, error_message = validate_sql(request.sql)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "sql_validation_error", "message": error_message or "Invalid SQL", "details": None}},
        )

    # Add LIMIT if needed
    sql_with_limit = add_limit_if_needed(request.sql)

    try:
        # Execute query
        result = await execute_query(db_conn.url, db_conn.database_type, sql_with_limit)
        return SqlQueryResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "query_execution_error", "message": str(e), "details": None}},
        )


@router.post(
    "/api/v1/dbs/{name}/query/natural",
    response_model=NaturalLanguageQueryResponse,
    summary="Natural language query",
    description="Generate and execute SQL from natural language",
)
async def natural_language_query(
    name: str,
    request: NaturalLanguageQueryRequest,
    session: AsyncSession = Depends(get_session),
) -> NaturalLanguageQueryResponse:
    """Generate SQL from natural language and execute it."""
    # Get database connection
    db_conn = await get_connection(session, name)
    if db_conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "connection_not_found", "message": f"Database connection '{name}' not found", "details": None}},
        )

    # Get metadata
    metadata_obj = await get_metadata_service(session, name)
    if metadata_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "metadata_not_found", "message": f"Metadata for database '{name}' not found. Please refresh metadata first.", "details": None}},
        )

    import json
    from ..services.llm import generate_sql_from_natural_language

    try:
        # Generate SQL using LLM
        metadata_dict = json.loads(metadata_obj.metadata_json)
        sql, explanation = await generate_sql_from_natural_language(
            request.prompt, metadata_dict
        )

        # Validate generated SQL
        is_valid, error_message = validate_sql(sql)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "sql_validation_error", "message": f"Generated SQL is invalid: {error_message}", "details": {"generated_sql": sql}}},
            )

        # Add LIMIT if needed
        sql_with_limit = add_limit_if_needed(sql)

        # Execute query
        result = await execute_query(db_conn.url, db_conn.database_type, sql_with_limit)

        return NaturalLanguageQueryResponse(
            sql=sql_with_limit,
            explanation=explanation,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "llm_error", "message": str(e), "details": None}},
        )

