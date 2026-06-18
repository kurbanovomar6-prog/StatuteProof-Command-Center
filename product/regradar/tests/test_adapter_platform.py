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
            "include_headers": True,
        },
    )

    assert result.adapter_family == "table"
    assert result.item_count == 2
    assert result.text.index("Alpha Payments LLC") < result.text.index("Beta Markets LLC")
    assert "Entity | Status | Licence" in result.text


def test_table_adapter_omits_headers_by_default_for_stable_monitoring_hash():
    result = extract_with_adapter(
        _TABLE_HTML,
        url="https://www.example.gov.ae/register",
        adapter_family="table",
        adapter_config={"table_selector": "#register"},
    )

    assert result.adapter_family == "table"
    assert result.item_count == 2
    assert "Entity | Status | Licence" not in result.text
    assert "Beta Markets LLC | Active | Broker" in result.text
    assert result.items[0]["Entity"] == "Beta Markets LLC"


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


def test_sca_listing_adapter_filters_noise_before_item_limit():
    noisy_links = "\n".join(
        f'<a href="/en/services/noise-{idx}">Service link {idx}</a>'
        for idx in range(140)
    )
    html = f"""
    <html><body>
      <header>Capital Market Authority Services Login Search</header>
      <section class="layout">
        {noisy_links}
        <a href="/en/regulations/circular-annual-general-assembly-2024">
          Circular on the Annual General Assembly Meetings of Public Joint-Stock Companies for 2024
        </a>
        <a href="/en/regulations/virtual-assets-guidelines">
          Guidelines Regulation of Virtual Assets and Virtual Assets Services Providers
        </a>
        <a href="/en/regulations/passporting-rules">Passporting Rules</a>
        <a href="/en/about">About the Authority</a>
        <a href="/en/services">Services</a>
      </section>
      <footer>Privacy Accessibility Search Services</footer>
    </body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures",
        adapter_family="sca_listing",
        adapter_config={
            "container_selector": "main",
            "item_selector": "article, li, tr, .card, .item, a[href]",
            "title_selector": "a, h2, h3, h4",
            "url_selector": "a[href]",
            "max_items": 20,
        },
    )

    assert result.adapter_name == "sca_listing"
    assert result.item_count == 3
    assert "Annual General Assembly" in result.text
    assert "Virtual Assets" in result.text
    assert "Passporting Rules" in result.text
    assert "Service link 139" not in result.text
    assert "About the Authority" not in result.text


def test_sca_listing_adapter_extracts_aegov_cards():
    html = """
    <html><body>
      <main class="main">
        <section>
          <div class="grid">
            <div class="aegov-card card-bordered card-service" role="group" aria-labelledby="general-landing-item-14529">
              <div><h5 id="general-landing-item-14529">Passporting Rules</h5></div>
              <div><a href="/assets/download/19029408/passporting-rules-en.aspx" title="View Details">View Details</a></div>
            </div>
            <div class="aegov-card card-bordered card-service" role="group" aria-labelledby="general-landing-item-14746">
              <div><h5 id="general-landing-item-14746">Circular on the Annual General Assembly Meetings of Public Joint-Stock Companies for 2024</h5></div>
              <div><a href="/assets/54c01814/circular-on-the-annual-general-assembly-meetings-of-public-joint-stock-companies-for-2024-en.aspx" title="View Details">View Details</a></div>
            </div>
          </div>
        </section>
      </main>
    </body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures",
        adapter_family="sca_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "sca_listing"
    assert result.item_count == 2
    assert "Passporting Rules" in result.text
    assert "public-joint-stock-companies-for-2024-en.aspx" in result.text
    assert "View Details" not in result.text


def test_sca_listing_adapter_removes_invalid_javascript_detail_urls():
    html = """
    <html><body>
      <main>
        <article class="decision">
          <a href="javascipt:;">Administrative Decision No. (123 /R.T) of 2017 Concerning Regulatory Controls</a>
          <time>2017</time>
        </article>
        <article class="decision">
          <a href="/en/regulations/decision-46-2016">Administrative Decision No. (46 / R.T) of 2016 concerning Grievances</a>
          <time>2016</time>
        </article>
      </main>
    </body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://www.sca.gov.ae/en/regulations/regulations-listing",
        adapter_family="sca_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "sca_listing"
    assert result.item_count == 2
    assert "Administrative Decision No. (123 /R.T)" in result.text
    assert "javascipt:;" not in result.text
    assert "https://www.sca.gov.ae/en/regulations/decision-46-2016" in result.text


def test_sca_listing_adapter_keeps_aspnet_form_wrapped_content():
    html = """
    <html><body>
      <form id="aspnetForm">
        <header>Search Services</header>
        <main class="main">
          <section>
            <div class="aegov-card card-bordered card-service" role="group" aria-labelledby="general-landing-item-14532">
              <h5 id="general-landing-item-14532">Guidelines Regulation of Virtual Assets and Virtual Assets Services Providers</h5>
              <a href="/assets/2f70b3b8/guidelines-regulation-of-virtual-assets-and-virtual-assets-services-providers.aspx" title="View Details">View Details</a>
            </div>
          </section>
        </main>
      </form>
    </body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures",
        adapter_family="sca_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "sca_listing"
    assert result.item_count == 1
    assert "Virtual Assets Services Providers" in result.text
    assert "Search Services" not in result.text


def test_sca_listing_adapter_extracts_fatca_crs_document_links():
    html = """
    <html><body>
      <form id="aspnetForm">
        <header>Search Services About Contact</header>
        <main>
          <section>
            <h1>Automatic Exchange of Information - FATCA and CRS</h1>
            <div class="aegov-card card-bordered card-service" aria-labelledby="fatca-item-1">
              <h5 id="fatca-item-1">Intergovernmental Agreement between the U.S and the UAE</h5>
              <a href="https://home.treasury.gov/system/files/131/FATCA-Agreement-UAE-6-17-2015.pdf">Download</a>
            </div>
            <div class="aegov-card card-bordered card-service" aria-labelledby="fatca-item-2">
              <h5 id="fatca-item-2">Cabinet Resolution No.93 of 2021 Implementing Certain Provisions of the Multilateral Administrative Agreement for Automatic Exchange of Information</h5>
              <a href="https://mof.gov.ae/wp-content/uploads/2023/05/Cabinet-Resolution-No.93-of-2021-Implementing-Certain-Provisions-of-the-Multilateral-Administrative-Agreement-for-Automatic-Exchange-of-Information.pdf">Download</a>
            </div>
            <div class="aegov-card card-bordered card-service" aria-labelledby="fatca-item-3">
              <h5 id="fatca-item-3">FATCA Frequently Asked Questions (“FAQs”)</h5>
              <a href="https://mof.gov.ae/wp-content/uploads/2022/08/FATCA-FAQ-ENGLISH.pdf">Download</a>
            </div>
          </section>
        </main>
      </form>
    </body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.sca.gov.ae/en/regulations/automatic-exchange-of-information-fatca-and-crs",
        adapter_family="sca_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "sca_listing"
    assert result.item_count == 3
    assert "Intergovernmental Agreement between the U.S and the UAE" in result.text
    assert "Cabinet Resolution No.93 of 2021" in result.text
    assert "FATCA-FAQ-ENGLISH.pdf" in result.text
    assert "Search Services" not in result.text


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


def test_fiu_document_listing_uses_card_heading_when_link_text_is_generic():
    html = """
    <html><body><main>
      <article class="publication-card">
        <h3>Federal Decree-Law No. 10 of 2025 on AML/CFT and Proliferation Financing</h3>
        <p>Official UAE FIU knowledge-centre publication for anti-money laundering,
        counter-terrorist financing, sanctions controls, reporting obligations, and
        financial intelligence compliance governance.</p>
        <a href="/media/laws/federal-decree-law-10-2025.pdf">Download</a>
      </article>
      <article class="publication-card">
        <h3>Cabinet Resolution No. 134 of 2025 Executive Regulations</h3>
        <p>Executive regulations covering AML, CFT, suspicious transaction reporting,
        targeted financial sanctions, customer due diligence, and supervisory controls.</p>
        <a href="/media/laws/cabinet-resolution-134-2025.pdf">View Details</a>
      </article>
    </main></body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/",
        adapter_family="fiu_eocn_document_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "fiu_eocn_document_listing"
    assert result.item_count == 2
    assert "Federal Decree-Law No. 10 of 2025" in result.text
    assert "Cabinet Resolution No. 134 of 2025" in result.text
    assert "- Title: Download" not in result.text
    assert "- Title: View Details" not in result.text


def test_eocn_news_listing_adapter_extracts_news_and_ignores_navigation():
    html = """
    <html><body>
      <nav>
        <a href="/en-us/about-us">About Us</a>
        <a href="/en-us/online-services/armed-vehicle-service">Armoring Request</a>
        <a href="/en-us/careers-List">Careers</a>
      </nav>
      <div id="NewsContainer" class="row default-list default-list-img">
        <div class="col-md-6">
          <div class="item default-section">
            <a title="Conclusion of the 42nd General Meeting of the MENAFATF group in Rebat"
               class="item-img-container pull-left"
               href="/en-us/news/conclusion-of-the-42nd-general-meeting-of-the-menafatf-group-in-rebat"></a>
            <div class="item-body-container pull-left">
              <a title="Conclusion of the 42nd General Meeting of the MENAFATF group in Rebat"
                 class="item-title-container"
                 href="/en-us/news/conclusion-of-the-42nd-general-meeting-of-the-menafatf-group-in-rebat">
                <h3>Conclusion of the 42nd General Meeting of the MENA..</h3>
              </a>
              <div class="item-brief">
                Led by His Excellency Talal Al Teneiji, Director of the Office, the UAE delegation
                participated in MENAFATF discussions related to anti-money laundering and
                counter-terrorist financing controls.
              </div>
              <div class="item-date"><span>14</span><span>May. 2026 </span></div>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="item default-section">
            <div class="item-body-container pull-left">
              <a title="UAE designates 16 individuals, five entities on its Local Terrorist List"
                 class="item-title-container"
                 href="/en-us/news/uae-designates-16-individuals-five-entities-on-its-local-terrorist-list">
                <h3>UAE designates 16 individuals, five entities on its Local Terrorist List</h3>
              </a>
              <div class="item-brief">Targeted financial sanctions update for regulated entities.</div>
              <div class="item-date"><span>9</span><span>May. 2026 </span></div>
            </div>
          </div>
        </div>
      </div>
    </body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://www.eocn.gov.ae/en-us/news",
        adapter_family="eocn_news_listing",
        adapter_config={"container_selector": "#NewsContainer"},
    )

    assert result.adapter_name == "eocn_news_listing"
    assert result.item_count == 2
    assert "Conclusion of the 42nd General Meeting" in result.text
    assert "Local Terrorist List" in result.text
    assert "14 May. 2026" in result.text
    assert "anti-money laundering" in result.text
    assert "Armoring Request" not in result.text
    assert "Careers" not in result.text


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


def test_vara_pdf_listing_uses_rulebook_card_heading_for_generic_buttons():
    html = """
    <html><body><main>
      <section class="rulebooks">
        <div class="card">
          <h3>VARA AML/CFT Rulebook</h3>
          <p>Official rulebook covering AML, CFT, sanctions, compliance governance,
          VASP controls, reporting, and regulatory obligations.</p>
          <a href="/media/rulebooks/aml-cft-rulebook.pdf">Download PDF</a>
        </div>
        <div class="card">
          <h3>VARA Company Rulebook</h3>
          <p>Official company rulebook covering governance, compliance, risk controls,
          senior management, audit, record keeping, and regulatory reporting.</p>
          <a href="/media/rulebooks/company-rulebook.pdf">Read more</a>
        </div>
        <a href="/en/contact">Contact VARA</a>
      </section>
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
    assert "VARA AML/CFT Rulebook" in result.text
    assert "VARA Company Rulebook" in result.text
    assert "- Title: Download PDF" not in result.text
    assert "- Title: Read more" not in result.text


def test_cbuae_document_listing_uses_heading_for_generic_download_links():
    html = """
    <html><body><main>
      <div class="publication-card">
        <h2>Retail Payment Services and Card Schemes Regulation</h2>
        <p>Regulation for licensed financial institutions, payment systems,
        consumer safeguards, operational controls, and Central Bank supervision.</p>
        <a href="/media/regulations/retail-payment-services-regulation.pdf">Download</a>
      </div>
      <div class="publication-card">
        <h2>Stored Value Facilities Regulation</h2>
        <p>Regulation covering payment service providers, stored value facilities,
        licensing controls, safeguarding, compliance, and operational governance.</p>
        <a href="/media/regulations/stored-value-facilities-regulation.pdf">View Details</a>
      </div>
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
    assert "Retail Payment Services" in result.text
    assert "Stored Value Facilities Regulation" in result.text
    assert "- Title: Download" not in result.text
    assert "- Title: View Details" not in result.text


def test_static_html_adapter_extracts_article_content_and_ignores_nav():
    html = """
    <html><body>
      <nav>Home Services Search</nav>
      <main><article><h1>AML Regulatory Guidance</h1><p>Regulated firms must keep
      anti-money laundering governance, screening, reporting, and training controls
      under periodic compliance review.</p></article></main>
    </body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://example.gov.ae/aml-guidance",
        adapter_family="static_html",
        adapter_config={"content_selector": "article"},
    )

    assert result.adapter_name == "static_html"
    assert "AML Regulatory Guidance" in result.text
    assert "Home Services Search" not in result.text


def test_custom_element_adapter_focus_keywords_drop_global_chrome():
    html = """
    <html><body>
      <adgm-page>
        <h2>ADGM Academy</h2>
        <h2>AccessADGM</h2>
        <p>Generic platform content about living and working in Abu Dhabi.</p>
        <h1>Financial & Cybercrime Prevention</h1>
        <h2>Developing sound practices in AML/TFS and cybercrime prevention compliance</h2>
        <p>Financial institutions must maintain AML, CFT, sanctions, suspicious activity
        reporting, customer due diligence, and regulatory compliance monitoring controls.</p>
      </adgm-page>
    </body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention",
        adapter_family="custom_element",
        adapter_config={
            "content_selector": "adgm-page",
            "focus_keywords": ["Financial & Cybercrime Prevention", "Developing sound practices"],
        },
    )

    assert result.adapter_name == "custom_element"
    assert result.text.startswith("Financial & Cybercrime Prevention")
    assert "ADGM Academy" not in result.text
    assert "AML, CFT, sanctions" in result.text


def test_pdf_listing_adapter_extracts_document_links():
    html = """
    <html><body><main>
      <a href="/docs/consultation-paper.pdf">Consultation Paper PDF</a>
      <a href="/docs/aml-guidance.pdf">AML Guidance PDF</a>
    </main></body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://example.gov.ae/publications",
        adapter_family="pdf_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "pdf_listing"
    assert result.item_count == 2
    assert "Consultation Paper PDF" in result.text


def test_register_adapter_extracts_register_rows():
    html = """
    <html><body><main>
      <table id="register">
        <tr><th>Firm</th><th>Status</th><th>Licence</th></tr>
        <tr><td>Alpha Capital</td><td>Active</td><td>Broker</td></tr>
      </table>
    </main></body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://example.gov.ae/register",
        adapter_family="register",
        adapter_config={"table_selector": "#register"},
    )

    assert result.adapter_name == "register"
    assert result.item_count == 1
    assert "Alpha Capital" in result.text


def test_pdf_document_adapter_wraps_extracted_pdf_text():
    text = "AML Rulebook\n" + ("Regulated entities must review customer due diligence and sanctions screening. " * 20)

    result = extract_with_adapter(
        text,
        url="https://example.gov.ae/rulebook.pdf",
        adapter_family="pdf_document",
    )

    assert result.adapter_name == "pdf_document"
    assert "AML Rulebook" in result.text
    assert result.source_health_risk in {"medium", "high"}


def test_adgm_fsra_listing_adapter_extracts_guidance_links():
    html = """
    <html><body><main>
      <a href="/legal-framework/guidance/aml-guidance">FSRA AML Guidance</a>
      <a href="/legal-framework/rules-and-regulations">FSRA Rules and Regulations</a>
      <a href="/contact">Contact</a>
    </main></body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.adgm.com/legal-framework/rules-and-regulations",
        adapter_family="adgm_fsra_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "adgm_fsra_listing"
    assert result.item_count == 2
    assert "FSRA AML Guidance" in result.text


def test_adgm_fsra_listing_adapter_extracts_component_link_buttons():
    html = """
    <html><body>
      <adgm-page>
        <adgm-section variant="primary">
          <adgm-expansion-panel type="plus" variant="primary">
            <span>Rules</span>
            <adgm-link-button href="https://assets.adgm.com/download/assets/ADGM1547_10529_VER08181223.pdf/21c4d7ae7efb11efb6bdd62fccae6617" icon="downloadPdf">
              Market Rules
            </adgm-link-button>
          </adgm-expansion-panel>
          <adgm-expansion-panel type="plus" variant="primary">
            <span>Guidance</span>
            <adgm-link-button href="https://assets.adgm.com/download/assets/Guidance+on+Preparing+Prospectus+VER01+290224+FINAL.pdf/740d3d527efc11ef8b05d62fccae6617" icon="downloadPdf">
              Guidance on Preparing a Prospectus
            </adgm-link-button>
            <adgm-link-button href="https://assets.adgm.com/download/assets/Guidance+-+Listing+Applications+and+Eligibility+VER01.100425.pdf/11df78d01a9b11f09d2c12dc9436842e" icon="downloadPdf">
              Guidance - Listing Applications and Eligibility
            </adgm-link-button>
          </adgm-expansion-panel>
        </adgm-section>
        <adgm-footer>
          <a href="/operating-in-adgm/e-services/fsra-connect">FSRA Connect</a>
        </adgm-footer>
      </adgm-page>
    </body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.adgm.com/financial-services-regulatory-authority/listing-authority/rules-and-guidance",
        adapter_family="adgm_fsra_listing",
        adapter_config={"container_selector": "adgm-section"},
    )

    assert result.adapter_name == "adgm_fsra_listing"
    assert result.item_count == 3
    assert "Market Rules" in result.text
    assert "Guidance on Preparing a Prospectus" in result.text
    assert "Guidance+-+Listing+Applications" in result.text
    assert "FSRA Connect" not in result.text


def test_adgm_listing_adapter_uses_card_heading_for_generic_action_links():
    html = """
    <html><body>
      <adgm-page>
        <adgm-section>
          <div class="card regulatory-action">
            <h3>Enforcement Action Against Licensed Firm</h3>
            <p>FSRA regulatory action concerning market abuse, governance controls,
            disclosure obligations, compliance monitoring, and enforcement outcomes.</p>
            <adgm-link-button href="/financial-services-regulatory-authority/enforcement/firm-action">View Details</adgm-link-button>
          </div>
          <div class="card regulatory-action">
            <h3>Listing Authority Market Disclosure Notice</h3>
            <p>Listing Authority announcement covering market disclosure, prospectus
            obligations, securities rules, issuer governance, and regulatory reporting.</p>
            <a href="/financial-services-regulatory-authority/listing-authority/announcements/disclosure-notice">Read more</a>
          </div>
          <adgm-footer><a href="/fsra-connect">FSRA Connect</a></adgm-footer>
        </adgm-section>
      </adgm-page>
    </body></html>
    """
    result = extract_with_adapter(
        html,
        url="https://www.adgm.com/financial-services-regulatory-authority/listing-authority/listing-authority-announcements",
        adapter_family="adgm_fsra_listing",
        adapter_config={"container_selector": "adgm-section"},
    )

    assert result.adapter_name == "adgm_fsra_listing"
    assert result.item_count == 2
    assert "Enforcement Action Against Licensed Firm" in result.text
    assert "Listing Authority Market Disclosure Notice" in result.text
    assert "- Title: View Details" not in result.text
    assert "- Title: Read more" not in result.text
    assert "FSRA Connect" not in result.text


def test_dfsa_notice_listing_adapter_extracts_financial_crime_links():
    html = """
    <html><body><main>
      <a href="/notices/mlro-letter-2026">MLRO Letter 2026</a>
      <a href="/enforcement/regulatory-actions/notice-1">Regulatory Action Notice</a>
      <a href="/contact">Contact</a>
    </main></body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/",
        adapter_family="dfsa_notice_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "dfsa_notice_listing"
    assert result.item_count == 2
    assert "MLRO Letter" in result.text


def test_vara_pdf_listing_extracts_rulebook_revision_updates():
    html = """
    <html><body><main>
      <div class="revision item">
        <h3>VARA Rulebook Revision Update</h3>
        <p>Updated AML/CFT rulebook controls for virtual asset service providers.</p>
        <a href="/sites/default/files/en_net_file_store/VARA_AML_Rulebook.pdf">Download PDF</a>
      </div>
      <div class="revision item">
        <h3>Company Rulebook Update</h3>
        <p>Regulatory framework and company rulebook changes.</p>
        <a href="/rulebook/company-rulebook">View Details</a>
      </div>
      <footer><a href="/contact">Contact VARA</a></footer>
    </main></body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://rulebooks.vara.ae/view-revision-updates",
        adapter_family="vara_pdf_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "vara_pdf_listing"
    assert result.item_count == 2
    assert "VARA Rulebook Revision Update" in result.text
    assert "Company Rulebook Update" in result.text
    assert "Contact VARA" not in result.text


def test_cbuae_document_listing_extracts_rulebook_links_without_static_hash_noise():
    html = """
    <html><body><main>
      <section class="rulebook-card">
        <h3>AML/CFT Rulebook Updates</h3>
        <p>Central Bank rulebook material for anti-money laundering and financial crime controls.</p>
        <a href="/en/rulebook/amlcft">View</a>
      </section>
      <section class="rulebook-card">
        <h3>Retail Payment Services Regulation</h3>
        <p>Payment services and card schemes regulation for licensed financial institutions.</p>
        <a href="/en/rulebook/312-retail-payment-services-and-card-schemes-regulation">Read more</a>
      </section>
      <nav><a href="/en/search">Search</a></nav>
    </main></body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://rulebook.centralbank.ae/en/rulebook/amlcft",
        adapter_family="cbuae_document_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "cbuae_document_listing"
    assert result.item_count == 2
    assert "AML/CFT Rulebook Updates" in result.text
    assert "Retail Payment Services Regulation" in result.text
    assert "- Title: View" not in result.text
    assert "- Title: Read more" not in result.text
    assert "Search" not in result.text


def test_dfsa_notice_listing_extracts_consultation_and_enforcement_links():
    html = """
    <html><body><main>
      <article class="card">
        <h3>Consultation Paper No.165</h3>
        <p>Proposed changes to licensed functions and authorised individual rules.</p>
        <a href="/your-resources/regulatory/consultation-papers/cp165">View Details</a>
      </article>
      <article class="card">
        <h3>Published Enforcement Decision</h3>
        <p>DFSA enforcement decision concerning AML controls and governance.</p>
        <a href="/what-we-do/enforcement/published-decisions/decision-1">Read more</a>
      </article>
      <footer><a href="/contact">Contact</a></footer>
    </main></body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.dfsa.ae/your-resources/regulatory/consultation-papers",
        adapter_family="dfsa_notice_listing",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "dfsa_notice_listing"
    assert result.item_count == 2
    assert "Consultation Paper No.165" in result.text
    assert "Published Enforcement Decision" in result.text
    assert "- Title: View Details" not in result.text
    assert "- Title: Read more" not in result.text
    assert "Contact" not in result.text


def test_uae_legal_database_adapter_extracts_legislation_cards():
    html = """
    <html><body><main>
      <article class="legislation-card">
        <h3>Federal Decree-Law No. 10 of 2025 on Anti-Money Laundering</h3>
        <p>Federal legislation covering AML/CFT and proliferation financing controls.</p>
        <a href="/en/laws-and-legislation/aml-cft-2025.pdf">View details</a>
      </article>
      <article class="legislation-card">
        <h3>Cabinet Decision No. 134 of 2025 Executive Regulation</h3>
        <p>Executive regulation for federal AML/CFT law.</p>
        <a href="/en/laws-and-legislation/cabinet-decision-134-2025">Read more</a>
      </article>
      <footer><a href="/contact">Contact</a></footer>
    </main></body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.moj.gov.ae/en/laws-and-legislation/latest-legislations-and-laws.aspx",
        adapter_family="uae_legal_database",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_name == "uae_legal_database"
    assert result.item_count == 2
    assert "Federal Decree-Law No. 10 of 2025" in result.text
    assert "Cabinet Decision No. 134 of 2025" in result.text
    assert "- Title: View details" not in result.text
    assert "Contact" not in result.text


def test_uae_legal_database_adapter_rejects_nav_shell():
    result = extract_with_adapter(
        "<html><body><nav>Home Search Contact</nav><main><a href='/contact'>Contact</a></main></body></html>",
        url="https://www.moj.gov.ae/en/laws-and-legislation.aspx",
        adapter_family="uae_legal_database",
    )

    assert result.item_count == 0
    assert result.failure_reason


def test_source_intake_uae_legal_database_passes_preview_only():
    html = """
    <html><body><main>
      <section class="card">
        <h3>Companies Law Federal Decree-Law No. 32 of 2021</h3>
        <p>Federal commercial companies legislation relevant to regulated UAE firms.</p>
        <a href="/en/laws-and-legislation/companies-law">View</a>
      </section>
      <section class="card">
        <h3>Economic Substance Regulations</h3>
        <p>Regulatory obligations and reporting expectations for UAE entities.</p>
        <a href="/en/laws-and-legislation/economic-substance-regulations">Read more</a>
      </section>
      <section class="card">
        <h3>Anti-Money Laundering and Combatting Terrorism Financing Law</h3>
        <p>Federal AML/CFT law for financial crime, sanctions, and regulatory compliance controls.</p>
        <a href="/en/laws-and-legislation/anti-money-laundering-law">Read more</a>
      </section>
      <section class="card">
        <h3>Consumer Protection Regulations and Compliance Controls</h3>
        <p>Federal consumer protection obligations relevant to regulated firms, disclosure, complaints, and market conduct.</p>
        <a href="/en/laws-and-legislation/consumer-protection-regulations">View details</a>
      </section>
    </main></body></html>
    """
    source = {
        "source_id": "AE-uae-legal-database-test",
        "name": "UAE Legal Database Test",
        "url": "https://www.moj.gov.ae/en/laws-and-legislation.aspx",
        "adapter_family": "uae_legal_database",
        "adapter_name": "uae_legal_database",
        "adapter_config": {"container_selector": "main"},
    }

    with patch("app.scraper.fetch_page_with_config", return_value=html):
        result = run_source_intake(source, write_evidence=False)

    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["adapter_family"] == "uae_legal_database"
    assert result["structured_adapter_content"] is True
    assert result["can_save_evidence"] is True
    assert result["can_activate_monitoring"] is False
    assert result["evidence_written"] is False


def test_source_intake_maps_structured_failure_code_for_nav_shell():
    source = {
        "source_id": "AE-test-nav-shell",
        "name": "Nav Shell Test",
        "url": "https://www.example.gov.ae/not-found",
        "expected_min_length": 500,
    }
    html = "<html><body><nav>Home About Search Contact Privacy Accessibility</nav><main>Home Search Contact</main></body></html>"

    with patch("app.scraper.fetch_page_with_config", return_value=html):
        result = run_source_intake(source, write_evidence=False)

    assert result["status"] == SourceIntakeStatus.NAV_SHELL_ONLY
    assert result["failure_code"] == "NAV_SHELL_ONLY"
    assert result["can_save_evidence"] is False
    assert result["meaningful_content"] is False
