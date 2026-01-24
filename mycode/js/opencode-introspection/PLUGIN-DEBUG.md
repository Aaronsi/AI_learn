# Plugin 调试指南

## 问题描述
`log-conversation.ts` plugin 没有正确运行并生成 jsonl 文件。

## 可能的原因

### 1. Plugin 路径格式问题
在 Windows 上，`file://` URL 的格式应该是：
- ✅ 正确: `file:///D:/path/to/file.ts` (三个斜杠)
- ❌ 错误: `file://D:/path/to/file.ts` (两个斜杠)

当前配置使用的是 `file://D:/...`，可能需要改为 `file:///D:/...`

### 2. Plugin 没有被加载
检查方法：
1. 启动 opencode 时查看控制台输出，应该能看到 `[log-conversation] Plugin loaded successfully`
2. 如果没有看到这个日志，说明 plugin 没有被加载

### 3. Hooks 没有被触发
检查方法：
- 与 opencode 交互时，查看控制台输出，应该能看到各种 hook 的触发日志：
  - `[log-conversation] chat.message hook triggered`
  - `[log-conversation] chat.params hook triggered`
  - `[log-conversation] experimental.chat.messages.transform hook triggered`
  - `[log-conversation] experimental.text.complete hook triggered`

### 4. 文件写入权限问题
检查 `logs/` 目录是否有写入权限。

## 调试步骤

### 步骤 1: 检查 plugin 路径格式
尝试修改 `opencode.json` 中的路径：
```json
{
  "plugin": [
    "file:///D:/develop/AI_learn/mycode/js/opencode-introspection/plugins/log-conversation.ts"
  ]
}
```

或者使用相对路径（如果 opencode 在项目目录下运行）：
```json
{
  "plugin": [
    "./plugins/log-conversation.ts"
  ]
}
```

### 步骤 2: 检查 plugin 是否被加载
1. 启动 opencode
2. 查看控制台输出，寻找 `[log-conversation] Plugin loaded successfully`
3. 如果没有看到，检查：
   - opencode.json 的路径是否正确
   - plugin 文件是否存在
   - 是否有语法错误

### 步骤 3: 检查 hooks 是否被触发
1. 与 opencode 进行一次对话
2. 查看控制台输出，应该能看到各种 hook 的日志
3. 如果没有看到，可能是：
   - hooks 名称不正确
   - hooks 没有被正确注册
   - opencode 版本不支持这些 hooks

### 步骤 4: 检查文件写入
1. 确认 `logs/` 目录存在
2. 确认有写入权限
3. 查看是否有 jsonl 文件生成

## 常见问题

### Q: 为什么看不到任何日志？
A: 可能是：
1. Plugin 没有被加载（检查路径格式）
2. Console.log 输出被重定向或隐藏
3. opencode 运行在不同的进程中

### Q: 为什么 hooks 没有被触发？
A: 可能是：
1. Hook 名称拼写错误
2. Hook 的签名不正确
3. opencode 版本不支持这些 hooks

### Q: 为什么文件没有被写入？
A: 可能是：
1. 目录权限问题
2. `completeTurn` 函数没有被调用
3. 文件路径解析错误

## 下一步
如果以上步骤都没有解决问题，请：
1. 检查 opencode 的版本
2. 查看 opencode 的官方文档，确认 hooks 的正确用法
3. 查看 opencode 的源码，了解 plugin 系统的工作原理

