from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.database import DbSession
from app.models.creative import CreativeModel
from app.rate_limit import limiter
from app.schemas.creative import (
    CreativeAnalysisRequest,
    CreativeAnalysisResponse,
    CreativeCreate,
    CreativeResponse,
    CreativeUpdate,
)
from app.services.ai_analyzer import ai_analyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/creatives", tags=["creatives"])


@router.get("", response_model=list[CreativeResponse])
def list_creatives(
    db: DbSession,
    campaign_id: int | None = None,
    platform: str | None = None,
):
    """List all creatives, optionally filtered by campaign or platform."""
    query = db.query(CreativeModel)
    if campaign_id:
        query = query.filter(CreativeModel.campaign_id == campaign_id)
    if platform:
        query = query.filter(CreativeModel.platform == platform)

    return [CreativeResponse.model_validate(c) for c in query.all()]


@router.get("/{creative_id}", response_model=CreativeResponse)
def get_creative(creative_id: int, db: DbSession):
    """Get a single creative by ID."""
    creative = db.query(CreativeModel).filter(CreativeModel.id == creative_id).first()
    if not creative:
        raise HTTPException(status_code=404, detail=f"Creative {creative_id} not found")
    return CreativeResponse.model_validate(creative)


@router.post("", response_model=CreativeResponse, status_code=201)
def create_creative(data: CreativeCreate, db: DbSession):
    """Create a new creative."""
    creative = CreativeModel(**data.model_dump())
    db.add(creative)
    db.commit()
    db.refresh(creative)
    return CreativeResponse.model_validate(creative)


@router.put("/{creative_id}", response_model=CreativeResponse)
def update_creative(creative_id: int, data: CreativeUpdate, db: DbSession):
    """Update an existing creative."""
    creative = db.query(CreativeModel).filter(CreativeModel.id == creative_id).first()
    if not creative:
        raise HTTPException(status_code=404, detail=f"Creative {creative_id} not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(creative, field, value)

    db.commit()
    db.refresh(creative)
    return CreativeResponse.model_validate(creative)


@router.delete("/{creative_id}", status_code=204)
def delete_creative(creative_id: int, db: DbSession):
    """Delete a creative."""
    creative = db.query(CreativeModel).filter(CreativeModel.id == creative_id).first()
    if not creative:
        raise HTTPException(status_code=404, detail=f"Creative {creative_id} not found")
    db.delete(creative)
    db.commit()


@router.post("/analyze", response_model=list[CreativeAnalysisResponse])
@limiter.limit("10/minute")
def analyze_creatives(request: Request, data: CreativeAnalysisRequest, db: DbSession):  # noqa: ARG001
    """Analyze creatives using AI for performance prediction."""
    creatives = db.query(CreativeModel).filter(
        CreativeModel.id.in_(data.creative_ids)
    ).all()

    if not creatives:
        raise HTTPException(status_code=404, detail="No creatives found for the given IDs")

    results = []
    for creative in creatives:
        analysis = ai_analyzer.analyze_creative(
            headline=creative.headline,
            body=creative.body,
            cta=creative.cta,
            platform=creative.platform,
            historical_data={
                "impressions": creative.impressions,
                "clicks": creative.clicks,
                "conversions": creative.conversions,
            },
        )

        # Save analysis results to the creative
        creative.ai_score = analysis["ai_score"]
        creative.ai_analysis = analysis.get("analysis_text", "")
        creative.strengths = analysis.get("strengths", [])
        creative.weaknesses = analysis.get("weaknesses", [])
        creative.recommendations = analysis.get("recommendations", [])
        db.add(creative)

        results.append(
            CreativeAnalysisResponse(
                creative_id=creative.id,
                headline=creative.headline,
                ai_score=analysis["ai_score"],
                strengths=analysis["strengths"],
                weaknesses=analysis["weaknesses"],
                recommendations=analysis["recommendations"],
                predicted_ctr=analysis.get("predicted_ctr"),
                predicted_conversion_rate=analysis.get("predicted_conversion_rate"),
            )
        )

    db.commit()
    logger.info("Analyzed %d creatives with AI", len(creatives))
    return results
