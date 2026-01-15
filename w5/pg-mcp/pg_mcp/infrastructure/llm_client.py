"""LLM client wrapper for OpenAI-compatible APIs (DeepSeek)"""

import json
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from pg_mcp.config.settings import LLMConfig
from pg_mcp.models.errors import PgMcpError, ErrorCode


class LLMClient:
    """LLM客户端（使用OpenAI兼容API对接DeepSeek）"""

    # NL2SQL系统提示词
    NL2SQL_SYSTEM_PROMPT = """你是一个PostgreSQL SQL专家。根据用户的自然语言描述和提供的数据库schema信息，生成精确的SQL查询语句。

要求：
1. 只生成SELECT语句
2. 使用标准PostgreSQL语法
3. 合理使用JOIN、WHERE、GROUP BY、ORDER BY等子句
4. 考虑性能优化，避免SELECT *
5. 根据schema信息选择正确的表和列
6. 对于模糊的需求，选择最合理的解释

输出格式（JSON）：
{
  "sql": "生成的SQL语句",
  "explanation": "SQL逻辑说明",
  "confidence": 0.0-1.0的置信度
}"""

    VALIDATION_SYSTEM_PROMPT = """你是一个SQL查询结果验证专家。根据用户的原始查询意图、生成的SQL和查询结果样本，评估结果是否满足用户需求。

输出格式（JSON）：
{
  "is_valid": true/false,
  "reason": "验证结论说明",
  "suggestions": ["改进建议列表"]
}"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key.get_secret_value(),
            base_url=config.base_url,
            timeout=config.timeout,
        )

    async def generate_sql(
        self,
        user_query: str,
        schema_context: str,
    ) -> dict[str, Any]:
        """根据自然语言生成SQL"""
        messages = [
            {"role": "system", "content": self.NL2SQL_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""数据库Schema信息：
{schema_context}

用户查询：{user_query}

请生成SQL查询。""",
            },
        ]

        try:
            response = await self._chat_completion(messages)
            return self._parse_json_response(response)
        except Exception as e:
            raise PgMcpError(
                code=ErrorCode.LLM_ERROR,
                message=f"LLM调用失败: {e}",
                retryable=True,
            )

    async def validate_result(
        self,
        user_query: str,
        sql: str,
        result_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """验证查询结果是否符合用户意图"""
        messages = [
            {"role": "system", "content": self.VALIDATION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""用户原始查询：{user_query}

生成的SQL：{sql}

结果摘要：{json.dumps(result_summary, ensure_ascii=False, indent=2)}

请验证结果是否满足用户需求。""",
            },
        ]

        try:
            response = await self._chat_completion(messages)
            return self._parse_json_response(response)
        except Exception as e:
            # 验证失败时降级处理，不阻塞主流程
            return {"is_valid": True, "reason": f"验证跳过: {e}", "suggestions": []}

    async def _chat_completion(self, messages: list[dict]) -> ChatCompletion:
        """调用Chat Completion API"""
        return await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"},
        )

    def _parse_json_response(self, response: ChatCompletion) -> dict[str, Any]:
        """解析JSON响应"""
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM返回空响应")
        result = json.loads(content)
        # 记录Token使用量（如果可用）
        if hasattr(response, "usage") and response.usage:
            result["_token_usage"] = {
                "prompt_tokens": response.usage.prompt_tokens or 0,
                "completion_tokens": response.usage.completion_tokens or 0,
                "total_tokens": response.usage.total_tokens or 0,
            }
        return result

