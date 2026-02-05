# Doubao Seedream 图像生成 Skill

使用火山引擎 Doubao-Seedream 模型生成高质量图像。支持文生图和图生图两种模式。

## 模型信息

| 项目 | 值 |
|------|-----|
| 模型ID | `doubao-seedream-4-5-251128` |
| API端点 | `https://ark.cn-beijing.volces.com/api/v3` |
| 推荐尺寸 | 1920x1920, 1920x1080, 1080x1920 |

## 核心功能

### 1. 文生图 (Text-to-Image)
从文本描述生成图像。

### 2. 图生图 (Image-to-Image)
使用参考图像进行风格迁移，生成风格一致的新图像。

## API 参数速查

| 参数 | 类型 | 必需 | 说明 |
|------|------|:----:|------|
| `model` | string | ✅ | 固定: `doubao-seedream-4-5-251128` |
| `prompt` | string | ✅ | 图像描述 (中英文均可) |
| `size` | string | ❌ | 尺寸，默认 `1920x1920` |
| `n` | int | ❌ | 生成数量 1-4 |
| `response_format` | string | ❌ | `b64_json` 或 `url` |
| `image` | string | ❌ | 参考图 data URL (图生图) |

## 常用尺寸

| 尺寸 | 比例 | 用途 |
|------|------|------|
| `1920x1920` | 1:1 | 默认方图 |
| `1920x1080` | 16:9 | 横版/PPT |
| `1080x1920` | 9:16 | 竖版/手机 |
| `1024x1024` | 1:1 | 快速生成 |
| `2048x2048` | 1:1 | 超高清 |

## Prompt 技巧

### 基本结构
```
[主体] + [风格] + [光线] + [质量词]
```

### 风格关键词

| 类型 | 关键词 |
|------|--------|
| 摄影 | 专业摄影、商业摄影、人像摄影、风光摄影 |
| 绘画 | 油画、水彩、素描、数字艺术、概念艺术 |
| 风格 | 赛博朋克、极简主义、日系动漫、吉卜力风格 |
| 光线 | 自然光、黄金时刻、逆光、霓虹灯、工作室灯光 |

### 质量增强词
`高清`, `4K`, `8K`, `精细细节`, `专业级`, `大师作品`

### 示例 Prompt

```
# 人物肖像
年轻女性肖像，柔和自然光，浅景深，专业摄影，高清

# 风景
日落时分的海边悬崖，金色阳光，电影级画面，4K

# 产品
高端护肤品，白色背景，工作室灯光，商业摄影

# 艺术
赛博朋克城市，霓虹灯，雨夜，科幻电影感
```

## 环境配置

在 `.env` 文件中配置:
```env
ARK_API_KEY=your_api_key_here
ARK_API_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL_ID=doubao-seedream-4-5-251128
```

## 语言支持

根据你使用的编程语言，参考对应的实现文档:

- **Python**: 参见 [references/python.md](references/python.md)

## 错误处理

| 错误码 | 原因 | 解决方案 |
|--------|------|----------|
| 401 | API Key 无效 | 检查 ARK_API_KEY |
| 400 | 参数错误 | 检查 size 格式 |
| 429 | 频率限制 | 等待后重试 |
| 500 | 服务器错误 | 稍后重试 |

## 参考资源

- [火山引擎 Ark 文档](https://www.volcengine.com/docs/82379/1824121)
- [Seedream Prompt 指南](https://docs.byteplus.com/id/docs/ModelArk/1829186)
- 本项目实现参考: `backend/app/clients/ark_client.py`
