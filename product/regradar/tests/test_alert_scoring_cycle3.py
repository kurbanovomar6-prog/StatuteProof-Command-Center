"""
Alert-quality cycle 3 (owner-approved, prerequisite of the excellence sprint):

1. Delta-only severity scoring — keywords are scored on the text that
   actually changed between removed/added block pairs, not on the whole
   block. Kills the 2026-07-05 false HIGH where an unchanged navigation
   menu ("Sanctions Compliance") inside a changed block supplied the
   keywords for a title-tagline flip.
2. UK spelling variants — DFSA/DIFC write UK English; 'licence' must score
   like 'license'.
3. ALERT_DRY_RUN — verification/e2e runs must never send real alerts:
   with the flag set, send_telegram_alert performs zero network I/O,
   logs the message, and reports not-sent (so dedup state is not poisoned).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.risk import analyze_risk

_NAV_BLOCK = (
    "Financial Crime Prevention Notices and MLRO Letters | DFSA | About us | "
    "AML, CTF & Sanctions Compliance | Regulatory Framework | Supervisory "
    "Methodology | Overview"
)


def test_title_flip_inside_keyword_heavy_block_is_not_high():
    """The exact 2026-07-05 shape: block text identical except a tagline;
    the block's own nav words must not supply severity keywords."""
    before = _NAV_BLOCK + " | THE INDEPENDENT REGULATOR OF FINANCIAL SERVICES"
    after = _NAV_BLOCK
    r = analyze_risk({"has_changes": True, "added": [after], "removed": [before]})
    assert r["risk_level"] != "HIGH", (
        f"unchanged nav words upgraded a tagline flip to HIGH: {r}"
    )
    assert "sanction" not in r.get("matched_keywords", []), (
        "keyword matched from text that did not change"
    )


def test_genuinely_added_keywords_still_score_high():
    before = _NAV_BLOCK
    after = _NAV_BLOCK + (
        " A new administrative penalty applies and licence suspension follows "
        "non-compliance with mandatory reporting."
    )
    r = analyze_risk({"has_changes": True, "added": [after], "removed": [before]})
    assert r["risk_level"] == "HIGH", f"real added obligations must stay HIGH: {r}"


def test_wholly_new_block_scores_on_full_text():
    r = analyze_risk({
        "has_changes": True,
        "added": ["New penalty framework with sanction screening obligations " * 3],
        "removed": [],
    })
    assert r["risk_level"] == "HIGH"


def test_removed_only_content_still_scores():
    r = analyze_risk({
        "has_changes": True,
        "added": [],
        "removed": ["Suspension of licence and enforcement action withdrawn " * 3],
    })
    assert r["risk_level"] in {"MEDIUM", "HIGH"}, f"removals must be scored: {r}"


def test_uk_spelling_licence_scores_like_license():
    r = analyze_risk({
        "has_changes": True,
        "added": ["licence obligations now include mandatory compliance reporting " * 3],
        "removed": [],
    })
    assert r["risk_level"] == "HIGH", f"UK 'licence' must match: {r}"
    assert "licence" in r.get("matched_keywords", [])


def test_alert_dry_run_sends_nothing_and_reports_not_sent(monkeypatch, caplog):
    from app.telegram import send_telegram_alert

    monkeypatch.setenv("ALERT_DRY_RUN", "true")

    def _boom(*a, **k):
        raise AssertionError("network I/O attempted during ALERT_DRY_RUN")

    payload = {
        "url": "https://example.gov.ae/x", "source_name": "X", "jurisdiction": "AE",
        "risk_level": "HIGH",
        "risk_details": {"rule": "HIGH_MULTIPLE_STRONG",
                         "matched_keywords": ["penalty", "sanction"], "matched_context": []},
        "added": ["penalty text"], "removed": [],
    }
    with patch("app.telegram.requests.post", side_effect=_boom), \
         patch("app.telegram._deliver_alert_to_subscribed_users", side_effect=_boom):
        with caplog.at_level(logging.INFO, logger="app.telegram"):
            sent = send_telegram_alert(payload)

    assert sent is False, "dry run must report not-sent (dedup state unpoisoned)"
    assert "ALERT_DRY_RUN" in caplog.text
    assert "penalty" in caplog.text, "dry run must log the rendered message"
