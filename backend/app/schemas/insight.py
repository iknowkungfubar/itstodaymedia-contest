from __future__ import annotations

import datetime

from pydantic import BaseModel


class InsightResponse(BaseModel):
    """Schema for insight API responses."""

    id: int
    type: str
    severity: str
    title: str
    description: str
    platform: str | None = None
    campaign_id: int | None = None
    campaign_name: str | None = None
    metric_name: str | None = None
    current_value: float | None = None
    previous_value: float | None = None
    threshold: float | None = None
    is_read: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class InsightListResponse(BaseModel):
    """Schema for paginated insight list."""

    items: list[InsightResponse]
    total: int
    unread_count: int
