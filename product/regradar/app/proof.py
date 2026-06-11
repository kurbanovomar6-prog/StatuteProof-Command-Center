"""Reusable source proof block builder."""

from __future__ import annotations

from typing import Any


DISCLAIMER = "StatuteProof provides early-warning regulatory intelligence, not legal advice."


def _proof_quality(run_record: dict[str, Any], diff_artifact: dict[str, Any] | None) -> str:
    if run_record.get("change_status") == "FAILED" or run_record.get("error"):
        return "INCOMPLETE"
    if not run_record.get("normalized_hash") or not run_record.get("snapshot_normalized_path"):
        return "INCOMPLETE"
    if diff_artifact and diff_artifact.get("diff_quality") == "INCOMPLETE":
        return "INCOMPLETE"
    if (
        run_record.get("limitations_notes")
        or run_record.get("extraction_quality") in {"THIN", "FAILED"}
        or (diff_artifact and diff_artifact.get("diff_quality") == "LIMITED")
    ):
        return "LIMITED"
    return "GOOD"


def build_source_proof(
    run_record: dict[str, Any],
    diff_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "source_name": run_record.get("source_name"),
        "market": run_record.get("market") or run_record.get("jurisdiction"),
        "source_id": run_record.get("source_id"),
        "official_url": run_record.get("official_url"),
        "final_url": run_record.get("final_url"),
        "checked_at_utc": run_record.get("timestamp_utc"),
        "fetch_method": run_record.get("fetch_method"),
        "extraction_quality": run_record.get("extraction_quality"),
        "raw_chars": run_record.get("raw_chars"),
        "normalized_chars": run_record.get("normalized_chars"),
        "raw_hash": run_record.get("raw_hash"),
        "normalized_hash": run_record.get("normalized_hash"),
        "pdf_text_hash": run_record.get("pdf_text_hash"),
        "pdf_links_count": run_record.get("pdf_links_count"),
        "pdf_extracted_chars": run_record.get("pdf_extracted_chars"),
        "change_status": run_record.get("change_status"),
        "limitations_notes": run_record.get("limitations_notes"),
        "snapshot_raw_path": run_record.get("snapshot_raw_path"),
        "snapshot_normalized_path": run_record.get("snapshot_normalized_path"),
        "snapshot_pdf_text_path": run_record.get("snapshot_pdf_text_path"),
        "diff_json_path": run_record.get("diff_json_path"),
        "diff_md_path": run_record.get("diff_md_path"),
        "meaningful_change_detected": (
            diff_artifact.get("meaningful_change_detected")
            if diff_artifact is not None
            else run_record.get("meaningful_change_detected")
        ),
        "proof_quality": _proof_quality(run_record, diff_artifact),
        "disclaimer": DISCLAIMER,
    }
