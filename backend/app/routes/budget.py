from __future__ import annotations

from fastapi import APIRouter, Query

from app.database import DbSession
from app.schemas.budget import BudgetRecommendationResponse
from app.services.budget_optimizer import budget_optimizer

router = APIRouter(prefix="/api/budget", tags=["budget"])


@router.get("/recommendations", response_model=BudgetRecommendationResponse)
def get_budget_recommendations(
    db: DbSession,
    total_budget: float | None = Query(None, ge=0),
):
    """Get AI-powered budget allocation recommendations across all campaigns."""
    result = budget_optimizer.get_recommendations(db, total_budget)
    return BudgetRecommendationResponse(**result)
