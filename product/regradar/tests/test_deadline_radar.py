"""Tests for the effective-date & deadline radar (Feature 2).

Covers:
  * app.risk.derive_urgency_and_dates — captured date(s) returned alongside the
    urgency label, and the existing derive_urgency_from_text behaviour unchanged.
  * app.deadline_radar — date parsing, evidence-grounded persistence keyed by
    evidence_record_id, dedup, past-date handling, lead-stage reminders that
    fire once per stage, the mandatory disclaimer, and the forbidden-claims guard.
  * app.scheduler.run_deadline_reminder_pass — best-effort daily pass.
  * run.py deadlines subcommand — read-only listing with disclaimer.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

from app.change_register import ChangeRegisterError
from app.evidence_assessment import LEGAL_DISCLAIMER
from app.monthly_assurance_report import _FORBIDDEN_PHRASES
from app.risk import derive_urgency_and_dates, derive_urgency_from_text
from app import deadline_radar as dr


DEADLINE = date(2026, 9, 1)


# ── app.risk.derive_urgency_and_dates (additive matcher) ──────────────────────

def test_urgency_matcher_returns_captured_effective_date():
    text = "This rule is effective from 1 September 2026 for all licensees."
    urgency, dates = derive_urgency_and_dates(text)
    # label preserved (existing callers unaffected)
    assert urgency == derive_urgency_from_text(text)
    assert len(dates) == 1
    assert dates[0]["date_text"] == "1 September 2026"
    assert dates[0]["kind"] == "effective"
    assert "1 September 2026" in dates[0]["excerpt"]


def test_urgency_matcher_label_unchanged_for_existing_callers():
    # derive_urgency_from_text must keep returning its documented values.
    assert derive_urgency_from_text("") == "MONITOR"
    assert derive_urgency_from_text("effective from 01/09/2026") == "IMMEDIATE"
    assert derive_urgency_from_text("respond within 14 days") == "WITHIN_30_DAYS"
    # And the additive function agrees on the label.
    assert derive_urgency_and_dates("effective from 01/09/2026")[0] == "IMMEDIATE"


def test_urgency_matcher_empty_text_returns_no_dates():
    urgency, dates = derive_urgency_and_dates("")
    assert urgency == "MONITOR"
    assert dates == []


def test_urgency_matcher_tags_consultation_and_transition_kinds():
    _, con = derive_urgency_and_dates("The consultation closes on 1 September 2026.")
    assert con and con[0]["kind"] == "consultation_close"
    _, tr = derive_urgency_and_dates("The transition period ends on 1 September 2026.")
    assert tr and tr[0]["kind"] == "transition"


# ── date parsing ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        ("1 September 2026", date(2026, 9, 1)),
        ("01/09/2026", date(2026, 9, 1)),
        ("2026-09-01", date(2026, 9, 1)),
        ("September 2026", date(2026, 9, 30)),        # bare month -> end of month
        ("end of September 2026", date(2026, 9, 30)),
    ],
)
def test_parse_deadline_date_forms(text, expected):
    assert dr._parse_deadline_date(text) == expected


def test_parse_deadline_date_rejects_impossible_date():
    assert dr._parse_deadline_date("31 February 2026") is None
    assert dr._parse_deadline_date("not a date") is None


# ── extraction ────────────────────────────────────────────────────────────────

def test_extract_deadlines_from_effective_from_diff():
    """Task requirement: a diff containing 'effective from 1 September 2026'."""
    items = dr.extract_deadlines("The framework is effective from 1 September 2026.")
    assert len(items) == 1
    assert items[0]["deadline_date"] == "2026-09-01"
    assert items[0]["deadline_kind"] == "effective"
    assert "1 September 2026" in items[0]["extracted_from_diff_excerpt"]


def test_extract_deadlines_ignores_dateless_urgency():
    # "within 30 days" has no absolute date -> nothing to persist.
    assert dr.extract_deadlines("You must respond within 30 days.") == []


# ── persistence: evidence-grounded, keyed by evidence_record_id ───────────────

def test_record_deadlines_for_change_persists_future_date(tmp_path):
    persisted = dr.record_deadlines_for_change(
        evidence_record_id="run_abc",
        source_id="AE-dfsa",
        regulator="DFSA",
        source_name="DFSA Test",
        official_url="https://dfsa.example/x",
        added_blocks=["The framework is effective from 1 September 2026."],
        as_of=date(2026, 1, 1),
        base_dir=tmp_path,
    )
    assert len(persisted) == 1
    rec = persisted[0]
    assert rec["evidence_record_id"] == "run_abc"
    assert rec["deadline_date"] == "2026-09-01"
    assert rec["deadline_kind"] == "effective"
    assert rec["source_id"] == "AE-dfsa"
    assert rec["regulator"] == "DFSA"
    # evidence-grounded: the exact diff excerpt is stored
    assert "1 September 2026" in rec["extracted_from_diff_excerpt"]
    # legal safety fields
    assert rec["legal_disclaimer"] == LEGAL_DISCLAIMER
    assert rec["human_review_required"] is True

    # it is on disk in the JSONL register
    assert dr.deadline_register_path(tmp_path).exists()
    assert len(dr.load_deadlines(tmp_path)) == 1


def test_record_deadlines_dedup_no_duplicate_line(tmp_path):
    for _ in range(3):
        dr.record_deadlines_for_change(
            evidence_record_id="run_abc",
            added_blocks=["effective from 1 September 2026"],
            as_of=date(2026, 1, 1),
            base_dir=tmp_path,
        )
    assert len(dr.load_deadlines(tmp_path)) == 1


def test_record_deadlines_skips_past_dates(tmp_path):
    persisted = dr.record_deadlines_for_change(
        evidence_record_id="run_old",
        added_blocks=["effective from 1 September 2026"],
        as_of=date(2027, 1, 1),  # the date is already in the past
        base_dir=tmp_path,
    )
    assert persisted == []
    assert dr.load_deadlines(tmp_path) == []


def test_record_deadlines_include_past_stores(tmp_path):
    persisted = dr.record_deadlines_for_change(
        evidence_record_id="run_old",
        added_blocks=["effective from 1 September 2026"],
        as_of=date(2027, 1, 1),
        include_past=True,
        base_dir=tmp_path,
    )
    assert len(persisted) == 1


def test_one_date_two_patterns_yields_single_deadline_and_reminder(tmp_path):
    # WARN-5: "comments are due by <date>" matches BOTH consultation_close AND
    # the generic 'deadline' pattern. It must collapse to ONE deadline (keeping
    # the most specific kind) so it fires ONE reminder per lead stage, not two.
    text = "Comments are due by 30 September 2026 for the consultation."
    items = dr.extract_deadlines(text)
    assert len(items) == 1
    assert items[0]["deadline_kind"] == "consultation_close"  # specific beats generic

    persisted = dr.record_deadlines_for_change(
        evidence_record_id="run_c1",
        added_blocks=[text],
        as_of=date(2026, 9, 1),
        base_dir=tmp_path,
    )
    assert len(persisted) == 1
    assert len(dr.load_deadlines(tmp_path)) == 1
    # One deadline record → exactly one due reminder (pre-fix this was two).
    due = dr.due_reminders(as_of=date(2026, 9, 1), base_dir=tmp_path)
    assert len(due) == 1


def test_reminder_surfaces_raw_date_text_and_flags_ambiguous_numeric(tmp_path):
    # WARN-5 (low): surface the raw captured text next to the parsed ISO date and
    # flag a dd/mm↔mm/dd numeric form for human verification.
    text = "The framework is effective from 01/09/2026."
    persisted = dr.record_deadlines_for_change(
        evidence_record_id="run_amb",
        added_blocks=[text],
        as_of=date(2026, 1, 1),
        base_dir=tmp_path,
    )
    assert len(persisted) == 1
    rec = persisted[0]
    assert rec["deadline_date"] == "2026-09-01"       # day-first by convention
    assert rec["raw_date_text"] == "01/09/2026"
    assert rec["date_ambiguous"] is True

    entry = {**rec, "lead_stage": 30, "days_until": 30}
    msg = dr.render_reminder_message(entry)
    assert "01/09/2026" in msg               # raw source text surfaced
    assert "ambiguous" in msg.lower()        # flagged for human verification
    assert LEGAL_DISCLAIMER in msg


def test_named_month_date_is_not_flagged_ambiguous(tmp_path):
    persisted = dr.record_deadlines_for_change(
        evidence_record_id="run_named",
        added_blocks=["effective from 1 September 2026"],
        as_of=date(2026, 1, 1),
        base_dir=tmp_path,
    )
    assert persisted[0]["date_ambiguous"] is False


def test_record_deadline_requires_evidence_grounding(tmp_path):
    # Missing evidence_record_id -> refuse (not evidence-grounded).
    with pytest.raises(ValueError):
        dr.record_deadline(
            evidence_record_id="",
            deadline_date="2026-09-01",
            deadline_kind="effective",
            extracted_from_diff_excerpt="effective from 1 September 2026",
            base_dir=tmp_path,
        )
    # Missing diff excerpt -> refuse.
    with pytest.raises(ValueError):
        dr.record_deadline(
            evidence_record_id="run_x",
            deadline_date="2026-09-01",
            deadline_kind="effective",
            extracted_from_diff_excerpt="   ",
            base_dir=tmp_path,
        )
    # Unknown kind -> refuse.
    with pytest.raises(ValueError):
        dr.record_deadline(
            evidence_record_id="run_x",
            deadline_date="2026-09-01",
            deadline_kind="made_up",
            extracted_from_diff_excerpt="x",
            base_dir=tmp_path,
        )
    assert dr.load_deadlines(tmp_path) == []


# ── upcoming listing ──────────────────────────────────────────────────────────

def test_upcoming_deadlines_sorted_and_excludes_past(tmp_path):
    dr.record_deadline(
        evidence_record_id="r1", deadline_date="2026-09-01", deadline_kind="effective",
        extracted_from_diff_excerpt="x", base_dir=tmp_path,
    )
    dr.record_deadline(
        evidence_record_id="r2", deadline_date="2026-07-01", deadline_kind="deadline",
        extracted_from_diff_excerpt="y", base_dir=tmp_path,
    )
    rows = dr.upcoming_deadlines(as_of=date(2026, 6, 1), base_dir=tmp_path)
    assert [r["deadline_date"] for r in rows] == ["2026-07-01", "2026-09-01"]
    assert rows[0]["days_until"] == 30

    # a date in the past is excluded by default, included with include_past
    past = dr.upcoming_deadlines(as_of=date(2026, 8, 1), base_dir=tmp_path)
    assert [r["deadline_date"] for r in past] == ["2026-09-01"]
    all_rows = dr.upcoming_deadlines(as_of=date(2026, 8, 1), include_past=True, base_dir=tmp_path)
    assert len(all_rows) == 2


# ── reminders: once per lead stage, dedup, past never fires ───────────────────

def _seed_one(tmp_path, ev_id="run_r", kind="effective"):
    dr.record_deadline(
        evidence_record_id=ev_id,
        deadline_date=DEADLINE.isoformat(),
        deadline_kind=kind,
        extracted_from_diff_excerpt="effective from 1 September 2026",
        source_id="AE-x", regulator="DFSA", source_name="DFSA",
        official_url="https://dfsa.example/x",
        base_dir=tmp_path,
    )


def test_reminder_fires_once_per_lead_stage(tmp_path):
    _seed_one(tmp_path)
    sent: list[str] = []

    def fake_send(chat_id, text):
        sent.append(text)
        return True

    def run(days_before):
        return dr.send_due_reminders(
            as_of=DEADLINE - timedelta(days=days_before),
            base_dir=tmp_path,
            send_fn=fake_send,
            recipients=["123"],
            require_review_approval=False,  # timing/dedup test — review gate covered separately
        )

    # too far out -> no reminder
    assert run(40)["sent"] == []
    # 30-day stage fires once
    assert [s["lead_stage"] for s in run(30)["sent"]] == [30]
    # same day again -> deduped
    assert run(30)["sent"] == []
    # still inside the 30 window -> no NEW stage
    assert run(25)["sent"] == []
    # 7-day stage
    assert [s["lead_stage"] for s in run(7)["sent"]] == [7]
    # 1-day stage
    assert [s["lead_stage"] for s in run(1)["sent"]] == [1]
    # on the day itself -> nothing new
    assert run(0)["sent"] == []
    # exactly three reminder messages were delivered across the lifecycle
    assert len(sent) == 3


def test_reminder_discovered_late_only_fires_applicable_stage(tmp_path):
    _seed_one(tmp_path)

    def run(days_before):
        return dr.send_due_reminders(
            as_of=DEADLINE - timedelta(days=days_before),
            base_dir=tmp_path,
            send_fn=lambda c, t: True,
            recipients=["1"],
            require_review_approval=False,
        )

    # discovered 3 days out: fire the 7-day stage (most urgent applicable),
    # never the 30-day stage that is already moot.
    assert [s["lead_stage"] for s in run(3)["sent"]] == [7]
    assert [s["lead_stage"] for s in run(1)["sent"]] == [1]
    # 30 never fires
    stages = {r["lead_stage"] for r in dr._load_jsonl(dr.deadline_reminders_path(tmp_path))}
    assert 30 not in stages


def test_reminder_never_fires_for_past_deadline(tmp_path):
    _seed_one(tmp_path)
    summary = dr.send_due_reminders(
        as_of=DEADLINE + timedelta(days=1),  # already passed
        base_dir=tmp_path,
        send_fn=lambda c, t: True,
        recipients=["1"],
        require_review_approval=False,
    )
    assert summary["due"] == 0
    assert summary["sent"] == []


def test_reminder_not_logged_when_no_recipient_delivers(tmp_path):
    _seed_one(tmp_path)
    # No recipients -> nothing marked sent -> retried next pass.
    s1 = dr.send_due_reminders(
        as_of=DEADLINE - timedelta(days=7), base_dir=tmp_path,
        send_fn=lambda c, t: True, recipients=[],
        require_review_approval=False,
    )
    assert s1["sent"] == [] and s1["skipped_no_recipients"] == 1
    assert dr._load_jsonl(dr.deadline_reminders_path(tmp_path)) == []

    # Failed delivery -> also not logged.
    s2 = dr.send_due_reminders(
        as_of=DEADLINE - timedelta(days=7), base_dir=tmp_path,
        send_fn=lambda c, t: False, recipients=["1"],
        require_review_approval=False,
    )
    assert s2["sent"] == [] and s2["failed"] == 1
    assert dr._load_jsonl(dr.deadline_reminders_path(tmp_path)) == []

    # Now a working delivery logs it once.
    s3 = dr.send_due_reminders(
        as_of=DEADLINE - timedelta(days=7), base_dir=tmp_path,
        send_fn=lambda c, t: True, recipients=["1"],
        require_review_approval=False,
    )
    assert [x["lead_stage"] for x in s3["sent"]] == [7]


# ── human-review gate: unreviewed deadlines are not broadcast ─────────────────

def test_reminder_held_until_parent_record_approved(tmp_path, monkeypatch):
    """A deadline whose parent evidence record is not human-approved must be
    held (never broadcast rule-extracted dates + diff excerpts unreviewed)."""
    _seed_one(tmp_path, ev_id="run_gate")
    sent: list[str] = []

    # Not yet reviewed -> held.
    monkeypatch.setattr(
        "app.evidence_records.latest_canonical_evidence_review",
        lambda ev, **k: None,
    )
    s = dr.send_due_reminders(
        as_of=DEADLINE - timedelta(days=7), base_dir=tmp_path,
        send_fn=lambda c, t: sent.append(t) or True, recipients=["1"],
    )
    assert s["sent"] == []
    assert s["skipped_unreviewed"] == 1
    assert sent == []
    assert dr._load_jsonl(dr.deadline_reminders_path(tmp_path)) == []

    # Parent record approved -> the same reminder now fires.
    monkeypatch.setattr(
        "app.evidence_records.latest_canonical_evidence_review",
        lambda ev, **k: {"decision": "approved"},
    )
    s2 = dr.send_due_reminders(
        as_of=DEADLINE - timedelta(days=7), base_dir=tmp_path,
        send_fn=lambda c, t: sent.append(t) or True, recipients=["1"],
    )
    assert [x["lead_stage"] for x in s2["sent"]] == [7]
    assert len(sent) == 1


def test_reminder_not_sent_when_parent_rejected(tmp_path, monkeypatch):
    _seed_one(tmp_path, ev_id="run_rej")
    monkeypatch.setattr(
        "app.evidence_records.latest_canonical_evidence_review",
        lambda ev, **k: {"decision": "rejected"},
    )
    sent: list[str] = []
    s = dr.send_due_reminders(
        as_of=DEADLINE - timedelta(days=7), base_dir=tmp_path,
        send_fn=lambda c, t: sent.append(t) or True, recipients=["1"],
    )
    assert s["sent"] == []
    assert s["skipped_unreviewed"] == 1
    assert sent == []


# ── legal safety: disclaimer + forbidden-claims guard ─────────────────────────

def test_reminder_message_carries_disclaimer_and_deep_link():
    entry = {
        "lead_stage": 7, "days_until": 7, "deadline_kind": "effective",
        "deadline_date": "2026-09-01", "source_name": "DFSA", "regulator": "DFSA",
        "evidence_record_id": "run_x", "official_url": "https://dfsa.example/x",
        "extracted_from_diff_excerpt": "effective from 1 September 2026",
    }
    msg = dr.render_reminder_message(entry)
    assert LEGAL_DISCLAIMER in msg
    assert "run_x" in msg                       # deep link to evidence record
    assert "https://dfsa.example/x" in msg       # official source link


def test_reminder_message_passes_forbidden_claims_guard():
    entry = {
        "lead_stage": 1, "days_until": 1, "deadline_kind": "deadline",
        "deadline_date": "2026-09-01", "source_name": "DFSA",
        "evidence_record_id": "run_x", "official_url": "",
        "extracted_from_diff_excerpt": "due by 1 September 2026",
    }
    # Should not raise — the standard reminder contains no forbidden claim.
    dr.render_reminder_message(entry)


def test_reminder_message_blocks_forbidden_claim_in_excerpt():
    # If a forbidden phrase somehow reached the excerpt, the guard must fire.
    entry = {
        "lead_stage": 1, "days_until": 1, "deadline_kind": "deadline",
        "deadline_date": "2026-09-01", "source_name": "DFSA",
        "evidence_record_id": "run_x", "official_url": "",
        "extracted_from_diff_excerpt": "we guarantee compliance by this date",
    }
    with pytest.raises(ChangeRegisterError):
        dr.render_reminder_message(entry)


def test_no_forbidden_phrase_in_static_reminder_text():
    entry = {
        "lead_stage": 30, "days_until": 30, "deadline_kind": "consultation_close",
        "deadline_date": "2026-09-01", "source_name": "S", "regulator": "R",
        "evidence_record_id": "run_x", "official_url": "",
        "extracted_from_diff_excerpt": "consultation closes on 1 September 2026",
    }
    msg = dr.render_reminder_message(entry).lower().replace(LEGAL_DISCLAIMER.lower(), " ")
    for phrase in _FORBIDDEN_PHRASES:
        assert phrase not in msg


def test_build_reminder_email_includes_disclaimer():
    entry = {
        "lead_stage": 7, "days_until": 7, "deadline_kind": "effective",
        "deadline_date": "2026-09-01", "source_name": "DFSA",
        "evidence_record_id": "run_x", "official_url": "",
        "extracted_from_diff_excerpt": "effective from 1 September 2026",
    }
    payload = dr.build_reminder_email(entry)
    assert LEGAL_DISCLAIMER in payload["body_text"]
    assert payload["disclaimer_included"] is True


# ── scheduler daily pass (best-effort) ────────────────────────────────────────

def test_scheduler_reminder_pass_never_raises(tmp_path):
    import app.scheduler as scheduler

    # Empty register -> a clean summary, no exception, no network.
    summary = scheduler.run_deadline_reminder_pass(base_dir=tmp_path)
    assert summary["due"] == 0
    assert summary["sent"] == []


# ── run.py deadlines subcommand ───────────────────────────────────────────────

def test_run_py_deadlines_subcommand_lists_with_disclaimer(tmp_path):
    run_py = Path(__file__).resolve().parents[1] / "run.py"
    env = {
        "STATUTEPROOF_BASE_DIR": str(tmp_path),
        "PATH": __import__("os").environ.get("PATH", ""),
    }
    proc = subprocess.run(
        [sys.executable, str(run_py), "deadlines"],
        capture_output=True, text=True, env=env, timeout=90,
    )
    assert proc.returncode == 0, proc.stderr
    assert LEGAL_DISCLAIMER in proc.stdout
    assert "No upcoming deadlines" in proc.stdout


def test_distinct_same_date_kinds_are_kept_separate():
    """Two genuinely distinct obligations on the same date must not collapse
    (regression: date-only dedup dropped the 'effective' date)."""
    from app.deadline_radar import extract_deadlines
    items = extract_deadlines(
        "The amended rules take effect on 30 September 2026. Separately, the "
        "public consultation closes on 30 September 2026."
    )
    kinds = sorted(i["deadline_kind"] for i in items)
    assert kinds == ["consultation_close", "effective"], items
    assert all(i["deadline_date"] == "2026-09-30" for i in items)


def test_generic_deadline_folds_into_specific_same_date():
    """One phrase matching consultation_close + generic 'deadline' yields ONE record."""
    from app.deadline_radar import extract_deadlines
    items = extract_deadlines("Comments are due by 30 September 2026.")
    assert len(items) == 1
    assert items[0]["deadline_kind"] == "consultation_close"
