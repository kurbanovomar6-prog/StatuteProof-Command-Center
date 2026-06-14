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
