"""Tests for LLM services."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import convert_metadata_to_json, generate_sql_from_natural_language


class TestConvertMetadataToJson:
    """Test metadata conversion using LLM."""

    @pytest.mark.asyncio
    async def test_convert_metadata_success(self, sample_metadata):
        """Test successful metadata conversion."""
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
                        "column_default": None
                    }
                ]
            }
        ]

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_metadata)

        with patch("app.services.llm.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await convert_metadata_to_json(raw_metadata)
            
            assert result == sample_metadata
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_metadata_with_markdown(self, sample_metadata):
        """Test metadata conversion with markdown code blocks."""
        raw_metadata = []

        # Mock LLM response with markdown
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = f"```json\n{json.dumps(sample_metadata)}\n```"

        with patch("app.services.llm.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await convert_metadata_to_json(raw_metadata)
            
            assert result == sample_metadata

    @pytest.mark.asyncio
    async def test_convert_metadata_failure(self):
        """Test metadata conversion failure."""
        raw_metadata = []

        # Mock LLM response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON"

        with patch("app.services.llm.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            with pytest.raises(ValueError, match="Failed to convert"):
                await convert_metadata_to_json(raw_metadata)

    @pytest.mark.asyncio
    async def test_convert_metadata_api_error(self):
        """Test metadata conversion with API error."""
        raw_metadata = []

        with patch("app.services.llm.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")

            with pytest.raises(ValueError, match="Failed to convert"):
                await convert_metadata_to_json(raw_metadata)


class TestGenerateSqlFromNaturalLanguage:
    """Test SQL generation from natural language."""

    @pytest.mark.asyncio
    async def test_generate_sql_success(self, sample_metadata):
        """Test successful SQL generation."""
        prompt = "查询所有用户"
        expected_sql = "SELECT * FROM users"

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = expected_sql

        with patch("app.services.llm.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            sql, explanation = await generate_sql_from_natural_language(prompt, sample_metadata)
            
            assert sql == expected_sql
            assert explanation is None
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_sql_with_markdown(self, sample_metadata):
        """Test SQL generation with markdown code blocks."""
        prompt = "查询所有用户"
        expected_sql = "SELECT * FROM users"

        # Mock LLM response with markdown
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = f"```sql\n{expected_sql}\n```"

        with patch("app.services.llm.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            sql, explanation = await generate_sql_from_natural_language(prompt, sample_metadata)
            
            assert sql == expected_sql

    @pytest.mark.asyncio
    async def test_generate_sql_api_error(self, sample_metadata):
        """Test SQL generation with API error."""
        prompt = "查询所有用户"

        with patch("app.services.llm.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")

            with pytest.raises(ValueError, match="Failed to generate"):
                await generate_sql_from_natural_language(prompt, sample_metadata)

    @pytest.mark.asyncio
    async def test_generate_sql_with_complex_query(self, sample_metadata):
        """Test SQL generation for complex queries."""
        prompt = "查询用户表中id大于10的所有记录，按id降序排列"
        expected_sql = "SELECT * FROM users WHERE id > 10 ORDER BY id DESC"

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = expected_sql

        with patch("app.services.llm.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            sql, _ = await generate_sql_from_natural_language(prompt, sample_metadata)
            
            assert sql == expected_sql

