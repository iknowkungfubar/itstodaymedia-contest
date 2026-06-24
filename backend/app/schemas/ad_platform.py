from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class PlatformConnect(BaseModel):
    """Schema for connecting an ad platform."""

    name: str = Field(..., min_length=1, max_length=100)
    platform_type: str = Field(..., pattern=r"^(google|meta|taboola|tiktok)$")
    credentials_json: str | None = None


class PlatformResponse(BaseModel):
    """Schema for ad platform API responses."""

    id: int
    name: str
    platform_type: str
    is_connected: bool
    last_sync_at: datetime.datetime | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class PlatformSyncResponse(BaseModel):
    """Schema for platform sync result."""

    platform_id: int
    platform_name: str
    status: str  # success, partial, error
    campaigns_synced: int
    message: str
