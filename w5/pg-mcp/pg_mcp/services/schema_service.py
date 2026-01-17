"""Schema management service"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pg_mcp.config.settings import CacheConfig
from pg_mcp.infrastructure.db_pool import DBPoolManager
from typing import TYPE_CHECKING
from pg_mcp.models.schema import (
    DatabaseInfo,
    SchemaInfo,
    TableInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    ViewInfo,
    EnumTypeInfo,
    CompositeTypeInfo,
)

if TYPE_CHECKING:
    from pg_mcp.infrastructure.metrics import Metrics


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

    VIEWS_QUERY = """
    SELECT
        v.table_schema,
        v.table_name AS view_name,
        v.view_definition
    FROM information_schema.views v
    WHERE v.table_schema = $1
    ORDER BY v.table_name
    """

    VIEW_COLUMNS_QUERY = """
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

    ENUM_TYPES_QUERY = """
    SELECT
        n.nspname AS schema_name,
        t.typname AS type_name,
        array_agg(e.enumlabel ORDER BY e.enumsortorder) AS values
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = $1
    GROUP BY n.nspname, t.typname
    ORDER BY t.typname
    """

    COMPOSITE_TYPES_QUERY = """
    SELECT
        n.nspname AS schema_name,
        t.typname AS type_name,
        a.attname AS column_name,
        pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
        a.attnotnull AS not_null
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    JOIN pg_attribute a ON a.attrelid = t.typrelid
    WHERE n.nspname = $1
      AND t.typtype = 'c'
      AND a.attnum > 0
      AND NOT a.attisdropped
    ORDER BY t.typname, a.attnum
    """

    INDEXES_QUERY = """
    SELECT
        i.relname AS index_name,
        ix.indisunique AS is_unique,
        ix.indisprimary AS is_primary,
        am.amname AS index_type,
        array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) AS columns
    FROM pg_class t
    JOIN pg_index ix ON t.oid = ix.indrelid
    JOIN pg_class i ON i.oid = ix.indexrelid
    JOIN pg_am am ON i.relam = am.oid
    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
    WHERE t.oid = ($1 || '.' || $2)::regclass
    GROUP BY i.relname, ix.indisunique, ix.indisprimary, am.amname
    ORDER BY i.relname
    """

    def __init__(
        self,
        db_pool: DBPoolManager,
        cache_config: CacheConfig,
        metrics: "Metrics | None" = None,
    ):
        self.db_pool = db_pool
        self.cache_config = cache_config
        self.metrics = metrics
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
                if self.metrics:
                    self.metrics.record_cache_hit(True)
                # 异步刷新，防止冷启动阻塞
                asyncio.create_task(
                    self._refresh_in_background(db_name, schemas, exclude_tables)
                )
                return cached
            if self.metrics:
                self.metrics.record_cache_hit(False)

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
        db_type = self.db_pool.get_db_type(db_name)

        ctx = self.db_pool.acquire_readonly(db_name)
        if asyncio.iscoroutine(ctx):
            ctx = await ctx  # 支持AsyncMock返回的协程上下文
        async with ctx as conn:
            # 获取数据库版本
            version = await conn.fetchval("SELECT version()")
            db_info.version = version

            for schema_name in schemas:
                schema_info = await self._load_schema(
                    conn, schema_name, exclude_tables or [], db_type
                )
                db_info.schemas[schema_name] = schema_info

        return db_info

    async def _load_schema(
        self,
        conn,
        schema_name: str,
        exclude_tables: list[str],
        db_type: str = "postgresql",
    ) -> SchemaInfo:
        """加载单个schema"""
        schema_info = SchemaInfo(name=schema_name)

        # 加载表
        if db_type == "mysql":
            tables = await conn.fetch(
                "SELECT table_schema, table_name, table_comment, "
                "table_rows as row_estimate "
                "FROM information_schema.tables "
                "WHERE table_schema = %s AND table_type = 'BASE TABLE' "
                "ORDER BY table_name",
                schema_name
            )
        else:
            tables = await conn.fetch(self.TABLES_QUERY, schema_name)
        
        for table_row in tables:
            table_name = table_row.get("table_name") or table_row.get("TABLE_NAME")
            if any(
                self._match_pattern(table_name, p)
                for p in exclude_tables
            ):
                continue
            table_info = await self._load_table(conn, schema_name, table_row, db_type)
            schema_info.tables[table_info.table_name] = table_info

        # 加载视图
        if db_type == "mysql":
            views = await conn.fetch(
                "SELECT table_schema, table_name as view_name, view_definition "
                "FROM information_schema.views "
                "WHERE table_schema = %s "
                "ORDER BY table_name",
                schema_name
            )
        else:
            views = await conn.fetch(self.VIEWS_QUERY, schema_name)
        
        for view_row in views:
            view_info = await self._load_view(conn, schema_name, view_row, db_type)
            schema_info.views[view_info.view_name] = view_info

        # 加载枚举类型（仅PostgreSQL）
        if db_type != "mysql":
            enum_rows = await conn.fetch(self.ENUM_TYPES_QUERY, schema_name)
            for row in enum_rows:
                enum_info = EnumTypeInfo(
                    schema_name=row["schema_name"],
                    type_name=row["type_name"],
                    values=row["values"],
                )
                schema_info.enum_types[enum_info.type_name] = enum_info

            # 加载复合类型（仅PostgreSQL）
            composite_rows = await conn.fetch(self.COMPOSITE_TYPES_QUERY, schema_name)
            if composite_rows:
                schema_info.composite_types = self._group_composite_types(
                    composite_rows
                )

        return schema_info

    async def _load_table(self, conn, schema_name: str, table_row, db_type: str = "postgresql") -> TableInfo:
        """加载单个表的详细信息"""
        table_name = table_row.get("table_name") or table_row.get("TABLE_NAME")

        # 加载列
        if db_type == "mysql":
            columns_rows = await conn.fetch(
                "SELECT column_name, data_type, "
                "CASE WHEN is_nullable = 'YES' THEN true ELSE false END as nullable, "
                "column_default, column_comment as comment "
                "FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s "
                "ORDER BY ordinal_position",
                schema_name, table_name
            )
        else:
            columns_rows = await conn.fetch(
                self.COLUMNS_QUERY, schema_name, table_name
            )
        
        columns = [
            ColumnInfo(
                name=row.get("column_name") or row.get("COLUMN_NAME"),
                data_type=row.get("data_type") or row.get("DATA_TYPE"),
                nullable=row.get("nullable") if "nullable" in row else (row.get("IS_NULLABLE") == "YES"),
                default=row.get("column_default") or row.get("COLUMN_DEFAULT"),
                comment=row.get("comment") or row.get("COLUMN_COMMENT"),
            )
            for row in columns_rows
        ]

        # 加载主键
        if db_type == "mysql":
            pk_rows = await conn.fetch(
                "SELECT column_name "
                "FROM information_schema.key_column_usage "
                "WHERE table_schema = %s AND table_name = %s "
                "AND constraint_name = 'PRIMARY' "
                "ORDER BY ordinal_position",
                schema_name, table_name
            )
            primary_key = [row.get("column_name") or row.get("COLUMN_NAME") for row in pk_rows]
        else:
            pk_rows = await conn.fetch(
                self.PRIMARY_KEY_QUERY, schema_name, table_name
            )
            primary_key = [row.get("attname") or row.get("ATTNAME") for row in pk_rows]

        # 标记主键列
        pk_set = set(primary_key)
        for col in columns:
            if col.name in pk_set:
                col.is_primary_key = True

        # 加载外键
        if db_type == "mysql":
            fk_rows = await conn.fetch(
                "SELECT constraint_name, column_name, "
                "referenced_table_schema as references_schema, "
                "referenced_table_name as references_table, "
                "referenced_column_name as references_column "
                "FROM information_schema.key_column_usage "
                "WHERE table_schema = %s AND table_name = %s "
                "AND referenced_table_name IS NOT NULL "
                "ORDER BY constraint_name, ordinal_position",
                schema_name, table_name
            )
        else:
            fk_rows = await conn.fetch(
                self.FOREIGN_KEYS_QUERY, schema_name, table_name
            )
        foreign_keys = self._group_foreign_keys(fk_rows)

        # 加载索引
        if db_type == "mysql":
            index_rows = await conn.fetch(
                "SELECT index_name, "
                "GROUP_CONCAT(column_name ORDER BY seq_in_index) as columns, "
                "CASE WHEN non_unique = 0 THEN true ELSE false END as is_unique, "
                "CASE WHEN index_name = 'PRIMARY' THEN true ELSE false END as is_primary, "
                "index_type "
                "FROM information_schema.statistics "
                "WHERE table_schema = %s AND table_name = %s "
                "GROUP BY index_name, non_unique, index_type "
                "ORDER BY index_name",
                schema_name, table_name
            )
            indexes = []
            for row in index_rows:
                columns_str = row.get("columns") or row.get("COLUMNS") or ""
                indexes.append(IndexInfo(
                    name=row.get("index_name") or row.get("INDEX_NAME"),
                    columns=columns_str.split(",") if columns_str else [],
                    is_unique=row.get("is_unique") if "is_unique" in row else (row.get("NON_UNIQUE") == 0),
                    is_primary=row.get("is_primary") if "is_primary" in row else (row.get("INDEX_NAME") == "PRIMARY"),
                    index_type=row.get("index_type") or row.get("INDEX_TYPE") or "",
                ))
        else:
            index_rows = await conn.fetch(
                self.INDEXES_QUERY, schema_name, table_name
            )
            indexes = [
                IndexInfo(
                    name=row.get("index_name") or row.get("INDEX_NAME"),
                    columns=row.get("columns") or row.get("COLUMNS") or [],
                    is_unique=row.get("is_unique") if "is_unique" in row else row.get("IS_UNIQUE"),
                    is_primary=row.get("is_primary") if "is_primary" in row else row.get("IS_PRIMARY"),
                    index_type=row.get("index_type") or row.get("INDEX_TYPE") or "",
                )
                for row in index_rows
            ]

        return TableInfo(
            schema_name=schema_name,
            table_name=table_name,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            indexes=indexes,
            comment=table_row.get("table_comment") or table_row.get("TABLE_COMMENT") or "",
            row_estimate=table_row["row_estimate"],
        )

    async def _load_view(self, conn, schema_name: str, view_row, db_type: str = "postgresql") -> ViewInfo:
        """加载单个视图信息"""
        view_name = view_row.get("view_name") or view_row.get("VIEW_NAME")
        
        if db_type == "mysql":
            columns_rows = await conn.fetch(
                "SELECT column_name, data_type, "
                "CASE WHEN is_nullable = 'YES' THEN true ELSE false END as nullable, "
                "column_default, column_comment as comment "
                "FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s "
                "ORDER BY ordinal_position",
                schema_name, view_name
            )
        else:
            columns_rows = await conn.fetch(
                self.VIEW_COLUMNS_QUERY, schema_name, view_name
            )
        
        columns = [
            ColumnInfo(
                name=row.get("column_name") or row.get("COLUMN_NAME"),
                data_type=row.get("data_type") or row.get("DATA_TYPE"),
                nullable=row.get("nullable") if "nullable" in row else (row.get("IS_NULLABLE") == "YES"),
                default=row.get("column_default") or row.get("COLUMN_DEFAULT"),
                comment=row.get("comment") or row.get("COLUMN_COMMENT"),
            )
            for row in columns_rows
        ]
        return ViewInfo(
            schema_name=schema_name,
            view_name=view_name,
            columns=columns,
            definition=view_row.get("view_definition") or view_row.get("VIEW_DEFINITION") or "",
        )

    def _group_foreign_keys(self, fk_rows) -> list[ForeignKeyInfo]:
        """将外键行分组"""
        fk_map: dict[str, ForeignKeyInfo] = {}
        for row in fk_rows:
            name = row.get("constraint_name") or row.get("CONSTRAINT_NAME")
            if name not in fk_map:
                fk_map[name] = ForeignKeyInfo(
                    name=name,
                    columns=[],
                    references_schema=row.get("references_schema") or row.get("REFERENCES_SCHEMA"),
                    references_table=row.get("references_table") or row.get("REFERENCES_TABLE"),
                    references_columns=[],
                )
            col_name = row.get("column_name") or row.get("COLUMN_NAME")
            ref_col = row.get("references_column") or row.get("REFERENCES_COLUMN")
            if col_name:
                fk_map[name].columns.append(col_name)
            if ref_col:
                fk_map[name].references_columns.append(ref_col)
        return list(fk_map.values())

    def _group_composite_types(self, rows) -> dict[str, CompositeTypeInfo]:
        """将复合类型列分组"""
        composite_map: dict[str, CompositeTypeInfo] = {}
        for row in rows:
            type_name = row["type_name"]
            if type_name not in composite_map:
                composite_map[type_name] = CompositeTypeInfo(
                    schema_name=row["schema_name"],
                    type_name=type_name,
                    attributes=[],
                )
            composite_map[type_name].attributes.append(
                ColumnInfo(
                    name=row["column_name"],
                    data_type=row["data_type"],
                    nullable=not row["not_null"],
                )
            )
        return composite_map

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
            if table.indexes:
                lines.append("  Indexes:")
                for idx in table.indexes:
                    flags = []
                    if idx.is_primary:
                        flags.append("PRIMARY")
                    if idx.is_unique:
                        flags.append("UNIQUE")
                    flag_text = f" ({', '.join(flags)})" if flags else ""
                    lines.append(
                        f"    - {idx.name}{flag_text}: {idx.columns} [{idx.index_type}]"
                    )

        if schema_info.views:
            lines.append("\nViews:")
            for view in schema_info.views.values():
                lines.append(f"  - {view.view_name}")

        if schema_info.enum_types:
            lines.append("\nEnum Types:")
            for enum in schema_info.enum_types.values():
                lines.append(f"  - {enum.type_name}: {enum.values}")

        if schema_info.composite_types:
            lines.append("\nComposite Types:")
            for comp in schema_info.composite_types.values():
                attr_names = [attr.name for attr in comp.attributes]
                lines.append(f"  - {comp.type_name}: {attr_names}")
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

