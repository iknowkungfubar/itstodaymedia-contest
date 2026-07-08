from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy import func as sa_func

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
    """Get aggregate campaign statistics across all platforms.

    Uses SQL aggregation functions to avoid loading every row into Python
    memory — O(1) queries regardless of table size.
    """
    from app.models.campaign import CampaignModel

    # ── Totals (single aggregation query) ────────────────────────────────
    totals = db.query(
        sa_func.count(CampaignModel.id),
        sa_func.sum(CampaignModel.impressions),
        sa_func.sum(CampaignModel.clicks),
        sa_func.sum(CampaignModel.conversions),
        sa_func.sum(CampaignModel.spent),
        sa_func.sum(CampaignModel.revenue),
    ).one()

    total_campaigns = totals[0] or 0
    total_impressions = totals[1] or 0
    total_clicks = totals[2] or 0
    total_conversions = totals[3] or 0
    total_spent = float(totals[4] or 0)
    total_revenue = float(totals[5] or 0)
    active = (
        db.query(sa_func.count(CampaignModel.id)).filter(CampaignModel.status == "active").scalar()
        or 0
    )

    # ── Per-platform breakdown (single grouped query) ────────────────────
    rows = (
        db.query(
            CampaignModel.platform,
            sa_func.count(CampaignModel.id),
            sa_func.sum(CampaignModel.impressions),
            sa_func.sum(CampaignModel.clicks),
            sa_func.sum(CampaignModel.conversions),
            sa_func.sum(CampaignModel.spent),
            sa_func.sum(CampaignModel.revenue),
        )
        .group_by(CampaignModel.platform)
        .all()
    )

    by_platform: dict[str, dict] = {}
    for row in rows:
        by_platform[row[0]] = {
            "count": row[1] or 0,
            "impressions": row[2] or 0,
            "clicks": row[3] or 0,
            "conversions": row[4] or 0,
            "spent": round(float(row[5] or 0), 2),
            "revenue": round(float(row[6] or 0), 2),
        }

    return {
        "total_campaigns": total_campaigns,
        "active_campaigns": active,
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_spent": round(total_spent, 2),
        "total_revenue": round(total_revenue, 2),
        "overall_roas": round(total_revenue / total_spent, 2) if total_spent > 0 else 0,
        "overall_ctr": (
            round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0
        ),
        "overall_cpa": round(total_spent / total_conversions, 2) if total_conversions > 0 else 0,
        "by_platform": by_platform,
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
    """Trigger a mock-data sync across all connected platforms.

    This endpoint uses the :class:`PlatformSyncService` to generate
    **mock/dev campaign data** for each connected platform.  It is
    intended for development and demo purposes only.

    For production sync via real MCP ad-platform servers, use the
    ``POST /api/mcp/sync`` endpoint instead.
    """
    from app.models.ad_platform import AdPlatformModel

    platforms = (
        db.query(AdPlatformModel)
        .filter(
            AdPlatformModel.is_connected == True  # noqa: E712
        )
        .all()
    )

    results = []
    for platform in platforms:
        result = platform_sync_service.sync_platform(platform.id, db)
        results.append(result)

    return {
        "sync_results": results,
        "total_platforms_synced": len(results),
    }
