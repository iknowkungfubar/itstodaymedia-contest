from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.campaign import CampaignModel


class TestCampaigns:
    """Test campaign CRUD operations."""

    def test_list_campaigns_empty(self, client: TestClient) -> None:
        """GET /api/campaigns returns empty list when no campaigns exist."""
        response = client.get("/api/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_create_campaign(self, client: TestClient) -> None:
        """POST /api/campaigns creates a new campaign."""
        payload = {
            "name": "Test Campaign",
            "platform": "meta",
            "status": "active",
            "daily_budget": 100.0,
        }
        response = client.post("/api/campaigns", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert data["platform"] == "meta"
        assert data["status"] == "active"
        assert data["daily_budget"] == 100.0
        assert "id" in data

    def test_get_campaign(self, client: TestClient) -> None:
        """GET /api/campaigns/:id returns the campaign."""
        create_resp = client.post("/api/campaigns", json={
            "name": "Get Test",
            "platform": "google",
        })
        campaign_id = create_resp.json()["id"]

        response = client.get(f"/api/campaigns/{campaign_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"

    def test_get_campaign_not_found(self, client: TestClient) -> None:
        """GET /api/campaigns/:id returns 404 for missing campaign."""
        response = client.get("/api/campaigns/9999")
        assert response.status_code == 404

    def test_update_campaign(self, client: TestClient) -> None:
        """PUT /api/campaigns/:id updates the campaign."""
        create_resp = client.post("/api/campaigns", json={
            "name": "Before Update",
            "platform": "meta",
        })
        campaign_id = create_resp.json()["id"]

        response = client.put(
            f"/api/campaigns/{campaign_id}",
            json={"name": "After Update", "status": "paused"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "After Update"
        assert data["status"] == "paused"

    def test_delete_campaign(self, client: TestClient) -> None:
        """DELETE /api/campaigns/:id removes the campaign."""
        create_resp = client.post("/api/campaigns", json={
            "name": "To Delete",
            "platform": "tiktok",
        })
        campaign_id = create_resp.json()["id"]

        response = client.delete(f"/api/campaigns/{campaign_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_resp = client.get(f"/api/campaigns/{campaign_id}")
        assert get_resp.status_code == 404

    def test_list_campaigns_pagination(self, client: TestClient) -> None:
        """GET /api/campaigns supports pagination."""
        for i in range(5):
            client.post("/api/campaigns", json={
                "name": f"Campaign {i}",
                "platform": "meta",
            })

        # Page 1 with 2 items
        response = client.get("/api/campaigns?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

    def test_create_campaign_validation(self, client: TestClient) -> None:
        """POST /api/campaigns validates required fields."""
        response = client.post("/api/campaigns", json={"platform": "meta"})
        assert response.status_code == 422

    def test_create_campaign_invalid_platform(self, client: TestClient) -> None:
        """POST /api/campaigns rejects invalid platform values."""
        response = client.post("/api/campaigns", json={
            "name": "Bad Platform",
            "platform": "snapchat",
        })
        assert response.status_code == 422

    def test_summary_endpoint(self, client: TestClient, db_session: Session) -> None:
        """GET /api/campaigns/summary returns aggregate stats."""
        # Add some test campaigns
        campaigns = [
            CampaignModel(name="C1", platform="meta", status="active",
                          spent=100.0, impressions=1000, clicks=50,
                          conversions=10, revenue=200.0),
            CampaignModel(name="C2", platform="google", status="active",
                          spent=200.0, impressions=2000, clicks=100,
                          conversions=20, revenue=600.0),
        ]
        for c in campaigns:
            db_session.add(c)
        db_session.commit()

        response = client.get("/api/campaigns/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_campaigns"] == 2
        assert data["active_campaigns"] == 2
        assert data["total_spent"] == 300.0
        assert "by_platform" in data
