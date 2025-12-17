# DBeaver 风格布局更新

## 更新内容

已成功将数据库查询工具更新为类似 DBeaver 的布局风格。

### 主要变更

1. **左侧数据库导航树** (`DatabaseTree.tsx`)
   - 显示所有数据库连接
   - 可展开查看模式（schemas）
   - 可展开查看表（tables）
   - 显示表的行数
   - 点击表自动生成 SELECT 查询

2. **数据库连接对话框** (`DatabaseConnectionDialog.tsx`)
   - 类似 DBeaver 的连接设置界面
   - 支持两种连接方式：主机方式 和 URL 方式
   - 连接测试功能
   - 分步向导界面

3. **主页面布局更新** (`MainPage.tsx`)
   - 左侧：数据库导航树（300px 宽度）
   - 右侧：SQL 编辑器和查询结果（各占 50%）
   - 移除了原来的表单和列表卡片布局

### 新增功能

- ✅ 树形数据库导航
- ✅ 按模式（schema）分组显示表
- ✅ 点击表自动生成查询
- ✅ 数据库连接对话框（类似 DBeaver）
- ✅ 连接测试功能
- ✅ 自动加载数据库元数据

### 文件结构

```
frontend/src/
├── components/
│   ├── DatabaseTree.tsx              # 新增：数据库树形导航
│   ├── DatabaseConnectionDialog.tsx  # 新增：连接对话框
│   ├── DatabaseForm.tsx              # 保留（可能不再使用）
│   ├── DatabaseList.tsx              # 保留（可能不再使用）
│   ├── SqlEditor.tsx                 # 保留
│   ├── QueryResults.tsx              # 保留
│   └── NaturalLanguageQuery.tsx      # 保留
├── pages/
│   └── MainPage.tsx                  # 更新：新布局
└── api/
    └── client.ts                      # 更新：添加 refreshDatabaseMetadata 方法
```

### 使用说明

1. **添加数据库连接**
   - 点击左侧导航树顶部的 "+" 按钮
   - 填写连接信息（主机/端口/数据库/用户名/密码 或 URL）
   - 点击"测试连接"验证连接
   - 点击"完成"保存连接

2. **浏览数据库**
   - 在左侧树中展开数据库连接
   - 展开"模式"节点查看所有模式
   - 展开模式节点查看表列表
   - 表名旁边显示行数

3. **查询表数据**
   - 点击左侧树中的表
   - 自动在 SQL 编辑器中生成 `SELECT * FROM schema.table LIMIT 100;`
   - 点击"执行查询"查看结果

### 技术细节

- 使用 Ant Design Tree 组件实现导航树
- 使用 Ant Design Modal 和 Steps 实现连接对话框
- 元数据按需加载（展开时加载）
- 元数据缓存机制避免重复请求

### 待优化项

- [ ] 添加表的右键菜单（查看结构、数据预览等）
- [ ] 添加视图（views）的支持
- [ ] 添加表的列信息显示
- [ ] 优化元数据加载性能
- [ ] 添加数据库连接的编辑和删除功能

