# Constitution - DB Query Tool

## 项目概述

这是一个数据库查询工具，用户可以添加数据库连接 URL，系统会连接到数据库，获取数据库的 metadata，然后将数据库中的表和视图信息展示出来。用户可以自己输入 SQL 查询，也可以通过自然语言来生成 SQL 查询。

## 技术栈

### 后端
- **语言**: Python 3.12+
- **包管理**: uv
- **框架**: FastAPI
- **数据库**: 
  - SQLite（存储连接和 metadata）
  - PostgreSQL（支持查询，可扩展其他数据库）
- **SQL 解析**: sqlglot
- **AI SDK**: OpenAI SDK
- **数据模型**: Pydantic
- **ORM**: SQLAlchemy (async)

### 前端
- **框架**: React
- **UI 框架**: Refine 5
- **样式**: Tailwind CSS
- **组件库**: Ant Design
- **SQL 编辑器**: Monaco Editor
- **语言**: TypeScript（严格类型标注）

## 编码规范

### 后端规范
- 使用 **Ergonomic Python** 风格编写代码
- **严格类型标注**：所有函数、类、变量都需要类型标注
- 使用 **Pydantic** 定义所有数据模型
- 所有后端生成的 **JSON 数据使用 camelCase 格式**
- 使用 async/await 进行异步操作

### 前端规范
- **严格类型标注**：使用 TypeScript，所有代码都需要类型标注
- 遵循 React 最佳实践
- 使用 Refine 5 的数据提供者和资源管理

## 架构设计

### 核心功能

1. **数据库连接管理**
   - 用户可以添加数据库连接 URL
   - 连接信息存储在 SQLite 数据库中
   - 支持测试连接功能

2. **Metadata 获取与存储**
   - 从 PostgreSQL 数据库查询系统和视图信息
   - 使用 LLM 将 metadata 信息转换成 JSON 格式
   - 存储到 SQLite 数据库中，便于后续复用

3. **SQL 查询**
   - 用户可以直接输入 SQL 查询
   - 所有 SQL 语句必须经过 sqlglot 解析验证
   - **仅允许 SELECT 语句**
   - 如果语法不正确，返回详细错误信息
   - **自动添加 LIMIT 1000**：如果查询不包含 LIMIT 子句，默认添加 `LIMIT 1000`
   - 查询结果以 JSON 格式返回，前端组织成表格显示

4. **自然语言生成 SQL**
   - 用户可以使用自然语言描述查询需求
   - 系统将数据库的表和视图信息作为 context 传递给 LLM
   - LLM 根据 metadata 信息生成 SQL 查询
   - 生成的 SQL 同样需要经过验证（仅 SELECT，自动添加 LIMIT）

### 数据流

1. **连接管理流程**
   ```
   用户添加连接 → 测试连接 → 存储到 SQLite → 获取 Metadata → LLM 转换 → 存储 Metadata
   ```

2. **查询流程**
   ```
   用户输入 SQL/自然语言 → SQL 解析/LLM 生成 → 验证（仅 SELECT） → 添加 LIMIT → 执行查询 → 返回 JSON 结果
   ```

3. **Metadata 复用**
   - Metadata 存储在 SQLite 中，避免重复查询数据库
   - 当数据库结构变化时，可以手动刷新 metadata

## 安全与权限

- **不需要 authentication**：任何用户都可以使用
- **SQL 安全**：仅允许 SELECT 语句，防止数据修改
- **连接字符串安全**：存储在本地 SQLite，不对外暴露

## 数据模型

### SQLite 存储模型
- **DatabaseConnection**: 存储数据库连接信息
  - id, name, connection_string, database_type, created_at, updated_at
- **DatabaseMetadata**: 存储数据库 metadata（JSON 格式）
  - id, connection_id, metadata_json, created_at, updated_at

### API 响应格式
- 所有 JSON 响应使用 **camelCase** 格式
- 统一错误响应格式
- 查询结果格式：`{ columns: string[], rows: any[][], rowCount: number }`

## 开发原则

1. **类型安全**：前后端都要有严格的类型标注
2. **错误处理**：所有错误都要有清晰的错误信息
3. **代码可读性**：遵循 Ergonomic Python 和 TypeScript 最佳实践
4. **可扩展性**：支持多种数据库类型（当前主要支持 PostgreSQL）
5. **性能优化**：Metadata 缓存，避免重复查询

## 项目结构

```
w2/db_query/
├── backend/          # 后端代码
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routes/
│   │   └── services/
│   ├── pyproject.toml
│   └── README.md
├── frontend/         # 前端代码
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── lib/
│   └── package.json
└── .specify/
    └── memory/
        └── constitution.md
```

