"""
Undecodable-content guard (VARA public-register incident, 2026-07-10).

An adapter advertised "Accept-Encoding: … br" on a host without the brotli
package: urllib3 could not decode the body, and brotli-compressed bytes were
read as UTF-8 mojibake (U+FFFD soup), passed the adapter quality gate, became
the normalized baseline, and shipped to customers inside an alert excerpt.

Three defense layers, each regression-guarded here:
1. Adapters never advertise a codec the runtime may not decode.
2. is_quality_content() rejects text saturated with replacement/control chars,
   so a mis-decoded body falls back to the generic scraper instead of
   entering the diff.
3. _build_excerpt() never renders unreadable chunks to a customer — it says
   plainly that the content could not be rendered.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.base import is_quality_content
from app.alert_content import (
    _OMITTED_CONTENT_NOTE,
    _UNREADABLE_EXCERPT_NOTE,
    _build_excerpt,
    build_alert_content,
)


def _mojibake(chars: int = 800) -> str:
    """Simulate a compressed body decoded as UTF-8: dense U+FFFD soup."""
    unit = "�\x07�i��*l��E��jz\x19`\x00��F�Fn\n\n"
    return (unit * (chars // len(unit) + 1))[:chars]


# ── layer 1: adapters must not advertise undecodable codecs ──────────────────

def test_adapters_do_not_hardcode_accept_encoding():
    from app.adapters import fta, vara
    for module in (vara, fta):
        headers = getattr(module, "_HEADERS")
        assert "Accept-Encoding" not in headers, (
            f"{module.__name__} hardcodes Accept-Encoding — urllib3 must "
            "negotiate only codecs it can decode"
        )


# ── layer 2: quality gate rejects mis-decoded bodies ─────────────────────────

def test_quality_gate_rejects_mojibake_saturated_text():
    assert not is_quality_content(_mojibake())


def test_quality_gate_rejects_mojibake_with_readable_prefix():
    text = "VARA official page\n\nURL: https://www.vara.ae/x/\n\n" + _mojibake()
    assert not is_quality_content(text)


def test_quality_gate_tolerates_a_stray_replacement_char():
    text = (
        "Registered virtual asset service providers must comply with "
        "licensing conditions.\n\n" * 10
    ) + "Entity name: Caf� Exchange Ltd\n\nEnd of register."
    assert is_quality_content(text)


def test_quality_gate_still_accepts_normal_clean_text():
    text = "A real regulatory paragraph about licensing rules.\n\n" * 12
    assert is_quality_content(text)


# ── layer 3: excerpt never ships unreadable bytes to a customer ──────────────

def test_excerpt_replaces_fully_unreadable_diff_with_plain_note():
    excerpt = _build_excerpt([_mojibake(200)], [_mojibake(200)])
    assert excerpt == _UNREADABLE_EXCERPT_NOTE
    assert "�" not in excerpt


def test_excerpt_keeps_readable_chunks_and_flags_omitted_garbage():
    readable = "Administrative Resolution No. (39) of 2026 concerning penalties."
    excerpt = _build_excerpt([readable, _mojibake(200)], [])
    assert readable in excerpt
    assert _OMITTED_CONTENT_NOTE in excerpt
    assert "�" not in excerpt


def test_excerpt_unchanged_for_clean_diffs():
    excerpt = _build_excerpt(["New fine schedule applies."], ["Old fine schedule."])
    assert excerpt == "+ New fine schedule applies.  − Old fine schedule."


def test_alert_content_end_to_end_never_contains_replacement_chars():
    payload = {
        "source_name": "VARA Public Register — Licensed Entities",
        "url": "https://www.vara.ae/en/licenses-and-register/public-register/",
        "jurisdiction": "AE",
        "risk_level": "MEDIUM",
        "risk_details": {"rule": "MEDIUM_ARABIC", "matched_keywords": [], "matched_context": []},
        "added": ["VARA official page URL: https://www.vara.ae/ " + _mojibake(300)],
        "removed": [],
        "checked_at_utc": "2026-07-10T17:46:44+00:00",
    }
    content = build_alert_content(payload)
    assert "�" not in content["excerpt"]
    assert content["excerpt"] == _UNREADABLE_EXCERPT_NOTE
