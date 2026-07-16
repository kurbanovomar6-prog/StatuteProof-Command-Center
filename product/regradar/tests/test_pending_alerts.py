"""G1 — deferred delivery of cooldown-suppressed alerts (app/pending_alerts.py).

A genuinely-new change suppressed ONLY by the per-source cooldown must be
delivered when the cooldown elapses (a delay), not lost forever. These tests
exercise the stash/flush lifecycle in isolation with the trail and send mocked.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import app.pending_alerts as pa

NOW = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)
SID = "AE-test-source"
SOURCE = {"id": SID, "name": "Test Source", "url": "https://reg.example/x"}


def _rec(hash_: str, *, alert_sent: bool, hours_ago: float, status: str = "CHANGED") -> dict:
    return {
        "source_id": SID,
        "change_status": status,
        "normalized_hash": hash_,
        "alert_sent": alert_sent,
        "timestamp_utc": (NOW - timedelta(hours=hours_ago)).isoformat(),
    }


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Point the stash at tmp and give both the trail readers a controllable list."""
    import app.source_runs as sr
    import app.alert_dedup as ad

    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    state = {"runs": [], "marked": []}

    def _fake_read_runs():
        return list(state["runs"])

    def _fake_mark(source_id, run_id, *, alert_sent=True):
        state["marked"].append((source_id, run_id, alert_sent))
        return True

    # flush_due imports _read_runs/make_source_id/mark_alert_sent from source_runs
    # lazily; should_send_alert uses alert_dedup's module-bound _read_runs.
    monkeypatch.setattr(sr, "_read_runs", _fake_read_runs)
    monkeypatch.setattr(ad, "_read_runs", _fake_read_runs)
    monkeypatch.setattr(sr, "mark_alert_sent", _fake_mark)
    return state


def _payload(hash_: str, run_id: str = "run123") -> dict:
    return {"source_id": SID, "run_id": run_id, "normalized_hash": hash_,
            "risk_level": "HIGH", "executive_summary": "A change."}


# ── stash / load / discard basics ─────────────────────────────────────────────

def test_stash_load_roundtrip_and_discard(env):
    assert pa.load(SID) is None
    path = pa.stash(_payload("H2"))
    assert path is not None and Path(path).exists()
    loaded = pa.load(SID)
    assert loaded["normalized_hash"] == "H2" and loaded["run_id"] == "run123"
    pa.discard(SID)
    assert pa.load(SID) is None


def test_stash_refuses_incomplete_payload(env):
    assert pa.stash({"source_id": SID, "run_id": "r"}) is None  # no hash
    assert pa.stash({"source_id": SID, "normalized_hash": "H"}) is None  # no run_id
    assert pa.stash({"run_id": "r", "normalized_hash": "H"}) is None  # no source_id
    assert pa.load(SID) is None


# ── flush_due lifecycle ───────────────────────────────────────────────────────

def test_flush_due_no_stash_is_noop(env):
    sent = []
    assert pa.flush_due(SOURCE, send_fn=lambda p: sent.append(p) or True, now=NOW) is False
    assert sent == []


def test_flush_kept_while_cooldown_active(env):
    # A recent delivered alert (1h ago) keeps the cooldown open → not yet due.
    env["runs"] = [_rec("H1", alert_sent=True, hours_ago=1),
                   _rec("H2", alert_sent=False, hours_ago=0.5)]
    pa.stash(_payload("H2"))
    sent = []
    assert pa.flush_due(SOURCE, send_fn=lambda p: sent.append(p) or True, now=NOW) is False
    assert sent == []
    assert pa.load(SID) is not None  # stash preserved for a later sweep


def test_flush_delivers_when_cooldown_elapsed_and_current(env):
    # Last delivered alert 48h ago (cooldown elapsed); H2 is the current change.
    env["runs"] = [_rec("H1", alert_sent=True, hours_ago=48),
                   _rec("H2", alert_sent=False, hours_ago=25)]
    pa.stash(_payload("H2", run_id="rA"))
    sent = []
    assert pa.flush_due(SOURCE, send_fn=lambda p: sent.append(p) or True, now=NOW) is True
    assert len(sent) == 1 and sent[0]["normalized_hash"] == "H2"
    assert (SID, "rA", True) in env["marked"]   # trail record flipped to alert_sent
    assert pa.load(SID) is None                 # stash cleared after delivery


def test_flush_discards_superseded_stash_unsent(env):
    # A newer CHANGED (H3) superseded the stashed H2 — deliver nothing, drop stash.
    env["runs"] = [_rec("H2", alert_sent=False, hours_ago=30),
                   _rec("H3", alert_sent=False, hours_ago=1)]
    pa.stash(_payload("H2"))
    sent = []
    assert pa.flush_due(SOURCE, send_fn=lambda p: sent.append(p) or True, now=NOW) is False
    assert sent == []
    assert pa.load(SID) is None


def test_flush_discards_already_alerted_stash_unsent(env):
    # The stashed hash was already delivered by another path → drop duplicate.
    env["runs"] = [_rec("H2", alert_sent=True, hours_ago=48)]
    pa.stash(_payload("H2"))
    sent = []
    assert pa.flush_due(SOURCE, send_fn=lambda p: sent.append(p) or True, now=NOW) is False
    assert sent == []
    assert pa.load(SID) is None


def test_flush_keeps_stash_when_send_returns_falsy(env):
    env["runs"] = [_rec("H1", alert_sent=True, hours_ago=48),
                   _rec("H2", alert_sent=False, hours_ago=25)]
    pa.stash(_payload("H2", run_id="rB"))
    assert pa.flush_due(SOURCE, send_fn=lambda p: False, now=NOW) is False
    assert pa.load(SID) is not None                  # retained for retry
    assert env["marked"] == []                        # not marked when unsent


def test_flush_keeps_stash_when_send_raises(env):
    env["runs"] = [_rec("H1", alert_sent=True, hours_ago=48),
                   _rec("H2", alert_sent=False, hours_ago=25)]
    pa.stash(_payload("H2"))

    def _boom(_p):
        raise RuntimeError("telegram down")

    assert pa.flush_due(SOURCE, send_fn=_boom, now=NOW) is False
    assert pa.load(SID) is not None
