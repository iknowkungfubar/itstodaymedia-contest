from __future__ import annotations

from fastapi.testclient import TestClient


class TestCreatives:
    """Test creative CRUD and AI analysis."""

    def setup_campaign(self, client: TestClient) -> int:
        """Helper to create a campaign and return its ID."""
        resp = client.post(
            "/api/campaigns",
            json={
                "name": "Creative Test Campaign",
                "platform": "meta",
            },
        )
        return resp.json()["id"]

    def test_list_creatives_empty(self, client: TestClient) -> None:
        """GET /api/creatives returns empty list when no creatives exist."""
        response = client.get("/api/creatives")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_creative(self, client: TestClient) -> None:
        """POST /api/creatives creates a new creative."""
        campaign_id = self.setup_campaign(client)
        payload = {
            "campaign_id": campaign_id,
            "platform": "meta",
            "headline": "Test Headline",
            "body": "Test body text",
            "cta": "Click Here",
        }
        response = client.post("/api/creatives", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["headline"] == "Test Headline"
        assert data["campaign_id"] == campaign_id

    def test_analyze_creatives(self, client: TestClient) -> None:
        """POST /api/creatives/analyze runs AI analysis on creatives."""
        campaign_id = self.setup_campaign(client)

        # Create two creatives
        c1 = client.post(
            "/api/creatives",
            json={
                "campaign_id": campaign_id,
                "platform": "meta",
                "headline": "Get Your Free Guide Now",
                "body": "Download the ultimate guide",
                "cta": "Download Free",
            },
        ).json()

        c2 = client.post(
            "/api/creatives",
            json={
                "campaign_id": campaign_id,
                "platform": "meta",
                "headline": "Limited Time Offer",
                "body": "Don't miss this exclusive deal",
                "cta": "Shop Now",
            },
        ).json()

        response = client.post(
            "/api/creatives/analyze",
            json={
                "creative_ids": [c1["id"], c2["id"]],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for analysis in data:
            assert "ai_score" in analysis
            assert "strengths" in analysis
            assert "weaknesses" in analysis
            assert "recommendations" in analysis
            assert isinstance(analysis["ai_score"], float)
