from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CreativeModel(Base):
    """Creative model for ad creatives/images/copy across platforms."""

    __tablename__ = "creatives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    platform_creative_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    cta: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cta_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    spend: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0.0)
    cpa: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    roas: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    ctr: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    campaign = relationship("CampaignModel", back_populates="creatives")

    def __repr__(self) -> str:
        return f"<Creative {self.id}: {self.headline[:50]}>"
