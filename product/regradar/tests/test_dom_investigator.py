"""
Tests for Auto DOM Investigator.

These tests use local HTML fixtures only. They do not make live network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.dom_investigator import investigate_html


def test_dom_investigator_detects_article_main_content():
    html = """
    <html><head><title>Official AML Guidance</title></head>
      <body>
        <nav>Home Search Contact</nav>
        <main>
          <article>
            <h1>AML Guidance for Regulated Firms</h1>
            <p>Licensed firms must review anti-money laundering controls, sanctions
            screening, governance, training, reporting processes, and escalation
            procedures as part of their compliance framework.</p>
          </article>
        </main>
      </body>
    </html>
    """

    result = investigate_html(html, url="https://example.gov.ae/aml-guidance")

    assert result["detected_page_type"] == "article"
    assert result["recommended_adapter_family"] == "static_html"
    assert result["content_selector"] in {"article", "main"}
    assert result["selector_confidence"] >= 70
    assert result["nav_shell_risk"] in {"low", "medium"}
    assert result["can_no_save_test"] is True


def test_dom_investigator_detects_listing_rows():
    html = """
    <html><body>
      <main data-icms-list>
        <div class="card"><a href="/regulations/decision-1">Decision No. 1 of 2026</a><time>2026</time></div>
        <div class="card"><a href="/regulations/decision-2">Decision No. 2 of 2026</a><time>2026</time></div>
        <div class="card"><a href="/regulations/decision-3">Decision No. 3 of 2026</a><time>2026</time></div>
      </main>
    </body></html>
    """

    result = investigate_html(html, url="https://www.sca.gov.ae/en/regulations/regulations")

    assert result["detected_page_type"] == "listing"
    assert result["recommended_adapter_family"] == "listing"
    assert result["item_selector"]
    assert "[data-icms-list]" in result["fallback_selectors"]


def test_dom_investigator_detects_table_content():
    html = """
    <html><body><main>
      <table><tr><th>Name</th><th>Status</th></tr><tr><td>Alpha</td><td>Active</td></tr></table>
    </main></body></html>
    """

    result = investigate_html(html, url="https://example.gov.ae/register")

    assert result["detected_page_type"] == "table"
    assert result["recommended_adapter_family"] == "table"
    assert result["content_selector"] == "table"


def test_dom_investigator_detects_pdf_links():
    html = """
    <html><body><main>
      <a href="/media/rulebook.pdf">Company Rulebook PDF</a>
      <a href="/media/aml-cft.pdf">AML/CFT Rulebook PDF</a>
    </main></body></html>
    """

    result = investigate_html(html, url="https://www.vara.ae/rulebooks/")

    assert result["detected_page_type"] == "pdf_listing"
    assert result["recommended_adapter_family"] == "pdf_listing"
    assert result["can_no_save_test"] is True


def test_dom_investigator_flags_nav_shell_and_shallow_content():
    html = """
    <html><body>
      <nav>Home About Services Search Contact Login Privacy Accessibility</nav>
      <main><a href="/about">About</a><a href="/contact">Contact</a></main>
    </body></html>
    """

    result = investigate_html(html, url="https://example.gov.ae/not-found")

    assert result["nav_shell_risk"] == "high"
    assert result["failure_reason"]
    assert result["can_save_evidence"] is False


def test_dom_investigator_detects_dfsa_summary_content():
    html = """
    <html><head><title>AML, CTF and Sanctions Compliance Summary</title></head>
      <body>
        <header>About us Search Contact</header>
        <section class="summary">
          <h1>AML, CTF and Sanctions Compliance</h1>
          <p>The DFSA publishes financial crime prevention notices, MLRO letters,
          sanctions compliance material, and related guidance for authorised firms.</p>
          <a href="/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters">
            Financial Crime Prevention Notices and MLRO Letters
          </a>
        </section>
      </body>
    </html>
    """

    result = investigate_html(
        html,
        url="https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/summary",
    )

    assert result["detected_page_type"] in {"article", "listing"}
    assert result["content_selector"] in {".summary", "section.summary"}
    assert result["recommended_adapter_name"] in {"static_html", "dfsa_notice_listing", "listing"}
    assert result["can_no_save_test"] is True
    assert result["source_health_risk"] != "high"
