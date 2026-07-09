"""Tests for the AnomalyDetector service.

Regression tests covering the core detection logic: zero-impression
campaigns, CPA spikes, ROAS declines, and spend acceleration.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.campaign import CampaignModel
from app.services.anomaly_detector import AnomalyDetector


class TestAnomalyDetector:
    """Direct unit tests for AnomalyDetector business logic."""

    def test_zero_impressions_with_spend_returns_critical(self, db_session: Session) -> None:
        """A campaign with spend but zero impressions gets a critical anomaly."""
        campaign = CampaignModel(
            name="No Impressions",
            platform="meta",
            status="active",
            spent=Decimal("500.00"),
            impressions=0,
        )
        db_session.add(campaign)
        db_session.commit()

        detector = AnomalyDetector()
        findings = detector._check_campaign(campaign, db_session)

        assert len(findings) == 1
        assert findings[0]["type"] == "anomaly"
        assert findings[0]["severity"] == "critical"
        assert "spend but zero impressions" in findings[0]["title"].lower()
        assert findings[0]["metric_name"] == "impressions"
        assert findings[0]["current_value"] == 0.0

    def test_zero_impressions_returns_immediately(self, db_session: Session) -> None:
        """Zero-impression case returns early and does not check other metrics."""
        campaign = CampaignModel(
            name="Only One Issue",
            platform="meta",
            status="active",
            spent=Decimal("100.00"),
            impressions=0,
            cpa=Decimal("999.00"),  # Would also trigger CPA spike
            roas=0.1,               # Would also trigger ROAS drop
        )
        db_session.add(campaign)
        db_session.commit()

        detector = AnomalyDetector()
        findings = detector._check_campaign(campaign, db_session)

        # Only the zero-impression finding — returned early
        assert len(findings) == 1
        assert findings[0]["metric_name"] == "impressions"

    def test_cpa_spike_detected(self, db_session: Session) -> None:
        """A campaign with CPA well above platform average triggers an anomaly."""
        # Seed campaigns to establish platform average CPA (~11)
        seed = CampaignModel(
            name="Avg C1", platform="meta", status="active",
            cpa=Decimal("10.00"), roas=2.0, conversions=10, spent=Decimal("100.00"),
        )
        seed2 = CampaignModel(
            name="Avg C2", platform="meta", status="active",
            cpa=Decimal("12.00"), roas=2.0, conversions=10, spent=Decimal("120.00"),
        )
        db_session.add_all([seed, seed2])
        db_session.commit()

        campaign = CampaignModel(
            name="Spiking CPA",
            platform="meta",
            status="active",
            spent=Decimal("250.00"),
            impressions=50000,
            clicks=2500,
            conversions=10,
            cpa=Decimal("50.00"),  # 4.5x the average of ~11 — well above 2.0x threshold
            roas=1.5,
        )
        db_session.add(campaign)
        db_session.commit()

        detector = AnomalyDetector()
        findings = detector._check_campaign(campaign, db_session)

        cpa_findings = [f for f in findings if f["metric_name"] == "cpa"]
        assert len(cpa_findings) == 1
        assert cpa_findings[0]["type"] == "anomaly"
        assert cpa_findings[0]["severity"] == "high"  # >2.0x avg
        assert "cpa spike" in cpa_findings[0]["title"].lower()

    def test_cpa_spike_medium_when_under_2x(self, db_session: Session) -> None:
        """CPA between 1.5x and 2.0x of average is 'medium' severity."""
        seed = CampaignModel(
            name="Avg", platform="google", status="active",
            cpa=Decimal("5.00"), roas=2.0, conversions=5, spent=Decimal("50.00"),
        )
        db_session.add(seed)
        db_session.commit()

        campaign = CampaignModel(
            name="Moderate CPA",
            platform="google",
            status="active",
            spent=Decimal("150.00"),
            impressions=50000,
            clicks=2000,
            conversions=8,
            cpa=Decimal("17.00"),  # 1.7x the average of 10 — between 1.5x and 2.0x
            roas=2.0,
        )
        db_session.add(campaign)
        db_session.commit()

        detector = AnomalyDetector()
        findings = detector._check_campaign(campaign, db_session)

        cpa_findings = [f for f in findings if f["metric_name"] == "cpa"]
        assert len(cpa_findings) == 1
        assert cpa_findings[0]["severity"] == "medium"

    def test_roas_decline_detected(self, db_session: Session) -> None:
        """A campaign with ROAS well below platform average triggers an anomaly."""
        seed = CampaignModel(
            name="Avg ROAS", platform="meta", status="active",
            roas=4.0, cpa=Decimal("5.00"), conversions=10, spent=Decimal("50.00"),
        )
        seed2 = CampaignModel(
            name="Good ROAS", platform="meta", status="active",
            roas=5.0, cpa=Decimal("5.00"), conversions=10, spent=Decimal("50.00"),
        )
        db_session.add_all([seed, seed2])
        db_session.commit()

        campaign = CampaignModel(
            name="Dropping ROAS",
            platform="meta",
            status="active",
            spent=Decimal("200.00"),
            impressions=50000,
            clicks=1000,
            conversions=5,
            cpa=Decimal("40.00"),
            roas=0.5,  # Well below 60% of average (4.5)
        )
        db_session.add(campaign)
        db_session.commit()

        detector = AnomalyDetector()
        findings = detector._check_campaign(campaign, db_session)

        roas_findings = [f for f in findings if f["metric_name"] == "roas"]
        assert len(roas_findings) == 1
        assert roas_findings[0]["type"] == "anomaly"
        assert roas_findings[0]["severity"] == "high"
        assert "roas" in roas_findings[0]["title"].lower()

    def test_spend_acceleration_detected(self, db_session: Session) -> None:
        """Campaign spending well above expected triggers a spend alert."""
        campaign = CampaignModel(
            name="Fast Spender",
            platform="meta",
            status="active",
            spent=Decimal("5000.00"),
            daily_budget=Decimal("100.00"),
            impressions=100000,
            clicks=5000,
            conversions=50,
            cpa=Decimal("100.00"),
            roas=2.0,
            start_date=datetime.now(UTC) - timedelta(days=30),  # expected: $100 * 30 = $3000
        )
        db_session.add(campaign)
        db_session.commit()

        detector = AnomalyDetector()
        findings = detector._check_campaign(campaign, db_session)

        spend_findings = [f for f in findings if f["metric_name"] == "spend"]
        assert len(spend_findings) == 1
        assert spend_findings[0]["type"] == "alert"
        assert spend_findings[0]["severity"] == "medium"
        assert "higher than expected spend" in spend_findings[0]["title"].lower()

    def test_healthy_campaign_no_anomalies(self, db_session: Session) -> None:
        """A well-performing campaign returns no findings."""
        seed = CampaignModel(
            name="Avg", platform="meta", status="active",
            cpa=Decimal("10.00"), roas=3.0, conversions=10, spent=Decimal("100.00"),
        )
        db_session.add(seed)
        db_session.commit()

        campaign = CampaignModel(
            name="Healthy",
            platform="meta",
            status="active",
            spent=Decimal("200.00"),
            daily_budget=Decimal("100.00"),
            impressions=100000,
            clicks=5000,
            conversions=50,
            cpa=Decimal("4.00"),        # Below average — no spike
            roas=3.5,                     # In line with average — no drop
            revenue=Decimal("700.00"),
            start_date=datetime.now(UTC) - timedelta(days=5),
        )
        db_session.add(campaign)
        db_session.commit()

        detector = AnomalyDetector()
        findings = detector._check_campaign(campaign, db_session)

        assert len(findings) == 0

    def test_detect_anomalies_queries_active_only(self, db_session: Session) -> None:
        """detect_anomalies only checks campaigns with status 'active'."""
        paused = CampaignModel(
            name="Paused", platform="meta", status="paused",
            spent=Decimal("500.00"), impressions=0,  # Should trigger but is paused
        )
        active_bad = CampaignModel(
            name="Active Bad", platform="meta", status="active",
            spent=Decimal("100.00"), impressions=0,
        )
        db_session.add_all([paused, active_bad])
        db_session.commit()

        detector = AnomalyDetector()
        anomalies = detector.detect_anomalies(db_session)

        # Only the active campaign with zero impressions should be detected
        assert len(anomalies) == 1
        assert anomalies[0]["campaign_id"] == active_bad.id

    def test_days_since_start_with_start_date(self, _db_session: Session) -> None:  # noqa: E501
        """_days_since_start returns days since campaign start_date."""
        campaign = CampaignModel(
            name="Dated", platform="meta", status="active",
            start_date=datetime.now(UTC) - timedelta(days=10),
        )
        detector = AnomalyDetector()
        days = detector._days_since_start(campaign)
        assert days == 10

    def test_days_since_start_without_date(self, _db_session: Session) -> None:  # noqa: E501
        """_days_since_start defaults to 7 when no start_date is set."""
        campaign = CampaignModel(
            name="No Date", platform="meta", status="active",
        )
        detector = AnomalyDetector()
        days = detector._days_since_start(campaign)
        assert days == 7

    def test_spend_acceleration_below_threshold(self, db_session: Session) -> None:
        """Campaign spending within expected range does not trigger an alert."""
        campaign = CampaignModel(
            name="On Budget",
            platform="meta",
            status="active",
            spent=Decimal("3200.00"),
            daily_budget=Decimal("100.00"),
            impressions=100000,
            clicks=5000,
            conversions=50,
            cpa=Decimal("64.00"),
            roas=2.0,
            start_date=datetime.now(UTC) - timedelta(days=30),  # expected: $3000, actual: $3200 (just 6.7% over)  # noqa: E501
        )
        db_session.add(campaign)
        db_session.commit()

        detector = AnomalyDetector()
        findings = detector._check_campaign(campaign, db_session)

        spend_findings = [f for f in findings if f["metric_name"] == "spend"]
        assert len(spend_findings) == 0

    def test_anomaly_detector_singleton_available(self) -> None:
        """The module-level singleton is importable and has expected type."""
        from app.services.anomaly_detector import anomaly_detector
        assert isinstance(anomaly_detector, AnomalyDetector)
