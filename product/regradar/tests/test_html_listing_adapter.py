"""
html_listing adapter — app/adapters/html_listing.py — and the config-gated
entire-section threshold added to rulebook_platform.

Covers:
  1. Strict opt-in dispatch (adapter_name + content_selector + host allowlist).
  2. Selector-scoped extraction: cleaned lines, deterministic output,
     selector-miss and too-thin regions fall back (return None).
  3. rulebook_platform entire_section_min_chars override: default unchanged
     for every existing source; override honored, floored, garbage-tolerant.

All tests use inline fixtures / mocks. No live network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.base import is_quality_content
from app.adapters.html_listing import HtmlListingAdapter
from app.adapters.registry import get_adapter_for_url
from app.adapters.rulebook_platform import (
    _MIN_ENTIRE_SECTION_CHARS,
    _entire_section_min_chars,
)


_ADAPTER = HtmlListingAdapter()

_OFAC_URL = "https://ofac.treasury.gov/recent-actions"
_MENAFATF_URL = "https://www.menafatf.org/information-center/general-publications"

_OFAC_SOURCE = {
    "adapter_name": "html_listing",
    "adapter_config": {"content_selector": ".view-content"},
}

_ROWS = "".join(
    f'<div class="views-row"><a href="/recent-actions/{i}">Sanctions action number {i} '
    f"with a descriptive title</a><span>July {i:02d}, 2026</span>"
    f"<span>Sanctions List Updates</span></div>"
    for i in range(1, 11)
)
_LISTING_HTML = f"""
<html><head><script>var junk=1;</script><style>.x{{}}</style></head>
<body>
  <nav><ul><li>Huge navigation</li><li>More nav</li></ul></nav>
  <main><div class="view-content">{_ROWS}</div></main>
</body></html>
"""


# ── opt-in dispatch ──────────────────────────────────────────────────────────

def test_can_handle_requires_source_opt_in_and_selector():
    assert _ADAPTER.can_handle(_OFAC_URL, None) is False
    assert _ADAPTER.can_handle(_OFAC_URL, {"adapter_name": "html_listing"}) is False  # no selector
    assert _ADAPTER.can_handle(_OFAC_URL, {"adapter_name": "xml_feed"}) is False
    assert _ADAPTER.can_handle(_OFAC_URL, _OFAC_SOURCE) is True


def test_can_handle_enforces_host_allowlist():
    src = dict(_OFAC_SOURCE)
    assert _ADAPTER.can_handle(_MENAFATF_URL, src) is True
    assert _ADAPTER.can_handle("https://evil.example.com/page", src) is False
    assert _ADAPTER.can_handle("https://menafatf.org.evil.com/page", src) is False


def test_registry_dispatches_only_on_opt_in():
    assert get_adapter_for_url(_OFAC_URL, _OFAC_SOURCE).name == "html_listing"
    assert get_adapter_for_url(_OFAC_URL, None) is None


# ── extraction ───────────────────────────────────────────────────────────────

def test_extract_scopes_to_selector_and_drops_chrome():
    text = HtmlListingAdapter.extract(_LISTING_HTML, _OFAC_URL, ".view-content")
    assert text is not None
    assert "Sanctions action number 3" in text
    assert "July 03, 2026" in text
    assert "Huge navigation" not in text
    assert "var junk" not in text


def test_extract_is_deterministic_and_passes_quality_gate():
    a = HtmlListingAdapter.extract(_LISTING_HTML, _OFAC_URL, ".view-content")
    b = HtmlListingAdapter.extract(_LISTING_HTML, _OFAC_URL, ".view-content")
    assert a == b
    assert is_quality_content(a)


def test_extract_selector_miss_returns_none():
    assert HtmlListingAdapter.extract(_LISTING_HTML, _OFAC_URL, ".does-not-exist") is None


def test_extract_too_thin_region_returns_none():
    html = '<html><body><div class="view-content">tiny</div></body></html>'
    assert HtmlListingAdapter.extract(html, _OFAC_URL, ".view-content") is None


def test_fetch_content_returns_none_on_fetch_failure():
    with patch("app.adapters.html_listing.fetch_text_bounded", return_value=None):
        assert _ADAPTER.fetch_content(_OFAC_URL, _OFAC_SOURCE) is None


def test_fetch_content_never_raises():
    with patch("app.adapters.html_listing.fetch_text_bounded", side_effect=RuntimeError("boom")):
        assert _ADAPTER.fetch_content(_OFAC_URL, _OFAC_SOURCE) is None


def test_fetch_content_end_to_end_with_mocked_fetch():
    with patch("app.adapters.html_listing.fetch_text_bounded", return_value=_LISTING_HTML):
        text = _ADAPTER.fetch_content(_OFAC_URL, _OFAC_SOURCE)
    assert "Content selector: .view-content" in text
    assert "Sanctions action number 10" in text


# ── rulebook_platform entire_section_min_chars config gate ───────────────────

def test_rulebook_default_threshold_unchanged_without_config():
    """Every existing rulebook_platform source (no override key) must keep the
    3000-char default — their output stays byte-identical."""
    assert _entire_section_min_chars(None) == _MIN_ENTIRE_SECTION_CHARS
    assert _entire_section_min_chars({}) == _MIN_ENTIRE_SECTION_CHARS
    assert _entire_section_min_chars({"adapter_config": {}}) == _MIN_ENTIRE_SECTION_CHARS
    assert (
        _entire_section_min_chars({"adapter_config": {"content_selector": "main"}})
        == _MIN_ENTIRE_SECTION_CHARS
    )


def test_rulebook_override_is_honored_and_floored():
    assert _entire_section_min_chars(
        {"adapter_config": {"entire_section_min_chars": 1200}}
    ) == 1200
    # below the JS-shell floor → clamped, never disabled
    assert _entire_section_min_chars(
        {"adapter_config": {"entire_section_min_chars": 5}}
    ) == 600


def test_rulebook_override_garbage_falls_back_to_default():
    assert _entire_section_min_chars(
        {"adapter_config": {"entire_section_min_chars": "not-a-number"}}
    ) == _MIN_ENTIRE_SECTION_CHARS
