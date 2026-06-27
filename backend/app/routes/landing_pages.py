from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.database import DbSession
from app.models.landing_page import LandingPageModel
from app.schemas.landing_page import (
    LandingPageCreate,
    LandingPagePerformanceSummary,
    LandingPageResponse,
)

router = APIRouter(prefix="/api/landing-pages", tags=["landing-pages"])


@router.get("", response_model=list[LandingPageResponse])
def list_landing_pages(
    db: DbSession,
    campaign_id: int | None = None,
):
    """List all landing pages, optionally filtered by campaign."""
    query = db.query(LandingPageModel)
    if campaign_id:
        query = query.filter(LandingPageModel.campaign_id == campaign_id)

    return [LandingPageResponse.model_validate(lp) for lp in query.all()]


@router.get("/{landing_page_id}", response_model=LandingPageResponse)
def get_landing_page(landing_page_id: int, db: DbSession):
    """Get a single landing page by ID."""
    lp = db.query(LandingPageModel).filter(LandingPageModel.id == landing_page_id).first()

    if not lp:
        raise HTTPException(status_code=404, detail=f"Landing page {landing_page_id} not found")
    return LandingPageResponse.model_validate(lp)


@router.post("", response_model=LandingPageResponse, status_code=201)
def create_landing_page(data: LandingPageCreate, db: DbSession):
    """Add a landing page to track."""
    lp = LandingPageModel(**data.model_dump())
    db.add(lp)
    db.commit()
    db.refresh(lp)
    return LandingPageResponse.model_validate(lp)


@router.get("/summary/performance", response_model=LandingPagePerformanceSummary)
def get_landing_page_performance_summary(db: DbSession):
    """Get aggregate landing page performance metrics."""
    pages = db.query(LandingPageModel).all()

    total_visits = sum(p.visits for p in pages)
    total_conversions = sum(p.conversions for p in pages)
    total_revenue = sum(float(p.revenue) for p in pages)
    total_cost = sum(float(p.cost) for p in pages)

    # Find top performer
    top_page = max(pages, key=lambda p: p.conversion_rate or 0) if pages else None

    return LandingPagePerformanceSummary(
        total_visits=total_visits,
        total_conversions=total_conversions,
        overall_conversion_rate=round(
            (total_conversions / total_visits * 100) if total_visits > 0 else 0, 2
        ),
        total_revenue=round(total_revenue, 2),
        total_cost=round(total_cost, 2),
        overall_roas=round(total_revenue / total_cost, 2) if total_cost > 0 else 0,
        top_performing_url=str(top_page.url) if top_page else None,
        top_conversion_rate=round(float(top_page.conversion_rate or 0), 2) if top_page else None,
    )
