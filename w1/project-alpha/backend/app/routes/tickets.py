from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import TicketStatus
from ..schemas import TicketCreate, TicketResponse, TicketsListResponse, TicketUpdate
from ..services import tickets as ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [tag.strip().lower() for tag in raw.split(",") if tag.strip()]


def _parse_status(raw: str | None) -> TicketStatus | None:
    """解析并规范化状态查询参数，支持大小写不敏感

    支持的输入格式：
    - "open", "OPEN", "Open" -> TicketStatus.OPEN
    - "done", "DONE", "Done" -> TicketStatus.DONE
    - None -> None

    返回的枚举对象的值（.value）是小写的 "open" 或 "done"
    """
    if raw is None:
        return None

    # 确保输入是字符串
    if not isinstance(raw, str):
        raise ValueError(f"状态值必须是字符串，收到: {type(raw).__name__}")

    normalized = raw.strip().lower()
    if normalized == "open":
        return TicketStatus.OPEN  # TicketStatus.OPEN.value == "open"
    elif normalized == "done":
        return TicketStatus.DONE  # TicketStatus.DONE.value == "done"
    else:
        # 如果值无效，抛出 ValueError，FastAPI 会将其转换为 422 验证错误
        raise ValueError(f"状态值无效: {raw}，必须是 'open' 或 'done'（大小写不敏感）")


@router.get("", response_model=TicketsListResponse)
async def list_tickets(
    status: str | None = Query(default=None, description="open/done (大小写不敏感)"),
    tags: str | None = Query(default=None, description="逗号分隔的标签名（AND 过滤）"),
    q: str | None = Query(default=None, description="标题关键词"),
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> TicketsListResponse:
    # 规范化状态值
    try:
        normalized_status = _parse_status(status)
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=str(e))

    tag_list = _parse_tags(tags)
    items, total = await ticket_service.list_tickets(
        session,
        status=normalized_status,
        tags=tag_list,
        q=q,
        limit=limit,
        offset=offset,
    )
    return TicketsListResponse(
        total=total, items=[TicketResponse.model_validate(item) for item in items]
    )


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    payload: TicketCreate, session: AsyncSession = Depends(get_session)
) -> TicketResponse:
    ticket = await ticket_service.create_ticket(session, payload)

    # 在 session 关闭前完成 Pydantic 序列化
    # create_ticket 已经返回了完整的 ticket 对象，包括加载了 tags 关系
    response = TicketResponse.model_validate(ticket)
    return response


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str, session: AsyncSession = Depends(get_session)
) -> TicketResponse:
    ticket = await ticket_service.get_ticket(session, ticket_id)
    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    ticket = await ticket_service.get_ticket(session, ticket_id)
    ticket = await ticket_service.update_ticket(session, ticket, payload)
    return TicketResponse.model_validate(ticket)


@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(
    ticket_id: str, session: AsyncSession = Depends(get_session)
) -> None:
    ticket = await ticket_service.get_ticket(session, ticket_id)
    await ticket_service.delete_ticket(session, ticket)
