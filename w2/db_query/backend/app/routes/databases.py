"""Database connection and query routes."""
import asyncio
import json
import logging
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
from ..services.database import delete_connection, execute_query, get_connection, list_connections, save_connection
from ..services.metadata import (
    fetch_mysql_metadata,
    fetch_postgres_metadata,
    get_metadata as get_metadata_service,
    refresh_metadata,
)
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
        # Use a new session for the background task to avoid session closure issues
        async def refresh_metadata_background():
            from ..db import async_session_maker
            async with async_session_maker() as bg_session:
                try:
                    await refresh_metadata(bg_session, name)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to refresh metadata for {name}: {str(e)}", exc_info=True)
        
        asyncio.create_task(refresh_metadata_background())

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


@router.delete(
    "/api/v1/dbs/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete database connection",
    description="Delete a database connection and its metadata",
)
async def delete_db(
    name: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a database connection."""
    # Check if connection exists
    db_conn = await get_connection(session, name)
    if db_conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "connection_not_found", "message": f"Database connection '{name}' not found", "details": None}},
        )

    try:
        # Delete metadata first if exists
        from ..models import DatabaseMetadata
        from sqlalchemy import select as sql_select
        metadata_result = await session.execute(
            sql_select(DatabaseMetadata).where(DatabaseMetadata.connection_name == name)
        )
        metadata_obj = metadata_result.scalar_one_or_none()
        if metadata_obj:
            await session.delete(metadata_obj)

        # Delete connection
        success = await delete_connection(session, name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "connection_not_found", "message": f"Database connection '{name}' not found", "details": None}},
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "delete_error", "message": str(e), "details": None}},
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

    return MetadataResponse(
        name=name,
        metadata=json.loads(metadata_obj.metadata_json),
    )


@router.post(
    "/api/v1/dbs/{name}/refresh",
    response_model=MetadataResponse,
    summary="Refresh database metadata",
    description="Manually refresh metadata for a database connection",
)
async def refresh_db_metadata(
    name: str, session: AsyncSession = Depends(get_session)
) -> MetadataResponse:
    """Refresh database metadata."""
    # Check if connection exists
    db_conn = await get_connection(session, name)
    if db_conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "connection_not_found", "message": f"Database connection '{name}' not found", "details": None}},
        )

    try:
        # Refresh metadata
        metadata_obj = await refresh_metadata(session, name)
        return MetadataResponse(
            name=name,
            metadata=json.loads(metadata_obj.metadata_json),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "metadata_refresh_error", "message": str(e), "details": None}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "metadata_refresh_error", "message": str(e), "details": None}},
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
    is_valid, error_message = validate_sql(request.sql, db_conn.database_type)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "sql_validation_error", "message": error_message or "Invalid SQL", "details": None}},
        )

    # Add LIMIT if needed
    sql_with_limit = add_limit_if_needed(request.sql, db_conn.database_type)

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

    # Get metadata - try to refresh if not exists
    metadata_obj = await get_metadata_service(session, name)
    if metadata_obj is None:
        # Try to refresh metadata automatically
        logger = logging.getLogger(__name__)
        try:
            logger.info(f"Metadata not found for {name}, attempting to refresh...")
            metadata_obj = await refresh_metadata(session, name)
        except Exception as e:
            error_str = str(e)
            logger.error(f"Failed to refresh metadata for {name}: {error_str}", exc_info=True)
            
            # Check if it's an API balance issue
            if "402" in error_str or "Insufficient Balance" in error_str or "balance" in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={"error": {"code": "llm_balance_insufficient", "message": "DeepSeek API 余额不足，无法刷新数据库元数据。请充值后重试，或联系管理员。", "details": {"error": error_str}}},
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": {"code": "metadata_refresh_failed", "message": f"无法刷新数据库元数据: {error_str}", "details": {"error": error_str}}},
                )

    from ..services.llm import generate_sql_from_natural_language

    try:
        # Generate SQL using LLM
        metadata_dict = json.loads(metadata_obj.metadata_json)
        
        try:
            sql, explanation = await generate_sql_from_natural_language(
                request.prompt, metadata_dict, db_conn.database_type
            )
        except ValueError as llm_error:
            error_str = str(llm_error)
            # Check if it's a balance issue
            if "402" in error_str or "Insufficient Balance" in error_str or "balance" in error_str.lower() or "余额不足" in error_str:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={"error": {"code": "llm_balance_insufficient", "message": "DeepSeek API 余额不足，无法生成 SQL。请充值后重试，或联系管理员。", "details": {"error": error_str}}},
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": {"code": "llm_error", "message": f"生成 SQL 失败: {error_str}", "details": {"error": error_str}}},
                )

        # Validate generated SQL
        is_valid, error_message = validate_sql(sql, db_conn.database_type)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "sql_validation_error", "message": f"Generated SQL is invalid: {error_message}", "details": {"generated_sql": sql}}},
            )

        # Add LIMIT if needed
        sql_with_limit = add_limit_if_needed(sql, db_conn.database_type)

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


@router.get(
    "/api/v1/dbs/{name}/tables",
    summary="Get database tables",
    description="Get list of tables for a database connection (on-demand loading)",
)
async def get_db_tables(
    name: str,
    schema: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get tables for a database connection."""
    # Check if connection exists
    db_conn = await get_connection(session, name)
    if db_conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "connection_not_found", "message": f"Database connection '{name}' not found", "details": None}},
        )

    try:
        if db_conn.database_type.lower() == "postgresql":
            # Fetch tables directly from database
            raw_metadata = await fetch_postgres_metadata(db_conn.url)
        elif db_conn.database_type.lower() == "mysql":
            # Fetch tables directly from database
            raw_metadata = await fetch_mysql_metadata(db_conn.url)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "unsupported_database", "message": f"Unsupported database type: {db_conn.database_type}", "details": None}},
            )
        
        # Filter by schema if provided
        if schema:
            raw_metadata = [t for t in raw_metadata if t.get("schema") == schema]
        
        # Group by schema
        schema_map: dict[str, list[dict[str, Any]]] = {}
        for table in raw_metadata:
            table_schema = table.get("schema", "public" if db_conn.database_type.lower() == "postgresql" else "")
            if table_schema not in schema_map:
                schema_map[table_schema] = []
            schema_map[table_schema].append({
                "name": table["name"],
                "type": table["type"],
                "schema": table_schema,
            })
        
        return {
            "schemas": [
                {
                    "name": schema_name,
                    "tables": tables,
                }
                for schema_name, tables in schema_map.items()
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "fetch_error", "message": str(e), "details": None}},
        )


@router.get(
    "/api/v1/dbs/{name}/tables/{schema}/{table}/columns",
    summary="Get table columns",
    description="Get column information for a specific table (on-demand loading)",
)
async def get_table_columns(
    name: str,
    schema: str,
    table: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get columns for a specific table."""
    # Check if connection exists
    db_conn = await get_connection(session, name)
    if db_conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "connection_not_found", "message": f"Database connection '{name}' not found", "details": None}},
        )

    try:
        if db_conn.database_type.lower() == "postgresql":
            import asyncpg
            
            conn = await asyncpg.connect(db_conn.url)
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
                
                columns = []
                for row in rows:
                    columns.append({
                        "name": row["column_name"],
                        "type": row["data_type"],
                        "nullable": row["is_nullable"] == "YES",
                        "default": row["column_default"],
                        "position": row["ordinal_position"],
                    })
                
                return {
                    "schema": schema,
                    "table": table,
                    "columns": columns,
                }
            finally:
                await conn.close()
        elif db_conn.database_type.lower() == "mysql":
            import aiomysql
            from urllib.parse import urlparse
            
            # Parse URL to extract connection parameters
            parsed = urlparse(db_conn.url)
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
                
                columns = []
                for row in rows:
                    columns.append({
                        "name": row["column_name"],
                        "type": row["data_type"],
                        "nullable": row["is_nullable"] == "YES",
                        "default": row["column_default"],
                        "position": row["ordinal_position"],
                    })
                
                return {
                    "schema": schema,
                    "table": table,
                    "columns": columns,
                }
            finally:
                conn.close()
                await conn.ensure_closed()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "unsupported_database", "message": f"Unsupported database type: {db_conn.database_type}", "details": None}},
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "fetch_error", "message": str(e), "details": None}},
        )

