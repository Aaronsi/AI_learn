"""Result validation service"""

from pg_mcp.infrastructure.llm_client import LLMClient
from pg_mcp.security.sanitizer import Sanitizer
from pg_mcp.models.query import QueryResultData


class ValidationService:
    """结果验证服务：对LLM生成的SQL结果进行意图校验"""

    def __init__(
        self,
        sanitizer: Sanitizer,
        llm_client: LLMClient,
        sample_rows: int,
        sample_cols: int,
    ):
        self.sanitizer = sanitizer
        self.llm_client = llm_client
        self.sample_rows = sample_rows
        self.sample_cols = sample_cols

    async def validate(
        self, user_query: str, sql: str, result: QueryResultData
    ) -> dict:
        """返回验证结果和说明，不阻断主流程"""
        _, safe_rows = self.sanitizer.sanitize_for_llm(
            result.columns,
            result.rows,
            max_rows=self.sample_rows,
            max_cols=self.sample_cols,
        )
        summary = self.sanitizer.generate_summary(
            result.columns, result.rows, result.row_count
        )
        return await self.llm_client.validate_result(user_query, sql, summary)

