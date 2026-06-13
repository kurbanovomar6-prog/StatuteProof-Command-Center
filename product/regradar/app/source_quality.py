"""
source_quality.py — transparent parser/source quality scorecard.

The score is a product safety gate. It explains why a source can or cannot move
from a preview test toward evidence confirmation and monitoring certification.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse


QUALITY_LABELS = (
    (90, "EXCELLENT"),
    (75, "GOOD"),
    (60, "ACCEPTABLE"),
    (40, "LIMITED"),
    (0, "POOR"),
)

POLICY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("login", r"\b(sign in|log in|login|username|password|single sign-on|sso)\b"),
    ("captcha", r"\b(captcha|recaptcha|verify you are human|cloudflare ray|checking your browser)\b"),
    ("paywall", r"\b(subscribe to continue|subscription required|premium access|paywall|members only)\b"),
    ("private_portal", r"\b(private portal|client portal|restricted access|authorised users only|authorized users only)\b"),
)


def quality_label(score: int) -> str:
    for minimum, label in QUALITY_LABELS:
        if score >= minimum:
            return label
    return "POOR"


def detect_policy_warnings(text: str, html: str = "") -> list[str]:
    blob = f"{text or ''}\n{html or ''}".lower()
    warnings: list[str] = []
    for name, pattern in POLICY_PATTERNS:
        if re.search(pattern, blob, flags=re.I):
            warnings.append(name)
    return sorted(set(warnings))


def _paragraph_count(text: str) -> int:
    return sum(1 for p in re.split(r"\n{2,}", text or "") if len(p.strip()) >= 80)


def _heading_count(text: str) -> int:
    return sum(1 for line in (text or "").splitlines() if 3 <= len(line.strip()) <= 90 and not line.strip().endswith("."))


def _regulatory_density(text: str) -> float:
    words = re.findall(r"[a-zA-Z]{3,}", text or "")
    if not words:
        return 0.0
    regulatory_terms = {
        "regulation", "regulatory", "rule", "rules", "law", "laws", "notice",
        "circular", "guidance", "consultation", "compliance", "supervisory",
        "license", "licence", "licensed", "authority", "aml", "ctf",
        "enforcement", "decision", "obligation", "requirements", "framework",
    }
    hits = sum(1 for w in words if w.lower() in regulatory_terms)
    return min(1.0, hits / max(1, len(words)) * 20)


def _safe_host_present(url: str) -> bool:
    parsed = urlparse(url or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def build_quality_score(
    *,
    url: str,
    fetch_success: bool,
    normalized_text: str,
    raw_html: str = "",
    nav_shell: bool = False,
    hash_collision: bool = False,
    selector_timeout: bool = False,
    pdf_shallow: bool = False,
    proof_path: str | None = None,
    normalized_hash: str | None = None,
    canonical_url: str | None = None,
    provider_confidence: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """Return a 0-100 quality report with component scores and penalties."""
    metadata = metadata or {}
    normalized_text = normalized_text or ""
    policy_warnings = detect_policy_warnings(normalized_text, raw_html)

    length = len(normalized_text)
    paragraphs = _paragraph_count(normalized_text)
    headings = _heading_count(normalized_text)
    density = _regulatory_density(normalized_text)

    components = {
        "url_safety": 10 if _safe_host_present(url) and not policy_warnings else 0,
        "fetch_success": 10 if fetch_success else 0,
        "extraction_length": 10 if length >= 2000 else 7 if length >= 1000 else 4 if length >= 500 else 0,
        "paragraph_heading_structure": 10 if paragraphs >= 3 or headings >= 3 else 6 if paragraphs >= 1 else 0,
        "regulatory_content_density": round(10 * density),
        "nav_shell_risk_low": 15 if not nav_shell else 0,
        "hash_uniqueness": 10 if normalized_hash and not hash_collision else 0,
        "metadata_extraction": 5 if metadata.get("publication_date") or metadata.get("canonical_url") or canonical_url else 0,
        "provider_confidence": 10 if provider_confidence == "high" else 7 if provider_confidence == "medium" else 4 if provider_confidence == "low" else 0,
        "evidence_completeness": 10 if proof_path else 0,
    }

    penalties: dict[str, int] = {}
    if nav_shell:
        penalties["nav_shell"] = -50
    if hash_collision:
        penalties["hash_collision"] = -40
    if selector_timeout:
        penalties["selector_timeout"] = -30
    if 0 < length < 500:
        penalties["shallow_content"] = -25
    if pdf_shallow:
        penalties["pdf_text_too_shallow"] = -30
    if not proof_path:
        penalties["no_proof"] = -25
    if not canonical_url:
        penalties["missing_official_or_canonical_url"] = -10
    if policy_warnings:
        penalties["source_policy_warning"] = -20

    raw_score = sum(components.values()) + sum(penalties.values())
    score = max(0, min(100, int(raw_score)))

    return {
        "quality_score": score,
        "quality_label": quality_label(score),
        "components": components,
        "penalties": penalties,
        "policy_warnings": policy_warnings,
        "text_stats": {
            "normalized_length": length,
            "paragraph_count": paragraphs,
            "heading_count": headings,
            "regulatory_density": round(density, 3),
        },
    }
