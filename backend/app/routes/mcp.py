"""MCP Router — bridge between the REST API and MCP ad-platform servers.

Exposes three endpoints:

* ``GET  /api/mcp/servers`` — list available MCP servers with their
  resources and tools.
* ``POST /api/mcp/servers/{server_name}/tools/call`` — invoke a tool on
  a specific MCP server.
* ``POST /api/mcp/sync`` — pull campaign data from all MCP-connected
  ad platforms and persist it to the database.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from app.database import DbSession
from app.models.ad_platform import AdPlatformModel
from app.models.campaign import CampaignModel
from app.services.mcp_manager import mcp_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mcp", tags=["mcp"])


# ── Helpers ─────────────────────────────────────────────────────────────────

# Maps the internal server identifier used by MCP to the short platform_type
# stored in the campaigns database.
_PLATFORM_TYPE_MAP: dict[str, str] = {
    "meta-ads": "meta",
    "google-ads": "google",
}

# Reverse map: platform_type → MCP server name.
_PLATFORM_TO_SERVER: dict[str, str] = {v: k for k, v in _PLATFORM_TYPE_MAP.items()}


def _normalise_status(raw: str) -> str:
    """Convert MCP status strings to CampaignModel status values."""
    upper = raw.upper()
    if upper in ("ACTIVE", "ENABLED"):
        return "active"
    if upper in ("PAUSED", "REMOVED"):
        return "paused"
    return "active"  # sensible default


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.get("/servers")
def list_mcp_servers() -> dict[str, list[dict[str, Any]]]:
    """List all MCP servers with their capabilities.

    Returns the server's name, version, available resources, and
    callable tools — effectively exposing the MCP protocol's
    ``list_resources`` + ``list_tools`` in one shot.
    """
    return {"servers": mcp_manager.list_servers()}


@router.post("/servers/{server_name}/tools/call")
async def call_mcp_tool(server_name: str, body: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool on a specific MCP server.

    The request body follows the MCP tool-call convention:

    .. code-block:: json

        {
            "name": "list_campaigns",
            "arguments": { "status": "ACTIVE", "limit": 10 }
        }
    """
    tool_name = body.get("name", "")
    arguments = body.get("arguments", {})

    if not tool_name:
        raise HTTPException(status_code=400, detail="Field 'name' is required")

    response = await mcp_manager.call_tool(server_name, tool_name, arguments)

    if response.error:
        raise HTTPException(status_code=400, detail=response.error)

    return response.result or {}


@router.post("/sync")
async def mcp_sync(db: DbSession) -> dict[str, Any]:
    """Pull campaign data from all connected MCP ad platforms.

    Iterates each platform in the database that has ``is_connected=True``,
    locates its corresponding MCP server, calls ``list_campaigns``, and
    upserts the returned campaigns into the local database.
    Returns per-platform sync results.
    """
    platforms = (
        db.query(AdPlatformModel)
        .filter(AdPlatformModel.is_connected == True)  # noqa: E712
        .all()
    )

    if not platforms:
        return {
            "sync_results": [],
            "message": "No connected platforms found. Connect a platform first.",
        }

    sync_results: list[dict[str, Any]] = []

    for platform in platforms:
        server_name = _PLATFORM_TO_SERVER.get(platform.platform_type)
        if not server_name:
            continue  # no MCP server for Taboola / TikTok yet

        try:
            response = await mcp_manager.call_tool(
                server_name,
                "list_campaigns",
                {},
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("MCP tool call failed for %s", server_name)
            sync_results.append(_error_result(platform, str(exc)))
            continue

        if response.error:
            sync_results.append(_error_result(platform, response.error))
            continue

        campaigns_data = (response.result or {}).get("campaigns", [])
        synced_count = 0

        for camp_data in campaigns_data:
            synced_count += _upsert_campaign(db, platform.platform_type, camp_data)

        if synced_count > 0:
            db.commit()

        # Stamp the platform's last-sync timestamp.
        platform.last_sync_at = datetime.now(UTC)
        db.commit()

        sync_results.append(
            {
                "platform_id": platform.id,
                "platform_name": platform.name,
                "platform_type": platform.platform_type,
                "status": "success",
                "campaigns_synced": synced_count,
                "message": (
                    f"Synced {synced_count} campaign(s) from {platform.name} "
                    f"via MCP server '{server_name}'"
                ),
            }
        )

    return {"sync_results": sync_results}


# ── Internal helpers ────────────────────────────────────────────────────────


def _error_result(platform: AdPlatformModel, detail: str) -> dict[str, Any]:
    return {
        "platform_id": platform.id,
        "platform_name": platform.name,
        "platform_type": platform.platform_type,
        "status": "error",
        "campaigns_synced": 0,
        "message": detail,
    }


def _upsert_campaign(
    db: DbSession,
    platform_type: str,
    camp_data: dict[str, Any],
) -> int:
    """Insert or update a single campaign from MCP data. Returns 1 on insert, 0 on update."""
    platform_campaign_id = str(camp_data.get("id", ""))
    if not platform_campaign_id:
        return 0

    existing = (
        db.query(CampaignModel)
        .filter(
            CampaignModel.platform_campaign_id == platform_campaign_id,
            CampaignModel.platform == platform_type,
        )
        .first()
    )

    if existing:
        # Update mutable fields.
        if "status" in camp_data:
            existing.status = _normalise_status(camp_data["status"])
        if "daily_budget" in camp_data:
            existing.daily_budget = float(camp_data["daily_budget"])
        return 0  # update, not a new insert

    campaign = CampaignModel(
        name=str(camp_data.get("name", f"Synced {platform_campaign_id}")),
        platform=platform_type,
        platform_campaign_id=platform_campaign_id,
        status=_normalise_status(camp_data.get("status", "")),
        daily_budget=float(camp_data.get("daily_budget", 0)),
    )
    db.add(campaign)
    return 1  # new campaign created
