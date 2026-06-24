from __future__ import annotations

import datetime

from pydantic import BaseModel, model_validator


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

    @model_validator(mode="before")
    @classmethod
    def resolve_campaign_name(cls, data: object) -> object:
        """Populate campaign_name from the ORM relationship when available.

        This avoids needing to set ``campaign_name`` manually after
        ``model_validate()`` in every caller — the relationship is resolved
        automatically at validation time.
        """
        if hasattr(data, "campaign") and data.campaign:  # noqa: B009
            data.campaign_name = data.campaign.name  # type: ignore[attr-defined]
        return data


class InsightListResponse(BaseModel):
    """Schema for paginated insight list."""

    items: list[InsightResponse]
    total: int
    unread_count: int
