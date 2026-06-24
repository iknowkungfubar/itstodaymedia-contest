"""CampaignPulse — AI-Powered Campaign Intelligence Platform.

FastAPI backend providing unified campaign management, AI creative analysis,
budget optimization, landing page tracking, and automated anomaly detection.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal, engine
from app.models import Base
from app.models.ad_platform import AdPlatformModel
from app.models.campaign import CampaignModel
from app.models.creative import CreativeModel
from app.models.insight import InsightModel
from app.models.landing_page import LandingPageModel

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s %(name)s  %(message)s",
)
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
        platforms = {}
        for p in platforms_data:
            platform = AdPlatformModel(**p)
            db.add(platform)
            db.flush()
            platforms[p["platform_type"]] = platform

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

        # --- Creatives ---
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

        for idx, campaign in enumerate(seed_campaigns[:4]):  # First 4 campaigns get mock data
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

        # --- Landing Pages ---
        landing_page_urls = [
            "https://example.com/affiliate-guide",
            "https://example.com/free-trial",
            "https://example.com/webinar-registration",
            "https://example.com/demo-request",
        ]

        for campaign in seed_campaigns[:6]:
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

        # --- Insights ---
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
                "campaign_id": seed_campaigns[1].id,
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
                "campaign_id": seed_campaigns[3].id,
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
                "campaign_id": seed_campaigns[4].id,
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
                "campaign_id": seed_campaigns[2].id,
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
                "campaign_id": seed_campaigns[7].id,
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
                "campaign_id": seed_campaigns[6].id,
                "metric_name": "spend",
                "current_value": 1200.0,
                "previous_value": 900.0,
                "threshold": 1020.0,
            },
        ]

        for insight in insights_data:
            ins = InsightModel(**insight)
            db.add(ins)

        db.commit()
        logger.info(
            "Seeded %d campaigns, %d creatives, %d landing pages, %d insights, %d platforms",
            len(seed_campaigns),
            8,
            len(seed_campaigns) * 2,
            len(insights_data),
            len(platforms_data),
        )

    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: create tables and seed demo data on startup."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    logger.info("CampaignPulse backend started successfully")
    yield


app = FastAPI(
    title="CampaignPulse API",
    description="AI-powered campaign intelligence platform for media buyers",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.routes.budget import router as budget_router  # noqa: E402
from app.routes.campaigns import router as campaigns_router  # noqa: E402
from app.routes.creatives import router as creatives_router  # noqa: E402
from app.routes.insights import router as insights_router  # noqa: E402
from app.routes.landing_pages import router as landing_pages_router  # noqa: E402
from app.routes.platforms import router as platforms_router  # noqa: E402

app.include_router(campaigns_router)
app.include_router(creatives_router)
app.include_router(platforms_router)
app.include_router(budget_router)
app.include_router(landing_pages_router)
app.include_router(insights_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "CampaignPulse API"}
