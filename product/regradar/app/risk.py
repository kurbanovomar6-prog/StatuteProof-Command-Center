"""
Lightweight rule-based risk scoring engine.

No AI, no external APIs.  Runs entirely offline via keyword matching.

Scoring rules (evaluated in order — first match wins):

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

_HIGH_KEYWORDS: tuple[str, ...] = (
    "ban",
    "restriction",
    "license",
    "rate",
    "penalty",
    "sanction",
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
)


def analyze_risk(diff_result: dict) -> dict:
    """
    Score a structured diff result and return a risk assessment.

    Parameters
    ----------
    diff_result : dict
        Output of ``diff.get_diff()``.
        Expected keys: ``added`` (list[str]), ``removed`` (list[str]).

    Returns
    -------
    dict
        {
            "risk_level": "HIGH" | "MEDIUM" | "LOW",
            "reason":     str,
        }
    """
    if not diff_result.get("has_changes"):
        return {"risk_level": "LOW", "reason": "No changes detected"}

    all_text = " ".join(
        diff_result.get("added",   []) +
        diff_result.get("removed", [])
    ).lower()

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
