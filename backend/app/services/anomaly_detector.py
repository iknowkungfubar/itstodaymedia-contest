"""Automated anomaly detection for campaign metrics.

Monitors campaign performance metrics and generates alerts when
significant deviations from historical patterns are detected.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.campaign import CampaignModel

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalies in campaign performance metrics."""

    def detect_anomalies(self, db: Session) -> list[dict[str, Any]]:
        """Run anomaly detection across all active campaigns."""
        anomalies: list[dict[str, Any]] = []

        campaigns = db.query(CampaignModel).filter(CampaignModel.status == "active").all()

        for campaign in campaigns:
            campaign_anomalies = self._check_campaign(campaign, db)
            anomalies.extend(campaign_anomalies)

        return anomalies

    def _check_campaign(self, campaign: CampaignModel, db: Session) -> list[dict[str, Any]]:
        """Check a single campaign for all anomaly types."""
        findings: list[dict[str, Any]] = []

        # Check for zero-impression campaigns (spending with no delivery)
        if campaign.impressions == 0 and float(campaign.spent) > 0:
            findings.append(
                {
                    "type": "anomaly",
                    "severity": "critical",
                    "title": f"Campaign '{campaign.name}' has spend but zero impressions",
                    "description": (
                        f"Campaign has spent ${float(campaign.spent):.2f} with 0 impressions. "
                        "This could indicate a delivery issue, rejected ads, or targeting problems."
                    ),
                    "platform": campaign.platform,
                    "campaign_id": campaign.id,
                    "metric_name": "impressions",
                    "current_value": 0.0,
                    "previous_value": None,
                    "threshold": None,
                }
            )
            return findings

        # Check for CPA spike
        if campaign.cpa and float(campaign.cpa) > 0 and campaign.conversions > 0:
            avg_cpa = self._get_avg_cpa(campaign.platform, db)
            if avg_cpa and float(campaign.cpa) > avg_cpa * 1.5:
                findings.append(
                    {
                        "type": "anomaly",
                        "severity": "high" if float(campaign.cpa) > avg_cpa * 2.0 else "medium",
                        "title": f"CPA spike detected for '{campaign.name}'",
                        "description": (
                            f"Current CPA (${float(campaign.cpa):.2f}) is "
                            f"{((float(campaign.cpa) / avg_cpa) - 1) * 100:.0f}% above "
                            f"platform average of ${avg_cpa:.2f}"
                        ),
                        "platform": campaign.platform,
                        "campaign_id": campaign.id,
                        "metric_name": "cpa",
                        "current_value": float(campaign.cpa),
                        "previous_value": avg_cpa,
                        "threshold": avg_cpa * 1.5,
                    }
                )

        # Check for ROAS drop
        if campaign.roas and float(campaign.roas) > 0:
            avg_roas = self._get_avg_roas(campaign.platform, db)
            if avg_roas and float(campaign.roas) < avg_roas * 0.6:
                findings.append(
                    {
                        "type": "anomaly",
                        "severity": "high",
                        "title": f"ROAS decline for '{campaign.name}'",
                        "description": (
                            f"Current ROAS ({float(campaign.roas):.2f}x) is significantly below "
                            f"platform average ({avg_roas:.2f}x). Review creative performance "
                            "and landing page experience."
                        ),
                        "platform": campaign.platform,
                        "campaign_id": campaign.id,
                        "metric_name": "roas",
                        "current_value": float(campaign.roas),
                        "previous_value": avg_roas,
                        "threshold": avg_roas * 0.6,
                    }
                )

        # Check for spend acceleration
        if float(campaign.spent) > 1000 and float(campaign.daily_budget or 0) > 0:
            days_active = max(1, self._days_since_start(campaign))
            expected_spend = float(campaign.daily_budget) * days_active
            actual_spend = float(campaign.spent)
            if actual_spend > expected_spend * 1.3:
                findings.append(
                    {
                        "type": "alert",
                        "severity": "medium",
                        "title": f"Higher than expected spend for '{campaign.name}'",
                        "description": (
                            f"Campaign spent ${actual_spend:.2f} vs expected "
                            f"${expected_spend:.2f} "
                            f"({((actual_spend / expected_spend) - 1) * 100:.0f}% over)."
                        ),
                        "platform": campaign.platform,
                        "campaign_id": campaign.id,
                        "metric_name": "spend",
                        "current_value": actual_spend,
                        "previous_value": expected_spend,
                        "threshold": expected_spend * 1.3,
                    }
                )

        return findings

    def _get_avg_cpa(self, platform: str, db: Session) -> float | None:
        """Get average CPA for a platform."""
        result = (
            db.query(func.avg(CampaignModel.cpa))
            .filter(
                CampaignModel.platform == platform,
                CampaignModel.cpa.isnot(None),
                CampaignModel.cpa > 0,
            )
            .scalar()
        )
        return float(result) if result else None

    def _get_avg_roas(self, platform: str, db: Session) -> float | None:
        """Get average ROAS for a platform."""
        result = (
            db.query(func.avg(CampaignModel.roas))
            .filter(
                CampaignModel.platform == platform,
                CampaignModel.roas.isnot(None),
                CampaignModel.roas > 0,
            )
            .scalar()
        )
        return float(result) if result else None

    def _days_since_start(self, campaign: CampaignModel) -> int:
        """Calculate days since campaign start."""
        if campaign.start_date:
            delta = datetime.now(UTC) - campaign.start_date.replace(tzinfo=UTC)
            return max(1, delta.days)
        return 7  # default assumption


anomaly_detector = AnomalyDetector()
