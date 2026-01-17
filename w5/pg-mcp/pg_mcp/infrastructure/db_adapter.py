"""Database adapter layer for unified database access"""

from typing import Any, Protocol
from abc import ABC, abstractmethod

try:
    import aiomysql
    from aiomysql import Connection as MySQLConnection
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False
    MySQLConnection = Any  # type: ignore

from asyncpg import Connection as PgConnection


class DBConnection(Protocol):
    """数据库连接协议接口"""

    async def execute(self, query: str, *args: Any) -> Any:
        """执行SQL语句"""
        ...

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        """执行查询并返回所有行"""
        ...

    async def fetchval(self, query: str, *args: Any) -> Any:
        """执行查询并返回单个值"""
        ...


class BaseDBAdapter(ABC):
    """数据库适配器基类"""

    @abstractmethod
    async def execute(self, query: str, *args: Any) -> Any:
        """执行SQL语句"""
        pass

    @abstractmethod
    async def fetch(self, query: str, *args: Any) -> list[Any]:
        """执行查询并返回所有行"""
        pass

    @abstractmethod
    async def fetchval(self, query: str, *args: Any) -> Any:
        """执行查询并返回单个值"""
        pass


class PostgreSQLAdapter(BaseDBAdapter):
    """PostgreSQL 适配器"""

    def __init__(self, conn: PgConnection):
        self.conn = conn

    async def execute(self, query: str, *args: Any) -> Any:
        """执行SQL语句"""
        return await self.conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        """执行查询并返回所有行"""
        return await self.conn.fetch(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        """执行查询并返回单个值"""
        return await self.conn.fetchval(query, *args)


class MySQLAdapter(BaseDBAdapter):
    """MySQL 适配器 - 为 aiomysql 连接提供 fetch/fetchval 接口"""

    def __init__(self, conn: MySQLConnection):
        if not HAS_MYSQL:
            raise RuntimeError("aiomysql is not installed")
        self.conn = conn

    async def execute(self, query: str, *args: Any) -> Any:
        """执行SQL语句"""
        cursor = await self.conn.cursor()
        try:
            # MySQL 使用 %s 占位符，但 aiomysql 会自动处理
            # 如果 args 为空，直接执行；否则使用参数化查询
            if args:
                await cursor.execute(query, args)
            else:
                await cursor.execute(query)
            return cursor.rowcount
        finally:
            await cursor.close()

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        """执行查询并返回所有行（字典格式）"""
        cursor = await self.conn.cursor(aiomysql.DictCursor)
        try:
            if args:
                await cursor.execute(query, args)
            else:
                await cursor.execute(query)
            rows = await cursor.fetchall()
            # 转换为字典列表
            return [dict(row) for row in rows] if rows else []
        finally:
            await cursor.close()

    async def fetchval(self, query: str, *args: Any) -> Any:
        """执行查询并返回单个值"""
        cursor = await self.conn.cursor(aiomysql.DictCursor)
        try:
            if args:
                await cursor.execute(query, args)
            else:
                await cursor.execute(query)
            row = await cursor.fetchone()
            if row:
                # 返回第一列的值
                values = list(row.values()) if isinstance(row, dict) else list(row)
                return values[0] if values else None
            return None
        finally:
            await cursor.close()


def create_adapter(conn: Any, db_type: str) -> BaseDBAdapter:
    """创建数据库适配器"""
    if db_type == "postgresql":
        return PostgreSQLAdapter(conn)
    elif db_type == "mysql":
        if not HAS_MYSQL:
            raise RuntimeError("MySQL support requires aiomysql")
        return MySQLAdapter(conn)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

