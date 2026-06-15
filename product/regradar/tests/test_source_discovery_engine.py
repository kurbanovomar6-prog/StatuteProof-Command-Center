"""
Tests for the structured Source Discovery Engine.

These tests use local fixtures only. They do not make live network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.source_discovery import (
    build_discovery_report_from_html,
    classify_network_response,
    discover_feed_links_from_html,
    discover_same_domain_links,
    extract_document_links_from_html,
    generate_source_candidate,
    parse_feed_xml,
    parse_robots_sitemaps,
    parse_sitemap_xml,
    score_endpoint_candidate,
)


def test_parse_robots_extracts_sitemap_lines():
    robots = """
    User-agent: *
    Disallow: /admin
    Sitemap: https://www.sca.gov.ae/sitemap.xml
    Sitemap: https://www.sca.gov.ae/en/sitemap-index.xml
    """

    result = parse_robots_sitemaps(robots)

    assert result["status"] == "parsed"
    assert result["sitemap_urls"] == [
        "https://www.sca.gov.ae/sitemap.xml",
        "https://www.sca.gov.ae/en/sitemap-index.xml",
    ]


def test_parse_sitemap_index_and_urlset():
    index_xml = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://example.gov/sitemap-regulations.xml</loc><lastmod>2026-06-01</lastmod></sitemap>
    </sitemapindex>
    """
    urlset_xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://example.gov/en/regulations/aml-cft</loc>
        <lastmod>2026-06-10</lastmod>
        <changefreq>weekly</changefreq>
      </url>
    </urlset>
    """

    index = parse_sitemap_xml(index_xml, "https://example.gov/sitemap.xml")
    urlset = parse_sitemap_xml(urlset_xml, "https://example.gov/sitemap-regulations.xml")

    assert index["type"] == "sitemapindex"
    assert index["entries"][0]["loc"] == "https://example.gov/sitemap-regulations.xml"
    assert urlset["type"] == "urlset"
    assert urlset["entries"][0]["loc"].endswith("/aml-cft")
    assert urlset["entries"][0]["changefreq"] == "weekly"


def test_feed_discovery_and_parsing_from_html():
    html = """
    <html><head>
      <link rel="alternate" type="application/rss+xml" title="Regulatory updates" href="/rss.xml" />
      <link rel="alternate" type="application/atom+xml" title="Consultations" href="https://example.gov/atom.xml" />
    </head><body></body></html>
    """
    rss = """
    <rss><channel>
      <item><title>AML Guidance Update</title><link>https://example.gov/aml</link><pubDate>Mon, 15 Jun 2026 00:00:00 GMT</pubDate></item>
    </channel></rss>
    """

    feeds = discover_feed_links_from_html(html, "https://example.gov/en/regulations")
    parsed = parse_feed_xml(rss, "https://example.gov/rss.xml")

    assert len(feeds) == 2
    assert feeds[0]["url"] == "https://example.gov/rss.xml"
    assert parsed["items"][0]["title"] == "AML Guidance Update"
    assert parsed["items"][0]["url"] == "https://example.gov/aml"


def test_document_links_and_same_domain_candidates_are_scored_safely():
    html = """
    <html><body>
      <a href="/media/aml-guidance.pdf">AML/CFT Guidance PDF</a>
      <a href="/en/regulations/payment-services">Payment Services Regulation</a>
      <a href="https://other.example/news">Off domain</a>
      <a href="/login">Login</a>
    </body></html>
    """

    docs = extract_document_links_from_html(html, "https://cbuae.gov.ae/en/regulations")
    links = discover_same_domain_links(html, "https://cbuae.gov.ae/en/regulations", max_links=10)

    assert docs[0]["url"] == "https://cbuae.gov.ae/media/aml-guidance.pdf"
    assert docs[0]["source_type"] == "pdf_document"
    assert any(link["url"].endswith("/en/regulations/payment-services") for link in links["accepted"])
    assert any("off-domain" in item["reason"] for item in links["rejected"])
    assert any("private/login" in item["reason"] for item in links["rejected"])


def test_off_domain_document_linked_from_official_page_is_not_active_by_default():
    candidate = score_endpoint_candidate(
        {
            "candidate_url": "https://official-storage.example/files/aml-notice.pdf",
            "title": "AML Notice",
            "content_type": "application/pdf",
            "discovery_method": "document_link",
            "linked_from_url": "https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance",
            "signals": ["publication", "guidance"],
            "source_type": "pdf_document",
        },
        official_domain="www.dfsa.ae",
    )

    assert candidate["official_status"] == "officially_linked"
    assert candidate["access_status"] == "manual_review_required"
    assert candidate["candidate_status"] == "candidate"
    assert candidate["next_action"] == "manual_review"
    assert candidate["adapter_family"] == "pdf_document"


def test_network_response_classification_for_public_json_and_pdf():
    json_candidate = classify_network_response(
        "https://www.sca.gov.ae/api/regulations",
        status_code=200,
        content_type="application/json",
        body_preview='{"items":[{"title":"Decision"}]}',
        page_url="https://www.sca.gov.ae/en/regulations",
    )
    pdf_candidate = classify_network_response(
        "https://www.vara.ae/rulebook.pdf",
        status_code=200,
        content_type="application/pdf",
        body_preview="",
        page_url="https://www.vara.ae/rulebooks",
    )
    private_candidate = classify_network_response(
        "https://www.sca.gov.ae/api/auth/token",
        status_code=200,
        content_type="application/json",
        body_preview='{"token":"x"}',
        page_url="https://www.sca.gov.ae/en/regulations",
    )

    assert json_candidate["source_type"] == "public_json_api"
    assert json_candidate["adapter_family"] == "public_json_api"
    assert pdf_candidate["source_type"] == "pdf_document"
    assert private_candidate["candidate_status"] == "rejected"


def test_candidate_scoring_recommends_adapter_and_never_activates():
    candidate = score_endpoint_candidate(
        {
            "candidate_url": "https://www.sca.gov.ae/en/regulations/regulations",
            "title": "SCA Regulations",
            "content_type": "text/html",
            "discovery_method": "sitemap",
            "signals": ["regulation", "listing", "official_domain"],
        },
        official_domain="www.sca.gov.ae",
    )

    generated = generate_source_candidate(candidate, regulator="SCA", jurisdiction="UAE Federal")

    assert candidate["adapter_family"] in {"listing", "sca_listing"}
    assert candidate["confidence"] >= 60
    assert generated["current_state"] == "candidate"
    assert generated["final_activation_gate"]["status"] == "candidate"
    assert generated["evidence_trail_gate"]["status"] == "hold"


def test_build_discovery_report_from_html_contains_required_contract_fields():
    html = """
    <html><head>
      <title>Central Bank Regulations</title>
      <link rel="canonical" href="https://www.centralbank.ae/en/regulations/" />
      <meta name="description" content="Regulations and guidance" />
      <link rel="alternate" type="application/rss+xml" href="/rss.xml" />
    </head>
    <body>
      <main>
        <a href="/en/regulations/payment-services">Retail Payment Services Regulation</a>
        <a href="/media/aml-guidance.pdf">AML Guidance PDF</a>
        <table><tr><th>Name</th></tr><tr><td>Licensed Firm</td></tr></table>
      </main>
    </body></html>
    """

    report = build_discovery_report_from_html(
        "https://www.centralbank.ae/en/regulations/",
        html,
        robots_text="Sitemap: https://www.centralbank.ae/sitemap.xml",
    )

    assert report["input_url"] == "https://www.centralbank.ae/en/regulations/"
    assert report["official_domain"] == "www.centralbank.ae"
    assert report["robots_status"] == "parsed"
    assert report["feed_urls"]
    assert report["pdf_links"]
    assert report["table_candidates"]
    assert report["recommended_activation_paths"]
    assert report["recommended_activation_paths"][0]["next_action"] != "activate_monitoring"


def test_sca_discovery_filters_generic_links_and_normalizes_doubled_paths():
    html = """
    <html><head><title>SCA Regulations</title></head>
    <body><main>
      <a href="en/about-us">About Us</a>
      <a href="en/services">Services</a>
      <a href="en/regulations/anti-money-laundering-and-terrorist-financing">AML/CFT</a>
      <a href="en/regulations/circulars-rules-and-procedures">Circulars, Rules and procedures</a>
      <a href="en/regulations/en/regulations/market-rules-approved-by-sca">Approved Regulations for Capital Market Institutions</a>
      <a href="en/open-data/companies">Registered Companies</a>
    </main></body></html>
    """

    report = build_discovery_report_from_html(
        "https://www.sca.gov.ae/en/regulations/regulations",
        html,
        max_links=20,
    )
    urls = [item["candidate_url"] for item in report["recommended_activation_paths"]]
    titles = [item.get("title", "") for item in report["recommended_activation_paths"]]

    assert not any("/about-us" in url for url in urls)
    assert not any("/services" in url for url in urls)
    assert "AML/CFT" in titles
    assert any(url.endswith("/en/regulations/circulars-rules-and-procedures") for url in urls)
    assert any(url.endswith("/en/regulations/market-rules-approved-by-sca") for url in urls)
    assert not any("/en/regulations/en/regulations/" in url for url in urls)
    assert any(item["source_type"] == "register" for item in report["recommended_activation_paths"])


def test_cbuae_403_discovery_maps_to_access_block_remediation():
    class Response:
        ok = False
        status_code = 403
        text = ""
        url = "https://www.centralbank.ae/en/our-operations/regulations/"

    def fake_get(url, **kwargs):
        return Response()

    from unittest.mock import patch

    with patch("app.source_discovery._req.get", side_effect=fake_get):
        from app.source_discovery import discover_source

        report = discover_source(
            "https://www.centralbank.ae/en/our-operations/regulations/",
            include_sitemap=False,
            include_feeds=False,
            include_documents=False,
            max_links=10,
        )

    assert report["access_status"] == "blocked"
    assert report["failure_code"] in {"ACCESS_BLOCKED", "LIKELY_WAF_403"}
    assert "official alternate" in report["remediation_hint"].lower()
    assert report["recommended_activation_paths"] == []
