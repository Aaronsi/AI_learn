"""Database connection pool manager"""

import asyncio
from urllib.parse import quote_plus
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any

import asyncpg
from asyncpg import Pool as PgPool, Connection as PgConnection

try:
    import aiomysql
    from aiomysql import Pool as MySQLPoolType, Connection as MySQLConnection
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False
    MySQLPoolType = Any  # type: ignore
    MySQLConnection = Any  # type: ignore

from pg_mcp.config.settings import DatabaseConfig
from pg_mcp.models.errors import PgMcpError, ErrorCode
from pg_mcp.infrastructure.db_adapter import BaseDBAdapter, create_adapter


class PostgreSQLPool:
    """PostgreSQL 连接池包装器"""

    def __init__(self, pool: PgPool, config: DatabaseConfig):
        self.pool = pool
        self.config = config

    @asynccontextmanager
    async def acquire(self, timeout: float | None = None) -> AsyncIterator[PgConnection]:
        """获取连接"""
        async with self.pool.acquire(timeout=timeout) as conn:
            yield conn

    async def close(self) -> None:
        """关闭连接池"""
        await self.pool.close()


class MySQLPoolWrapper:
    """MySQL 连接池包装器"""

    def __init__(self, pool: MySQLPoolType, config: DatabaseConfig):
        self.pool = pool
        self.config = config

    @asynccontextmanager
    async def acquire(self, timeout: float | None = None) -> AsyncIterator[MySQLConnection]:
        """获取连接"""
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            self.pool.release(conn)

    async def close(self) -> None:
        """关闭连接池"""
        self.pool.close()
        await self.pool.wait_closed()


class DBPoolManager:
    """数据库连接池管理器 - 支持 PostgreSQL 和 MySQL"""

    def __init__(self):
        self._pools: dict[str, PostgreSQLPool | MySQLPoolWrapper] = {}
        self._configs: dict[str, DatabaseConfig] = {}
        self._lock = asyncio.Lock()

    async def initialize(self, configs: list[DatabaseConfig]) -> None:
        """初始化所有数据库连接池"""
        for config in configs:
            await self._create_pool(config)

    async def _create_pool(self, config: DatabaseConfig) -> None:
        """创建单个数据库连接池"""
        if config.db_type == "postgresql":
            pool = await self._create_postgresql_pool(config)
        elif config.db_type == "mysql":
            if not HAS_MYSQL:
                raise PgMcpError(
                    code=ErrorCode.CONFIGURATION_ERROR,
                    message=f"MySQL支持需要安装aiomysql: pip install aiomysql",
                    retryable=False,
                )
            pool = await self._create_mysql_pool(config)
        else:
            raise PgMcpError(
                code=ErrorCode.CONFIGURATION_ERROR,
                message=f"不支持的数据库类型: {config.db_type}",
                retryable=False,
            )
        self._pools[config.name] = pool
        self._configs[config.name] = config

    async def _create_postgresql_pool(self, config: DatabaseConfig) -> PostgreSQLPool:
        """创建 PostgreSQL 连接池"""
        dsn = self._build_postgresql_dsn(config)
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
            return PostgreSQLPool(pool, config)
        except Exception as e:
            raise PgMcpError(
                code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message=f"无法连接到PostgreSQL数据库 {config.name}: {e}",
                retryable=True,
            )

    async def _create_mysql_pool(self, config: DatabaseConfig) -> MySQLPoolWrapper:
        """创建 MySQL 连接池"""
        if not HAS_MYSQL:
            raise PgMcpError(
                code=ErrorCode.CONFIGURATION_ERROR,
                message="MySQL支持需要安装aiomysql: pip install aiomysql",
                retryable=False,
            )
        password = config.password.get_secret_value()
        try:
            # 使用 DictCursor 以便返回字典格式的结果
            pool = await aiomysql.create_pool(
                host=config.host,
                port=config.port,
                user=config.username,
                password=password,
                db=config.database,
                minsize=config.min_pool_size,
                maxsize=config.max_pool_size,
                autocommit=False,
                charset="utf8mb4",
                cursorclass=aiomysql.DictCursor,  # 返回字典格式
            )
            return MySQLPoolWrapper(pool, config)
        except Exception as e:
            raise PgMcpError(
                code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message=f"无法连接到MySQL数据库 {config.name}: {e}",
                retryable=True,
            )

    def _build_postgresql_dsn(self, config: DatabaseConfig) -> str:
        """构建 PostgreSQL 连接字符串"""
        password = quote_plus(config.password.get_secret_value())
        return (
            f"postgresql://{config.username}:{password}"
            f"@{config.host}:{config.port}/{config.database}"
            f"?sslmode={config.ssl_mode}"
        )

    def get_pool(self, db_name: str) -> PostgreSQLPool | MySQLPoolWrapper:
        """获取指定数据库的连接池"""
        if db_name not in self._pools:
            raise PgMcpError(
                code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message=f"数据库 {db_name} 未配置",
            )
        return self._pools[db_name]

    def get_db_type(self, db_name: str) -> str:
        """获取数据库类型"""
        if db_name not in self._configs:
            raise PgMcpError(
                code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message=f"数据库 {db_name} 未配置",
            )
        return self._configs[db_name].db_type

    @asynccontextmanager
    async def acquire_readonly(
        self, db_name: str, timeout: int = 30
    ) -> AsyncIterator[BaseDBAdapter]:
        """获取只读连接并按需降权，返回统一的适配器接口"""
        pool = self.get_pool(db_name)
        config = self._configs[db_name]

        if config.db_type == "postgresql":
            async with pool.acquire(timeout=timeout) as conn:
                # 可选降权角色
                if config.role:
                    await conn.execute(f"SET ROLE {config.role}")
                # 只读事务与超时（事务内设置 LOCAL）
                async with conn.transaction(readonly=True):
                    await conn.execute(
                        f"SET LOCAL statement_timeout = '{int(timeout * 1000)}ms'"
                    )
                    adapter = create_adapter(conn, "postgresql")
                    yield adapter
        elif config.db_type == "mysql":
            async with pool.acquire(timeout=timeout) as conn:
                # MySQL 设置只读模式和超时（必须在事务开始前设置）
                try:
                    # 使用游标执行设置语句
                    cursor = await conn.cursor()
                    try:
                        # 先设置会话级别的只读和超时
                        await cursor.execute("SET SESSION TRANSACTION READ ONLY")
                        # MySQL 5.7.8+ 支持 max_execution_time
                        try:
                            await cursor.execute(f"SET SESSION max_execution_time = {timeout * 1000}")
                        except Exception:
                            # 如果版本不支持，忽略超时设置
                            pass
                        # 可选降权角色（MySQL 8.0+ 支持 SET ROLE）
                        if config.role:
                            try:
                                await cursor.execute(f"SET ROLE {config.role}")
                            except Exception:
                                # 如果版本不支持 SET ROLE，忽略
                                pass
                    finally:
                        await cursor.close()
                    # 开始只读事务
                    await conn.begin()
                    adapter = create_adapter(conn, "mysql")
                    yield adapter
                finally:
                    await conn.rollback()  # 只读事务回滚
        else:
            raise PgMcpError(
                code=ErrorCode.CONFIGURATION_ERROR,
                message=f"不支持的数据库类型: {config.db_type}",
                retryable=False,
            )

    async def close_all(self) -> None:
        """关闭所有连接池"""
        for pool in self._pools.values():
            await pool.close()
        self._pools.clear()

    def list_databases(self) -> list[str]:
        """列出所有已配置的数据库"""
        return list(self._pools.keys())
