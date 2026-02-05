# Doubao Seedream - Python 实现指南

## 安装依赖

### 方式1: 使用 httpx (推荐，轻量)
```bash
pip install httpx
# 或
uv add httpx
```

### 方式2: 使用官方 SDK
```bash
pip install 'volcengine-python-sdk[ark]>=5.0'
```

---

## 最小可用代码

### 文生图 (Text-to-Image)

```python
import asyncio
import httpx
import base64
import os

async def text_to_image(prompt: str, size: str = "1920x1920") -> bytes:
    """从文本生成图像"""
    response = await httpx.AsyncClient(timeout=120).post(
        "https://ark.cn-beijing.volces.com/api/v3/images/generations",
        headers={
            "Authorization": f"Bearer {os.getenv('ARK_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "doubao-seedream-4-5-251128",
            "prompt": prompt,
            "size": size,
            "response_format": "b64_json"
        }
    )
    return base64.b64decode(response.json()["data"][0]["b64_json"])

# 使用示例
async def main():
    image = await text_to_image("一只可爱的猫咪，专业摄影，高清")
    with open("output.jpg", "wb") as f:
        f.write(image)

asyncio.run(main())
```

### 图生图 (Image-to-Image)

```python
async def image_to_image(
    prompt: str,
    reference_base64: str,
    size: str = "1920x1920"
) -> bytes:
    """使用参考图像生成风格一致的新图像"""
    response = await httpx.AsyncClient(timeout=120).post(
        "https://ark.cn-beijing.volces.com/api/v3/images/generations",
        headers={
            "Authorization": f"Bearer {os.getenv('ARK_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "doubao-seedream-4-5-251128",
            "prompt": prompt,
            "image": f"data:image/jpeg;base64,{reference_base64}",
            "size": size,
            "response_format": "b64_json"
        }
    )
    return base64.b64decode(response.json()["data"][0]["b64_json"])

# 使用示例
async def main():
    # 读取参考图像
    with open("style_reference.jpg", "rb") as f:
        ref_base64 = base64.b64encode(f.read()).decode()

    image = await image_to_image("现代城市建筑", ref_base64)
    with open("output.jpg", "wb") as f:
        f.write(image)
```

---

## 完整封装类

```python
"""
doubao_image.py - Doubao Seedream 图像生成器
可直接复制到新项目使用
"""

import asyncio
import httpx
import base64
import os
from pathlib import Path
from typing import Optional, List


class DoubaoImage:
    """Doubao Seedream 图像生成器"""

    ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    MODEL = "doubao-seedream-4-5-251128"

    def __init__(self, api_key: str = None, timeout: float = 120.0):
        """
        初始化生成器

        Args:
            api_key: API密钥，默认从 ARK_API_KEY 环境变量读取
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key or os.getenv("ARK_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 ARK_API_KEY 环境变量或传入 api_key")
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        size: str = "1920x1920",
        reference_image: str = None,
        n: int = 1
    ) -> List[bytes]:
        """
        生成图像

        Args:
            prompt: 图像描述文本
            size: 图像尺寸 (如 "1920x1920", "1920x1080")
            reference_image: 参考图像的 base64 编码 (可选，用于图生图)
            n: 生成数量 (1-4)

        Returns:
            生成的图像字节列表
        """
        payload = {
            "model": self.MODEL,
            "prompt": prompt,
            "size": size,
            "n": min(max(n, 1), 4),
            "response_format": "b64_json"
        }

        # 添加参考图像 (图生图模式)
        if reference_image:
            if not reference_image.startswith("data:"):
                payload["image"] = f"data:image/jpeg;base64,{reference_image}"
            else:
                payload["image"] = reference_image

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.ENDPOINT,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code != 200:
                raise Exception(f"API错误 ({response.status_code}): {response.text}")

            data = response.json()

            if "error" in data:
                raise Exception(f"API错误: {data['error']}")

            return [
                base64.b64decode(item["b64_json"])
                for item in data["data"]
            ]

    async def text_to_image(
        self,
        prompt: str,
        size: str = "1920x1920"
    ) -> bytes:
        """
        文生图

        Args:
            prompt: 图像描述
            size: 图像尺寸

        Returns:
            图像字节数据
        """
        images = await self.generate(prompt, size)
        return images[0]

    async def image_to_image(
        self,
        prompt: str,
        reference_path: str,
        size: str = "1920x1920"
    ) -> bytes:
        """
        图生图 (风格迁移)

        Args:
            prompt: 图像描述
            reference_path: 参考图像文件路径
            size: 图像尺寸

        Returns:
            图像字节数据
        """
        with open(reference_path, "rb") as f:
            ref_base64 = base64.b64encode(f.read()).decode()
        images = await self.generate(prompt, size, ref_base64)
        return images[0]

    async def save(
        self,
        prompt: str,
        output_path: str,
        size: str = "1920x1920",
        reference_path: str = None
    ) -> str:
        """
        生成并保存图像

        Args:
            prompt: 图像描述
            output_path: 输出文件路径
            size: 图像尺寸
            reference_path: 参考图像路径 (可选)

        Returns:
            保存的文件路径
        """
        if reference_path:
            image = await self.image_to_image(prompt, reference_path, size)
        else:
            image = await self.text_to_image(prompt, size)

        Path(output_path).write_bytes(image)
        return output_path


# ============ 便捷函数 ============

async def generate_image(
    prompt: str,
    output: str = "output.jpg",
    size: str = "1920x1920",
    reference: str = None
) -> str:
    """
    一行代码生成图像

    Args:
        prompt: 图像描述
        output: 输出文件路径
        size: 图像尺寸
        reference: 参考图像路径 (可选)

    Returns:
        保存的文件路径
    """
    generator = DoubaoImage()
    return await generator.save(prompt, output, size, reference)


# ============ 使用示例 ============

if __name__ == "__main__":
    async def demo():
        gen = DoubaoImage()

        # 示例1: 文生图
        print("生成文生图...")
        image = await gen.text_to_image(
            prompt="一只可爱的橘猫在阳光下打盹，专业宠物摄影，浅景深，高清",
            size="1920x1920"
        )
        Path("cat.jpg").write_bytes(image)
        print(f"✓ 已保存: cat.jpg ({len(image):,} bytes)")

        # 示例2: 图生图 (风格迁移)
        print("\n生成图生图...")
        image = await gen.image_to_image(
            prompt="现代简约风格的办公室，明亮通透",
            reference_path="cat.jpg",  # 使用上一张图作为风格参考
            size="1920x1080"
        )
        Path("office.jpg").write_bytes(image)
        print(f"✓ 已保存: office.jpg ({len(image):,} bytes)")

        # 示例3: 批量生成
        print("\n批量生成...")
        images = await gen.generate(
            prompt="抽象艺术，流动的色彩，现代风格",
            size="1024x1024",
            n=2
        )
        for i, img in enumerate(images):
            Path(f"art_{i+1}.jpg").write_bytes(img)
            print(f"✓ 已保存: art_{i+1}.jpg")

    asyncio.run(demo())
```

---

## 同步版本 (非异步)

如果项目不使用异步，可以使用同步版本:

```python
import httpx
import base64
import os
from pathlib import Path


def generate_image_sync(
    prompt: str,
    output: str = "output.jpg",
    size: str = "1920x1920",
    reference_base64: str = None
) -> str:
    """同步版本的图像生成"""
    payload = {
        "model": "doubao-seedream-4-5-251128",
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json"
    }

    if reference_base64:
        payload["image"] = f"data:image/jpeg;base64,{reference_base64}"

    with httpx.Client(timeout=120) as client:
        response = client.post(
            "https://ark.cn-beijing.volces.com/api/v3/images/generations",
            headers={
                "Authorization": f"Bearer {os.getenv('ARK_API_KEY')}",
                "Content-Type": "application/json"
            },
            json=payload
        )

    if response.status_code != 200:
        raise Exception(f"API错误: {response.text}")

    image_bytes = base64.b64decode(response.json()["data"][0]["b64_json"])
    Path(output).write_bytes(image_bytes)
    return output


# 使用
generate_image_sync("美丽的风景画", "landscape.jpg")
```

---

## 错误处理

```python
from typing import Optional

class ImageGenerationError(Exception):
    """图像生成错误"""
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def safe_generate(prompt: str) -> Optional[bytes]:
    """带错误处理的图像生成"""
    try:
        gen = DoubaoImage()
        return await gen.text_to_image(prompt)
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            raise ImageGenerationError("API Key 无效，请检查 ARK_API_KEY", 401)
        elif "429" in error_msg:
            raise ImageGenerationError("请求频率超限，请稍后重试", 429)
        elif "400" in error_msg:
            raise ImageGenerationError("参数错误，请检查 prompt 和 size", 400)
        else:
            raise ImageGenerationError(f"生成失败: {error_msg}")
```

---

## 内容缓存 (避免重复生成)

```python
import hashlib
from pathlib import Path


class CachedImageGenerator:
    """带缓存的图像生成器"""

    def __init__(self, cache_dir: str = ".image_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.generator = DoubaoImage()

    def _get_cache_key(self, prompt: str, size: str) -> str:
        """生成缓存键"""
        content = f"{prompt}:{size}"
        return hashlib.blake2b(content.encode(), digest_size=16).hexdigest()

    async def generate(
        self,
        prompt: str,
        size: str = "1920x1920",
        force: bool = False
    ) -> bytes:
        """
        生成图像 (带缓存)

        Args:
            prompt: 图像描述
            size: 图像尺寸
            force: 是否强制重新生成

        Returns:
            图像字节数据
        """
        cache_key = self._get_cache_key(prompt, size)
        cache_path = self.cache_dir / f"{cache_key}.jpg"

        # 检查缓存
        if not force and cache_path.exists():
            print(f"使用缓存: {cache_key}")
            return cache_path.read_bytes()

        # 生成新图像
        print(f"生成新图像: {cache_key}")
        image = await self.generator.text_to_image(prompt, size)
        cache_path.write_bytes(image)
        return image


# 使用
async def main():
    gen = CachedImageGenerator()

    # 第一次调用 - 生成新图像
    img1 = await gen.generate("可爱的猫咪")

    # 第二次调用相同内容 - 使用缓存
    img2 = await gen.generate("可爱的猫咪")

    # 强制重新生成
    img3 = await gen.generate("可爱的猫咪", force=True)
```

---

## 批量并行生成

```python
import asyncio


async def batch_generate(prompts: list[str], size: str = "1920x1920") -> list[bytes]:
    """并行生成多张图片"""
    gen = DoubaoImage()
    tasks = [gen.text_to_image(p, size) for p in prompts]
    return await asyncio.gather(*tasks)


# 使用
async def main():
    prompts = [
        "日出时分的山峰",
        "繁华的城市夜景",
        "宁静的湖边小屋",
    ]
    images = await batch_generate(prompts)

    for i, img in enumerate(images):
        Path(f"image_{i+1}.jpg").write_bytes(img)
```

---

## 项目参考实现

本项目 (`gen-slide`) 中的实现可作为参考:

| 文件 | 说明 |
|------|------|
| `backend/app/clients/ark_client.py` | API 客户端封装 |
| `backend/app/services/image_service.py` | 业务逻辑 + 缓存 |
| `backend/app/services/style_service.py` | 风格管理 |
| `backend/app/config.py` | 配置管理 |
