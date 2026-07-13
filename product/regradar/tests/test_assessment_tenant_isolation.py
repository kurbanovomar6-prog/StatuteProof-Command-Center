"""Cross-tenant isolation of PRIVATE Acknowledge & Assess notes.

The official evidence records are SHARED across customers (everyone monitors the
same public regulators), but a customer's internal review note / impact / next
action on a shared record is PRIVATE to their org. Before this fix the assessment
store was global and keyed only by evidence_record_id, so any account could read
another org's internal notes. This proves the note is org-isolated across EVERY
read surface: latest_assessment_for, load_assessments, the review queue, and the
review-history builder.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import evidence_assessment as ea  # noqa: E402
from app import review_queue as rq  # noqa: E402
from app import source_health_timeline as sht  # noqa: E402

_REC = {
    "run_id": "run-shared-1",
    "evidence_record_id": "run-shared-1",
    "source_id": "AE-dfsa-aml",
    "source_name": "DFSA AML Rulebook",
    "official_url": "https://dfsa.example/aml",
    "change_status": "CHANGED",
    "normalized_hash": "sha256:abc",
}

ORG_A = "1"
ORG_B = "2"
SECRET = "SECRET-NOTE-FROM-ORG-A"


def _seed_org_a_assessment(tmp_path, monkeypatch):
    # Stub record lookup/validation so the test isolates the ORG-scoping logic.
    monkeypatch.setattr(ea, "find_evidence_record", lambda eid, base_dir=None: dict(_REC))
    monkeypatch.setattr(ea, "validate_saved_evidence", lambda r, base_dir=None: None)
    ea.create_assessment(
        evidence_record_id=_REC["run_id"], impact_level="monitor",
        internal_note=SECRET, next_action="Escalate internally",
        reviewer_name="MLRO A", org_id=ORG_A, base_dir=tmp_path,
    )


def test_latest_and_load_are_org_isolated(tmp_path, monkeypatch):
    _seed_org_a_assessment(tmp_path, monkeypatch)
    # Org B sees NOTHING.
    assert ea.latest_assessment_for(_REC["run_id"], base_dir=tmp_path, org_id=ORG_B) is None
    assert ea.load_assessments(base_dir=tmp_path, org_id=ORG_B) == []
    # Org A sees its own note.
    a = ea.latest_assessment_for(_REC["run_id"], base_dir=tmp_path, org_id=ORG_A)
    assert a is not None and a["internal_note"] == SECRET
    assert a["org_id"] == ORG_A
    # A caller with an UNRESOLVED org (None) also sees nothing (fails closed).
    assert ea.latest_assessment_for(_REC["run_id"], base_dir=tmp_path, org_id=None) is None


def test_review_queue_is_org_isolated(tmp_path, monkeypatch):
    _seed_org_a_assessment(tmp_path, monkeypatch)
    monkeypatch.setattr(rq, "_read_runs", lambda root, market: [dict(_REC)])
    # Org B: the shared record shows as PENDING with NO reviewer/impact — B never
    # sees that org A reviewed it, nor A's reviewer name or impact.
    q_b = rq.build_review_queue(org_id=ORG_B, status="all", base_dir=tmp_path)
    assert SECRET not in json.dumps(q_b)
    assert "MLRO A" not in json.dumps(q_b)
    row_b = q_b["queue"][0]
    assert row_b["pending_review"] is True
    assert row_b["reviewer"] is None
    assert row_b["impact_level"] is None
    # Org A: sees its own assessment (assessed, its reviewer + impact).
    q_a = rq.build_review_queue(org_id=ORG_A, status="all", base_dir=tmp_path)
    row_a = q_a["queue"][0]
    assert row_a["pending_review"] is False
    assert row_a["reviewer"] == "MLRO A"
    assert row_a["impact_level"] == "monitor"


def test_review_history_is_org_isolated(tmp_path, monkeypatch):
    _seed_org_a_assessment(tmp_path, monkeypatch)
    monkeypatch.setattr(sht, "_find_run", lambda eid, root: dict(_REC))
    hist_b = sht.build_evidence_review_history(_REC["run_id"], org_id=ORG_B, base_dir=tmp_path)
    assert SECRET not in json.dumps(hist_b)
    assert hist_b["latest_assessment"] is None
    hist_a = sht.build_evidence_review_history(_REC["run_id"], org_id=ORG_A, base_dir=tmp_path)
    assert hist_a["latest_assessment"] is not None
    assert hist_a["latest_assessment"]["internal_note"] == SECRET
