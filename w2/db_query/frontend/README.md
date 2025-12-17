# DB Query Tool Frontend

数据库查询工具前端应用，使用 React + Refine 5 + Monaco Editor 构建。

## 技术栈

- React 19
- TypeScript
- Vite
- Refine 5
- Ant Design
- Monaco Editor
- Tailwind CSS
- React Query (@tanstack/react-query)

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:3000` 启动。

### 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 客户端
│   │   └── client.ts
│   ├── components/       # UI 组件
│   │   ├── DatabaseList.tsx
│   │   ├── DatabaseForm.tsx
│   │   ├── SqlEditor.tsx
│   │   ├── QueryResults.tsx
│   │   └── NaturalLanguageQuery.tsx
│   ├── pages/           # 页面
│   │   └── MainPage.tsx
│   ├── types/           # TypeScript 类型
│   │   └── index.ts
│   ├── App.tsx          # 应用入口
│   ├── main.tsx         # 入口文件
│   └── index.css        # 全局样式
├── package.json
└── vite.config.ts
```

## 功能

- 数据库连接管理
- SQL 编辑器（Monaco Editor）
- SQL 查询执行
- 自然语言生成 SQL
- 查询结果展示

## 开发

确保后端服务运行在 `http://localhost:8000`。

