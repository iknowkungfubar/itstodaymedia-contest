from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc

from app.database import DbSession
from app.models.campaign import CampaignModel
from app.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignResponse,
    CampaignUpdate,
)
from app.services.platform_sync import platform_sync_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    platform: str | None = Query(None, pattern=r"^(google|meta|taboola|tiktok)?$"),
    status: str | None = Query(None, pattern=r"^(active|paused|completed|archived)?$"),
    sort_by: str = Query("created_at", pattern=r"^(created_at|name|spent|roas|cpa|conversions)$"),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
):
    """List all campaigns with optional filtering and pagination."""
    query = db.query(CampaignModel)

    if platform:
        query = query.filter(CampaignModel.platform == platform)
    if status:
        query = query.filter(CampaignModel.status == status)

    # Sorting
    sort_column = getattr(CampaignModel, sort_by, CampaignModel.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return CampaignListResponse(
        items=[CampaignResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=dict)
def get_campaign_summary(db: DbSession):
    """Get aggregate campaign statistics across all platforms."""
    campaigns = db.query(CampaignModel).all()

    total_impressions = sum(c.impressions for c in campaigns)
    total_clicks = sum(c.clicks for c in campaigns)
    total_conversions = sum(c.conversions for c in campaigns)
    total_spent = sum(float(c.spent) for c in campaigns)
    total_revenue = sum(float(c.revenue) for c in campaigns)
    active = sum(1 for c in campaigns if c.status == "active")

    # Platform breakdown
    platforms: dict[str, dict] = {}
    for c in campaigns:
        if c.platform not in platforms:
            platforms[c.platform] = {
                "impressions": 0, "clicks": 0, "conversions": 0,
                "spent": 0.0, "revenue": 0.0, "count": 0,
            }
        platforms[c.platform]["impressions"] += c.impressions
        platforms[c.platform]["clicks"] += c.clicks
        platforms[c.platform]["conversions"] += c.conversions
        platforms[c.platform]["spent"] += float(c.spent)
        platforms[c.platform]["revenue"] += float(c.revenue)
        platforms[c.platform]["count"] += 1

    return {
        "total_campaigns": len(campaigns),
        "active_campaigns": active,
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_spent": round(total_spent, 2),
        "total_revenue": round(total_revenue, 2),
        "overall_roas": round(total_revenue / total_spent, 2) if total_spent > 0 else 0,
        "overall_ctr": (
            round(total_clicks / total_impressions * 100, 2)
            if total_impressions > 0 else 0
        ),
        "overall_cpa": round(total_spent / total_conversions, 2) if total_conversions > 0 else 0,
        "by_platform": {
            p: {
                "count": data["count"],
                "impressions": data["impressions"],
                "clicks": data["clicks"],
                "conversions": data["conversions"],
                "spent": round(data["spent"], 2),
                "revenue": round(data["revenue"], 2),
            }
            for p, data in platforms.items()
        },
    }


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: DbSession):
    """Get a single campaign by ID."""
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return CampaignResponse.model_validate(campaign)


@router.post("", response_model=CampaignResponse, status_code=201)
def create_campaign(data: CampaignCreate, db: DbSession):
    """Create a new campaign."""
    campaign = CampaignModel(**data.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    logger.info("Created campaign %d: %s", campaign.id, campaign.name)
    return CampaignResponse.model_validate(campaign)


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(campaign_id: int, data: CampaignUpdate, db: DbSession):
    """Update an existing campaign."""
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)

    db.commit()
    db.refresh(campaign)
    logger.info("Updated campaign %d", campaign.id)
    return CampaignResponse.model_validate(campaign)


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(campaign_id: int, db: DbSession):
    """Delete a campaign."""
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    db.delete(campaign)
    db.commit()
    logger.info("Deleted campaign %d", campaign_id)


@router.post("/sync", response_model=dict)
def trigger_sync(db: DbSession):
    """Trigger a sync across all connected platforms."""
    from app.models.ad_platform import AdPlatformModel

    platforms = db.query(AdPlatformModel).filter(
        AdPlatformModel.is_connected == True  # noqa: E712
    ).all()

    results = []
    for platform in platforms:
        result = platform_sync_service.sync_platform(platform.id, db)
        results.append(result)

    return {
        "sync_results": results,
        "total_platforms_synced": len(results),
    }
