"""
RegRadar — source run history.

Lightweight JSONL run evidence for source-readiness checks. This is intentionally
append-only and filesystem-based so it can support first pilots without a DB
migration.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.chunk_diff import build_chunk_diff, build_incomplete_diff, render_diff_markdown, utc_now
from app.proof import build_source_proof
from app.text_normalization import normalize_for_change_hash, stable_normalized_hash


_BASE_DIR = Path(__file__).parent.parent
_RUN_DIR = _BASE_DIR / "data" / "source_runs"
_RUN_FILE = _RUN_DIR / "source_runs.jsonl"
_SNAPSHOT_DIR = _BASE_DIR / "data" / "source_snapshots"

_GOOD_ORDER = {"FAILED": 0, "THIN": 1, "MEDIUM": 2, "GOOD": 3}
_MIN_NORMALIZED_CHARS = 500

_RUNS_CACHE: list[dict] | None = None
_CACHE_VALID: bool = False


def source_run_path() -> Path:
    return _RUN_FILE


def source_snapshot_dir() -> Path:
    return _SNAPSHOT_DIR


def make_source_id(source: dict) -> str:
    existing = source.get("id") or source.get("source_id")
    if existing:
        return str(existing)
    market = str(source.get("jurisdiction") or source.get("market") or "XX").upper()
    name = str(source.get("name") or source.get("url") or "source").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", name).strip("-")[:72] or "source"
    return f"{market}-{slug}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stable_content_hash(text: str) -> str | None:
    if not text:
        return None
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _raw_hash(text: str) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(_BASE_DIR))
    except ValueError:
        return str(path)


def _path_from_rel(path: str | None) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return _BASE_DIR / candidate


def _snapshot_paths(timestamp_utc: str, market: str, source_id: str, run_id: str) -> Path:
    date_part = timestamp_utc[:10] if timestamp_utc else datetime.now(timezone.utc).date().isoformat()
    return _SNAPSHOT_DIR / date_part / market.upper() / source_id / run_id


def _write_snapshots(
    *,
    timestamp_utc: str,
    market: str,
    source_id: str,
    run_id: str,
    raw_text: str,
    normalized_text: str,
    pdf_text: str,
    metadata: dict,
) -> dict[str, str | None]:
    base = _snapshot_paths(timestamp_utc, market, source_id, run_id)
    base.mkdir(parents=True, exist_ok=True)

    raw_path = base / "raw.txt"
    normalized_path = base / "normalized.txt"
    metadata_path = base / "metadata.json"
    pdf_path = base / "pdf_text.txt" if pdf_text else None

    raw_path.write_text(raw_text or "", encoding="utf-8")
    normalized_path.write_text(normalized_text or "", encoding="utf-8")
    if pdf_path is not None:
        pdf_path.write_text(pdf_text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return {
        "snapshot_raw_path": _rel(raw_path),
        "snapshot_normalized_path": _rel(normalized_path),
        "snapshot_pdf_text_path": _rel(pdf_path),
        "snapshot_metadata_path": _rel(metadata_path),
    }


def _read_runs() -> list[dict]:
    global _RUNS_CACHE, _CACHE_VALID
    if _CACHE_VALID and _RUNS_CACHE is not None:
        return _RUNS_CACHE
    if not _RUN_FILE.exists():
        _RUNS_CACHE = []
        _CACHE_VALID = True
        return _RUNS_CACHE
    rows: list[dict] = []
    try:
        for line in _RUN_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except FileNotFoundError:
        rows = []
    _RUNS_CACHE = rows
    _CACHE_VALID = True
    return _RUNS_CACHE


def latest_runs(
    market: str | None = None,
    source_filter: str | None = None,
) -> dict[str, dict]:
    market_norm = market.upper() if market else None
    source_norm = source_filter.lower() if source_filter else None
    latest: dict[str, dict] = {}

    for rec in _read_runs():
        if market_norm and str(rec.get("market", "")).upper() != market_norm:
            continue
        if source_norm:
            sid = str(rec.get("source_id", "")).lower()
            name = str(rec.get("source_name", "")).lower()
            if source_norm not in sid and source_norm not in name:
                continue
        sid = str(rec.get("source_id") or rec.get("official_url") or "")
        if not sid:
            continue
        latest[sid] = rec
    return latest


def previous_run(source_id: str) -> dict | None:
    for rec in reversed(_read_runs()):
        if rec.get("source_id") == source_id:
            return rec
    return None


def changed_runs(
    market: str | None = None,
    source_filter: str | None = None,
    limit: int = 20,
) -> list[dict]:
    market_norm = market.upper() if market else None
    source_norm = source_filter.lower() if source_filter else None
    rows: list[dict] = []
    for rec in _read_runs():
        if rec.get("change_status") != "CHANGED":
            continue
        if market_norm and str(rec.get("market", "")).upper() != market_norm:
            continue
        if source_norm:
            sid = str(rec.get("source_id", "")).lower()
            name = str(rec.get("source_name", "")).lower()
            if source_norm not in sid and source_norm not in name:
                continue
        rows.append(rec)
    rows.sort(key=lambda r: r.get("timestamp_utc", ""), reverse=True)
    return rows[:limit]


def classify_change(current: dict, previous: dict | None) -> str:
    quality = current.get("extraction_quality", "FAILED")
    chars = int(current.get("extracted_chars") or 0)
    normalized_chars = int(current.get("normalized_chars") or 0)
    if current.get("access_status") == "failed" or quality == "FAILED":
        return "FAILED"
    if previous is None:
        return "FIRST_SEEN"

    prev_quality = previous.get("extraction_quality", "FAILED")
    prev_chars = int(previous.get("extracted_chars") or 0)
    prev_norm_chars = int(previous.get("normalized_chars") or 0)
    if prev_quality == "FAILED" and quality != "FAILED":
        return "FIRST_SEEN"
    if _GOOD_ORDER.get(prev_quality, 0) >= _GOOD_ORDER["MEDIUM"] and _GOOD_ORDER.get(quality, 0) <= _GOOD_ORDER["THIN"]:
        return "QUALITY_DROP"
    if prev_chars > 0 and chars < prev_chars * 0.4:
        return "QUALITY_DROP"
    if normalized_chars and normalized_chars < _MIN_NORMALIZED_CHARS:
        return "QUALITY_DROP"
    if prev_norm_chars > 0 and normalized_chars and normalized_chars < prev_norm_chars * 0.4:
        return "QUALITY_DROP"

    if previous.get("normalized_hash"):
        prev_hash = previous.get("normalized_hash")
        cur_hash = current.get("normalized_hash") or current.get("content_hash")
    else:
        prev_hash = previous.get("content_hash")
        cur_hash = current.get("content_hash")
    if prev_hash and cur_hash and prev_hash != cur_hash:
        return "CHANGED"
    return "UNCHANGED"


def append_run(record: dict) -> dict:
    _RUN_DIR.mkdir(parents=True, exist_ok=True)
    prev = previous_run(record["source_id"])
    record["change_status"] = classify_change(record, prev)
    if (
        record["change_status"] == "UNCHANGED"
        and prev
        and record.get("raw_hash")
        and prev.get("raw_hash")
        and record.get("raw_hash") != prev.get("raw_hash")
        and record.get("normalized_hash")
        and record.get("normalized_hash") == prev.get("normalized_hash")
    ):
        _append_limitation(record, "Raw content changed; normalized regulatory content unchanged.")
    diff_artifact = None
    snapshot_base = _snapshot_base_from_record(record)
    if snapshot_base is not None:
        if record["change_status"] == "CHANGED":
            diff_artifact = _write_diff_artifacts(record, prev, snapshot_base)
        _write_proof_artifact(record, diff_artifact, snapshot_base)
    with _RUN_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    global _CACHE_VALID
    _CACHE_VALID = False
    return record


def _append_limitation(record: dict, note: str) -> None:
    existing = str(record.get("limitations_notes") or "").strip()
    if note in existing:
        return
    record["limitations_notes"] = f"{existing}; {note}" if existing else note


def _snapshot_base_from_record(record: dict) -> Path | None:
    for key in ("snapshot_normalized_path", "snapshot_raw_path", "snapshot_metadata_path"):
        path = _path_from_rel(record.get(key))
        if path is not None:
            return path.parent
    return None


def _read_snapshot_text(path: str | None) -> str | None:
    snapshot_path = _path_from_rel(path)
    if snapshot_path is None or not snapshot_path.exists():
        return None
    return snapshot_path.read_text(encoding="utf-8", errors="replace")


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_diff_artifacts(record: dict, prev: dict | None, snapshot_base: Path) -> dict:
    previous_path = prev.get("snapshot_normalized_path") if prev else None
    current_path = record.get("snapshot_normalized_path")
    previous_text = _read_snapshot_text(previous_path)
    current_text = _read_snapshot_text(current_path)

    if previous_text is None or current_text is None:
        artifact = build_incomplete_diff(
            previous_run_id=prev.get("run_id") if prev else None,
            current_run_id=record.get("run_id"),
            previous_snapshot_normalized_path=previous_path,
            current_snapshot_normalized_path=current_path,
            limitation="Previous normalized snapshot unavailable; diff cannot be generated.",
        )
    else:
        artifact = build_chunk_diff(previous_text, current_text)
        artifact.update({
            "previous_run_id": prev.get("run_id") if prev else None,
            "current_run_id": record.get("run_id"),
            "previous_snapshot_normalized_path": previous_path,
            "current_snapshot_normalized_path": current_path,
            "generated_at_utc": utc_now(),
        })

    diff_json_path = snapshot_base / "diff.json"
    diff_md_path = snapshot_base / "diff.md"
    _write_json(diff_json_path, artifact)
    diff_md_path.write_text(render_diff_markdown(artifact), encoding="utf-8")
    record["diff_json_path"] = _rel(diff_json_path)
    record["diff_md_path"] = _rel(diff_md_path)
    record["meaningful_change_detected"] = artifact.get("meaningful_change_detected")
    record["diff_quality"] = artifact.get("diff_quality")
    return artifact


def _write_proof_artifact(record: dict, diff_artifact: dict | None, snapshot_base: Path) -> None:
    proof_path = snapshot_base / "proof.json"
    record["proof_block_path"] = _rel(proof_path)
    proof = build_source_proof(record, diff_artifact)
    _write_json(proof_path, proof)


def record_from_source_result(
    *,
    run_id: str,
    source: dict,
    result: dict,
    limitations_notes: list[str] | None = None,
) -> dict:
    doc_info = result.get("document_info") or {}
    pdf_text = doc_info.get("combined_text") or ""
    page_text = result.get("extracted_text") or ""
    combined_raw_text = _combine_text(page_text, pdf_text)
    normalized_text = normalize_for_change_hash(combined_raw_text)
    extracted_chars = int(result.get("extracted_chars") or 0)
    pdf_chars = int(doc_info.get("combined_chars") or 0)
    quality = _quality_from_chars(extracted_chars + pdf_chars)
    timestamp_utc = now_utc()
    market = str(source.get("jurisdiction") or "").upper()
    source_id = make_source_id(source)

    fetch_method = result.get("fetch_method") or result.get("recommended_method") or "failed"
    if pdf_chars > 0 and fetch_method not in ("failed", "pdf"):
        fetch_method = "mixed"

    access_status = "accessible" if result.get("status") == "ok" else "failed"
    if result.get("verdict") == "needs_adapter":
        access_status = "dynamic/adapter_needed"
    elif source.get("status") in ("disabled_external_access", "disabled_navigation_only"):
        access_status = "restricted"

    notes = list(limitations_notes or [result.get("reason") or ""])
    if int(doc_info.get("pdf_links_count") or 0) > 0 and pdf_chars == 0:
        notes.append("PDF links found but no extractable text; manual validation/OCR may be required.")
    if normalized_text and len(normalized_text) < _MIN_NORMALIZED_CHARS and quality != "FAILED":
        notes.append("Normalized regulatory text is thin; manual validation may be required.")

    pdf_text_hash = stable_normalized_hash(pdf_text) or None
    metadata = {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "source_id": source_id,
        "source_name": source.get("name", ""),
        "official_url": source.get("url", ""),
        "final_url": result.get("final_url") or result.get("url") or source.get("url", ""),
        "raw_chars": len(combined_raw_text),
        "normalized_chars": len(normalized_text),
        "pdf_extracted_chars": pdf_chars,
    }
    snapshots = _write_snapshots(
        timestamp_utc=timestamp_utc,
        market=market,
        source_id=source_id,
        run_id=run_id,
        raw_text=combined_raw_text,
        normalized_text=normalized_text,
        pdf_text=pdf_text,
        metadata=metadata,
    )

    return {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "market": market,
        "jurisdiction": market,
        "source_id": source_id,
        "source_name": source.get("name", ""),
        "category": source.get("category", ""),
        "official_url": source.get("url", ""),
        "final_url": result.get("final_url") or result.get("url") or source.get("url", ""),
        "access_status": access_status,
        "fetch_method": fetch_method,
        "extraction_quality": quality,
        "extracted_chars": extracted_chars,
        "raw_chars": len(combined_raw_text),
        "normalized_chars": len(normalized_text),
        "raw_hash": _raw_hash(combined_raw_text),
        "normalized_hash": stable_normalized_hash(combined_raw_text) or None,
        "pdf_text_hash": pdf_text_hash,
        "pdf_links_count": int(doc_info.get("pdf_links_count") or 0),
        "pdf_extracted_chars": pdf_chars,
        "content_hash": stable_content_hash(page_text + "\n\n" + pdf_text),
        **snapshots,
        "title": result.get("title"),
        "publication_date": result.get("publication_date"),
        "limitations_notes": "; ".join(n for n in notes if n),
        "error": result.get("error") or (result.get("reason") if result.get("status") != "ok" else None),
        "pipeline_version": "4.2",
        "normalization_version": "1.0",
    }


def restricted_record(
    *,
    run_id: str,
    source: dict,
    limitations_notes: list[str],
) -> dict:
    timestamp_utc = now_utc()
    market = str(source.get("jurisdiction") or "").upper()
    source_id = make_source_id(source)
    metadata = {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "source_id": source_id,
        "source_name": source.get("name", ""),
        "official_url": source.get("url", ""),
        "restricted": True,
    }
    snapshots = _write_snapshots(
        timestamp_utc=timestamp_utc,
        market=market,
        source_id=source_id,
        run_id=run_id,
        raw_text="",
        normalized_text="",
        pdf_text="",
        metadata=metadata,
    )
    return {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "market": market,
        "jurisdiction": market,
        "source_id": source_id,
        "source_name": source.get("name", ""),
        "category": source.get("category", ""),
        "official_url": source.get("url", ""),
        "final_url": source.get("url", ""),
        "access_status": "restricted",
        "fetch_method": "failed",
        "extraction_quality": "FAILED",
        "extracted_chars": 0,
        "raw_chars": 0,
        "normalized_chars": 0,
        "raw_hash": None,
        "normalized_hash": None,
        "pdf_text_hash": None,
        "pdf_links_count": 0,
        "pdf_extracted_chars": 0,
        "content_hash": None,
        **snapshots,
        "title": None,
        "publication_date": None,
        "limitations_notes": "; ".join(limitations_notes),
        "error": "Source is marked restricted/blocked in sources.json.",
        "pipeline_version": "4.2",
        "normalization_version": "1.0",
    }


def _combine_text(page_text: str, pdf_text: str) -> str:
    if page_text and pdf_text:
        return f"{page_text.strip()}\n\n--- PDF TEXT ---\n\n{pdf_text.strip()}"
    return (page_text or pdf_text or "").strip()


def _quality_from_chars(chars: int) -> str:
    if chars >= 2_000:
        return "GOOD"
    if chars >= 800:
        return "MEDIUM"
    if chars > 0:
        return "THIN"
    return "FAILED"


def render_history_terminal(
    *,
    market: str = "AE",
    source_filter: str | None = None,
    limit: int = 20,
) -> None:
    latest = list(latest_runs(market, source_filter).values())
    latest.sort(key=lambda r: r.get("timestamp_utc", ""), reverse=True)
    rows = latest[:limit]

    print(f"\nStatuteProof — Source History  {market.upper()}")
    print("─" * 96)
    if not rows:
        print("No source run records found.")
        return
    for rec in rows:
        name = rec.get("source_name", "source")[:42]
        ts = rec.get("timestamp_utc", "unknown")
        quality = rec.get("extraction_quality", "UNKNOWN")
        chars = int(rec.get("extracted_chars") or 0)
        norm_chars = int(rec.get("normalized_chars") or 0)
        pdf_chars = int(rec.get("pdf_extracted_chars") or 0)
        change = rec.get("change_status", "UNKNOWN")
        limit_note = rec.get("limitations_notes") or rec.get("error") or ""
        norm_hash = str(rec.get("normalized_hash") or "")[:10] or "—"
        raw_hash = str(rec.get("raw_hash") or "")[:10] or "—"
        snap = rec.get("snapshot_normalized_path") or rec.get("snapshot_raw_path") or ""
        print(
            f"{ts}  {quality:<7} {change:<12} "
            f"{chars:>7,}c n={norm_chars:>7,} h={norm_hash:<10} "
            f"raw={raw_hash:<10} + {pdf_chars:>7,}pdf  {name}"
        )
        if limit_note:
            print(f"  - {limit_note[:140]}")
        if snap:
            print(f"  - snapshot: {snap}")
        if rec.get("diff_json_path"):
            print(f"  - diff: {rec.get('diff_json_path')}")
        if rec.get("proof_block_path"):
            print(f"  - proof: {rec.get('proof_block_path')}")
