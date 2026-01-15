"""Schema management service"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pg_mcp.config.settings import CacheConfig
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.models.schema import (
    DatabaseInfo,
    SchemaInfo,
    TableInfo,
    ColumnInfo,
    ForeignKeyInfo,
)
from pg_mcp.models.errors import PgMcpError, ErrorCode


class SchemaService:
    """Schema管理服务"""

    # Schema加载SQL
    TABLES_QUERY = """
    SELECT
        t.table_schema,
        t.table_name,
        obj_description((t.table_schema || '.' || t.table_name)::regclass) as table_comment,
        (SELECT reltuples::bigint FROM pg_class WHERE oid = (t.table_schema || '.' || t.table_name)::regclass) as row_estimate
    FROM information_schema.tables t
    WHERE t.table_schema = $1 AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name
    """

    COLUMNS_QUERY = """
    SELECT
        c.column_name,
        c.data_type,
        c.is_nullable = 'YES' as nullable,
        c.column_default,
        col_description((c.table_schema || '.' || c.table_name)::regclass, c.ordinal_position) as comment
    FROM information_schema.columns c
    WHERE c.table_schema = $1 AND c.table_name = $2
    ORDER BY c.ordinal_position
    """

    PRIMARY_KEY_QUERY = """
    SELECT a.attname
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = ($1 || '.' || $2)::regclass AND i.indisprimary
    """

    FOREIGN_KEYS_QUERY = """
    SELECT
        tc.constraint_name,
        kcu.column_name,
        ccu.table_schema AS references_schema,
        ccu.table_name AS references_table,
        ccu.column_name AS references_column
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.table_schema = $1 AND tc.table_name = $2 AND tc.constraint_type = 'FOREIGN KEY'
    """

    def __init__(
        self,
        db_pool: DBPoolManager,
        cache_config: CacheConfig,
    ):
        self.db_pool = db_pool
        self.cache_config = cache_config
        self._cache: dict[str, DatabaseInfo] = {}
        self._lock = asyncio.Lock()
        self._refresh_status: dict[str, dict[str, Any]] = {}
        self._refresh_tasks: dict[str, asyncio.Task] = {}

    async def load_all(
        self,
        db_name: str,
        schemas: list[str],
        exclude_tables: list[str] | None = None,
    ) -> DatabaseInfo:
        """加载数据库的所有schema信息（支持磁盘缓存、TTL、后台刷新）"""
        async with self._lock:
            cached = (
                self._load_from_disk(db_name)
                if self.cache_config.enable_disk_cache
                else None
            )
            if cached and self._is_cache_valid(cached):
                self._cache[db_name] = cached
                # 异步刷新，防止冷启动阻塞
                asyncio.create_task(
                    self._refresh_in_background(db_name, schemas, exclude_tables)
                )
                return cached

            # 从数据库加载
            db_info = await self._load_from_db(db_name, schemas, exclude_tables)
            self._cache[db_name] = db_info

            # 持久化到磁盘
            if self.cache_config.enable_disk_cache:
                self._save_to_disk(db_name, db_info)

            return db_info

    async def _load_from_db(
        self,
        db_name: str,
        schemas: list[str],
        exclude_tables: list[str] | None = None,
    ) -> DatabaseInfo:
        """从数据库加载schema信息"""
        db_info = DatabaseInfo(name=db_name, loaded_at=datetime.now().isoformat())

        ctx = self.db_pool.acquire_readonly(db_name)
        if asyncio.iscoroutine(ctx):
            ctx = await ctx  # 支持AsyncMock返回的协程上下文
        async with ctx as conn:
            # 获取PG版本
            version = await conn.fetchval("SELECT version()")
            db_info.version = version

            for schema_name in schemas:
                schema_info = await self._load_schema(
                    conn, schema_name, exclude_tables or []
                )
                db_info.schemas[schema_name] = schema_info

        return db_info

    async def _load_schema(
        self,
        conn,
        schema_name: str,
        exclude_tables: list[str],
    ) -> SchemaInfo:
        """加载单个schema"""
        schema_info = SchemaInfo(name=schema_name)

        # 加载表
        tables = await conn.fetch(self.TABLES_QUERY, schema_name)
        for table_row in tables:
            if any(
                self._match_pattern(table_row["table_name"], p)
                for p in exclude_tables
            ):
                continue
            table_info = await self._load_table(conn, schema_name, table_row)
            schema_info.tables[table_info.table_name] = table_info

        return schema_info

    async def _load_table(self, conn, schema_name: str, table_row) -> TableInfo:
        """加载单个表的详细信息"""
        table_name = table_row["table_name"]

        # 加载列
        columns_rows = await conn.fetch(
            self.COLUMNS_QUERY, schema_name, table_name
        )
        columns = [
            ColumnInfo(
                name=row["column_name"],
                data_type=row["data_type"],
                nullable=row["nullable"],
                default=row["column_default"],
                comment=row["comment"],
            )
            for row in columns_rows
        ]

        # 加载主键
        pk_rows = await conn.fetch(
            self.PRIMARY_KEY_QUERY, schema_name, table_name
        )
        primary_key = [row["attname"] for row in pk_rows]

        # 标记主键列
        pk_set = set(primary_key)
        for col in columns:
            if col.name in pk_set:
                col.is_primary_key = True

        # 加载外键
        fk_rows = await conn.fetch(
            self.FOREIGN_KEYS_QUERY, schema_name, table_name
        )
        foreign_keys = self._group_foreign_keys(fk_rows)

        return TableInfo(
            schema_name=schema_name,
            table_name=table_name,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            comment=table_row["table_comment"],
            row_estimate=table_row["row_estimate"],
        )

    def _group_foreign_keys(self, fk_rows) -> list[ForeignKeyInfo]:
        """将外键行分组"""
        fk_map: dict[str, ForeignKeyInfo] = {}
        for row in fk_rows:
            name = row["constraint_name"]
            if name not in fk_map:
                fk_map[name] = ForeignKeyInfo(
                    name=name,
                    columns=[],
                    references_schema=row["references_schema"],
                    references_table=row["references_table"],
                    references_columns=[],
                )
            fk_map[name].columns.append(row["column_name"])
            fk_map[name].references_columns.append(row["references_column"])
        return list(fk_map.values())

    def get_cached(self, db_name: str) -> DatabaseInfo | None:
        """获取缓存的schema信息"""
        return self._cache.get(db_name)

    def format_for_llm(self, db_name: str, schema_name: str) -> str:
        """格式化schema信息供LLM使用"""
        db_info = self._cache.get(db_name)
        if not db_info:
            return ""

        schema_info = db_info.schemas.get(schema_name)
        if not schema_info:
            return ""

        lines = [f"Schema: {schema_name}\n"]
        for table_name, table in schema_info.tables.items():
            lines.append(f"\nTable: {table_name}")
            if table.comment:
                lines.append(f"  Comment: {table.comment}")
            lines.append("  Columns:")
            for col in table.columns:
                pk = " [PK]" if col.is_primary_key else ""
                nullable = " NULL" if col.nullable else " NOT NULL"
                comment = f" -- {col.comment}" if col.comment else ""
                lines.append(
                    f"    - {col.name}: {col.data_type}{nullable}{pk}{comment}"
                )
            if table.foreign_keys:
                lines.append("  Foreign Keys:")
                for fk in table.foreign_keys:
                    lines.append(
                        f"    - {fk.columns} -> {fk.references_schema}.{fk.references_table}({fk.references_columns})"
                    )
        return "\n".join(lines)

    def _load_from_disk(self, db_name: str) -> DatabaseInfo | None:
        """从磁盘加载缓存"""
        cache_file = self.cache_config.cache_dir / f"{db_name}.json"
        if not cache_file.exists():
            return None
        try:
            data = json.loads(cache_file.read_text())
            return DatabaseInfo.model_validate(data)
        except Exception:
            return None

    def _is_cache_valid(self, db_info: DatabaseInfo) -> bool:
        """判断磁盘缓存是否过期"""
        if not db_info.loaded_at:
            return False
        ttl_hours = self.cache_config.cache_ttl_hours
        if ttl_hours <= 0:
            return False
        loaded_time = datetime.fromisoformat(db_info.loaded_at)
        age_hours = (datetime.now() - loaded_time).total_seconds() / 3600
        return age_hours <= ttl_hours

    def _save_to_disk(self, db_name: str, db_info: DatabaseInfo) -> None:
        """保存缓存到磁盘"""
        self.cache_config.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_config.cache_dir / f"{db_name}.json"
        cache_file.write_text(db_info.model_dump_json(indent=2))

    async def _refresh_in_background(
        self,
        db_name: str,
        schemas: list[str],
        exclude_tables: list[str] | None = None,
    ) -> None:
        """后台刷新缓存，失败不阻塞主流程"""
        try:
            db_info = await self._load_from_db(db_name, schemas, exclude_tables)
            self._cache[db_name] = db_info
            if self.cache_config.enable_disk_cache:
                self._save_to_disk(db_name, db_info)
            self._update_refresh_status(db_name, "success", None)
        except Exception as e:
            # 刷新失败时保留旧缓存，记录错误
            self._update_refresh_status(db_name, "failed", str(e))

    def _update_refresh_status(
        self, db_name: str, status: str, error: str | None
    ) -> None:
        """更新刷新状态"""
        self._refresh_status[db_name] = {
            "last_refresh_time": datetime.now().isoformat(),
            "refresh_status": status,
            "error": error,
        }

    def get_refresh_status(self, db_name: str) -> dict[str, Any] | None:
        """获取刷新状态"""
        return self._refresh_status.get(db_name)

    def start_auto_refresh(
        self,
        db_name: str,
        schemas: list[str],
        exclude_tables: list[str] | None = None,
    ) -> None:
        """启动定时自动刷新任务"""
        if self.cache_config.auto_refresh_interval_hours <= 0:
            return
        if db_name in self._refresh_tasks:
            return

        async def refresh_loop():
            interval = timedelta(
                hours=self.cache_config.auto_refresh_interval_hours
            )
            while True:
                await asyncio.sleep(interval.total_seconds())
                await self._refresh_in_background(db_name, schemas, exclude_tables)

        self._refresh_tasks[db_name] = asyncio.create_task(refresh_loop())

    def stop_auto_refresh(self) -> None:
        """停止定时自动刷新任务"""
        for task in self._refresh_tasks.values():
            task.cancel()
        self._refresh_tasks.clear()

    def _match_pattern(self, value: str, pattern: str) -> bool:
        """简单支持通配符的表名匹配"""
        return Path(value).match(pattern)

