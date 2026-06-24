"""Platform synchronization service.

Provides mock data generation for development and interfaces for
syncing campaign data from ad platforms.
"""

from __future__ import annotations

import logging
import random
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.ad_platform import AdPlatformModel
from app.models.campaign import CampaignModel
from app.models.creative import CreativeModel
from app.models.landing_page import LandingPageModel

logger = logging.getLogger(__name__)


class PlatformSyncService:
    """Handles syncing campaign data from ad platforms."""

    def sync_platform(self, platform_id: int, db: Session) -> dict[str, Any]:
        """Sync data from a connected platform."""
        platform = db.query(AdPlatformModel).filter(
            AdPlatformModel.id == platform_id
        ).first()

        if not platform:
            return {
                "platform_id": platform_id,
                "status": "error",
                "campaigns_synced": 0,
                "message": "Platform not found",
            }

        platform.last_sync_at = datetime.now(UTC)
        db.commit()

        # For dev/demo: generate mock campaign data
        new_campaigns = self._generate_mock_campaigns(platform.platform_type, db)

        return {
            "platform_id": platform.id,
            "platform_name": platform.name,
            "status": "success",
            "campaigns_synced": new_campaigns,
            "message": f"Successfully synced {new_campaigns} campaigns from {platform.name}",
        }

    def _generate_mock_campaigns(self, platform_type: str, db: Session) -> int:
        """Generate mock campaigns for demonstration purposes."""
        platform_names = {
            "meta": "Meta Ads",
            "google": "Google Ads",
            "taboola": "Taboola",
            "tiktok": "TikTok Ads",
        }

        campaign_templates = [
            {
                "name": platform_names.get(platform_type, platform_type)
                + " - Brand Awareness Q3",
                "roas": 4.2, "cpa": 8.50,
            },
            {
                "name": platform_names.get(platform_type, platform_type)
                + " - Retargeting - Warm Audiences",
                "roas": 6.8, "cpa": 5.20,
            },
            {
                "name": platform_names.get(platform_type, platform_type)
                + " - Lead Gen - Email List",
                "roas": 3.5, "cpa": 12.00,
            },
            {
                "name": platform_names.get(platform_type, platform_type)
                + " - SMS Signup Campaign",
                "roas": 5.1, "cpa": 7.80,
            },
            {
                "name": platform_names.get(platform_type, platform_type)
                + " - Lookalike Audience Expansion",
                "roas": 2.9, "cpa": 15.40,
            },
        ]

        count = 0
        for template in campaign_templates[:random.randint(2, 4)]:
            existing = db.query(CampaignModel).filter(
                CampaignModel.name == template["name"],
                CampaignModel.platform == platform_type,
            ).first()

            if existing:
                continue

            impressions = random.randint(50000, 500000)
            clicks = int(impressions * random.uniform(0.01, 0.05))
            conversions = int(clicks * random.uniform(0.02, 0.08))
            spent = conversions * template["cpa"]
            revenue = spent * template["roas"]
            ctr = (clicks / impressions * 100) if impressions > 0 else 0

            campaign = CampaignModel(
                name=template["name"],
                platform=platform_type,
                status=random.choice(["active", "active", "active", "paused"]),
                daily_budget=random.uniform(50, 500),
                total_budget=random.uniform(1000, 10000),
                spent=float(spent),
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                cpa=float(template["cpa"]),
                roas=float(template["roas"]),
                revenue=float(revenue),
                ctr=float(ctr),
                start_date=datetime.now(UTC) - timedelta(days=random.randint(7, 60)),
            )
            db.add(campaign)
            db.flush()

            # Generate mock creatives
            self._generate_mock_creatives(campaign, platform_type, db)

            # Generate mock landing pages
            self._generate_mock_landing_pages(campaign, platform_type, db)

            count += 1

        db.commit()
        return count

    def _generate_mock_creatives(self, campaign: CampaignModel, platform: str, db: Session) -> None:
        """Generate mock creatives for a campaign."""
        creative_templates = [
            {
                "headline": "Get Your Free Guide Now",
                "body": "Download our comprehensive guide to affiliate marketing success",
                "cta": "Download Free Guide",
            },
            {
                "headline": "Limited Time Offer - Join Today",
                "body": "Exclusive access to premium marketing resources. Don't miss out!",
                "cta": "Join Now",
            },
            {
                "headline": "Grow Your Business 10x",
                "body": "Proven strategies that top affiliates use daily. Start your journey.",
                "cta": "Get Started",
            },
            {
                "headline": "You're Missing Out on Revenue",
                "body": "Discover the affiliate secrets that generate passive income",
                "cta": "Learn More",
            },
        ]

        for template in creative_templates[:random.randint(2, 4)]:
            impressions = random.randint(10000, campaign.impressions)
            clicks = int(impressions * random.uniform(0.01, 0.06))
            conversions = int(clicks * random.uniform(0.02, 0.08))
            spend = random.uniform(100, float(campaign.spent) * 0.3)
            cpa = spend / conversions if conversions > 0 else 0
            roas = random.uniform(1.0, 8.0)

            creative = CreativeModel(
                campaign_id=campaign.id,
                platform=platform,
                headline=template["headline"],
                body=template["body"],
                cta=template["cta"],
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                spend=float(spend),
                cpa=float(cpa),
                roas=float(roas),
                ctr=float(clicks / impressions * 100) if impressions > 0 else 0,
                ai_score=random.uniform(0.3, 0.95),
                ai_analysis="Heuristic analysis completed.",
            )
            db.add(creative)

    def _generate_mock_landing_pages(
        self, campaign: CampaignModel, platform: str, db: Session
    ) -> None:
        """Generate mock landing pages for a campaign."""
        urls = [
            "https://example.com/affiliate-guide",
            "https://example.com/free-trial",
            "https://example.com/webinar-registration",
            "https://example.com/demo-request",
        ]

        for url in urls[:random.randint(1, 3)]:
            visits = random.randint(500, campaign.clicks)
            conversions = int(visits * random.uniform(0.01, 0.1))
            revenue = float(campaign.revenue) * random.uniform(0.1, 0.4)

            landing = LandingPageModel(
                campaign_id=campaign.id,
                url=url,
                platform=platform,
                visits=visits,
                unique_visits=int(visits * random.uniform(0.6, 0.9)),
                conversions=conversions,
                conversion_rate=float(conversions / visits * 100) if visits > 0 else 0,
                revenue=float(revenue),
                cost=float(campaign.spent) * random.uniform(0.1, 0.4),
                roas=float(
                    revenue / (float(campaign.spent) * 0.3)
                ) if float(campaign.spent) > 0 else 0,
                bounce_rate=random.uniform(0.2, 0.7),
                avg_time_on_page=random.uniform(30, 300),
            )
            db.add(landing)


platform_sync_service = PlatformSyncService()
