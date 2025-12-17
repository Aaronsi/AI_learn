"""Tests for refresh_metadata function."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import DatabaseConnection
from app.services.metadata import refresh_metadata


class TestRefreshMetadata:
    """Test refresh_metadata functionality."""

    @pytest.mark.asyncio
    async def test_refresh_metadata_success(self, test_db_session):
        """Test successful metadata refresh."""
        # Create a test connection
        db_conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(db_conn)
        await test_db_session.commit()

        raw_metadata = [
            {
                "schema": "public",
                "name": "users",
                "type": "table",
                "columns": [
                    {
                        "column_name": "id",
                        "data_type": "integer",
                        "is_nullable": "NO",
                        "column_default": None,
                    }
                ],
            }
        ]

        with patch("app.services.metadata.fetch_postgres_metadata", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_metadata
            
            with patch("app.services.metadata.convert_metadata_to_json", new_callable=AsyncMock) as mock_convert:
                mock_convert.return_value = {
                    "tables": [
                        {
                            "name": "public.users",
                            "type": "table",
                            "columns": [
                                {
                                    "name": "id",
                                    "type": "integer",
                                    "nullable": False,
                                    "default": None,
                                }
                            ],
                        }
                    ]
                }
                
                metadata_obj = await refresh_metadata(test_db_session, "test_db")
                
                assert metadata_obj is not None
                assert metadata_obj.connection_name == "test_db"

    @pytest.mark.asyncio
    async def test_refresh_metadata_llm_fallback(self, test_db_session):
        """Test metadata refresh with LLM fallback to raw format."""
        # Create a test connection
        db_conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(db_conn)
        await test_db_session.commit()

        raw_metadata = [
            {
                "schema": "public",
                "name": "users",
                "type": "table",
                "columns": [
                    {
                        "column_name": "id",
                        "data_type": "integer",
                        "is_nullable": "NO",
                        "column_default": None,
                    }
                ],
            }
        ]

        with patch("app.services.metadata.fetch_postgres_metadata", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_metadata
            
            with patch("app.services.metadata.convert_metadata_to_json", new_callable=AsyncMock) as mock_convert:
                # Simulate LLM balance error
                mock_convert.side_effect = ValueError("Error code: 402 - Insufficient Balance")
                
                metadata_obj = await refresh_metadata(test_db_session, "test_db")
                
                assert metadata_obj is not None
                assert metadata_obj.connection_name == "test_db"
                # Should use raw metadata format
                import json
                stored_metadata = json.loads(metadata_obj.metadata_json)
                assert "tables" in stored_metadata
                assert len(stored_metadata["tables"]) > 0

    @pytest.mark.asyncio
    async def test_refresh_metadata_connection_not_found(self, test_db_session):
        """Test metadata refresh with non-existent connection."""
        with pytest.raises(ValueError, match="Connection.*not found"):
            await refresh_metadata(test_db_session, "nonexistent")

    @pytest.mark.asyncio
    async def test_refresh_metadata_unsupported_database(self, test_db_session):
        """Test metadata refresh with unsupported database type."""
        db_conn = DatabaseConnection(
            name="test_db",
            url="mysql://test:test@localhost:3306/test",
            database_type="mysql",
        )
        test_db_session.add(db_conn)
        await test_db_session.commit()

        with pytest.raises(ValueError, match="Unsupported database type"):
            await refresh_metadata(test_db_session, "test_db")

