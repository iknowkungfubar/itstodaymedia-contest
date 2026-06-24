from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LandingPageModel(Base):
    """Landing page model for tracking conversion performance from ad spend."""

    __tablename__ = "landing_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    visits: Mapped[int] = mapped_column(Integer, default=0)
    unique_visits: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    revenue: Mapped[Decimal] = mapped_column(Float, default=0.0)
    cost: Mapped[Decimal] = mapped_column(Float, default=0.0)
    roas: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    bounce_rate: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    avg_time_on_page: Mapped[Decimal | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    campaign = relationship("CampaignModel", back_populates="landing_pages")

    def __repr__(self) -> str:
        return f"<LandingPage {self.id}: {self.url[:50]}>"
