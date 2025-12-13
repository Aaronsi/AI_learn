import os

import pytest
from httpx import AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import TicketStatus  # noqa: E402


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


# ========== Ticket CRUD Tests ==========


@pytest.mark.asyncio
async def test_create_and_get_ticket(client: AsyncClient):
    """测试创建和获取 ticket"""
    create_payload = {
        "title": "My first ticket",
        "description": "Hello",
        "tags": ["alpha", "Beta"],
    }
    resp = await client.post("/tickets", json=create_payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "My first ticket"
    assert data["description"] == "Hello"
    assert data["status"] == TicketStatus.OPEN.value
    assert {t["name"] for t in data["tags"]} == {"alpha", "beta"}

    ticket_id = data["id"]
    get_resp = await client.get(f"/tickets/{ticket_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ticket_id


@pytest.mark.asyncio
async def test_create_ticket_minimal(client: AsyncClient):
    """测试创建最小 ticket（只有标题）"""
    resp = await client.post("/tickets", json={"title": "Minimal ticket"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Minimal ticket"
    assert data["description"] is None
    assert data["status"] == TicketStatus.OPEN.value
    assert data["tags"] == []


@pytest.mark.asyncio
async def test_create_ticket_validation_errors(client: AsyncClient):
    """测试创建 ticket 时的验证错误"""
    # 空标题
    resp = await client.post("/tickets", json={"title": ""})
    assert resp.status_code == 422

    # 标题过长
    resp = await client.post("/tickets", json={"title": "x" * 201})
    assert resp.status_code == 422

    # 缺少标题
    resp = await client.post("/tickets", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_nonexistent_ticket(client: AsyncClient):
    """测试获取不存在的 ticket"""
    resp = await client.get("/tickets/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert "error" in resp.json()


@pytest.mark.asyncio
async def test_update_ticket(client: AsyncClient):
    """测试更新 ticket"""
    resp = await client.post("/tickets", json={"title": "to update"})
    ticket_id = resp.json()["id"]

    # 更新状态和标签
    patch_resp = await client.patch(
        f"/tickets/{ticket_id}",
        json={"status": TicketStatus.DONE.value, "tags": ["done"]},
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["status"] == TicketStatus.DONE.value
    assert updated["tags"][0]["name"] == "done"

    # 更新标题和描述
    patch_resp = await client.patch(
        f"/tickets/{ticket_id}",
        json={"title": "Updated title", "description": "Updated description"},
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["title"] == "Updated title"
    assert updated["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_ticket_partial(client: AsyncClient):
    """测试部分更新 ticket"""
    resp = await client.post(
        "/tickets", json={"title": "Original", "description": "Original desc"}
    )
    ticket_id = resp.json()["id"]

    # 只更新标题
    patch_resp = await client.patch(
        f"/tickets/{ticket_id}", json={"title": "New title"}
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["title"] == "New title"
    assert updated["description"] == "Original desc"  # 保持不变


@pytest.mark.asyncio
async def test_update_ticket_status_normalization(client: AsyncClient):
    """测试状态值的大小写不敏感"""
    resp = await client.post("/tickets", json={"title": "Test"})
    ticket_id = resp.json()["id"]

    # 测试大写状态值
    patch_resp = await client.patch(f"/tickets/{ticket_id}", json={"status": "DONE"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == TicketStatus.DONE.value

    # 测试混合大小写
    patch_resp = await client.patch(f"/tickets/{ticket_id}", json={"status": "Open"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == TicketStatus.OPEN.value


@pytest.mark.asyncio
async def test_delete_ticket(client: AsyncClient):
    """测试删除 ticket"""
    resp = await client.post("/tickets", json={"title": "to delete"})
    ticket_id = resp.json()["id"]

    delete_resp = await client.delete(f"/tickets/{ticket_id}")
    assert delete_resp.status_code == 204

    fetch_resp = await client.get(f"/tickets/{ticket_id}")
    assert fetch_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_ticket(client: AsyncClient):
    """测试删除不存在的 ticket"""
    resp = await client.delete("/tickets/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ========== Ticket Filtering Tests ==========


@pytest.mark.asyncio
async def test_filter_by_status(client: AsyncClient):
    """测试按状态筛选"""
    # 创建两个 ticket，一个 open，一个 done
    await client.post("/tickets", json={"title": "Open ticket"})
    resp2 = await client.post("/tickets", json={"title": "Done ticket"})
    ticket_id = resp2.json()["id"]
    await client.patch(
        f"/tickets/{ticket_id}", json={"status": TicketStatus.DONE.value}
    )

    # 筛选 open
    res = await client.get("/tickets", params={"status": "open"})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Open ticket"

    # 筛选 done
    res = await client.get("/tickets", params={"status": "done"})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Done ticket"

    # 测试大小写不敏感
    res = await client.get("/tickets", params={"status": "OPEN"})
    assert res.status_code == 200
    assert res.json()["total"] == 1


@pytest.mark.asyncio
async def test_filter_by_tags_and(client: AsyncClient):
    """测试按标签 AND 筛选"""
    await client.post("/tickets", json={"title": "A", "tags": ["x", "y"]})
    await client.post("/tickets", json={"title": "B", "tags": ["y", "z"]})
    await client.post("/tickets", json={"title": "C", "tags": ["x"]})

    # 筛选同时有 x 和 y 的
    res = await client.get("/tickets", params={"tags": "x,y"})
    assert res.status_code == 200
    payload = res.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "A"

    # 筛选只有 y 的
    res = await client.get("/tickets", params={"tags": "y"})
    assert res.status_code == 200
    assert res.json()["total"] == 2  # A 和 B


@pytest.mark.asyncio
async def test_filter_by_search_query(client: AsyncClient):
    """测试按标题搜索"""
    await client.post("/tickets", json={"title": "Python tutorial"})
    await client.post("/tickets", json={"title": "JavaScript guide"})
    await client.post("/tickets", json={"title": "Python advanced"})

    # 搜索 "python"
    res = await client.get("/tickets", params={"q": "python"})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert all("python" in item["title"].lower() for item in data["items"])


@pytest.mark.asyncio
async def test_filter_combined(client: AsyncClient):
    """测试组合筛选"""
    # 创建多个 ticket
    """
    resp1 = await client.post(
        "/tickets", json={"title": "Open Python", "tags": ["python", "tutorial"]}
    )
    """
    resp2 = await client.post(
        "/tickets", json={"title": "Done Python", "tags": ["python"]}
    )
    """
    resp3 = await client.post(
        "/tickets", json={"title": "Open JS", "tags": ["javascript"]}
    )
    """

    # 将第二个设为 done
    await client.patch(
        f"/tickets/{resp2.json()['id']}", json={"status": TicketStatus.DONE.value}
    )

    # 组合筛选：open + python + tutorial
    res = await client.get(
        "/tickets", params={"status": "open", "tags": "python,tutorial", "q": "python"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Open Python"


# ========== Pagination Tests ==========


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient):
    """测试分页"""
    # 创建 25 个 ticket
    for i in range(25):
        await client.post("/tickets", json={"title": f"Ticket {i}"})

    # 第一页（默认 limit=20）
    res = await client.get("/tickets", params={"limit": 20, "offset": 0})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 25
    assert len(data["items"]) == 20

    # 第二页
    res = await client.get("/tickets", params={"limit": 20, "offset": 20})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 25
    assert len(data["items"]) == 5

    # 测试 limit 限制
    res = await client.get("/tickets", params={"limit": 101})  # 超过最大限制
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_pagination_edge_cases(client: AsyncClient):
    """测试分页边界情况"""
    # 空结果
    res = await client.get("/tickets", params={"limit": 10, "offset": 0})
    assert res.status_code == 200
    assert res.json()["total"] == 0
    assert res.json()["items"] == []

    # offset 超出范围
    await client.post("/tickets", json={"title": "One ticket"})
    res = await client.get("/tickets", params={"limit": 10, "offset": 100})
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert len(res.json()["items"]) == 0


# ========== Error Format Tests ==========


@pytest.mark.asyncio
async def test_error_format(client: AsyncClient):
    """测试统一错误格式"""
    # 404 错误
    resp = await client.get("/tickets/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    error_data = resp.json()
    assert "error" in error_data
    assert "code" in error_data["error"]
    assert "message" in error_data["error"]

    # 422 验证错误
    resp = await client.post("/tickets", json={"title": ""})
    assert resp.status_code == 422
    error_data = resp.json()
    assert "error" in error_data or "detail" in error_data  # FastAPI 可能返回 detail


@pytest.mark.asyncio
async def test_invalid_status_value(client: AsyncClient):
    """测试无效的状态值"""
    resp = await client.get("/tickets", params={"status": "invalid"})
    assert resp.status_code == 422
