"""Services module"""

# Lazy imports to avoid optional deps during test discovery
try:
    from pg_mcp.services.schema_service import SchemaService
except ImportError:
    SchemaService = None  # type: ignore

try:
    from pg_mcp.services.query_service import QueryService
except ImportError:
    QueryService = None  # type: ignore

try:
    from pg_mcp.services.validation_service import ValidationService
except ImportError:
    ValidationService = None  # type: ignore

__all__ = ["SchemaService", "QueryService", "ValidationService"]

