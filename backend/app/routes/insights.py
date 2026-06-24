from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.orm import joinedload

from app.database import DbSession
from app.models.insight import InsightModel
from app.rate_limit import limiter
from app.schemas.insight import InsightListResponse, InsightResponse
from app.services.anomaly_detector import anomaly_detector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("", response_model=InsightListResponse)
def list_insights(
    db: DbSession,
    type: str | None = Query(None, pattern=r"^(anomaly|recommendation|insight|alert)?$"),
    severity: str | None = Query(None, pattern=r"^(critical|high|medium|low|info)?$"),
    is_read: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
):
    """List all insights with optional filtering."""
    query = db.query(InsightModel)

    if type:
        query = query.filter(InsightModel.type == type)
    if severity:
        query = query.filter(InsightModel.severity == severity)
    if is_read is not None:
        query = query.filter(InsightModel.is_read == is_read)

    total = query.count()
    unread_count = (
        db.query(InsightModel)
        .filter(InsightModel.is_read == False)  # noqa: E712
        .count()
    )

    items = (
        query.options(joinedload(InsightModel.campaign))
        .order_by(InsightModel.created_at.desc())
        .limit(limit)
        .all()
    )

    validated = [InsightResponse.model_validate(item) for item in items]

    return InsightListResponse(
        items=validated,
        total=total,
        unread_count=unread_count,
    )


@router.put("/{insight_id}/read", response_model=InsightResponse)
def mark_insight_read(insight_id: int, db: DbSession):
    """Mark an insight as read."""
    insight = db.query(InsightModel).filter(InsightModel.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail=f"Insight {insight_id} not found")

    insight.is_read = True
    db.commit()
    db.refresh(insight)
    return InsightResponse.model_validate(insight)


@router.post("/scan", response_model=list[InsightResponse])
@limiter.limit("10/minute")
def scan_for_anomalies(request: Request, db: DbSession):  # noqa: ARG001
    """Run anomaly detection across all active campaigns."""
    logger.info("Running anomaly detection scan...")
    anomalies = anomaly_detector.detect_anomalies(db)

    created_insights = []
    for anomaly in anomalies:
        # Avoid duplicates: check if similar insight exists recently
        existing = (
            db.query(InsightModel)
            .filter(
                InsightModel.title == anomaly["title"],
                InsightModel.campaign_id == anomaly["campaign_id"],
                InsightModel.created_at
                >= datetime.now(UTC) - timedelta(hours=24),  # Last 24 hours
            )
            .first()
        )
        if existing:
            continue

        insight = InsightModel(**anomaly)
        db.add(insight)
        db.flush()
        # Reload to pick up the campaign relationship
        db.refresh(insight)
        created_insights.append(InsightResponse.model_validate(insight))

    db.commit()
    logger.info("Detected %d anomalies", len(created_insights))
    return created_insights
