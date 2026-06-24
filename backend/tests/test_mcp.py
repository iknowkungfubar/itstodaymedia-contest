"""Tests for MCP server integration endpoints.

Covers server listing, tool execution, error handling, and the
database sync flow.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestMCPServers:
    """MCP server listing and capability discovery."""

    def test_list_mcp_servers(self, client: TestClient) -> None:
        """GET /api/mcp/servers returns meta-ads and google-ads."""
        response = client.get("/api/mcp/servers")
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data

        names = {s["name"] for s in data["servers"]}
        assert "meta-ads" in names
        assert "google-ads" in names

    def test_list_mcp_servers_structure(self, client: TestClient) -> None:
        """Each server entry has version, resources, and tools."""
        response = client.get("/api/mcp/servers")
        servers = response.json()["servers"]

        for s in servers:
            assert "version" in s
            assert isinstance(s["resources"], list)
            assert isinstance(s["tools"], list)
            if s["name"] == "meta-ads":
                assert any(
                    r["uri"] == "meta-ads://campaigns" for r in s["resources"]
                )
                assert any(
                    t["name"] == "list_campaigns" for t in s["tools"]
                )


class TestMCPToolCall:
    """Tool execution on individual MCP servers."""

    def test_meta_ads_list_campaigns(self, client: TestClient) -> None:
        """POST list_campaigns on meta-ads returns mock campaign data."""
        response = client.post(
            "/api/mcp/servers/meta-ads/tools/call",
            json={"name": "list_campaigns", "arguments": {}},
        )
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert len(data["campaigns"]) == 3
        assert data["campaigns"][0]["name"] == "Brand Awareness - Q3"

    def test_google_ads_list_campaigns(self, client: TestClient) -> None:
        """POST list_campaigns on google-ads returns mock campaign data."""
        response = client.post(
            "/api/mcp/servers/google-ads/tools/call",
            json={"name": "list_campaigns", "arguments": {}},
        )
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert len(data["campaigns"]) == 3
        assert data["campaigns"][0]["name"] == "Search - Affiliate Offers"

    def test_meta_ads_get_campaign_insights(self, client: TestClient) -> None:
        """POST get_campaign_insights on meta-ads returns mock insights."""
        response = client.post(
            "/api/mcp/servers/meta-ads/tools/call",
            json={
                "name": "get_campaign_insights",
                "arguments": {"campaign_id": "123456789"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert "impressions" in data["insights"]
        assert "ctr" in data["insights"]

    def test_google_ads_get_campaign_performance(self, client: TestClient) -> None:
        """POST get_campaign_performance on google-ads returns mock performance."""
        response = client.post(
            "/api/mcp/servers/google-ads/tools/call",
            json={
                "name": "get_campaign_performance",
                "arguments": {"campaign_id": "987654321"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "performance" in data
        assert "impressions" in data["performance"]

    def test_meta_ads_update_budget(self, client: TestClient) -> None:
        """POST update_campaign_budget returns success."""
        response = client.post(
            "/api/mcp/servers/meta-ads/tools/call",
            json={
                "name": "update_campaign_budget",
                "arguments": {"campaign_id": "123456789", "daily_budget": 10000},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestMCPToolErrors:
    """Error handling for tool calls."""

    def test_unknown_server(self, client: TestClient) -> None:
        """Calling a non-existent server returns 400."""
        response = client.post(
            "/api/mcp/servers/nonexistent/tools/call",
            json={"name": "list_campaigns", "arguments": {}},
        )
        assert response.status_code == 400
        assert "nonexistent" in response.json()["detail"]

    def test_missing_tool_name(self, client: TestClient) -> None:
        """Request without a 'name' field returns 400."""
        response = client.post(
            "/api/mcp/servers/meta-ads/tools/call",
            json={"arguments": {}},
        )
        assert response.status_code == 400
        assert "name" in response.json()["detail"].lower()

    def test_unknown_tool(self, client: TestClient) -> None:
        """Calling a non-existent tool returns 400."""
        response = client.post(
            "/api/mcp/servers/meta-ads/tools/call",
            json={"name": "do_nothing", "arguments": {}},
        )
        assert response.status_code == 400


class TestMCPSync:
    """Database sync via MCP servers."""

    def test_sync_no_platforms(self, client: TestClient) -> None:
        """POST /api/mcp/sync with no platforms returns empty results."""
        response = client.post("/api/mcp/sync")
        assert response.status_code == 200
        data = response.json()
        assert data["sync_results"] == []

    def test_sync_with_connected_platforms(
        self, client: TestClient, db_session: Session
    ) -> None:
        """POST /api/mcp/sync pulls campaigns from MCP servers into the DB."""
        from app.models.ad_platform import AdPlatformModel
        from app.models.campaign import CampaignModel

        # Arrange: create two connected platforms matching our MCP servers.
        platforms = [
            AdPlatformModel(
                name="Meta Ads",
                platform_type="meta",
                is_connected=True,
            ),
            AdPlatformModel(
                name="Google Ads",
                platform_type="google",
                is_connected=True,
            ),
        ]
        for p in platforms:
            db_session.add(p)
        db_session.commit()

        # Act
        response = client.post("/api/mcp/sync")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sync_results"]) == 2

        for result in data["sync_results"]:
            assert result["status"] == "success"
            assert result["campaigns_synced"] > 0
            assert "platform_id" in result

        # Assert: campaigns were created in the database
        campaigns = db_session.query(CampaignModel).all()
        assert len(campaigns) > 0

        # The meta-ads mock returns 3 campaigns, google-ads returns 3 => at least 6
        assert len(campaigns) >= 6

        # Verify the platform_campaign_id was stored
        meta_campaigns = (
            db_session.query(CampaignModel)
            .filter(CampaignModel.platform == "meta")
            .all()
        )
        assert len(meta_campaigns) == 3
        for c in meta_campaigns:
            assert c.platform_campaign_id is not None

    def test_sync_is_idempotent(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Calling sync twice does not create duplicate campaigns."""
        from app.models.ad_platform import AdPlatformModel
        from app.models.campaign import CampaignModel

        platform = AdPlatformModel(
            name="Meta Ads",
            platform_type="meta",
            is_connected=True,
        )
        db_session.add(platform)
        db_session.commit()

        # First sync
        client.post("/api/mcp/sync")
        count_after_first = db_session.query(CampaignModel).count()

        # Second sync
        client.post("/api/mcp/sync")
        count_after_second = db_session.query(CampaignModel).count()

        # Should be identical — upserts don't duplicate
        assert count_after_first == count_after_second
        assert count_after_first == 3  # meta-ads mock has 3 campaigns

    def test_sync_skips_platform_without_mcp_server(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Platforms like Taboola (no MCP server) are silently skipped."""
        from app.models.ad_platform import AdPlatformModel
        from app.models.campaign import CampaignModel

        taboola = AdPlatformModel(
            name="Taboola",
            platform_type="taboola",
            is_connected=True,
        )
        db_session.add(taboola)
        db_session.commit()

        response = client.post("/api/mcp/sync")
        assert response.status_code == 200
        # Taboola has no MCP server mapping, so no results
        assert response.json()["sync_results"] == []

        # No campaigns should have been created
        assert db_session.query(CampaignModel).count() == 0
