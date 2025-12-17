"""Tests for metadata services."""
import json

import pytest

from app.models import DatabaseConnection, DatabaseMetadata
from app.services.metadata import get_metadata, save_metadata


class TestMetadataStorage:
    """Test metadata storage and retrieval."""

    @pytest.mark.asyncio
    async def test_save_metadata(self, test_db_session, sample_metadata):
        """Test saving metadata."""
        # Create a test connection first
        db_conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(db_conn)
        await test_db_session.commit()

        # Save metadata
        metadata_obj = await save_metadata(test_db_session, "test_db", sample_metadata)
        
        assert metadata_obj is not None
        assert metadata_obj.connection_name == "test_db"
        assert metadata_obj.metadata_json is not None
        
        # Verify JSON content
        stored_metadata = json.loads(metadata_obj.metadata_json)
        assert stored_metadata == sample_metadata

    @pytest.mark.asyncio
    async def test_get_metadata(self, test_db_session, sample_metadata):
        """Test retrieving metadata."""
        # Create a test connection
        db_conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(db_conn)
        await test_db_session.commit()

        # Save metadata
        await save_metadata(test_db_session, "test_db", sample_metadata)

        # Retrieve metadata
        metadata_obj = await get_metadata(test_db_session, "test_db")
        
        assert metadata_obj is not None
        assert metadata_obj.connection_name == "test_db"
        
        stored_metadata = json.loads(metadata_obj.metadata_json)
        assert stored_metadata == sample_metadata

    @pytest.mark.asyncio
    async def test_get_nonexistent_metadata(self, test_db_session):
        """Test retrieving non-existent metadata."""
        metadata_obj = await get_metadata(test_db_session, "nonexistent")
        assert metadata_obj is None

    @pytest.mark.asyncio
    async def test_update_metadata(self, test_db_session, sample_metadata):
        """Test updating existing metadata."""
        # Create a test connection
        db_conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(db_conn)
        await test_db_session.commit()

        # Save initial metadata
        await save_metadata(test_db_session, "test_db", sample_metadata)

        # Update metadata
        updated_metadata = {
            "tables": [
                {
                    "name": "public.posts",
                    "type": "table",
                    "columns": [
                        {
                            "name": "id",
                            "type": "integer",
                            "nullable": False,
                            "default": None
                        }
                    ]
                }
            ]
        }
        updated_obj = await save_metadata(test_db_session, "test_db", updated_metadata)
        
        assert updated_obj is not None
        
        # Verify updated content
        stored_metadata = json.loads(updated_obj.metadata_json)
        assert stored_metadata == updated_metadata
        assert stored_metadata != sample_metadata

    @pytest.mark.asyncio
    async def test_metadata_json_structure(self, test_db_session, sample_metadata):
        """Test that metadata JSON structure is correct."""
        # Create a test connection
        db_conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(db_conn)
        await test_db_session.commit()

        # Save metadata
        metadata_obj = await save_metadata(test_db_session, "test_db", sample_metadata)
        
        # Verify JSON is valid
        stored_metadata = json.loads(metadata_obj.metadata_json)
        assert "tables" in stored_metadata
        assert isinstance(stored_metadata["tables"], list)
        assert len(stored_metadata["tables"]) > 0
        
        # Verify table structure
        table = stored_metadata["tables"][0]
        assert "name" in table
        assert "type" in table
        assert "columns" in table
        assert isinstance(table["columns"], list)

