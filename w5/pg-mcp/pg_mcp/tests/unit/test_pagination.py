"""Unit tests for SQL pagination handling."""

from unittest.mock import MagicMock

from pydantic import SecretStr
from sqlglot import parse_one, exp

from pg_mcp.config.settings import Settings, DatabaseConfig, LLMConfig, SecurityConfig
from pg_mcp.infrastructure.metrics import Metrics
from pg_mcp.infrastructure.token_meter import TokenMeter
from pg_mcp.infrastructure.rate_limiter import RateLimiter
from pg_mcp.services.query_service import QueryService


def _make_query_service() -> QueryService:
    settings = Settings(
        databases=[
            DatabaseConfig(
                name="test_db",
                host="localhost",
                port=5432,
                database="test",
                username="test_user",
                password=SecretStr("test_pass"),
            )
        ],
        llm=LLMConfig(api_key=SecretStr("test_key")),
        security=SecurityConfig(),
    )
    return QueryService(
        settings=settings,
        db_pool=MagicMock(),
        schema_service=MagicMock(),
        llm_client=MagicMock(),
        rate_limiter=RateLimiter(settings.rate_limit),
        metrics=Metrics(),
        token_meter=TokenMeter(Metrics()),
    )


def _literal_value(expr: exp.Expression | None) -> str | None:
    if expr is None:
        return None
    literal = expr.args.get("expression") if isinstance(expr, exp.Expression) else None
    if literal is None and hasattr(expr, "this"):
        literal = expr.this
    if isinstance(literal, exp.Literal):
        return str(literal.this)
    if isinstance(expr, exp.Literal):
        return str(expr.this)
    if hasattr(expr, "name") and expr.name:
        return str(expr.name)
    return expr.sql() if isinstance(expr, exp.Expression) else None


def test_add_pagination_when_missing():
    service = _make_query_service()
    sql = "SELECT id, name FROM users ORDER BY id"
    paginated = service._add_pagination(sql, limit=10, offset=5)
    parsed = parse_one(paginated, dialect="postgres")
    limit = parsed.find(exp.Limit)
    offset = parsed.find(exp.Offset)
    assert _literal_value(limit) == "10"
    assert _literal_value(offset) == "5"


def test_keep_existing_limit_offset():
    service = _make_query_service()
    sql = "SELECT id FROM users LIMIT 20 OFFSET 10"
    paginated = service._add_pagination(sql, limit=10, offset=5)
    parsed = parse_one(paginated, dialect="postgres")
    limit = parsed.find(exp.Limit)
    offset = parsed.find(exp.Offset)
    assert _literal_value(limit) == "20"
    assert _literal_value(offset) == "10"

