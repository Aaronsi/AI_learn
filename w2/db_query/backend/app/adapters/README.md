# Database Adapter Architecture

## Overview

This module implements a pluggable database adapter architecture following SOLID principles, specifically:

- **Open-Closed Principle**: Open for extension (new database types), closed for modification (existing code)
- **Dependency Inversion Principle**: High-level modules depend on abstractions (Protocol), not concrete implementations
- **Single Responsibility Principle**: Each adapter handles one database type
- **Interface Segregation Principle**: `DatabaseAdapter` protocol defines only essential operations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Routes Layer                              │
│  (depends on DatabaseAdapter abstraction)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Services Layer                              │
│  (uses DatabaseAdapterFactory)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              DatabaseAdapterFactory                          │
│  (Registry Pattern - maps types to adapters)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│PostgreSQL    │ │MySQL         │ │SQLite        │
│Adapter       │ │Adapter       │ │Adapter       │
│              │ │              │ │(future)      │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Core Components

### 1. `DatabaseAdapter` Protocol

Defines the interface that all database adapters must implement:

```python
class DatabaseAdapter(Protocol):
    @property
    def database_type(self) -> str: ...
    
    @property
    def sqlglot_dialect(self) -> DialectType: ...
    
    @property
    def default_schema(self) -> str: ...
    
    async def test_connection(self, connection_info: ConnectionInfo) -> bool: ...
    async def execute_query(self, connection_info: ConnectionInfo, sql: str) -> QueryResult: ...
    async def fetch_metadata(self, connection_info: ConnectionInfo) -> list[dict[str, Any]]: ...
    async def fetch_tables(self, connection_info: ConnectionInfo, schema: str | None) -> list[dict[str, Any]]: ...
    async def fetch_table_columns(self, connection_info: ConnectionInfo, schema: str, table: str) -> list[dict[str, Any]]: ...
```

### 2. `ConnectionInfo` Dataclass

Type-safe encapsulation of connection parameters:

```python
@dataclass(frozen=True)
class ConnectionInfo:
    url: str
    host: str
    port: int
    user: str
    password: str
    database: str | None = None
    schema: str | None = None
```

### 3. `DatabaseAdapterFactory`

Factory with registry pattern for creating adapters:

```python
factory = get_adapter_factory()
adapter = factory.create("postgresql", connection_info)
```

## Adding a New Database Type

To add support for a new database type (e.g., SQLite), follow these steps:

### Step 1: Create Adapter Implementation

Create `app/adapters/sqlite.py`:

```python
"""SQLite database adapter implementation."""

from typing import Any
from sqlglot import DialectType, dialect as sqlglot_dialect

from .base import ConnectionInfo, DatabaseAdapter, QueryResult

class SQLiteAdapter:
    """SQLite database adapter."""
    
    @property
    def database_type(self) -> str:
        return "sqlite"
    
    @property
    def sqlglot_dialect(self) -> DialectType:
        return sqlglot_dialect("sqlite")
    
    @property
    def default_schema(self) -> str:
        return "main"
    
    async def test_connection(self, connection_info: ConnectionInfo) -> bool:
        # Implementation
        ...
    
    async def execute_query(self, connection_info: ConnectionInfo, sql: str) -> QueryResult:
        # Implementation
        ...
    
    # ... implement other required methods
```

### Step 2: Register the Adapter

Update `app/adapters/factory.py`:

```python
def _register_builtin_adapters(factory: DatabaseAdapterFactory) -> None:
    from .postgresql import PostgreSQLAdapter
    from .mysql import MySQLAdapter
    from .sqlite import SQLiteAdapter  # Add this
    
    factory.register("postgresql", PostgreSQLAdapter)
    factory.register("mysql", MySQLAdapter)
    factory.register("sqlite", SQLiteAdapter)  # Add this
```

### Step 3: Update URL Detection (if needed)

Update `app/services/database.py`:

```python
def detect_database_type(url: str) -> str:
    scheme_map = {
        "postgresql": "postgresql",
        "postgres": "postgresql",
        "mysql": "mysql",
        "mariadb": "mysql",
        "sqlite": "sqlite",  # Add this
        "sqlite3": "sqlite",  # Add this
    }
    return scheme_map.get(scheme.lower(), "unknown")
```

That's it! No other code changes needed. The existing routes, services, and SQL parser will automatically work with the new database type.

## Benefits

1. **No Code Duplication**: Database-specific logic is isolated in adapters
2. **Easy Testing**: Mock `DatabaseAdapter` protocol for unit tests
3. **Type Safety**: `ConnectionInfo` and `QueryResult` provide type-safe data structures
4. **Extensibility**: Add new databases without touching existing code
5. **Maintainability**: Clear separation of concerns

## Usage Example

```python
from app.adapters import ConnectionInfo, get_adapter_factory

# Get factory
factory = get_adapter_factory()

# Create adapter
connection_info = ConnectionInfo.from_url("postgresql://user:pass@localhost:5432/db")
adapter = factory.create("postgresql", connection_info)

# Use adapter
result = await adapter.execute_query(connection_info, "SELECT * FROM users")
print(result.columns)  # ['id', 'name', 'email']
print(result.rows)      # [[1, 'Alice', 'alice@example.com'], ...]
```

## Design Decisions

1. **Protocol vs ABC**: Using `Protocol` allows structural typing and easier mocking
2. **Factory Pattern**: Centralizes adapter creation and registration
3. **Singleton Adapters**: Adapters are stateless, so we reuse instances
4. **ConnectionInfo**: Encapsulates connection parameters, avoiding string parsing everywhere
5. **QueryResult**: Provides consistent result structure across all database types

