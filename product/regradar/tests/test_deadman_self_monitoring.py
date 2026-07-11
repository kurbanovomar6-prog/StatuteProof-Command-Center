"""
B-deadman: founder self-monitoring regression tests.

The monitoring loop is the product. A wedged or wholesale-failed monitor that
nobody notices means customers silently stop getting alerts while StatuteProof
keeps promising coverage. `Restart=on-failure` catches a crash but NOT a loop
that is alive yet doing nothing. This suite pins the three deadman mechanisms:

1. app/ops_alert.notify_founder — posts to the ADMIN bot (mock requests), is a
   quiet no-op when the admin bot is unconfigured or disabled via env.
2. app/monitor — fires notify_founder on an all-fail / nothing-succeeded cycle
   and does NOT fire on a healthy cycle; rate-limited to the transition edge.
3. app/scheduler.write_heartbeat + app/ops_alert.check_heartbeat — the
   heartbeat file is written after a cycle, and the watchdog alerts on a
   missing/stale heartbeat but stays quiet when it is fresh.

All tests are hermetic: no live network, all state redirected to tmp_path.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ══════════════════════════════════════════════════════════════════════════
# Part 1 — ops_alert.notify_founder
# ══════════════════════════════════════════════════════════════════════════
class TestNotifyFounder:
    def test_posts_to_admin_bot_when_configured(self):
        import app.ops_alert as ops_alert

        with patch.object(ops_alert, "TELEGRAM_BOT_TOKEN", "admin-tkn"), \
             patch.object(ops_alert, "TELEGRAM_CHAT_ID", "42"), \
             patch.object(ops_alert, "_ops_alerts_disabled", return_value=False), \
             patch.object(ops_alert._req, "post") as mock_post:
            mock_post.return_value.json.return_value = {"ok": True}
            ok = ops_alert.notify_founder("deadman test")

        assert ok is True
        assert mock_post.called
        url = mock_post.call_args[0][0]
        body = mock_post.call_args[1]["json"]
        # Uses the ADMIN bot token + founder chat id, not the alerts bot.
        assert "admin-tkn" in url
        assert str(body["chat_id"]) == "42"
        assert body["text"] == "deadman test"

    def test_noop_when_disabled_via_env(self):
        import app.ops_alert as ops_alert

        with patch.object(ops_alert, "TELEGRAM_BOT_TOKEN", "admin-tkn"), \
             patch.object(ops_alert, "TELEGRAM_CHAT_ID", "42"), \
             patch.object(ops_alert, "_ops_alerts_disabled", return_value=True), \
             patch.object(ops_alert._req, "post") as mock_post:
            ok = ops_alert.notify_founder("should not send")

        assert ok is False
        mock_post.assert_not_called()

    def test_disable_env_read_at_call_time(self, monkeypatch):
        """The disable switch honours os.environ set after import."""
        import app.ops_alert as ops_alert

        monkeypatch.setenv("STATUTEPROOF_OPS_ALERTS_DISABLED", "true")
        assert ops_alert._ops_alerts_disabled() is True
        monkeypatch.setenv("STATUTEPROOF_OPS_ALERTS_DISABLED", "false")
        assert ops_alert._ops_alerts_disabled() is False

    def test_noop_when_admin_bot_unconfigured(self):
        import app.ops_alert as ops_alert

        with patch.object(ops_alert, "TELEGRAM_BOT_TOKEN", ""), \
             patch.object(ops_alert, "TELEGRAM_CHAT_ID", ""), \
             patch.object(ops_alert, "_ops_alerts_disabled", return_value=False), \
             patch.object(ops_alert._req, "post") as mock_post:
            ok = ops_alert.notify_founder("no config")

        assert ok is False
        mock_post.assert_not_called()

    def test_never_raises_on_request_error(self):
        """A requests failure must return False, never propagate."""
        import app.ops_alert as ops_alert

        with patch.object(ops_alert, "TELEGRAM_BOT_TOKEN", "admin-tkn"), \
             patch.object(ops_alert, "TELEGRAM_CHAT_ID", "42"), \
             patch.object(ops_alert, "_ops_alerts_disabled", return_value=False), \
             patch.object(ops_alert._req, "post", side_effect=Exception("boom")):
            ok = ops_alert.notify_founder("will error")  # must not raise

        assert ok is False

    def test_returns_false_on_api_not_ok(self):
        import app.ops_alert as ops_alert

        with patch.object(ops_alert, "TELEGRAM_BOT_TOKEN", "admin-tkn"), \
             patch.object(ops_alert, "TELEGRAM_CHAT_ID", "42"), \
             patch.object(ops_alert, "_ops_alerts_disabled", return_value=False), \
             patch.object(ops_alert._req, "post") as mock_post:
            mock_post.return_value.json.return_value = {"ok": False, "description": "bad"}
            ok = ops_alert.notify_founder("api rejects")

        assert ok is False


# ══════════════════════════════════════════════════════════════════════════
# Part 2 — monitor fires notify_founder on catastrophic cycles only
# ══════════════════════════════════════════════════════════════════════════
def _source(name: str, url: str) -> dict:
    return {
        "name": name,
        "url": url,
        "jurisdiction": "AE",
        "category": "banking",
        "status": "active",
        "enabled": True,
    }


@pytest.fixture
def deadman_monitor(tmp_path, monkeypatch):
    """monitor with breaker + deadman state redirected to tmp, alert captured."""
    import app.monitor as monitor

    monkeypatch.setattr(monitor, "init_pipeline", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_CIRCUIT_STATE_FILE", tmp_path / "circuit_state.json")
    monkeypatch.setattr(monitor, "_DEADMAN_STATE_FILE", tmp_path / "deadman_state.json")
    monkeypatch.setattr(monitor, "_circuit_open", set())
    monkeypatch.setattr(monitor, "_circuit_skip_counts", {})
    # Never let a real FAILED-trail write touch the repo during these tests.
    monkeypatch.setattr(monitor, "_persist_failure_record", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_consecutive_failures", lambda _url: 0)
    return monitor


def _install_notify_spy(monitor, monkeypatch):
    """Patch app.ops_alert.notify_founder (imported lazily inside monitor)."""
    import app.ops_alert as ops_alert

    calls: list[str] = []

    def _spy(text: str) -> bool:
        calls.append(text)
        return True

    monkeypatch.setattr(ops_alert, "notify_founder", _spy)
    return calls


def test_alerts_founder_when_all_sources_fail(deadman_monitor, monkeypatch):
    monitor = deadman_monitor
    calls = _install_notify_spy(monitor, monkeypatch)

    src = _source("Always-Fails", "https://fails.example/x")
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: [src])
    monkeypatch.setattr(
        monitor, "run_pipeline_for_source",
        lambda _s: (_ for _ in ()).throw(TimeoutError("down")),
    )

    monitor.monitor_all_sources(verbose=False)

    assert len(calls) == 1, "founder must be alerted exactly once on all-fail"
    assert "CATASTROPHIC" in calls[0]


def test_alerts_when_nothing_succeeds_even_without_all_fail(deadman_monitor, monkeypatch):
    """ok + unchanged == 0 (all circuit-skipped) is catastrophic too."""
    monitor = deadman_monitor
    calls = _install_notify_spy(monitor, monkeypatch)

    src = _source("Open-Circuit", "https://skip.example/x")
    # Pre-open the circuit so the source is skipped (failed++), never fetched.
    monkeypatch.setattr(monitor, "_circuit_open", {src["name"]})
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: [src])

    def _must_not_fetch(_s):  # pragma: no cover - asserts non-invocation
        raise AssertionError("open circuit must skip, not fetch")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_fetch)

    monitor.monitor_all_sources(verbose=False)

    assert len(calls) == 1
    assert "CATASTROPHIC" in calls[0]


def test_does_not_alert_on_healthy_cycle(deadman_monitor, monkeypatch):
    monitor = deadman_monitor
    calls = _install_notify_spy(monitor, monkeypatch)

    src = _source("Healthy", "https://ok.example/x")
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: [src])
    monkeypatch.setattr(
        monitor, "run_pipeline_for_source",
        lambda _s: {"changed": False, "status": "ok", "risk_level": "LOW"},
    )

    monitor.monitor_all_sources(verbose=False)

    assert calls == [], "a healthy cycle must never alert the founder"


def test_rate_limited_alert_only_fires_on_transition(deadman_monitor, monkeypatch):
    """Two consecutive catastrophic cycles alert once, not twice."""
    monitor = deadman_monitor
    calls = _install_notify_spy(monitor, monkeypatch)

    src = _source("Always-Fails", "https://fails.example/x")
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: [src])
    monkeypatch.setattr(
        monitor, "run_pipeline_for_source",
        lambda _s: (_ for _ in ()).throw(TimeoutError("down")),
    )

    monitor.monitor_all_sources(verbose=False)
    monitor.monitor_all_sources(verbose=False)

    assert len(calls) == 1, "must alert only on the transition into the bad state"
    # The persisted degraded flag is what suppresses the second alert.
    state = json.loads((monitor._DEADMAN_STATE_FILE).read_text())
    assert state["degraded"] is True


def test_recovery_clears_flag_and_sends_recovery_note(deadman_monitor, monkeypatch):
    monitor = deadman_monitor
    calls = _install_notify_spy(monitor, monkeypatch)

    src = _source("Flaps", "https://flaps.example/x")
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: [src])

    # Cycle 1: catastrophic → alert + degraded flag set.
    monkeypatch.setattr(
        monitor, "run_pipeline_for_source",
        lambda _s: (_ for _ in ()).throw(TimeoutError("down")),
    )
    monitor.monitor_all_sources(verbose=False)
    assert len(calls) == 1 and "CATASTROPHIC" in calls[0]

    # Cycle 2: healthy → recovery note + degraded flag cleared.
    monkeypatch.setattr(
        monitor, "run_pipeline_for_source",
        lambda _s: {"changed": False, "status": "ok"},
    )
    monitor.monitor_all_sources(verbose=False)
    assert len(calls) == 2 and "recovered" in calls[1].lower()
    state = json.loads((monitor._DEADMAN_STATE_FILE).read_text())
    assert state["degraded"] is False


def test_empty_cycle_is_not_catastrophic(deadman_monitor, monkeypatch):
    """No enabled sources (total == 0) is a config state, not an outage."""
    monitor = deadman_monitor
    calls = _install_notify_spy(monitor, monkeypatch)

    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: [])
    monitor.monitor_all_sources(verbose=False)

    assert calls == []


def test_is_catastrophic_cycle_classifier():
    import app.monitor as monitor

    assert monitor._is_catastrophic_cycle(
        {"sources_total": 3, "sources_failed": 3, "sources_ok": 0, "sources_unchanged": 0}
    )
    assert monitor._is_catastrophic_cycle(
        {"sources_total": 2, "sources_failed": 1, "sources_ok": 0, "sources_unchanged": 0}
    )
    assert not monitor._is_catastrophic_cycle(
        {"sources_total": 3, "sources_failed": 1, "sources_ok": 1, "sources_unchanged": 1}
    )
    assert not monitor._is_catastrophic_cycle(
        {"sources_total": 0, "sources_failed": 0, "sources_ok": 0, "sources_unchanged": 0}
    )


# ══════════════════════════════════════════════════════════════════════════
# Part 3 — heartbeat write + watchdog check
# ══════════════════════════════════════════════════════════════════════════
def test_write_heartbeat_creates_file(tmp_path, monkeypatch):
    import app.scheduler as scheduler

    hb = tmp_path / "data" / "monitor_heartbeat"
    monkeypatch.setattr(scheduler, "_HEARTBEAT_FILE", hb)

    assert not hb.exists()
    assert scheduler.write_heartbeat() is True
    assert hb.exists()
    # Contains an ISO-8601 UTC timestamp line.
    assert hb.read_text().strip().endswith("+00:00")


def test_full_cycle_writes_heartbeat(tmp_path, monkeypatch):
    """run_watch_loop writes the heartbeat after a completed full cycle."""
    import app.scheduler as scheduler

    hb = tmp_path / "data" / "monitor_heartbeat"
    monkeypatch.setattr(scheduler, "_HEARTBEAT_FILE", hb)
    monkeypatch.setattr(scheduler, "monitor_all_sources", lambda **_k: [])
    monkeypatch.setattr(scheduler, "get_sources_by_priority", lambda _p: [])
    monkeypatch.setattr(scheduler, "_print_cycle_summary", lambda *_a, **_k: None)
    monkeypatch.setattr(scheduler, "_print_cycle_header", lambda *_a, **_k: None)
    monkeypatch.setattr(scheduler, "_log_priority_summary", lambda: None)

    # Break out of the infinite loop after the first sleep call.
    def _stop(*_a, **_k):
        raise KeyboardInterrupt

    monkeypatch.setattr(scheduler.time, "sleep", _stop)

    scheduler.run_watch_loop(interval_minutes=60)

    assert hb.exists(), "heartbeat must be written after the first full cycle"


def test_check_heartbeat_alerts_when_missing(tmp_path, monkeypatch):
    import app.ops_alert as ops_alert

    hb = tmp_path / "data" / "monitor_heartbeat"  # never created
    monkeypatch.setattr(ops_alert, "_HEARTBEAT_FILE", hb)

    calls: list[str] = []
    monkeypatch.setattr(ops_alert, "notify_founder", lambda t: calls.append(t) or True)

    stale = ops_alert.check_heartbeat()

    assert stale is True
    assert len(calls) == 1 and "MISSING" in calls[0]


def test_check_heartbeat_alerts_when_stale(tmp_path, monkeypatch):
    import app.ops_alert as ops_alert

    hb = tmp_path / "data" / "monitor_heartbeat"
    hb.parent.mkdir(parents=True, exist_ok=True)
    hb.write_text("2020-01-01T00:00:00+00:00\n")
    monkeypatch.setattr(ops_alert, "_HEARTBEAT_FILE", hb)
    monkeypatch.setattr(ops_alert, "WATCH_INTERVAL_MINUTES", 60)

    # Age the file well past 2x the 60-min interval.
    old = time.time() - (3 * 60 * 60)
    import os as _os
    _os.utime(hb, (old, old))

    calls: list[str] = []
    monkeypatch.setattr(ops_alert, "notify_founder", lambda t: calls.append(t) or True)

    stale = ops_alert.check_heartbeat()

    assert stale is True
    assert len(calls) == 1 and "STALE" in calls[0]


def test_check_heartbeat_quiet_when_fresh(tmp_path, monkeypatch):
    import app.ops_alert as ops_alert

    hb = tmp_path / "data" / "monitor_heartbeat"
    hb.parent.mkdir(parents=True, exist_ok=True)
    hb.write_text("now\n")  # just written → mtime is fresh
    monkeypatch.setattr(ops_alert, "_HEARTBEAT_FILE", hb)
    monkeypatch.setattr(ops_alert, "WATCH_INTERVAL_MINUTES", 60)

    calls: list[str] = []
    monkeypatch.setattr(ops_alert, "notify_founder", lambda t: calls.append(t) or True)

    stale = ops_alert.check_heartbeat()

    assert stale is False
    assert calls == [], "a fresh heartbeat must never alert"
