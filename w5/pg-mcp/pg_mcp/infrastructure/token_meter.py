"""Token metering and cost control"""

from dataclasses import dataclass, field
from typing import Callable

from pg_mcp.infrastructure.metrics import Metrics


@dataclass
class TokenMeter:
    """Token计量和成本控制"""

    metrics: Metrics
    threshold: int = 1_000_000  # 默认阈值：100万tokens
    cost_threshold: float = 100.0  # 默认成本阈值：$100
    alert_callback: Callable[[str, dict], None] | None = None
    degraded_mode: bool = False

    def record_usage(
        self, prompt_tokens: int, completion_tokens: int, cost: float = 0.0
    ) -> None:
        """记录Token使用"""
        total_tokens = prompt_tokens + completion_tokens
        self.metrics.record_tokens(total_tokens, cost)

        # 检查阈值
        if self.metrics.total_tokens >= self.threshold:
            self._trigger_alert("token_threshold", {
                "total_tokens": self.metrics.total_tokens,
                "threshold": self.threshold,
            })
            self.degraded_mode = True

        if self.metrics.total_cost >= self.cost_threshold:
            self._trigger_alert("cost_threshold", {
                "total_cost": self.metrics.total_cost,
                "threshold": self.cost_threshold,
            })
            self.degraded_mode = True

    def _trigger_alert(self, alert_type: str, details: dict) -> None:
        """触发告警"""
        message = f"Token meter alert: {alert_type}"
        if self.alert_callback:
            self.alert_callback(message, details)
        else:
            # 默认日志输出
            print(f"WARNING: {message} - {details}")

    def should_skip_validation(self) -> bool:
        """是否应该跳过结果验证（降级策略）"""
        return self.degraded_mode

    def should_return_sql_only(self) -> bool:
        """是否应该只返回SQL（降级策略）"""
        return self.degraded_mode and self.metrics.total_tokens >= self.threshold * 1.5

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_tokens": self.metrics.total_tokens,
            "total_cost": self.metrics.total_cost,
            "threshold": self.threshold,
            "cost_threshold": self.cost_threshold,
            "degraded_mode": self.degraded_mode,
        }

