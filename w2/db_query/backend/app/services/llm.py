"""LLM services for metadata conversion and SQL generation."""
import json
from typing import Any

from openai import AsyncOpenAI

from ..config import settings

# Initialize OpenAI client (compatible with DeepSeek API)
client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
)


async def convert_metadata_to_json(raw_metadata: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert raw metadata to structured JSON using LLM."""
    prompt = f"""Convert the following database metadata into a structured JSON format.
The metadata contains information about tables and views in a PostgreSQL database.

Raw metadata:
{json.dumps(raw_metadata, indent=2)}

Please convert this into a clean JSON structure with the following format:
{{
  "tables": [
    {{
      "name": "schema.table_name",
      "type": "table" or "view",
      "columns": [
        {{
          "name": "column_name",
          "type": "data_type",
          "nullable": true/false,
          "default": "default_value" or null
        }}
      ]
    }}
  ]
}}

Return only the JSON, no additional text."""

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that converts database metadata into structured JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )

        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        return json.loads(content)
    except Exception as e:
        raise ValueError(f"Failed to convert metadata using LLM: {str(e)}")


async def generate_sql_from_natural_language(
    prompt: str, metadata: dict[str, Any], database_type: str = "postgresql"
) -> tuple[str, str | None]:
    """Generate SQL from natural language using LLM."""
    # Format metadata for context
    metadata_text = json.dumps(metadata, indent=2, ensure_ascii=False)

    # Map database type to SQL dialect name
    db_name_map = {
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
    }
    db_name = db_name_map.get(database_type.lower(), "PostgreSQL")
    
    system_prompt = f"""You are a SQL query generator. You generate {db_name} SELECT queries based on natural language descriptions.

Rules:
1. Only generate SELECT statements
2. Do not include LIMIT clauses (they will be added automatically)
3. Use proper {db_name} syntax
4. Reference tables and columns from the provided schema
5. Return only the SQL query, no explanations unless asked"""

    user_prompt = f"""Database Schema:
{metadata_text}

User Query: {prompt}

Generate a {db_name} SELECT query for the above request. Return only the SQL query."""

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
        )

        sql = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        sql = sql.strip()

        explanation = None
        return sql, explanation
    except Exception as e:
        error_str = str(e)
        # Preserve the original error for better error handling
        if "402" in error_str or "Insufficient Balance" in error_str or "balance" in error_str.lower():
            raise ValueError(f"DeepSeek API 余额不足: {error_str}")
        raise ValueError(f"Failed to generate SQL using LLM: {error_str}")

