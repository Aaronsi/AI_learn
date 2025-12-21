"""Database adapters package.

This package provides a pluggable architecture for database support.
New database types can be added by implementing the DatabaseAdapter protocol
and registering with the DatabaseAdapterFactory.
"""

from .base import DatabaseAdapter, ConnectionInfo, QueryResult
from .factory import DatabaseAdapterFactory, get_adapter_factory
from .postgresql import PostgreSQLAdapter
from .mysql import MySQLAdapter

__all__ = [
    "DatabaseAdapter",
    "ConnectionInfo",
    "QueryResult",
    "DatabaseAdapterFactory",
    "get_adapter_factory",
    "PostgreSQLAdapter",
    "MySQLAdapter",
]

