# Spec-Kit Commands

## `/speckit.constitution`

初始化或更新项目的宪法（constitution）文件。宪法文件定义了项目的核心原则、技术栈和编码规范。

**用法：**
```
/speckit.constitution @path/to/instructions.md
```

**功能：**
- 基于 instructions.md 文件创建或更新 `.specify/memory/constitution.md`
- 包含项目概述、技术栈、编码规范、架构设计等核心内容

**示例：**
```
/speckit.constitution @specs/w2/instructions.md
```

---

## `/speckit.specify`

基于 instructions.md 或选中的内容创建详细的项目规范文档。

**用法：**
```
/speckit.specify @path/to/instructions.md [line-range]
```

**功能：**
- 基于 instructions.md 创建详细的需求与设计文档
- 文档保存在 `specs/{project}/0001-spec.md`
- 包含功能需求、API 设计、数据模型、安全控制等详细内容

**示例：**
```
/speckit.specify @specs/w2/instructions.md (14-21)
```

---

## `/speckit.plan`

基于规范文档创建详细的实现计划。

**用法：**
```
/speckit.plan @path/to/spec.md
```

**功能：**
- 基于 spec.md 创建实现计划文档
- 文档保存在 `specs/{project}/0002-implementation-plan.md`
- 包含开发里程碑、代码结构、实现步骤等

**示例：**
```
/speckit.plan @specs/w2/0001-spec.md
```

---

## `/speckit.init`

初始化一个新的 Spec-Kit 项目。

**用法：**
```
/speckit.init [project-name]
```

**功能：**
- 创建项目目录结构
- 初始化 `.specify` 目录
- 创建基础的 constitution.md 文件

**示例：**
```
/speckit.init my-project
```

---

## `/speckit.check`

检查 Spec-Kit 项目配置和工具依赖。

**用法：**
```
/speckit.check
```

**功能：**
- 检查 `.specify` 目录是否存在
- 验证 constitution.md 文件
- 检查必要的工具（git, specify CLI 等）

---

## `/speckit.refresh`

刷新项目的 metadata 和规范文档。

**用法：**
```
/speckit.refresh
```

**功能：**
- 重新读取 constitution.md
- 更新项目规范
- 同步最新的项目状态

