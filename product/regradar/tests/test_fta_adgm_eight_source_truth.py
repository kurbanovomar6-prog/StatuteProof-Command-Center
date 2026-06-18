from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.adapter_platform import extract_with_adapter
from app.source_intake import SourceIntakeStatus, run_source_intake


def test_pdf_document_adapter_preserves_lines_for_quality_gate():
    extracted_text = "\n".join(
        [
            "ADGM Data Protection Regulations 2021",
            "Part 1 - General Provisions",
            "Part 2 - Principles",
            "Part 3 - Data Subject Rights",
            "Controller and processor obligations apply to personal data processing.",
            "The Commissioner may issue guidance, decisions, notices, and regulatory requirements.",
        ]
        + [
            f"Section {idx}: These regulations include compliance, risk, reporting, obligation, authority, law, and regulatory terms."
            for idx in range(1, 81)
        ]
    )
    source = {
        "source_id": "AE-adgm-data-protection-regulations-2021-pdf",
        "name": "ADGM Data Protection Regulations 2021 - Official PDF",
        "url": "https://www.adgm.com/documents/office-of-data-protection/resources/adgm-data-protection-regulations-2021-updated.pdf",
        "source_type": "pdf",
        "adapter_family": "pdf_document",
        "adapter_name": "pdf_document",
    }

    with patch("app.scraper.fetch_page_with_config", return_value="%PDF raw bytes"), \
        patch("app.document_extractor.fetch_document") as fetch_document, \
        patch("app.document_extractor.extract_pdf_text") as extract_pdf_text:
        fetch_document.return_value = {
            "status": "ok",
            "http_status": 200,
            "content_type": "application/pdf",
            "bytes": 4096,
            "data": b"%PDF fixture bytes",
            "error": "",
        }
        extract_pdf_text.return_value = {
            "text": extracted_text,
            "chars": len(extracted_text),
            "quality": "good",
            "method": "pypdf",
            "error": "",
        }

        result = run_source_intake(source, all_sources=[], write_evidence=False)

    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["adapter_name"] == "pdf_document"
    assert result["quality_breakdown"]["text_stats"]["heading_count"] >= 3
    assert result["can_save_evidence"] is True


def test_adgm_fsra_listing_adapter_extracts_regulatory_alerts():
    html = """
    <html><body>
      <adgm-page>
        <section class="cards">
          <article class="card">
            <h3>FSRA Regulatory Alert - Unauthorised firm warning</h3>
            <p>Published 13 May 2026. The FSRA issued a regulatory alert and enforcement warning.</p>
            <a href="/operating-in-adgm/fsra/enforcement/regulatory-alerts/unauthorised-firm-warning">Read alert</a>
          </article>
          <article class="card">
            <h3>FSRA Regulatory Alert - Market abuse warning</h3>
            <p>Published 20 April 2026. Public notice for compliance teams and authorised firms.</p>
            <a href="/operating-in-adgm/fsra/enforcement/regulatory-alerts/market-abuse-warning">Read alert</a>
          </article>
          <article class="card">
            <h3>FSRA Regulatory Alert - Suspicious investment scheme</h3>
            <p>Published 02 March 2026. Regulatory warning for investors and regulated firms.</p>
            <a href="/operating-in-adgm/fsra/enforcement/regulatory-alerts/suspicious-investment-scheme">Read alert</a>
          </article>
        </section>
      </adgm-page>
    </body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/enforcement/regulatory-alerts",
        adapter_family="adgm_fsra_listing",
        adapter_name="adgm_fsra_listing",
        adapter_config={"container_selector": "adgm-page"},
    )

    assert result.failure_reason == ""
    assert result.item_count == 3
    assert "Regulatory Alert" in result.text
    assert "Row hash:" in result.text
