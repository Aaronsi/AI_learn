"""Pytest configuration and fixtures."""
import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set environment variable before importing app modules
os.environ.setdefault("DeepSeek_API_KEY", "test_key")

from app.db import Base


@pytest.fixture
async def test_db_session():
    """Create a test database session."""
    # Create a temporary SQLite database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    database_url = f"sqlite+aiosqlite:///{db_path}"
    
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    # Remove temp directory
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_postgres_url():
    """Sample PostgreSQL connection URL for testing."""
    return "postgresql://postgres:postgres@localhost:5432/test_db"


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "tables": [
            {
                "name": "public.users",
                "type": "table",
                "columns": [
                    {
                        "name": "id",
                        "type": "integer",
                        "nullable": False,
                        "default": None
                    },
                    {
                        "name": "name",
                        "type": "varchar",
                        "nullable": False,
                        "default": None
                    },
                    {
                        "name": "email",
                        "type": "varchar",
                        "nullable": True,
                        "default": None
                    }
                ]
            }
        ]
    }

