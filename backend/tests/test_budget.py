from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.campaign import CampaignModel


class TestBudget:
    """Test budget optimization endpoints."""

    def test_budget_recommendations_empty(self, client: TestClient) -> None:
        """GET /api/budget/recommendations returns empty when no campaigns."""
        response = client.get("/api/budget/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert data["recommendations"] == []

    def test_budget_recommendations_with_campaigns(
        self, client: TestClient, db_session: Session
    ) -> None:
        """GET /api/budget/recommendations returns recommendations."""
        campaigns = [
            CampaignModel(
                name="High Performer",
                platform="meta",
                status="active",
                daily_budget=200.0,
                spent=3000.0,
                impressions=200000,
                clicks=10000,
                conversions=500,
                cpa=6.0,
                roas=5.0,
                revenue=15000.0,
                ctr=5.0,
            ),
            CampaignModel(
                name="Low Performer",
                platform="google",
                status="active",
                daily_budget=200.0,
                spent=3000.0,
                impressions=50000,
                clicks=500,
                conversions=20,
                cpa=150.0,
                roas=0.5,
                revenue=1500.0,
                ctr=1.0,
            ),
            CampaignModel(
                name="Paused Campaign",
                platform="meta",
                status="paused",
                daily_budget=100.0,
                spent=1000.0,
                impressions=50000,
                clicks=2500,
                conversions=100,
                cpa=10.0,
                roas=2.0,
                revenue=2000.0,
                ctr=5.0,
            ),
        ]
        for c in campaigns:
            db_session.add(c)
        db_session.commit()

        response = client.get("/api/budget/recommendations")
        assert response.status_code == 200
        data = response.json()
        # Only active campaigns should be included
        assert len(data["recommendations"]) == 2
        assert data["total_current_budget"] > 0
        assert data["total_recommended_budget"] > 0
        assert data["summary"] != ""

        # High performer should get higher budget
        recs = sorted(data["recommendations"], key=lambda r: r["recommended_budget"], reverse=True)
        assert recs[0]["campaign_name"] == "High Performer"
