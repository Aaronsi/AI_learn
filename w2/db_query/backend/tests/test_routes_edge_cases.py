"""Tests for edge cases and error scenarios in routes."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import DatabaseConnection, DatabaseMetadata


@pytest.fixture
def client(test_db_session):
    """Create a test client with mocked database session."""
    def override_get_session():
        return test_db_session
    
    from app.db import get_session
    app.dependency_overrides[get_session] = override_get_session
    
    yield TestClient(app)
    
    app.dependency_overrides.clear()


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_put_database_invalid_url_scheme(self, client, test_db_session):
        """Test adding database with invalid URL scheme."""
        with patch("app.services.database.test_connection", new_callable=AsyncMock) as mock_test:
            mock_test.return_value = False
            
            response = client.put(
                "/api/v1/dbs/test_db",
                json={"url": "invalid://test:test@localhost:5432/test"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]

    @pytest.mark.asyncio
    async def test_query_with_empty_result(self, client, test_db_session):
        """Test query execution with empty result."""
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        with patch("app.routes.databases.execute_query", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "columns": [],
                "rows": [],
                "row_count": 0,
            }
            
            response = client.post(
                "/api/v1/dbs/test_db/query",
                json={"sql": "SELECT * FROM users WHERE 1=0"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["rowCount"] == 0
            assert len(data["columns"]) == 0

    @pytest.mark.asyncio
    async def test_query_with_null_values(self, client, test_db_session):
        """Test query execution with NULL values."""
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        with patch("app.routes.databases.execute_query", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "columns": ["id", "name", "email"],
                "rows": [[1, "test", None], [2, None, "email@test.com"]],
                "row_count": 2,
            }
            
            response = client.post(
                "/api/v1/dbs/test_db/query",
                json={"sql": "SELECT id, name, email FROM users"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["rowCount"] == 2
            assert len(data["rows"]) == 2

    @pytest.mark.asyncio
    async def test_natural_language_query_with_llm_error(self, client, test_db_session, sample_metadata):
        """Test natural language query with LLM error."""
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        metadata_obj = DatabaseMetadata(
            connection_name="test_db",
            metadata_json=json.dumps(sample_metadata),
        )
        test_db_session.add(metadata_obj)
        await test_db_session.commit()

        with patch("app.services.llm.generate_sql_from_natural_language", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = ValueError("LLM API Error: 402 - Insufficient Balance")
            
            response = client.post(
                "/api/v1/dbs/test_db/query/natural",
                json={"prompt": "查询所有用户"}
            )
            
            assert response.status_code == 402
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "余额不足" in data["detail"]["error"]["message"]

    @pytest.mark.asyncio
    async def test_get_tables_with_schema_filter(self, client, test_db_session):
        """Test getting tables with schema filter."""
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        with patch("app.routes.databases.fetch_postgres_metadata", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {"schema": "public", "name": "users", "type": "table"},
                {"schema": "private", "name": "logs", "type": "table"},
            ]
            
            response = client.get("/api/v1/dbs/test_db/tables?schema=public")
            
            assert response.status_code == 200
            data = response.json()
            assert "schemas" in data

