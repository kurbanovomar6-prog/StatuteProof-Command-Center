from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.adapter_platform import extract_with_adapter
from app.audit_export import build_audit_pack_export_response
from app.review_queue import build_review_queue
from app.source_intake import SourceIntakeStatus, run_source_intake
from app.source_quality import detect_policy_warnings


_DIFC_LEGAL_DATABASE_HTML = """
<html>
  <body>
    <nav>Home Business Client Portal Contact</nav>
    <main>
      <h1>DIFC Legal Database</h1>
      <article class="law-card">
        <h3>Data Protection Law DIFC Law No. 5 of 2020</h3>
        <p>DIFC Data Protection Law establishes data protection obligations, commissioner powers,
        compliance duties, enforcement, penalties, notices, and regulatory requirements.</p>
        <a href="/business/laws-and-regulations/legal-database/difc-laws/data-protection-law-difc-law-no-5-2020">More info</a>
        <a href="https://assets.difc.com/public/data-protection-law.pdf"></a>
      </article>
      <article class="law-card">
        <h3>Digital Assets Law DIFC Law No. 2 of 2024</h3>
        <p>The Digital Assets Law supports DIFC legal certainty for digital assets, obligations,
        amendments, regulatory framework updates, and compliance review by legal teams.</p>
        <a href="/business/laws-and-regulations/legal-database/difc-laws/digital-assets-law-difc-law-no-2-of-2024">More info</a>
        <a href="https://assets.difc.com/public/digital_assets_law_2_of_2024.pdf">Download PDF</a>
      </article>
      <article class="law-card">
        <h3>Companies Regulations</h3>
        <p>DIFC Companies Regulations describe filing, registrar, governance, compliance,
        reporting, and regulatory obligations.</p>
        <a href="/business/laws-and-regulations/legal-database/difc-regulations/companies-regulations">More info</a>
      </article>
    </main>
  </body>
</html>
"""


def test_difc_public_page_client_portal_reference_is_not_private_portal_block():
    text = (
        "DIFC Legal Database publishes laws, regulations, consultation papers, data protection "
        "guidance, commissioner supervision material, enforcement material, and compliance "
        "requirements for regulated businesses. The page also links to the DIFC Client Portal "
        "as site chrome, but the legal database content is public. "
    ) * 10
    html = f"<html><body><nav>DIFC Client Portal</nav><main>{text}</main></body></html>"

    assert "private_portal" not in detect_policy_warnings(text, html)


def test_difc_private_portal_gate_is_still_blocked():
    warnings = detect_policy_warnings("DIFC Client Portal restricted access for authorised users only. Login required.")

    assert "private_portal" in warnings


def test_difc_legal_database_adapter_extracts_laws_and_pdf_links():
    result = extract_with_adapter(
        _DIFC_LEGAL_DATABASE_HTML,
        url="https://www.difc.com/business/laws-and-regulations/legal-database/",
        adapter_family="difc_legal_database",
        adapter_config={"container_selector": "main"},
    )

    assert result.adapter_family == "difc_legal_database"
    assert result.item_count >= 3
    assert "Data Protection Law DIFC Law No. 5 of 2020" in result.text
    assert "Digital Assets Law DIFC Law No. 2 of 2024" in result.text
    assert "Companies Regulations" in result.text
    assert "Client Portal" not in result.text
    assert "data-protection-law.pdf" in result.text
    assert all(item.get("row_hash") for item in result.items)


def test_difc_legal_database_adapter_derives_title_from_real_li_pattern():
    html = """
    <html><body><main>
      <ul class="grid">
        <li class="col-span-full flex items-center">
          <span>Data Protection Law DIFC Law No. 5 of 2020</span>
          <span><a class="group" href="/business/laws-and-regulations/legal-database/difc-laws/data-protection-law-difc-law-no-5-2020">More info</a></span>
          <a href="https://assets.difc.com/v1/media/data-protection-law.pdf"></a>
        </li>
      </ul>
    </main></body></html>
    """

    result = extract_with_adapter(
        html,
        url="https://www.difc.com/business/laws-and-regulations/legal-database/",
        adapter_family="difc_legal_database",
    )

    assert result.item_count >= 1
    assert "Data Protection Law DIFC Law No. 5 of 2020" in result.text
    assert "Title: More info" not in result.text


def test_difc_legal_database_nav_shell_fixture_is_rejected():
    result = extract_with_adapter(
        "<html><body><nav>Home Client Portal Contact</nav><main><a href='/contact'>Contact</a></main></body></html>",
        url="https://www.difc.com/business/laws-and-regulations/legal-database/",
        adapter_family="difc_legal_database",
    )

    assert result.item_count == 0
    assert result.failure_reason


def test_difc_source_intake_with_adapter_can_pass_without_evidence_claim():
    source = {
        "source_id": "AE-difc-legal-database-test",
        "name": "DIFC Legal Database",
        "url": "https://www.difc.com/business/laws-and-regulations/legal-database/",
        "adapter_family": "difc_legal_database",
        "adapter_name": "difc_legal_database",
        "adapter_config": {"container_selector": "main"},
    }

    with patch("app.scraper.fetch_page_with_config", return_value=_DIFC_LEGAL_DATABASE_HTML):
        result = run_source_intake(source, all_sources=[], write_evidence=False)

    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["adapter_family"] == "difc_legal_database"
    assert result["can_save_evidence"] is True
    assert result["can_activate_monitoring"] is False
    assert result["evidence_written"] is False


def test_difc_access_blocked_response_is_classified_honestly():
    source = {
        "source_id": "AE-difc-blocked-test",
        "name": "DIFC blocked test",
        "url": "https://www.difc.com/private",
        "adapter_family": "difc_legal_database",
        "adapter_name": "difc_legal_database",
    }

    with patch("app.scraper.fetch_page_with_config", return_value="403 Forbidden. Restricted access. Login required."):
        result = run_source_intake(source, all_sources=[], write_evidence=False)

    assert result["status"] == SourceIntakeStatus.BLOCKED
    assert result["can_save_evidence"] is False
    assert result["failure_code"] in {"ACCESS_BLOCKED", "LIKELY_WAF_403"}


def _write_difc_evidence_record(base: Path) -> dict:
    source_id = "AE-difc-legal-database"
    run_id = "difc-run-1"
    snapshot_dir = base / "data" / "source_snapshots" / "2026-06-16" / "AE" / source_id / run_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    proof_path = snapshot_dir / "proof.json"
    normalized_path = snapshot_dir / "normalized.txt"
    proof_path.write_text(json.dumps({"proof_quality": "GOOD", "source_id": source_id}), encoding="utf-8")
    normalized_path.write_text("DIFC Legal Database law and regulation listing content", encoding="utf-8")
    record = {
        "run_id": run_id,
        "timestamp_utc": "2026-06-16T12:00:00Z",
        "market": "AE",
        "jurisdiction": "AE",
        "source_id": source_id,
        "source_name": "DIFC Legal Database",
        "official_url": "https://www.difc.com/business/laws-and-regulations/legal-database/",
        "final_url": "https://www.difc.com/business/laws-and-regulations/legal-database/",
        "access_status": "public_fetch_attempted",
        "extraction_quality": "GOOD",
        "change_status": "UNCHANGED",
        "source_health_status": "MONITOR_OK",
        "quality_score": 75,
        "normalized_hash": "c" * 64,
        "content_hash": "a" * 64,
        "raw_hash": "b" * 64,
        "snapshot_normalized_path": str(normalized_path.relative_to(base)),
        "proof_block_path": str(proof_path.relative_to(base)),
    }
    runs_path = base / "data" / "source_runs" / "source_runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    runs_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return record


def test_review_queue_can_include_saved_difc_evidence_record():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        record = _write_difc_evidence_record(base)

        queue = build_review_queue(base_dir=base, status="pending")

        assert queue["total"] == 1
        assert queue["queue"][0]["evidence_record_id"] == record["run_id"]
        assert queue["queue"][0]["source_id"] == "AE-difc-legal-database"
        assert queue["queue"][0]["pending_review"] is True


def test_pdf_audit_export_works_for_saved_difc_evidence_record():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        record = _write_difc_evidence_record(base)

        response = build_audit_pack_export_response(record, export_format="pdf", base_dir=base)

        assert response["ok"] is True
        assert response["format"] == "pdf"
        assert "Monitoring intelligence only. Not legal advice." in response["disclaimer"]
        assert (base / response["export"]["pdf_path"]).exists()
