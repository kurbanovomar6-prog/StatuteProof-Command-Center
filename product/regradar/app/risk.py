"""
Lightweight rule-based risk scoring engine.

No AI, no external APIs.  Runs entirely offline via keyword matching.

Scoring rules (evaluated in order — first match wins):

  NON_MATERIAL  Fires before all other tiers.
                Change exists but net diff < 80 chars AND no obligation
                keywords detected.  Pure formatting / whitespace edits.

  HIGH    requires one of:
            • ≥ 2 strong-risk keywords matched, OR
            • 1 strong-risk keyword + ≥ 1 context-amplifier word
          strong-risk keywords:   ban, restriction, license, rate, penalty, sanction
          context-amplifier words: deadline, compliance, reporting, obligation,
                                   mandatory, enforcement, fine

  MEDIUM  • 1 strong-risk keyword without context support, OR
          • Moderate-change keyword: update, change, amendment

  LOW     Everything else (no keywords matched)
"""

from __future__ import annotations

import re

_ARABIC_RE = re.compile(r"[؀-ۿ]")

_HIGH_KEYWORDS: tuple[str, ...] = (
    "ban",
    "restriction",
    "license",
    "penalty",
    "sanction",
    "circular",
    "vasp",
    "virtual asset",
    "revoke",
    "revocation",
    "cease",
    "suspend",
    "enforcement action",
)

# Words that amplify a single HIGH keyword into a confirmed HIGH signal.
# They indicate a concrete regulatory obligation rather than incidental usage
# (e.g. "exchange rate update" vs "penalty for non-compliance by deadline").
_HIGH_CONTEXT_WORDS: tuple[str, ...] = (
    "deadline",
    "penalty",
    "license",
    "sanction",
    "compliance",
    "reporting",
    "obligation",
    "mandatory",
    "enforcement",
    "fine",
)

_MEDIUM_KEYWORDS: tuple[str, ...] = (
    "update",
    "change",
    "amendment",
    "guidance",
    "guideline",
    "notice",
    "consultation",
    "aml",
    "cft",
    "fit and proper",
    "prudential",
)

# ── NON_MATERIAL tier constants ───────────────────────────────────────────────

NON_MATERIAL_MAX_CHARS = 80  # net diff length threshold

_OBLIGATION_KEYWORDS: tuple[str, ...] = (
    "deadline",
    "obligation",
    "mandatory",
    "must",
    "shall",
    "required",
    "compliance date",
    "effective date",
    "enforcement",
    "penalty",
    "fine",
    "sanction",
    "revoke",
    "suspend",
    "cease",
    "ban",
)


def is_non_material(diff_result: dict) -> bool:
    """Return True when a change is below the materiality threshold.

    A change is NON_MATERIAL when ALL of the following are true:

    a. ``diff_result["changed"]`` is True (there is a change).
    b. Net character change (|added_len - removed_len|) < NON_MATERIAL_MAX_CHARS.
    c. None of the _OBLIGATION_KEYWORDS appear in the combined added+removed text.
    d. ``diff_result["risk_level"]`` is not already "HIGH".

    Returns False (conservative fallback) if the diff has no added/removed text fields.
    """
    if not diff_result.get("changed"):
        return False

    added_text = diff_result.get("added")
    removed_text = diff_result.get("removed")

    # Conservative fallback: no text to analyse → do not downgrade
    if added_text is None and removed_text is None:
        return False

    # Normalise: added/removed may be list[str] or str
    if isinstance(added_text, list):
        added_str = " ".join(added_text)
    else:
        added_str = str(added_text or "")

    if isinstance(removed_text, list):
        removed_str = " ".join(removed_text)
    else:
        removed_str = str(removed_text or "")

    # (b) Net character change
    net_change = abs(len(added_str) - len(removed_str))
    if net_change >= NON_MATERIAL_MAX_CHARS:
        return False

    # (c) Obligation keywords
    combined_lower = (added_str + " " + removed_str).lower()
    for kw in _OBLIGATION_KEYWORDS:
        if kw in combined_lower:
            return False

    # (d) Do not downgrade already-HIGH
    if str(diff_result.get("risk_level") or "").upper() == "HIGH":
        return False

    return True


def analyze_risk(diff_result: dict) -> dict:
    """
    Score a structured diff result and return a risk assessment.

    Parameters
    ----------
    diff_result : dict
        Output of ``diff.get_diff()``.
        Expected keys: ``added`` (list[str]), ``removed`` (list[str]),
        optionally ``changed`` (bool) and ``has_changes`` (bool).

    Returns
    -------
    dict
        {
            "risk_level": "NON_MATERIAL" | "HIGH" | "MEDIUM" | "LOW",
            "reason":     str,
        }
    """
    if not diff_result.get("has_changes"):
        return {"risk_level": "LOW", "reason": "No changes detected"}

    # NON_MATERIAL check fires before all other tiers
    if is_non_material(diff_result):
        return {
            "risk_level": "NON_MATERIAL",
            "reason": (
                "Change is below materiality threshold: net diff < 80 chars "
                "and no obligation keywords detected."
            ),
            "matched_keywords": [],
            "non_material": True,
        }

    combined_text = " ".join(
        diff_result.get("added",   []) +
        diff_result.get("removed", [])
    )

    if _ARABIC_RE.search(combined_text):
        return {
            "risk_level": "MEDIUM",
            "reason": (
                "Arabic regulatory content detected. Rule-based keyword matching "
                "is English-only — manual review required to assess risk."
            ),
        }

    all_text = combined_text.lower()

    matched_high    = [kw for kw in _HIGH_KEYWORDS      if kw in all_text]
    matched_context = [cw for cw in _HIGH_CONTEXT_WORDS if cw in all_text]

    # HIGH path 1: two or more strong keywords
    if len(matched_high) >= 2:
        return {
            "risk_level": "HIGH",
            "reason": (
                "High risk: multiple strong regulatory risk indicators were "
                "detected (such as penalties, licensing requirements, sanctions, "
                "or mandatory reporting obligations). Compliance review is required."
            ),
        }

    # HIGH path 2: one strong keyword confirmed by a context amplifier
    if len(matched_high) == 1 and matched_context:
        return {
            "risk_level": "HIGH",
            "reason": (
                "High risk: a strong regulatory risk indicator was detected "
                "alongside supporting compliance context (such as a deadline, "
                "penalty, or mandatory obligation). Compliance review is required."
            ),
        }

    # MEDIUM: one strong keyword present but no context support
    if len(matched_high) == 1:
        return {
            "risk_level": "MEDIUM",
            "reason": (
                "Medium risk: one strong regulatory keyword was detected, but "
                "there is not enough supporting context for a high-risk "
                "classification. Compliance review is recommended."
            ),
        }

    # MEDIUM: moderate-change language
    for keyword in _MEDIUM_KEYWORDS:
        if keyword in all_text:
            return {
                "risk_level": "MEDIUM",
                "reason": (
                    "Medium risk: the change contains a regulatory signal "
                    "(such as an update, amendment, or policy change), but does "
                    "not include high-risk indicators. Compliance review is "
                    "recommended."
                ),
            }

    return {
        "risk_level": "LOW",
        "reason": (
            "Low risk: no clear signs of new penalties, licensing duties, "
            "reporting deadlines, sanctions, or mandatory compliance obligations "
            "were detected. Continue routine monitoring."
        ),
    }
