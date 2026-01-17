"""Structured logging configuration."""

from __future__ import annotations

import logging
from typing import Literal, Any

try:  # structlog is optional in some test environments
    import structlog
except ImportError:  # pragma: no cover - depends on env
    structlog = None  # type: ignore


def configure_structlog(
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
) -> None:
    """Configure structlog with stdlib logging."""
    logging.basicConfig(level=getattr(logging, log_level))
    if structlog is None:
        return
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Return structlog logger if available, otherwise stdlib logger."""
    if structlog is None:
        return logging.getLogger(name)
    return structlog.get_logger(name)


def has_structlog() -> bool:
    """Whether structlog is available."""
    return structlog is not None

