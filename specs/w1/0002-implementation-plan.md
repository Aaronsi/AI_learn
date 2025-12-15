# Project Alpha 实现计划

## 里程碑
- M0 准备：环境就绪（Python 3.11+、uv、Node 18+、本地 Postgres，设置 `DATABASE_URL`）。
- M1 后端基础：数据模型、迁移、核心 CRUD API、标签同步、健康检查。
- M2 前端基础：项目脚手架、UI 组件库、API 客户端封装、列表页与筛选。
- M3 迭代完善：表单校验、搜索防抖、错误提示、分页与状态管理完善。
- M4 验收与打磨：补充测试、日志与配置检查、文档与示例运行。

## 代码结构（目标）
- 根目录：`./w1/project-alpha/`
- 后端：`backend/`（FastAPI + Postgres）
- 前端：`frontend/`（Vite + React + TS + Tailwind + Shadcn）
- 数据库迁移：`backend/migrations/`（Alembic）
- 脚本与配置：`Makefile` 或 `scripts/`，`.env.example`

## 后端实现步骤（FastAPI + Postgres）
1) 项目骨架
- 目录：`backend/app/` 下创建 `main.py`, `config.py`, `db.py`, `models.py`, `schemas.py`, `routes/`, `services/`, `logger.py`.
- 依赖（使用 uv 安装）：fastapi, uvicorn[standard], SQLAlchemy[asyncio], asyncpg, pydantic, alembic, python-multipart, httpx (测试), pytest/pytest-asyncio。
2) 配置与数据库
- `config.py` 读取环境变量：`DATABASE_URL`（默认本地 postgres/postgres）、`APP_PORT`, `ALLOWED_ORIGINS`, `LOG_LEVEL`。
- `db.py`：创建 async engine 与 sessionmaker，提供依赖 `get_session`。
3) 数据模型与迁移
- `models.py`：`Ticket`, `Tag`, `TicketTag`（复合主键）。`status` 枚举 open/done。
- Alembic 初始化：生成 `alembic.ini`、`env.py`；首版迁移建表与索引（status、lower(title)、ticket_tags(tag_id)）。
4) Schema 与校验
- `schemas.py`：请求/响应分离；标题 <=200，标签名 <=50；统一错误模型 `{error:{code,message,details}}`。
5) 路由与服务
- `routes/tickets.py`：`GET /tickets`（status、tags AND、q、limit/offset）、`POST /tickets`、`GET /tickets/{id}`、`PATCH /tickets/{id}`、`DELETE /tickets/{id}`。
- `routes/tags.py`：`GET /tags`（q 过滤）、`POST /tags`（幂等创建）、`DELETE /tags/{id}`。
- `routes/health.py`：`GET /health` 检查 DB。
- `services/tickets.py`：封装标签 upsert、覆盖式同步、多标签 AND 过滤（分组计数 == 选中标签数）。
6) 错误、日志、中间件
- 统一异常处理器，返回统一错误结构；结构化 JSON 日志（路径、状态码、耗时）。
- CORS 仅允许前端域名；限制请求体大小。
7) 启动与运行
- `main.py` 组装 app、路由、CORS、异常处理。
- 命令：`uvicorn app.main:app --reload`。
8) 测试
- 使用 pytest + httpx/async；用临时数据库或事务回滚；覆盖创建/更新/删除、标签过滤、搜索、分页、错误格式。

## 前端实现步骤（Vite + React + TS + Tailwind + Shadcn）
1) 项目初始化
- 目录：`frontend/`；使用 Vite 创建 React+TS；配置 Tailwind 与 Shadcn 组件。
- 结构：`src/api/`, `src/components/`, `src/pages/`, `src/hooks/`, `src/types/`, `src/lib/`.
2) API 客户端
- 封装 fetch/axios；配合 React Query。
- `tickets`：列表（status、tags、q、分页）、创建、更新、删除、完成/撤销。
- `tags`：列表（q）、创建（幂等）、删除。
- 统一错误适配为前端可读信息，toast 提示。
3) UI 组件
- `FiltersBar`：状态筛选、标签多选、标题搜索（300ms 防抖）。
- `TagSelector`：多选下拉 + 新建标签（调用创建接口）。
- `TicketList`：表格/卡片展示，含状态切换、标签、删除按钮。
- `TicketForm`：创建/编辑弹窗；校验标题必填/长度；标签选择。
- `Pagination`：limit/offset 控制。
4) 页面与状态
- 主列表页：组合 FiltersBar + TicketList + Pagination；支持 AND 标签过滤、状态过滤、搜索、防抖、分页。
- 状态管理：React Query 缓存；乐观更新完成/撤销、删除；提交后刷新列表。
5) UX 细节
- 删除二次确认；长描述折叠；状态切换可快速恢复；错误提示区分网络/校验/服务器。
6) 配置
- `.env` 指向后端 API 基址；CORS 配合后端。

## 运维与运行
- 本地运行：`uv sync` 安装后端依赖；`uvicorn app.main:app --reload`。前端 `npm install && npm run dev`。
- 数据库：本地 Postgres 用户/密码 postgres/postgres；`alembic upgrade head` 初始化表。
- Docker（可选）：准备 docker-compose（db + backend + frontend），确保健康检查。

## 测试与验收检查表
- 后端：创建/编辑/删除/完成/取消完成 ticket；标签创建/删除与 AND 过滤；标题搜索；分页；统一错误格式；健康检查。
- 前端：表单校验、搜索防抖、状态切换与乐观更新、删除确认、标签过滤准确、分页正常。
- 文档：README 补充运行步骤、环境变量示例、`DATABASE_URL` 配置说明。

## 工作量评估（粗估人日）
- M0 准备：0.5 人日（环境、依赖、DB 准备）。
- M1 后端基础：2~3 人日（模型/迁移/路由/服务/错误处理/健康检查）。
- M2 前端基础：2~3 人日（脚手架、UI 组件、API 客户端、列表与筛选）。
- M3 迭代完善：1.5~2 人日（表单校验、防抖、错误提示、分页与状态管理完善）。
- M4 验收与打磨：1 人日（测试补充、文档、配置检查、演示跑通）。
- 合计：7~9.5 人日（单人连续投入）；多人并行可压缩日历周期。
