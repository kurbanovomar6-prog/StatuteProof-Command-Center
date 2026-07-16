"""/api/health must report real health, not a hardcoded ok:true.

Regression for the finding that the payload pinned ``"ok": True`` even when the
database was unavailable, so every uptime monitor saw 200/ok while the DB was
down. Health is now: ok = db connected AND last run not stale beyond 2x the
watch interval; unhealthy returns HTTP 503.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.api import _Handler  # noqa: E402


def _make_handler():
    handler = _Handler.__new__(_Handler)
    handler.command = "GET"
    handler.path = "/api/health"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": "0"}.get(key, default)
    handler.headers = hdrs
    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _seed_trail(base: Path, timestamp: str) -> None:
    d = base / "data" / "source_runs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "source_runs.jsonl").write_text(
        json.dumps({"timestamp_utc": timestamp, "change_status": "UNCHANGED"}) + "\n",
        encoding="utf-8",
    )


def _fake_ok_conn(*_a, **_k):
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (1,)
    return conn


def test_health_db_down_reports_not_ok_503(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    import sqlite3
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("db down")))
    handler = _make_handler()
    handler._handle_health()
    data, status = handler._sent[-1]
    assert data["ok"] is False
    assert data["db"] == "unavailable"
    assert status == 503


def test_health_fresh_run_reports_ok_200(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(config, "WATCH_INTERVAL_MINUTES", 60)
    import sqlite3
    monkeypatch.setattr(sqlite3, "connect", _fake_ok_conn)
    fresh = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _seed_trail(tmp_path, fresh)
    handler = _make_handler()
    handler._handle_health()
    data, status = handler._sent[-1]
    assert data["ok"] is True
    assert data["stale"] is False
    assert status == 200


def test_health_stale_run_reports_not_ok_503(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(config, "WATCH_INTERVAL_MINUTES", 60)
    import sqlite3
    monkeypatch.setattr(sqlite3, "connect", _fake_ok_conn)
    # 5 hours old, well beyond 2x60min.
    stale = (datetime.now(timezone.utc) - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _seed_trail(tmp_path, stale)
    handler = _make_handler()
    handler._handle_health()
    data, status = handler._sent[-1]
    assert data["ok"] is False
    assert data["stale"] is True
    assert status == 503


def test_health_no_runs_yet_is_ok_when_db_up(monkeypatch, tmp_path):
    # Fresh deploy: no runs recorded. Absence of runs is not a failure signal.
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    import sqlite3
    monkeypatch.setattr(sqlite3, "connect", _fake_ok_conn)
    handler = _make_handler()
    handler._handle_health()
    data, status = handler._sent[-1]
    assert data["ok"] is True
    assert data["last_run_at"] is None
    assert status == 200


def test_health_exposes_fresh_alert_count_leq_configured(monkeypatch, tmp_path):
    """DH-5: /api/health exposes the fresh-alert-eligible count so the landing can
    disclose it beside 'configured'. It must be present and never exceed the
    enabled (configured) count."""
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(config, "WATCH_INTERVAL_MINUTES", 60)
    import sqlite3
    monkeypatch.setattr(sqlite3, "connect", _fake_ok_conn)
    fresh = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _seed_trail(tmp_path, fresh)
    handler = _make_handler()
    handler._handle_health()
    data, _status = handler._sent[-1]
    assert "sources_fresh_alert" in data
    assert isinstance(data["sources_fresh_alert"], int)
    if data["sources_active"] >= 0 and data["sources_fresh_alert"] >= 0:
        assert data["sources_fresh_alert"] <= data["sources_active"]
