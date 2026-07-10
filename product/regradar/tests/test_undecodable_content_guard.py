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

from app.adapters.base import is_quality_content, read_bytes_bounded
from app.alert_content import (
    _EXCERPT_CAP,
    _OMITTED_CONTENT_NOTE,
    _UNREADABLE_EXCERPT_NOTE,
    _build_excerpt,
    build_alert_content,
)
from app.text_quality import is_unreadable_char


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


def test_excerpt_total_length_capped_even_with_omission_note():
    long_readable = ("Administrative Resolution concerning licensing fees. " * 20).strip()
    excerpt = _build_excerpt([long_readable, _mojibake(200)], [])
    assert len(excerpt) <= _EXCERPT_CAP
    assert excerpt.endswith(_OMITTED_CONTENT_NOTE)


def test_excerpt_strips_markdown_metacharacters_from_kept_chunks():
    chunk = "See [Click here](https://evil.example/phish) *bold* _italic_ `code`"
    excerpt = _build_excerpt([chunk], [])
    for ch in "*_`[]":
        assert ch not in excerpt
    # Parentheses are legitimate legal-text characters and must survive —
    # without brackets they cannot form a Markdown link.
    assert "(39)" in _build_excerpt(["Resolution No. (39) of 2026"], [])


def test_excerpt_strips_stray_control_bytes_from_kept_chunks():
    # 2 BEL bytes in a ~70-char chunk is under the 5% drop threshold,
    # so the chunk is kept — but the control bytes must not survive.
    chunk = "Penalty schedule updated\x07 for licensed entities\x07 effective 2026."
    excerpt = _build_excerpt([chunk], [])
    assert "\x07" not in excerpt
    assert "Penalty schedule updated" in excerpt


# ── shared predicate: DEL and C1 range count as unreadable ────────────────────

def test_unreadable_predicate_covers_del_and_c1_range():
    assert is_unreadable_char("\x7f")   # DEL
    assert is_unreadable_char("\x85")   # NEL (C1)
    assert is_unreadable_char("\x9f")   # C1 upper bound
    assert is_unreadable_char("�")
    assert not is_unreadable_char("\n")
    assert not is_unreadable_char("ب")   # Arabic
    assert not is_unreadable_char("ж")   # Cyrillic
    assert not is_unreadable_char("😀")  # emoji


def test_quality_gate_boundary_floor_and_ratio_are_strict():
    para = "Licensing conditions apply to registered providers.\n\n"
    # 8 junk chars == floor → must pass regardless of ratio (strict >)
    base = (para * 12)[:492]
    assert is_quality_content(base + "�" * 8)
    # 10 junk in 500 chars == exactly the 2% ratio → still passes (strict >)
    assert is_quality_content((para * 12)[:490] + "�" * 10)
    # 11 junk in 500 chars → 2.2% > 2% → rejected
    assert not is_quality_content((para * 12)[:489] + "�" * 11)


# ── layer 1b: bounded reads stop decompression bombs ──────────────────────────

class _StubResponse:
    url = "https://example.test/page"

    def __init__(self, chunks: list[bytes]):
        self._chunks = chunks
        self.closed = False

    def iter_content(self, chunk_size: int):
        yield from self._chunks

    def close(self):
        self.closed = True


def test_read_bytes_bounded_returns_body_within_limit():
    stub = _StubResponse([b"a" * 1000] * 5)
    assert read_bytes_bounded(stub, 10_000) == b"a" * 5000


def test_read_bytes_bounded_aborts_oversized_decompressed_body():
    stub = _StubResponse([b"a" * 1024] * 20)  # 20 KB decompressed
    assert read_bytes_bounded(stub, 10 * 1024) is None
    assert stub.closed, "connection must be closed on abort"


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
