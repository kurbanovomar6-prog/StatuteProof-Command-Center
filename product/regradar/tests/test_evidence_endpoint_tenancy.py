"""Cross-tenant leak-CLASS regression tests for the evidence/review/briefs endpoints.

Round 4 of the tenancy review found that six read handlers and two write
handlers echoed another tenant's PRIVATE custom source (source_id, source_name,
official_url, private diff text, internal MLRO notes) to any authenticated
account, and let any account tamper with another tenant's review state. This
suite pins every one of those paths closed.

Each test asserts BOTH halves so a future "fix" that simply blanks the endpoint
for everyone still fails:

* attacker (a user who does NOT own custom-A) is blocked / the victim's private
  strings are absent;
* owner (the user who owns custom-A) still sees their own data — the guard only
  removes cross-tenant rows, it does not break the endpoint.

The fixture makes ``custom-A`` a custom source owned by user 1, so
``_denied_custom_source_ids`` denies it to user 2 and allows it to user 1.
``official-X`` is a shared official source and must stay visible to everyone.
"""
from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

PRODUCT_DIR = str(Path(__file__).resolve().parents[1])
if PRODUCT_DIR not in sys.path:
    sys.path.insert(0, PRODUCT_DIR)

import app.api as api
import app.evidence_assessment as evidence_assessment
import app.source_health_timeline as source_health_timeline
import app.review_queue as review_queue
import app.evidence_records as evidence_records
from app.api import _Handler

_VICTIM_NAME = "ACME Internal Compliance Feed"
_VICTIM_URL = "https://acme-private.example/regulatory-inbox"
_VICTIM_NOTE = "MLRO flagged: internal counsel escalation pending, do not disclose to client"

_OWNER_ID = 1
_ATTACKER_ID = 2

# custom-A is owned by user 1 (denied to user 2); official-X is shared.
_SOURCES = [
    {"source_id": "custom-A", "custom": True, "owner_user_id": _OWNER_ID,
     "name": _VICTIM_NAME, "url": _VICTIM_URL, "jurisdiction": "AE",
     "enabled": True, "category": "financial_regulator", "status": "active"},
    {"source_id": "official-X", "name": "CBUAE — Public Notices",
     "url": "https://www.centralbank.ae/en/notices", "jurisdiction": "AE",
     "enabled": True, "category": "central_bank", "status": "active"},
]


def _make_handler(method: str = "GET", path: str = "/") -> _Handler:
    header_map = {"Content-Length": "0", "X-Real-IP": "10.0.0.5"}
    handler = _Handler.__new__(_Handler)
    handler.command = method
    handler.path = path
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    handler.headers = hdrs

    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _payload(handler: _Handler) -> dict:
    return handler._sent[-1][0]  # type: ignore[attr-defined]


def _status(handler: _Handler) -> int:
    return handler._sent[-1][1]  # type: ignore[attr-defined]


def _auth(monkeypatch, user_id: int) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": user_id, "email": "u@x.io"})


def _patch_sources(monkeypatch) -> None:
    """The denied-set is computed from source_intake.load_sources_json."""
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: list(_SOURCES))


def _seed_victim_run(tmp_path: Path) -> None:
    runs_dir = tmp_path / "data" / "source_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "source_runs.jsonl").write_text(
        json.dumps({
            "run_id": "r-A", "source_id": "custom-A", "market": "AE",
            "source_name": _VICTIM_NAME, "official_url": _VICTIM_URL,
            "normalized_hash": "deadbeef", "change_status": "CHANGED",
            "diff_md_path": "data/diffs/r-A.md",
            "timestamp_utc": "2026-07-01T00:00:00Z",
        }) + "\n",
        encoding="utf-8",
    )
    diff_dir = tmp_path / "data" / "diffs"
    diff_dir.mkdir(parents=True, exist_ok=True)
    (diff_dir / "r-A.md").write_text(
        f"# diff for {_VICTIM_NAME}\n- private internal policy text change\n", encoding="utf-8"
    )


def _seed_victim_assessment(tmp_path: Path) -> None:
    assess_dir = tmp_path / "data" / "evidence_assessments"
    assess_dir.mkdir(parents=True, exist_ok=True)
    (assess_dir / "assessments.jsonl").write_text(
        json.dumps({
            "assessment_id": "as-1", "evidence_record_id": "r-A",
            "source_id": "custom-A", "source_name": _VICTIM_NAME,
            "official_url": _VICTIM_URL, "impact_level": "escalate",
            "internal_note": _VICTIM_NOTE, "reviewer_name": "victim-owner",
        }) + "\n",
        encoding="utf-8",
    )


def _seed_canonical_record(tmp_path: Path) -> None:
    rec_dir = tmp_path / "evidence" / "custom-A" / "run-1"
    rec_dir.mkdir(parents=True, exist_ok=True)
    (rec_dir / "evidence-record.json").write_text(
        json.dumps({
            "record_id": "rec-A",
            "source": {"source_id": "custom-A", "regulator": _VICTIM_NAME},
            "run": {"run_id": "r-A", "status": "ok"},
            "review": {"review_status": "pending"},
        }),
        encoding="utf-8",
    )


# ── Read paths ──────────────────────────────────────────────────────────────


def test_evidence_review_scoped(monkeypatch, tmp_path):
    _seed_victim_run(tmp_path)
    _seed_victim_assessment(tmp_path)
    monkeypatch.setattr(evidence_assessment, "_BASE_DIR", tmp_path)
    _patch_sources(monkeypatch)

    _auth(monkeypatch, _ATTACKER_ID)
    h = _make_handler("GET", "/api/evidence/review?evidence_record_id=r-A")
    h._handle_evidence_review_get()
    assert _status(h) == 403
    blob = json.dumps(_payload(h))
    assert _VICTIM_NAME not in blob and _VICTIM_URL not in blob and _VICTIM_NOTE not in blob

    _auth(monkeypatch, _OWNER_ID)
    h2 = _make_handler("GET", "/api/evidence/review?evidence_record_id=r-A")
    h2._handle_evidence_review_get()
    assert _status(h2) == 200
    assert _VICTIM_NAME in json.dumps(_payload(h2))


def test_evidence_review_history_scoped(monkeypatch, tmp_path):
    _seed_victim_run(tmp_path)
    _seed_victim_assessment(tmp_path)
    monkeypatch.setattr(source_health_timeline, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(evidence_assessment, "_BASE_DIR", tmp_path)
    _patch_sources(monkeypatch)

    _auth(monkeypatch, _ATTACKER_ID)
    h = _make_handler("GET", "/api/evidence/review-history?evidence_record_id=r-A")
    h._handle_evidence_review_history_get()
    assert _status(h) == 403
    blob = json.dumps(_payload(h))
    assert _VICTIM_NAME not in blob and _VICTIM_URL not in blob and _VICTIM_NOTE not in blob

    _auth(monkeypatch, _OWNER_ID)
    h2 = _make_handler("GET", "/api/evidence/review-history?evidence_record_id=r-A")
    h2._handle_evidence_review_history_get()
    assert _status(h2) == 200
    assert _VICTIM_NAME in json.dumps(_payload(h2))


def test_evidence_diff_scoped(monkeypatch, tmp_path):
    _seed_victim_run(tmp_path)
    monkeypatch.setattr(api, "BASE_DIR", tmp_path)
    _patch_sources(monkeypatch)

    _auth(monkeypatch, _ATTACKER_ID)
    h = _make_handler("GET", "/api/evidence/diff?run_id=r-A")
    h._handle_evidence_diff_get()
    assert _status(h) == 404  # same 404 as "no diff" — no existence oracle
    assert _VICTIM_NAME not in json.dumps(_payload(h))

    _auth(monkeypatch, _OWNER_ID)
    h2 = _make_handler("GET", "/api/evidence/diff?run_id=r-A")
    h2._handle_evidence_diff_get()
    assert _status(h2) == 200
    assert _VICTIM_NAME in json.dumps(_payload(h2))


def test_reviews_queue_scoped(monkeypatch, tmp_path):
    _seed_victim_run(tmp_path)
    monkeypatch.setattr(review_queue, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(evidence_assessment, "_BASE_DIR", tmp_path)
    _patch_sources(monkeypatch)

    _auth(monkeypatch, _ATTACKER_ID)
    h = _make_handler("GET", "/api/reviews/queue?market=AE&status=all")
    h._handle_reviews_queue_get()
    blob = json.dumps(_payload(h))
    ids = {r.get("source_id") for r in _payload(h).get("queue", [])}
    assert "custom-A" not in ids and _VICTIM_NAME not in blob and _VICTIM_URL not in blob

    _auth(monkeypatch, _OWNER_ID)
    h2 = _make_handler("GET", "/api/reviews/queue?market=AE&status=all")
    h2._handle_reviews_queue_get()
    ids2 = {r.get("source_id") for r in _payload(h2).get("queue", [])}
    assert "custom-A" in ids2


def test_briefs_list_scoped(monkeypatch, tmp_path):
    alert_dir = tmp_path / "data" / "alert_queue"
    alert_dir.mkdir(parents=True)
    (alert_dir / "20260701T000000-custom-A-r-A-1234.json").write_text(
        json.dumps({
            "source_id": "custom-A", "run_id": "r-A", "change_status": "CHANGED",
            "status": "PENDING_REVIEW", "notes": "internal MLRO note about ACME account",
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(api, "BASE_DIR", tmp_path)
    _patch_sources(monkeypatch)

    _auth(monkeypatch, _ATTACKER_ID)
    h = _make_handler("GET", "/api/briefs?market=ALL")
    h._handle_briefs_list()
    ids = {b.get("source_id") for b in _payload(h).get("briefs", [])}
    assert "custom-A" not in ids
    assert "ACME account" not in json.dumps(_payload(h))

    _auth(monkeypatch, _OWNER_ID)
    h2 = _make_handler("GET", "/api/briefs?market=ALL")
    h2._handle_briefs_list()
    ids2 = {b.get("source_id") for b in _payload(h2).get("briefs", [])}
    assert "custom-A" in ids2


def test_briefs_generate_scoped(monkeypatch, tmp_path):
    _seed_victim_run(tmp_path)
    monkeypatch.setattr(api, "BASE_DIR", tmp_path)
    monkeypatch.setattr("app.config.ENABLE_AI_ANALYSIS", False, raising=False)
    _patch_sources(monkeypatch)

    _auth(monkeypatch, _ATTACKER_ID)
    h = _make_handler("POST", "/api/briefs/generate")
    h._read_json_strict = lambda: ({"source_id": "custom-A", "run_id": "r-A"}, None)  # type: ignore[method-assign]
    h._handle_briefs_generate()
    assert _status(h) == 403
    blob = json.dumps(_payload(h))
    assert _VICTIM_NAME not in blob and _VICTIM_URL not in blob

    _auth(monkeypatch, _OWNER_ID)
    h2 = _make_handler("POST", "/api/briefs/generate")
    h2._read_json_strict = lambda: ({"source_id": "custom-A", "run_id": "r-A"}, None)  # type: ignore[method-assign]
    h2._handle_briefs_generate()
    assert _status(h2) != 403
    assert _VICTIM_NAME in json.dumps(_payload(h2))


def test_canonical_evidence_scoped(monkeypatch, tmp_path):
    _seed_canonical_record(tmp_path)
    monkeypatch.setattr(evidence_records, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(review_queue, "_BASE_DIR", tmp_path)
    _patch_sources(monkeypatch)

    _auth(monkeypatch, _ATTACKER_ID)
    h = _make_handler("GET", "/api/canonical-evidence")
    h._handle_canonical_evidence_get()
    blob = json.dumps(_payload(h))
    assert "custom-A" not in blob and _VICTIM_NAME not in blob

    _auth(monkeypatch, _OWNER_ID)
    h2 = _make_handler("GET", "/api/canonical-evidence")
    h2._handle_canonical_evidence_get()
    assert "custom-A" in json.dumps(_payload(h2))


# ── Write paths (IDOR) ──────────────────────────────────────────────────────


def test_evidence_assess_write_idor_blocked(monkeypatch, tmp_path):
    _seed_victim_run(tmp_path)
    monkeypatch.setattr(evidence_assessment, "_BASE_DIR", tmp_path)
    _patch_sources(monkeypatch)

    _auth(monkeypatch, _ATTACKER_ID)
    h = _make_handler("POST", "/api/evidence/assess")
    h._read_json_strict = lambda: (  # type: ignore[method-assign]
        {"evidence_record_id": "r-A", "impact_level": "escalate", "internal_note": "x"},
        None,
    )
    h._handle_evidence_assess()
    assert _status(h) == 403
    # No assessment for the victim's record may be written by the attacker.
    store = tmp_path / "data" / "evidence_assessments" / "assessments.jsonl"
    assert not store.exists() or "r-A" not in store.read_text(encoding="utf-8")

    # Owner passes the scope gate (may 400 later on missing proof artifact, but
    # never the scope-denied 403).
    _auth(monkeypatch, _OWNER_ID)
    h2 = _make_handler("POST", "/api/evidence/assess")
    h2._read_json_strict = lambda: (  # type: ignore[method-assign]
        {"evidence_record_id": "r-A", "impact_level": "escalate", "internal_note": "x"},
        None,
    )
    h2._handle_evidence_assess()
    assert _status(h2) != 403


def test_canonical_review_action_write_idor_blocked(monkeypatch, tmp_path):
    _seed_canonical_record(tmp_path)
    monkeypatch.setattr(evidence_records, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(review_queue, "_BASE_DIR", tmp_path)
    _patch_sources(monkeypatch)

    _auth(monkeypatch, _ATTACKER_ID)
    h = _make_handler("POST", "/api/canonical-evidence/review")
    h._read_json_strict = lambda: (  # type: ignore[method-assign]
        {"record_id": "rec-A", "decision": "approve", "note": "n"},
        None,
    )
    h._handle_canonical_evidence_review_action()
    assert _status(h) == 403

    _auth(monkeypatch, _OWNER_ID)
    h2 = _make_handler("POST", "/api/canonical-evidence/review")
    h2._read_json_strict = lambda: (  # type: ignore[method-assign]
        {"record_id": "rec-A", "decision": "approve", "note": "n"},
        None,
    )
    h2._handle_canonical_evidence_review_action()
    assert _status(h2) != 403
