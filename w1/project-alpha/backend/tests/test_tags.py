import os

import pytest
from httpx import AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_tables():
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ========== Tag CRUD Tests ==========


@pytest.mark.asyncio
async def test_create_and_list_tags(client: AsyncClient):
    """测试创建和列出标签"""
    # 创建标签
    resp = await client.post("/tags", json={"name": "python"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "python"
    assert "id" in data
    assert "created_at" in data

    # 列出所有标签
    list_resp = await client.get("/tags")
    assert list_resp.status_code == 200
    tags = list_resp.json()
    assert len(tags) == 1
    assert tags[0]["name"] == "python"


@pytest.mark.asyncio
async def test_create_tag_idempotent(client: AsyncClient):
    """测试标签创建的幂等性（同名标签只创建一个）"""
    # 创建同名标签（大小写不同）
    resp1 = await client.post("/tags", json={"name": "Python"})
    assert resp1.status_code == 201
    tag_id1 = resp1.json()["id"]

    resp2 = await client.post("/tags", json={"name": "python"})
    assert resp2.status_code == 201
    tag_id2 = resp2.json()["id"]

    # 应该返回同一个标签
    assert tag_id1 == tag_id2

    # 列表中应该只有一个标签
    list_resp = await client.get("/tags")
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_create_tag_validation(client: AsyncClient):
    """测试标签创建时的验证"""
    # 空名称
    resp = await client.post("/tags", json={"name": ""})
    assert resp.status_code == 422

    # 名称过长
    resp = await client.post("/tags", json={"name": "x" * 51})
    assert resp.status_code == 422

    # 缺少名称
    resp = await client.post("/tags", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_tag_name_normalization(client: AsyncClient):
    """测试标签名称规范化（去除空格、转小写）"""
    resp = await client.post("/tags", json={"name": "  Python  "})
    assert resp.status_code == 201
    assert resp.json()["name"] == "python"


@pytest.mark.asyncio
async def test_filter_tags_by_query(client: AsyncClient):
    """测试按查询字符串筛选标签"""
    await client.post("/tags", json={"name": "python"})
    await client.post("/tags", json={"name": "javascript"})
    await client.post("/tags", json={"name": "python-advanced"})

    # 搜索 "python"
    resp = await client.get("/tags", params={"q": "python"})
    assert resp.status_code == 200
    tags = resp.json()
    assert len(tags) == 2
    assert all("python" in tag["name"] for tag in tags)


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient):
    """测试删除标签"""
    resp = await client.post("/tags", json={"name": "to-delete"})
    tag_id = resp.json()["id"]

    delete_resp = await client.delete(f"/tags/{tag_id}")
    assert delete_resp.status_code == 204

    # 验证标签已删除
    list_resp = await client.get("/tags")
    tags = list_resp.json()
    assert len(tags) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_tag(client: AsyncClient):
    """测试删除不存在的标签"""
    resp = await client.delete("/tags/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_tag_with_tickets(client: AsyncClient):
    """测试删除有关联 ticket 的标签"""
    # 创建标签和 ticket
    tag_resp = await client.post("/tags", json={"name": "test-tag"})
    tag_id = tag_resp.json()["id"]

    ticket_resp = await client.post(
        "/tickets", json={"title": "Test", "tags": ["test-tag"]}
    )
    ticket_id = ticket_resp.json()["id"]

    # 删除标签应该成功（级联删除关联）
    delete_resp = await client.delete(f"/tags/{tag_id}")
    assert delete_resp.status_code == 204

    # 验证 ticket 仍然存在，但标签已移除
    ticket_resp = await client.get(f"/tickets/{ticket_id}")
    assert ticket_resp.status_code == 200
    assert len(ticket_resp.json()["tags"]) == 0


@pytest.mark.asyncio
async def test_list_tags_empty(client: AsyncClient):
    """测试空标签列表"""
    resp = await client.get("/tags")
    assert resp.status_code == 200
    assert resp.json() == []
