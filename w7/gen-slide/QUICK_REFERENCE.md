# GenSlides 快速参考

## 🚀 快速启动

### 首次安装
```bash
# 1. 安装uv
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装依赖
uv sync
cd frontend && npm install

# 3. 配置API密钥
cd ../backend
cp .env.example .env
# 编辑 .env 添加 ARK_API_KEY
```

### 启动服务

**Backend** (终端1):
```bash
./start-backend.bat  # Windows
./start-backend.sh   # Linux/Mac
```

**Frontend** (终端2):
```bash
cd frontend
npm run dev
```

**访问**: http://localhost:3003

## 📝 常用命令

### Backend
```bash
# 从backend目录运行
cd backend

# 开发模式
uv run uvicorn app.main:app --reload

# 生产模式
uv run uvicorn app.main:app --workers 4

# 添加依赖
cd ..  # 回到项目根目录
uv add package-name
```

### Frontend
```bash
cd frontend

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 🔧 故障排除

### ❌ ModuleNotFoundError: No module named 'blake3'
```bash
# 原因：没有使用uv run
# 解决：
cd backend
uv run uvicorn app.main:app --reload
```

### ❌ ModuleNotFoundError: No module named 'app'
```bash
# 原因：从错误的目录运行
# 解决：
cd backend  # 确保在backend目录
uv run uvicorn app.main:app --reload
```

### ❌ 端口8000已被占用
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <进程ID>

# Linux/Mac
lsof -i :8000
kill -9 <进程ID>

# 或使用不同端口
uv run uvicorn app.main:app --port 8001
```

## 📚 文档索引

| 文档 | 用途 |
|------|------|
| `README.md` | 项目概述和快速开始 |
| `FAQ.md` | 常见问题解答 |
| `COMPLETION_REPORT.md` | 优化完成报告 |
| `MIGRATION_TO_UV.md` | uv迁移指南 |
| `backend/README.md` | Backend API文档 |
| `backend/CLAUDE.md` | Backend开发指南 |
| `frontend/CLAUDE.md` | Frontend开发指南 |

## 🌐 访问地址

| 服务 | 地址 |
|------|------|
| Frontend | http://localhost:3003 |
| Backend API | http://localhost:8000 |
| API文档 (Swagger) | http://localhost:8000/docs |
| API文档 (ReDoc) | http://localhost:8000/redoc |
| 健康检查 | http://localhost:8000/health |

## 💡 使用技巧

### 创建新项目
访问: `http://localhost:3003/your-project-name`

### 查看欢迎页面
创建新项目后，在添加第一个slide之前会自动显示

### 编辑Slide
双击侧边栏中的任意slide

### 重排序Slides
拖拽slide到目标位置

### 插入Slide
点击两个slides之间的空隙

### 生成图片
选中slide后，点击"Generate Image"按钮

### 全屏播放
点击右上角的"Play"按钮

## 🔑 关键要点

✅ **始终使用 `uv run`** - 确保使用正确的虚拟环境
✅ **从backend目录运行** - 确保模块导入正确
✅ **使用启动脚本** - 最简单可靠的方式
✅ **查看FAQ.md** - 包含所有常见问题的解决方案

## 📦 项目结构

```
gen-slide/
├── backend/              # FastAPI后端
│   ├── app/             # 应用代码
│   ├── slides/          # 数据存储
│   └── .env             # 环境配置
├── frontend/            # React前端
│   └── src/             # 源代码
├── .venv/               # uv虚拟环境
├── pyproject.toml       # Python依赖
├── start-backend.bat    # Windows启动脚本
└── start-backend.sh     # Linux/Mac启动脚本
```

## 🎯 核心功能

1. **创建Slides** - 添加文本内容
2. **生成图片** - AI转换文本为图像
3. **设置风格** - 保持视觉一致性
4. **全屏播放** - 演示模式
5. **成本追踪** - 监控API使用

---

**需要帮助？** 查看 `FAQ.md` 或 `COMPLETION_REPORT.md`
