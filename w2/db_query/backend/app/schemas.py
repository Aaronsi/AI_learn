"""Pydantic schemas for request/response models."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.capitalize() for x in components[1:])


class CamelCaseModel(BaseModel):
    """Base model with camelCase JSON serialization."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel_case,
    )


# Database Connection Schemas
class DatabaseConnectionRequest(CamelCaseModel):
    """Schema for creating/updating a database connection."""

    url: str = Field(..., description="Database connection URL")


class DatabaseConnectionResponse(CamelCaseModel):
    """Schema for database connection response."""

    name: str
    url: str
    database_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatabaseListResponse(CamelCaseModel):
    """Schema for database list response."""

    databases: list[DatabaseConnectionResponse]


# Metadata Schemas
class MetadataResponse(CamelCaseModel):
    """Schema for database metadata response."""

    name: str
    metadata: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


# SQL Query Schemas
class SqlQueryRequest(CamelCaseModel):
    """Schema for SQL query request."""

    sql: str = Field(..., description="SQL query string")


class SqlQueryResponse(CamelCaseModel):
    """Schema for SQL query response."""

    columns: list[str]
    rows: list[list[Any]]
    row_count: int


# Natural Language Query Schemas
class NaturalLanguageQueryRequest(CamelCaseModel):
    """Schema for natural language query request."""

    prompt: str = Field(..., description="Natural language query prompt")


class NaturalLanguageQueryResponse(CamelCaseModel):
    """Schema for natural language query response."""

    sql: str
    explanation: str | None = None


# Error Schemas
class ErrorDetail(CamelCaseModel):
    """Error detail schema."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(CamelCaseModel):
    """Error response schema."""

    error: ErrorDetail

