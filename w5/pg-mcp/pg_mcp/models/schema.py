"""Schema data models"""

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    """列信息"""

    name: str
    data_type: str
    nullable: bool = True
    default: str | None = None
    comment: str | None = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: str | None = None  # 格式: "schema.table.column"


class IndexInfo(BaseModel):
    """索引信息"""

    name: str
    columns: list[str]
    is_unique: bool = False
    is_primary: bool = False
    index_type: str = "btree"  # btree, hash, gin, gist, etc.


class ForeignKeyInfo(BaseModel):
    """外键信息"""

    name: str
    columns: list[str]
    references_schema: str
    references_table: str
    references_columns: list[str]
    on_delete: str = "NO ACTION"
    on_update: str = "NO ACTION"


class TableInfo(BaseModel):
    """表信息"""

    schema_name: str
    table_name: str
    columns: list[ColumnInfo]
    primary_key: list[str] = Field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = Field(default_factory=list)
    indexes: list[IndexInfo] = Field(default_factory=list)
    comment: str | None = None
    row_estimate: int | None = None  # 估算行数


class ViewInfo(BaseModel):
    """视图信息"""

    schema_name: str
    view_name: str
    columns: list[ColumnInfo]
    definition: str | None = None
    comment: str | None = None


class EnumTypeInfo(BaseModel):
    """枚举类型信息"""

    schema_name: str
    type_name: str
    values: list[str]


class CompositeTypeInfo(BaseModel):
    """复合类型信息"""

    schema_name: str
    type_name: str
    attributes: list[ColumnInfo]


class SchemaInfo(BaseModel):
    """Schema信息"""

    name: str
    tables: dict[str, TableInfo] = Field(default_factory=dict)
    views: dict[str, ViewInfo] = Field(default_factory=dict)
    enum_types: dict[str, EnumTypeInfo] = Field(default_factory=dict)
    composite_types: dict[str, CompositeTypeInfo] = Field(default_factory=dict)


class DatabaseInfo(BaseModel):
    """数据库信息"""

    name: str
    schemas: dict[str, SchemaInfo] = Field(default_factory=dict)
    version: str | None = None
    loaded_at: str | None = None  # ISO格式时间戳

