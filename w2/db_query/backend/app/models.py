"""Database models."""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class DatabaseConnection(Base):
    """Database connection model."""

    __tablename__ = "database_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    database_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DatabaseMetadata(Base):
    """Database metadata model (tables and views information)."""

    __tablename__ = "database_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    connection_name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True
    )
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

