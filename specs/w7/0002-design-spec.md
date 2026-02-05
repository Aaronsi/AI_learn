# GenSlides - 设计规格说明书

## 1. 概述

本文档是 GenSlides 项目的详细设计规格说明书，基于 [PRD](./0001-prd.md) 编写，定义了项目的技术架构、API 接口、数据模型和目录结构。

---

## 2. 项目目录结构

```
genslides/
├── backend/                          # 后端 Python 代码
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── config.py                 # 配置管理（环境变量）
│   │   │
│   │   ├── api/                      # API 层 - 路由定义
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # 路由聚合
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       ├── slides.py         # Slides CRUD 接口
│   │   │       ├── images.py         # 图片相关接口
│   │   │       └── style.py          # 风格相关接口
│   │   │
│   │   ├── services/                 # 业务层 - 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── slide_service.py      # Slide 业务逻辑
│   │   │   ├── image_service.py      # 图片生成业务逻辑
│   │   │   └── style_service.py      # 风格选择业务逻辑
│   │   │
│   │   ├── repositories/             # 存储层 - 数据访问
│   │   │   ├── __init__.py
│   │   │   ├── slide_repository.py   # Slide 数据存取
│   │   │   └── image_repository.py   # 图片文件存取
│   │   │
│   │   ├── models/                   # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── slide.py              # Slide 相关模型
│   │   │   ├── style.py              # Style 相关模型
│   │   │   └── api_schemas.py        # API 请求/响应 Schema
│   │   │
│   │   ├── clients/                  # 外部服务客户端
│   │   │   ├── __init__.py
│   │   │   └── ark_client.py         # 火山方舟 API 客户端
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── __init__.py
│   │       ├── hash.py               # Blake3 哈希工具
│   │       └── yaml_handler.py       # YAML 文件处理
│   │
│   ├── requirements.txt              # Python 依赖
│   ├── .env.example                  # 环境变量示例
│   └── README.md
│
├── frontend/                         # 前端 TypeScript 代码
│   ├── src/
│   │   ├── main.tsx                  # 应用入口
│   │   ├── App.tsx                   # 根组件
│   │   ├── vite-env.d.ts
│   │   │
│   │   ├── components/               # UI 组件
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx        # 顶部导航栏
│   │   │   │   ├── Sidebar.tsx       # 左侧边栏容器
│   │   │   │   └── MainContent.tsx   # 主内容区容器
│   │   │   │
│   │   │   ├── slides/
│   │   │   │   ├── SlideList.tsx     # Slide 列表（支持拖拽）
│   │   │   │   ├── SlideItem.tsx     # 单个 Slide 项
│   │   │   │   ├── SlideEditor.tsx   # Slide 文本编辑器
│   │   │   │   └── SlideInsertLine.tsx # 插入新 Slide 的线
│   │   │   │
│   │   │   ├── preview/
│   │   │   │   ├── SlidePreview.tsx  # 图片预览区
│   │   │   │   ├── Thumbnails.tsx    # 缩略图列表
│   │   │   │   └── GenerateButton.tsx # 生成图片按钮
│   │   │   │
│   │   │   ├── carousel/
│   │   │   │   └── Carousel.tsx      # 全屏走马灯播放
│   │   │   │
│   │   │   ├── style/
│   │   │   │   └── StyleSelector.tsx # 风格选择 Popup
│   │   │   │
│   │   │   └── common/
│   │   │       ├── Button.tsx
│   │   │       ├── Modal.tsx
│   │   │       ├── Loading.tsx
│   │   │       └── Toast.tsx
│   │   │
│   │   ├── stores/                   # Zustand 状态管理
│   │   │   ├── slideStore.ts         # Slide 状态
│   │   │   ├── previewStore.ts       # 预览状态
│   │   │   └── uiStore.ts            # UI 状态（modal、toast等）
│   │   │
│   │   ├── services/                 # API 调用服务
│   │   │   ├── api.ts                # Axios 实例配置
│   │   │   ├── slideApi.ts           # Slide 相关 API
│   │   │   ├── imageApi.ts           # 图片相关 API
│   │   │   └── styleApi.ts           # 风格相关 API
│   │   │
│   │   ├── hooks/                    # 自定义 Hooks
│   │   │   ├── useSlides.ts
│   │   │   ├── useDragAndDrop.ts
│   │   │   └── useCarousel.ts
│   │   │
│   │   ├── types/                    # TypeScript 类型定义
│   │   │   ├── slide.ts
│   │   │   ├── style.ts
│   │   │   └── api.ts
│   │   │
│   │   ├── utils/                    # 工具函数
│   │   │   ├── hash.ts               # Blake3 哈希（前端）
│   │   │   └── helpers.ts
│   │   │
│   │   └── styles/
│   │       └── globals.css           # 全局样式 + Tailwind v4 配置
│   │
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── slides/                           # 数据存储目录（运行时生成）
│   └── <slug>/
│       ├── outline.yml
│       ├── style.jpg
│       └── images/
│           └── <sid>/
│               └── <blake3_hash>.jpg
│
└── README.md                         # 项目说明
```

---

## 3. 后端架构设计

### 3.1 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                     API Layer (api/)                     │
│  - 路由定义、请求参数校验、响应格式化                          │
│  - 依赖注入 Service 层                                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Service Layer (services/)               │
│  - 业务逻辑处理                                           │
│  - 调用 Repository 和 Client                             │
│  - 事务管理、业务规则校验                                   │
└─────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Repository (repositories/)│   │   Client (clients/)     │
│  - 文件系统读写            │   │  - 火山方舟 API 调用      │
│  - YAML 解析/序列化        │   │  - HTTP 请求封装         │
│  - 图片文件管理            │   │                         │
└─────────────────────────┘   └─────────────────────────┘
```

### 3.2 配置管理

```python
# backend/app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 火山方舟配置
    ARK_API_KEY: str
    ARK_API_ENDPOINT: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_MODEL_ID: str = "doubao-seed-1-8-251228"
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 存储路径
    SLIDES_BASE_PATH: str = "./slides"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

## 4. API 接口规格

### 4.1 基础信息

- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **图片返回**: `image/jpeg`

### 4.2 Slides 接口

#### 4.2.1 获取 Slides 数据

```
GET /api/slides/{slug}
```

**Response 200:**
```json
{
  "slug": "hello-world",
  "title": "Hello World Slides",
  "style": {
    "prompt": "科技感、蓝色调、扁平风格",
    "image": "style.jpg"
  },
  "slides": [
    {
      "sid": "slide-001",
      "content": "第一张幻灯片的文字内容",
      "created_at": "2026-01-27T10:00:00Z",
      "updated_at": "2026-01-27T10:30:00Z",
      "current_image_hash": "a1b2c3d4e5f6",
      "has_matching_image": true
    },
    {
      "sid": "slide-002",
      "content": "第二张幻灯片的文字内容",
      "created_at": "2026-01-27T10:05:00Z",
      "updated_at": "2026-01-27T10:35:00Z",
      "current_image_hash": "b2c3d4e5f6g7",
      "has_matching_image": false
    }
  ],
  "total_cost": 0.15
}
```

**说明**: `current_image_hash` 为内容哈希（由 slide content 计算），`has_matching_image` 表示是否存在与该哈希匹配的图片。

**Response 404:**
```json
{
  "error": "not_found",
  "message": "Slides project not found"
}
```

#### 4.2.2 创建 Slides 项目

```
POST /api/slides/{slug}
```

**Request Body:**
```json
{
  "title": "My New Slides"
}
```

**Response 201:**
```json
{
  "slug": "my-new-slides",
  "title": "My New Slides",
  "style": null,
  "slides": [],
  "total_cost": 0
}
```

**Response 409:**
```json
{
  "error": "conflict",
  "message": "Slides project already exists"
}
```

#### 4.2.3 更新 Slides 数据

```
PUT /api/slides/{slug}
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "slides": [
    {
      "sid": "slide-001",
      "content": "更新后的文字内容"
    },
    {
      "sid": "slide-002",
      "content": "第二张幻灯片"
    }
  ]
}
```

**Response 200:**
```json
{
  "slug": "hello-world",
  "title": "Updated Title",
  "style": {
    "prompt": "科技感、蓝色调、扁平风格",
    "image": "style.jpg"
  },
  "slides": [
    {
      "sid": "slide-001",
      "content": "更新后的文字内容",
      "created_at": "2026-01-27T10:00:00Z",
      "updated_at": "2026-01-28T15:30:00Z",
      "current_image_hash": "x1y2z3w4v5u6",
      "has_matching_image": false
    },
    {
      "sid": "slide-002",
      "content": "第二张幻灯片",
      "created_at": "2026-01-28T15:30:00Z",
      "updated_at": "2026-01-28T15:30:00Z",
      "current_image_hash": "m1n2o3p4q5r6",
      "has_matching_image": false
    }
  ],
  "total_cost": 0.15
}
```

#### 4.2.4 更新 Slides 顺序

```
PUT /api/slides/{slug}/reorder
```

**Request Body:**
```json
{
  "order": ["slide-002", "slide-001", "slide-003"]
}
```

**说明**: `order` 必须包含当前项目的所有 sid，且每个 sid 仅出现一次；否则返回 400。

**Response 200:**
```json
{
  "success": true,
  "order": ["slide-002", "slide-001", "slide-003"]
}
```

#### 4.2.5 添加新 Slide

```
POST /api/slides/{slug}/slides
```

**Request Body:**
```json
{
  "content": "新幻灯片的文字内容",
  "after_sid": "slide-001"
}
```

**说明**: `after_sid` 可选，表示在哪个 slide 后面插入。如果不提供，则添加到末尾。

**Response 201:**
```json
{
  "sid": "slide-003",
  "content": "新幻灯片的文字内容",
  "created_at": "2026-01-28T16:00:00Z",
  "updated_at": "2026-01-28T16:00:00Z",
  "current_image_hash": "h1i2j3k4l5m6",
  "has_matching_image": false
}
```

#### 4.2.6 删除 Slide

```
DELETE /api/slides/{slug}/slides/{sid}
```

**说明**: 删除 slide 同时删除对应图片目录及成本记录。

**Response 204:** No Content

---

### 4.3 图片接口

#### 4.3.1 为指定 Slide 生成图片

```
POST /api/slides/{slug}/generate/{sid}
```

**Request Body:** 无（使用当前 slide 的 content 生成）

**Response 200:**
```json
{
  "sid": "slide-001",
  "hash": "a1b2c3d4e5f6",
  "image_url": "/api/slides/hello-world/images/slide-001/a1b2c3d4e5f6.jpg",
  "cost": 0.05
}
```

**Response 202:** (生成中，异步处理)
```json
{
  "sid": "slide-001",
  "status": "generating",
  "message": "Image generation in progress"
}
```

**说明**: 客户端可轮询 `GET /api/slides/{slug}/images/{sid}` 获取最新图片列表。

#### 4.3.2 获取 Slide 的所有图片列表

```
GET /api/slides/{slug}/images/{sid}
```

**Response 200:**
```json
{
  "sid": "slide-001",
  "images": [
    {
      "hash": "a1b2c3d4e5f6",
      "url": "/api/slides/hello-world/images/slide-001/a1b2c3d4e5f6.jpg",
      "is_current": true,
      "created_at": "2026-01-27T10:30:00Z"
    },
    {
      "hash": "old123hash456",
      "url": "/api/slides/hello-world/images/slide-001/old123hash456.jpg",
      "is_current": false,
      "created_at": "2026-01-27T09:00:00Z"
    }
  ]
}
```

#### 4.3.3 获取指定图片

```
GET /api/slides/{slug}/images/{sid}/{hash}.jpg
```

**Response 200:** 返回 JPEG 图片二进制数据

**Headers:**
```
Content-Type: image/jpeg
Cache-Control: public, max-age=31536000
```

**Response 404:**
```json
{
  "error": "not_found",
  "message": "Image not found"
}
```

---

### 4.4 风格接口

#### 4.4.1 生成风格候选图

```
POST /api/slides/{slug}/style/generate
```

**Request Body:**
```json
{
  "prompt": "科技感、蓝色调、扁平风格"
}
```

**Response 200:**
```json
{
  "candidates": [
    {
      "id": "candidate-1",
      "url": "/api/slides/hello-world/style/candidate-1.jpg"
    },
    {
      "id": "candidate-2",
      "url": "/api/slides/hello-world/style/candidate-2.jpg"
    }
  ],
  "cost": 0.10
}
```

#### 4.4.2 选择风格图片

```
POST /api/slides/{slug}/style/select
```

**Request Body:**
```json
{
  "candidate_id": "candidate-1",
  "prompt": "科技感、蓝色调、扁平风格"
}
```

**Response 200:**
```json
{
  "style": {
    "prompt": "科技感、蓝色调、扁平风格",
    "image": "style.jpg"
  },
  "image_url": "/api/slides/hello-world/style.jpg"
}
```

#### 4.4.3 获取当前风格图片

```
GET /api/slides/{slug}/style
```

**Response 200:** 返回 JPEG 图片二进制数据（如果存在）

**Response 404:**
```json
{
  "error": "not_found",
  "message": "Style image not configured"
}
```

---

### 4.5 成本接口

#### 4.5.1 获取总成本

```
GET /api/slides/{slug}/cost
```

**Response 200:**
```json
{
  "total_cost": 0.35,
  "currency": "CNY",
  "breakdown": {
    "style_generation": 0.10,
    "slide_image": 0.25
  }
}
```

---

## 5. 数据模型

### 5.1 outline.yml Schema

```yaml
# outline.yml 完整结构
title: string                    # Slides 标题
style:                           # 风格配置（可选，首次打开时为空）
  prompt: string                 # 用户输入的风格描述
  image: string                  # 风格图片文件名（相对路径）
slides:                          # Slide 列表
  - sid: string                  # Slide 唯一 ID (格式: slide-XXX)
    content: string              # Slide 文字内容
    created_at: datetime         # 创建时间 (ISO 8601)
    updated_at: datetime         # 更新时间 (ISO 8601)
# current_image_hash / has_matching_image 由服务端根据图片目录计算，不存储在 outline.yml
cost:                            # 成本记录（可选）
  total: number                  # 总成本
  records:                       # 成本明细
    - type: string               # 类型: style_generation | slide_image
      amount: number             # 金额
      timestamp: datetime        # 时间
```

### 5.2 TypeScript 类型定义

```typescript
// frontend/src/types/slide.ts

export interface Style {
  prompt: string;
  image: string;
}

export interface Slide {
  sid: string;
  content: string;
  created_at: string;
  updated_at: string;
  // 由 content 计算的哈希，用于匹配图片是否已生成
  current_image_hash: string;
  has_matching_image: boolean;
}

export interface SlideImage {
  hash: string;
  url: string;
  is_current: boolean;
  created_at: string;
}

export interface SlidesProject {
  slug: string;
  title: string;
  style: Style | null;
  slides: Slide[];
  total_cost: number;
}

export interface StyleCandidate {
  id: string;
  url: string;
}
```

### 5.3 Python Pydantic 模型

```python
# backend/app/models/slide.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Style(BaseModel):
    prompt: str
    image: str

class SlideBase(BaseModel):
    sid: str
    content: str

class Slide(SlideBase):
    created_at: datetime
    updated_at: datetime
    # 由 content 计算的哈希，用于匹配图片是否已生成
    current_image_hash: str
    has_matching_image: bool

class SlidesProject(BaseModel):
    slug: str
    title: str
    style: Optional[Style] = None
    slides: List[Slide]
    total_cost: float = 0.0

class SlideImage(BaseModel):
    hash: str
    url: str
    is_current: bool
    created_at: datetime
```

---

## 6. 前端组件设计

### 6.1 页面布局

```
┌────────────────────────────────────────────────────────────────┐
│  Header                                                         │
│  ┌──────┐  ┌─────────────────────────────┐  ┌────────────────┐ │
│  │ Logo │  │      Slides 标题 (可编辑)     │  │    播放按钮    │ │
│  └──────┘  └─────────────────────────────┘  └────────────────┘ │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌─────────────────────────────────────────┐ │
│  │   Sidebar    │  │              MainContent                 │ │
│  │              │  │                                          │ │
│  │  ┌────────┐  │  │  ┌─────────────────────────────────┐   │ │
│  │  │Slide 1 │  │  │  │                                 │   │ │
│  │  └────────┘  │  │  │                                 │   │ │
│  │  ┌────────┐  │  │  │         SlidePreview            │   │ │
│  │  │Slide 2 │◄─┼──┼──│         (主图片预览)             │   │ │
│  │  └────────┘  │  │  │                                 │   │ │
│  │  ┌────────┐  │  │  │            ▶ 播放               │   │ │
│  │  │Slide 3 │  │  │  │                                 │   │ │
│  │  └────────┘  │  │  └─────────────────────────────────┘   │ │
│  │      ⋮       │  │                                          │ │
│  │              │  │  ┌─────────────────────────────────┐   │ │
│  │  (可拖拽排序) │  │  │    [ 生成图片 ] (条件显示)        │   │ │
│  │              │  │  └─────────────────────────────────┘   │ │
│  │              │  │                                          │ │
│  │              │  │  ┌─────────────────────────────────┐   │ │
│  │              │  │  │ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐  │   │ │
│  │              │  │  │ │ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 │  │   │ │
│  │              │  │  │ └───┘ └───┘ └───┘ └───┘ └───┘  │   │ │
│  │              │  │  │        Thumbnails (缩略图)       │   │ │
│  │              │  │  └─────────────────────────────────┘   │ │
│  └──────────────┘  └─────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 组件状态管理

```typescript
// frontend/src/stores/slideStore.ts

import { create } from 'zustand';
import { SlidesProject, Slide } from '../types/slide';

interface SlideState {
  // 数据
  project: SlidesProject | null;
  selectedSlideId: string | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setProject: (project: SlidesProject) => void;
  selectSlide: (sid: string) => void;
  updateSlide: (sid: string, content: string) => void;
  reorderSlides: (order: string[]) => void;
  addSlide: (content: string, afterSid?: string) => void;
  deleteSlide: (sid: string) => void;
}

// frontend/src/stores/previewStore.ts

interface PreviewState {
  // 当前预览的图片
  currentImageHash: string | null;
  images: SlideImage[];
  isGenerating: boolean;
  
  // Actions
  setCurrentImage: (hash: string) => void;
  setImages: (images: SlideImage[]) => void;
  setGenerating: (status: boolean) => void;
}

// frontend/src/stores/uiStore.ts

interface UIState {
  // Modal 状态
  isStyleSelectorOpen: boolean;
  isCarouselOpen: boolean;
  
  // Toast
  toast: { message: string; type: 'success' | 'error' } | null;
  
  // Actions
  openStyleSelector: () => void;
  closeStyleSelector: () => void;
  openCarousel: () => void;
  closeCarousel: () => void;
  showToast: (message: string, type: 'success' | 'error') => void;
}
```

### 6.3 关键组件接口

#### SlideList 组件

```typescript
// frontend/src/components/slides/SlideList.tsx

interface SlideListProps {
  slides: Slide[];
  selectedId: string | null;
  onSelect: (sid: string) => void;
  onDoubleClick: (sid: string) => void;
  onReorder: (order: string[]) => void;
  onInsert: (afterSid: string) => void;
}
```

#### SlidePreview 组件

```typescript
// frontend/src/components/preview/SlidePreview.tsx

interface SlidePreviewProps {
  slide: Slide | null;
  currentImage: string | null;  // 图片 URL
  onPlayClick: () => void;
}
```

#### StyleSelector 组件

```typescript
// frontend/src/components/style/StyleSelector.tsx

interface StyleSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (candidateId: string, prompt: string) => void;
}
```

#### Carousel 组件

```typescript
// frontend/src/components/carousel/Carousel.tsx

interface CarouselProps {
  slides: Slide[];
  startIndex: number;
  getImageUrl: (slide: Slide) => string;
  onClose: () => void;
}
```

---

### 6.4 Tailwind v4 全局样式配置

```css
/* frontend/src/styles/globals.css */
@import "tailwindcss";

@theme {
  --font-sans: "Inter", system-ui, sans-serif;
}
```

## 7. 火山方舟 API 集成

### 7.1 客户端封装

```python
# backend/app/clients/ark_client.py

import httpx
from typing import Optional
import base64

class ArkClient:
    def __init__(self, api_key: str, endpoint: str, model_id: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model_id = model_id
        self.client = httpx.AsyncClient(
            base_url=endpoint,
            headers={"Authorization": f"Bearer {api_key}"}
        )
    
    async def generate_image(
        self,
        prompt: str,
        reference_image: Optional[bytes] = None,
        size: str = "1024x1024"
    ) -> tuple[bytes, float]:
        """
        生成图片
        
        Args:
            prompt: 文字描述
            reference_image: 参考图片（风格参考）
            size: 图片尺寸
            
        Returns:
            (图片二进制数据, 成本)
        """
        payload = {
            "model": self.model_id,
            "prompt": prompt,
            "size": size,
            "response_format": "b64_json"
        }
        
        if reference_image:
            payload["image"] = base64.b64encode(reference_image).decode()
        
        response = await self.client.post(
            "/images/generations",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        image_b64 = data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(image_b64)
        
        # 成本计算（根据火山方舟定价）
        cost = 0.05  # 示例成本
        
        return image_bytes, cost
```

### 7.2 图片生成服务

```python
# backend/app/services/image_service.py

from app.clients.ark_client import ArkClient
from app.repositories.image_repository import ImageRepository
from app.repositories.slide_repository import SlideRepository
from app.utils.hash import compute_blake3_hash

class ImageService:
    def __init__(
        self,
        ark_client: ArkClient,
        image_repo: ImageRepository,
        slide_repo: SlideRepository
    ):
        self.ark_client = ark_client
        self.image_repo = image_repo
        self.slide_repo = slide_repo
    
    async def generate_slide_image(
        self,
        slug: str,
        sid: str
    ) -> dict:
        """为指定 slide 生成图片"""
        # 1. 获取 slide 内容
        slide = await self.slide_repo.get_slide(slug, sid)
        content = slide.content
        
        # 2. 计算内容 hash
        content_hash = compute_blake3_hash(content)
        
        # 3. 获取风格参考图
        style_image = await self.image_repo.get_style_image(slug)
        
        # 4. 调用 AI 生成图片
        image_bytes, cost = await self.ark_client.generate_image(
            prompt=content,
            reference_image=style_image
        )
        
        # 5. 保存图片
        image_path = await self.image_repo.save_slide_image(
            slug, sid, content_hash, image_bytes
        )
        
        # 6. 记录成本
        await self.slide_repo.add_cost_record(
            slug, "slide_image", cost
        )
        
        return {
            "sid": sid,
            "hash": content_hash,
            "image_url": f"/api/slides/{slug}/images/{sid}/{content_hash}.jpg",
            "cost": cost
        }
```

---

## 8. 文件存储规范

### 8.1 Blake3 哈希计算

```python
# backend/app/utils/hash.py

import blake3

def compute_blake3_hash(content: str) -> str:
    """
    计算字符串的 blake3 哈希值
    返回 16 字符的十六进制字符串
    """
    hasher = blake3.blake3(content.encode('utf-8'))
    return hasher.hexdigest()[:16]
```

```typescript
// frontend/src/utils/hash.ts

import { blake3 } from '@noble/hashes/blake3.js';
import { bytesToHex } from '@noble/hashes/utils.js';

export function computeBlake3Hash(content: string): string {
  const hash = blake3(new TextEncoder().encode(content));
  return bytesToHex(hash).slice(0, 16);
}
```

### 8.2 图片存储路径

```
slides/
└── {slug}/
    ├── outline.yml
    ├── style.jpg                    # 风格参考图 (1024x1024)
    └── images/
        └── {sid}/
            ├── {hash1}.jpg          # 内容 hash 对应的图片
            ├── {hash2}.jpg          # 历史版本
            └── {hash3}.jpg
```

---

## 9. 错误处理规范

### 9.1 HTTP 状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | 请求成功 |
| 201 | Created | 创建成功 |
| 202 | Accepted | 异步任务已接受 |
| 204 | No Content | 删除成功 |
| 400 | Bad Request | 请求参数错误 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 500 | Internal Error | 服务器内部错误 |
| 503 | Service Unavailable | 外部服务不可用 |

### 9.2 错误响应格式

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "details": {
    "field": "具体错误信息"
  }
}
```

---

## 10. 环境变量配置

```bash
# backend/.env.example

# 火山方舟配置
ARK_API_KEY=your_api_key_here
ARK_API_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL_ID=doubao-seed-1-8-251228

# 服务配置
HOST=0.0.0.0
PORT=8000

# 存储路径
SLIDES_BASE_PATH=./slides

# 开发模式
DEBUG=true
```

---

## 11. 依赖清单

### 11.1 后端依赖 (requirements.txt)

```
fastapi==0.128.0
uvicorn[standard]==0.40.0
pydantic==2.12.5
pydantic-settings==2.12.0
httpx==0.28.1
pyyaml==6.0.3
blake3==1.0.8
python-multipart==0.0.22
```

> **注意**: uvicorn 0.40.0 和 pydantic-settings 2.12.0 要求 Python ≥3.10

### 11.2 前端依赖 (package.json)

```json
{
  "dependencies": {
    "react": "^19.2.4",
    "react-dom": "^19.2.4",
    "react-router-dom": "^7.13.0",
    "zustand": "^5.0.10",
    "axios": "^1.13.4",
    "@dnd-kit/core": "^6.3.1",
    "@dnd-kit/sortable": "^10.0.0",
    "@noble/hashes": "^2.0.1"
  },
  "devDependencies": {
    "typescript": "^5.9.3",
    "vite": "^7.3.0",
    "@vitejs/plugin-react": "^5.1.2",
    "tailwindcss": "^4.1.0",
    "@types/react": "^19.2.10",
    "@types/react-dom": "^19.2.3"
  }
}
```

> **重要升级说明**:
> - **React 19**: 包含 Server Components、Actions 等新特性
> - **Tailwind CSS v4**: 采用 CSS-first 配置，不再需要 `tailwind.config.js` 和 `postcss.config.js`，改用 CSS 文件中的 `@import "tailwindcss"` 和 `@theme` 指令
> - **@noble/hashes v2**: 导入路径需添加 `.js` 扩展名（如 `@noble/hashes/blake3.js`）
> - **react-router-dom v7**: API 有变化，需要 Node 20+
> - **Vite 7**: 支持更多现代特性，需要 Node 20+

---

## 12. 开发与运行

### 12.0 环境要求

- Python >= 3.10（uvicorn 0.40.0 与 pydantic-settings 2.12.0 要求）
- Node.js >= 20（Vite 7 与 react-router-dom v7 要求）

### 12.1 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 ARK_API_KEY
uvicorn app.main:app --reload --port 8000
```

### 12.2 前端启动

```bash
cd frontend
npm install
npm run dev -- --port 3003
```

### 12.3 访问

- 前端: `http://localhost:3003/{slug}`
- 后端 API: `http://localhost:8000/api`
- API 文档: `http://localhost:8000/docs`

