# Tauri API 初始化问题修复

## 问题描述

在启动应用并录入语音时，出现以下错误：

```
Cannot read properties of undefined (reading 'transformCallback')
Cannot read properties of undefined (reading 'invoke')
Failed to start transcription service
```

### 错误位置

1. `transcription.ts:84` - `listen()` 函数调用
2. `FloatingWindow.tsx:80` - `listen()` 函数调用
3. `FloatingWindow.tsx:157` - `toggleRecording()` 函数调用
4. `App.tsx:17` - `invoke()` 函数调用

## 根本原因

### 原因 1：缺少 `withGlobalTauri` 配置

在 Tauri v2 中，需要显式启用 `withGlobalTauri` 来初始化全局 IPC (进程间通信) 对象。

### 原因 2：Vite 优化了 Tauri 依赖

Vite 默认会优化所有依赖，但 Tauri 的 API 包含特殊的 IPC 绑定，不应被优化。

### 原因 3：React.StrictMode 双重渲染

在开发模式下，StrictMode 导致组件双重挂载，可能干扰 Tauri 的 IPC 初始化。

### 原因 4：缺少 Tauri 就绪检查

代码直接调用 Tauri API，没有等待 Tauri 完全初始化。

## 修复方案

### 修复 1：启用 `withGlobalTauri`

**文件：** `src-tauri/tauri.conf.json`

```json
{
  "app": {
    "withGlobalTauri": true,  // ✅ 添加这一行
    "windows": [...]
  }
}
```

### 修复 2：配置 Vite 排除 Tauri 依赖

**文件：** `vite.config.ts`

```typescript
export default defineConfig({
  // ... 其他配置

  // 阻止 Vite 优化 Tauri 依赖
  optimizeDeps: {
    exclude: [
      '@tauri-apps/api',
      '@tauri-apps/plugin-clipboard-manager',
      '@tauri-apps/plugin-global-shortcut'
    ]
  },

  build: {
    // Tauri 在 Windows 使用 Chromium，在 macOS/Linux 使用 WebKit
    target: process.env.TAURI_PLATFORM == 'windows' ? 'chrome105' : 'safari13',
    // 调试构建不压缩
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    // 调试构建生成 sourcemap
    sourcemap: !!process.env.TAURI_DEBUG,
  },
});
```

### 修复 3：禁用开发模式的 StrictMode

**文件：** `src/main.tsx`

```typescript
const isDev = import.meta.env.DEV;

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  isDev ? (
    <App />  // 开发模式：不使用 StrictMode
  ) : (
    <React.StrictMode>
      <App />  // 生产模式：使用 StrictMode
    </React.StrictMode>
  )
);
```

### 修复 4：创建 Tauri 工具函数

**文件：** `src/utils/tauri.ts` (新文件)

```typescript
/**
 * 检查 Tauri API 是否可用
 */
export function isTauriAvailable(): boolean {
  return typeof window !== 'undefined' && '__TAURI__' in window;
}

/**
 * 等待 Tauri API 就绪
 */
export async function waitForTauri(
  timeout: number = 5000,
  interval: number = 100
): Promise<boolean> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (isTauriAvailable()) {
      console.log('Tauri API is available');
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  console.error('Tauri API initialization timeout');
  return false;
}

/**
 * 安全的 invoke 包装器
 */
export async function safeInvoke<T>(
  command: string,
  args?: unknown
): Promise<T> {
  if (!isTauriAvailable()) {
    throw new Error('Tauri API is not available');
  }

  const { invoke } = await import('@tauri-apps/api/core');
  return invoke<T>(command, args);
}

/**
 * 安全的 listen 包装器
 */
export async function safeListen<T>(
  event: string,
  handler: (event: { payload: T }) => void
): Promise<() => void> {
  if (!isTauriAvailable()) {
    throw new Error('Tauri API is not available');
  }

  const { listen } = await import('@tauri-apps/api/event');
  return listen<T>(event, handler);
}
```

### 修复 5：更新组件使用安全包装器

**文件：** `src/App.tsx`

```typescript
import { waitForTauri, safeInvoke } from './utils/tauri';

function App() {
  useEffect(() => {
    async function initialize() {
      try {
        // 等待 Tauri 就绪
        const ready = await waitForTauri(5000);
        if (!ready) {
          console.error('Tauri API initialization timeout');
          return;
        }

        // 使用安全的 invoke
        const state = await safeInvoke('get_recording_state');
        console.log('Initial recording state:', state);
      } catch (error) {
        console.error('Failed to initialize:', error);
      }
    }

    initialize();
  }, []);
}
```

**文件：** `src/components/raflow/FloatingWindow.tsx`

```typescript
import { waitForTauri, safeListen } from '../../utils/tauri';

export const FloatingWindow: React.FC = () => {
  // ... 其他代码

  useEffect(() => {
    let unlistenFn: (() => void) | null = null;
    let mounted = true;

    async function setupListener() {
      try {
        // 等待 Tauri 就绪
        const ready = await waitForTauri(5000);
        if (!ready) {
          throw new Error('Tauri API initialization timeout');
        }

        if (!mounted) return;

        // 使用安全的 listen
        unlistenFn = await safeListen<number>('audio-level', (event) => {
          useAppStore.getState().setAudioLevel(event.payload);
        });

        console.log('Audio level listener registered');
      } catch (error) {
        console.error('Failed to setup audio level listener:', error);
        if (mounted) {
          setError(`初始化失败: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }
    }

    setupListener();

    return () => {
      mounted = false;
      if (unlistenFn) {
        unlistenFn();
      }
    };
  }, []);
}
```

**文件：** `src/services/transcription.ts`

```typescript
import { waitForTauri, safeInvoke, safeListen } from '../utils/tauri';

export class TranscriptionService {
  async start(config: TranscriptionConfig, callbacks: TranscriptionCallbacks) {
    try {
      // 等待 Tauri 就绪
      const ready = await waitForTauri(5000);
      if (!ready) {
        throw new Error('Tauri API initialization timeout');
      }

      // 使用安全的 listen
      this.audioChunkUnlisten = await safeListen<AudioChunkPayload>(
        'audio-chunk',
        (event) => {
          this.handleAudioChunk(event.payload);
        }
      );

      // 使用安全的 invoke
      await safeInvoke('start_audio_capture');
    } catch (error) {
      console.error('Failed to start transcription service:', error);
      throw error;
    }
  }
}
```

## 验证步骤

### 1. 清理并重新构建

```bash
# 清理 Vite 缓存
rm -rf node_modules/.vite
rm -rf dist

# 重新构建
npm run build
```

### 2. 启动应用

```bash
npm run tauri dev
```

### 3. 检查控制台输出

应该看到：

```
Waiting for Tauri API...
Tauri API is available
RAFlow initialized - Phase 1
Initial recording state: {...}
Audio level listener registered
```

### 4. 测试录音功能

1. 点击"配置"按钮，输入 ElevenLabs API Key
2. 点击"开始录音"按钮
3. 说话测试（例如："你好，这是一个测试"）
4. 点击"停止录音"按钮

应该能看到：

```
Starting transcription service...
Waiting for Tauri API...
Tauri API is available
Setting up event listeners...
Audio level listener registered
Connecting to ElevenLabs WebSocket...
WebSocket connected
Starting audio capture...
Transcription service started successfully
```

## 修改的文件清单

1. ✅ `src-tauri/tauri.conf.json` - 添加 `withGlobalTauri: true`
2. ✅ `vite.config.ts` - 配置依赖排除和构建选项
3. ✅ `src/main.tsx` - 禁用开发模式 StrictMode
4. ✅ `src/utils/tauri.ts` - 创建 Tauri 工具函数（新文件）
5. ✅ `src/App.tsx` - 使用安全包装器
6. ✅ `src/components/raflow/FloatingWindow.tsx` - 使用安全包装器
7. ✅ `src/services/transcription.ts` - 使用安全包装器

## 技术说明

### 为什么需要等待 Tauri 就绪？

在 Tauri v2 中，IPC 层的初始化是异步的：

1. Tauri 应用启动
2. WebView 加载
3. Tauri IPC 注入到 window 对象
4. `window.__TAURI__` 可用

如果在步骤 3 完成之前调用 API，会导致 `transformCallback` 等内部函数未定义。

### 为什么 StrictMode 会导致问题？

React.StrictMode 在开发模式下会：
- 组件挂载两次
- useEffect 执行两次

这可能导致：
- 事件监听器重复注册
- Tauri IPC 状态不一致
- 竞态条件

### 为什么需要排除 Tauri 依赖优化？

Vite 的依赖优化会：
1. 扫描所有依赖
2. 使用 esbuild 预打包
3. 将依赖转换为 ES 模块

但 Tauri 的 API：
- 依赖运行时注入的 `window.__TAURI__`
- 包含特殊的 IPC 转换函数
- 不能被预打包

## 故障排除

### 问题 1：仍然显示 "transformCallback" 错误

**解决方案：**
```bash
# 完全清理
rm -rf node_modules
rm -rf dist
rm -rf src-tauri/target
npm install
npm run build
npm run tauri dev
```

### 问题 2：Tauri API initialization timeout

**检查：**
1. 确认 `tauri.conf.json` 中 `withGlobalTauri: true`
2. 检查浏览器控制台是否有其他错误
3. 验证 Tauri 版本是否为 2.x

### 问题 3：事件监听器没有收到事件

**检查：**
1. Rust 后端是否正确发送事件
2. 事件名称是否匹配
3. 是否在监听器注册后才开始发送事件

## 相关资源

- [Tauri v2 文档](https://v2.tauri.app/)
- [Tauri API 参考](https://v2.tauri.app/reference/javascript/api/)
- [Vite 配置](https://vitejs.dev/config/)

---

**修复日期：** 2024-12-24
**Tauri 版本：** 2.8.0
**修复状态：** ✅ 已完成并测试
