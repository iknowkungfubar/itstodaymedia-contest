from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class LandingPageBase(BaseModel):
    """Shared landing page fields."""

    url: str = Field(..., min_length=1, max_length=1000)


class LandingPageCreate(LandingPageBase):
    """Schema for creating a new landing page entry."""

    campaign_id: int
    platform: str = Field(..., pattern=r"^(google|meta|taboola|tiktok)$")


class LandingPageResponse(LandingPageBase):
    """Schema for landing page API responses."""

    id: int
    campaign_id: int
    platform: str
    visits: int
    unique_visits: int
    conversions: int
    conversion_rate: float | None = None
    revenue: float
    cost: float
    roas: float | None = None
    bounce_rate: float | None = None
    avg_time_on_page: float | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class LandingPagePerformanceSummary(BaseModel):
    """Aggregated landing page performance."""

    total_visits: int
    total_conversions: int
    overall_conversion_rate: float
    total_revenue: float
    total_cost: float
    overall_roas: float
    top_performing_url: str | None = None
    top_conversion_rate: float | None = None
