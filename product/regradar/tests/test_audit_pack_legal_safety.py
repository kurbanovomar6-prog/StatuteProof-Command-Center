"""The audit-pack render path must run the forbidden-claims guard.

Regression: render_audit_pack_markdown emitted reviewer free-text fields
(internal_note, next_action) with no legal-safety scan, unlike every sibling
export — a reviewer-typed forbidden phrase could ship to a customer.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import legal_safety  # noqa: E402
from app.audit_export import render_audit_pack_markdown  # noqa: E402


_RECORD = {
    "source_name": "DFSA AML Rulebook",
    "source_id": "AE-dfsa-aml",
    "official_url": "https://dfsa.example/aml",
    "timestamp_utc": "2026-07-13T09:00:00Z",
    "change_status": "CHANGED",
    "normalized_hash": "sha256:abc",
    "raw_hash": "sha256:def",
}


def test_forbidden_reviewer_note_is_scrubbed():
    assessment = {
        "assessment_id": "a1",
        "assessment_status": "approved",
        "impact_level": "monitor",
        "reviewer_name": "Alice",
        "reviewed_at": "2026-07-13T10:00:00Z",
        "internal_note": "We guarantee compliance for the client.",
        "next_action": "Relax — this will prevent fines.",
    }
    # Sanity: both phrases are genuinely on the ban list.
    assert legal_safety.find_forbidden_claims(assessment["internal_note"])
    assert legal_safety.find_forbidden_claims(assessment["next_action"])

    md = render_audit_pack_markdown(_RECORD, assessment=assessment)
    # No forbidden claim survives in the rendered pack...
    assert legal_safety.find_forbidden_claims(md) == []
    # ...and the offending phrases are gone.
    assert "guarantee compliance" not in md.lower()
    assert "prevent fines" not in md.lower()


def test_clean_reviewer_note_is_preserved():
    assessment = {
        "assessment_id": "a2",
        "assessment_status": "approved",
        "impact_level": "policy_review",
        "reviewer_name": "Bob",
        "reviewed_at": "2026-07-13T10:00:00Z",
        "internal_note": "Reviewed against the source; scope looks relevant to CDD teams.",
        "next_action": "Consider a policy review.",
    }
    md = render_audit_pack_markdown(_RECORD, assessment=assessment)
    assert "scope looks relevant to CDD teams" in md
    assert legal_safety.find_forbidden_claims(md) == []


def test_pack_without_assessment_renders_clean():
    md = render_audit_pack_markdown(_RECORD)
    assert legal_safety.find_forbidden_claims(md) == []
    assert "No Acknowledge & Assess record" in md
