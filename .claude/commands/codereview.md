# Code Review Commands

深度代码审查命令集，专注于 Python 和 TypeScript 代码的全面质量分析。

---

## `/codereview.deep`

对指定的代码文件或目录进行全面深度审查，涵盖架构设计、代码质量、最佳实践等所有方面。
once it finished, it shall create a markdown file under ./specs/ with proper name - e.o. <number>-deep-code-review.md.

**用法：**
```
/codereview.deep @path/to/file.py
/codereview.deep @path/to/directory/
```

**审查维度：**

### 1. 架构与设计 (Architecture & Design)
- **最佳实践符合度**
  - Python: PEP 8, 类型注解使用、异步编程模式、上下文管理器
  - TypeScript: 接口优先设计、类型安全、装饰器使用、泛型设计
- **接口设计清晰度**
  - 公共API的清晰性和一致性
  - 抽象层次是否合理
  - 依赖注入和控制反转的应用
- **可扩展性评估**
  - 开闭原则 (OCP) 的遵循
  - 插件化架构的可能性
  - 配置与代码分离
  - 策略模式和工厂模式的应用

### 2. KISS 原则 (Keep It Simple, Stupid)
- 是否存在过度设计
- 逻辑复杂度分析（圈复杂度）
- 不必要的抽象层检测
- 是否有更简单的实现方案

### 3. 代码质量原则
- **DRY (Don't Repeat Yourself)**
  - 代码重复检测
  - 可提取的共同逻辑
  - 重复的业务逻辑模式
- **YAGNI (You Aren't Gonna Need It)**
  - 未使用的功能和代码
  - 过早优化的场景
  - 预留但不需要的扩展点
- **SOLID 原则**
  - **S**RP: 单一职责原则
  - **O**CP: 开闭原则
  - **L**SP: 里氏替换原则
  - **I**SP: 接口隔离原则
  - **D**IP: 依赖倒置原则

### 4. 代码度量 (Code Metrics)
- **函数长度**: 标记超过 150 行的函数
- **参数数量**: 标记超过 7 个参数的函数
- **嵌套深度**: 标记过深的嵌套（>4层）
- **认知复杂度**: 评估代码的理解难度

### 5. 设计模式应用
- **Builder 模式**
  - 复杂对象构造是否适合 Builder 模式
  - 现有 Builder 实现的质量
  - 流式 API 的设计
- **其他模式**
  - 单例、工厂、策略、观察者等模式的合理性

**输出格式：**
审查报告保存在 `code-reviews/{file-name}/{timestamp}-deep-review.md`，包含：
- 执行摘要（严重程度分级：Critical/High/Medium/Low）
- 各维度详细分析
- 具体问题位置（文件名:行号）
- 改进建议和重构方案
- 示例代码对比

**示例：**
```
/codereview.deep @src/services/user_service.py
/codereview.deep @src/api/
```

---

## `/codereview.architecture`

专注于架构和设计层面的审查，评估代码的结构化程度和设计模式应用。

**用法：**
```
/codereview.architecture @path/to/file.{py,ts}
```

**审查重点：**
- 分层架构的合理性（Controller/Service/Repository）
- 模块间的耦合度和内聚性
- 依赖方向是否正确（高层不依赖低层）
- 领域模型的清晰度
- 接口定义和契约设计
- 错误处理架构（异常层次、错误传播）
- 可测试性设计（依赖注入、模拟友好）

**特定语言检查：**
- **Python**:
  - 包结构组织（__init__.py 使用）
  - ABC (Abstract Base Classes) 使用
  - Protocol 和 TypedDict 应用
  - 装饰器和上下文管理器设计
- **TypeScript**:
  - 接口 vs 类型别名的选择
  - 模块导出策略
  - 泛型约束设计
  - 命名空间使用

**示例：**
```
/codereview.architecture @src/core/engine.ts
```

---

## `/codereview.quality`

深入分析代码质量，关注 DRY、YAGNI、SOLID 等原则的遵循情况。

**用法：**
```
/codereview.quality @path/to/file.{py,ts}
```

**检查项：**

1. **重复代码分析**
   - 相似代码块检测（>6行）
   - 重复的业务逻辑
   - 可提取的公共函数

2. **死代码检测**
   - 未调用的函数和类
   - 注释掉的代码
   - 未使用的导入和变量

3. **SOLID 违规**
   - 单一职责违规（函数/类做太多事）
   - 过多的 if-else（违反 OCP）
   - 接口污染（ISP 违规）
   - 具体类依赖（DIP 违规）

4. **代码异味 (Code Smells)**
   - Long Method / Large Class
   - Long Parameter List
   - Primitive Obsession
   - Data Clumps
   - Feature Envy
   - Shotgun Surgery

5. **命名规范**
   - Python: snake_case, PascalCase, UPPER_CASE
   - TypeScript: camelCase, PascalCase, UPPER_CASE
   - 魔法数字和字符串

**示例：**
```
/codereview.quality @src/utils/helpers.py
```

---

## `/codereview.metrics`

量化分析代码度量指标，确保符合设定的标准。

**用法：**
```
/codereview.metrics @path/to/file.{py,ts} [--threshold=strict|normal|relaxed]
```

**度量标准：**

| 指标 | Strict | Normal | Relaxed |
|------|--------|--------|---------|
| 函数行数 | 50 | 150 | 200 |
| 参数数量 | 4 | 7 | 10 |
| 圈复杂度 | 5 | 10 | 15 |
| 嵌套深度 | 3 | 4 | 5 |
| 类方法数 | 10 | 20 | 30 |
| 文件行数 | 300 | 500 | 800 |

**检查内容：**
- 超过阈值的函数列表（含具体行号）
- 复杂度热力图
- 参数列表过长的建议（使用配置对象/数据类）
- 认知复杂度得分
- 代码重复率百分比

**输出示例：**
```
❌ function processUserData (line 45-230): 186 lines (exceeds 150)
   建议: 拆分为 validateUser, transformData, saveUser

❌ function createOrder (line 312): 9 parameters (exceeds 7)
   建议: 使用 Builder 模式或配置对象

⚠️  function calculatePrice (line 156): complexity 12 (exceeds 10)
   建议: 提取条件逻辑到策略模式
```

**示例：**
```
/codereview.metrics @src/services/order_service.py --threshold=strict
```

---

## `/codereview.patterns`

检查设计模式的应用和实现质量，特别关注 Builder 模式等创建型模式。

**用法：**
```
/codereview.patterns @path/to/file.{py,ts} [--focus=builder|factory|singleton]
```

**检查重点：**

### Builder 模式专项
- **适用场景识别**
  - 构造函数参数 > 5个
  - 必选/可选参数组合复杂
  - 对象创建需要多步骤
  - 需要创建不可变对象

- **实现质量**
  - Python: 方法链式调用、__enter__/__exit__ 支持
  - TypeScript: 流式接口、类型安全的 Builder
  - 是否支持验证逻辑
  - 是否有清晰的 build() 方法

- **改进建议**
  - 使用数据类/接口作为配置
  - 添加默认值和验证
  - 提供示例用法

### 其他模式检查
- **工厂模式**: 对象创建是否过于复杂
- **单例模式**: 是否线程安全、是否真的需要单例
- **策略模式**: if-else 链是否应该用策略替代
- **观察者模式**: 事件驱动场景的实现
- **装饰器模式**: 功能增强是否合理

**示例：**
```
/codereview.patterns @src/builders/ --focus=builder
/codereview.patterns @src/factories/widget_factory.ts
```

---

## `/codereview.best-practices`

检查语言特定的最佳实践和惯用法。

**用法：**
```
/codereview.best-practices @path/to/file.{py,ts}
```

**Python 最佳实践：**
- 类型注解完整性（typing, mypy 兼容）
- 上下文管理器使用（with 语句）
- 列表推导式 vs 循环
- 生成器和迭代器的合理使用
- 异常处理最佳实践（具体异常、finally 块）
- dataclass vs NamedTuple vs attrs 选择
- async/await 模式
- 装饰器和描述符应用
- 魔法方法实现（__repr__, __eq__ 等）

**TypeScript 最佳实践：**
- 严格模式配置（strict: true）
- 类型收窄和类型守卫
- never 和 unknown 类型使用
- 联合类型和交叉类型
- 泛型约束（extends, keyof, typeof）
- readonly 和 const assertions
- 映射类型和条件类型
- 工具类型使用（Partial, Required, Pick 等）
- Promise 和 async/await 模式
- 错误处理（Result 类型、Option 类型）

**示例：**
```
/codereview.best-practices @src/models/user.py
```

---

## `/codereview.security`

安全性审查，检查常见的安全漏洞和风险。

**用法：**
```
/codereview.security @path/to/file.{py,ts}
```

**检查项：**
- SQL 注入风险
- XSS 漏洞
- CSRF 防护
- 敏感信息泄露（hardcoded secrets, 日志记录密码）
- 输入验证和清理
- 路径遍历攻击
- 不安全的反序列化
- 加密算法选择（避免 MD5, SHA1）
- 随机数生成（使用 secrets 而非 random）
- 依赖漏洞提示

**示例：**
```
/codereview.security @src/api/auth.py
```

---

## `/codereview.refactor`

基于审查结果生成重构方案和示例代码。

**用法：**
```
/codereview.refactor @path/to/file.{py,ts} [--priority=high|all]
```

**输出内容：**
- 重构优先级列表
- 具体重构步骤
- Before/After 代码对比
- 单元测试建议
- 重构风险评估

**示例：**
```
/codereview.refactor @src/legacy/payment.py --priority=high
```

---

## `/codereview.report`

生成项目整体的代码质量报告。

**用法：**
```
/codereview.report @path/to/project/
```

**报告内容：**
- 项目概览（文件数、代码行数、测试覆盖率）
- 质量评分（A-F 等级）
- 问题统计（按严重程度和类型）
- 热点文件（问题最多的文件）
- 趋势分析（如果有历史数据）
- 可操作建议清单

**示例：**
```
/codereview.report @src/
```

---

## 配置文件

可在 `.claude/codereview.config.json` 中自定义审查规则：

```json
{
  "thresholds": {
    "maxFunctionLines": 150,
    "maxParameters": 7,
    "maxComplexity": 10,
    "maxNestingDepth": 4
  },
  "rules": {
    "enforceTypeHints": true,
    "enforceDocstrings": true,
    "requireBuilderForComplexObjects": true,
    "minBuilderParameterCount": 5
  },
  "patterns": {
    "preferredPatterns": ["builder", "factory", "strategy"],
    "avoidPatterns": ["singleton"]
  },
  "ignore": [
    "**/migrations/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/*.test.{py,ts}"
  ]
}
```

---

## 使用流程示例

### 场景 1：新功能代码审查
```bash
# 1. 全面审查
/codereview.deep @src/features/payment/

# 2. 查看具体问题
cd code-reviews/payment/

# 3. 重构高优先级问题
/codereview.refactor @src/features/payment/processor.py --priority=high
```

### 场景 2：架构重构前评估
```bash
# 1. 架构分析
/codereview.architecture @src/core/

# 2. 度量检查
/codereview.metrics @src/core/ --threshold=strict

# 3. 模式识别
/codereview.patterns @src/core/

# 4. 生成重构方案
/codereview.refactor @src/core/ --priority=all
```

### 场景 3：代码质量提升
```bash
# 1. 质量检查
/codereview.quality @src/

# 2. 最佳实践
/codereview.best-practices @src/

# 3. 生成报告
/codereview.report @src/
```

---

## 审查原则

1. **严格但务实**: 遵循原则但不教条，考虑实际场景
2. **可操作性**: 每个问题都提供具体的改进建议
3. **优先级明确**: Critical > High > Medium > Low
4. **代码示例**: 提供重构前后的代码对比
5. **学习导向**: 解释为什么这样做更好
6. **工具友好**: 输出格式适合与 IDE、CI/CD 集成

---

## 集成建议

### Pre-commit Hook
```yaml
- repo: local
  hooks:
    - id: code-review
      name: Claude Code Review
      entry: claude-code codereview.quality
      language: system
      pass_filenames: true
```

### CI/CD Pipeline
```yaml
- name: Code Quality Check
  run: |
    claude-code codereview.report @src/ > quality-report.md
    if grep -q "Critical" quality-report.md; then exit 1; fi
```
