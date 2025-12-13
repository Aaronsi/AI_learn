from typing import Iterable, List, Tuple
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..errors import AppError
from ..models import Tag, Ticket, TicketStatus, ticket_tags
from ..schemas import TicketCreate, TicketUpdate


async def get_ticket(session: AsyncSession, ticket_id: str | UUID) -> Ticket:
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id).options(selectinload(Ticket.tags))
    )
    ticket = result.scalars().first()
    if not ticket:
        raise AppError(status_code=404, code="not_found", message="Ticket 不存在")
    return ticket


async def list_tickets(
    session: AsyncSession,
    *,
    status: TicketStatus | None,
    tags: List[str],
    q: str | None,
    limit: int,
    offset: int,
) -> Tuple[List[Ticket], int]:
    base_query: Select[tuple[Ticket]] = select(Ticket).options(
        selectinload(Ticket.tags)
    )

    if status:
        base_query = base_query.where(Ticket.status == status)

    if q:
        keyword = f"%{q.lower()}%"
        base_query = base_query.where(func.lower(Ticket.title).like(keyword))

    if tags:
        normalized_tags = [tag.lower() for tag in tags]
        tag_subquery = (
            select(ticket_tags.c.ticket_id)
            .join(Tag, Tag.id == ticket_tags.c.tag_id)
            .where(func.lower(Tag.name).in_(normalized_tags))
            .group_by(ticket_tags.c.ticket_id)
            .having(
                func.count(func.distinct(ticket_tags.c.tag_id)) == len(normalized_tags)
            )
            .subquery()
        )
        base_query = base_query.where(Ticket.id.in_(select(tag_subquery.c.ticket_id)))

    total = await session.scalar(
        select(func.count()).select_from(base_query.subquery())
    )
    rows = await session.execute(
        base_query.order_by(Ticket.created_at.desc()).limit(limit).offset(offset)
    )
    return list(rows.scalars().all()), int(total or 0)


async def _upsert_tags(session: AsyncSession, tag_names: Iterable[str]) -> List[Tag]:
    normalized = [tag.strip().lower() for tag in tag_names if tag.strip()]
    if not normalized:
        return []

    existing = await session.execute(
        select(Tag).where(func.lower(Tag.name).in_(normalized))
    )
    existing_tags = list(existing.scalars().all())

    existing_names = {tag.name.lower(): tag for tag in existing_tags}
    new_tags = []
    for name in normalized:
        if name in existing_names:
            continue
        new_tag = Tag(name=name)
        session.add(new_tag)
        new_tags.append(new_tag)

    if new_tags:
        try:
            await session.flush()
        except IntegrityError as exc:
            raise AppError(
                status_code=400,
                code="tag_conflict",
                message="标签创建失败",
                details={"error": str(exc)},
            )

    return existing_tags + new_tags


async def _sync_ticket_tags(
    session: AsyncSession, ticket: Ticket, tag_names: Iterable[str]
) -> None:
    tags = await _upsert_tags(session, tag_names)

    # 先清除现有的关联关系
    await session.execute(
        ticket_tags.delete().where(ticket_tags.c.ticket_id == ticket.id)
    )

    # 如果有新标签，添加新的关联关系
    if tags:
        for tag in tags:
            await session.execute(
                ticket_tags.insert().values(ticket_id=ticket.id, tag_id=tag.id)
            )

    await session.flush()


async def create_ticket(session: AsyncSession, payload: TicketCreate) -> Ticket:
    ticket = Ticket(
        title=payload.title, description=payload.description, status=TicketStatus.OPEN
    )
    session.add(ticket)
    await session.flush()  # 先 flush 获取 ticket.id

    # 同步标签关系
    await _sync_ticket_tags(session, ticket, payload.tags)

    await session.commit()

    # 使用重新查询的方式获取完整的 ticket 对象，包括加载 tags 关系
    # 这种方式比 refresh 更可靠，可以避免 MissingGreenlet 错误
    return await get_ticket(session, ticket.id)


async def update_ticket(
    session: AsyncSession, ticket: Ticket, payload: TicketUpdate
) -> Ticket:
    if payload.title is not None:
        ticket.title = payload.title
    if payload.description is not None:
        ticket.description = payload.description
    if payload.status is not None:
        ticket.status = payload.status
    if payload.tags is not None:
        await _sync_ticket_tags(session, ticket, payload.tags)
    await session.commit()

    # 使用重新查询的方式获取完整的 ticket 对象，包括加载 tags 关系
    # 这种方式比 refresh 更可靠，可以避免 MissingGreenlet 错误
    return await get_ticket(session, ticket.id)


async def delete_ticket(session: AsyncSession, ticket: Ticket) -> None:
    await session.delete(ticket)
    await session.commit()
