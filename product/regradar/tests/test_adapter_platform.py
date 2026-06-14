"""
Tests for the Source Lab adapter platform.

These tests use local HTML fixtures only. They do not make live network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.source_certification import EvidenceLevel
from app.source_intake import SourceIntakeStatus, run_source_intake
from app.adapters.adapter_platform import extract_with_adapter


_SCA_LISTING_HTML = """
<html>
  <body>
    <nav>Home About Services Search Contact</nav>
    <main data-icms-list>
      <form class="search">Search by keyword</form>
      <div class="regulation-card">
        <a class="title" href="/en/regulations/rulebook-2026">Capital Market Rulebook Update</a>
        <span class="date">14 June 2026</span>
        <span class="category">Regulation</span>
      </div>
      <div class="regulation-card">
        <a class="title" href="/en/regulations/aml-cft-guidance">AML/CFT Guidance for Licensed Firms</a>
        <span class="date">12 June 2026</span>
        <span class="category">AML/CFT</span>
      </div>
    </main>
    <footer>Privacy Accessibility Social links</footer>
  </body>
</html>
"""


_TABLE_HTML = """
<html>
  <body>
    <main>
      <table id="register">
        <thead>
          <tr><th>Entity</th><th>Status</th><th>Licence</th></tr>
        </thead>
        <tbody>
          <tr><td>Beta Markets LLC</td><td>Active</td><td>Broker</td></tr>
          <tr><td>Alpha Payments LLC</td><td>Active</td><td>Payment services</td></tr>
        </tbody>
      </table>
    </main>
  </body>
</html>
"""


_ADGM_CUSTOM_HTML = """
<html>
  <body>
    <adgm-page>
      <span>
        <h1>Financial and Cyber Crime Prevention</h1>
        <p>ADGM and the FSRA publish financial crime prevention material for firms operating
        in ADGM. The material supports anti-money laundering, counter-terrorist financing,
        sanctions compliance, suspicious activity reporting, governance, systems and controls,
        and staff training review by regulated financial services entities.</p>
        <p>Firms should review official guidance, notices, risk updates, and public regulatory
        material before changing internal policies. Human compliance review remains required.</p>
      </span>
    </adgm-page>
  </body>
</html>
"""


def test_listing_adapter_extracts_items_and_ignores_chrome():
    result = extract_with_adapter(
        _SCA_LISTING_HTML,
        url="https://www.sca.gov.ae/en/regulations/regulations",
        adapter_family="listing",
        adapter_config={
            "container_selector": "[data-icms-list]",
            "item_selector": ".regulation-card",
            "title_selector": ".title",
            "date_selector": ".date",
            "url_selector": "a",
            "category_selector": ".category",
            "exclude_selectors": ["nav", "footer", ".search"],
        },
    )

    assert result.adapter_family == "listing"
    assert result.item_count == 2
    assert "Capital Market Rulebook Update" in result.text
    assert "AML/CFT Guidance for Licensed Firms" in result.text
    assert "Privacy Accessibility" not in result.text
    assert "Search by keyword" not in result.text
    assert all(item.get("row_hash") for item in result.items)


def test_listing_adapter_falls_back_when_configured_container_missing():
    html = """
    <html><body>
      <main>
        <a href="/regulations/decision-11">Decision 11 of 2026 concerning AML controls</a>
        <a href="/regulations/decision-13">Decision 13 of 2026 concerning market conduct</a>
      </main>
    </body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://www.sca.gov.ae/en/regulations/regulations",
        adapter_family="listing",
        adapter_config={
            "container_selector": "[data-icms-list]",
            "item_selector": "a[href]",
            "title_selector": "a",
            "url_selector": "a[href]",
        },
    )

    assert result.item_count == 2
    assert "Decision 11 of 2026" in result.text
    assert result.warnings


def test_table_adapter_extracts_and_stable_sorts_rows():
    result = extract_with_adapter(
        _TABLE_HTML,
        url="https://www.example.gov.ae/register",
        adapter_family="table",
        adapter_config={
            "table_selector": "#register",
            "sort_rows": True,
        },
    )

    assert result.adapter_family == "table"
    assert result.item_count == 2
    assert result.text.index("Alpha Payments LLC") < result.text.index("Beta Markets LLC")
    assert "Entity | Status | Licence" in result.text


def test_custom_element_adapter_extracts_adgm_like_text():
    result = extract_with_adapter(
        _ADGM_CUSTOM_HTML,
        url="https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention",
        adapter_family="custom_element",
        adapter_config={"content_selector": "adgm-page > span"},
    )

    assert result.adapter_family == "custom_element"
    assert "Financial and Cyber Crime Prevention" in result.text
    assert "anti-money laundering" in result.text
    assert result.source_health_risk in {"low", "medium", "unknown"}


def test_source_intake_explicit_adapter_exposes_metadata_and_stays_preview_only():
    body = "<p>" + ("Regulated firms must review AML controls and sanctions screening. " * 40) + "</p>"
    html = f"<html><body><adgm-page><span>{body}</span></adgm-page></body></html>"
    source = {
        "source_id": "AE-test-adapter",
        "name": "Adapter Test",
        "url": "https://www.adgm.com/official-source",
        "adapter_family": "custom_element",
        "adapter_config": {"content_selector": "adgm-page > span"},
        "expected_min_length": 500,
    }

    with patch("app.scraper.fetch_page_with_config", return_value=html):
        result = run_source_intake(source, write_evidence=False)

    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["adapter_used"] is True
    assert result["adapter_family"] == "custom_element"
    assert result["extraction_strategy"] == "adapter:custom_element"
    assert result["evidence_written"] is False
    assert result["evidence_level"] == EvidenceLevel.PREVIEW_ONLY
    assert result["can_activate_monitoring"] is False


def test_sca_listing_adapter_extracts_item_title_link_and_date():
    html = """
    <html><body>
      <header>Capital Market Authority Services Login Search</header>
      <main>
        <section class="icms-list">
          <article class="decision">
            <a href="/en/regulations/decision-11-2026">The Chairman Decision No. (11/Chairman) of 2026 Concerning AML Controls</a>
            <time>14 June 2026</time>
          </article>
          <article class="decision">
            <a href="/en/regulations/decision-13-2026">The Chairman Decision No. (13/Chairman) of 2026 Concerning Market Conduct</a>
            <time>11 June 2026</time>
          </article>
        </section>
      </main>
      <footer>Privacy Accessibility Search Services</footer>
    </body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://www.sca.gov.ae/en/regulations/regulations",
        adapter_family="sca_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "sca_listing"
    assert result.item_count == 2
    assert "Decision No. (11/Chairman) of 2026" in result.text
    assert "14 June 2026" in result.text
    assert "Privacy Accessibility" not in result.text


def test_dfsa_rulebook_adapter_extracts_module_titles_and_links():
    html = """
    <html><body><article>
      <h1>Rulebook Modules</h1>
      <a href="/rulebook/aml">Anti-Money Laundering, Counter-Terrorist Financing and Sanctions Module (AML)</a>
      <a href="/rulebook/gen">General Module (GEN)</a>
      <a href="/rulebook/cob">Conduct of Business Module (COB)</a>
    </article></body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules",
        adapter_family="dfsa_rulebook",
        adapter_config={"container_selector": "article"},
    )

    assert result.adapter_name == "dfsa_rulebook"
    assert result.item_count == 3
    assert "Anti-Money Laundering" in result.text
    assert "https://dfsaen.thomsonreuters.com/rulebook/aml" in result.text


def test_cbuae_document_listing_adapter_extracts_document_links():
    html = """
    <html><body><main>
      <div class="card"><a href="/media/regulations/aml-guidance.pdf">AML/CFT Guidance for Licensed Financial Institutions</a><span>2026</span></div>
      <div class="card"><a href="/media/regulations/payment-services.pdf">Retail Payment Services Regulation</a><span>2025</span></div>
      <nav><a href="/search">Search</a></nav>
    </main></body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://www.centralbank.ae/en/regulations/",
        adapter_family="cbuae_document_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "cbuae_document_listing"
    assert result.item_count == 2
    assert "AML/CFT Guidance" in result.text
    assert "payment-services.pdf" in result.text


def test_fiu_eocn_document_listing_adapter_extracts_publication_links():
    html = """
    <html><body><main>
      <a href="/en/publications/typologies-report.pdf">UAE FIU Typologies Report 2026</a>
      <a href="/en/publications/goaml-guide.pdf">goAML Registration Guidance</a>
      <a href="/contact">Contact us</a>
    </main></body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://www.uaefiu.gov.ae/en/Publications/",
        adapter_family="fiu_eocn_document_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "fiu_eocn_document_listing"
    assert result.item_count == 2
    assert "Typologies Report" in result.text
    assert "goAML Registration Guidance" in result.text


def test_vara_pdf_listing_adapter_extracts_rulebook_pdf_links():
    html = """
    <html><body><main>
      <a href="/media/rulebooks/company-rulebook.pdf">Company Rulebook</a>
      <a href="/media/rulebooks/aml-cft-rulebook.pdf">AML/CFT Rulebook</a>
      <a href="/en/contact">Contact VARA</a>
    </main></body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://www.vara.ae/en/regulatory-framework/rulebooks/",
        adapter_family="vara_pdf_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "vara_pdf_listing"
    assert result.item_count == 2
    assert "Company Rulebook" in result.text
    assert "aml-cft-rulebook.pdf" in result.text
