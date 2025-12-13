import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from .models import TicketStatus


class ErrorModel(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorModel


class TagBase(BaseModel):
    name: str = Field(..., max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("标签名不能为空")
        if len(cleaned) > 50:
            raise ValueError("标签名长度需 <= 50")
        return cleaned.lower()


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("标题不能为空")
        if len(cleaned) > 200:
            raise ValueError("标题长度需 <= 200")
        return cleaned

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else value


class TicketCreate(TicketBase):
    tags: List[str] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: List[str]) -> List[str]:
        return [tag.strip().lower() for tag in value if tag.strip()]


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    tags: Optional[List[str]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("标题不能为空")
        if len(cleaned) > 200:
            raise ValueError("标题长度需 <= 200")
        return cleaned

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(
        cls, value: Optional[str | TicketStatus]
    ) -> Optional[TicketStatus]:
        if value is None:
            return None
        # 处理字符串输入（可能是大写或小写）
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "open":
                return TicketStatus.OPEN
            elif normalized == "done":
                return TicketStatus.DONE
            else:
                raise ValueError(f"状态值无效: {value}，必须是 'open' 或 'done'")
        # 如果已经是 TicketStatus 枚举，直接返回
        return value

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        return [tag.strip().lower() for tag in value if tag.strip()]

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else value


class TicketResponse(TicketBase):
    id: uuid.UUID
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TicketsListResponse(BaseModel):
    total: int
    items: List[TicketResponse]


class HealthResponse(BaseModel):
    status: str
