"""F2 — structured fact detection over the actual change delta.

Extracts facts a compliance officer acts on — deadlines, effective dates,
fee/penalty amounts, law/article/licence references, in-force status — from
the ADDED blocks of a diff. Every fact carries the exact matched span so the
alert can prove the claim. Nothing is inferred: no match, no fact.

Pattern frequencies over the real trail justify each detector
(docs/signal/SIGNAL_QUALITY.md §B): 629 law refs, 200 effective-date,
145 AED amounts, 167 article refs in the historical delta corpus.

Arabic scope (measured): law references (242 قانون اتحادي / 149 مرسوم بقانون
delta hits) are detected; Arabic *deadline* vocabulary is effectively absent
from the trail (0 delta hits), so no AR deadline detector is claimed — those
routes stay with the Arabic human-review path (F3).
"""

from __future__ import annotations

import re
from typing import Any

_MONTH = (
    "january|february|march|april|may|june|july|august|september|october|"
    "november|december"
)
_DATE = rf"(?:\d{{1,2}}\s+(?:{_MONTH})\s+\d{{4}}|\d{{1,2}}[\/\-]\d{{1,2}}[\/\-]\d{{2,4}}|\d{{4}}-\d{{2}}-\d{{2}})"

# Ordered list of (kind, pattern). Patterns capture the span via group(0).
_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "deadline",
        re.compile(
            rf"(?:no\s+later\s+than\s+{_DATE}|within\s+\d+\s+(?:days|months|business\s+days)|deadline\s+(?:of|is)\s+{_DATE}|due\s+(?:by|on)\s+{_DATE})",
            re.IGNORECASE,
        ),
    ),
    (
        "effective_date",
        re.compile(
            rf"effective\s+(?:from|as\s+of|on|date[:\s])\s*{_DATE}",
            re.IGNORECASE,
        ),
    ),
    (
        "in_force_status",
        re.compile(r"status:\s*(?:in[-\s]?force|repealed|superseded)", re.IGNORECASE),
    ),
    (
        "law_reference",
        re.compile(
            r"(?:federal\s+)?(?:decree[-\s]?law|cabinet\s+(?:decision|resolution)|federal\s+law|administrative\s+decision|circular|resolution)\s+no\.?\s*\(?\s*[\d\s/.RT]+\)?\s*of\s+\d{4}",
            re.IGNORECASE,
        ),
    ),
    (
        "law_reference",
        re.compile(
            r"(?:قانون\s+اتحادي|مرسوم\s+بقانون(?:\s+اتحادي)?|قرار(?:\s+مجلس\s+الوزراء)?)\s+رقم\s*\(?\s*[\d٠-٩]+\s*\)?\s*لسنة\s+[\d٠-٩]{4}"
        ),
    ),
    (
        "article_reference",
        re.compile(r"articles?\s+\(?\d+\)?(?:\s+and\s+\(?\d+\)?)?", re.IGNORECASE),
    ),
    (
        "article_reference",
        re.compile(r"المادة\s*\(?\s*[\d٠-٩]+\s*\)?"),
    ),
    (
        "licence_reference",
        re.compile(
            r"licen[cs]e\s+categor(?:y|ies)(?:\s+applied\s+for)?|categor(?:y|ies)\s+of\s+licen[cs]e",
            re.IGNORECASE,
        ),
    ),
    (
        "amount",
        re.compile(
            r"(?:aed|dhs?\.?)\s*[\d,]+(?:\.\d+)?|[\d,]+(?:\.\d+)?\s*(?:aed|dirhams?)|[\d٠-٩,]+\s*درهم",
            re.IGNORECASE,
        ),
    ),
]

_MAX_FACTS = 12


def extract_detected_facts(added_blocks: list | None) -> list[dict[str, Any]]:
    """Return facts truly present in the added delta text.

    Each fact: {"kind": str, "value": str, "span": str}. `span` is the exact
    matched substring; `value` is the cleaned span. Deduplicated on
    (kind, value). Removed text is deliberately NOT scanned: a fact that left
    the page is not an obligation to state.
    """
    text = "\n".join(str(b) for b in (added_blocks or []) if str(b).strip())
    if not text.strip():
        return []

    facts: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for kind, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            span = match.group(0)
            value = " ".join(span.split())
            key = (kind, value.lower())
            if key in seen:
                continue
            seen.add(key)
            facts.append({"kind": kind, "value": value, "span": span})
            if len(facts) >= _MAX_FACTS:
                return facts
    return facts


_KIND_LABEL = {
    "deadline": "Deadline",
    "effective_date": "Effective date",
    "in_force_status": "Status",
    "law_reference": "Instrument",
    "article_reference": "Article",
    "licence_reference": "Licensing",
    "amount": "Amount",
}


def format_facts_lines(facts: list[dict[str, Any]]) -> list[str]:
    """Human lines for alert rendering; empty list when nothing detected."""
    lines: list[str] = []
    for fact in facts or []:
        label = _KIND_LABEL.get(str(fact.get("kind")), str(fact.get("kind")))
        value = str(fact.get("value") or "").strip()
        if value:
            lines.append(f"{label}: {value}")
    return lines
