"""Regression: POST /api/briefs/generate must never render a forbidden claim.

The briefs_generate handler interpolates ``executive_summary`` and
``business_action_required`` from ``generate_ai_brief`` straight into the
persisted internal brief AND the JSON response. That was the one AI-text
render path that skipped the shared find_forbidden_claims pass, so a model
hallucination (or a prompt-injected instruction echoed from an adversarial
source) carrying a banned compliance claim reached both disk and the client.

This test monkeypatches ``generate_ai_brief`` to return a forbidden claim and
asserts the banned wording is scrubbed from the persisted brief and the JSON
response, mirroring the alert_content SF-1 scrub-before-render pattern.
"""

from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db

_FORBIDDEN = ("guarantee compliance", "prevent fines", "stay compliant automatically")


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "briefs.db"))
    monkeypatch.delenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", raising=False)
    monkeypatch.delenv("STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS", raising=False)
    yield tmp_path / "briefs.db"


def _run_brief_generate(monkeypatch, tmp_path, ai_brief: dict, source_id: str = "AE-1"):
    """Drive _handle_briefs_generate with the AI path forced on and gated off."""
    import app.api as api

    # A run record with a diff artifact so change_text is non-empty and the
    # AI branch (ENABLE_AI_ANALYSIS + change_text) is taken.
    diffs_dir = tmp_path / "data" / "diffs"
    diffs_dir.mkdir(parents=True, exist_ok=True)
    (diffs_dir / "diff.json").write_text(
        json.dumps({"added_chunks": ["Firms must now file a quarterly return."]}),
        encoding="utf-8",
    )
    runs_dir = tmp_path / "data" / "source_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "source_runs.jsonl").write_text(
        json.dumps({
            "run_id": "run-1",
            "source_id": source_id,
            "source_name": "DFSA Rulebook",
            "official_url": "https://dfsa.example.ae/rulebook-change",
            "change_status": "CHANGED",
            "timestamp_utc": "2026-07-10T10:00:00+00:00",
            "diff_json_path": "data/diffs/diff.json",
        }) + "\n",
        encoding="utf-8",
    )

    # Plan gate off (owner pilot flag) so generation proceeds; force AI on and
    # replace generate_ai_brief with our poisoned payload.
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    monkeypatch.setattr("app.config.ENABLE_AI_ANALYSIS", True, raising=False)
    monkeypatch.setattr("app.ai_brief.generate_ai_brief", lambda text, meta: dict(ai_brief))

    handler = api._Handler.__new__(api._Handler)
    handler.command = "POST"
    handler.path = "/api/briefs/generate"
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
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))

    monkeypatch.setattr(api, "BASE_DIR", tmp_path)
    monkeypatch.setattr(api, "require_auth", lambda h: {"id": 1})
    monkeypatch.setattr(api._Handler, "_source_visible_to", lambda self, user, sid: True)
    handler._rate_limited = lambda *a, **kw: False
    handler._read_json_strict = lambda: ({"source_id": source_id, "run_id": "run-1"}, None)
    handler._handle_briefs_generate()
    return sent[-1], tmp_path


def test_forbidden_claim_scrubbed_from_brief_and_response(isolated_db, monkeypatch, tmp_path):
    poisoned = {
        "risk_level": "HIGH",
        "executive_summary": (
            "This update means you can stay compliant automatically and we "
            "guarantee compliance for your firm."
        ),
        "business_action_required": "Rely on StatuteProof to prevent fines.",
        "confidence": "HIGH",
        "ai_used": True,
        "fallback_used": False,
    }

    (body, status), base = _run_brief_generate(monkeypatch, tmp_path, poisoned)

    assert status == 200
    assert body["ok"] is True

    # JSON response carries no forbidden wording (summary + recommended_action).
    blob = json.dumps(body).lower()
    for phrase in _FORBIDDEN:
        assert phrase not in blob, f"forbidden {phrase!r} leaked into JSON response"
    assert "withheld" in blob

    # Persisted brief on disk carries no forbidden wording either.
    brief_files = list((base / "data" / "internal_briefs").rglob("*_brief.md"))
    assert brief_files, "brief was not persisted"
    saved = brief_files[0].read_text(encoding="utf-8").lower()
    for phrase in _FORBIDDEN:
        assert phrase not in saved, f"forbidden {phrase!r} leaked into persisted brief"
    assert "withheld" in saved


def test_forbidden_claim_scrubbed_from_obligation_and_entities(isolated_db, monkeypatch, tmp_path):
    """specific_obligation and affected_entities also feed brief_markdown (disk
    + JSON response) and must be screened by the same guard."""
    poisoned = {
        "risk_level": "HIGH",
        "executive_summary": "The rulebook now requires a quarterly return filing.",
        "business_action_required": "Review the new filing obligation with your MLRO.",
        "specific_obligation": (
            "Firms must file quarterly, and StatuteProof will guarantee "
            "compliance so you prevent fines under this rule."
        ),
        "affected_entities": [
            "DFSA-authorised firms",
            "Anyone relying on us to stay compliant automatically",
        ],
        "confidence": "HIGH",
        "ai_used": True,
        "fallback_used": False,
    }

    (body, status), base = _run_brief_generate(monkeypatch, tmp_path, poisoned)

    assert status == 200
    assert body["ok"] is True

    # brief_markdown is carried in the JSON response — it must be clean.
    blob = json.dumps(body).lower()
    for phrase in _FORBIDDEN:
        assert phrase not in blob, f"forbidden {phrase!r} leaked into JSON response"
    assert "withheld" in blob

    # Persisted brief on disk (which renders both fields) must be clean too.
    brief_files = list((base / "data" / "internal_briefs").rglob("*_brief.md"))
    assert brief_files, "brief was not persisted"
    saved = brief_files[0].read_text(encoding="utf-8").lower()
    for phrase in _FORBIDDEN:
        assert phrase not in saved, f"forbidden {phrase!r} leaked into persisted brief"
    assert "withheld" in saved
    # The clean affected entity survives the per-item scrub.
    assert "dfsa-authorised firms" in saved


def test_clean_ai_brief_passes_through_unchanged(isolated_db, monkeypatch, tmp_path):
    """The guard must not disturb a clean brief — no false-positive scrub."""
    clean = {
        "risk_level": "MEDIUM",
        "executive_summary": "The rulebook now requires a quarterly return filing.",
        "business_action_required": "Review the new filing obligation with your MLRO.",
        "confidence": "MEDIUM",
        "ai_used": True,
        "fallback_used": False,
    }

    (body, status), base = _run_brief_generate(monkeypatch, tmp_path, clean)

    assert status == 200
    assert "quarterly return filing" in body["summary"]
    assert "Review the new filing obligation" in body["recommended_action"]
    assert "withheld" not in json.dumps(body).lower()
