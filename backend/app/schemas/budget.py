from __future__ import annotations

from pydantic import BaseModel, Field


class BudgetAllocation(BaseModel):
    """Schema for a single budget allocation recommendation."""

    campaign_id: int
    campaign_name: str
    platform: str
    current_budget: float
    recommended_budget: float
    change_amount: float
    change_percent: float
    rationale: str
    expected_impact: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class BudgetRecommendationResponse(BaseModel):
    """Schema for budget optimization recommendations."""

    recommendations: list[BudgetAllocation]
    total_current_budget: float
    total_recommended_budget: float
    expected_roas_improvement: float | None = None
    estimated_additional_revenue: float | None = None
    summary: str
