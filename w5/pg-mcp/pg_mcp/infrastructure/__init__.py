"""Infrastructure module"""

# Import core modules that don't have external dependencies
from pg_mcp.infrastructure.db_pool import DBPoolManager

# Lazy imports for modules with optional dependencies
# These will be imported when needed, avoiding import errors during test collection
try:
    from pg_mcp.infrastructure.llm_client import LLMClient
except ImportError:
    LLMClient = None  # type: ignore

try:
    from pg_mcp.infrastructure.rate_limiter import RateLimiter, CircuitBreaker, CircuitState
except ImportError:
    RateLimiter = None  # type: ignore
    CircuitBreaker = None  # type: ignore
    CircuitState = None  # type: ignore

try:
    from pg_mcp.infrastructure.metrics import Metrics, HealthChecker
except ImportError:
    Metrics = None  # type: ignore
    HealthChecker = None  # type: ignore

try:
    from pg_mcp.infrastructure.token_meter import TokenMeter
except ImportError:
    TokenMeter = None  # type: ignore

try:
    from pg_mcp.infrastructure.log_sanitizer import LogSanitizer
except ImportError:
    LogSanitizer = None  # type: ignore

__all__ = [
    "DBPoolManager",
    "LLMClient",
    "RateLimiter",
    "CircuitBreaker",
    "CircuitState",
    "Metrics",
    "HealthChecker",
    "TokenMeter",
    "LogSanitizer",
]

