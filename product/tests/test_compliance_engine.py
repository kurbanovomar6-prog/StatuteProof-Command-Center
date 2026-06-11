"""
tests/test_compliance_engine.py — pytest suite for RegRadar compliance engine.

Coverage:
  1. RegulationRepository.upsert_raw_versioned — versioning / SHA-256 dedup
  2. SubscriptionRepository — subscribe, filter, last-notified
  3. DeltaAnalyzer unit — None guards, message formatters
  4. Celery task dispatch — analyze_delta_task, send_scheduled_alerts_task
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.models import AlertSubscription, Base, RegulationVersion
from app.infrastructure.db.repository import RegulationRepository, SubscriptionRepository
from services.delta_analyzer import (
    DeltaAnalysis,
    analyze_delta,
    format_delta_alert,
    format_digest,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def _engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def _session_factory(_engine):
    return sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _patch_db(_session_factory):
    with patch("app.infrastructure.db.repository.SessionLocal", _session_factory):
        yield


# ── Shared helpers ────────────────────────────────────────────────────────────

def _raw_data(url: str, summary: str, **overrides) -> dict:
    data = {
        "source_url":       url,
        "title":            "Test Regulation",
        "jurisdiction":     "RU",
        "publication_date": "2026-01-01",
        "effective_date":   "2026-03-01",
        "summary":          summary,
        "industries":       "banking",
        "critical_level":   "HIGH",
        "confidence":       0.9,
        "status":           "ACTIVE",
        "source_type":      "WEB",
    }
    data.update(overrides)
    return data


def _make_delta(
    changes: list[str] | None = None,
    impact:  str = "HIGH",
    action:  str = "Update internal compliance policy. Deadline: 2026-06-30.",
) -> DeltaAnalysis:
    return DeltaAnalysis(
        critical_changes=changes or [
            "Penalty raised to 5 M RUB",
            "New quarterly reporting added",
        ],
        impact_level=impact,
        business_action_required=action,
    )


# ── 1. Database versioning ────────────────────────────────────────────────────

class TestUpsertRawVersioned:
    def test_new_record_returns_saved_true(self):
        repo   = RegulationRepository()
        result = repo.upsert_raw_versioned(_raw_data("https://cbr.ru/v/1", "First summary"))
        assert result.saved      is True
        assert result.is_update  is False
        assert result.old_summary is None
        assert result.version_id  is not None
        assert result.record_id   is not None

    def test_identical_summary_skips_version(self):
        repo    = RegulationRepository()
        url     = "https://cbr.ru/v/2"
        summary = "Unchanging regulatory text — no edit."
        repo.upsert_raw_versioned(_raw_data(url, summary))
        second = repo.upsert_raw_versioned(_raw_data(url, summary))
        assert second.saved      is False
        assert second.is_update  is False
        assert second.version_id is None

    def test_changed_summary_triggers_update(self):
        repo   = RegulationRepository()
        url    = "https://cbr.ru/v/3"
        first  = repo.upsert_raw_versioned(_raw_data(url, "Penalty: 1 M RUB"))
        second = repo.upsert_raw_versioned(_raw_data(url, "Penalty: 5 M RUB"))
        assert second.saved       is True
        assert second.is_update   is True
        assert second.old_summary == "Penalty: 1 M RUB"
        assert second.record_id   == first.record_id
        assert second.version_id  is not None

    def test_version_numbers_increment_sequentially(self, _session_factory):
        repo = RegulationRepository()
        url  = "https://cbr.ru/v/4"
        repo.upsert_raw_versioned(_raw_data(url, "Text A"))
        repo.upsert_raw_versioned(_raw_data(url, "Text B"))
        repo.upsert_raw_versioned(_raw_data(url, "Text C"))

        with _session_factory() as db:
            nums = [
                v.version_number
                for v in db.query(RegulationVersion)
                .order_by(RegulationVersion.version_number)
                .all()
            ]
        assert nums == [1, 2, 3]

    def test_get_versions_returns_12char_fingerprint(self):
        repo  = RegulationRepository()
        url   = "https://cbr.ru/v/5"
        first = repo.upsert_raw_versioned(_raw_data(url, "Alpha"))
        repo.upsert_raw_versioned(_raw_data(url, "Beta"))

        versions = repo.get_versions(first.record_id)
        assert len(versions) == 2
        for v in versions:
            assert len(v["summary_hash"]) == 12

    def test_update_version_delta_persists_delta_json(self, _session_factory):
        repo   = RegulationRepository()
        result = repo.upsert_raw_versioned(_raw_data("https://cbr.ru/v/6", "Summary"))
        delta  = _make_delta()

        repo.update_version_delta(result.version_id, delta)

        with _session_factory() as db:
            v = db.query(RegulationVersion).filter_by(id=result.version_id).first()
        assert v.delta_json   is not None
        assert v.impact_level == "HIGH"


# ── 2. Subscription filtering ─────────────────────────────────────────────────

class TestSubscriptionRepository:
    def test_new_subscription_returns_true(self):
        repo   = SubscriptionRepository()
        is_new = repo.subscribe("111", "RU,KZ", "daily", "HIGH")
        assert is_new is True

    def test_update_existing_returns_false(self):
        repo = SubscriptionRepository()
        repo.subscribe("222", "RU", "daily", "LOW")
        is_new = repo.subscribe("222", "RU,KZ", "weekly", "HIGH")
        assert is_new is False

    def test_list_active_excludes_inactive(self, _session_factory):
        repo = SubscriptionRepository()
        repo.subscribe("active_chat",   "RU", "daily", "LOW")
        repo.subscribe("inactive_chat", "KZ", "daily", "LOW")

        with _session_factory() as db:
            row = db.query(AlertSubscription).filter_by(chat_id="inactive_chat").first()
            row.is_active = False
            db.commit()

        ids = [s.chat_id for s in repo.list_active()]
        assert "active_chat"   in ids
        assert "inactive_chat" not in ids

    def test_update_last_notified_sets_timestamp(self, _session_factory):
        repo = SubscriptionRepository()
        repo.subscribe("notify_me", "RU", "daily", "LOW")
        repo.update_last_notified(["notify_me"])

        with _session_factory() as db:
            sub = db.query(AlertSubscription).filter_by(chat_id="notify_me").first()
        assert sub.last_notified_at is not None

    def test_jurisdiction_and_risk_persisted(self, _session_factory):
        repo = SubscriptionRepository()
        repo.subscribe("jur_test", "RU,AZ,BY", "weekly", "MEDIUM")

        with _session_factory() as db:
            sub = db.query(AlertSubscription).filter_by(chat_id="jur_test").first()
        assert "AZ"      in sub.jurisdictions
        assert sub.min_risk_level == "MEDIUM"
        assert sub.frequency      == "weekly"

    def test_empty_chat_ids_update_does_not_crash(self):
        repo = SubscriptionRepository()
        repo.update_last_notified([])   # must not raise


# ── 3. DeltaAnalyzer unit behaviour ──────────────────────────────────────────

class TestDeltaAnalyzerUnit:
    def test_returns_none_when_old_empty(self):
        assert analyze_delta("", "some new regulatory text") is None

    def test_returns_none_when_new_empty(self):
        assert analyze_delta("some text", "") is None

    def test_returns_none_on_identical_summaries(self):
        text = "Identical regulatory clause about reporting obligations."
        assert analyze_delta(text, text) is None

    def test_format_delta_alert_contains_impact_level(self):
        reg   = {"jurisdiction": "RU", "title": "CBR Directive № 42"}
        delta = _make_delta(impact="HIGH")
        msg   = format_delta_alert(reg, delta, "https://dash.regrada.io")
        assert "HIGH IMPACT"              in msg
        assert "Penalty raised to 5 M"   in msg
        assert "https://dash.regrada.io" in msg

    def test_format_delta_alert_medium_impact(self):
        reg   = {"jurisdiction": "KZ", "title": "NBK Order 7"}
        delta = _make_delta(impact="MEDIUM")
        msg   = format_delta_alert(reg, delta)
        assert "MEDIUM IMPACT" in msg
        assert "KZ"            in msg

    def test_format_delta_alert_no_url_when_empty(self):
        reg   = {"jurisdiction": "AZ", "title": "CBAR Notice"}
        delta = _make_delta()
        msg   = format_delta_alert(reg, delta, "")
        assert "href" not in msg

    def test_format_digest_includes_jurisdiction_and_level(self):
        regs = [
            {
                "jurisdiction":   "AZ",
                "critical_level": "CRITICAL",
                "title":          "CBAR Resolution 2026",
                "summary":        "Banks must resubmit capital ratios.",
            }
        ]
        msg = format_digest(regs, dashboard_url="https://regrada.io")
        assert "AZ"                in msg
        assert "CRITICAL"          in msg
        assert "https://regrada.io" in msg

    def test_format_digest_dashboard_link_absent_when_empty(self):
        regs = [{"jurisdiction": "RU", "critical_level": "LOW", "title": "x", "summary": ""}]
        msg  = format_digest(regs, dashboard_url="")
        assert "href" not in msg


# ── 4. Celery task dispatch ───────────────────────────────────────────────────

class TestCeleryTaskDispatch:
    def test_analyze_delta_task_ok_path(self):
        """Mocked LLM returns delta → update_version_delta called with correct args."""
        repo   = RegulationRepository()
        r      = repo.upsert_raw_versioned(_raw_data("https://cbr.ru/task/1", "Old summary"))
        ver_id = r.version_id
        delta  = _make_delta()

        with patch("services.delta_analyzer.analyze_delta", return_value=delta), \
             patch.object(RegulationRepository, "update_version_delta") as mock_upd:
            from celery_app import analyze_delta_task
            result = analyze_delta_task(version_id=ver_id, old_summary="Old summary")

        assert result["status"]       == "ok"
        assert result["impact_level"] == "HIGH"
        assert result["changes"]      == 2
        mock_upd.assert_called_once_with(ver_id, delta)

    def test_analyze_delta_task_version_not_found(self):
        """Missing version_id → returns not_found, analyze_delta never called."""
        with patch("services.delta_analyzer.analyze_delta") as mock_analyze:
            from celery_app import analyze_delta_task
            result = analyze_delta_task(version_id=99999, old_summary="x")

        assert result["status"] == "not_found"
        mock_analyze.assert_not_called()

    def test_analyze_delta_task_no_delta_when_llm_returns_none(self):
        """analyze_delta returns None → task returns no_delta without crashing."""
        repo   = RegulationRepository()
        r      = repo.upsert_raw_versioned(_raw_data("https://cbr.ru/task/2", "Summary"))
        ver_id = r.version_id

        with patch("services.delta_analyzer.analyze_delta", return_value=None):
            from celery_app import analyze_delta_task
            result = analyze_delta_task(version_id=ver_id, old_summary="Old text")

        assert result["status"] == "no_delta"

    def test_send_scheduled_alerts_task_daily_digest(self):
        """Daily subscriber receives digest; httpx.post called once with RU content."""
        sub_repo = SubscriptionRepository()
        sub_repo.subscribe("tg_daily_user", "RU", "daily", "LOW")

        recent = [
            {
                "id":             1,
                "title":          "CBR Liquidity Rule",
                "jurisdiction":   "RU",
                "critical_level": "HIGH",
                "summary":        "Banks must hold extra 5% liquidity buffer.",
                "source_url":     "https://cbr.ru/liq",
                "delta_json":     None,
                "impact_level":   "HIGH",
            }
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(RegulationRepository, "get_recent_with_versions", return_value=recent), \
             patch("httpx.post", return_value=mock_resp) as mock_post, \
             patch.dict(os.environ, {
                 "TELEGRAM_BOT_TOKEN":    "fake_token",
                 "REGRADA_DASHBOARD_URL": "https://regrada.io/dash",
             }):
            from celery_app import send_scheduled_alerts_task
            result = send_scheduled_alerts_task()

        assert result["status"] == "ok"
        assert result["sent"]   == 1
        mock_post.assert_called_once()

        payload = mock_post.call_args.kwargs["json"]
        assert payload["chat_id"]           == "tg_daily_user"
        assert "RU"                          in payload["text"]
        assert "https://regrada.io/dash"     in payload["text"]

    def test_send_scheduled_alerts_task_risk_threshold_filters_low(self):
        """Subscriber with min_risk=HIGH must not receive a LOW-impact regulation."""
        sub_repo = SubscriptionRepository()
        sub_repo.subscribe("strict_user", "RU", "daily", "HIGH")

        low_impact = [
            {
                "id": 2, "title": "Minor Reporting Tweak",
                "jurisdiction": "RU", "critical_level": "LOW",
                "summary": "Minor wording change.", "source_url": "https://cbr.ru/minor",
                "delta_json": None, "impact_level": "LOW",
            }
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(RegulationRepository, "get_recent_with_versions", return_value=low_impact), \
             patch("httpx.post", return_value=mock_resp) as mock_post, \
             patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "t", "REGRADA_DASHBOARD_URL": ""}):
            from celery_app import send_scheduled_alerts_task
            result = send_scheduled_alerts_task()

        assert result["sent"] == 0
        mock_post.assert_not_called()

    def test_send_scheduled_alerts_task_instant_sends_delta_alert(self):
        """Instant subscriber receives format_delta_alert; payload contains IMPACT level."""
        sub_repo = SubscriptionRepository()
        sub_repo.subscribe("instant_user", "KZ", "instant", "LOW")

        delta    = _make_delta(impact="HIGH")
        recent   = [
            {
                "id": 3, "title": "NBK Capital Mandate",
                "jurisdiction": "KZ", "critical_level": "HIGH",
                "summary": "Critical capital adequacy rule.",
                "source_url": "https://nbk.kz/mandate",
                "delta_json": delta.model_dump_json(),
                "impact_level": "HIGH",
            }
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(RegulationRepository, "get_recent_with_versions", return_value=recent), \
             patch("httpx.post", return_value=mock_resp) as mock_post, \
             patch.dict(os.environ, {
                 "TELEGRAM_BOT_TOKEN":    "fake_token",
                 "REGRADA_DASHBOARD_URL": "https://d.io",
             }):
            from celery_app import send_scheduled_alerts_task
            result = send_scheduled_alerts_task()

        assert result["sent"] == 1
        mock_post.assert_called_once()

        payload = mock_post.call_args.kwargs["json"]
        assert "HIGH IMPACT" in payload["text"]
        assert "KZ"          in payload["text"]

    def test_send_scheduled_alerts_task_jurisdiction_filter(self):
        """Subscriber filtered to KZ must not receive RU-only regulations."""
        sub_repo = SubscriptionRepository()
        sub_repo.subscribe("kz_only_user", "KZ", "daily", "LOW")

        ru_only = [
            {
                "id": 4, "title": "RU-only Regulation",
                "jurisdiction": "RU", "critical_level": "HIGH",
                "summary": "Russian-only rule.", "source_url": "https://cbr.ru/ru",
                "delta_json": None, "impact_level": "HIGH",
            }
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(RegulationRepository, "get_recent_with_versions", return_value=ru_only), \
             patch("httpx.post", return_value=mock_resp) as mock_post, \
             patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "t", "REGRADA_DASHBOARD_URL": ""}):
            from celery_app import send_scheduled_alerts_task
            result = send_scheduled_alerts_task()

        assert result["sent"] == 0
        mock_post.assert_not_called()

    def test_send_scheduled_alerts_task_no_subscribers(self):
        """No active subscribers → returns ok with sent=0 without touching httpx."""
        with patch.object(RegulationRepository, "get_recent_with_versions", return_value=[]), \
             patch("httpx.post") as mock_post, \
             patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "t", "REGRADA_DASHBOARD_URL": ""}):
            from celery_app import send_scheduled_alerts_task
            result = send_scheduled_alerts_task()

        assert result["status"] == "ok"
        assert result["sent"]   == 0
        mock_post.assert_not_called()
