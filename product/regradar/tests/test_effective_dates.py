"""Tests for app/effective_dates.py — the effective-date / key-date calendar.

The calendar is a MONITORING view: every date is a string DETECTED in the
changed text of a monitored source and sealed into an evidence record — never
the reader's legal deadline, never advice, never a completeness claim. These
tests pin the legally load-bearing behaviour:

* dates are parsed from real change text, and text with no date yields NONE
  (no fabrication);
* the coarse type hint is derived from the surrounding wording;
* each emitted date links to a real SEALED record_hash + evidence_record_id;
* out-of-scope / other-tenant records are excluded;
* the horizon window filters correctly;
* every authored string passes the shared forbidden-claims guard.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from app.effective_dates import (
    VIEW_FRAMING,
    _read_sealed_diff_text,
    extract_key_dates_from_change,
    upcoming_key_dates,
)
from app.legal_safety import assert_no_forbidden_claims


_CHUNK_REPORT_WITH_REPEAL = """# Source Diff

## Removed Chunks

```text
The compliance filing deadline of 1 September 2026 is hereby repealed.
```

## Changed Chunks

### Change 1

Before:
```text
Firms must comply by 15 March 2027.
```

After:
```text
Firms must comply by 30 June 2028.
```

## Added Chunks

```text
A new obligation takes effect on 1 January 2029.
```
"""


def test_sealed_markdown_report_excludes_removed_and_before_dates(tmp_path):
    # A date that a change REMOVED (## Removed Chunks) or REPLACED (the "Before:"
    # side) must never reach the date extractor — otherwise a repealed deadline
    # would surface on the calendar as an upcoming obligation. Only the added /
    # After side is returned. (verify-swarm 2026-07-12)
    diff_path = tmp_path / "diff.md"
    diff_path.write_text(_CHUNK_REPORT_WITH_REPEAL, encoding="utf-8")
    text = _read_sealed_diff_text(tmp_path, "diff.md")
    assert text is not None
    assert "1 September 2026" not in text   # repealed (Removed Chunks)
    assert "15 March 2027" not in text      # superseded (Before:)
    assert "30 June 2028" in text           # new obligation (After:)
    assert "1 January 2029" in text         # new obligation (Added Chunks)


def test_unified_diff_still_extracts_added_only(tmp_path):
    diff_path = tmp_path / "diff.txt"
    diff_path.write_text(
        "--- prev\n+++ curr\n@@ -1 +1 @@\n"
        "-The old deadline was 15 March 2027.\n"
        "+The new deadline is 30 June 2028.\n",
        encoding="utf-8",
    )
    text = _read_sealed_diff_text(tmp_path, "diff.txt")
    assert text is not None
    assert "15 March 2027" not in text
    assert "30 June 2028" in text


def test_oversize_sealed_diff_is_skipped_not_silently_truncated(tmp_path):
    """A sealed diff larger than the read cap returns None (no partial diff).

    Regression: the previous read used ``fh.read(_MAX_DIFF_BYTES)``, which
    silently returned the truncated prefix — surfacing dates only from the head
    of the diff and MISSING every date in the dropped tail. It must instead skip
    the artifact so the record is dropped rather than surfaced from a partial diff.
    """
    from app.effective_dates import _MAX_DIFF_BYTES

    # A date near the very END of an over-cap unified diff — inside the tail that
    # a truncating read would drop.
    filler = "\n".join(f"+filler line {i}" for i in range(_MAX_DIFF_BYTES // 10))
    oversize = (
        "--- prev\n+++ curr\n@@ -1 +1 @@\n"
        + filler
        + "\n+The effective date is 30 June 2028.\n"
    )
    assert len(oversize) > _MAX_DIFF_BYTES  # genuinely over the cap
    diff_path = tmp_path / "huge.txt"
    diff_path.write_text(oversize, encoding="utf-8")

    assert _read_sealed_diff_text(tmp_path, "huge.txt") is None


def test_diff_exactly_at_cap_is_read_not_skipped(tmp_path):
    """A diff at/under the cap is read normally (off-by-one boundary)."""
    from app.effective_dates import _MAX_DIFF_BYTES

    body = "--- prev\n+++ curr\n@@ -1 +1 @@\n+The effective date is 30 June 2028.\n"
    body += "+" + "x" * (_MAX_DIFF_BYTES - len(body) - 2) + "\n"
    assert len(body) <= _MAX_DIFF_BYTES
    diff_path = tmp_path / "atcap.txt"
    diff_path.write_text(body, encoding="utf-8")

    text = _read_sealed_diff_text(tmp_path, "atcap.txt")
    assert text is not None
    assert "30 June 2028" in text


# ── fixtures ───────────────────────────────────────────────────────────────────

def _make_record(
    base: Path,
    *,
    source_id: str,
    regulator_slug: str,
    regulator: str,
    source_name: str,
    run_id: str,
    record_id: str,
    timestamp: str,
    current_text: str,
    previous_text: str = "The previous official text carried no dated provisions.",
    record_hash: str = "sha256:deadbeefcafe",
    status: str = "CHANGED",
) -> dict:
    """Write a canonical-shaped evidence record on disk and return it.

    Mirrors the real writer's on-disk shape closely enough for
    ``list_canonical_evidence_records`` to enumerate it and for the calendar to
    reconstruct the changed text from the previous/current normalized snapshots.
    """
    record_dir = base / "evidence" / regulator_slug / source_id / run_id
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "current.normalized.txt").write_text(current_text, encoding="utf-8")
    (record_dir / "previous.normalized.txt").write_text(previous_text, encoding="utf-8")

    record = {
        "schema_version": "2.0",
        "record_id": record_id,
        "record_status": "complete",
        "record_hash": record_hash,
        "record_hash_method": "sha256-canonical-json-v1",
        "source": {
            "source_id": source_id,
            "regulator": regulator,
            "official_url": f"https://www.{regulator_slug}.ae/example",
            "source_name": source_name,
        },
        "run": {"run_id": run_id, "timestamp": timestamp, "status": status},
        "content": {
            "current_hash": "sha256:aa",
            "previous_hash": "sha256:bb",
            "normalized_current_path": str((record_dir / "current.normalized.txt").relative_to(base)),
            "normalized_previous_path": str((record_dir / "previous.normalized.txt").relative_to(base)),
        },
        "change": {"summary": "changed", "lines_added": 1, "lines_removed": 1},
        "files": {
            "normalized_path": str((record_dir / "current.normalized.txt").relative_to(base)),
            "previous_path": str((record_dir / "previous.normalized.txt").relative_to(base)),
        },
        "integrity": {"hash_verified": True, "integrity_status": "VERIFIED", "verified_at": timestamp},
        "review": {"human_review_required": True, "review_status": "approved", "review_reason": "review"},
    }
    (record_dir / "evidence-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True), encoding="utf-8"
    )
    return record


def _cbuae(base: Path, **kwargs) -> dict:
    defaults = dict(
        source_id="cbuae",
        regulator_slug="cbuae",
        regulator="CBUAE",
        source_name="CBUAE Rulebook",
        run_id="run_cbuae_1",
        record_id="evr_cbuae_1",
        timestamp="2026-07-01T09:00:00Z",
        current_text="The revised capital rules are effective from 1 September 2026.",
    )
    defaults.update(kwargs)
    return _make_record(base, **defaults)


# ── pure extraction ─────────────────────────────────────────────────────────────

def test_dates_parsed_from_real_change_text():
    text = (
        "The new rules are effective from 1 September 2026. "
        "Comments on the consultation close on 30 September 2026."
    )
    dates = extract_key_dates_from_change(
        text, source_id="cbuae", source_name="CBUAE Rulebook",
        evidence_record_id="evr_1", record_hash="sha256:abc", captured_at="2026-07-01T00:00:00Z",
    )
    resolved = {d["date"] for d in dates}
    assert "2026-09-01" in resolved
    assert "2026-09-30" in resolved


def test_text_with_no_date_yields_none_no_fabrication():
    text = "This paragraph is about licensing and reporting duties but names no date."
    assert extract_key_dates_from_change(text, source_id="x") == []


def test_type_hint_is_derived_from_surrounding_words():
    effective = extract_key_dates_from_change("These rules are effective from 1 September 2026.")
    assert effective and effective[0]["detected_type"] == "effective_date"

    consult = extract_key_dates_from_change(
        "The consultation closes on 30 September 2026 for public comment."
    )
    assert consult and consult[0]["detected_type"] == "consultation_close"

    deadline = extract_key_dates_from_change(
        "Firms must file the return no later than 15 October 2026."
    )
    assert deadline and deadline[0]["detected_type"] == "deadline"


def test_extracted_item_carries_verification_pointer_and_framing():
    dates = extract_key_dates_from_change(
        "Effective from 1 September 2026.",
        source_id="cbuae", source_name="CBUAE Rulebook",
        evidence_record_id="evr_1", record_hash="sha256:sealedhash", captured_at="2026-07-01T00:00:00Z",
    )
    assert len(dates) == 1
    item = dates[0]
    assert item["record_hash"] == "sha256:sealedhash"
    assert item["evidence_record_id"] == "evr_1"
    assert "detected in the changed text" in item["framing"].lower()
    assert item["disclaimer"] == "For monitoring information only. Not legal advice and not a guarantee of compliance."


def test_excerpt_and_date_count_are_bounded():
    # A pile of dates in one blob must be capped and excerpts trimmed.
    text = " ".join(f"effective from {d} January 2026." for d in range(1, 40))
    dates = extract_key_dates_from_change(text, max_dates=5)
    assert len(dates) <= 5
    assert all(len(d["excerpt"]) <= 240 for d in dates)


# ── forward-looking calendar (orchestration + tenancy) ──────────────────────────

def test_calendar_lists_upcoming_dates_linked_to_sealed_record(tmp_path):
    _cbuae(tmp_path, record_hash="sha256:sealed-cbuae")
    result = upcoming_key_dates(as_of=date(2026, 7, 1), base_dir=tmp_path)
    assert result["count"] == 1
    item = result["dates"][0]
    assert item["date"] == "2026-09-01"
    assert item["detected_type"] == "effective_date"
    assert item["record_hash"] == "sha256:sealed-cbuae"
    assert item["evidence_record_id"] == "evr_cbuae_1"
    assert item["source_name"] == "CBUAE Rulebook"
    assert item["days_until"] == (date(2026, 9, 1) - date(2026, 7, 1)).days


def test_horizon_window_filters_dates(tmp_path):
    # Within the default 90-day window (Sep 1).
    _cbuae(tmp_path)
    # Far outside (Mar 2027) — must be excluded at horizon 90.
    _cbuae(
        tmp_path,
        source_id="dfsa",
        regulator_slug="dfsa",
        regulator="DFSA",
        source_name="DFSA Handbook",
        run_id="run_dfsa_far",
        record_id="evr_dfsa_far",
        current_text="This regime is effective from 1 March 2027.",
    )
    narrow = upcoming_key_dates(as_of=date(2026, 7, 1), horizon_days=90, base_dir=tmp_path)
    assert {d["date"] for d in narrow["dates"]} == {"2026-09-01"}

    # A wide horizon reaches the March 2027 date.
    wide = upcoming_key_dates(as_of=date(2026, 7, 1), horizon_days=365, base_dir=tmp_path)
    assert "2027-03-01" in {d["date"] for d in wide["dates"]}


def test_past_dates_are_excluded_by_default(tmp_path):
    _cbuae(
        tmp_path,
        run_id="run_past",
        record_id="evr_past",
        current_text="Those rules were effective from 1 January 2026.",
    )
    result = upcoming_key_dates(as_of=date(2026, 7, 1), base_dir=tmp_path)
    assert result["count"] == 0


def test_explicit_from_to_window(tmp_path):
    _cbuae(tmp_path)  # 2026-09-01
    inside = upcoming_key_dates(
        base_dir=tmp_path, as_of=date(2026, 7, 1),
        date_from=date(2026, 8, 1), date_to=date(2026, 10, 1),
    )
    assert {d["date"] for d in inside["dates"]} == {"2026-09-01"}
    outside = upcoming_key_dates(
        base_dir=tmp_path, as_of=date(2026, 7, 1),
        date_from=date(2026, 10, 1), date_to=date(2026, 12, 1),
    )
    assert outside["count"] == 0


def test_excluded_source_ids_drops_other_tenant_records(tmp_path):
    _cbuae(tmp_path)  # official source, always in scope
    _make_record(
        tmp_path,
        source_id="custom-B",
        regulator_slug="custom",
        regulator="Custom",
        source_name="Another tenant private source",
        run_id="run_custom_b",
        record_id="evr_custom_b",
        timestamp="2026-07-01T09:00:00Z",
        current_text="This private rule is effective from 5 September 2026.",
    )
    # Default view WITHOUT the deny-list would see both; the tenancy guard drops
    # the custom source owned by another tenant.
    guarded = upcoming_key_dates(
        as_of=date(2026, 7, 1), base_dir=tmp_path, excluded_source_ids={"custom-B"}
    )
    ids = {d["source_id"] for d in guarded["dates"]}
    assert ids == {"cbuae"}


def test_allow_list_restricts_to_named_sources(tmp_path):
    _cbuae(tmp_path)
    _make_record(
        tmp_path,
        source_id="dfsa",
        regulator_slug="dfsa",
        regulator="DFSA",
        source_name="DFSA Handbook",
        run_id="run_dfsa",
        record_id="evr_dfsa",
        timestamp="2026-07-01T09:00:00Z",
        current_text="Effective from 3 September 2026.",
    )
    only_cbuae = upcoming_key_dates(
        as_of=date(2026, 7, 1), base_dir=tmp_path, source_ids=["cbuae"]
    )
    assert {d["source_id"] for d in only_cbuae["dates"]} == {"cbuae"}


def test_non_changed_records_are_skipped(tmp_path):
    _cbuae(
        tmp_path,
        run_id="run_unchanged",
        record_id="evr_unchanged",
        current_text="Effective from 9 September 2026.",
        status="UNCHANGED",
    )
    result = upcoming_key_dates(as_of=date(2026, 7, 1), base_dir=tmp_path)
    assert result["count"] == 0


def test_duplicate_date_dedupes_to_earliest_capture(tmp_path):
    _cbuae(tmp_path, run_id="run_late", record_id="evr_late", timestamp="2026-07-10T00:00:00Z",
           record_hash="sha256:late")
    _cbuae(tmp_path, run_id="run_early", record_id="evr_early", timestamp="2026-07-01T00:00:00Z",
           record_hash="sha256:early")
    result = upcoming_key_dates(as_of=date(2026, 7, 1), base_dir=tmp_path)
    assert result["count"] == 1
    # Earliest capture wins — its sealed hash is the one that ships.
    assert result["dates"][0]["record_hash"] == "sha256:early"


def test_empty_evidence_tree_yields_empty_calendar(tmp_path):
    result = upcoming_key_dates(as_of=date(2026, 7, 1), base_dir=tmp_path)
    assert result["count"] == 0
    assert result["dates"] == []
    assert result["horizon"]["days"] == 90


# ── legal-safety ────────────────────────────────────────────────────────────────

def test_authored_strings_pass_forbidden_claims_guard(tmp_path):
    _cbuae(tmp_path)
    result = upcoming_key_dates(as_of=date(2026, 7, 1), base_dir=tmp_path)
    # View-level framing + disclaimer.
    assert_no_forbidden_claims(VIEW_FRAMING)
    assert_no_forbidden_claims(result["framing"])
    assert_no_forbidden_claims(result["disclaimer"])
    # Per-date authored framing + type label.
    for item in result["dates"]:
        assert_no_forbidden_claims(item["framing"])
        assert_no_forbidden_claims(item["type_label"])
    # Honest framing never promises an outcome or asserts the reader's deadline.
    lowered = VIEW_FRAMING.lower()
    assert "not legal deadlines" in lowered
    assert "verify" in lowered


def test_horizon_days_are_clamped(tmp_path):
    over = upcoming_key_dates(as_of=date(2026, 7, 1), base_dir=tmp_path, horizon_days=99999)
    assert over["horizon"]["days"] == 365
    under = upcoming_key_dates(as_of=date(2026, 7, 1), base_dir=tmp_path, horizon_days=0)
    assert under["horizon"]["days"] == 1


def test_truncated_snapshots_are_skipped_not_misaligned(tmp_path, monkeypatch):
    # Security rationale (effective_dates.py): if either normalized snapshot
    # exceeded the read bound it was truncated at an independent point, so a
    # re-diff could misalign and surface a date the sealed diff would not classify
    # as changed. The record must be SKIPPED, not have a spurious date surfaced.
    # (test-coverage audit 2026-07-13 — the comment had no backing test.)
    import app.effective_dates as ed

    monkeypatch.setattr(ed, "_MAX_SNAPSHOT_BYTES", 100)
    oversize = "x" * 150 + " The revised rules are effective from 1 September 2026."
    _cbuae(tmp_path, current_text=oversize, previous_text="y" * 150)
    result = upcoming_key_dates(as_of=date(2026, 7, 1), base_dir=tmp_path)
    assert result["count"] == 0
