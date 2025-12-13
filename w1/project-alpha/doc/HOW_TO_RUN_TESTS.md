# 如何运行 test.rest API 测试文件

`test.rest` 是一个 REST Client 格式的 API 测试文件，包含了对 Project Alpha 后端所有 API 端点的测试用例。

## 前置条件

1. **确保后端服务正在运行**
   ```bash
   cd w1/project-alpha/backend
   uv run uvicorn app.main:app --reload --port 8000
   ```

2. **确保数据库已迁移并包含测试数据**
   ```bash
   # 运行迁移
   uv run alembic upgrade head

   # 可选：导入 seed 数据
   psql -U postgres -d postgres -f seed.sql
   ```

## 方法 1: VS Code REST Client 扩展（推荐）

### 安装扩展

1. 打开 VS Code
2. 按 `Ctrl+Shift+X` (Windows/Linux) 或 `Cmd+Shift+X` (Mac) 打开扩展市场
3. 搜索 "REST Client"（作者：Huachao Mao）
4. 点击安装

### 使用方法

1. 打开 `w1/project-alpha/doc/test.rest` 文件
2. 在每个请求上方会看到一个 **"Send Request"** 按钮（或文本链接）
3. 点击 "Send Request" 即可发送请求
4. 响应结果会显示在右侧面板或新标签页中

### 快捷键

- 将光标放在请求行上，按 `Ctrl+Alt+R` (Windows/Linux) 或 `Cmd+Alt+R` (Mac) 发送请求
- 按 `Ctrl+Alt+E` (Windows/Linux) 或 `Cmd+Alt+E` (Mac) 查看请求历史

### 示例

```http
### 健康检查
GET {{baseUrl}}/health
```

将光标放在 `GET` 这一行，点击上方的 "Send Request" 或使用快捷键即可发送请求。

## 方法 2: IntelliJ IDEA / PyCharm HTTP Client

### 使用方法

1. 打开 IntelliJ IDEA 或 PyCharm
2. 打开 `w1/project-alpha/doc/test.rest` 文件
3. 每个请求旁边会有一个绿色的运行按钮（▶️）
4. 点击运行按钮即可发送请求
5. 响应结果会显示在底部的 "Services" 或 "HTTP Client" 面板中

### 快捷键

- 将光标放在请求上，按 `Ctrl+Enter` (Windows/Linux) 或 `Cmd+Enter` (Mac) 发送请求

## 方法 3: 使用 curl 命令（命令行）

虽然 `test.rest` 文件本身不能直接运行，但你可以手动将请求转换为 curl 命令：

### 示例转换

**REST Client 格式：**
```http
GET {{baseUrl}}/health
```

**对应的 curl 命令：**
```bash
curl -X GET http://localhost:8000/health
```

**POST 请求示例：**
```http
POST {{baseUrl}}/tags
Content-Type: {{contentType}}

{
  "name": "bug"
}
```

**对应的 curl 命令：**
```bash
curl -X POST http://localhost:8000/tags \
  -H "Content-Type: application/json" \
  -d '{"name": "bug"}'
```

## 方法 4: 使用 Postman / Insomnia

### 导入到 Postman

1. 打开 Postman
2. 点击 "Import" 按钮
3. 选择 "File" 标签
4. 选择 `test.rest` 文件
5. Postman 会自动识别并导入请求

**注意**：Postman 可能不完全支持 REST Client 格式，某些复杂请求可能需要手动调整。

### 使用 Insomnia

Insomnia 原生支持 REST Client 格式（`.rest` 文件）：

1. 打开 Insomnia
2. 点击 "Create" → "Import/Export" → "Import Data"
3. 选择 "From File"
4. 选择 `test.rest` 文件
5. Insomnia 会自动解析并创建请求集合

## 方法 5: 使用 HTTPie（命令行工具）

HTTPie 是一个更友好的命令行 HTTP 客户端：

### 安装 HTTPie

```bash
# Windows (使用 pip)
pip install httpie

# macOS
brew install httpie

# Linux
sudo apt install httpie
```

### 使用示例

```bash
# GET 请求
http GET http://localhost:8000/health

# POST 请求
http POST http://localhost:8000/tags name=bug

# 带 JSON body
http POST http://localhost:8000/tickets \
  title="测试标题" \
  description="测试描述" \
  tags:='["bug","urgent"]'
```

## 测试文件结构说明

`test.rest` 文件包含以下测试组：

1. **Health Check** - 健康检查
2. **Tags API** - 标签相关 API（创建、查询、删除）
3. **Tickets API** - Ticket 相关 API（CRUD 操作）
4. **错误场景测试** - 404、验证错误等
5. **工作流测试** - 完整的 ticket 生命周期
6. **性能测试** - 分页、边界值测试
7. **边界情况测试** - 特殊字符、Unicode 等

## 变量说明

文件开头定义了以下变量：

```http
@baseUrl = http://localhost:8000
@contentType = application/json
```

这些变量会在所有请求中自动替换。如果需要修改后端地址，只需修改 `@baseUrl` 变量即可。

## 常见问题

### Q: 点击 "Send Request" 没有反应？

**A:** 检查：
1. REST Client 扩展是否已安装并启用
2. 文件是否以 `.rest` 或 `.http` 扩展名保存
3. 后端服务是否正在运行（`http://localhost:8000`）

### Q: 收到连接错误？

**A:** 确保：
1. 后端服务正在运行：`uv run uvicorn app.main:app --reload --port 8000`
2. 端口号正确（默认 8000）
3. 防火墙没有阻止连接

### Q: 收到 404 错误？

**A:** 检查：
1. API 路径是否正确
2. 后端路由是否已注册
3. 数据库迁移是否已运行

### Q: 收到 CORS 错误？

**A:** 确保后端 `.env` 文件中配置了 `ALLOWED_ORIGINS`：
```env
ALLOWED_ORIGINS=http://localhost:3000
```

对于 REST Client，通常不需要 CORS，但如果遇到问题，可以添加：
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## 推荐工作流程

1. **启动后端服务**
   ```bash
   cd w1/project-alpha/backend
   uv run uvicorn app.main:app --reload --port 8000
   ```

2. **打开测试文件**
   - 在 VS Code 中打开 `w1/project-alpha/doc/test.rest`

3. **按顺序测试**
   - 先测试健康检查
   - 然后测试标签 API
   - 最后测试 Ticket API

4. **查看响应**
   - 检查状态码（200, 201, 404 等）
   - 检查响应体内容
   - 验证数据是否正确

5. **调试问题**
   - 查看后端日志输出
   - 检查数据库中的数据
   - 使用浏览器访问 `http://localhost:8000/docs` 查看 Swagger 文档

## 快速开始示例

1. **打开 VS Code**
2. **安装 REST Client 扩展**
3. **打开 `w1/project-alpha/doc/test.rest`**
4. **确保后端运行在 `http://localhost:8000`**
5. **点击第一个请求（健康检查）上方的 "Send Request"**
6. **查看响应结果**

现在你可以开始测试 API 了！🎉
