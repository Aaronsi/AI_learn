# Project Alpha

一个基于标签的 Ticket 管理系统，使用 FastAPI + PostgreSQL 作为后端，React + TypeScript + Tailwind CSS 作为前端。

## 项目结构

```
project-alpha/
├── backend/          # FastAPI 后端
├── frontend/         # React 前端
└── README.md         # 本文件
```

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL（默认配置：postgres/postgres@localhost:5432/projectalpha）
- uv（Python 包管理器，推荐）

### 1. 后端设置

```bash
cd backend

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，确保 DATABASE_URL 和 ALLOWED_ORIGINS 配置正确

# 创建数据库（如果不存在）
createdb projectalpha
# 或使用 psql: psql -U postgres -c "CREATE DATABASE projectalpha;"

# 运行数据库迁移
uv run alembic upgrade head

# （可选）填充种子数据
psql -U postgres -d projectalpha -f seed.sql

# 启动后端服务
uv run uvicorn app.main:app --reload --port 8000
```

后端将在 `http://localhost:8000` 启动。

**重要配置说明：**

- `DATABASE_URL`：PostgreSQL 连接串
  - 格式：`postgresql+asyncpg://username:password@host:port/database`
  - 默认：`postgresql+asyncpg://postgres:postgres@localhost:5432/projectalpha`
  - **确保数据库已创建**

- `ALLOWED_ORIGINS`：CORS 允许的源（逗号分隔）
  - 必须包含前端地址，例如：`http://localhost:3000,http://localhost:5173`
  - **如果前端无法访问 API，检查此配置**

### 2. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量（可选，默认使用 http://localhost:8000）
cp .env.example .env
# 如果后端运行在不同端口，编辑 .env 文件修改 VITE_API_BASE_URL

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:5173`（Vite 默认端口）启动。

**Windows PowerShell 用户注意：**

如果遇到执行策略错误，可以使用以下方法之一：

1. **使用 CMD**（推荐）：
   ```cmd
   cmd
   npm run dev
   ```

2. **临时绕过执行策略**：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   npm run dev
   ```

**环境变量说明：**

- `VITE_API_BASE_URL`：后端 API 地址
  - 默认：`http://localhost:8000`
  - 如果后端运行在不同端口，请相应修改

## 功能特性

### 后端（M1）
- ✅ RESTful API
- ✅ 数据库迁移（Alembic）
- ✅ Ticket CRUD 操作
- ✅ 标签管理
- ✅ 多条件筛选（状态、标签、搜索）
- ✅ 分页支持
- ✅ 统一错误处理
- ✅ CORS 支持
- ✅ 结构化日志

### 前端（M2）
- ✅ Ticket 的创建、编辑、删除
- ✅ Ticket 状态切换（进行中/已完成）
- ✅ 标签管理（创建、选择、删除）
- ✅ 多条件筛选（状态、标签、标题搜索）
- ✅ 搜索防抖（300ms）
- ✅ 分页支持
- ✅ 乐观更新
- ✅ 错误提示
- ✅ 删除二次确认
- ✅ 响应式设计

## API 文档

后端启动后，访问以下地址查看 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 开发

### 后端测试

```bash
cd backend
uv run pytest
```

### 前端构建

```bash
cd frontend
npm run build
```

## 环境变量

### 后端（backend/.env）

详细说明请参考 `backend/.env.example`：

- `DATABASE_URL`: PostgreSQL 数据库连接串
  - 格式：`postgresql+asyncpg://username:password@host:port/database`
  - 默认：`postgresql+asyncpg://postgres:postgres@localhost:5432/projectalpha`
  - **重要**：确保数据库已创建

- `APP_PORT`: 服务端口（默认 8000）

- `ALLOWED_ORIGINS`: CORS 允许的源（逗号分隔）
  - 示例：`http://localhost:3000,http://localhost:5173`
  - **重要**：必须包含前端地址

- `LOG_LEVEL`: 日志级别（默认 INFO）
  - 可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL

- `MAX_REQUEST_SIZE`: 请求体大小限制（字节，默认 1048576 = 1MB）

### 前端（frontend/.env）

详细说明请参考 `frontend/.env.example`：

- `VITE_API_BASE_URL`: 后端 API 地址
  - 默认：`http://localhost:8000`
  - 如果后端运行在不同端口，请相应修改

## 技术栈

### 后端
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Alembic
- Pydantic

### 前端
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Shadcn UI
- React Query
- Axios

## 许可证

MIT
