"""Metrics collection and health checks"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.infrastructure.llm_client import LLMClient
from pg_mcp.infrastructure.rate_limiter import RateLimiter
from pg_mcp.services.schema_service import SchemaService


@dataclass
class Metrics:
    """核心指标收集"""

    # 查询执行时间（毫秒）
    query_times: deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    # LLM 调用次数
    llm_calls: int = 0
    llm_successes: int = 0
    llm_failures: int = 0
    # 数据库查询次数
    db_queries: int = 0
    db_successes: int = 0
    db_failures: int = 0
    # 缓存命中次数
    cache_hits: int = 0
    cache_misses: int = 0
    # 结果截断次数
    truncations: int = 0
    # Token 使用量
    total_tokens: int = 0
    total_cost: float = 0.0

    def record_query_time(self, ms: float) -> None:
        """记录查询执行时间"""
        self.query_times.append(ms)

    def record_llm_call(self, success: bool) -> None:
        """记录LLM调用"""
        self.llm_calls += 1
        if success:
            self.llm_successes += 1
        else:
            self.llm_failures += 1

    def record_db_query(self, success: bool) -> None:
        """记录数据库查询"""
        self.db_queries += 1
        if success:
            self.db_successes += 1
        else:
            self.db_failures += 1

    def record_cache_hit(self, hit: bool) -> None:
        """记录缓存命中"""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def record_truncation(self) -> None:
        """记录结果截断"""
        self.truncations += 1

    def record_tokens(self, tokens: int, cost: float = 0.0) -> None:
        """记录Token使用"""
        self.total_tokens += tokens
        self.total_cost += cost

    def get_p50(self) -> float | None:
        """获取P50延迟"""
        if not self.query_times:
            return None
        sorted_times = sorted(self.query_times)
        idx = len(sorted_times) // 2
        return sorted_times[idx]

    def get_p95(self) -> float | None:
        """获取P95延迟"""
        if not self.query_times:
            return None
        sorted_times = sorted(self.query_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx]

    def get_summary(self) -> dict[str, Any]:
        """获取指标摘要"""
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            self.cache_hits / total_requests if total_requests > 0 else 0.0
        )
        truncation_rate = (
            self.truncations / self.db_queries if self.db_queries > 0 else 0.0
        )
        llm_success_rate = (
            self.llm_successes / self.llm_calls if self.llm_calls > 0 else 0.0
        )

        return {
            "query_times": {
                "count": len(self.query_times),
                "p50_ms": self.get_p50(),
                "p95_ms": self.get_p95(),
            },
            "llm": {
                "calls": self.llm_calls,
                "successes": self.llm_successes,
                "failures": self.llm_failures,
                "success_rate": llm_success_rate,
            },
            "db": {
                "queries": self.db_queries,
                "successes": self.db_successes,
                "failures": self.db_failures,
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": cache_hit_rate,
            },
            "truncations": {
                "count": self.truncations,
                "rate": truncation_rate,
            },
            "tokens": {
                "total": self.total_tokens,
                "cost": self.total_cost,
            },
        }


class HealthChecker:
    """健康检查器"""

    def __init__(
        self,
        db_pool: DBPoolManager,
        llm_client: LLMClient,
        schema_service: SchemaService,
        rate_limiter: RateLimiter,
    ):
        self.db_pool = db_pool
        self.llm_client = llm_client
        self.schema_service = schema_service
        self.rate_limiter = rate_limiter

    async def check_health(self) -> dict[str, Any]:
        """执行健康检查"""
        health = {
            "status": "healthy",
            "checks": {},
        }

        # 检查数据库连接
        db_status = await self._check_db()
        health["checks"]["database"] = db_status

        # 检查LLM可用性（简单检查配置）
        llm_status = self._check_llm()
        health["checks"]["llm"] = llm_status

        # 检查缓存状态
        cache_status = self._check_cache()
        health["checks"]["cache"] = cache_status

        # 检查熔断器状态
        circuit_status = self.rate_limiter.get_circuit_status()
        health["checks"]["circuit_breaker"] = circuit_status

        # 如果任何检查失败，整体状态为不健康
        if any(
            check.get("status") != "ok"
            for check in health["checks"].values()
            if isinstance(check, dict)
        ):
            health["status"] = "degraded"

        return health

    async def _check_db(self) -> dict[str, Any]:
        """检查数据库连接"""
        try:
            databases = self.db_pool.list_databases()
            if not databases:
                return {"status": "error", "message": "No databases configured"}
            # 尝试获取一个连接池
            pool = self.db_pool.get_pool(databases[0])
            return {"status": "ok", "databases": len(databases)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_llm(self) -> dict[str, Any]:
        """检查LLM配置"""
        try:
            # 简单检查配置是否存在
            if hasattr(self.llm_client, "config"):
                return {"status": "ok", "model": self.llm_client.config.model}
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_cache(self) -> dict[str, Any]:
        """检查缓存状态"""
        try:
            cached_dbs = len(self.schema_service._cache)
            return {"status": "ok", "cached_databases": cached_dbs}
        except Exception as e:
            return {"status": "error", "message": str(e)}

