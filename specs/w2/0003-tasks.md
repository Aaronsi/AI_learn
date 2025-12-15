# DB Query Tool 任务分解（3 Phase）

## Phase 1: 后端核心功能（M1-M4）

**目标**：完成后端基础架构和核心查询功能

**交付成果**：
- ✅ 完整的后端项目结构
- ✅ 数据库连接管理 API（CRUD）
- ✅ Metadata 获取与存储功能
- ✅ SQL 查询执行功能（带验证和安全控制）

**包含的里程碑**：
- M1: 后端基础架构
- M2: 数据库连接管理
- M3: Metadata 获取与存储
- M4: SQL 查询功能

**详细任务**：

### 1.1 项目初始化（M1）
- [ ] 创建后端项目结构（`backend/app/`）
- [ ] 配置 `pyproject.toml` 和依赖
- [ ] 实现 `config.py`（环境变量、SQLite 路径处理）
- [ ] 实现 `db.py`（SQLite async engine）
- [ ] 实现 `models.py`（DatabaseConnection, DatabaseMetadata）
- [ ] 实现 `schemas.py`（Pydantic 模型，camelCase）
- [ ] 配置 CORS（允许所有 origin）
- [ ] 创建 `.env.example`

### 1.2 数据库连接管理（M2）
- [ ] 实现 `services/database.py`（连接测试、CRUD）
- [ ] 实现 `routes/databases.py`：
  - [ ] `GET /api/v1/dbs` - 获取所有数据库
  - [ ] `PUT /api/v1/dbs/{name}` - 添加/更新数据库
- [ ] 实现连接测试功能
- [ ] 实现错误处理（DatabaseConnectionError）

### 1.3 Metadata 获取与存储（M3）
- [ ] 实现 `services/metadata.py`：
  - [ ] `fetch_postgres_metadata()` - 从 PostgreSQL 获取原始 metadata
  - [ ] `save_metadata()` - 保存到 SQLite
  - [ ] `get_metadata()` - 获取 metadata
- [ ] 实现 `services/llm.py`：
  - [ ] `convert_metadata_to_json()` - 使用 DeepSeek LLM 转换 metadata
- [ ] 实现 `routes/databases.py`：
  - [ ] `GET /api/v1/dbs/{name}` - 获取 metadata
- [ ] 在 PUT 数据库时自动触发 metadata 获取（异步）

### 1.4 SQL 查询功能（M4）
- [ ] 实现 `services/sql_parser.py`：
  - [ ] `validate_sql()` - SQL 解析和验证（sqlglot）
  - [ ] `add_limit_if_needed()` - 自动添加 LIMIT 1000
- [ ] 实现 `routes/databases.py`：
  - [ ] `POST /api/v1/dbs/{name}/query` - 执行 SQL 查询
- [ ] 实现错误处理（SqlValidationError）
- [ ] 测试 SQL 验证和 LIMIT 添加功能

**验收标准**：
- ✅ 可以添加数据库连接
- ✅ 可以获取数据库 metadata
- ✅ 可以执行 SQL 查询（仅 SELECT）
- ✅ SQL 自动添加 LIMIT 1000
- ✅ 所有 API 返回 camelCase JSON

---

## Phase 2: 自然语言查询 + 前端实现（M5-M7）

**目标**：完成自然语言生成 SQL 功能和完整的前端界面

**交付成果**：
- ✅ 自然语言生成 SQL API
- ✅ 完整的前端应用
- ✅ 数据库连接管理 UI
- ✅ SQL 编辑器（Monaco Editor）
- ✅ 查询结果展示
- ✅ 自然语言查询 UI

**包含的里程碑**：
- M5: 自然语言生成 SQL
- M6: 前端基础
- M7: 前端功能实现

**详细任务**：

### 2.1 自然语言生成 SQL（M5）
- [ ] 完善 `services/llm.py`：
  - [ ] `generate_sql_from_natural_language()` - 生成 SQL
  - [ ] 构建包含 metadata context 的 prompt
  - [ ] 错误处理和重试机制
- [ ] 实现 `routes/databases.py`：
  - [ ] `POST /api/v1/dbs/{name}/query/natural` - 自然语言查询
- [ ] 实现错误处理（LlmError）
- [ ] 测试自然语言生成 SQL 功能

### 2.2 前端项目初始化（M6）
- [ ] 创建前端项目（Vite + React + TypeScript）
- [ ] 安装依赖（Refine 5, Ant Design, Monaco Editor, Tailwind）
- [ ] 配置 Tailwind CSS
- [ ] 配置 Refine 5（数据提供者、路由）
- [ ] 创建项目目录结构
- [ ] 实现 `src/api/client.ts` - API 客户端封装
- [ ] 实现 `src/types/index.ts` - TypeScript 类型定义

### 2.3 前端功能实现（M7）
- [ ] 实现 `components/DatabaseList.tsx` - 数据库列表
- [ ] 实现 `components/DatabaseForm.tsx` - 添加数据库表单
- [ ] 实现 `components/SqlEditor.tsx` - SQL 编辑器（Monaco）
- [ ] 实现 `components/QueryResults.tsx` - 查询结果表格
- [ ] 实现 `components/NaturalLanguageQuery.tsx` - 自然语言查询
- [ ] 实现 `pages/MainPage.tsx` - 主页面布局
- [ ] 集成所有组件
- [ ] 实现状态管理（React Query）
- [ ] 实现错误处理和用户提示

**验收标准**：
- ✅ 可以通过自然语言生成 SQL
- ✅ 前端可以添加和管理数据库连接
- ✅ 前端可以查看 metadata
- ✅ 前端可以编辑和执行 SQL
- ✅ 前端可以展示查询结果
- ✅ 前端可以使用自然语言查询

---

## Phase 3: 测试与优化（M8）

**目标**：完善测试、优化性能和用户体验

**交付成果**：
- ✅ 完整的单元测试
- ✅ 集成测试
- ✅ 性能优化
- ✅ 错误处理完善
- ✅ 文档完善

**包含的里程碑**：
- M8: 测试与优化

**详细任务**：

### 3.1 后端测试
- [ ] 编写 `tests/test_sql_parser.py` - SQL 解析测试
- [ ] 编写 `tests/test_metadata.py` - Metadata 测试
- [ ] 编写 `tests/test_database.py` - 数据库连接测试
- [ ] 编写 `tests/test_llm.py` - LLM 服务测试（mock）
- [ ] 编写 `tests/test_api.py` - API 端点集成测试
- [ ] 测试错误场景
- [ ] 测试边界情况

### 3.2 前端测试（可选）
- [ ] 组件单元测试
- [ ] 集成测试
- [ ] E2E 测试（可选）

### 3.3 优化与完善
- [ ] 性能优化：
  - [ ] SQL 查询性能优化
  - [ ] Metadata 缓存优化
  - [ ] 前端加载性能优化
- [ ] 错误处理完善：
  - [ ] 统一错误响应格式
  - [ ] 用户友好的错误提示
  - [ ] 错误日志记录
- [ ] 代码质量：
  - [ ] 代码审查
  - [ ] 类型检查完善
  - [ ] 代码格式化
- [ ] 文档：
  - [ ] 更新 README.md
  - [ ] API 文档（可选）
  - [ ] 使用说明

**验收标准**：
- ✅ 测试覆盖率 > 80%
- ✅ 所有关键功能都有测试
- ✅ 性能满足要求（查询响应 < 2s）
- ✅ 错误处理完善
- ✅ 文档完整

---

## 开发时间估算

- **Phase 1**: 4-5 天
  - 项目初始化：1 天
  - 连接管理：1 天
  - Metadata：1-1.5 天
  - SQL 查询：1-1.5 天

- **Phase 2**: 4-5 天
  - 自然语言生成：1-1.5 天
  - 前端基础：1 天
  - 前端功能：2-2.5 天

- **Phase 3**: 2-3 天
  - 测试：1-1.5 天
  - 优化与完善：1-1.5 天

**总计**：10-13 天

## 开发顺序

1. **先完成后端核心功能**（Phase 1）
   - 确保后端 API 完整可用
   - 可以使用 Postman/curl 测试所有接口

2. **然后实现前端和自然语言功能**（Phase 2）
   - 前端可以调用后端 API
   - 自然语言功能可以独立测试

3. **最后完善测试和优化**（Phase 3）
   - 确保代码质量
   - 优化用户体验

## 关键依赖

- **Phase 1 → Phase 2**: 前端依赖后端 API
- **Phase 2 → Phase 3**: 测试依赖完整功能实现

## 风险与注意事项

1. **DeepSeek API 集成**：需要确保 API key 正确配置
2. **SQLite 路径处理**：需要正确处理 `~/.db_query/` 路径
3. **SQL 安全**：严格限制仅允许 SELECT 语句
4. **CORS 配置**：开发环境允许所有 origin，生产环境需要限制
5. **Monaco Editor 集成**：可能需要额外的配置

