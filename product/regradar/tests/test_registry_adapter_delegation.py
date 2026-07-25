"""Guard the intake→FETCHING-registry-adapter delegation boundary.

Why this file exists
--------------------
The readiness gate used to fetch every document itself and could only transform
HTML, so a source served by a fetching-registry adapter (xml_feed, html_listing,
rulebook_platform, the per-host adapters) could never be certified: the gate read
raw XML or a listing shell, ran the generic extractor over it and scored
NAV_SHELL_ONLY / CERTIFICATION_FAILED while the monitoring pipeline read the very
same source perfectly.

Delegation fixed that, but the FIRST version delegated whenever
``get_adapter_for_url`` matched — and several registry adapters match on HOST
alone. That hijacked a direct-PDF source and broke eight existing tests. The
boundary is therefore deliberately narrow, and every clause below is load-bearing:
these tests exist so a future widening of it fails loudly here instead of silently
shifting a live source's baseline hash.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.source_intake import (  # noqa: E402
    _extract_intake_config,
    _fetch_via_registry_adapter,
    _has_structured_adapter_content,
    _mark_registry_adapter_result,
)

_DIGEST = "Official listing monitor\n" + "\n".join(f"08 Jan 2026 Decision {i}" for i in range(40))


class _FakeAdapter:
    """Stands in for a registry adapter; records whether it was asked to fetch."""

    def __init__(self, name: str, text: str | None = _DIGEST, raises: bool = False):
        self.name = name
        self._text = text
        self._raises = raises
        self.fetch_calls = 0

    def fetch_content(self, _url, _source=None):  # adapter contract: (url, source)
        self.fetch_calls += 1
        if self._raises:
            raise RuntimeError("adapter exploded")
        return self._text


def _delegate(source: dict, adapter: _FakeAdapter | None):
    """Run the delegation probe for `source` with `adapter` as the registry match."""
    result: dict = {}
    cfg = _extract_intake_config(source)
    with patch("app.adapters.registry.get_adapter_for_url", return_value=adapter):
        text = _fetch_via_registry_adapter(result, source, cfg)
    return text, result


def _source(**over) -> dict:
    base = {
        "source_id": "AE-test-listing",
        "url": "https://ofac.treasury.gov/recent-actions",
        "adapter_name": "html_listing",
        "adapter_config": {"content_selector": ".view-content"},
    }
    base.update(over)
    return base


# ── delegation engages ───────────────────────────────────────────────────────


def test_delegation_engages_when_the_source_names_the_adapter():
    adapter = _FakeAdapter("html_listing")
    text, result = _delegate(_source(), adapter)

    assert text == _DIGEST
    assert adapter.fetch_calls == 1
    assert result["registry_adapter_used"] is True
    assert result["registry_adapter_name"] == "html_listing"


def test_delegation_reports_the_adapter_text_length_as_raw_chars():
    """chars_raw must be set or the gate's "chars_raw < 200" branch scores the
    source BLOCKED — the normal fetch that usually sets it was skipped."""
    text, result = _delegate(_source(), _FakeAdapter("html_listing"))

    assert text is not None
    assert result["chars_raw"] == len(text)
    assert result["chars_raw"] >= 200


# ── delegation refuses (each clause is a real bug it prevents) ───────────────


def test_a_host_matched_adapter_cannot_hijack_a_source_configured_for_another():
    """The regression that broke eight tests: an adapter matching on host alone
    must not replace the text of a source that asked for a different one."""
    adapter = _FakeAdapter("uae_dfsa")
    text, result = _delegate(_source(adapter_name="dfsa_notice_listing"), adapter)

    assert text is None
    assert adapter.fetch_calls == 0, "the wrong adapter must not even be fetched"
    assert "registry_adapter_used" not in result


def test_direct_pdf_sources_are_never_delegated():
    """A per-host adapter can match a PDF's host; delegating would silently
    replace the extracted PDF text with a listing digest."""
    pdf_source = _source(
        url="https://rulebooks.vara.ae/sites/default/files/x/VARA_Rulebook.pdf",
        source_type="pdf",
        adapter_name="html_listing",
    )
    cfg = _extract_intake_config(pdf_source)
    assert cfg.is_direct_pdf, "fixture must actually be a direct-PDF source"

    adapter = _FakeAdapter("html_listing")
    text, result = _delegate(pdf_source, adapter)

    assert text is None
    assert adapter.fetch_calls == 0
    assert "registry_adapter_used" not in result


def test_a_source_without_an_adapter_name_is_untouched():
    adapter = _FakeAdapter("html_listing")
    text, result = _delegate(_source(adapter_name=""), adapter)

    assert text is None
    assert adapter.fetch_calls == 0
    assert result == {}


def test_no_registry_match_leaves_the_normal_fetch_path_alone():
    text, result = _delegate(_source(), None)

    assert text is None
    assert result == {}


def test_empty_adapter_output_is_not_labelled_as_delegated():
    """Selector drift returns None/blank. Recording "registry adapter used" here
    would exempt an empty payload from the nav-shell heuristic."""
    for blank in (None, "", "   \n\t "):
        text, result = _delegate(_source(), _FakeAdapter("html_listing", text=blank))
        assert text is None
        assert "registry_adapter_used" not in result


def test_an_adapter_that_raises_falls_back_instead_of_breaking_intake():
    text, result = _delegate(_source(), _FakeAdapter("html_listing", raises=True))

    assert text is None
    assert "registry_adapter_used" not in result


# ── provenance labels survive the extraction phase ───────────────────────────


def test_marking_restores_provenance_after_the_platform_relabels_it():
    """_extract_source_text rewrites adapter_*/provider_used unconditionally, so
    without this the recorded provenance would claim generic_fallback:bs4
    produced bytes that a registry adapter actually produced."""
    result = {
        "registry_adapter_used": True,
        "registry_adapter_name": "xml_feed",
        "adapter_family": "static_html",
        "provider_used": "generic_fallback:bs4",
        "extraction_strategy": "generic_fallback:bs4",
    }
    _mark_registry_adapter_result(result)

    assert result["provider_used"] == "registry_adapter:xml_feed"
    assert result["extraction_strategy"] == "registry_adapter:xml_feed"
    assert result["extraction_method"] == "registry_adapter:xml_feed"
    assert result["adapter_used"] is True
    assert result["adapter_family"] == "xml_feed"


def test_marking_clears_a_stale_platform_failure_note():
    """A leftover platform failure would read as if the monitored content failed
    when the registry adapter in fact produced it."""
    result = {
        "registry_adapter_used": True,
        "registry_adapter_name": "html_listing",
        "adapter_declared_and_failed": True,
        "adapter_fallback_used": True,
        "adapter_failure_reason": "selector matched nothing",
        "adapter_warnings": ["stale"],
    }
    _mark_registry_adapter_result(result)

    assert "adapter_declared_and_failed" not in result
    assert "adapter_fallback_used" not in result
    assert "adapter_failure_reason" not in result
    assert result["adapter_warnings"] == []


# ── the nav-shell exemption is bounded by size, not blanket ──────────────────


def test_registry_adapter_text_is_structured_by_construction():
    """A dated listing is >=65% short lines, so the HTML-shaped nav-shell
    heuristic reads it as a navigation menu. Registry digests bypass it."""
    assert _has_structured_adapter_content(
        {"registry_adapter_used": True, "chars_normalized": 5000}
    )


def test_the_exemption_does_not_cover_a_thin_payload():
    """The exemption is not a blanket pass: a near-empty digest still fails, so
    selector drift degrades loudly instead of certifying an empty page."""
    assert not _has_structured_adapter_content(
        {"registry_adapter_used": True, "chars_normalized": 199}
    )
    assert not _has_structured_adapter_content(
        {"registry_adapter_used": True, "chars_normalized": 0}
    )
