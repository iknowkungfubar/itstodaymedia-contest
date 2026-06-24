from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.insight import InsightModel


class TestInsights:
    """Test insight and anomaly detection endpoints."""

    def test_list_insights_empty(self, client: TestClient) -> None:
        """GET /api/insights returns empty list when no insights exist."""
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["unread_count"] == 0
        assert data["items"] == []

    def test_scan_anomalies_no_campaigns(self, client: TestClient) -> None:
        """POST /api/insights/scan returns empty list when no campaigns."""
        response = client.post("/api/insights/scan")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_and_mark_read(self, client: TestClient, db_session: Session) -> None:
        """PUT /api/insights/:id/read marks insight as read."""
        insight = InsightModel(
            type="insight",
            severity="info",
            title="Test Insight",
            description="Test description",
            platform="meta",
        )
        db_session.add(insight)
        db_session.commit()
        insight_id = insight.id

        response = client.put(f"/api/insights/{insight_id}/read")
        assert response.status_code == 200
        assert response.json()["is_read"] is True

    def test_list_with_filters(self, client: TestClient, db_session: Session) -> None:
        """GET /api/insights supports filtering."""
        insights = [
            InsightModel(type="anomaly", severity="high", title="Anomaly 1",
                         description="Desc", platform="meta"),
            InsightModel(type="recommendation", severity="info", title="Rec 1",
                         description="Desc", platform="google"),
            InsightModel(type="insight", severity="low", title="Insight 1",
                         description="Desc", platform="tiktok"),
        ]
        for ins in insights:
            db_session.add(ins)
        db_session.commit()

        response = client.get("/api/insights?type=anomaly")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["type"] == "anomaly"
