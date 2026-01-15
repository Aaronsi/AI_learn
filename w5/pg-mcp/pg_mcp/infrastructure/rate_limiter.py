"""Rate limiter and circuit breaker"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from aiolimiter import AsyncLimiter

from pg_mcp.config.settings import RateLimitConfig
from pg_mcp.models.errors import PgMcpError, ErrorCode


class CircuitState(Enum):
    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class CircuitBreaker:
    """熔断器"""

    threshold: int
    timeout: int
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: datetime | None = None

    def record_failure(self) -> None:
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN

    def record_success(self) -> None:
        """记录成功"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        """检查是否可以执行"""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                elapsed = datetime.now() - self.last_failure_time
                if elapsed > timedelta(seconds=self.timeout):
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
        return True  # HALF_OPEN允许尝试


class RateLimiter:
    """限流管理器"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.llm_limiter = AsyncLimiter(
            config.llm_requests_per_minute, 60
        )
        self.db_limiter = AsyncLimiter(config.db_queries_per_minute, 60)
        self.llm_circuit = CircuitBreaker(
            threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout,
        )
        self.db_circuit = CircuitBreaker(
            threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout,
        )

    async def acquire_llm(self) -> None:
        """获取LLM调用许可"""
        if not self.config.enable_circuit_breaker:
            await self.llm_limiter.acquire()
            return

        if not self.llm_circuit.can_execute():
            raise PgMcpError(
                code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message="LLM服务熔断中",
                retryable=True,
                details={"retry_after_ms": self.config.circuit_breaker_timeout * 1000},
            )
        await self.llm_limiter.acquire()

    async def acquire_db(self) -> None:
        """获取数据库查询许可"""
        if not self.config.enable_circuit_breaker:
            await self.db_limiter.acquire()
            return

        if not self.db_circuit.can_execute():
            raise PgMcpError(
                code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message="数据库服务熔断中",
                retryable=True,
                details={"retry_after_ms": self.config.circuit_breaker_timeout * 1000},
            )
        await self.db_limiter.acquire()

    def record_llm_success(self) -> None:
        """记录LLM调用成功"""
        if self.config.enable_circuit_breaker:
            self.llm_circuit.record_success()

    def record_llm_failure(self) -> None:
        """记录LLM调用失败"""
        if self.config.enable_circuit_breaker:
            self.llm_circuit.record_failure()

    def record_db_success(self) -> None:
        """记录数据库调用成功"""
        if self.config.enable_circuit_breaker:
            self.db_circuit.record_success()

    def record_db_failure(self) -> None:
        """记录数据库调用失败"""
        if self.config.enable_circuit_breaker:
            self.db_circuit.record_failure()

    def get_circuit_status(self) -> dict[str, dict[str, str]]:
        """获取熔断器状态"""
        return {
            "llm": {
                "state": self.llm_circuit.state.value,
                "failure_count": str(self.llm_circuit.failure_count),
            },
            "db": {
                "state": self.db_circuit.state.value,
                "failure_count": str(self.db_circuit.failure_count),
            },
        }

