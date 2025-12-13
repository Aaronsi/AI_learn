# Project Alpha Frontend

前端应用使用 Vite + React + TypeScript + Tailwind CSS + Shadcn UI 构建。

## 环境要求

- Node.js 18+
- npm 或 yarn

## 安装依赖

```bash
npm install
```

## 开发运行

```bash
npm run dev
```

应用将在 `http://localhost:5173` 启动（Vite 默认端口）。

### Windows PowerShell 执行策略问题

如果遇到以下错误：
```
npm : 无法加载文件 ...\npm.ps1，因为在此系统上禁止运行脚本。
```

**解决方案（选择其一）：**

1. **使用 CMD 而不是 PowerShell**（推荐）：
   ```cmd
   cmd
   npm run dev
   ```

2. **临时绕过执行策略**（仅当前会话）：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   npm run dev
   ```

3. **修改执行策略**（需要管理员权限）：
   ```powershell
   # 以管理员身份运行 PowerShell，然后执行：
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **直接使用 node**：
   ```powershell
   node node_modules/.bin/vite
   ```

## 构建

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

## 环境变量

### 配置步骤

1. 复制 `.env.example` 到 `.env`：
```bash
cp .env.example .env
```

2. 修改 `.env` 文件中的配置：

```env
# Backend API Base URL
# Default: http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000
```

**重要说明：**
- `VITE_API_BASE_URL` 必须指向后端服务的地址
- 默认值为 `http://localhost:8000`
- 如果后端运行在不同端口，请相应修改
- 确保后端 `ALLOWED_ORIGINS` 包含前端地址

## 功能特性

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

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **Shadcn UI** - UI 组件库
- **React Query** - 数据获取和状态管理
- **Axios** - HTTP 客户端

## 项目结构

```
src/
├── api/              # API 客户端（已集成到 lib/api.ts）
├── components/       # React 组件
│   ├── ui/          # Shadcn UI 基础组件
│   ├── FiltersBar.tsx
│   ├── TagSelector.tsx
│   ├── TicketList.tsx
│   ├── TicketForm.tsx
│   └── Pagination.tsx
├── hooks/           # 自定义 Hooks
├── lib/             # 工具函数和 API
├── pages/           # 页面组件
├── types/           # TypeScript 类型定义
├── App.tsx          # 根组件
└── main.tsx         # 入口文件
```

## 与后端通信

前端通过 `VITE_API_BASE_URL` 环境变量配置的后端 API 地址进行通信。默认情况下，Vite 开发服务器配置了代理，将 `/api` 请求转发到后端。

## CORS 配置

确保后端 `ALLOWED_ORIGINS` 环境变量包含前端地址（例如：`http://localhost:3000`）。
