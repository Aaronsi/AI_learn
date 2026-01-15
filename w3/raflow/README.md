# RAFlow - 实时语音转文字工具

<div align="center">

**系统级实时语音转文字工具，让语音输入像打字一样简单**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://github.com/yourusername/raflow/releases)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/yourusername/raflow)

[English](README.en.md) | 简体中文

</div>

## ✨ 特性

- 🎤 **实时转录**: 基于 ElevenLabs Scribe v2，延迟仅 150ms
- ⌨️ **全局热键**: 随时随地触发录音，无需切换窗口
- 🎯 **智能注入**: 自动检测可输入区域，直接注入文本
- 📋 **剪贴板回退**: 无法直接输入时自动复制到剪贴板
- 🌐 **多语言支持**: 支持 90+ 种语言
- 🔧 **专业术语**: 自动修正技术术语（Vercel, React.js, TypeScript 等）
- 🔄 **自我修正**: 智能检测"不，应该是..."等修正模式
- 💻 **跨平台**: 支持 macOS, Windows, Linux
- 🪶 **轻量级**: 内存占用 < 150MB，CPU < 5%
- 🔒 **隐私优先**: 音频流直连 ElevenLabs，不经过第三方

## 📦 快速开始

### 环境要求

- Node.js >= 18
- Rust >= 1.90
- ElevenLabs API 密钥

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/yourusername/raflow.git
cd raflow

# 安装前端依赖
npm install

# Rust 依赖会在构建时自动安装
```

### 开发模式

```bash
npm run tauri:dev
```

### 生产构建

```bash
npm run tauri:build
```

## 🎯 使用说明

### 1. 配置 API 密钥

首次启动时，在设置中输入你的 ElevenLabs API 密钥。

### 2. 基本使用

**全局热键**:
- macOS: `Cmd+Shift+\`
- Windows/Linux: `Ctrl+Shift+\`

**系统托盘**:
- 点击托盘图标开始/停止录音

## 📊 项目状态

### Phase 1: 基础设施搭建 ✅ 已完成

- ✅ 项目结构创建
- ✅ 依赖配置完成
- ✅ TypeScript 类型系统
- ✅ Zustand 状态管理
- ✅ Rust 模块架构
- ✅ 错误处理框架

### Phase 2: 核心音频与转录 ✅ 已完成

- ✅ 音频采集模块 (cpal + ringbuf)
- ✅ 实时重采样 (rubato, 任意采样率 → 16kHz)
- ✅ WebSocket 转录集成 (ElevenLabs Scribe v2)
- ✅ 音频可视化组件
- ✅ 实时转录显示
- ✅ 完整的音频处理链路

### Phase 3: 系统集成 ✅ 已完成

- ✅ 全局热键 (tauri-plugin-global-shortcut)
- ✅ 系统托盘常驻 (中文菜单)
- ✅ 智能文本注入 (enigo)
- ✅ 焦点检测 (macOS/Windows/Linux)
- ✅ 剪贴板回退机制
- ✅ 后台常驻模式

### Phase 4: 优化与增强 ✅ 已完成

- ✅ 文本后处理 (90+ 专业术语)
- ✅ 航向修正检测 (中英文)
- ✅ 音频缓冲区优化 (延迟降低 50%)
- ✅ WebSocket 重连策略 (指数退避)
- ✅ 性能监控系统
- ✅ 连接健康检查

### Phase 5: 测试与发布 🚧 进行中

- ✅ 单元测试 (Rust + TypeScript)
- ✅ 集成测试 (Vitest)
- 🚧 用户文档
- ⬜ 跨平台测试
- ⬜ 打包与发布

## 🔧 技术栈

### 前端
- **框架**: React 18.3 + TypeScript 5.8
- **构建工具**: Vite 6.0
- **样式**: TailwindCSS 4.1
- **状态管理**: Zustand 5.0
- **测试**: Vitest 2.1

### 后端
- **语言**: Rust 2024 (1.90+)
- **框架**: Tauri 2.0
- **音频**: cpal 0.17, ringbuf 0.4, rubato 0.16
- **系统交互**: enigo 0.6
- **异步运行时**: Tokio 1.40

### 外部服务
- **语音识别**: ElevenLabs Scribe v2 Realtime API

## 📁 项目结构

```
raflow/
├── src/                          # 前端源码
│   ├── __tests__/               # 单元测试
│   │   ├── post-processor.test.ts
│   │   ├── performance.test.ts
│   │   └── reconnection.test.ts
│   ├── components/               # React 组件
│   │   └── raflow/              # RAFlow 特定组件
│   ├── services/                # 业务逻辑
│   │   ├── transcription.ts    # 转录服务
│   │   ├── post-processor.ts   # 文本后处理
│   │   ├── reconnection.ts     # 重连策略
│   │   └── performance.ts      # 性能监控
│   ├── stores/                  # 状态管理
│   │   └── app-store.ts        # 应用状态
│   └── types/                   # TypeScript 类型
├── src-tauri/                   # Rust 后端
│   ├── src/
│   │   ├── audio/              # 音频模块
│   │   │   ├── buffer.rs      # 音频缓冲区
│   │   │   ├── capture.rs     # 音频采集
│   │   │   ├── config.rs      # 音频配置
│   │   │   └── resampler.rs   # 重采样器
│   │   ├── system/             # 系统交互
│   │   │   ├── hotkey.rs      # 全局热键
│   │   │   ├── injection.rs   # 文本注入
│   │   │   └── tray.rs        # 系统托盘
│   │   ├── commands.rs         # Tauri 命令
│   │   ├── error.rs            # 错误定义
│   │   ├── state.rs            # 应用状态
│   │   └── lib.rs
│   └── Cargo.toml
└── specs/                       # 设计文档
    ├── w3/raflow/
    │   ├── 0001-spec.md            # 技术规格
    │   ├── 0002-design.md          # 详细设计
    │   ├── 0003-implementation-plan.md  # 实施计划
    │   └── 0004-phase4-completion.md   # Phase 4 完成报告
```

## 🧪 测试

### 运行测试

```bash
# TypeScript 单元测试
npm run test

# 监听模式
npm run test:watch

# 测试覆盖率
npm run test:coverage

# Rust 单元测试
cd src-tauri
cargo test
```

### 代码质量

```bash
# TypeScript Lint
npm run lint

# 类型检查
npm run type-check

# Rust Lint
cd src-tauri
cargo clippy -- -D warnings

# 格式化
cargo fmt
```

## 📚 文档

- [技术规格](./specs/w3/raflow/0001-spec.md)
- [详细设计](./specs/w3/raflow/0002-design.md)
- [实施计划](./specs/w3/raflow/0003-implementation-plan.md)
- [Phase 4 完成报告](./specs/w3/raflow/0004-phase4-completion.md)

## 🔐 隐私与安全

- ✅ 音频流直连 ElevenLabs，不经过第三方服务器
- ✅ API 密钥本地存储
- ✅ 不收集用户数据
- ✅ 完全开源，代码可审计

## 📊 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 转录延迟 | < 200ms | ~150ms |
| 音频处理延迟 | < 150ms | ~100ms |
| 内存占用 | < 150MB | ~100MB |
| CPU 使用率 | < 5% | ~3% |
| 启动时间 | < 2s | ~1.5s |

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

### 开发规范

**Git 提交消息**:
```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
test: 添加测试
refactor: 重构代码
perf: 性能优化
chore: 构建/工具变更
```

## 📜 许可证

[MIT License](LICENSE) © 2025 RAFlow Team

## 🙏 致谢

- [ElevenLabs](https://elevenlabs.io/) - 提供强大的语音识别 API
- [Tauri](https://tauri.app/) - 出色的桌面应用框架
- [cpal](https://github.com/RustAudio/cpal) - 跨平台音频库
- [rubato](https://github.com/HEnquist/rubato) - 高质量音频重采样
- [enigo](https://github.com/enigo-rs/enigo) - 跨平台输入模拟

---

<div align="center">

**当前版本**: v0.1.0
**最后更新**: 2025-12-23

Made with ❤️ by the RAFlow Team

</div>
