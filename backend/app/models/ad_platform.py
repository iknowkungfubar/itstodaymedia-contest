from __future__ import annotations

import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AdPlatformModel(Base):
    """Ad platform connection model for managing API credentials and sync status."""

    __tablename__ = "ad_platforms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    platform_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="google, meta, taboola, tiktok"
    )
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    credentials_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<AdPlatform {self.id}: {self.name} ({self.platform_type})>"
