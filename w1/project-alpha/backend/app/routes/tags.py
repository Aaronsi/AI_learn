from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..schemas import TagCreate, TagResponse
from ..services import tags as tag_service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
async def list_tags(
    q: str | None = Query(default=None, description="按名称模糊过滤"),
    session: AsyncSession = Depends(get_session),
) -> list[TagResponse]:
    tags = await tag_service.list_tags(session, q)
    return [TagResponse.model_validate(tag) for tag in tags]


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(
    payload: TagCreate, session: AsyncSession = Depends(get_session)
) -> TagResponse:
    tag = await tag_service.create_tag(session, payload)
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: str, session: AsyncSession = Depends(get_session)) -> None:
    await tag_service.delete_tag(session, tag_id)
