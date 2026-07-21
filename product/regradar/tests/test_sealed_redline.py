"""Sealed-evidence redline — parser correctness, bounds, safety, resolution.

Proves the contract in app/sealed_redline.py:

1. PARSER — both sealed-diff shapes (markdown chunk report, difflib unified
   diff) parse into ordered added/removed blocks; nothing is fabricated.
2. BOUNDS — line count, per-line length, and input size are capped; a
   pathological artifact yields ``truncated`` instead of unbounded output.
3. READABILITY — unreadable (binary-saturated) lines are dropped and disclosed
   via ``partial``; legitimate Arabic official text is NOT dropped.
4. RESOLUTION — build_redline_for_match renders only a COMPLETE +
   integrity-VERIFIED record's sealed diff; a diff_path escaping the evidence
   root is refused (confinement); every failure mode is fail-soft with an
   honest note, never a raise.
5. LEGAL — all StatuteProof-authored copy passes the forbidden-claims guard at
   import time and rides on every payload with the short disclaimer.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.sealed_redline import (
    REDLINE_FRAMING,
    _MAX_LINE_CHARS,
    _MAX_TOTAL_LINES,
    build_redline_for_match,
    parse_sealed_diff_to_redline,
)
from app.legal_safety import assert_no_forbidden_claims
from app.materiality import SHORT_DISCLAIMER


# ── helpers ───────────────────────────────────────────────────────────────────

CHUNK_REPORT = """# Source Diff

- Previous run: intake-A
- Current run: intake-B
- Summary: 1 added, 1 removed, 1 changed chunks; 0 unchanged.

## Added Chunks

```text
New AML notification requirement text.
```

## Removed Chunks

```text
Old superseded paragraph.
```

## Changed Chunks

### Change 1

Before:
```text
The threshold is AED 55,000.
```

After:
```text
The threshold is AED 15,000.
```

## Limitations

Ignored section content.
"""

UNIFIED_DIFF = """--- previous
+++ current
@@ -1,3 +1,3 @@
 context line stays out
-The threshold is AED 55,000.
+The threshold is AED 15,000.
+A second added line.
"""


def _flat(parsed, op):
    return [line for b in parsed["blocks"] if b["op"] == op for line in b["lines"]]


def _write_sealed_record(tmp_path: Path, *, diff_text=CHUNK_REPORT, diff_rel="diff.txt",
                         integrity="VERIFIED", status="complete", diff_path_override=None):
    """Lay out evidence/<reg>/<source>/<run>/ with a record + sealed diff."""
    run_dir = tmp_path / "evidence" / "vara" / "AE-vara-test" / "intake-1"
    run_dir.mkdir(parents=True)
    (run_dir / diff_rel).write_text(diff_text, encoding="utf-8")
    record = {
        "record_status": status,
        "integrity": {"integrity_status": integrity},
        "record_hash": "ab" * 32,
        "change": {"diff_path": diff_path_override or f"evidence/vara/AE-vara-test/intake-1/{diff_rel}"},
        "files": {},
    }
    (run_dir / "evidence-record.json").write_text(json.dumps(record), encoding="utf-8")
    return {
        "alert_id": "draft-x1",
        "source_id": "AE-vara-test",
        "source_name": "VARA Test Source",
        "source_url": "https://example.gov.ae/x",
        "detected_at": "2026-07-12T00:00:00Z",
        "proof": {
            "run_id": "intake-1",
            "record_hash": "ab" * 32,
            "evidence_record_id": "rec-1",
            "diff_available": True,
        },
    }


# ── 1. parser: both sealed shapes ─────────────────────────────────────────────

def test_chunk_report_parses_added_removed_and_changed():
    parsed = parse_sealed_diff_to_redline(CHUNK_REPORT)
    assert parsed["available"] is True
    assert parsed["format"] == "chunk_report"
    added = _flat(parsed, "added")
    removed = _flat(parsed, "removed")
    assert "New AML notification requirement text." in added
    assert "The threshold is AED 15,000." in added          # After: → added
    assert "Old superseded paragraph." in removed
    assert "The threshold is AED 55,000." in removed        # Before: → removed
    # The Limitations section is never rendered as change lines.
    assert not any("Ignored section" in line for line in added + removed)


def test_unified_diff_parses_ops_and_skips_context_and_headers():
    parsed = parse_sealed_diff_to_redline(UNIFIED_DIFF)
    assert parsed["available"] is True
    assert parsed["format"] == "unified"
    added = _flat(parsed, "added")
    removed = _flat(parsed, "removed")
    assert added == ["The threshold is AED 15,000.", "A second added line."]
    assert removed == ["The threshold is AED 55,000."]
    joined = added + removed
    assert not any("context line" in line or line.startswith("+++") for line in joined)


def test_unknown_format_is_honestly_unavailable():
    parsed = parse_sealed_diff_to_redline("just some prose, no diff markers at all")
    assert parsed["available"] is False
    assert parsed["format"] == "none"
    assert parsed["blocks"] == []
    assert parsed["note"]  # honest explanation, not silence


def test_parser_never_fabricates_lines():
    parsed = parse_sealed_diff_to_redline(CHUNK_REPORT)
    for block in parsed["blocks"]:
        for line in block["lines"]:
            assert line.rstrip("…").strip()[:40] in CHUNK_REPORT


def test_unterminated_fence_content_is_kept_not_dropped():
    # A truncated artifact can end mid-fence; the collected lines are sealed
    # change text and must be flushed, not silently dropped (security-review
    # LOW, 2026-07-12).
    truncated_report = """## Added Chunks

```text
Trailing sealed line with no closing fence."""
    parsed = parse_sealed_diff_to_redline(truncated_report)
    assert parsed["available"] is True
    assert "Trailing sealed line with no closing fence." in _flat(parsed, "added")


# ── 2. bounds ─────────────────────────────────────────────────────────────────

def test_total_line_cap_truncates():
    many = "\n".join(f"+line {i}" for i in range(_MAX_TOTAL_LINES + 200))
    parsed = parse_sealed_diff_to_redline(f"@@ -1 +1 @@\n{many}\n")
    assert parsed["available"] is True
    assert parsed["added_lines"] <= _MAX_TOTAL_LINES
    assert parsed["truncated"] is True


def test_per_line_length_cap():
    long_line = "x" * (_MAX_LINE_CHARS * 3)
    parsed = parse_sealed_diff_to_redline(f"@@ -1 +1 @@\n+{long_line}\n")
    line = _flat(parsed, "added")[0]
    assert len(line) <= _MAX_LINE_CHARS
    assert line.endswith("…")


# ── 3. readability gate ───────────────────────────────────────────────────────

def test_binary_saturated_line_dropped_and_disclosed():
    binary = "\x00\x01\x02��� garbage \x07\x08"
    text = f"@@ -1 +1 @@\n+{binary}\n+A readable line.\n"
    parsed = parse_sealed_diff_to_redline(text)
    added = _flat(parsed, "added")
    assert added == ["A readable line."]
    assert parsed["partial"] is True
    assert parsed["note"]  # the drop is disclosed, not silent


def test_arabic_official_text_is_kept():
    arabic = "سُلطة تنظيم الأصول الافتراضية - Virtual Assets Regulatory Authority"
    parsed = parse_sealed_diff_to_redline(f"@@ -1 +1 @@\n+{arabic}\n")
    assert _flat(parsed, "added") == [arabic]
    assert parsed["partial"] is False


# ── 4. resolution: sealed-record gating + confinement ─────────────────────────

def test_happy_path_renders_redline_with_seal_pointer(tmp_path):
    match = _write_sealed_record(tmp_path)
    redline = build_redline_for_match(match, base_dir=tmp_path)
    assert redline["available"] is True
    assert redline["record_hash"] == "ab" * 32
    assert redline["source_name"] == "VARA Test Source"
    assert "The threshold is AED 15,000." in _flat(redline, "added")
    assert redline["framing"] == REDLINE_FRAMING
    assert redline["disclaimer"] == SHORT_DISCLAIMER


def test_unverified_integrity_is_refused(tmp_path):
    match = _write_sealed_record(tmp_path, integrity="TAMPERED")
    redline = build_redline_for_match(match, base_dir=tmp_path)
    assert redline["available"] is False
    assert redline["blocks"] == []


def test_incomplete_record_is_refused(tmp_path):
    match = _write_sealed_record(tmp_path, status="partial")
    assert build_redline_for_match(match, base_dir=tmp_path)["available"] is False


def test_diff_path_escaping_evidence_root_is_refused(tmp_path):
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("+leaked\n@@ -1 +1 @@\n", encoding="utf-8")
    match = _write_sealed_record(
        tmp_path, diff_path_override="evidence/vara/AE-vara-test/intake-1/../../../../../secret.txt"
    )
    redline = build_redline_for_match(match, base_dir=tmp_path)
    assert redline["available"] is False
    assert not any("leaked" in line for b in redline["blocks"] for line in b["lines"])


def test_absolute_foreign_diff_path_is_refused(tmp_path):
    outside = tmp_path.parent / "abs-secret.txt"
    outside.write_text("@@ -1 +1 @@\n+abs leaked\n", encoding="utf-8")
    match = _write_sealed_record(tmp_path, diff_path_override=str(outside))
    assert build_redline_for_match(match, base_dir=tmp_path)["available"] is False


def test_missing_proof_and_missing_diff_fail_soft(tmp_path):
    match = _write_sealed_record(tmp_path)
    no_proof = {**match, "proof": None}
    assert build_redline_for_match(no_proof, base_dir=tmp_path)["available"] is False
    no_diff = {**match, "proof": {**match["proof"], "diff_available": False}}
    assert build_redline_for_match(no_diff, base_dir=tmp_path)["available"] is False
    # Nothing above raised — the fail-soft contract held throughout.


# ── 5. legal safety ───────────────────────────────────────────────────────────

def test_all_payload_copy_passes_forbidden_claims_guard(tmp_path):
    match = _write_sealed_record(tmp_path)
    redline = build_redline_for_match(match, base_dir=tmp_path)
    assert_no_forbidden_claims(redline["framing"], label="redline framing")
    assert_no_forbidden_claims(redline["note"] or "ok", label="redline note")
    assert redline["disclaimer"] == SHORT_DISCLAIMER


# ── 6. HTTP endpoint (auth, validation, scope-by-preview, no-oracle 404) ──────

from io import BytesIO  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

import app.api as api  # noqa: E402
import app.api_alerts as api_alerts
from app.api import _Handler  # noqa: E402


def _make_handler(path: str) -> _Handler:
    header_map = {"Content-Length": "0", "X-Real-IP": "10.0.0.9"}
    handler = _Handler.__new__(_Handler)
    handler.command = "GET"
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
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _last(handler: _Handler) -> tuple[dict, int]:
    return handler._sent[-1]  # type: ignore[attr-defined]


def test_endpoint_requires_auth(monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: None)
    monkeypatch.setattr(api_alerts, "require_auth", lambda handler: None)
    handler = _make_handler("/api/alerts/redline?alert_id=draft-x1")
    handler._handle_alert_redline_get()
    _, status = _last(handler)
    assert status == 401


def test_endpoint_rejects_malformed_alert_id(monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": 1})
    monkeypatch.setattr(api_alerts, "require_auth", lambda handler: {"id": 1})
    handler = _make_handler("/api/alerts/redline?alert_id=..%2F..%2Fetc")
    handler._handle_alert_redline_get()
    _, status = _last(handler)
    assert status == 400


def test_endpoint_scopes_by_owner_lookup_and_404s_unknown(monkeypatch, tmp_path):
    """The alert is resolved ONLY through the owner-scoped targeted lookup."""
    # Entitlement is covered in tests/test_alert_plan_gating.py; this test is
    # about TENANCY, so take the plan gate out of the way.
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    match = _write_sealed_record(tmp_path)
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": 7})
    monkeypatch.setattr(api_alerts, "require_auth", lambda handler: {"id": 7})
    seen: list[tuple[int, str]] = []

    def fake_find(user_id, alert_id, days=14):
        seen.append((user_id, alert_id))
        return match if alert_id == "draft-x1" else None

    monkeypatch.setattr(api_alerts, "find_routing_match_for_user", fake_find)

    # Known alert (in the caller's scope) → redline payload.
    import app.sealed_redline as sr
    monkeypatch.setattr(sr, "build_redline_for_match", lambda m: {"available": True, "blocks": []})
    handler = _make_handler("/api/alerts/redline?alert_id=draft-x1")
    handler._handle_alert_redline_get()
    body, status = _last(handler)
    assert status == 200 and body["ok"] is True
    assert seen[0] == (7, "draft-x1")  # scope key came from the session, not the request

    # Unknown alert (another tenant's, or gone) → the same 404, no oracle.
    handler2 = _make_handler("/api/alerts/redline?alert_id=draft-not-mine")
    handler2._handle_alert_redline_get()
    body2, status2 = _last(handler2)
    assert status2 == 404
    assert body2["message"] == "Alert not found."


def test_ev1_tampered_sealed_diff_is_refused(tmp_path):
    """EV-1: when content.diff_hash is sealed, an in-place edit to diff.txt must
    make build_redline_for_match refuse to render it as a verified redline."""
    import hashlib
    import json as _json
    from app.sealed_redline import _INTEGRITY_NOTE

    match = _write_sealed_record(tmp_path)
    run_dir = tmp_path / "evidence" / "vara" / "AE-vara-test" / "intake-1"
    diff_file = run_dir / "diff.txt"
    rec_file = run_dir / "evidence-record.json"

    rec = _json.loads(rec_file.read_text(encoding="utf-8"))
    rec["content"] = {"diff_hash": "sha256:" + hashlib.sha256(diff_file.read_bytes()).hexdigest()}
    rec_file.write_text(_json.dumps(rec), encoding="utf-8")

    # Untampered: the sealed hash matches, so the redline still renders.
    assert build_redline_for_match(match, base_dir=tmp_path)["available"] is True

    # Tampered in place: hash mismatch -> refused with the integrity note.
    diff_file.write_text("```diff\n- original\n+ ATTACKER-INSERTED\n```\n", encoding="utf-8")
    out = build_redline_for_match(match, base_dir=tmp_path)
    assert out["available"] is False
    assert out["note"] == _INTEGRITY_NOTE
