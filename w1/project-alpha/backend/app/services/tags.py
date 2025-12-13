from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import AppError
from ..models import Tag
from ..schemas import TagCreate


async def list_tags(session: AsyncSession, q: str | None = None) -> List[Tag]:
    query = select(Tag)
    if q:
        query = query.where(func.lower(Tag.name).like(f"%{q.lower()}%"))
    rows = await session.execute(query.order_by(Tag.name.asc()))
    return list(rows.scalars().all())


async def create_tag(session: AsyncSession, payload: TagCreate) -> Tag:
    normalized = payload.name.strip().lower()
    existing = await session.execute(
        select(Tag).where(func.lower(Tag.name) == normalized)
    )
    tag = existing.scalar_one_or_none()
    if tag:
        return tag
    tag = Tag(name=normalized)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


async def delete_tag(session: AsyncSession, tag_id: str) -> None:
    tag = await session.get(Tag, tag_id)
    if not tag:
        raise AppError(status_code=404, code="not_found", message="标签不存在")
    await session.delete(tag)
    await session.commit()
