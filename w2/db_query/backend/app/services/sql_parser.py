"""SQL parsing and validation services.

This module has been refactored to use the DatabaseAdapter pattern for
dialect detection, following the Dependency Inversion Principle.
"""

import sqlglot
from sqlglot import exp

from ..adapters import get_adapter_factory


def validate_sql(sql: str, database_type: str = "postgresql") -> tuple[bool, str | None]:
    """Validate SQL and ensure it only contains SELECT statements.
    
    Args:
        sql: SQL query to validate
        database_type: Database type identifier
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Get adapter to determine dialect
        factory = get_adapter_factory()
        if not factory.is_supported(database_type):
            return False, f"Unsupported database type: {database_type}"
        
        adapter = factory.create(database_type)
        dialect = adapter.sqlglot_dialect
        
        # Parse SQL
        parsed = sqlglot.parse_one(sql, dialect=dialect)
        if parsed is None:
            return False, "Failed to parse SQL"
        
        # Check if it's a SELECT statement
        if not isinstance(parsed, exp.Select):
            return False, "Only SELECT statements are allowed"
        
        # Check for any non-SELECT statements in the query
        for expression in parsed.walk():
            if isinstance(expression, (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create)):
                return False, (
                    f"Statement type {type(expression).__name__} is not allowed. "
                    "Only SELECT statements are permitted."
                )
        
        return True, None
    except sqlglot.errors.ParseError as e:
        return False, f"SQL syntax error: {str(e)}"
    except Exception as e:
        return False, f"Error validating SQL: {str(e)}"


def add_limit_if_needed(sql: str, database_type: str = "postgresql", default_limit: int = 1000) -> str:
    """Add LIMIT clause if not present.
    
    Args:
        sql: SQL query
        database_type: Database type identifier
        default_limit: Default limit value
        
    Returns:
        SQL query with LIMIT clause added if needed
    """
    try:
        # Get adapter to determine dialect
        factory = get_adapter_factory()
        if not factory.is_supported(database_type):
            # Fallback to simple string append
            return _fallback_add_limit(sql, default_limit)
        
        adapter = factory.create(database_type)
        dialect = adapter.sqlglot_dialect
        
        parsed = sqlglot.parse_one(sql, dialect=dialect)
        if parsed is None:
            return _fallback_add_limit(sql, default_limit)
        
        # Check if LIMIT already exists
        if parsed.find(exp.Limit):
            return sql
        
        # Add LIMIT clause
        parsed.set("limit", exp.Limit(expression=exp.Literal.number(default_limit)))
        return parsed.sql(dialect=dialect)
    except Exception:
        # If parsing fails, try simple string append (fallback)
        return _fallback_add_limit(sql, default_limit)


def _fallback_add_limit(sql: str, default_limit: int) -> str:
    """Fallback method to add LIMIT using string manipulation.
    
    Args:
        sql: SQL query
        default_limit: Default limit value
        
    Returns:
        SQL query with LIMIT clause added
    """
    sql_upper = sql.upper().strip()
    if "LIMIT" not in sql_upper:
        return f"{sql.rstrip(';')} LIMIT {default_limit}"
    return sql
