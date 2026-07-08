from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.database import DbSession
from app.models.ad_platform import AdPlatformModel
from app.schemas.ad_platform import PlatformConnect, PlatformResponse, PlatformSyncResponse
from app.services.platform_sync import platform_sync_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/platforms", tags=["platforms"])


@router.get("", response_model=list[PlatformResponse])
def list_platforms(db: DbSession):
    """List all connected ad platforms."""
    platforms = db.query(AdPlatformModel).all()
    return [PlatformResponse.model_validate(p) for p in platforms]


@router.post("/connect", response_model=PlatformResponse, status_code=201)
def connect_platform(data: PlatformConnect, db: DbSession):
    """Connect a new ad platform."""
    existing = db.query(AdPlatformModel).filter(AdPlatformModel.name == data.name).first()

    if existing:
        raise HTTPException(status_code=409, detail=f"Platform '{data.name}' already exists")

    platform = AdPlatformModel(
        name=data.name,
        platform_type=data.platform_type,
        credentials_json=data.credentials_json,
        is_connected=True,
    )
    db.add(platform)
    db.commit()
    db.refresh(platform)
    logger.info("Connected platform: %s (%s)", platform.name, platform.platform_type)
    return PlatformResponse.model_validate(platform)


@router.delete("/{platform_id}", status_code=204)
def disconnect_platform(platform_id: int, db: DbSession):
    """Disconnect an ad platform."""
    platform = db.query(AdPlatformModel).filter(AdPlatformModel.id == platform_id).first()

    if not platform:
        raise HTTPException(status_code=404, detail=f"Platform {platform_id} not found")

    db.delete(platform)
    db.commit()
    logger.info("Disconnected platform: %s", platform.name)


@router.post("/{platform_id}/sync", response_model=PlatformSyncResponse)
def sync_platform(platform_id: int, db: DbSession):
    """Sync campaign data from an ad platform."""
    result = platform_sync_service.sync_platform(platform_id, db)
    return PlatformSyncResponse(**result)
