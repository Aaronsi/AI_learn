# DB Query Tool

数据库查询工具，支持 SQL 查询和自然语言生成 SQL。

## 快速开始

### 1. 安装依赖

```bash
make install
```

或手动安装：

```bash
cd backend
uv sync
```

### 2. 配置环境变量

创建 `backend/.env` 文件：

```bash
DeepSeek_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
SQLITE_DB_PATH=~/.db_query/db_query.db
APP_PORT=8000
LOG_LEVEL=INFO
```

### 3. 启动开发服务器

```bash
make dev
```

或指定端口：

```bash
PORT=8000 make dev
```

### 4. 测试 API

使用 VS Code REST Client 扩展打开 `test.rest` 文件，点击每个请求上方的 "Send Request" 按钮。

## Makefile 命令

```bash
make help          # 显示所有可用命令
make install       # 安装依赖
make dev           # 启动开发服务器（自动重载）
make start         # 启动生产服务器
make stop          # 停止服务器
make test          # 运行测试
make format        # 格式化代码
make lint          # 代码检查
make check         # 运行格式化和检查
make clean         # 清理缓存文件
make upgrade       # 升级依赖
make outdated      # 查看过时的包
make list          # 列出已安装的包
make health        # 检查服务器健康状态
```

## API 端点

### 健康检查
- `GET /health` - 服务器健康状态

### 数据库连接管理
- `GET /api/v1/dbs` - 获取所有数据库连接
- `PUT /api/v1/dbs/{name}` - 添加或更新数据库连接
- `GET /api/v1/dbs/{name}` - 获取数据库 metadata

### SQL 查询
- `POST /api/v1/dbs/{name}/query` - 执行 SQL 查询
- `POST /api/v1/dbs/{name}/query/natural` - 自然语言生成 SQL

## 使用 REST Client 测试

1. 安装 VS Code REST Client 扩展
2. 打开 `test.rest` 文件
3. 点击每个请求上方的 "Send Request" 按钮
4. 查看响应结果

## 项目结构

```
w2/db_query/
├── backend/          # 后端代码
│   ├── app/          # 应用代码
│   │   ├── main.py   # FastAPI 应用入口
│   │   ├── routes/   # API 路由
│   │   └── services/  # 业务逻辑
│   └── pyproject.toml
├── Makefile          # 构建和运行命令
├── test.rest         # API 测试文件
└── README.md         # 项目说明
```

## 开发

### 运行开发服务器

```bash
make dev
```

服务器会在 `http://localhost:8000` 启动，支持自动重载。

### 运行测试

```bash
make test
```

### 代码格式化

```bash
make format
```

### 代码检查

```bash
make lint
```

## 环境要求

- Python 3.12+
- uv 包管理器
- PostgreSQL（用于测试数据库连接）

## 许可证

MIT

