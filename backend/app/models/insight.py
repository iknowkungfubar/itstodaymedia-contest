from __future__ import annotations

import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InsightModel(Base):
    """AI-generated insights, anomaly alerts, and budget recommendations."""

    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="anomaly, recommendation, insight, alert",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        default="info",
        comment="critical, high, medium, low, info",
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    campaign_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True
    )
    metric_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_value: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Current metric value"
    )
    previous_value: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Previous metric value for comparison"
    )
    threshold: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Threshold that was breached"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    campaign = relationship("CampaignModel", back_populates="insights")

    def __repr__(self) -> str:
        return f"<Insight {self.id}: [{self.severity}] {self.title[:50]}>"
