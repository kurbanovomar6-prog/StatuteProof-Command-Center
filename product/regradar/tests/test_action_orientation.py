"""Action-orientation triage label (VIXIO/FINRA model).

Answers the reviewer's first question ("do I need to act?") as a WORKFLOW prompt,
never a legal obligation — so it must stay on the monitoring side of the
legal-advice line (no "you must comply" / applicability determination) and pass
the forbidden-claims guard.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.alert_drafts import action_orientation  # noqa: E402
from app.alert_content import build_alert_content, render_telegram  # noqa: E402
from app.legal_safety import find_forbidden_claims  # noqa: E402


def test_actionable_indicative_informative_mapping():
    assert action_orientation("ENFORCEMENT")["code"] == "actionable"
    assert action_orientation("DEADLINE_OR_REPORTING")["code"] == "actionable"
    assert action_orientation("AML_CFT")["code"] == "actionable"
    assert action_orientation("CONSULTATION")["code"] == "indicative"
    assert action_orientation("GUIDANCE_UPDATE")["code"] == "informative"
    assert action_orientation("UNKNOWN")["code"] == "informative"
    assert action_orientation("")["code"] == "informative"


def test_labels_are_workflow_prompts_not_obligations():
    # Never a second-person legal obligation; only review-workflow framing.
    for ct in ("ENFORCEMENT", "CONSULTATION", "GUIDANCE_UPDATE", "AML_CFT"):
        o = action_orientation(ct)
        blob = f"{o['label']} {o['description']}".lower()
        assert "you must" not in blob
        assert "applies to you" not in blob
        assert find_forbidden_claims(f"{o['label']} {o['description']}") == []


def test_orientation_renders_in_alert_and_is_metachar_safe():
    payload = {
        "risk_level": "HIGH",
        "risk_details": {"rule": "HIGH_MULTIPLE_STRONG", "matched_keywords": ["penalty"]},
        "source_name": "DFSA",
        "url": "https://dfsa.example/x",
        "change_type": "ENFORCEMENT",
        "added": ["A new penalty framework applies."],
    }
    content = build_alert_content(payload)
    assert content["action_orientation"] == "Review recommended"
    msg = render_telegram(content)
    assert "Review recommended" in msg
    # No forbidden claim anywhere in the rendered alert.
    assert find_forbidden_claims(msg) == []


def test_no_change_type_omits_orientation():
    content = build_alert_content({"risk_level": "LOW", "source_name": "X", "url": "https://x"})
    assert "action_orientation" not in content
