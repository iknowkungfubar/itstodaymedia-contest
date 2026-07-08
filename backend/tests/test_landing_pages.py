from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.landing_page import LandingPageModel


class TestLandingPages:
    """Test landing page tracking endpoints."""

    def setup_campaign(self, client: TestClient) -> int:
        """Helper to create a campaign and return its ID."""
        resp = client.post(
            "/api/campaigns",
            json={
                "name": "LP Test Campaign",
                "platform": "meta",
            },
        )
        return resp.json()["id"]

    def test_list_landing_pages_empty(self, client: TestClient) -> None:
        """GET /api/landing-pages returns empty list."""
        response = client.get("/api/landing-pages")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_landing_page(self, client: TestClient) -> None:
        """POST /api/landing-pages creates a landing page entry."""
        campaign_id = self.setup_campaign(client)
        response = client.post(
            "/api/landing-pages",
            json={
                "campaign_id": campaign_id,
                "platform": "meta",
                "url": "https://example.com/test",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://example.com/test"
        assert data["campaign_id"] == campaign_id

    def test_performance_summary(self, client: TestClient, db_session: Session) -> None:
        """GET /api/landing-pages/summary/performance returns aggregate stats."""
        # Need a campaign first
        camp_resp = client.post(
            "/api/campaigns",
            json={
                "name": "LP Summary Campaign",
                "platform": "meta",
            },
        )
        campaign_id = camp_resp.json()["id"]

        pages = [
            LandingPageModel(
                campaign_id=campaign_id,
                platform="meta",
                url="https://example.com/a",
                visits=1000,
                conversions=50,
                revenue=500.0,
                cost=100.0,
            ),
            LandingPageModel(
                campaign_id=campaign_id,
                platform="meta",
                url="https://example.com/b",
                visits=500,
                conversions=40,
                revenue=400.0,
                cost=80.0,
            ),
        ]
        for p in pages:
            db_session.add(p)
        db_session.commit()

        response = client.get("/api/landing-pages/summary/performance")
        assert response.status_code == 200
        data = response.json()
        assert data["total_visits"] == 1500
        assert data["total_conversions"] == 90
        assert data["total_revenue"] == 900.0
