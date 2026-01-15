"""Query request/response models"""

from pydantic import BaseModel, Field
from typing import Literal, Any


class QueryRequest(BaseModel):
    """查询请求"""

    query: str = Field(..., description="自然语言查询描述")
    database: str | None = Field(default=None, description="目标数据库")
    schema_name: str = Field(default="public", description="目标schema", alias="schema")
    return_type: Literal["sql", "result"] = Field(default="result")
    max_rows: int | None = Field(default=None, ge=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)


class SQLGenerationResult(BaseModel):
    """SQL生成结果"""

    sql: str
    explanation: str
    confidence: float = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class QueryResultData(BaseModel):
    """查询结果数据"""

    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    total_count: int | None = None  # 总行数（如果可知）
    truncated: bool = False
    page: int = 1
    page_size: int = 100
    execution_time_ms: int
    explanation: str


class QueryResponse(BaseModel):
    """查询响应"""

    success: bool
    data: SQLGenerationResult | QueryResultData | None = None
    error: "ErrorDetail | None" = None


class ErrorDetail(BaseModel):
    """错误详情"""

    code: str
    type: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    retryable: bool = False
    suggestion: str | None = None
    retry_after_ms: int | None = None

