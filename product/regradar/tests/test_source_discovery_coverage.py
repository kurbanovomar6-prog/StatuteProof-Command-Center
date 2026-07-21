"""
Behavioral coverage tests for app.source_discovery.

Focus: the deterministic classification / scoring / verdict / gating logic and
error handling that is testable in-process. All network, Playwright, and
document-extraction I/O is mocked; no live endpoint or browser is touched.

These tests assert REAL behavior (return values, verdicts, capability flags,
readiness scores, client field mapping, error/warning handling) — not imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.source_discovery as sd


# ── fake HTTP response doubles ────────────────────────────────────────────────

class _Resp:
    """Streamed-response stand-in supporting `with resp:` and `.text`."""

    def __init__(self, status=200, text="", *, url="https://example.gov/", body=b""):
        self.status_code = status
        self._text = text
        self.url = url
        self.headers = {}
        # The discovery read path now streams the body via iter_content and
        # decodes it (bounded), instead of touching resp.text — mirror a real
        # requests.Response so the fake feeds content through the same seam.
        self._body = body or text.encode("utf-8")
        self.encoding = "utf-8"

    @property
    def ok(self):
        return 200 <= self.status_code < 400

    @property
    def text(self):
        return self._text

    def iter_content(self, chunk_size):
        yield self._body

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# ── _quality ──────────────────────────────────────────────────────────────────

def test_quality_thresholds():
    assert sd._quality(2_000) == "good"
    assert sd._quality(1_000) == "good"
    assert sd._quality(500) == "low_content"
    assert sd._quality(100) == "low_content"
    assert sd._quality(99) == "failed"
    assert sd._quality(0) == "failed"


# ── _infer_source_type ─────────────────────────────────────────────────────────

def test_infer_source_type_variants():
    assert sd._infer_source_type("https://x/report.pdf") == "pdf_document"
    assert sd._infer_source_type("https://x/api", content_type="application/json") == "public_json_api"
    assert sd._infer_source_type("https://x/rss.xml", signals=["rss"]) == "feed"
    assert sd._infer_source_type("https://x/sitemap.xml") == "sitemap"
    assert sd._infer_source_type("https://x/licensed-register") == "register"
    assert sd._infer_source_type("https://x/rulebook/module-1") == "rulebook"
    assert sd._infer_source_type("https://x/data-table") == "table"
    assert sd._infer_source_type("https://x/en/circular-2026") == "listing"
    assert sd._infer_source_type("https://x/about") == "html_page"


def test_infer_source_type_sca_register_by_open_data_slug():
    # sca.gov.ae + companies token → register even without "register" in path
    assert sd._infer_source_type("https://www.sca.gov.ae/open-data/companies") == "register"


# ── _adapter_for_source_type ───────────────────────────────────────────────────

def test_adapter_for_source_type_by_type():
    assert sd._adapter_for_source_type("public_json_api")[0] == "public_json_api"
    assert sd._adapter_for_source_type("pdf_document")[0] == "pdf_document"
    assert sd._adapter_for_source_type("feed")[0] == "sitemap_feed"
    assert sd._adapter_for_source_type("sitemap")[0] == "sitemap_feed"
    assert sd._adapter_for_source_type("register")[0] == "register"
    assert sd._adapter_for_source_type("table")[0] == "table"


def test_adapter_for_source_type_by_domain():
    assert sd._adapter_for_source_type("listing", "https://www.sca.gov.ae/x")[0] == "sca_listing"
    assert sd._adapter_for_source_type("listing", "https://cbuae.gov.ae/x")[0] == "cbuae_document_listing"
    assert sd._adapter_for_source_type("listing", "https://tax.gov.ae/x")[0] == "fta_tax_listing"
    assert sd._adapter_for_source_type("listing", "https://adgm.com/x")[0] == "adgm_fsra_listing"
    assert sd._adapter_for_source_type("listing", "https://dfsa.ae/x")[0] == "dfsa_notice_listing"
    assert sd._adapter_for_source_type("listing", "https://vara.ae/x")[0] == "vara_pdf_listing"
    assert sd._adapter_for_source_type("listing", "https://fiu.gov.ae/x")[0] == "fiu_eocn_document_listing"


def test_adapter_for_source_type_rulebook_and_fallback():
    fam, name = sd._adapter_for_source_type("rulebook", "https://dfsa.ae/rulebook")
    assert fam == "dfsa_rulebook" and name == "dfsa_rulebook"
    # rulebook type but no dfsa/rulebook token in url+title → name falls back to listing
    fam2, name2 = sd._adapter_for_source_type("rulebook", "https://x/foo", "bar")
    assert fam2 == "dfsa_rulebook" and name2 == "listing"
    # generic listing on an unknown domain
    assert sd._adapter_for_source_type("listing", "https://unknown.example/x")[0] == "listing"
    # completely unknown type + domain → static_html
    assert sd._adapter_for_source_type("html_page", "https://unknown.example/x")[0] == "static_html"


# ── _normalize_candidate_url ────────────────────────────────────────────────────

def test_normalize_candidate_url_collapses_sca_doubled_paths():
    doubled = "https://www.sca.gov.ae/en/regulations/en/regulations/market-rules"
    assert sd._normalize_candidate_url(doubled) == "https://www.sca.gov.ae/en/regulations/market-rules"
    # non-sca host is returned untouched
    other = "https://example.gov/en/regulations/en/regulations/x"
    assert sd._normalize_candidate_url(other) == other


# ── _private_url_reason ────────────────────────────────────────────────────────

def test_private_url_reason_detects_creds_and_login():
    assert sd._private_url_reason("https://user:pass@x.gov/") == "credentials-in-url"
    assert "private" in sd._private_url_reason("https://x.gov/login")
    assert sd._private_url_reason("https://x.gov/en/regulations") == ""


# ── _is_sca_low_value_candidate ────────────────────────────────────────────────

def test_is_sca_low_value_candidate_rules():
    # allowed open-data slug → not low value
    assert sd._is_sca_low_value_candidate("https://www.sca.gov.ae/open-data/companies") is False
    # generic chrome fragment → low value
    assert sd._is_sca_low_value_candidate("https://www.sca.gov.ae/about-us") is True
    # generic title → low value
    assert sd._is_sca_low_value_candidate("https://www.sca.gov.ae/x", title="About Us") is True
    # non-allowed open-data path with non-register type → low value
    assert sd._is_sca_low_value_candidate("https://www.sca.gov.ae/open-data/foo", source_type="listing") is True
    # non-allowed open-data path but register type → allowed
    assert sd._is_sca_low_value_candidate("https://www.sca.gov.ae/open-data/foo", source_type="register") is False
    # non-sca host → never low value
    assert sd._is_sca_low_value_candidate("https://cbuae.gov.ae/about-us") is False


# ── parse_feed_xml ──────────────────────────────────────────────────────────────

def test_parse_feed_xml_atom_relative_link_resolved():
    atom = """
    <feed>
      <entry><title>Notice A</title><link href="/en/a" /><updated>2026-06-01</updated></entry>
      <entry><title>Notice B</title><link href="https://gov.example/b" /></entry>
    </feed>
    """
    parsed = sd.parse_feed_xml(atom, "https://gov.example/atom.xml")
    assert parsed["item_count"] == 2
    assert parsed["items"][0]["url"] == "https://gov.example/en/a"
    assert parsed["items"][0]["date"] == "2026-06-01"
    assert parsed["items"][1]["url"] == "https://gov.example/b"


def test_parse_feed_xml_empty_input():
    parsed = sd.parse_feed_xml("", "https://gov.example/feed")
    assert parsed["item_count"] == 0
    assert parsed["items"] == []


# ── parse_sitemap_xml invalid input ─────────────────────────────────────────────

def test_parse_sitemap_xml_invalid_returns_failure_reason():
    result = sd.parse_sitemap_xml("<not-valid-xml", "https://x/sitemap.xml")
    assert result["type"] == "invalid"
    assert result["entries"] == []
    assert result["failure_reason"]


def test_parse_sitemap_xml_unknown_root():
    result = sd.parse_sitemap_xml("<html><body>x</body></html>", "https://x/s.xml")
    assert result["type"] == "unknown"
    assert result["entries"] == []


# ── _extract_links (Layer 4 pure parser) ────────────────────────────────────────

def test_extract_links_categorizes_by_keyword_and_extension():
    html = """
    <html><body>
      <a href="/law/decree-2026.pdf">Federal Decree Law</a>
      <a href="/news/press-release">Press release</a>
      <a href="/en/regulation/circular">Circular guidance</a>
      <a href="#frag">frag</a>
      <a href="mailto:x@y.z">mail</a>
      <a href="https://other.example/misc">misc external</a>
    </body></html>
    """
    out = sd._extract_links(html, "https://cbuae.gov.ae/en")
    assert "https://cbuae.gov.ae/law/decree-2026.pdf" in out["document_links"]
    assert any("decree-2026.pdf" in u for u in out["legal_links"])
    assert any("press-release" in u for u in out["news_links"])
    # publication_links includes all valid hrefs (frag/mailto excluded)
    assert not any(u.startswith("mailto") for u in out["publication_links"])
    assert not any("#frag" in u for u in out["publication_links"])


# ── _readiness_score branches ───────────────────────────────────────────────────

def test_readiness_score_ready_html_source():
    result = {
        "safe_url": True,
        "page": {"status": "ok", "used_playwright": False, "quality": "good"},
        "capabilities": {"html_monitoring": True},
        "links": {"publication_links": list(range(25))},
        "verdict": "can_monitor",
        "recommended_mode": "html",
    }
    # 10 safe + 15 reachable + 30 html + 10 (>20 links) = 65
    assert sd._readiness_score(result) == 65


def test_readiness_score_feed_source_high():
    result = {
        "safe_url": True,
        "page": {"status": "ok", "used_playwright": False, "quality": "good"},
        "capabilities": {"html_monitoring": True, "feed_monitoring": True},
        "links": {"publication_links": []},
        "verdict": "can_monitor",
        "recommended_mode": "feed",
    }
    # 10 + 15 + 30 html + 25 feed = 80
    assert sd._readiness_score(result) == 80


def test_readiness_score_low_content_penalty_and_cap():
    result = {
        "safe_url": True,
        "page": {"status": "ok", "used_playwright": False, "quality": "low_content"},
        "capabilities": {},
        "links": {"publication_links": []},
        "verdict": "needs_adapter",
        "recommended_mode": "adapter",
    }
    # 10 + 15 - 20(low_content no alternative) = 5, then needs_adapter cap 60 → 5
    assert sd._readiness_score(result) == 5


def test_readiness_score_cannot_monitor_capped_at_25():
    result = {
        "safe_url": True,
        "page": {"status": "ok", "used_playwright": True, "quality": "good"},
        "capabilities": {"js_html_monitoring": True, "feed_monitoring": True,
                         "sitemap_monitoring": True, "document_monitoring": True},
        "links": {"publication_links": list(range(30))},
        "verdict": "cannot_monitor",
        "recommended_mode": "unavailable",
    }
    assert sd._readiness_score(result) == 25


def test_readiness_score_playwright_weak_extraction():
    result = {
        "safe_url": True,
        "page": {"status": "ok", "used_playwright": True, "quality": "low_content"},
        "capabilities": {},
        "links": {"publication_links": []},
        "verdict": "needs_adapter",
        "recommended_mode": "adapter",
    }
    # 10 + 15 + 10 (playwright reached, quality != failed) - 20 (low_content, no alt) = 15
    assert sd._readiness_score(result) == 15


# ── _client_fields mapping ───────────────────────────────────────────────────────

def test_client_fields_unavailable_and_custom_adapter():
    unavail = sd._client_fields({"verdict": "cannot_monitor"}, 10)
    assert unavail["client_verdict"] == "unavailable"
    assert unavail["client_title"] == sd._CLIENT_TITLES["unavailable"]

    custom = sd._client_fields({"verdict": "needs_adapter"}, 40)
    assert custom["client_verdict"] == "custom_adapter"


def test_client_fields_ready_vs_limited_by_score():
    ready = sd._client_fields({"verdict": "can_monitor"}, 80)
    assert ready["client_verdict"] == "ready"
    limited = sd._client_fields({"verdict": "can_monitor"}, 50)
    assert limited["client_verdict"] == "limited"
    assert limited["readiness_score"] == 50


# ── _empty_result ────────────────────────────────────────────────────────────────

def test_empty_result_is_unavailable_contract():
    res = sd._empty_result("https://x/", safe=False, reason="bad url")
    assert res["verdict"] == "cannot_monitor"
    assert res["recommended_mode"] == "unavailable"
    assert res["client_verdict"] == "unavailable"
    assert res["reason"] == "bad url"
    assert res["readiness_score"] <= 25


# ── generate_source_candidate gating ─────────────────────────────────────────────

def test_generate_source_candidate_all_gates_hold_and_id_slug():
    gen = sd.generate_source_candidate(
        {"candidate_url": "https://www.sca.gov.ae/en/regulations/aml",
         "title": "AML", "source_type": "listing",
         "adapter_family": "sca_listing", "adapter_name": "sca_listing"},
        regulator="SCA", jurisdiction="UAE",
    )
    assert gen["current_state"] == "candidate"
    assert gen["final_activation_gate"]["status"] == "candidate"
    for gate in ("source_monitor_gate", "evidence_trail_gate", "qa_critic_gate",
                 "legal_language_gate", "product_manager_gate", "code_architect_gate"):
        assert gen[gate]["status"] == "hold"
    assert gen["proposed_source_id"].startswith("candidate-www-sca-gov-ae-")
    assert gen["regulator"] == "SCA"


def test_generate_source_candidate_empty_path_uses_source_slug():
    gen = sd.generate_source_candidate({"candidate_url": "https://gov.example/"})
    assert gen["proposed_source_id"].endswith("-source")


# ── classify_network_response rejection branches ─────────────────────────────────

def test_classify_network_response_off_domain_rejected():
    out = sd.classify_network_response(
        "https://cdn.other.example/data.json",
        status_code=200, content_type="application/json",
        body_preview="{}", page_url="https://gov.example/page",
    )
    assert out["candidate_status"] == "rejected"
    assert out["failure_reason"] == "off-domain network endpoint"


def test_classify_network_response_http_error_rejected():
    out = sd.classify_network_response(
        "/data.json", status_code=500, content_type="application/json",
        body_preview="{}", page_url="https://gov.example/page",
    )
    assert out["candidate_status"] == "rejected"
    assert out["failure_reason"] == "HTTP 500"


def test_classify_network_response_unknown_content_type_rejected():
    out = sd.classify_network_response(
        "/page2", status_code=200, content_type="text/html",
        body_preview="<html>", page_url="https://gov.example/page",
    )
    # preview starts with "<" → classified as feed_or_xml, so this is accepted
    assert out["source_type"] == "feed_or_xml"

    out2 = sd.classify_network_response(
        "/thing", status_code=200, content_type="text/plain",
        body_preview="plain text", page_url="https://gov.example/page",
    )
    assert out2["source_type"] == "unknown"
    assert out2["candidate_status"] == "rejected"
    assert out2["failure_reason"] == "unsupported network content type"


# ── score_endpoint_candidate remediation / low-confidence branch ─────────────────

def test_score_endpoint_candidate_same_domain_no_signal_floor_confidence():
    out = sd.score_endpoint_candidate(
        {"candidate_url": "https://gov.example/misc-page", "title": "Misc",
         "source_type": "html_page", "signals": []},
        official_domain="gov.example",
    )
    # same-domain (+25) over base 20 with no regulatory signal / no type bonus
    # yields exactly the 45 floor → candidate (never activated).
    assert out["confidence"] == 45
    assert out["candidate_status"] == "candidate"
    assert out["next_action"] == "run_no_save_test"
    assert out["official_status"] == "official_domain"


def test_score_endpoint_candidate_off_domain_rejected():
    out = sd.score_endpoint_candidate(
        {"candidate_url": "https://cdn.other.example/x", "title": "X",
         "source_type": "listing", "signals": ["regulation"]},
        official_domain="gov.example",
    )
    assert out["candidate_status"] == "rejected"
    assert out["confidence"] >= 0
    assert "not on the official source domain" in out["failure_reason"]


# ── discover_source_capabilities end-to-end (mocked I/O) ─────────────────────────

def _patch_layer1(monkeypatch, *, safe=True, resp=None, low=False, pw_html="",
                  extract=None):
    monkeypatch.setattr(sd, "validate_public_url", lambda u: (safe, "ok" if safe else "unsafe"))
    monkeypatch.setattr(sd, "_safe_get", lambda *a, **k: resp)
    monkeypatch.setattr(sd, "is_low_content_html", lambda h: low)
    monkeypatch.setattr(sd, "_fetch_via_playwright", lambda u: pw_html)
    monkeypatch.setattr(sd, "extract_best_text",
                        lambda html, url: extract or {"extracted_chars": 0, "method": "none",
                                                      "quality": "failed", "candidates": []})


def test_capabilities_unsafe_url_returns_empty(monkeypatch):
    _patch_layer1(monkeypatch, safe=False)
    res = sd.discover_source_capabilities("http://169.254.169.254/")
    assert res["verdict"] == "cannot_monitor"
    assert res["safe_url"] is False
    assert "safety validation" in res["reason"]


def test_capabilities_static_html_good(monkeypatch):
    html = "<html><body>" + ("Regulation text. " * 200) + "</body></html>"
    resp = _Resp(200, html)
    _patch_layer1(monkeypatch, resp=resp, low=False,
                  extract={"extracted_chars": 5000, "method": "readability", "candidates": []})
    res = sd.discover_source_capabilities("https://cbuae.gov.ae/en/regulations")
    assert res["verdict"] == "can_monitor"
    assert res["recommended_mode"] == "html"
    assert res["capabilities"]["html_monitoring"] is True
    assert res["page"]["used_playwright"] is False
    assert res["client_verdict"] in {"ready", "limited"}


def test_capabilities_js_html_when_tier1_low(monkeypatch):
    thin = "<html></html>"
    resp = _Resp(200, thin)
    rich = "<html><body>" + ("x " * 5000) + "</body></html>"
    _patch_layer1(monkeypatch, resp=resp, low=True, pw_html=rich,
                  extract={"extracted_chars": 6000, "method": "readability", "candidates": []})
    res = sd.discover_source_capabilities("https://dfsa.ae/rulebook")
    assert res["recommended_mode"] == "js_html"
    assert res["capabilities"]["js_html_monitoring"] is True
    assert res["page"]["used_playwright"] is True


def test_capabilities_needs_adapter_when_reachable_but_thin(monkeypatch):
    thin = "<html><body>tiny</body></html>"
    resp = _Resp(200, thin)
    _patch_layer1(monkeypatch, resp=resp, low=True, pw_html="",
                  extract={"extracted_chars": 40, "method": "none", "candidates": []})
    res = sd.discover_source_capabilities("https://x.gov.ae/page")
    assert res["verdict"] == "needs_adapter"
    assert res["recommended_mode"] == "adapter"
    assert res["capabilities"]["needs_adapter"] is True
    assert res["client_verdict"] == "custom_adapter"


def test_capabilities_unavailable_when_fetch_none(monkeypatch):
    _patch_layer1(monkeypatch, resp=None, low=True, pw_html="")
    res = sd.discover_source_capabilities("https://down.gov.ae/")
    assert res["verdict"] == "cannot_monitor"
    assert res["recommended_mode"] == "unavailable"
    assert res["client_verdict"] == "unavailable"


def test_capabilities_http_error_treated_as_no_html(monkeypatch):
    resp = _Resp(403, "")  # resp.ok False → raw_html stays None
    _patch_layer1(monkeypatch, resp=resp, low=True, pw_html="")
    res = sd.discover_source_capabilities("https://waf.gov.ae/")
    assert res["verdict"] == "cannot_monitor"
    assert res["page"]["http_status"] == 403


def test_capabilities_deep_feed_wins(monkeypatch):
    html = "<html><body>" + ("Regulation. " * 200) + "</body></html>"
    resp = _Resp(200, html)
    _patch_layer1(monkeypatch, resp=resp, low=False,
                  extract={"extracted_chars": 5000, "method": "readability", "candidates": []})
    # Force a discovered feed via Layer 3
    monkeypatch.setattr(sd, "_discover_feeds",
                        lambda base: [{"url": "https://cbuae.gov.ae/rss.xml", "status": "ok", "items_found": 12}])
    monkeypatch.setattr(sd, "_discover_sitemaps", lambda base: [])
    res = sd.discover_source_capabilities("https://cbuae.gov.ae/en/regulations", deep=True)
    assert res["recommended_mode"] == "feed"
    assert res["capabilities"]["feed_monitoring"] is True
    assert "RSS/Atom feed found" in res["reason"]


def test_capabilities_deep_sitemap_mode(monkeypatch):
    # thin HTML so html/js not good, but a sitemap is found → sitemap mode
    thin = "<html><body>x</body></html>"
    resp = _Resp(200, thin)
    _patch_layer1(monkeypatch, resp=resp, low=True, pw_html="",
                  extract={"extracted_chars": 30, "method": "none", "candidates": []})
    monkeypatch.setattr(sd, "_discover_feeds", lambda base: [])
    monkeypatch.setattr(sd, "_discover_sitemaps",
                        lambda base: [{"url": "https://x.gov.ae/sitemap.xml", "status": "ok", "links_found": 42}])
    res = sd.discover_source_capabilities("https://x.gov.ae/", deep=True)
    assert res["recommended_mode"] == "sitemap"
    assert res["capabilities"]["sitemap_monitoring"] is True


# ── _discover_feeds / _discover_sitemaps with mocked _probe ──────────────────────

def test_discover_feeds_accepts_valid_rss(monkeypatch):
    rss = "<?xml version='1.0'?><rss><channel><item>a</item><item>b</item></channel></rss>"

    def fake_probe(url):
        if url.endswith("/rss"):
            return 200, "application/rss+xml", rss
        return 404, "", None

    monkeypatch.setattr(sd, "_probe", fake_probe)
    feeds = sd._discover_feeds("https://gov.example/en/news")
    assert feeds and feeds[0]["url"] == "https://gov.example/rss"
    assert feeds[0]["items_found"] == 2


def test_discover_feeds_rejects_non_feed_content(monkeypatch):
    monkeypatch.setattr(sd, "_probe", lambda url: (200, "text/html", "<html>no feed here</html>"))
    assert sd._discover_feeds("https://gov.example/") == []


def test_discover_sitemaps_from_paths_and_robots(monkeypatch):
    sitemap = "<urlset><url><loc>https://gov.example/a</loc></url></urlset>"

    def fake_probe(url):
        if url.endswith("/robots.txt"):
            return 200, "text/plain", "Sitemap: https://gov.example/extra-sitemap.xml"
        if url.endswith(".xml"):
            return 200, "application/xml", sitemap
        return 404, "", None

    monkeypatch.setattr(sd, "_probe", fake_probe)
    monkeypatch.setattr(sd, "validate_public_url", lambda u: (True, "ok"))
    out = sd._discover_sitemaps("https://gov.example/en")
    urls = [s["url"] for s in out]
    assert "https://gov.example/sitemap.xml" in urls
    assert any(s["links_found"] == 1 for s in out)


def test_discover_sitemaps_ignores_non_sitemap_body(monkeypatch):
    monkeypatch.setattr(sd, "_probe", lambda url: (200, "text/html", "<html>not a sitemap</html>"))
    monkeypatch.setattr(sd, "validate_public_url", lambda u: (True, "ok"))
    assert sd._discover_sitemaps("https://gov.example/") == []


# ── _sample_documents with mocked fetch + extractors ─────────────────────────────

def test_sample_documents_extracts_pdf_and_counts(monkeypatch):
    monkeypatch.setattr(sd, "validate_public_url", lambda u: (True, "ok"))
    monkeypatch.setattr(sd, "_safe_get", lambda *a, **k: _Resp(200, body=b"%PDF-bytes"))
    import app.document_extractors as de
    monkeypatch.setattr(de, "extract_pdf_text", lambda buf: "A" * 500)
    monkeypatch.setattr(de, "extract_docx_text", lambda buf: "")
    monkeypatch.setattr(de, "extract_xlsx_text", lambda buf: "")

    samples, extractable = sd._sample_documents(["https://gov.example/a.pdf"])
    assert extractable == 1
    assert samples[0]["status"] == "ok"
    assert samples[0]["chars"] == 500


def test_sample_documents_marks_failed_when_fetch_fails(monkeypatch):
    monkeypatch.setattr(sd, "validate_public_url", lambda u: (True, "ok"))
    monkeypatch.setattr(sd, "_safe_get", lambda *a, **k: _Resp(500, body=b""))
    samples, extractable = sd._sample_documents(["https://gov.example/a.pdf"])
    assert extractable == 0
    assert samples[0]["status"] == "failed"


def test_sample_documents_skips_unsafe_urls(monkeypatch):
    monkeypatch.setattr(sd, "validate_public_url", lambda u: (False, "unsafe"))
    samples, extractable = sd._sample_documents(["http://169.254.169.254/x.pdf"])
    assert samples == []
    assert extractable == 0


def test_sample_documents_low_char_not_counted(monkeypatch):
    monkeypatch.setattr(sd, "validate_public_url", lambda u: (True, "ok"))
    monkeypatch.setattr(sd, "_safe_get", lambda *a, **k: _Resp(200, body=b"docx-bytes"))
    import app.document_extractors as de
    monkeypatch.setattr(de, "extract_docx_text", lambda buf: "tiny")  # < 100 chars
    samples, extractable = sd._sample_documents(["https://gov.example/a.docx"])
    assert extractable == 0
    assert samples[0]["status"] == "ok"
    assert samples[0]["chars"] == 4
