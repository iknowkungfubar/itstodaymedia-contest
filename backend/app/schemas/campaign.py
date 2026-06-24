from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class CampaignBase(BaseModel):
    """Shared campaign fields."""

    name: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., pattern=r"^(google|meta|taboola|tiktok)$")
    platform_campaign_id: str | None = None
    status: str = Field(default="active", pattern=r"^(active|paused|completed|archived)$")
    daily_budget: float | None = None
    total_budget: float | None = None
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""

    pass


class CampaignUpdate(BaseModel):
    """Schema for updating an existing campaign."""

    name: str | None = Field(None, min_length=1, max_length=255)
    status: str | None = Field(None, pattern=r"^(active|paused|completed|archived)$")
    daily_budget: float | None = None
    total_budget: float | None = None
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None


class CampaignResponse(CampaignBase):
    """Schema for campaign API responses."""

    id: int
    spent: float
    impressions: int
    clicks: int
    conversions: int
    cpa: float | None = None
    roas: float | None = None
    revenue: float
    ctr: float | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    """Schema for paginated campaign list."""

    items: list[CampaignResponse]
    total: int
    page: int = 1
    page_size: int = 50
