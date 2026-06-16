from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.audit_export import build_audit_pack_export_response
from app.review_queue import build_review_queue
from app.source_intake import SourceIntakeStatus, run_source_intake


def test_direct_pdf_source_intake_uses_extracted_pdf_text():
    extracted_text = (
        "VARA Broker-Dealer Services Rulebook\n"
        + "Virtual Asset Service Providers must maintain governance, compliance, AML, risk, and reporting controls. " * 80
    )
    source = {
        "source_id": "AE-vara-broker-dealer-rulebook-pdf",
        "name": "VARA Broker-Dealer Services Rulebook PDF",
        "url": "https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_226_VER20250519.pdf",
        "source_type": "pdf",
        "adapter_family": "pdf_document",
        "adapter_name": "pdf_document",
    }

    with patch("app.scraper.fetch_page_with_config", return_value="%PDF-1.7 raw bytes should not be normalized"), \
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

    fetch_document.assert_called_once_with(source["url"])
    extract_pdf_text.assert_called_once_with(b"%PDF fixture bytes")
    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["provider_used"] == "pdf_document"
    assert result["adapter_name"] == "pdf_document"
    assert result["pdf_chars"] == len(extracted_text)
    assert "Broker-Dealer Services Rulebook" in result["normalized_preview"]
    assert not result["normalized_preview"].startswith("%PDF")
    assert result["can_save_evidence"] is True


def test_direct_pdf_source_intake_blocks_shallow_pdf():
    source = {
        "source_id": "AE-vara-shallow-rulebook-pdf",
        "name": "VARA Shallow Rulebook PDF",
        "url": "https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_EMPTY.pdf",
        "source_type": "pdf",
        "adapter_family": "pdf_document",
        "adapter_name": "pdf_document",
    }

    with patch("app.scraper.fetch_page_with_config", return_value="%PDF-1.7 raw bytes"), \
        patch("app.document_extractor.fetch_document") as fetch_document, \
        patch("app.document_extractor.extract_pdf_text") as extract_pdf_text:
        fetch_document.return_value = {
            "status": "ok",
            "http_status": 200,
            "content_type": "application/pdf",
            "bytes": 512,
            "data": b"%PDF shallow fixture",
            "error": "",
        }
        extract_pdf_text.return_value = {
            "text": "Too short",
            "chars": 9,
            "quality": "failed",
            "method": "pypdf",
            "error": "",
        }

        result = run_source_intake(source, all_sources=[], write_evidence=False)

    assert result["status"] != SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["can_save_evidence"] is False
    assert result["shallow_content"] is True
    assert result["failure_code"] in {"SHALLOW_CONTENT", "PDF_ONLY_SOURCE"}


def _write_vara_pdf_evidence_record(base: Path) -> dict:
    source_id = "AE-vara-broker-dealer-rulebook-pdf"
    run_id = "vara-pdf-run-1"
    snapshot_dir = base / "data" / "source_snapshots" / "2026-06-16" / "AE" / source_id / run_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    proof_path = snapshot_dir / "proof.json"
    normalized_path = snapshot_dir / "normalized.txt"
    proof_path.write_text(json.dumps({"proof_quality": "GOOD", "source_id": source_id}), encoding="utf-8")
    normalized_path.write_text("VARA Broker-Dealer Services Rulebook extracted text", encoding="utf-8")
    record = {
        "run_id": run_id,
        "timestamp_utc": "2026-06-16T12:00:00Z",
        "market": "AE",
        "jurisdiction": "AE",
        "source_id": source_id,
        "source_name": "VARA Broker-Dealer Services Rulebook PDF",
        "official_url": "https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_226_VER20250519.pdf",
        "final_url": "https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_226_VER20250519.pdf",
        "access_status": "public_pdf_fetch_attempted",
        "extraction_quality": "ACCEPTABLE",
        "change_status": "UNCHANGED",
        "source_health_status": "MONITOR_OK",
        "quality_score": 60,
        "normalized_hash": "b0e6d901933fa5ae47d9be1528614c2af7c456856e336977b0699170f3ef4022",
        "content_hash": "a" * 64,
        "raw_hash": "b" * 64,
        "snapshot_normalized_path": str(normalized_path.relative_to(base)),
        "proof_block_path": str(proof_path.relative_to(base)),
    }
    runs_path = base / "data" / "source_runs" / "source_runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    runs_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return record


def test_review_queue_can_include_saved_vara_pdf_evidence_record():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        record = _write_vara_pdf_evidence_record(base)

        queue = build_review_queue(base_dir=base, status="pending")

        assert queue["total"] == 1
        assert queue["queue"][0]["evidence_record_id"] == record["run_id"]
        assert queue["queue"][0]["source_id"] == "AE-vara-broker-dealer-rulebook-pdf"
        assert queue["queue"][0]["source_health_status"] == "MONITOR_OK"
        assert queue["queue"][0]["pending_review"] is True


def test_pdf_audit_export_works_for_saved_vara_pdf_evidence_record():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        record = _write_vara_pdf_evidence_record(base)

        response = build_audit_pack_export_response(record, export_format="md_html", base_dir=base)

        assert response["ok"] is True
        assert response["format"] == "md_html"
        assert "Monitoring intelligence only. Not legal advice." in response["disclaimer"]
        assert (base / response["export"]["md_path"]).exists()
        assert (base / response["export"]["html_path"]).exists()
