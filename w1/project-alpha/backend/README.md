 # Project Alpha Backend

## 环境要求
- Python 3.11+
- PostgreSQL（默认配置：`postgres/postgres@localhost:5432/projectalpha`）
- 建议使用 `uv` 安装依赖

## 快速开始

### 1. 安装依赖
```bash
uv sync
```

### 2. 配置环境变量
复制 `.env.example` 到 `.env` 并修改配置：
```bash
cp .env.example .env
```

**重要环境变量说明：**

- `DATABASE_URL`：PostgreSQL 数据库连接串
  - 格式：`postgresql+asyncpg://username:password@host:port/database`
  - 默认：`postgresql+asyncpg://postgres:postgres@localhost:5432/projectalpha`
  - **注意**：确保数据库已创建，或使用已存在的数据库

- `APP_PORT`：服务端口（默认：8000）

- `ALLOWED_ORIGINS`：CORS 允许的源（逗号分隔）
  - 示例：`http://localhost:3000,http://localhost:5173`
  - **重要**：必须包含前端地址，否则前端无法访问 API

- `LOG_LEVEL`：日志级别（默认：INFO）
  - 可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL

- `MAX_REQUEST_SIZE`：请求体大小限制（字节，默认：1048576 = 1MB）

### 3. 创建数据库（如需要）
```bash
# 使用 PostgreSQL 客户端创建数据库
createdb projectalpha

# 或使用 psql
psql -U postgres -c "CREATE DATABASE projectalpha;"
```

### 4. 运行数据库迁移
```bash
uv run alembic upgrade head
```

### 5. 启动服务
```bashpre
uv run uvicorn app.main:app --reload --port 8000
```

服务将在 `http://localhost:8000` 启动。

## API 文档

启动服务后，访问以下地址查看 API 文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 测试

### 安装测试依赖
```bash
uv sync --extra dev
```

### 运行测试

运行所有测试：
```bash
uv run pytest
```

运行特定测试文件：
```bash
uv run pytest tests/test_tickets.py
uv run pytest tests/test_tags.py
uv run pytest tests/test_health.py
```

运行测试并显示详细输出：
```bash
uv run pytest -v
```

查看测试覆盖率（需要安装 pytest-cov）：
```bash
uv run pytest --cov=app --cov-report=html
```

### 测试说明

- 测试使用 SQLite 内存数据库（`:memory:`），无需配置 PostgreSQL
- 每个测试文件都有独立的数据库清理机制
- 测试覆盖了所有 API 端点、错误处理、分页、搜索、标签过滤等功能

## 数据库种子数据

如果需要填充测试数据，可以使用 `seed.sql`：
```bash
psql -U postgres -d projectalpha -f seed.sql
```

## 目录结构
- `app/`：应用代码
  - `main.py`：FastAPI 应用入口
  - `config.py`：配置管理
  - `db.py`：数据库连接
  - `models.py`：数据模型
  - `schemas.py`：Pydantic 模式
  - `routes/`：API 路由
  - `services/`：业务逻辑
  - `errors.py`：错误处理
  - `logger.py`：日志配置
- `migrations/`：Alembic 迁移脚本
- `tests/`：pytest + httpx 异步测试
- `seed.sql`：数据库种子数据

## 开发

### 添加新的数据库迁移
```bash
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head
```

### 代码格式化
```bash
uv run ruff format .
uv run ruff check .
```

## 故障排除

### 数据库连接失败
- 检查 PostgreSQL 服务是否运行
- 验证 `DATABASE_URL` 配置是否正确
- 确认数据库用户权限

### CORS 错误
- 确保 `ALLOWED_ORIGINS` 包含前端地址
- 检查前端 `VITE_API_BASE_URL` 配置

### 迁移失败
- 确保数据库已创建
- 检查数据库用户是否有足够权限
- 查看 `TROUBLESHOOTING.md` 获取更多帮助
