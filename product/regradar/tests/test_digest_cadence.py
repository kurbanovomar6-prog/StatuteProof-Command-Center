"""Configurable digest cadence + all-clear heartbeat (feature 3-digest-cadence).

Covers the four DONE-gates for the feature:

1. Delivery thresholds + digest cadence come from the per-user PROFILE, not the
   hardcoded 80/50 constants that used to live in alert_routing.
2. Daily/weekly bundling groups matched alerts into ONE risk-sorted message and
   is idempotent (per period, and cross-period via per-alert dedup markers).
3. A quiet digest window emits a customer-safe all-clear heartbeat that is
   evidence-grounded (real source-run counts) and passes the forbidden-claims
   guard + carries the standard disclaimer.
4. Instant HIGH/urgent alerts still fire immediately, for a customer of ANY
   cadence.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "digest.db"))
    yield tmp_path / "digest.db"


def _make_paired_user(email: str, chat_id: str, *, alerts_enabled: bool = True) -> int:
    from app.auth import create_user
    from app.profile import update_profile
    from app.telegram_pairing import consume_pairing_code, create_pairing_code

    user = create_user(email, "password-123")
    user_id = int(user["id"])
    code = create_pairing_code(user_id)["code"]
    assert consume_pairing_code(code, chat_id, {"username": "tester"}) == "ok"
    update_profile(
        user_id,
        {"telegram_alerts_enabled": 1 if alerts_enabled else 0, "onboarding_completed": 1},
    )
    return user_id


def _match(alert_id, *, risk="MEDIUM", score=60, delivery_ready=True, summary="A monitored change.", source="DFSA"):
    return {
        "alert_id": alert_id,
        "source_id": f"AE-{alert_id}",
        "source_name": source,
        "market": "DIFC",
        "jurisdiction": "DIFC",
        "change_type": "Regulatory update",
        "risk_level": risk,
        "score": score,
        "matched": True,
        "delivery_ready": delivery_ready,
        "executive_summary": summary,
        "source_url": f"https://example.gov.ae/{alert_id}",
        "reviewed_at": "2026-07-10T10:00:00+00:00",
    }


def _preview(matches):
    return {"ok": True, "matches": matches, "profile_ready": True, "not_ready_reasons": []}


# ---------------------------------------------------------------------------
# 1. Thresholds + cadence are profile fields (not hardcoded)
# ---------------------------------------------------------------------------


class TestProfileFields:
    def test_defaults_present(self, isolated_db):
        from app.profile import get_or_create_profile

        profile = get_or_create_profile(101)
        assert profile["urgent_threshold"] == 80
        assert profile["weekly_threshold"] == 50
        assert profile["digest_cadence"] == "daily"

    def test_update_and_persist(self, isolated_db):
        from app.profile import get_or_create_profile, update_profile

        update_profile(102, {"urgent_threshold": 90, "weekly_threshold": 30, "digest_cadence": "weekly"})
        reread = get_or_create_profile(102)
        assert reread["urgent_threshold"] == 90
        assert reread["weekly_threshold"] == 30
        assert reread["digest_cadence"] == "weekly"

    def test_invalid_cadence_rejected(self, isolated_db):
        from app.profile import update_profile

        with pytest.raises(ValueError):
            update_profile(103, {"digest_cadence": "hourly"})

    def test_out_of_range_threshold_rejected(self, isolated_db):
        from app.profile import update_profile

        with pytest.raises(ValueError):
            update_profile(104, {"urgent_threshold": 150})
        with pytest.raises(ValueError):
            update_profile(104, {"weekly_threshold": -5})

    def test_non_integer_threshold_rejected(self, isolated_db):
        from app.profile import update_profile

        with pytest.raises(ValueError):
            update_profile(105, {"urgent_threshold": "loud"})

    def test_routing_profile_reads_profile_not_hardcoded(self, isolated_db):
        from app.alert_routing import user_profile_to_routing_profile
        from app.profile import update_profile

        update_profile(106, {"urgent_threshold": 70, "weekly_threshold": 40, "digest_cadence": "weekly"})
        routing = user_profile_to_routing_profile(106)
        assert routing["urgent_threshold"] == 70
        assert routing["weekly_threshold"] == 40
        assert routing["digest_cadence"] == "weekly"
        # The old hardcoded 80/50 must no longer be forced.
        assert routing["delivery_preferences"]["urgent_threshold"] == 70
        assert routing["delivery_preferences"]["weekly_threshold"] == 40

    def test_additive_migration_backfills_legacy_rows(self, isolated_db):
        """A pre-feature user_profiles row backfills to the sane defaults after
        the additive column migration, and reads tolerantly."""
        from app.profile import get_or_create_profile

        conn = db._connect()
        try:
            conn.execute(
                "CREATE TABLE user_profiles (user_id INTEGER PRIMARY KEY, "
                "alert_threshold TEXT, created_at TEXT, updated_at TEXT)"
            )
            conn.execute(
                "INSERT INTO user_profiles(user_id, alert_threshold, created_at, updated_at) "
                "VALUES (777, 'HIGH', 't', 't')"
            )
            conn.commit()
        finally:
            conn.close()

        profile = get_or_create_profile(777)  # runs ensure_profile_table() migration
        assert profile["alert_threshold"] == "HIGH"
        assert profile["urgent_threshold"] == 80
        assert profile["weekly_threshold"] == 50
        assert profile["digest_cadence"] == "daily"


# ---------------------------------------------------------------------------
# 2. split_matches_for_cadence — the pure cadence gate
# ---------------------------------------------------------------------------


class TestSplitMatches:
    def test_high_is_instant_medium_is_bundle(self):
        from app.digest_cadence import split_matches_for_cadence

        matches = [
            _match("high1", risk="HIGH", score=40),
            _match("med1", risk="MEDIUM", score=60),
        ]
        instant, bundle = split_matches_for_cadence(matches, urgent_threshold=80, weekly_threshold=50)
        assert [m["alert_id"] for m in instant] == ["high1"]
        assert [m["alert_id"] for m in bundle] == ["med1"]

    def test_high_score_medium_is_instant_via_urgent_threshold(self):
        from app.digest_cadence import split_matches_for_cadence

        matches = [_match("hot", risk="MEDIUM", score=85)]
        instant, bundle = split_matches_for_cadence(matches, urgent_threshold=80, weekly_threshold=50)
        assert [m["alert_id"] for m in instant] == ["hot"]
        assert bundle == []

    def test_below_weekly_threshold_is_dropped(self):
        from app.digest_cadence import split_matches_for_cadence

        matches = [_match("weak", risk="MEDIUM", score=45)]
        instant, bundle = split_matches_for_cadence(matches, urgent_threshold=80, weekly_threshold=50)
        assert instant == []
        assert bundle == []

    def test_profile_threshold_changes_grouping(self):
        """Same score, different weekly_threshold -> different bundling."""
        from app.digest_cadence import split_matches_for_cadence

        matches = [_match("m", risk="MEDIUM", score=35)]
        _, bundle_default = split_matches_for_cadence(matches, urgent_threshold=80, weekly_threshold=50)
        _, bundle_low = split_matches_for_cadence(matches, urgent_threshold=80, weekly_threshold=30)
        assert bundle_default == []
        assert [m["alert_id"] for m in bundle_low] == ["m"]

    def test_non_delivery_ready_excluded(self):
        from app.digest_cadence import split_matches_for_cadence

        matches = [_match("nr", risk="HIGH", score=90, delivery_ready=False)]
        instant, bundle = split_matches_for_cadence(matches, urgent_threshold=80, weekly_threshold=50)
        assert instant == []
        assert bundle == []

    def test_suppress_ids_excludes_already_digested(self):
        from app.digest_cadence import split_matches_for_cadence

        matches = [_match("a", risk="MEDIUM", score=60), _match("b", risk="MEDIUM", score=60)]
        _, bundle = split_matches_for_cadence(
            matches, urgent_threshold=80, weekly_threshold=50, suppress_ids={"a"}
        )
        assert [m["alert_id"] for m in bundle] == ["b"]

    def test_bundle_is_risk_sorted(self):
        from app.digest_cadence import split_matches_for_cadence

        matches = [
            _match("low", risk="LOW", score=55),
            _match("med", risk="MEDIUM", score=55),
        ]
        _, bundle = split_matches_for_cadence(matches, urgent_threshold=80, weekly_threshold=50)
        assert [m["alert_id"] for m in bundle] == ["med", "low"]


# ---------------------------------------------------------------------------
# 3. Daily/weekly bundling: groups + idempotent
# ---------------------------------------------------------------------------


class TestBundleDelivery:
    def test_bundle_groups_and_is_idempotent_within_period(self, isolated_db):
        from app.digest_cadence import dispatch_digest_for_user

        user_id = _make_paired_user("bundle@co.com", "900001")
        preview = _preview([_match("a1", score=60), _match("a2", score=70)])
        now = datetime(2026, 7, 11, 9, 0, tzinfo=timezone.utc)
        sent: list[tuple[str, str]] = []

        def fake_send(chat_id, text):
            sent.append((chat_id, text))
            return True

        first = dispatch_digest_for_user(
            user_id, cadence="daily", now=now, preview=preview, send_fn=fake_send
        )
        assert first["status"] == "sent"
        assert first["kind"] == "digest"
        assert first["alert_count"] == 2
        assert len(sent) == 1
        # ONE message, both alerts grouped, risk-sorted, disclaimer present.
        assert "2 human-reviewed change(s)" in sent[0][1]
        assert "Not legal advice." in sent[0][1]

        # Second call same period -> duplicate, nothing re-sent.
        second = dispatch_digest_for_user(
            user_id, cadence="daily", now=now, preview=preview, send_fn=fake_send
        )
        assert second["status"] == "duplicate"
        assert len(sent) == 1

    def test_next_period_suppresses_already_digested_alert(self, isolated_db):
        """Cross-period idempotency: an alert bundled on day 1 is not re-bundled
        on day 2; with nothing new left, day 2 becomes a quiet heartbeat."""
        from app.digest_cadence import dispatch_digest_for_user

        user_id = _make_paired_user("cross@co.com", "900002")
        preview = _preview([_match("a1", score=60), _match("a2", score=70)])
        sent: list[str] = []

        def fake_send(chat_id, text):
            sent.append(text)
            return True

        day1 = datetime(2026, 7, 11, 9, 0, tzinfo=timezone.utc)
        r1 = dispatch_digest_for_user(user_id, cadence="daily", now=day1, preview=preview, send_fn=fake_send)
        assert r1["status"] == "sent" and r1["kind"] == "digest"

        # Day 2: the same two alerts are still approved, but already digested ->
        # bundle empty -> quiet heartbeat (grounded, base_dir has no runs -> 0).
        day2 = datetime(2026, 7, 12, 9, 0, tzinfo=timezone.utc)
        r2 = dispatch_digest_for_user(
            user_id, cadence="daily", now=day2, preview=preview, send_fn=fake_send, base_dir=isolated_db.parent
        )
        assert r2["status"] == "sent"
        assert r2["kind"] == "heartbeat"
        assert "Monitoring is active." in sent[-1]

    def test_high_alert_is_not_bundled(self, isolated_db):
        """A HIGH-risk match belongs to the instant path; the digest bundle must
        never include it (it is instant, not bundle)."""
        from app.digest_cadence import dispatch_digest_for_user

        user_id = _make_paired_user("high@co.com", "900003")
        preview = _preview([_match("h1", risk="HIGH", score=40)])
        now = datetime(2026, 7, 11, 9, 0, tzinfo=timezone.utc)
        sent: list[str] = []

        def fake_send(chat_id, text):
            sent.append(text)
            return True

        result = dispatch_digest_for_user(
            user_id, cadence="daily", now=now, preview=preview, send_fn=fake_send,
            base_dir=isolated_db.parent,
        )
        # HIGH is instant-only, nothing to bundle, and window is not quiet ->
        # digest pass is a silent no-op.
        assert result["status"] == "instant_only"
        assert sent == []

    def test_weekly_period_key_rolls_once_per_iso_week(self, isolated_db):
        from app.digest_cadence import dispatch_digest_for_user

        user_id = _make_paired_user("weekly@co.com", "900004")
        preview = _preview([_match("w1", score=60)])
        sent: list[str] = []

        def fake_send(chat_id, text):
            sent.append(text)
            return True

        # Two different days within the SAME ISO week -> one digest only.
        mon = datetime(2026, 7, 6, 9, 0, tzinfo=timezone.utc)
        wed = datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc)
        r1 = dispatch_digest_for_user(user_id, cadence="weekly", now=mon, preview=preview, send_fn=fake_send)
        r2 = dispatch_digest_for_user(user_id, cadence="weekly", now=wed, preview=preview, send_fn=fake_send)
        assert r1["status"] == "sent"
        assert r2["status"] == "duplicate"
        assert len(sent) == 1


# ---------------------------------------------------------------------------
# 4. Quiet-window heartbeat: emitted, grounded, legally safe
# ---------------------------------------------------------------------------


def _seed_source_runs(base_dir: Path, source_ids, *, ts: str, change_status: str = "UNCHANGED") -> None:
    run_dir = base_dir / "data" / "source_runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, sid in enumerate(source_ids):
        lines.append(json.dumps({
            "run_id": f"r{i}",
            "source_id": sid,
            "timestamp_utc": ts,
            "change_status": change_status,
            "normalized_hash": f"h{i}",
        }))
    (run_dir / "source_runs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestQuietHeartbeat:
    def test_quiet_window_emits_grounded_heartbeat(self, isolated_db, tmp_path):
        from app.digest_cadence import dispatch_digest_for_user

        user_id = _make_paired_user("quiet@co.com", "900010")
        base = tmp_path / "artifacts"
        now = datetime(2026, 7, 11, 12, 0, tzinfo=timezone.utc)
        _seed_source_runs(base, ["AE-a", "AE-b", "AE-c"], ts="2026-07-11T06:00:00+00:00")

        sent: list[str] = []

        def fake_send(chat_id, text):
            sent.append(text)
            return True

        result = dispatch_digest_for_user(
            user_id, cadence="daily", now=now, preview=_preview([]), send_fn=fake_send, base_dir=base
        )
        assert result["status"] == "sent"
        assert result["kind"] == "heartbeat"
        assert result["sources_checked"] == 3  # grounded in seeded runs
        # Grounded count appears; legally safe wording; disclaimer present.
        msg = sent[0]
        assert "checked 3 official source(s)" in msg
        assert "Not legal advice." in msg
        assert "never miss" not in msg.lower()
        assert "guarantee" not in msg.lower()

    def test_heartbeat_passes_forbidden_guard(self, isolated_db, tmp_path):
        from app.change_register import assert_no_forbidden_claims
        from app.digest_cadence import build_heartbeat_stats, render_heartbeat_message

        stats = build_heartbeat_stats(window_days=7, base_dir=tmp_path)
        msg = render_heartbeat_message({}, stats, cadence="weekly", period_label="ISO week 2026-W28")
        # Does not raise -> passes the shared guard.
        assert_no_forbidden_claims(msg)
        assert "Monitoring intelligence only. Not legal advice." in msg

    def test_heartbeat_idempotent_within_period(self, isolated_db, tmp_path):
        from app.digest_cadence import dispatch_digest_for_user

        user_id = _make_paired_user("quiet2@co.com", "900011")
        now = datetime(2026, 7, 11, 12, 0, tzinfo=timezone.utc)
        sent: list[str] = []

        def fake_send(chat_id, text):
            sent.append(text)
            return True

        r1 = dispatch_digest_for_user(user_id, cadence="daily", now=now, preview=_preview([]), send_fn=fake_send, base_dir=tmp_path)
        r2 = dispatch_digest_for_user(user_id, cadence="daily", now=now, preview=_preview([]), send_fn=fake_send, base_dir=tmp_path)
        assert r1["status"] == "sent"
        assert r2["status"] == "duplicate"
        assert len(sent) == 1

    def test_heartbeat_only_grounded_in_real_runs(self, isolated_db, tmp_path):
        """No recorded runs -> heartbeat reports 0 sources, never invents a count."""
        from app.digest_cadence import build_heartbeat_stats

        stats = build_heartbeat_stats(window_days=1, base_dir=tmp_path)
        assert stats["sources_checked"] == 0
        assert stats["changes_in_window"] == 0


# ---------------------------------------------------------------------------
# 5. Instant HIGH/urgent still fires immediately (any cadence)
# ---------------------------------------------------------------------------


class TestInstantDispatch:
    def test_high_fires_immediately_regardless_of_cadence(self, isolated_db):
        from app.digest_cadence import dispatch_instant_for_user
        from app.profile import update_profile

        user_id = _make_paired_user("inst@co.com", "900020")
        update_profile(user_id, {"digest_cadence": "weekly"})  # even on weekly cadence
        preview = _preview([_match("h1", risk="HIGH", score=40), _match("m1", risk="MEDIUM", score=55)])

        fired: list[str] = []

        def fake_send_preview(uid, alert_id):
            fired.append(alert_id)
            return {"ok": True}

        result = dispatch_instant_for_user(user_id, preview=preview, send_preview_fn=fake_send_preview)
        assert result["instant_sent"] == 1
        assert fired == ["h1"]  # HIGH fired; MEDIUM (below urgent 80) did not

    def test_urgent_threshold_promotes_medium_to_instant(self, isolated_db):
        from app.digest_cadence import dispatch_instant_for_user
        from app.profile import update_profile

        user_id = _make_paired_user("urg@co.com", "900021")
        update_profile(user_id, {"urgent_threshold": 50})
        preview = _preview([_match("m1", risk="MEDIUM", score=60)])  # 60 >= 50

        fired: list[str] = []

        def fake_send_preview(uid, alert_id):
            fired.append(alert_id)
            return {"ok": True}

        result = dispatch_instant_for_user(user_id, preview=preview, send_preview_fn=fake_send_preview)
        assert result["instant_sent"] == 1
        assert fired == ["m1"]

    def test_non_delivery_ready_not_fired(self, isolated_db):
        from app.digest_cadence import dispatch_instant_for_user

        user_id = _make_paired_user("nrf@co.com", "900022")
        preview = _preview([_match("h1", risk="HIGH", score=90, delivery_ready=False)])

        fired: list[str] = []

        def fake_send_preview(uid, alert_id):
            fired.append(alert_id)
            return {"ok": True}

        result = dispatch_instant_for_user(user_id, preview=preview, send_preview_fn=fake_send_preview)
        assert result["instant_sent"] == 0
        assert fired == []


# ---------------------------------------------------------------------------
# 6. Forbidden-claims guard actively blocks a poisoned bundle
# ---------------------------------------------------------------------------


class TestForbiddenGuard:
    def test_render_raises_on_forbidden_phrase(self):
        from app.change_register import ChangeRegisterError
        from app.digest_cadence import render_digest_message

        poisoned = [_match("bad", summary="This will guarantee compliance for you.")]
        with pytest.raises(ChangeRegisterError):
            render_digest_message({}, poisoned, cadence="daily", period_label="2026-07-11")

    def test_dispatch_blocks_and_does_not_send_poisoned_bundle(self, isolated_db):
        from app.digest_cadence import dispatch_digest_for_user

        user_id = _make_paired_user("poison@co.com", "900030")
        preview = _preview([_match("bad", score=60, summary="We guarantee compliance and prevent fines.")])
        now = datetime(2026, 7, 11, 9, 0, tzinfo=timezone.utc)
        sent: list[str] = []

        def fake_send(chat_id, text):
            sent.append(text)
            return True

        result = dispatch_digest_for_user(user_id, cadence="daily", now=now, preview=preview, send_fn=fake_send)
        assert result["status"] == "blocked"
        assert sent == []  # unguarded text is never delivered


# ---------------------------------------------------------------------------
# 7. End-to-end scheduler entry point
# ---------------------------------------------------------------------------


class TestRunScheduledDigests:
    def test_instant_plus_digest_for_one_user(self, isolated_db, tmp_path, monkeypatch):
        import app.digest_cadence as dc

        user_id = _make_paired_user("e2e@co.com", "900040")
        preview = _preview([_match("h1", risk="HIGH", score=40), _match("m1", risk="MEDIUM", score=60)])

        monkeypatch.setattr(dc, "build_routing_preview_for_user", lambda uid, days: preview)
        fired: list[str] = []

        def fake_send_preview(uid, alert_id):
            fired.append(alert_id)
            return {"ok": True}

        monkeypatch.setattr(dc, "send_preview_alert_to_user", fake_send_preview)

        bundle_sent: list[str] = []

        def fake_send(chat_id, text):
            bundle_sent.append(text)
            return True

        now = datetime(2026, 7, 11, 9, 0, tzinfo=timezone.utc)
        summary = dc.run_scheduled_digests(now=now, send_fn=fake_send, base_dir=tmp_path)
        assert summary["users"] == 1
        assert summary["instant_sent"] == 1  # HIGH fired
        assert summary["digests_sent"] == 1  # MEDIUM bundled
        assert fired == ["h1"]
        assert len(bundle_sent) == 1
        assert "1 human-reviewed change(s)" in bundle_sent[0]

    def test_idempotent_across_two_cycles(self, isolated_db, tmp_path, monkeypatch):
        import app.digest_cadence as dc

        _make_paired_user("e2e2@co.com", "900041")
        preview = _preview([_match("m1", risk="MEDIUM", score=60)])
        monkeypatch.setattr(dc, "build_routing_preview_for_user", lambda uid, days: preview)
        monkeypatch.setattr(dc, "send_preview_alert_to_user", lambda uid, aid: {"ok": True})

        bundle_sent: list[str] = []

        def fake_send(chat_id, text):
            bundle_sent.append(text)
            return True

        now = datetime(2026, 7, 11, 9, 0, tzinfo=timezone.utc)
        s1 = dc.run_scheduled_digests(now=now, send_fn=fake_send, base_dir=tmp_path)
        s2 = dc.run_scheduled_digests(now=now, send_fn=fake_send, base_dir=tmp_path)
        assert s1["digests_sent"] == 1
        assert s2["digests_sent"] == 0  # idempotent per period
        assert len(bundle_sent) == 1
