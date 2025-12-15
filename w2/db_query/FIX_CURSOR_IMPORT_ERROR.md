# 修复 Cursor IDE 导入错误

## 问题确认

✅ **依赖已安装**：sqlalchemy 2.0.45 已安装
✅ **Python 可导入**：命令行测试通过
❌ **IDE 报错**：Cursor 显示黄色波浪线

## 快速修复步骤

### 步骤 1：手动选择 Python 解释器（必须）

1. 在 Cursor 中，点击**右下角的 Python 版本显示**
2. 如果看到多个选项，选择：
   - `Python 3.12.7 ('.venv': venv) .\backend\.venv\Scripts\python.exe`
   - 或者选择 `Enter interpreter path...`
3. 输入绝对路径：
   ```
   D:\develop\AI_learn\w2\db_query\backend\.venv\Scripts\python.exe
   ```

### 步骤 2：重新加载窗口

1. 按 `Ctrl+Shift+P` 打开命令面板
2. 输入：`Developer: Reload Window`
3. 回车

### 步骤 3：验证

重新加载后：
- 右下角应显示正确的 Python 路径
- 黄色波浪线应该消失
- 导入应该正常工作

## 如果仍然报错

### 方法 1：检查工作区根目录

确保 Cursor 打开的是 `w2/db_query` 目录（不是 `backend` 目录）。

### 方法 2：重启 Cursor

完全关闭 Cursor 并重新打开。

### 方法 3：清除 Python 缓存

1. 关闭 Cursor
2. 删除 `backend/.venv/__pycache__` 文件夹（如果存在）
3. 重新打开 Cursor

### 方法 4：验证配置文件

确认以下文件存在：
- `.vscode/settings.json` ✅ 已创建（使用绝对路径）
- `backend/pyrightconfig.json` ✅ 已创建

## 验证依赖安装

运行以下命令确认：

```bash
cd w2\db_query\backend
uv run python -c "from sqlalchemy.ext.asyncio import AsyncSession; print('OK')"
```

如果输出 `OK`，说明依赖已正确安装。

## 当前配置

- ✅ Python 解释器路径：`D:\develop\AI_learn\w2\db_query\backend\.venv\Scripts\python.exe`
- ✅ 配置文件已更新为绝对路径
- ✅ Pyright 配置已更新

## 重要提示

**最关键的一步**：必须在 Cursor 中手动选择正确的 Python 解释器！

即使配置文件正确，Cursor 也可能不会自动识别，需要手动选择一次。


