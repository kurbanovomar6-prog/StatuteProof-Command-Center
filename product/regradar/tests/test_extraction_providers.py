"""Branch-path coverage for the evidence-extraction provider layer.

This suite exercises the graceful-degradation branches of the extraction
providers — the "dependency missing", "dependency present", and internal-error
paths — that line coverage alone cannot see. Every optional dependency is
forced-absent deterministically (``sys.modules[name] = None`` makes the guarded
``import`` raise ``ImportError``) so the fallback branch is hit regardless of
what is installed in the test environment.

No invented regulatory content is used: fixtures are plainly synthetic HTML/PDF
byte strings that stand in for arbitrary fetched pages.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import extractors
from app.providers import html_extraction, optional_tools, pdf_extraction


# ── helpers ───────────────────────────────────────────────────────────────────

def _force_missing(monkeypatch, *module_names: str) -> None:
    """Make ``import <name>`` raise ImportError inside the provider under test."""
    for name in module_names:
        monkeypatch.setitem(sys.modules, name, None)


_LONG_PARAGRAPH = (
    "This paragraph contains enough words to clear the useful-content "
    "threshold used by the extraction quality gate so that it is not treated "
    "as a navigation shell or as low-content boilerplate. " * 20
)

_ARTICLE_HTML = (
    "<html><head><title>Doc</title></head><body>"
    "<nav>Home About Contact</nav>"
    f"<main><article><p>{_LONG_PARAGRAPH}</p></article></main>"
    "<footer>Footer</footer></body></html>"
)


# ── extractors.py: pure scoring / normalisation helpers ────────────────────────

class TestExtractorHelpers:
    def test_quality_thresholds_all_three_branches(self):
        assert extractors._quality(0) == "failed"
        assert extractors._quality(99) == "failed"
        assert extractors._quality(100) == "low_content"
        assert extractors._quality(999) == "low_content"
        assert extractors._quality(1000) == "good"

    def test_normalize_collapses_horizontal_space_keeps_paragraphs(self):
        out = extractors._normalize("a  \t b\n\n  c   d ")
        assert out == "a b\n\nc d"

    def test_deduplicate_removes_repeated_paragraphs(self):
        out = extractors._deduplicate("one\n\ntwo\n\none\n\n")
        assert out == "one\n\ntwo"

    def test_score_empty_is_zero(self):
        assert extractors._score("") == 0.0

    def test_score_penalises_duplicate_lines(self):
        line = "a meaningful line of real content that exceeds min length"
        unique_only = extractors._score(line)
        with_dupe = extractors._score(line + "\n" + line)
        assert with_dupe < unique_only


# ── extractors.py: individual strategy wrappers ────────────────────────────────

class TestBeautifulSoupStrategy:
    def test_returns_text_for_valid_html(self):
        assert extractors._try_beautifulsoup(_ARTICLE_HTML)

    def test_swallows_parser_error_returns_empty(self, monkeypatch):
        def _boom(_html):
            raise ValueError("parser exploded")

        monkeypatch.setattr(extractors, "extract_text", _boom)
        assert extractors._try_beautifulsoup("<p>x</p>") == ""


class TestTrafilaturaStrategy:
    def test_missing_dependency_returns_none(self, monkeypatch):
        _force_missing(monkeypatch, "trafilatura")
        assert extractors._try_trafilatura(_ARTICLE_HTML) is None


class TestReadabilityStrategy:
    def test_missing_dependency_returns_none(self, monkeypatch):
        _force_missing(monkeypatch, "readability")
        assert extractors._try_readability(_ARTICLE_HTML) is None


class TestCrawl4aiStrategy:
    def test_flag_off_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            "app.config.ENABLE_CRAWL4AI_EXTRACTOR", False, raising=False
        )
        assert extractors._try_crawl4ai("https://example.com") is None

    def test_empty_url_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            "app.config.ENABLE_CRAWL4AI_EXTRACTOR", True, raising=False
        )
        assert extractors._try_crawl4ai("") is None

    def test_non_http_scheme_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            "app.config.ENABLE_CRAWL4AI_EXTRACTOR", True, raising=False
        )
        assert extractors._try_crawl4ai("ftp://example.com/x") is None

    def test_flag_enabled_but_not_installed_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            "app.config.ENABLE_CRAWL4AI_EXTRACTOR", True, raising=False
        )
        _force_missing(monkeypatch, "crawl4ai")
        assert extractors._try_crawl4ai("https://example.com") is None


# ── extractors.py: legacy cascade ──────────────────────────────────────────────

class TestLegacyCascade:
    def test_empty_html_short_circuits(self):
        result = extractors._legacy_extract_best_text("")
        assert result["method"] == "none"
        assert result["quality"] == "failed"
        assert result["extracted_chars"] == 0

    def test_good_html_selects_viable_candidate(self):
        result = extractors._legacy_extract_best_text(_ARTICLE_HTML, "https://x.test")
        assert result["extracted_chars"] >= extractors._LOW_CHARS
        assert result["method"] == result["provider_used"]
        assert any(c["method"] == "beautifulsoup" for c in result["candidates"])

    def test_trivially_short_html_falls_back_to_bs4(self):
        result = extractors._legacy_extract_best_text("<p>hi</p>", "")
        assert result["method"] == "beautifulsoup"
        assert result["quality"] == "failed"


# ── extractors.py: public extract_best_text ────────────────────────────────────

class TestExtractBestText:
    def test_empty_html_returns_none_provider(self):
        result = extractors.extract_best_text("")
        assert result["method"] == "none"
        assert result["provider_used"] == "none"
        assert result["candidates"] == []

    def test_provider_success_path(self):
        result = extractors.extract_best_text(_ARTICLE_HTML, "https://x.test")
        assert result["extracted_chars"] > 0
        assert result["quality"] in {"good", "low_content", "failed"}
        assert isinstance(result["candidates"], list) and result["candidates"]

    def test_provider_exception_falls_back_to_legacy(self, monkeypatch):
        def _boom(*_a, **_k):
            raise RuntimeError("cascade down")

        monkeypatch.setattr(
            "app.providers.html_extraction.best_html_extract", _boom
        )
        result = extractors.extract_best_text(_ARTICLE_HTML, "https://x.test")
        # legacy fallback still returns a structured result
        assert "method" in result and "candidates" in result

    def test_provider_no_content_appends_warning(self, monkeypatch):
        def _empty(*_a, **_k):
            return {"success": False, "error": "provider produced nothing"}

        monkeypatch.setattr(
            "app.providers.html_extraction.best_html_extract", _empty
        )
        result = extractors.extract_best_text(_ARTICLE_HTML, "https://x.test")
        assert "provider produced nothing" in result["warnings"]


# ── providers/html_extraction.py ───────────────────────────────────────────────

class TestNavShellDetection:
    def test_empty_is_not_nav_shell(self):
        assert html_extraction._looks_nav_shell("") is False

    def test_huge_text_is_not_nav_shell(self):
        assert html_extraction._looks_nav_shell("x " * 6000) is False

    def test_few_lines_is_not_nav_shell(self):
        assert html_extraction._looks_nav_shell("one\ntwo\nthree") is False

    def test_many_short_lines_is_nav_shell(self):
        shell = "\n".join(f"Menu {i}" for i in range(20))
        assert html_extraction._looks_nav_shell(shell) is True

    def test_long_lines_not_nav_shell(self):
        body = "\n".join(_LONG_PARAGRAPH for _ in range(12))
        assert html_extraction._looks_nav_shell(body) is False


class TestHtmlProvidersDependencyMissing:
    def test_trafilatura_missing(self, monkeypatch):
        _force_missing(monkeypatch, "trafilatura")
        r = html_extraction.trafilatura_extract(_ARTICLE_HTML)
        assert r["dependency_available"] is False and r["success"] is False

    def test_readability_missing(self, monkeypatch):
        _force_missing(monkeypatch, "readability")
        r = html_extraction.readability_extract(_ARTICLE_HTML)
        assert r["dependency_available"] is False and r["success"] is False

    def test_selectolax_missing(self, monkeypatch):
        _force_missing(monkeypatch, "selectolax", "selectolax.parser")
        r = html_extraction.selectolax_extract(_ARTICLE_HTML)
        assert r["dependency_available"] is False and r["success"] is False

    def test_bs4_missing(self, monkeypatch):
        _force_missing(monkeypatch, "bs4")
        r = html_extraction.bs4_extract(_ARTICLE_HTML)
        assert r["dependency_available"] is False and r["success"] is False


class TestBs4ExtractPresent:
    def test_bs4_extracts_visible_text(self):
        # bs4 is a hard dependency of the project, so this hits the success path.
        r = html_extraction.bs4_extract(_ARTICLE_HTML)
        assert r["provider_name"] == "bs4"
        assert r["success"] is True
        assert "Footer" not in r["content"]  # footer decomposed


class TestBestHtmlExtract:
    def test_content_selector_useful_returns_early(self, monkeypatch):
        useful = html_extraction._provider_result(
            provider_name="selectolax",
            success=True,
            dependency_available=True,
            content=_LONG_PARAGRAPH,
            confidence="medium",
        )
        monkeypatch.setattr(
            html_extraction, "selectolax_extract", lambda *_a, **_k: dict(useful)
        )
        result = html_extraction.best_html_extract(_ARTICLE_HTML, content_selector="main")
        assert result["provider_name"] == "selectolax"
        assert result["candidates"]

    def test_cascade_returns_first_useful(self):
        result = html_extraction.best_html_extract(_ARTICLE_HTML)
        assert result["success"] is True
        assert result.get("candidates")

    def test_all_providers_short_returns_best_fallback(self, monkeypatch):
        def _short(html):
            return html_extraction._provider_result(
                provider_name="stub",
                success=True,
                dependency_available=True,
                content="tiny",
            )

        for name in ("trafilatura_extract", "readability_extract",
                     "selectolax_extract", "bs4_extract"):
            monkeypatch.setattr(html_extraction, name, _short)
        result = html_extraction.best_html_extract(_ARTICLE_HTML)
        assert any("best fallback" in w for w in result["warnings"])

    def test_content_selector_nav_shell_gets_warning(self, monkeypatch):
        shell = "\n".join(f"Nav {i}" for i in range(20))

        def _shell(_html, _sel=None):
            return html_extraction._provider_result(
                provider_name="selectolax",
                success=True,
                dependency_available=True,
                content=shell,
            )

        monkeypatch.setattr(html_extraction, "selectolax_extract", _shell)
        # force the rest of the cascade to also be short so we exercise fallback
        for name in ("trafilatura_extract", "readability_extract", "bs4_extract"):
            monkeypatch.setattr(
                html_extraction, name,
                lambda _h: html_extraction._provider_result(
                    provider_name="stub", success=True,
                    dependency_available=True, content="tiny",
                ),
            )
        result = html_extraction.best_html_extract(_ARTICLE_HTML, content_selector="main")
        # selectolax content_selector output was flagged as a nav shell
        assert result is not None
        first = result["candidates"][0]
        assert any("navigation shell" in w for w in first["warnings"])


# ── providers/pdf_extraction.py ────────────────────────────────────────────────

_GARBAGE_PDF = b"%PDF-1.4 this is not really a valid pdf body at all"


class TestPdfProvidersDependencyMissing:
    def test_pymupdf_missing(self, monkeypatch):
        _force_missing(monkeypatch, "fitz")
        r = pdf_extraction.pymupdf_extract(_GARBAGE_PDF)
        assert r["dependency_available"] is False and r["success"] is False

    def test_pdfplumber_missing(self, monkeypatch):
        _force_missing(monkeypatch, "pdfplumber")
        r = pdf_extraction.pdfplumber_extract(_GARBAGE_PDF)
        assert r["dependency_available"] is False and r["success"] is False

    def test_pypdf_missing(self, monkeypatch):
        _force_missing(monkeypatch, "pypdf")
        r = pdf_extraction.pypdf_extract(_GARBAGE_PDF)
        assert r["dependency_available"] is False and r["success"] is False


class TestPdfProvidersErrorPath:
    """When the library IS present, garbage bytes drive the inner-error branch.

    Each assertion tolerates the dependency being absent in some CI images:
    either the error branch (available=True, success=False) or the missing
    branch (available=False) is acceptable; both mean 'no text extracted'.
    """

    def test_pymupdf_bad_bytes(self):
        r = pdf_extraction.pymupdf_extract(_GARBAGE_PDF)
        assert r["success"] is False

    def test_pdfplumber_bad_bytes(self):
        r = pdf_extraction.pdfplumber_extract(_GARBAGE_PDF)
        assert r["success"] is False

    def test_pypdf_bad_bytes(self):
        r = pdf_extraction.pypdf_extract(_GARBAGE_PDF)
        assert r["success"] is False


class TestBestPdfExtract:
    def test_all_fail_returns_none_provider(self):
        result = pdf_extraction.best_pdf_extract(_GARBAGE_PDF)
        assert result["success"] is False
        assert result["provider_name"] == "none"

    def test_first_success_short_circuits(self, monkeypatch):
        good = pdf_extraction._provider_result(
            provider_name="pymupdf", success=True,
            dependency_available=True, content="real text", page_count=1,
        )
        monkeypatch.setattr(
            pdf_extraction, "pymupdf_extract", lambda _b: dict(good)
        )
        result = pdf_extraction.best_pdf_extract(_GARBAGE_PDF)
        assert result["provider_name"] == "pymupdf" and result["success"] is True


# ── providers/optional_tools.py ────────────────────────────────────────────────

class TestOptionalTools:
    def test_htmldate_missing_fallback(self, monkeypatch):
        _force_missing(monkeypatch, "htmldate")
        r = optional_tools.extract_date_from_html(_ARTICLE_HTML)
        assert r["available"] is False and r["success"] is False

    def test_courlan_missing_uses_urllib_fallback_valid(self, monkeypatch):
        _force_missing(monkeypatch, "courlan")
        r = optional_tools.canonicalize_url("https://example.com/page")
        assert r["provider"] == "courlan_fallback_urllib"
        assert r["is_valid"] is True

    def test_courlan_missing_urllib_fallback_invalid(self, monkeypatch):
        _force_missing(monkeypatch, "courlan")
        r = optional_tools.canonicalize_url("not-a-url")
        assert r["is_valid"] is False

    def test_deepdiff_present_detects_changes(self):
        # An added key is reported by deepdiff even at verbose_level=0.
        r = optional_tools.structured_diff({"a": 1}, {"a": 1, "b": 2})
        assert r["success"] is True
        assert r["has_changes"] is True

    def test_deepdiff_present_no_changes(self):
        r = optional_tools.structured_diff({"a": 1}, {"a": 1})
        assert r["success"] is True
        assert r["has_changes"] is False

    def test_deepdiff_missing_shallow_fallback(self, monkeypatch):
        _force_missing(monkeypatch, "deepdiff")
        r = optional_tools.structured_diff({"a": 1, "b": 2}, {"a": 1, "c": 3})
        assert r["provider"] == "deepdiff_fallback_shallow"
        assert r["has_changes"] is True
        assert r["diff"]["added"] == {"c": 3}
        assert r["diff"]["removed"] == {"b": 2}

    def test_deepdiff_missing_no_changes(self, monkeypatch):
        _force_missing(monkeypatch, "deepdiff")
        r = optional_tools.structured_diff({"a": 1}, {"a": 1})
        assert r["has_changes"] is False
