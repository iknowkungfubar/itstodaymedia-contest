from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class CreativeBase(BaseModel):
    """Shared creative fields."""

    headline: str = Field(..., min_length=1, max_length=500)
    body: str | None = None
    image_url: str | None = Field(None, max_length=1000)
    cta: str | None = None
    cta_type: str | None = None


class CreativeCreate(CreativeBase):
    """Schema for creating a new creative."""

    campaign_id: int
    platform: str = Field(..., pattern=r"^(google|meta|taboola|tiktok)$")
    platform_creative_id: str | None = None


class CreativeUpdate(BaseModel):
    """Schema for updating a creative."""

    headline: str | None = Field(None, min_length=1, max_length=500)
    body: str | None = None
    image_url: str | None = None
    cta: str | None = None


class CreativeResponse(CreativeBase):
    """Schema for creative API responses."""

    id: int
    campaign_id: int
    platform: str
    platform_creative_id: str | None = None
    impressions: int
    clicks: int
    conversions: int
    spend: float
    cpa: float | None = None
    roas: float | None = None
    ctr: float | None = None
    ai_score: float | None = None
    ai_analysis: str | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    recommendations: list[str] | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CreativeAnalysisRequest(BaseModel):
    """Schema for requesting AI creative analysis."""

    creative_ids: list[int] = Field(..., min_length=1)
    include_recommendations: bool = True


class CreativeAnalysisResponse(BaseModel):
    """Schema for AI creative analysis results."""

    creative_id: int
    headline: str
    ai_score: float
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    predicted_ctr: float | None = None
    predicted_conversion_rate: float | None = None
