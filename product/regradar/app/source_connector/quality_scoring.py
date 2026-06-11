"""
Source quality scoring — 0-100 numeric scale.
score_source(...) → dict with "score", "label", "breakdown"
Labels: excellent(80+), good(65-79), acceptable(50-64), weak(35-49), unusable(<35)
"""
from typing import Any


def score_source(
    extracted_chars: int,
    has_feed: bool = False,
    has_sitemap: bool = False,
    has_documents: bool = False,
    has_api: bool = False,
    used_playwright: bool = False,
) -> dict[str, Any]:
    """
    Compute 0-100 quality score.
    Scoring:
      Content quality (0-70): 0c=0, 100-499c=15, 500-999c=30, 1000-4999c=50, 5000-19999c=60, ≥20000c=70
      JS overhead penalty: requires Playwright → -5
      Structural signals (0-30, additive): has_feed→+12, has_sitemap→+10, has_documents→+8, has_api→+5
    """
    breakdown: dict[str, int] = {}

    if extracted_chars >= 20_000:
        content_pts = 70
    elif extracted_chars >= 5_000:
        content_pts = 60
    elif extracted_chars >= 1_000:
        content_pts = 50
    elif extracted_chars >= 500:
        content_pts = 30
    elif extracted_chars >= 100:
        content_pts = 15
    else:
        content_pts = 0
    breakdown["content_quality"] = content_pts

    js_penalty = -5 if used_playwright else 0
    breakdown["js_overhead_penalty"] = js_penalty

    struct_pts = 0
    if has_feed:      struct_pts += 12
    if has_sitemap:   struct_pts += 10
    if has_documents: struct_pts += 8
    if has_api:       struct_pts += 5
    struct_pts = min(30, struct_pts)
    breakdown["structural_signals"] = struct_pts

    score = max(0, min(100, content_pts + js_penalty + struct_pts))

    if score >= 80:
        label = "excellent"
    elif score >= 65:
        label = "good"
    elif score >= 45:
        label = "acceptable"
    elif score >= 30:
        label = "weak"
    else:
        label = "unusable"

    return {"score": score, "label": label, "breakdown": breakdown}
