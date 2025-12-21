"""Integration tests for API endpoints."""
import asyncio
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


class TestListDatabases:
    """Test GET /api/v1/dbs endpoint."""

    @pytest.mark.asyncio
    async def test_list_empty_databases(self, client, test_db_session):
        """Test listing databases when none exist."""
        response = client.get("/api/v1/dbs")
        assert response.status_code == 200
        data = response.json()
        assert "databases" in data
        assert len(data["databases"]) == 0

    @pytest.mark.asyncio
    async def test_list_databases(self, client, test_db_session):
        """Test listing databases."""
        # Create test connections
        conn1 = DatabaseConnection(
            name="db1",
            url="postgresql://test:test@localhost:5432/db1",
            database_type="postgresql",
        )
        conn2 = DatabaseConnection(
            name="db2",
            url="postgresql://test:test@localhost:5432/db2",
            database_type="postgresql",
        )
        test_db_session.add(conn1)
        test_db_session.add(conn2)
        await test_db_session.commit()

        response = client.get("/api/v1/dbs")
        assert response.status_code == 200
        data = response.json()
        assert "databases" in data
        assert len(data["databases"]) >= 2
        names = [db["name"] for db in data["databases"]]
        assert "db1" in names
        assert "db2" in names


class TestPutDatabase:
    """Test PUT /api/v1/dbs/{name} endpoint."""

    @pytest.mark.asyncio
    async def test_put_database_success(self, client, test_db_session):
        """Test adding a database connection."""
        # Mock test_connection to return True
        with patch("app.services.database.test_connection", new_callable=AsyncMock) as mock_test:
            mock_test.return_value = True
            
            with patch("app.services.metadata.refresh_metadata", new_callable=AsyncMock):
                response = client.put(
                    "/api/v1/dbs/test_db",
                    json={"url": "postgresql://test:test@localhost:5432/test"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "test_db"
                assert "postgresql" in data["url"]

    @pytest.mark.asyncio
    async def test_put_database_connection_failed(self, client, test_db_session):
        """Test adding a database with connection failure."""
        # Mock test_connection to return False
        with patch("app.services.database.test_connection", new_callable=AsyncMock) as mock_test:
            mock_test.return_value = False
            
            response = client.put(
                "/api/v1/dbs/test_db",
                json={"url": "postgresql://invalid:invalid@localhost:5432/test"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert data["detail"]["error"]["code"] == "connection_failed"


class TestDeleteDatabase:
    """Test DELETE /api/v1/dbs/{name} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_database_success(self, client, test_db_session):
        """Test deleting a database connection."""
        # Create a test connection
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        response = client.delete("/api/v1/dbs/test_db")
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get("/api/v1/dbs")
        data = get_response.json()
        names = [db["name"] for db in data["databases"]]
        assert "test_db" not in names

    def test_delete_nonexistent_database(self, client, test_db_session):
        """Test deleting a non-existent database."""
        response = client.delete("/api/v1/dbs/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "connection_not_found"


class TestGetDatabaseMetadata:
    """Test GET /api/v1/dbs/{name} endpoint."""

    @pytest.mark.asyncio
    async def test_get_metadata_success(self, client, test_db_session, sample_metadata):
        """Test getting database metadata."""
        # Create connection and metadata
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

        response = client.get("/api/v1/dbs/test_db")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_db"
        assert "metadata" in data
        assert "tables" in data["metadata"]

    def test_get_metadata_not_found(self, client, test_db_session):
        """Test getting metadata for non-existent connection."""
        response = client.get("/api/v1/dbs/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "connection_not_found"

    @pytest.mark.asyncio
    async def test_get_metadata_no_metadata(self, client, test_db_session):
        """Test getting metadata when metadata doesn't exist."""
        # Create connection without metadata
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        response = client.get("/api/v1/dbs/test_db")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "metadata_not_found"


class TestQueryDatabase:
    """Test POST /api/v1/dbs/{name}/query endpoint."""

    @pytest.mark.asyncio
    async def test_query_success(self, client, test_db_session):
        """Test executing a SQL query."""
        # Create connection
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        # Mock execute_query
        mock_result = {
            "columns": ["id", "name"],
            "rows": [[1, "test"]],
            "row_count": 1,
        }
        
        with patch("app.routes.databases.execute_query", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_result
            
            response = client.post(
                "/api/v1/dbs/test_db/query",
                json={"sql": "SELECT * FROM users"}
            )
            
            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")
            
            assert response.status_code == 200
            data = response.json()
            assert "columns" in data
            assert "rows" in data
            assert data["rowCount"] == 1

    @pytest.mark.asyncio
    async def test_query_invalid_sql(self, client, test_db_session):
        """Test query with invalid SQL."""
        # Create connection
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        response = client.post(
            "/api/v1/dbs/test_db/query",
            json={"sql": "INSERT INTO users VALUES (1)"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "sql_validation_error"

    def test_query_nonexistent_database(self, client, test_db_session):
        """Test querying non-existent database."""
        response = client.post(
            "/api/v1/dbs/nonexistent/query",
            json={"sql": "SELECT * FROM users"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "connection_not_found"


class TestRefreshMetadata:
    """Test POST /api/v1/dbs/{name}/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_metadata_success(self, client, test_db_session):
        """Test successful metadata refresh."""
        # Create connection
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        # Mock metadata refresh
        with patch("app.services.metadata.refresh_metadata", new_callable=AsyncMock) as mock_refresh:
            from app.models import DatabaseMetadata
            mock_metadata = DatabaseMetadata(
                connection_name="test_db",
                metadata_json='{"tables": []}',
            )
            mock_refresh.return_value = mock_metadata
            
            response = client.post("/api/v1/dbs/test_db/refresh")
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "test_db"
            assert "metadata" in data

    def test_refresh_metadata_not_found(self, client, test_db_session):
        """Test refreshing metadata for non-existent connection."""
        response = client.post("/api/v1/dbs/nonexistent/refresh")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "connection_not_found"


class TestGetTables:
    """Test GET /api/v1/dbs/{name}/tables endpoint."""

    @pytest.mark.asyncio
    async def test_get_tables_success(self, client, test_db_session):
        """Test getting tables for a database."""
        # Create connection
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        # Mock fetch_postgres_metadata
        with patch("app.routes.databases.fetch_postgres_metadata", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {
                    "schema": "public",
                    "name": "users",
                    "type": "table",
                }
            ]
            
            response = client.get("/api/v1/dbs/test_db/tables")
            
            assert response.status_code == 200
            data = response.json()
            assert "schemas" in data
            assert len(data["schemas"]) > 0

    def test_get_tables_not_found(self, client, test_db_session):
        """Test getting tables for non-existent connection."""
        response = client.get("/api/v1/dbs/nonexistent/tables")
        assert response.status_code == 404


class TestGetTableColumns:
    """Test GET /api/v1/dbs/{name}/tables/{schema}/{table}/columns endpoint."""

    @pytest.mark.asyncio
    async def test_get_table_columns_success(self, client, test_db_session):
        """Test getting columns for a table."""
        # Create connection
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        # Mock asyncpg connection
        with patch("app.services.metadata.asyncpg.connect", new_callable=AsyncMock) as mock_connect:
            mock_conn = AsyncMock()
            mock_rows = [
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "is_nullable": "NO",
                    "column_default": None,
                    "ordinal_position": 1,
                }
            ]
            mock_conn.fetch = AsyncMock(return_value=mock_rows)
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn
            
            response = client.get("/api/v1/dbs/test_db/tables/public/users/columns")
            
            assert response.status_code == 200
            data = response.json()
            assert "columns" in data
            assert len(data["columns"]) > 0
            assert data["columns"][0]["name"] == "id"

    def test_get_table_columns_not_found(self, client, test_db_session):
        """Test getting columns for non-existent connection."""
        response = client.get("/api/v1/dbs/nonexistent/tables/public/users/columns")
        assert response.status_code == 404


class TestNaturalLanguageQuery:
    """Test POST /api/v1/dbs/{name}/query/natural endpoint."""

    @pytest.mark.asyncio
    async def test_natural_language_query_success(self, client, test_db_session, sample_metadata):
        """Test natural language query."""
        # Create connection and metadata
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

        # Mock LLM and execute_query
        with patch("app.services.llm.generate_sql_from_natural_language", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = ("SELECT * FROM users", None)
            
            with patch("app.routes.databases.execute_query", new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    "columns": ["id", "name"],
                    "rows": [[1, "test"]],
                    "row_count": 1,
                }
                
                response = client.post(
                    "/api/v1/dbs/test_db/query/natural",
                    json={"prompt": "查询所有用户"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "sql" in data
                assert "SELECT" in data["sql"]

    @pytest.mark.asyncio
    async def test_natural_language_query_no_metadata(self, client, test_db_session):
        """Test natural language query without metadata."""
        # Create connection without metadata
        conn = DatabaseConnection(
            name="test_db",
            url="postgresql://test:test@localhost:5432/test",
            database_type="postgresql",
        )
        test_db_session.add(conn)
        await test_db_session.commit()

        # Mock refresh_metadata to raise an error (simulating connection failure)
        with patch("app.services.metadata.refresh_metadata", new_callable=AsyncMock) as mock_refresh:
            mock_refresh.side_effect = Exception("Connection failed")
            
            response = client.post(
                "/api/v1/dbs/test_db/query/natural",
                json={"prompt": "查询所有用户"}
            )
            
            # Should return 500 because refresh failed
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]

