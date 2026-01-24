# 如何在 opencode 中设置 DeepSeek 的 API Key

## 方法 1: 使用 opencode auth login（推荐）

这是最简单和推荐的方式：

```powershell
opencode auth login
```

然后：
1. 选择 `deepseek`（如果列表中没有，可能需要先配置）
2. 输入你的 DeepSeek API Key
3. 看到 "Login successful" 提示

验证配置：
```powershell
opencode auth list
```

应该能看到 `deepseek api` 在列表中。

## 方法 2: 使用环境变量

### Windows PowerShell

```powershell
# 临时设置（当前会话有效）
$env:DEEPSEEK_API_KEY = "your-deepseek-api-key"

# 永久设置（用户环境变量）
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "your-deepseek-api-key", "User")
```

设置后需要重启 PowerShell 或手动加载：
```powershell
$env:DEEPSEEK_API_KEY = [System.Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "User")
```

### Linux/macOS

```bash
# 临时设置
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export DEEPSEEK_API_KEY="your-deepseek-api-key"' >> ~/.bashrc
source ~/.bashrc
```

## 方法 3: 在 opencode.json 中配置

编辑 `opencode.json` 文件，添加 DeepSeek provider 配置：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "file://D:/develop/AI_learn/mycode/js/opencode-introspection/plugins/log-conversation.ts"
  ],
  "provider": {
    "deepseek": {
      "name": "DeepSeek",
      "env": ["DEEPSEEK_API_KEY"],
      "options": {
        "apiKey": "your-deepseek-api-key",
        "baseURL": "https://api.deepseek.com"
      }
    }
  }
}
```

**注意**：
- `baseURL` 应该是 `https://api.deepseek.com`（DeepSeek 的官方 API 端点）
- `apiKey` 可以直接写在这里，或者使用环境变量（推荐）
- 如果使用环境变量，可以写成：`"apiKey": "{env:DEEPSEEK_API_KEY}"` 或直接不写（opencode 会自动从环境变量读取）

## 验证配置

### 1. 检查 API Key 是否配置成功

```powershell
opencode auth list
```

应该能看到 DeepSeek 在列表中。

### 2. 检查模型是否可用

```powershell
opencode models deepseek
```

应该能看到：
- `deepseek/deepseek-chat`
- `deepseek/deepseek-reasoner`

### 3. 在 opencode 界面中测试

1. 运行 `opencode`
2. 按 `/` 键打开命令对话框
3. 输入 `models` 或选择 "Switch model"
4. 在模型列表中找到 DeepSeek 的模型
5. 选择一个 DeepSeek 模型测试

## 常见问题

### Q: 为什么在 `/models` 中看不到 DeepSeek 模型？

**A:** 可能的原因：
1. API Key 未正确配置 - 运行 `opencode auth list` 检查
2. 需要重启 opencode - 配置更改后需要重启
3. baseURL 配置错误 - 确保是 `https://api.deepseek.com`

### Q: 如何获取 DeepSeek API Key？

**A:** 
1. 访问 [DeepSeek 官网](https://www.deepseek.com/)
2. 注册/登录账号
3. 进入 API 控制台
4. 创建新的 API Key

### Q: 环境变量和 opencode.json 哪个优先级更高？

**A:** opencode 的加载顺序：
1. `opencode.json` 中的 `options.apiKey`（如果存在）
2. 环境变量（`DEEPSEEK_API_KEY`）
3. `opencode auth login` 保存的凭证（`auth.json`）

如果多个都存在，通常 `opencode.json` 中的配置优先级最高。

## 完整配置示例

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "file://D:/develop/AI_learn/mycode/js/opencode-introspection/plugins/log-conversation.ts"
  ],
  "provider": {
    "anthropic": {
      "name": "Anthropic (88code.ai)",
      "env": ["ANTHROPIC_API_KEY"],
      "options": {
        "apiKey": "88_5d918257373ce8c1ab3917a96e0765f40d233ddd688f8dfcd56ff2c4d803e694",
        "baseURL": "https://www.88code.ai/api"
      }
    },
    "deepseek": {
      "name": "DeepSeek",
      "env": ["DEEPSEEK_API_KEY"],
      "options": {
        "baseURL": "https://api.deepseek.com"
      }
    }
  }
}
```

**注意**：如果使用环境变量，`options.apiKey` 可以省略，opencode 会自动从环境变量读取。

## 总结

**推荐步骤**：
1. ✅ 运行 `opencode auth login`，选择 `deepseek`，输入 API Key
2. ✅ 确保 `opencode.json` 中有 `baseURL` 配置（如果需要自定义）
3. ✅ 运行 `opencode auth list` 验证
4. ✅ 重启 opencode
5. ✅ 使用 `/models` 命令切换模型



