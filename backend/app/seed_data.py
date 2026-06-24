"""Seed data module — populates the database with demonstration records."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from app.database import SessionLocal
from app.models.ad_platform import AdPlatformModel
from app.models.campaign import CampaignModel
from app.models.creative import CreativeModel
from app.models.insight import InsightModel
from app.models.landing_page import LandingPageModel

logger = logging.getLogger(__name__)


def seed_demo_data() -> None:
    """Seed the database with demonstration data if empty."""
    db = SessionLocal()
    try:
        existing = db.query(CampaignModel).count()
        if existing > 0:
            logger.info("Database already has %d campaigns — skipping seed", existing)
            return

        logger.info("Seeding demo data...")

        # --- Ad Platforms ---
        platforms_data = [
            {"name": "Meta Ads", "platform_type": "meta", "is_connected": True},
            {"name": "Google Ads", "platform_type": "google", "is_connected": True},
            {"name": "Taboola", "platform_type": "taboola", "is_connected": False},
            {"name": "TikTok Ads", "platform_type": "tiktok", "is_connected": False},
        ]
        _seed_platforms(db, platforms_data)

        # --- Campaigns ---
        campaigns_data = [
            {
                "name": "Meta Ads - Brand Awareness Q3",
                "platform": "meta",
                "status": "active",
                "daily_budget": 250.0,
                "total_budget": 7500.0,
                "spent": 4850.0,
                "impressions": 425000,
                "clicks": 14875,
                "conversions": 892,
                "revenue": 20370.0,
                "start_date": datetime.now(UTC) - timedelta(days=45),
            },
            {
                "name": "Meta Ads - Retargeting - Warm Audiences",
                "platform": "meta",
                "status": "active",
                "daily_budget": 180.0,
                "total_budget": 5400.0,
                "spent": 3200.0,
                "impressions": 185000,
                "clicks": 9250,
                "conversions": 740,
                "revenue": 25160.0,
                "start_date": datetime.now(UTC) - timedelta(days=30),
            },
            {
                "name": "Meta Ads - SMS Signup Campaign",
                "platform": "meta",
                "status": "active",
                "daily_budget": 150.0,
                "total_budget": 4500.0,
                "spent": 2100.0,
                "impressions": 98000,
                "clicks": 5880,
                "conversions": 470,
                "revenue": 11985.0,
                "start_date": datetime.now(UTC) - timedelta(days=20),
            },
            {
                "name": "Google Ads - Search - Affiliate Offers",
                "platform": "google",
                "status": "active",
                "daily_budget": 300.0,
                "total_budget": 9000.0,
                "spent": 6100.0,
                "impressions": 320000,
                "clicks": 12800,
                "conversions": 640,
                "revenue": 17920.0,
                "start_date": datetime.now(UTC) - timedelta(days=50),
            },
            {
                "name": "Google Ads - Display - Prospecting",
                "platform": "google",
                "status": "paused",
                "daily_budget": 200.0,
                "total_budget": 6000.0,
                "spent": 3800.0,
                "impressions": 580000,
                "clicks": 8700,
                "conversions": 261,
                "revenue": 4959.0,
                "start_date": datetime.now(UTC) - timedelta(days=60),
            },
            {
                "name": "Google Ads - YouTube - Video Ads",
                "platform": "google",
                "status": "active",
                "daily_budget": 120.0,
                "total_budget": 3600.0,
                "spent": 1800.0,
                "impressions": 245000,
                "clicks": 6125,
                "conversions": 245,
                "revenue": 7350.0,
                "start_date": datetime.now(UTC) - timedelta(days=15),
            },
            {
                "name": "Taboola - Content Discovery",
                "platform": "taboola",
                "status": "active",
                "daily_budget": 100.0,
                "total_budget": 3000.0,
                "spent": 1200.0,
                "impressions": 89000,
                "clicks": 1780,
                "conversions": 71,
                "revenue": 1278.0,
                "start_date": datetime.now(UTC) - timedelta(days=14),
            },
            {
                "name": "TikTok Ads - Gen Z Targeting",
                "platform": "tiktok",
                "status": "active",
                "daily_budget": 80.0,
                "total_budget": 2400.0,
                "spent": 960.0,
                "impressions": 156000,
                "clicks": 4680,
                "conversions": 187,
                "revenue": 4488.0,
                "start_date": datetime.now(UTC) - timedelta(days=10),
            },
        ]
        seed_campaigns = _seed_campaigns(db, campaigns_data)

        # --- Creatives ---
        _seed_creatives(db, seed_campaigns)

        # --- Landing Pages ---
        _seed_landing_pages(db, seed_campaigns)

        # --- Insights ---
        _seed_insights(db, seed_campaigns)

        db.commit()
        logger.info(
            "Seeded %d campaigns, %d creatives, %d landing pages, %d insights, %d platforms",
            len(seed_campaigns),
            8,
            len(seed_campaigns) * 2,
            6,
            4,
        )

    finally:
        db.close()


def _seed_platforms(db, platforms_data: list[dict]) -> dict[str, AdPlatformModel]:
    """Create ad platform records and return a platform_type -> model mapping."""
    platforms = {}
    for p in platforms_data:
        platform = AdPlatformModel(**p)
        db.add(platform)
        db.flush()
        platforms[p["platform_type"]] = platform
    return platforms


def _seed_campaigns(db, campaigns_data: list[dict]) -> list[CampaignModel]:
    """Create campaign records and return the list of created models."""
    seed_campaigns = []
    for c in campaigns_data:
        cpa_val = float(c["spent"] / c["conversions"]) if c["conversions"] > 0 else 0
        roas_val = float(c["revenue"] / c["spent"]) if c["spent"] > 0 else 0
        ctr_val = float(c["clicks"] / c["impressions"] * 100) if c["impressions"] > 0 else 0

        campaign = CampaignModel(
            name=c["name"],
            platform=c["platform"],
            status=c["status"],
            daily_budget=c["daily_budget"],
            total_budget=c["total_budget"],
            spent=c["spent"],
            impressions=c["impressions"],
            clicks=c["clicks"],
            conversions=c["conversions"],
            cpa=round(cpa_val, 2),
            roas=round(roas_val, 2),
            revenue=c["revenue"],
            ctr=round(ctr_val, 2),
            start_date=c["start_date"],
        )
        db.add(campaign)
        db.flush()
        seed_campaigns.append(campaign)
    return seed_campaigns


def _seed_creatives(db, campaigns: list[CampaignModel]) -> None:
    """Create creative records for the first 4 campaigns."""
    creative_data = [
        {
            "headline": "Get Your Free Marketing Guide Now",
            "body": "Download our comprehensive guide to affiliate marketing success.",
            "cta": "Download Free Guide",
        },
        {
            "headline": "Limited Time Offer - Join Today",
            "body": "Exclusive access to premium marketing resources.",
            "cta": "Join Now",
        },
    ]

    for idx, campaign in enumerate(campaigns[:4]):
        for _ in range(2):
            tmpl = creative_data[idx % len(creative_data)]
            imp = 20000
            cl = int(imp * 0.03)
            cv = int(cl * 0.05)
            sp = float(campaign.spent) * 0.15
            cpa_val = sp / cv if cv > 0 else 0
            roas_val = float(campaign.revenue) * 0.15 / sp if sp > 0 else 0

            creative = CreativeModel(
                campaign_id=campaign.id,
                platform=campaign.platform,
                headline=tmpl["headline"],
                body=tmpl["body"],
                cta=tmpl["cta"],
                impressions=imp,
                clicks=cl,
                conversions=cv,
                spend=round(sp, 2),
                cpa=round(cpa_val, 2),
                roas=round(roas_val, 2),
                ctr=round(cl / imp * 100, 2),
                ai_score=round(0.5 + (idx * 0.1), 2),
            )
            db.add(creative)


def _seed_landing_pages(db, campaigns: list[CampaignModel]) -> None:
    """Create landing page records for the first 6 campaigns."""
    landing_page_urls = [
        "https://example.com/affiliate-guide",
        "https://example.com/free-trial",
        "https://example.com/webinar-registration",
        "https://example.com/demo-request",
    ]

    for campaign in campaigns[:6]:
        for url in landing_page_urls[:2]:
            visits = int(campaign.clicks * 0.8)
            conversions = int(visits * 0.04)
            revenue = float(campaign.revenue) * 0.2
            cost = float(campaign.spent) * 0.2

            lp = LandingPageModel(
                campaign_id=campaign.id,
                url=url,
                platform=campaign.platform,
                visits=visits,
                unique_visits=int(visits * 0.75),
                conversions=conversions,
                conversion_rate=round(conversions / visits * 100 if visits > 0 else 0, 2),
                revenue=round(revenue, 2),
                cost=round(cost, 2),
                roas=round(revenue / cost if cost > 0 else 0, 2),
                bounce_rate=round(0.35 + (conversions / visits) * 0.5, 2),
                avg_time_on_page=round(120 + (conversions / visits) * 100, 2),
            )
            db.add(lp)


def _seed_insights(db, campaigns: list[CampaignModel]) -> None:
    """Create insight/recommendation/anomaly records."""
    insights_data = [
        {
            "type": "insight",
            "severity": "info",
            "title": "Meta Ads retargeting outperforming prospecting 2.4x",
            "description": (
                "Retargeting campaigns show 2.4x higher ROAS and 35% lower CPA "
                "compared to prospecting campaigns. Consider increasing "
                "retargeting budget allocation."
            ),
            "platform": "meta",
            "campaign_id": campaigns[1].id,
        },
        {
            "type": "recommendation",
            "severity": "high",
            "title": "Increase budget on 'Google Ads - Search' campaign",
            "description": (
                "Campaign is hitting daily budget cap by 2 PM consistently. "
                "Increasing budget by 30% could capture additional high-intent "
                "traffic during evening hours."
            ),
            "platform": "google",
            "campaign_id": campaigns[3].id,
            "metric_name": "daily_budget",
            "current_value": 300.0,
            "previous_value": 250.0,
            "threshold": 250.0,
        },
        {
            "type": "anomaly",
            "severity": "medium",
            "title": "CTR decline detected on 'Google Ads - Display' campaign",
            "description": (
                "CTR dropped from 1.8% to 1.2% over the past week. "
                "This may indicate creative fatigue. Consider refreshing ad creatives."
            ),
            "platform": "google",
            "campaign_id": campaigns[4].id,
            "metric_name": "ctr",
            "current_value": 1.2,
            "previous_value": 1.8,
            "threshold": 1.5,
        },
        {
            "type": "insight",
            "severity": "info",
            "title": "SMS signup campaigns showing strong ROI",
            "description": (
                "SMS-focused campaigns have 35% higher conversion rates "
                "and 28% lower CPA vs email-focused campaigns. Consider "
                "reallocating budget toward SMS channels."
            ),
            "platform": "meta",
            "campaign_id": campaigns[2].id,
        },
        {
            "type": "recommendation",
            "severity": "low",
            "title": "Test TikTok creative formats",
            "description": (
                "TikTok campaigns are still ramping up. Test Spark Ads "
                "and Branded Mission formats to improve engagement rates."
            ),
            "platform": "tiktok",
            "campaign_id": campaigns[7].id,
        },
        {
            "type": "alert",
            "severity": "critical",
            "title": "Taboola campaign approaching budget overspend",
            "description": (
                "Campaign has spent 85% of monthly budget with 10 days remaining. "
                "Review pacing and adjust daily budget if needed."
            ),
            "platform": "taboola",
            "campaign_id": campaigns[6].id,
            "metric_name": "spend",
            "current_value": 1200.0,
            "previous_value": 900.0,
            "threshold": 1020.0,
        },
    ]

    for insight in insights_data:
        ins = InsightModel(**insight)
        db.add(ins)
