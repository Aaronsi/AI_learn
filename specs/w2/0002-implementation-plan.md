# DB Query Tool 实现计划

## 里程碑

- **M0 准备**：环境就绪（Python 3.12+、uv、Node 18+、本地 PostgreSQL、设置 `DeepSeek_API_KEY`）
- **M1 后端基础**：项目结构、SQLite 数据库模型、配置管理、CORS 设置
- **M2 数据库连接管理**：连接 CRUD API、连接测试、PostgreSQL 连接支持
- **M3 Metadata 获取与存储**：PostgreSQL metadata 查询、DeepSeek LLM 转换、SQLite 存储
- **M4 SQL 查询功能**：SQL 解析验证（sqlglot）、SELECT 限制、LIMIT 自动添加、查询执行
- **M5 自然语言生成 SQL**：DeepSeek API 集成、Context 构建、SQL 生成与验证
- **M6 前端基础**：React + Refine 5 项目搭建、Monaco Editor 集成、API 客户端
- **M7 前端功能实现**：连接管理 UI、Metadata 展示、SQL 编辑器、查询结果表格、自然语言查询
- **M8 测试与优化**：单元测试、集成测试、错误处理完善、性能优化

## 代码结构（目标）

- 根目录：`./w2/db_query/`
- 后端：`backend/`（FastAPI + SQLite + PostgreSQL）
- 前端：`frontend/`（React + Refine 5 + Monaco Editor）
- SQLite 数据库：`~/.db_query/db_query.db`（用户主目录）
- 配置文件：`.env.example`、`pyproject.toml`

## 后端实现步骤（FastAPI + SQLite + PostgreSQL）

### 1) 项目骨架

**目录结构：**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口
│   ├── config.py        # 配置管理（环境变量）
│   ├── db.py            # SQLite 数据库连接
│   ├── models.py        # SQLAlchemy 模型
│   ├── schemas.py       # Pydantic 模型（camelCase）
│   ├── routes/
│   │   ├── __init__.py
│   │   └── databases.py # 数据库连接和查询路由
│   └── services/
│       ├── __init__.py
│       ├── database.py  # 数据库连接服务
│       ├── metadata.py  # Metadata 获取与存储
│       ├── sql_parser.py # SQL 解析与验证
│       └── llm.py       # DeepSeek LLM 服务
├── pyproject.toml
└── README.md
```

**依赖（使用 uv 安装）：**
```toml
dependencies = [
    "fastapi>=0.111,<1.0",
    "uvicorn[standard]>=0.30,<1.0",
    "SQLAlchemy[asyncio]>=2.0,<3.0",
    "aiosqlite>=0.19,<1.0",          # SQLite 异步驱动
    "asyncpg>=0.29,<1.0",            # PostgreSQL 异步驱动
    "pydantic>=2.7,<3.0",
    "pydantic-settings>=2.0,<3.0",
    "sqlglot>=24.0,<25.0",           # SQL 解析
    "openai>=1.0,<2.0",              # DeepSeek API（兼容 OpenAI SDK）
    "python-multipart>=0.0.9,<1.0",
]
```

### 2) 配置与数据库

**`config.py`：**
- 读取环境变量：
  - `DeepSeek_API_KEY`：DeepSeek API 密钥（必需）
  - `DEEPSEEK_BASE_URL`：DeepSeek API 基础 URL（默认：https://api.deepseek.com）
  - `SQLITE_DB_PATH`：SQLite 数据库路径（默认：`~/.db_query/db_query.db`）
  - `APP_PORT`：服务端口（默认：8000）
  - `LOG_LEVEL`：日志级别（默认：INFO）
- 自动创建 SQLite 数据库目录（如果不存在）
- 使用 `pydantic-settings` 管理配置

**`db.py`：**
- 创建 SQLite async engine（使用 `sqlite+aiosqlite:///`）
- 创建 async sessionmaker
- 提供依赖 `get_session()`
- 初始化时创建表结构

### 3) 数据模型与迁移

**`models.py`：**
- `DatabaseConnection` 模型：
  - `id`: INTEGER PRIMARY KEY
  - `name`: VARCHAR(200) UNIQUE（数据库名称，作为唯一标识）
  - `url`: TEXT（数据库连接 URL）
  - `database_type`: VARCHAR(50)（postgresql, mysql 等）
  - `created_at`: TIMESTAMP
  - `updated_at`: TIMESTAMP
- `DatabaseMetadata` 模型：
  - `id`: INTEGER PRIMARY KEY
  - `connection_name`: VARCHAR(200)（关联到 DatabaseConnection.name）
  - `metadata_json`: TEXT（JSON 格式的 metadata）
  - `created_at`: TIMESTAMP
  - `updated_at`: TIMESTAMP
- 使用 SQLAlchemy async 模型
- 在应用启动时自动创建表（如果不存在）

### 4) Schema 与校验

**`schemas.py`：**
- 所有响应模型使用 camelCase（通过 `alias_generator`）
- `DatabaseConnectionRequest`：`{ "url": str }`
- `DatabaseConnectionResponse`：包含 name, url, databaseType, createdAt, updatedAt
- `DatabaseListResponse`：`{ "databases": List[DatabaseConnectionResponse] }`
- `MetadataResponse`：`{ "name": str, "metadata": dict }`
- `SqlQueryRequest`：`{ "sql": str }`
- `SqlQueryResponse`：`{ "columns": List[str], "rows": List[List[Any]], "rowCount": int }`
- `NaturalLanguageQueryRequest`：`{ "prompt": str }`
- `NaturalLanguageQueryResponse`：`{ "sql": str, "explanation": str | None }`
- 统一错误模型：`{ "error": { "code": str, "message": str, "details": dict } }`

### 5) 路由与服务

**`routes/databases.py`：**
- `GET /api/v1/dbs`：获取所有已存储的数据库
  - 返回：`DatabaseListResponse`
  - 查询 SQLite 获取所有连接
- `PUT /api/v1/dbs/{name}`：添加或更新一个数据库
  - 请求体：`DatabaseConnectionRequest`
  - 处理流程：
    1. 验证 URL 格式
    2. 测试数据库连接
    3. 存储或更新到 SQLite
    4. 自动触发 metadata 获取（异步）
  - 返回：`DatabaseConnectionResponse`
- `GET /api/v1/dbs/{name}`：获取一个数据库的 metadata
  - 返回：`MetadataResponse`
  - 如果 metadata 不存在，返回 404
- `POST /api/v1/dbs/{name}/query`：查询某个数据库
  - 请求体：`SqlQueryRequest`
  - 处理流程：
    1. 获取数据库连接信息
    2. 使用 sqlglot 解析和验证 SQL
    3. 确保仅包含 SELECT 语句
    4. 自动添加 LIMIT 1000（如需要）
    5. 执行查询
    6. 返回结果
  - 返回：`SqlQueryResponse`
- `POST /api/v1/dbs/{name}/query/natural`：根据自然语言生成 SQL
  - 请求体：`NaturalLanguageQueryRequest`
  - 处理流程：
    1. 获取数据库连接和 metadata
    2. 构建 LLM prompt（包含 metadata context）
    3. 调用 DeepSeek API 生成 SQL
    4. 验证生成的 SQL
    5. 执行查询
    6. 返回 SQL 和结果
  - 返回：`NaturalLanguageQueryResponse` + `SqlQueryResponse`

**`services/database.py`：**
- `test_connection(url: str, database_type: str) -> bool`：测试数据库连接
- `get_connection(session, name: str) -> DatabaseConnection | None`：获取连接
- `save_connection(session, name: str, url: str) -> DatabaseConnection`：保存连接
- `list_connections(session) -> List[DatabaseConnection]`：列出所有连接
- `delete_connection(session, name: str) -> bool`：删除连接

**`services/metadata.py`：**
- `fetch_postgres_metadata(url: str) -> dict`：从 PostgreSQL 获取 metadata
  - 查询 `information_schema.tables` 和 `information_schema.columns`
  - 返回结构化的表和列信息
- `save_metadata(session, connection_name: str, metadata: dict) -> DatabaseMetadata`：保存 metadata
- `get_metadata(session, connection_name: str) -> DatabaseMetadata | None`：获取 metadata
- `refresh_metadata(session, connection_name: str) -> DatabaseMetadata`：刷新 metadata
  - 调用 `fetch_postgres_metadata`
  - 调用 LLM 转换格式
  - 保存到 SQLite

**`services/sql_parser.py`：**
- `validate_sql(sql: str) -> tuple[bool, str | None]`：验证 SQL
  - 使用 sqlglot 解析
  - 检查是否仅包含 SELECT 语句
  - 返回 (is_valid, error_message)
- `add_limit_if_needed(sql: str, default_limit: int = 1000) -> str`：添加 LIMIT
  - 检查是否已有 LIMIT 子句
  - 如果没有，添加 `LIMIT {default_limit}`
  - 使用 sqlglot 安全地添加 LIMIT

**`services/llm.py`：**
- `convert_metadata_to_json(raw_metadata: dict) -> dict`：使用 LLM 转换 metadata
  - 构建 prompt，要求 LLM 将原始 metadata 转换为结构化 JSON
  - 调用 DeepSeek API
  - 解析返回的 JSON
- `generate_sql_from_natural_language(prompt: str, metadata: dict) -> tuple[str, str | None]`：生成 SQL
  - 构建 prompt，包含：
    - 数据库 schema 信息（表和列）
    - 用户查询需求
    - 生成规则（仅 SELECT，自动添加 LIMIT）
  - 调用 DeepSeek API
  - 返回 (sql, explanation)
- 使用 OpenAI SDK（兼容 DeepSeek API）
- 配置 `base_url` 为 DeepSeek API 地址
- 错误处理和重试机制

### 6) 错误、日志、中间件

**错误处理：**
- 统一异常处理器：
  - `DatabaseConnectionError`：连接失败
  - `SqlValidationError`：SQL 验证失败
  - `MetadataNotFoundError`：Metadata 不存在
  - `LlmError`：LLM 调用失败
- 返回统一错误结构：`{ "error": { "code": str, "message": str, "details": dict } }`

**CORS 配置：**
- 允许所有 origin：`allow_origins=["*"]`
- 允许所有方法：`allow_methods=["*"]`
- 允许所有头部：`allow_headers=["*"]`

**日志：**
- 结构化日志（JSON 格式）
- 记录：路径、状态码、耗时、错误信息
- 使用 Python `logging` 模块

### 7) 启动与运行

**`main.py`：**
- 创建 FastAPI 应用
- 配置 CORS（允许所有 origin）
- 注册路由：`/api/v1/dbs/*`
- 注册异常处理器
- 启动时初始化 SQLite 数据库（创建表）

**启动命令：**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**环境变量配置：**
```bash
# .env
DeepSeek_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
SQLITE_DB_PATH=~/.db_query/db_query.db
APP_PORT=8000
LOG_LEVEL=INFO
```

### 8) 测试

**单元测试：**
- `test_sql_parser.py`：SQL 解析和验证
- `test_metadata.py`：Metadata 获取和存储
- `test_llm.py`：LLM 服务（mock API）
- `test_database.py`：数据库连接管理

**集成测试：**
- `test_api.py`：API 端点测试
  - 使用临时 SQLite 数据库
  - Mock PostgreSQL 连接
  - Mock DeepSeek API
- 覆盖所有 API 端点
- 测试错误场景

## 前端实现步骤（React + Refine 5 + Monaco Editor）

### 1) 项目初始化

**目录结构：**
```
frontend/
├── src/
│   ├── api/              # API 客户端
│   │   └── client.ts
│   ├── components/       # UI 组件
│   │   ├── DatabaseList.tsx
│   │   ├── DatabaseForm.tsx
│   │   ├── SqlEditor.tsx
│   │   ├── QueryResults.tsx
│   │   └── NaturalLanguageQuery.tsx
│   ├── pages/           # 页面
│   │   └── MainPage.tsx
│   ├── hooks/           # 自定义 Hooks
│   ├── types/           # TypeScript 类型
│   │   └── index.ts
│   └── lib/            # 工具函数
├── package.json
└── vite.config.ts
```

**依赖安装：**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@refinedev/core": "^5.0.0",
    "@refinedev/simple-rest": "^5.0.0",
    "@refinedev/react-hook-form": "^5.0.0",
    "antd": "^5.0.0",
    "monaco-editor": "^0.45.0",
    "@monaco-editor/react": "^4.6.0",
    "tailwindcss": "^3.4.0",
    "axios": "^1.6.0"
  }
}
```

### 2) API 客户端

**`src/api/client.ts`：**
- 使用 axios 封装 API 调用
- 基础 URL：`http://localhost:8000/api/v1`
- 统一错误处理
- TypeScript 类型定义

**API 方法：**
- `getDatabases()`：获取所有数据库
- `putDatabase(name: string, url: string)`：添加/更新数据库
- `getDatabaseMetadata(name: string)`：获取 metadata
- `queryDatabase(name: string, sql: string)`：执行 SQL 查询
- `naturalLanguageQuery(name: string, prompt: string)`：自然语言查询

### 3) UI 组件

**`DatabaseList.tsx`：**
- 使用 Ant Design Table 展示数据库列表
- 显示：名称、URL、类型、创建时间
- 操作：查看 metadata、删除、刷新 metadata

**`DatabaseForm.tsx`：**
- 使用 Ant Design Form
- 输入：数据库名称、连接 URL
- 提交：调用 PUT API
- 表单验证

**`SqlEditor.tsx`：**
- 使用 Monaco Editor
- SQL 语法高亮
- 自动补全（可选）
- 执行按钮
- 显示执行结果或错误

**`QueryResults.tsx`：**
- 使用 Ant Design Table 展示查询结果
- 动态列（根据返回的 columns）
- 分页支持（如需要）
- 导出功能（可选）

**`NaturalLanguageQuery.tsx`：**
- 输入框（自然语言）
- 生成 SQL 按钮
- 显示生成的 SQL
- 执行查询按钮
- 显示结果

### 4) 页面与状态

**`MainPage.tsx`：**
- 布局：
  - 左侧：数据库列表 + 添加数据库表单
  - 中间：SQL 编辑器 + 自然语言查询
  - 右侧：查询结果表格
- 状态管理：使用 React Query（Refine 5 内置）
- 数据获取：自动刷新数据库列表

### 5) Refine 5 配置

**数据提供者：**
- 使用 `@refinedev/simple-rest`
- 配置 API 基础 URL
- 配置资源（databases）

**路由：**
- 单页应用
- 主页面：`/`

### 6) 样式

**Tailwind CSS：**
- 配置 Tailwind
- 自定义主题（可选）
- 响应式布局

**Ant Design：**
- 使用 Ant Design 组件
- 主题配置（可选）

## 开发顺序建议

1. **M1：后端基础**（1-2 天）
   - 项目结构搭建
   - 配置管理
   - SQLite 数据库模型
   - CORS 设置

2. **M2：数据库连接管理**（1 天）
   - 连接 CRUD API
   - 连接测试功能

3. **M3：Metadata 获取**（2 天）
   - PostgreSQL metadata 查询
   - DeepSeek LLM 集成
   - Metadata 存储

4. **M4：SQL 查询功能**（1-2 天）
   - SQL 解析验证
   - SELECT 限制
   - LIMIT 自动添加
   - 查询执行

5. **M5：自然语言生成 SQL**（1-2 天）
   - LLM prompt 构建
   - SQL 生成
   - 错误处理

6. **M6：前端基础**（1-2 天）
   - 项目搭建
   - Monaco Editor 集成
   - API 客户端

7. **M7：前端功能**（2-3 天）
   - 连接管理 UI
   - SQL 编辑器
   - 查询结果展示
   - 自然语言查询 UI

8. **M8：测试与优化**（1-2 天）
   - 单元测试
   - 集成测试
   - 错误处理完善

## 注意事项

1. **SQLite 数据库路径**：使用 `~/.db_query/db_query.db`，需要处理路径展开
2. **DeepSeek API**：使用 OpenAI SDK，配置 `base_url` 为 DeepSeek API 地址
3. **CORS**：允许所有 origin（开发环境），生产环境需要限制
4. **错误处理**：所有错误都要返回清晰的错误信息
5. **类型安全**：前后端都要有严格的类型标注
6. **SQL 安全**：严格限制仅允许 SELECT 语句
7. **LIMIT 限制**：自动添加 LIMIT 1000，防止返回过多数据

