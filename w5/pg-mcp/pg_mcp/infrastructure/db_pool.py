"""Database connection pool manager"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
from asyncpg import Pool, Connection

from pg_mcp.config.settings import DatabaseConfig
from pg_mcp.models.errors import PgMcpError, ErrorCode


class DBPoolManager:
    """数据库连接池管理器"""

    def __init__(self):
        self._pools: dict[str, Pool] = {}
        self._configs: dict[str, DatabaseConfig] = {}
        self._lock = asyncio.Lock()

    async def initialize(self, configs: list[DatabaseConfig]) -> None:
        """初始化所有数据库连接池"""
        for config in configs:
            await self._create_pool(config)

    async def _create_pool(self, config: DatabaseConfig) -> Pool:
        """创建单个数据库连接池"""
        dsn = self._build_dsn(config)
        try:
            pool = await asyncpg.create_pool(
                dsn,
                min_size=config.min_pool_size,
                max_size=config.max_pool_size,
                command_timeout=60,
                server_settings={
                    "application_name": "pg_mcp",
                },
            )
            self._pools[config.name] = pool
            self._configs[config.name] = config
            return pool
        except Exception as e:
            raise PgMcpError(
                code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message=f"无法连接到数据库 {config.name}: {e}",
                retryable=True,
            )

    def _build_dsn(self, config: DatabaseConfig) -> str:
        """构建数据库连接字符串"""
        password = config.password.get_secret_value()
        return (
            f"postgresql://{config.username}:{password}"
            f"@{config.host}:{config.port}/{config.database}"
            f"?sslmode={config.ssl_mode}"
        )

    def get_pool(self, db_name: str) -> Pool:
        """获取指定数据库的连接池"""
        if db_name not in self._pools:
            raise PgMcpError(
                code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message=f"数据库 {db_name} 未配置",
            )
        return self._pools[db_name]

    @asynccontextmanager
    async def acquire_readonly(
        self, db_name: str, timeout: int = 30
    ) -> AsyncIterator[Connection]:
        """获取只读连接并按需降权"""
        pool = self.get_pool(db_name)
        config = self._configs[db_name]
        async with pool.acquire(timeout=timeout) as conn:
            # 可选降权角色
            if config.role:
                await conn.execute(f"SET ROLE {config.role}")
            # 设置只读事务与超时
            await conn.execute("SET TRANSACTION READ ONLY")
            await conn.execute(f"SET statement_timeout = '{timeout}s'")
            yield conn

    async def close_all(self) -> None:
        """关闭所有连接池"""
        for pool in self._pools.values():
            await pool.close()
        self._pools.clear()

    def list_databases(self) -> list[str]:
        """列出所有已配置的数据库"""
        return list(self._pools.keys())

