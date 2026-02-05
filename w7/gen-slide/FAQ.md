# 常见问题解答 (FAQ)

## Backend相关

### Q: 为什么运行时提示 `ModuleNotFoundError: No module named 'blake3'`？

**A**: 这是因为你直接使用了系统的Python而不是uv管理的虚拟环境。

**解决方案**：
1. 确保已经运行 `uv sync` 安装依赖
2. 始终使用 `uv run` 前缀来运行Python命令：
   ```bash
   # 错误 ❌
   cd backend
   python -m app.main

   # 正确 ✅
   cd backend
   uv run python -m app.main
   ```

### Q: 为什么运行时提示 `ModuleNotFoundError: No module named 'app'`？

**A**: 这是因为Python的模块搜索路径问题。Backend代码使用相对导入（如 `from app.api.router import api_router`）。

**解决方案**：
1. 始终从backend目录运行命令：
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

2. 或使用项目根目录的启动脚本：
   ```bash
   # 从项目根目录
   ./start-backend.bat  # Windows
   ./start-backend.sh   # Linux/Mac
   ```

### Q: 如何验证uv环境是否正确？

**A**: 运行以下命令检查：

```bash
# 检查uv版本
uv --version

# 检查Python路径（应该指向.venv目录）
uv run python -c "import sys; print(sys.executable)"

# 检查blake3是否安装
uv run python -c "import blake3; print(blake3.__version__)"
```

预期输出：
```
uv 0.9.16 (或更高版本)
D:\develop\AI_learn\w7\gen-slide\.venv\Scripts\python.exe
1.0.8
```

### Q: 端口8000已被占用怎么办？

**A**:
1. 找到占用端口的进程：
   ```bash
   # Windows
   netstat -ano | findstr :8000

   # Linux/Mac
   lsof -i :8000
   ```

2. 停止该进程：
   ```bash
   # Windows
   taskkill /F /PID <进程ID>

   # Linux/Mac
   kill -9 <进程ID>
   ```

3. 或者使用不同的端口：
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload --port 8001
   ```

### Q: 如何添加新的Python依赖？

**A**: 使用uv命令从项目根目录添加：

```bash
# 添加运行时依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 添加特定版本
uv add package-name@1.2.3

# 同步依赖（安装所有依赖）
uv sync
```

### Q: 旧的venv目录可以删除吗？

**A**: 可以！现在使用uv管理依赖，旧的 `backend/venv/` 目录不再需要：

```bash
# 安全删除
rm -rf backend/venv  # Linux/Mac
rmdir /s backend\venv  # Windows
```

## Frontend相关

### Q: 首次打开页面看不到欢迎界面？

**A**: 欢迎界面只在项目没有slides时显示。如果你的项目已经有slides，你会看到正常的编辑界面。

要查看欢迎界面：
1. 访问一个新的项目URL：`http://localhost:3003/new-project-name`
2. 创建项目后，在添加第一个slide之前会看到欢迎界面

### Q: 页面滚动不正常？

**A**: 确保你使用的是最新的代码。主要修复包括：
- 页面根容器使用 `overflow-hidden`
- Flex容器使用 `min-h-0`
- 侧边栏和主内容区独立滚动

### Q: 如何启动Frontend开发服务器？

**A**:
```bash
cd frontend
npm install  # 首次运行
npm run dev
```

访问：http://localhost:3003

## 通用问题

### Q: 如何同时启动Backend和Frontend？

**A**: 需要两个终端窗口：

**终端1 - Backend**:
```bash
cd gen-slide
./start-backend.bat  # Windows
./start-backend.sh   # Linux/Mac
```

**终端2 - Frontend**:
```bash
cd gen-slide/frontend
npm run dev
```

### Q: 如何检查服务是否正常运行？

**A**:
- Backend健康检查：http://localhost:8000/health
- Backend API文档：http://localhost:8000/docs
- Frontend应用：http://localhost:3003

### Q: 在哪里配置Volcano Ark API密钥？

**A**:
1. 复制环境变量模板：
   ```bash
   cd backend
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，添加你的API密钥：
   ```
   ARK_API_KEY=your_api_key_here
   ```

### Q: 项目数据存储在哪里？

**A**: 所有slides数据存储在 `backend/slides/` 目录下：
```
backend/slides/
└── <project-slug>/
    ├── outline.yml          # Slides元数据
    ├── style.jpg            # 风格参考图片
    └── images/
        └── <slide-id>/
            └── <hash>.jpg   # 生成的图片
```

### Q: 如何清理项目重新开始？

**A**:
```bash
# 删除所有slides数据
rm -rf backend/slides/*

# 重新安装依赖
uv sync
cd frontend && npm install
```

## 开发相关

### Q: 如何查看详细的错误日志？

**A**: Backend使用Python的logging模块，日志会输出到控制台。要查看更详细的日志：

```bash
cd backend
uv run uvicorn app.main:app --reload --log-level debug
```

### Q: 如何运行测试？

**A**:
```bash
# Backend测试（如果有）
cd backend
uv run pytest

# Frontend测试
cd frontend
npm test
```

### Q: 推荐的开发工具？

**A**:
- **IDE**: VS Code, PyCharm
- **VS Code扩展**:
  - Python
  - Pylance
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense
- **浏览器**: Chrome/Edge (带开发者工具)

## 更多帮助

如果以上FAQ没有解决你的问题：
1. 查看 `README.md` - 项目概述和快速开始
2. 查看 `MIGRATION_TO_UV.md` - uv迁移详细说明
3. 查看 `backend/CLAUDE.md` - Backend开发指南
4. 查看 `frontend/CLAUDE.md` - Frontend开发指南
