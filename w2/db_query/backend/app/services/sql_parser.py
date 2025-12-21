"""SQL parsing and validation services."""
import sqlglot
from sqlglot import exp


def validate_sql(sql: str, database_type: str = "postgresql") -> tuple[bool, str | None]:
    """Validate SQL and ensure it only contains SELECT statements."""
    try:
        # Map database type to sqlglot dialect
        dialect_map = {
            "postgresql": "postgres",
            "mysql": "mysql",
        }
        dialect = dialect_map.get(database_type.lower(), "postgres")
        
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
                return False, f"Statement type {type(expression).__name__} is not allowed. Only SELECT statements are permitted."

        return True, None
    except sqlglot.errors.ParseError as e:
        return False, f"SQL syntax error: {str(e)}"
    except Exception as e:
        return False, f"Error validating SQL: {str(e)}"


def add_limit_if_needed(sql: str, database_type: str = "postgresql", default_limit: int = 1000) -> str:
    """Add LIMIT clause if not present."""
    try:
        # Map database type to sqlglot dialect
        dialect_map = {
            "postgresql": "postgres",
            "mysql": "mysql",
        }
        dialect = dialect_map.get(database_type.lower(), "postgres")
        
        parsed = sqlglot.parse_one(sql, dialect=dialect)
        if parsed is None:
            return sql

        # Check if LIMIT already exists
        if parsed.find(exp.Limit):
            return sql

        # Add LIMIT clause
        parsed.set("limit", exp.Limit(expression=exp.Literal.number(default_limit)))
        return parsed.sql(dialect=dialect)
    except Exception:
        # If parsing fails, try simple string append (fallback)
        sql_upper = sql.upper().strip()
        if "LIMIT" not in sql_upper:
            # Simple fallback: append LIMIT at the end
            return f"{sql.rstrip(';')} LIMIT {default_limit}"
        return sql

