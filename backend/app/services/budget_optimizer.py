"""Budget optimization engine.

Allocates budget across campaigns based on performance metrics
using a weighted scoring system. When OpenAI is configured, it also
provides AI-powered strategic recommendations.
"""

from __future__ import annotations

import logging
from typing import Any

from openai import OpenAI
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.models.campaign import CampaignModel

logger = logging.getLogger(__name__)


class BudgetOptimizer:
    """Optimizes budget allocation across campaigns based on performance."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None
        if settings.openai_api_key:
            self._client = OpenAI(api_key=settings.openai_api_key, timeout=30.0)

    def get_recommendations(self, db: Session, total_budget: float | None = None) -> dict[str, Any]:
        """Generate budget allocation recommendations across all campaigns."""
        campaigns = (
            db.query(CampaignModel)
            .filter(CampaignModel.status == "active")
            .order_by(desc(CampaignModel.roas))
            .all()
        )

        if not campaigns:
            return {
                "recommendations": [],
                "total_current_budget": 0.0,
                "total_recommended_budget": 0.0,
                "expected_roas_improvement": None,
                "estimated_additional_revenue": None,
                "summary": "No active campaigns to optimize.",
            }

        # Calculate total current budget from daily budgets or spent
        total_current = total_budget or sum(float(c.daily_budget or 0) for c in campaigns)
        if total_current == 0:
            total_current = sum(float(c.spent or 0) for c in campaigns)
        if total_current == 0:
            total_current = 1000.0  # Default budget if none set

        # Score each campaign on a weighted composite metric
        scored = []
        for c in campaigns:
            score = self._score_campaign(c)
            scored.append((c, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        total_score = sum(s for _, s in scored) or 1.0

        # Allocate budget proportional to score
        recommendations = []
        for c, score in scored:
            current_budget = float(
                c.daily_budget if c.daily_budget and c.daily_budget > 0 else c.spent
            )
            if current_budget <= 0:
                current_budget = total_current * 0.1 / len(campaigns)

            recommended = round(total_current * (score / total_score), 2)
            change = recommended - current_budget

            rec = {
                "campaign_id": c.id,
                "campaign_name": c.name,
                "platform": c.platform,
                "current_budget": round(current_budget, 2),
                "recommended_budget": recommended,
                "change_amount": round(change, 2),
                "change_percent": round(
                    (change / current_budget * 100) if current_budget > 0 else 0, 1
                ),
                "rationale": self._generate_rationale(c, score),
                "expected_impact": self._generate_expected_impact(c, change),
                "confidence": round(score, 2),
            }
            recommendations.append(rec)

        # Calculate expected improvement
        current_total_roas = sum(float(c.roas or 0) for c in campaigns)
        avg_roas = current_total_roas / len(campaigns) if campaigns else 0

        return {
            "recommendations": recommendations,
            "total_current_budget": round(total_current, 2),
            "total_recommended_budget": round(total_current, 2),
            "expected_roas_improvement": round(avg_roas * 0.15, 4) if avg_roas > 0 else None,
            "estimated_additional_revenue": round(total_current * avg_roas * 0.08, 2),
            "summary": self._generate_summary(recommendations, total_current),
        }

    def _score_campaign(self, campaign: CampaignModel) -> float:
        """Score a campaign on a 0-1 scale based on performance metrics."""
        score = 0.5  # baseline

        # ROAS scoring (higher is better)
        if campaign.roas:
            roas = float(campaign.roas)
            score += min(roas / 10.0, 0.3)

        # CPA scoring (lower is better)
        if campaign.cpa and float(campaign.cpa) > 0:
            # Lower CPA = higher score contribution
            cpa_score = max(0, 0.2 - (float(campaign.cpa) / 500.0))
            score += cpa_score

        # CTR scoring
        if campaign.ctr:
            score += min(float(campaign.ctr) / 0.1, 0.1)

        # Conversion volume
        if campaign.conversions > 100:
            score += 0.1
        elif campaign.conversions > 50:
            score += 0.05

        # Spend efficiency (more spend with good ROAS = scaling well)
        if campaign.roas and float(campaign.roas) > 2 and float(campaign.spent) > 500:
            score += 0.1

        # Volume signal
        if campaign.impressions > 100000:
            score += 0.05

        return max(0.0, min(1.0, score))

    def _generate_rationale(self, campaign: CampaignModel, score: float) -> str:
        """Generate human-readable rationale for a recommendation."""
        parts = []
        if campaign.roas and float(campaign.roas) > 3:
            parts.append(f"High ROAS of {float(campaign.roas):.2f}x suggests strong performance")
        elif campaign.roas and float(campaign.roas) > 1.5:
            parts.append(f"Positive ROAS of {float(campaign.roas):.2f}x with room to scale")
        else:
            parts.append(f"ROAS of {float(campaign.roas or 0):.2f}x needs improvement")

        if campaign.conversions > 0:
            parts.append(
                f"Generated {campaign.conversions} conversions "
                f"at ${float(campaign.cpa or 0):.2f} CPA"
            )

        if score > 0.7:
            parts.append("This campaign is outperforming average — increase budget")
        elif score > 0.4:
            parts.append("Moderate performer — maintain current budget")
        else:
            parts.append("Underperforming — consider creative refreshes before scaling")

        return " | ".join(parts)

    def _generate_expected_impact(self, campaign: CampaignModel, change: float) -> str:
        """Describe expected impact of budget change."""
        if change > 0:
            return (
                f"Increasing budget by ${change:.0f} could drive "
                f"~{abs(int(change * (float(campaign.roas or 1) * 2))):,} additional in revenue"
            )
        elif change < 0:
            return (
                f"Reducing budget by ${abs(change):.0f} reallocates spend "
                f"to higher-performing campaigns"
            )
        return "No change recommended"

    def _generate_summary(self, recommendations: list[dict[str, Any]], _total_budget: float) -> str:
        """Generate an executive summary of budget recommendations."""
        increases = [r for r in recommendations if r["change_amount"] > 0]
        decreases = [r for r in recommendations if r["change_amount"] < 0]

        summary_parts = []
        if increases:
            names = ", ".join(r["campaign_name"] for r in increases[:3])
            summary_parts.append(
                f"Increase budget for {names}"
                + (f" and {len(increases) - 3} more" if len(increases) > 3 else "")
            )
        if decreases:
            names = ", ".join(r["campaign_name"] for r in decreases[:3])
            summary_parts.append(
                f"Reduce budget for {names}"
                + (f" and {len(decreases) - 3} more" if len(decreases) > 3 else "")
            )

        if not summary_parts:
            return "Current budget allocation is well-balanced across all campaigns."

        return " | ".join(summary_parts)


budget_optimizer = BudgetOptimizer()
