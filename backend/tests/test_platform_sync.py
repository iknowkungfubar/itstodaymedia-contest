"""Tests for the PlatformSyncService.

Regression tests covering the core sync logic: missing-platform
error handling and successful sync flow that exercises the full
mock data generation pipeline.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ad_platform import AdPlatformModel
from app.services.platform_sync import PlatformSyncService


class TestPlatformSyncService:
    """Direct unit tests for PlatformSyncService business logic."""

    def test_sync_platform_not_found_returns_error(self, db_session: Session) -> None:
        """Calling sync_platform with a non-existent ID returns an error status."""
        service = PlatformSyncService()
        result = service.sync_platform(platform_id=9999, db=db_session)

        assert result["status"] == "error"
        assert result["campaigns_synced"] == 0
        assert "platf" in result["message"].lower()  # "Platform not found"
        assert result["platform_id"] == 9999

    def test_sync_platform_with_valid_platform_generates_data(
        self, db_session: Session
    ) -> None:
        """A valid platform sync updates last_sync_at and generates campaigns.

        This exercises the full pipeline: sync_platform -> _generate_mock_campaigns
        -> _generate_mock_creatives -> _generate_mock_landing_pages.
        """
        platform = AdPlatformModel(
            name="Test Meta",
            platform_type="meta",
            is_connected=True,
        )
        db_session.add(platform)
        db_session.commit()
        platform_id = platform.id

        result = PlatformSyncService().sync_platform(
            platform_id=platform_id, db=db_session
        )

        # Result shape
        assert result["status"] == "success"
        assert result["platform_id"] == platform.id
        assert result["platform_name"] == "Test Meta"
        assert result["campaigns_synced"] > 0

        # last_sync_at was updated
        db_session.refresh(platform)
        assert platform.last_sync_at is not None

        # Campaigns, creatives, and landing pages were created in the DB
        from app.models.campaign import CampaignModel
        from app.models.creative import CreativeModel
        from app.models.landing_page import LandingPageModel

        campaigns = (
            db_session.query(CampaignModel)
            .filter(CampaignModel.platform == "meta")
            .all()
        )
        assert len(campaigns) == result["campaigns_synced"]

        for campaign in campaigns:
            assert campaign.name.startswith("Meta Ads")
            assert campaign.status in ("active", "paused")
            assert campaign.impressions > 0
            assert campaign.clicks > 0
            assert campaign.spent > 0

            creatives = (
                db_session.query(CreativeModel)
                .filter(CreativeModel.campaign_id == campaign.id)
                .all()
            )
            assert len(creatives) >= 2, (
                f"Expected at least 2 creatives per campaign, got {len(creatives)}"
            )

            landing_pages = (
                db_session.query(LandingPageModel)
                .filter(LandingPageModel.campaign_id == campaign.id)
                .all()
            )
            assert len(landing_pages) >= 1, (
                f"Expected at least 1 landing page per campaign, "
                f"got {len(landing_pages)}"
            )

    def test_sync_platform_with_unsupported_type_returns_zero(
        self, db_session: Session
    ) -> None:
        """An unsupported platform type generates no campaigns but reports success."""
        platform = AdPlatformModel(
            name="Snapchat",
            platform_type="snapchat",
            is_connected=True,
        )
        db_session.add(platform)
        db_session.commit()

        result = PlatformSyncService().sync_platform(
            platform_id=platform.id, db=db_session
        )

        # Still succeeds because the platform exists and was updated
        assert result["status"] == "success"
        # But no campaigns generated (unsupported type logs a warning)
        assert result["campaigns_synced"] == 0

    def test_sync_platform_duplicate_names_skipped(
        self, db_session: Session
    ) -> None:
        """Existing campaign names are skipped during re-sync.

        The random subset of templates means a second sync may generate fewer
        campaigns than the first (existing names are skipped), but it must
        NOT generate duplicates of already-present names.
        """
        platform = AdPlatformModel(
            name="Google Dupe",
            platform_type="google",
            is_connected=True,
        )
        db_session.add(platform)
        db_session.commit()

        service = PlatformSyncService()

        # First sync
        first = service.sync_platform(platform_id=platform.id, db=db_session)
        assert first["campaigns_synced"] > 0

        from app.models.campaign import CampaignModel

        names_before = {
            row[0]
            for row in db_session.query(CampaignModel.name)
            .filter(CampaignModel.platform == "google")
            .all()
        }

        # Second sync — existing names are skipped
        second = service.sync_platform(platform_id=platform.id, db=db_session)

        names_after = {
            row[0]
            for row in db_session.query(CampaignModel.name)
            .filter(CampaignModel.platform == "google")
            .all()
        }

        # No new campaign names were introduced (duplicates were skipped)
        assert names_after == names_before, (
            f"Second sync introduced new campaign names: "
            f"{names_after - names_before}"
        )
