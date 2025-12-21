"""Database adapter factory with registration mechanism.

This module implements the Factory pattern with a registry, allowing
new database types to be added without modifying existing code (Open-Closed Principle).
"""

import logging
from typing import Type

from .base import ConnectionInfo, DatabaseAdapter, DialectType

logger = logging.getLogger(__name__)


class DatabaseAdapterFactory:
    """Factory for creating database adapters.
    
    This factory uses a registry pattern to map database types to their
    adapter implementations. New database types can be registered at runtime
    without modifying existing code.
    
    Example:
        factory = DatabaseAdapterFactory()
        factory.register("postgresql", PostgreSQLAdapter)
        adapter = factory.create("postgresql", connection_info)
    """
    
    def __init__(self) -> None:
        """Initialize the factory with an empty registry."""
        self._registry: dict[str, Type[DatabaseAdapter]] = {}
        self._instances: dict[str, DatabaseAdapter] = {}
    
    def register(
        self, database_type: str, adapter_class: Type[DatabaseAdapter]
    ) -> None:
        """Register a database adapter class.
        
        Args:
            database_type: Database type identifier (e.g., 'postgresql', 'mysql')
            adapter_class: Adapter class implementing DatabaseAdapter protocol
            
        Raises:
            ValueError: If database_type is already registered
        """
        if database_type.lower() in self._registry:
            logger.warning(
                f"Database type '{database_type}' is already registered. "
                f"Overwriting with {adapter_class.__name__}"
            )
        
        self._registry[database_type.lower()] = adapter_class
        logger.info(f"Registered database adapter: {database_type} -> {adapter_class.__name__}")
    
    def create(
        self, database_type: str, connection_info: ConnectionInfo | None = None
    ) -> DatabaseAdapter:
        """Create a database adapter instance.
        
        Args:
            database_type: Database type identifier
            connection_info: Optional connection info (some adapters may need this)
            
        Returns:
            DatabaseAdapter instance
            
        Raises:
            ValueError: If database_type is not registered
        """
        db_type_lower = database_type.lower()
        
        if db_type_lower not in self._registry:
            available = ", ".join(self._registry.keys())
            raise ValueError(
                f"Unsupported database type: {database_type}. "
                f"Available types: {available}"
            )
        
        # Use singleton pattern for adapters (they're stateless)
        if db_type_lower not in self._instances:
            adapter_class = self._registry[db_type_lower]
            # Try to instantiate with connection_info if adapter accepts it
            try:
                instance = adapter_class(connection_info) if connection_info else adapter_class()
            except TypeError:
                # Adapter doesn't accept connection_info in __init__
                instance = adapter_class()
            
            self._instances[db_type_lower] = instance
        
        return self._instances[db_type_lower]
    
    def is_supported(self, database_type: str) -> bool:
        """Check if a database type is supported.
        
        Args:
            database_type: Database type identifier
            
        Returns:
            True if supported, False otherwise
        """
        return database_type.lower() in self._registry
    
    def get_supported_types(self) -> list[str]:
        """Get list of all supported database types.
        
        Returns:
            List of database type identifiers
        """
        return list(self._registry.keys())


# Global factory instance
_factory: DatabaseAdapterFactory | None = None


def get_adapter_factory() -> DatabaseAdapterFactory:
    """Get the global database adapter factory instance.
    
    This function ensures a single factory instance is used throughout
    the application, following the Singleton pattern.
    
    Returns:
        DatabaseAdapterFactory instance
    """
    global _factory
    if _factory is None:
        _factory = DatabaseAdapterFactory()
        # Auto-register built-in adapters
        _register_builtin_adapters(_factory)
    return _factory


def _register_builtin_adapters(factory: DatabaseAdapterFactory) -> None:
    """Register built-in database adapters.
    
    This function is called automatically when the factory is first created.
    New adapters should be imported and registered here.
    
    Args:
        factory: Factory instance to register adapters with
    """
    # Import here to avoid circular dependencies
    from .postgresql import PostgreSQLAdapter
    from .mysql import MySQLAdapter
    
    factory.register("postgresql", PostgreSQLAdapter)
    factory.register("postgres", PostgreSQLAdapter)  # Alias
    factory.register("mysql", MySQLAdapter)
    factory.register("mariadb", MySQLAdapter)  # Alias
    
    logger.info("Registered built-in database adapters")

