from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CampaignModel(Base):
    """Campaign model representing an ad campaign across any platform."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="google, meta, taboola, tiktok"
    )
    platform_campaign_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Platform-native campaign ID"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="active", comment="active, paused, completed, archived"
    )
    daily_budget: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    total_budget: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    spent: Mapped[Decimal] = mapped_column(Float, default=0.0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    cpa: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    roas: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    revenue: Mapped[Decimal] = mapped_column(Float, default=0.0)
    ctr: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    creatives = relationship(
        "CreativeModel", back_populates="campaign", cascade="all, delete-orphan"
    )
    landing_pages = relationship(
        "LandingPageModel", back_populates="campaign", cascade="all, delete-orphan"
    )
    insights = relationship(
        "InsightModel", back_populates="campaign", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Campaign {self.id}: {self.name} ({self.platform})>"
