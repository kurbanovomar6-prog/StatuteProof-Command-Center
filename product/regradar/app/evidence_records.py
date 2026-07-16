"""Canonical evidence-record validation and risk-brief eligibility gates.

This module is deliberately separate from source snapshot proof. A saved
``proof.json`` can support source activation review, but it is not enough to
support a customer risk brief.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.record_hashing import RECORD_HASH_METHOD, canonical_record_hash
from app.text_quality import is_mostly_unreadable


_BASE_DIR = Path(__file__).parent.parent
_SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
_ALLOWED_RUN_STATUSES = {"FIRST_SEEN", "UNCHANGED", "CHANGED", "FAILED", "QUALITY_DROP"}
_BLOCKED_RUN_STATUSES = {"FAILED", "QUALITY_DROP"}
_NON_BRIEF_PROOF_NAMES = {"proof.json"}
_REVIEW_DECISIONS = {"approved", "rejected", "blocked"}
_CANONICAL_REVIEW_FILE = Path("data") / "evidence_reviews" / "canonical_evidence_reviews.jsonl"


class EvidenceRecordError(ValueError):
    """Raised when an input is not a canonical evidence record."""


class EvidenceRecordExistsError(EvidenceRecordError):
    """Raised when a canonical evidence record already exists for a run.

    A distinct type so callers can treat the benign idempotency case ("this
    run is already sealed") differently from a real integrity failure —
    substring-matching the message would also swallow unrelated errors that
    happen to contain the same words.
    """


def create_canonical_evidence_record(
    run_record: dict[str, Any],
    previous_run: dict[str, Any] | None = None,
    *,
    base_dir: Path | None = None,
    review_status: str = "pending",
    human_review_required: bool = True,
    review_reason: str = "Customer-facing brief requires human review.",
) -> dict[str, Any]:
    """Create an append-only canonical evidence record from a saved source run.

    Source snapshot proof is an input to this function, not the customer-facing
    evidence object. The writer copies verified artifacts into the canonical
    ``evidence/`` tree and rejects incomplete, failed, no-proof, or hash-mismatch
    runs before any risk-brief gate can consume them.
    """

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    if not isinstance(run_record, dict):
        raise EvidenceRecordError("run_record must be a JSON object.")

    run_status = _run_status(run_record)
    if run_status in _BLOCKED_RUN_STATUSES:
        raise EvidenceRecordError(f"Run status {run_status} is not eligible for canonical evidence.")
    if run_status not in {"FIRST_SEEN", "UNCHANGED", "CHANGED"}:
        raise EvidenceRecordError(f"Run status {run_status or '<missing>'} is not eligible for canonical evidence.")

    run_id = _required_run_text(run_record, "run_id")
    source_id = _required_run_text(run_record, "source_id")
    source_name = _required_run_text(run_record, "source_name")
    official_url = _required_run_text(run_record, "official_url")
    timestamp = str(run_record.get("timestamp_utc") or run_record.get("run_at") or run_record.get("timestamp") or "").strip()
    if not timestamp:
        raise EvidenceRecordError("timestamp_utc is required for canonical evidence.")

    proof_path = _resolve_input_artifact(run_record.get("proof_block_path"), root, "proof_block_path")
    if proof_path.name != "proof.json":
        raise EvidenceRecordError("proof_block_path must point to a saved source snapshot proof.json.")

    raw_input = _resolve_input_artifact(run_record.get("snapshot_raw_path"), root, "snapshot_raw_path")
    current_input = _resolve_input_artifact(
        run_record.get("snapshot_normalized_path"),
        root,
        "snapshot_normalized_path",
    )
    metadata_input = _resolve_input_artifact(
        run_record.get("snapshot_metadata_path"),
        root,
        "snapshot_metadata_path",
    )

    expected_current_hash = _normalize_sha256(run_record.get("normalized_hash"), "normalized_hash")
    actual_current_hash = _sha256_path(current_input)
    if expected_current_hash != f"sha256:{actual_current_hash}":
        # EV-3: the LIVE pipeline stores a flavor-B normalized_hash
        # (stable_content_hash(normalize(...)), whitespace-collapsed) while intake
        # stores flavor-A (sha256(normalized.txt)). Both are legitimate hashes of
        # THIS same normalized.txt, so accept either — otherwise a live CHANGED run
        # (the kind that fires a customer alert) can NEVER be certified and gets no
        # sealed evidence record. The sealed content.current_hash below stays
        # flavor-A (sha256 of the file), so the verifier contract and the sealed
        # format are byte-identical; this only relaxes the ACCEPTANCE gate. The
        # mojibake/empty-content quarantine still runs, so garbage is never sealed.
        from app.text_normalization import stable_content_hash as _sch
        _flavor_b = _sch(current_input.read_text(encoding="utf-8", errors="replace"))
        if not (_flavor_b and f"sha256:{_flavor_b}" == expected_current_hash):
            raise EvidenceRecordError("normalized_hash does not match snapshot_normalized_path.")

    if run_status != "FIRST_SEEN" and previous_run is None:
        previous_run = _find_previous_evidence_run(run_record, root)
    previous_input: Path | None = None
    previous_hash = ""
    if run_status != "FIRST_SEEN":
        if previous_run is None:
            raise EvidenceRecordError("previous_run is required for non-FIRST_SEEN canonical evidence.")
        previous_input = _resolve_input_artifact(
            previous_run.get("snapshot_normalized_path"),
            root,
            "previous_run.snapshot_normalized_path",
        )
        previous_hash = f"sha256:{_sha256_path(previous_input)}"
        expected_previous_hash = previous_run.get("normalized_hash")
        if expected_previous_hash:
            _exp_prev = _normalize_sha256(expected_previous_hash, "previous_run.normalized_hash")
            if _exp_prev != previous_hash:
                # EV-3 (symmetry): the PREVIOUS run's normalized_hash is also the
                # live-pipeline flavor-B. Every CHANGED/UNCHANGED run resolves a
                # previous run, so without this fallback the alert-firing case still
                # never certifies (the current-run fallback above is not enough).
                # Accept flavor-B here too; the sealed content.previous_hash stays
                # flavor-A (sha256 of the file), so the sealed format is unchanged.
                from app.text_normalization import stable_content_hash as _sch_prev
                _prev_flavor_b = _sch_prev(previous_input.read_text(encoding="utf-8", errors="replace"))
                if not (_prev_flavor_b and f"sha256:{_prev_flavor_b}" == _exp_prev):
                    raise EvidenceRecordError("previous_run.normalized_hash does not match previous normalized snapshot.")

    regulator_slug, regulator_name = _regulator_for_run(run_record)
    record_dir = root / "evidence" / regulator_slug / source_id / run_id
    record_path = record_dir / "evidence-record.json"
    if record_path.exists():
        raise EvidenceRecordExistsError(f"Canonical evidence record already exists: {_relative_or_absolute(record_path, root)}")
    if record_dir.exists() and any(record_dir.iterdir()):
        raise EvidenceRecordError(f"Canonical evidence record directory is not empty: {_relative_or_absolute(record_dir, root)}")

    try:
        record_dir.mkdir(parents=True, exist_ok=False)
        raw_path = _copy_artifact(raw_input, record_dir / "raw.txt")
        snapshot_path = _copy_artifact(raw_input, record_dir / "snapshot.txt")
        current_path = _copy_artifact(current_input, record_dir / "current.normalized.txt")
        metadata_path = _copy_artifact(metadata_input, record_dir / "metadata.json")
        previous_path = _copy_artifact(previous_input, record_dir / "previous.normalized.txt") if previous_input else None

        # Integrity is not just "the hash matches the bytes" — undecodable
        # content (the VARA mojibake incident, 2026-07-10) hashes perfectly
        # and would otherwise be stamped VERIFIED. Refuse certification when
        # the normalized content the customer brief would rest on is
        # saturated with replacement/control characters (or empty). Both the
        # current AND previous normalized snapshots must be checked: a CHANGED
        # record with clean current but mojibake previous still bakes garbled
        # previous-side lines into the customer diff, so an unreadable previous
        # side must quarantine too. Quarantine the record with a clear reason
        # instead of raising, so the failure is auditable and never
        # brief-eligible.
        unreadable_reason = _normalized_content_integrity_reason(
            current_path, side="current"
        ) or _normalized_content_integrity_reason(previous_path, side="previous")
        if unreadable_reason is not None:
            record = _build_quarantined_record(
                source_id=source_id,
                run_id=run_id,
                run_status=run_status,
                timestamp=timestamp,
                source_name=source_name,
                official_url=official_url,
                regulator_name=regulator_name,
                current_path=current_path,
                raw_path=raw_path,
                snapshot_path=snapshot_path,
                metadata_path=metadata_path,
                run_record=run_record,
                root=root,
                reason=unreadable_reason,
                human_review_required=human_review_required,
            )
            record_path.write_text(
                json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            return record

        diff_path, lines_added, lines_removed = _canonical_diff_artifact(
            run_record=run_record,
            previous_path=previous_path,
            current_path=current_path,
            record_dir=record_dir,
            root=root,
        )

        record = {
            "schema_version": "2.0",
            "record_id": _canonical_record_id(source_id, run_id),
            "record_status": "complete",
            "source": {
                "source_id": source_id,
                "regulator": regulator_name,
                "official_url": official_url,
                "source_name": source_name,
            },
            "run": {
                "run_id": run_id,
                "timestamp": timestamp,
                "status": run_status,
            },
            "content": {
                "current_hash": f"sha256:{_sha256_path(current_path)}",
                # Additive self-seal input: the raw source bytes' own hash lives
                # INSIDE content so it is covered by record_hash below, and so the
                # public verifier can match a submitted raw.txt against the record.
                "raw_hash": f"sha256:{_sha256_path(raw_input)}",
                "raw_content_path": _relative_or_absolute(raw_path, root),
                "normalized_current_path": _relative_or_absolute(current_path, root),
                # Seal the WHEN and WHERE of capture. These duplicate run.timestamp
                # and source.official_url, but placing them INSIDE content brings
                # them under record_hash, so the capture time and source URL can no
                # longer be altered without breaking the seal. The public verifier
                # cross-checks the display copies against these sealed values.
                # Additive — legacy records predate them and stay valid.
                "captured_at": timestamp,
                "source_url": official_url,
            },
            "change": {
                "summary": _change_summary(run_record, run_status),
                "lines_added": lines_added,
                "lines_removed": lines_removed,
            },
            "files": {
                "snapshot_path": _relative_or_absolute(snapshot_path, root),
                "raw_path": _relative_or_absolute(raw_path, root),
                "normalized_path": _relative_or_absolute(current_path, root),
                "metadata_path": _relative_or_absolute(metadata_path, root),
            },
            "integrity": {
                "hash_verified": True,
                "integrity_status": "VERIFIED",
                "verified_at": _utc_now(),
            },
            "review": {
                "human_review_required": bool(human_review_required),
                "review_status": str(review_status or "").strip() or "pending",
                "review_reason": str(review_reason or "").strip() or "Customer-facing brief requires human review.",
            },
        }
        if previous_path is not None:
            record["content"]["previous_hash"] = previous_hash
            record["content"]["normalized_previous_path"] = _relative_or_absolute(previous_path, root)
            record["files"]["previous_path"] = _relative_or_absolute(previous_path, root)
        if diff_path is not None:
            rel_diff = _relative_or_absolute(diff_path, root)
            record["change"]["diff_path"] = rel_diff
            record["files"]["diff_path"] = rel_diff
            # Seal the redline: hash the stored diff.txt and place it INSIDE
            # content, so record_hash below covers it and any later in-place edit
            # to diff.txt is detectable by re-hashing against this value. Additive
            # — legacy records predate diff_hash and stay valid (the verifier only
            # checks it when present).
            record["content"]["diff_hash"] = f"sha256:{_sha256_path(diff_path)}"

        # Seal the record with its own fingerprint LAST, once the content block is
        # fully built (current_hash + raw_hash + paths, and the previous-side
        # fields when present). record_hash covers the whole content block, so any
        # later in-place edit to content makes the recomputed hash diverge. This is
        # additive: legacy records predate these two fields and stay valid.
        record["record_hash"] = f"sha256:{canonical_record_hash(record['content'])}"
        record["record_hash_method"] = RECORD_HASH_METHOD

        validation = validate_evidence_record(record, base_dir=root)
        if not validation["valid"]:
            raise EvidenceRecordError("; ".join(validation["errors"]))
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        if record_dir.exists() and not record_path.exists():
            shutil.rmtree(record_dir)
        raise

    return record


def validate_evidence_record(record: dict[str, Any], base_dir: Path | None = None) -> dict[str, Any]:
    """Validate a canonical evidence-record.json object.

    Returns a dict rather than raising so validators and product gates can show
    a precise blocked reason without accidentally generating a brief.
    """

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    errors: list[str] = []

    if not isinstance(record, dict):
        return {"valid": False, "errors": ["Evidence record must be a JSON object."]}

    _require_equal(record, "schema_version", "2.0", errors)
    _require_equal(record, "record_status", "complete", errors)
    _require_text(record, "record_id", errors)

    source = _require_dict(record, "source", errors)
    _require_text(source, "source_id", errors, "source.source_id")
    _require_text(source, "regulator", errors, "source.regulator")
    _require_text(source, "official_url", errors, "source.official_url")
    _require_text(source, "source_name", errors, "source.source_name")

    run = _require_dict(record, "run", errors)
    _require_text(run, "run_id", errors, "run.run_id")
    _require_text(run, "timestamp", errors, "run.timestamp")
    run_status = _require_text(run, "status", errors, "run.status")
    if run_status and run_status not in _ALLOWED_RUN_STATUSES:
        errors.append(f"run.status is not supported: {run_status}")
    if run_status in _BLOCKED_RUN_STATUSES:
        errors.append(f"Run status {run_status} is not brief-eligible.")

    content = _require_dict(record, "content", errors)
    current_hash = _require_text(content, "current_hash", errors, "content.current_hash")
    if current_hash and not _SHA256_RE.match(current_hash):
        errors.append("content.current_hash must be sha256:<64 lowercase hex>.")

    raw_content_path = _require_path(content, "raw_content_path", root, errors, "content.raw_content_path")
    # EV-1: enforce raw_hash. raw_content_path was required to EXIST but never
    # re-hashed, so raw.txt could be swapped post-seal (for bytes that normalize
    # identically) with the chain still verifying. content.raw_hash is sealed under
    # record_hash — re-check it here. Additive: legacy records without raw_hash are
    # unaffected.
    _raw_hash = str(content.get("raw_hash") or "").strip()
    if raw_content_path is not None and _raw_hash and f"sha256:{_sha256_path(raw_content_path)}" != _raw_hash:
        errors.append("content.raw_hash does not match raw_content_path (raw evidence tampered).")
    normalized_current_path = _require_path(
        content,
        "normalized_current_path",
        root,
        errors,
        "content.normalized_current_path",
    )

    if normalized_current_path is not None and current_hash:
        recomputed = _sha256_path(normalized_current_path)
        if f"sha256:{recomputed}" != current_hash:
            errors.append("content.current_hash does not match normalized_current_path.")

    # A matching hash over mojibake (or over empty content) is still not
    # readable regulatory text. Report the integrity problem so no gate can
    # treat a certified hash of undecodable bytes as brief-eligible (VARA
    # mojibake incident).
    current_unreadable_reason = (
        _normalized_content_integrity_reason(normalized_current_path, side="current")
        if normalized_current_path is not None
        else None
    )
    if current_unreadable_reason is not None:
        errors.append(current_unreadable_reason)

    if run_status and run_status != "FIRST_SEEN":
        previous_hash = _require_text(content, "previous_hash", errors, "content.previous_hash")
        if previous_hash and not _SHA256_RE.match(previous_hash):
            errors.append("content.previous_hash must be sha256:<64 lowercase hex>.")
        previous_path = _require_path(
            content,
            "normalized_previous_path",
            root,
            errors,
            "content.normalized_previous_path",
        )
        if previous_path is not None and previous_hash and f"sha256:{_sha256_path(previous_path)}" != previous_hash:
            errors.append("content.previous_hash does not match normalized_previous_path.")
        # The previous normalized snapshot feeds the customer-facing diff just
        # as the current side does. A CHANGED record with clean current but
        # undecodable/empty previous still certifies VERIFIED and bakes garbled
        # previous-side lines into the diff, so the previous side must fail
        # integrity too, naming which side broke.
        previous_unreadable_reason = (
            _normalized_content_integrity_reason(previous_path, side="previous")
            if previous_path is not None
            else None
        )
        if previous_unreadable_reason is not None:
            errors.append(previous_unreadable_reason)

    change = _require_dict(record, "change", errors)
    _require_text(change, "summary", errors, "change.summary")
    _require_number(change, "lines_added", errors, "change.lines_added")
    _require_number(change, "lines_removed", errors, "change.lines_removed")

    files = _require_dict(record, "files", errors)
    _require_path(files, "snapshot_path", root, errors, "files.snapshot_path")
    _require_path(files, "raw_path", root, errors, "files.raw_path")
    _require_path(files, "normalized_path", root, errors, "files.normalized_path")
    _require_path(files, "metadata_path", root, errors, "files.metadata_path")
    if run_status and run_status != "FIRST_SEEN":
        _require_path(files, "previous_path", root, errors, "files.previous_path")
    if run_status == "CHANGED":
        diff_path = str(change.get("diff_path") or files.get("diff_path") or "").strip()
        if not diff_path:
            errors.append("CHANGED records require change.diff_path or files.diff_path.")
        else:
            diff_resolved = _resolve_existing_path(diff_path, root, errors, "change.diff_path/files.diff_path")
            # EV-1: enforce the sealed redline. content.diff_hash is hashed into
            # record_hash at creation, but validate only checked diff.txt EXISTED —
            # so the one artifact a customer actually reads could be edited in place
            # and still render as "sealed". Re-hash it here. Additive: legacy
            # records without diff_hash are unaffected.
            _diff_hash = str(content.get("diff_hash") or "").strip()
            if diff_resolved is not None and _diff_hash and f"sha256:{_sha256_path(diff_resolved)}" != _diff_hash:
                errors.append("content.diff_hash does not match the stored diff file (redline tampered).")

    integrity = _require_dict(record, "integrity", errors)
    if integrity.get("hash_verified") is not True:
        errors.append("integrity.hash_verified must be true.")
    if integrity.get("integrity_status") != "VERIFIED":
        errors.append("integrity.integrity_status must be VERIFIED.")
    _require_text(integrity, "verified_at", errors, "integrity.verified_at")

    review = _require_dict(record, "review", errors)
    if "human_review_required" not in review:
        errors.append("review.human_review_required is required.")
    _require_text(review, "review_status", errors, "review.review_status")
    _require_text(review, "review_reason", errors, "review.review_reason")

    # Additive self-seal check (content-sha256-v1). Records written after this
    # change carry a top-level record_hash over their content block; recompute it
    # through the SAME shared function the writer used and flag any mismatch.
    # Legacy records predate BOTH fields and must stay valid, so this is a strict
    # no-op unless the method marker AND the record_hash are both present.
    if record.get("record_hash_method") == RECORD_HASH_METHOD and record.get("record_hash"):
        content_block = record.get("content")
        if isinstance(content_block, dict):
            expected = canonical_record_hash(content_block)
            stored = str(record.get("record_hash") or "").strip().lower().removeprefix("sha256:")
            if stored != expected:
                errors.append("record_hash does not match content")

    return {"valid": not errors, "errors": errors}


def build_risk_brief_inputs(evidence_record_id_or_path: str, base_dir: Path | None = None) -> dict[str, Any]:
    """Return brief input fields only for complete canonical evidence records."""

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    try:
        record, record_path = load_evidence_record(evidence_record_id_or_path, base_dir=root)
    except EvidenceRecordError as exc:
        return {"eligible": False, "blocked_reason": str(exc)}

    validation = validate_evidence_record(record, base_dir=root)
    if not validation["valid"]:
        return {
            "eligible": False,
            "evidence_record_id": record.get("record_id") or str(evidence_record_id_or_path),
            "blocked_reason": "; ".join(validation["errors"]),
            "validation_errors": validation["errors"],
        }

    source = record["source"]
    run = record["run"]
    content = record["content"]
    change = record["change"]
    files = record["files"]
    review = record["review"]
    review_status = str(review.get("review_status") or "").strip()
    external_review = latest_canonical_evidence_review(record["record_id"], base_dir=root)
    effective_review_status = review_status
    effective_review_reason = str(review.get("review_reason") or "").strip()
    if review_status not in {"approved", "not_required"} and external_review:
        current_record_hash = f"sha256:{_sha256_path(record_path)}"
        reviewed_record_hash = str(external_review.get("evidence_record_hash") or "").strip().lower()
        if reviewed_record_hash != current_record_hash:
            return {
                "eligible": False,
                "evidence_record_id": record["record_id"],
                "blocked_reason": "Canonical evidence record external review hash no longer matches current record.",
            }
        decision = str(external_review.get("decision") or "").strip()
        if decision == "approved":
            effective_review_status = "approved"
            effective_review_reason = str(external_review.get("note") or "").strip()
        elif decision in {"rejected", "blocked"}:
            return {
                "eligible": False,
                "evidence_record_id": record["record_id"],
                "blocked_reason": (
                    "Canonical evidence record external review decision is "
                    f"{decision}: {external_review.get('note') or '<no note>'}."
                ),
            }
    if effective_review_status not in {"approved", "not_required"}:
        return {
            "eligible": False,
            "evidence_record_id": record["record_id"],
            "blocked_reason": (
                "Canonical evidence record review_status must be approved or not_required "
                f"before customer brief use; got {review_status!r}."
            ),
        }
    return {
        "eligible": True,
        "blocked_reason": "",
        "evidence_record_id": record["record_id"],
        "evidence_record_path": _relative_or_absolute(record_path, root),
        "source_id": source["source_id"],
        "source_name": source["source_name"],
        "regulator": source["regulator"],
        "official_url": source["official_url"],
        "run_id": run["run_id"],
        "run_status": run["status"],
        "run_timestamp": run["timestamp"],
        "current_hash": content["current_hash"],
        "previous_hash": content.get("previous_hash") or "",
        "diff_path": change.get("diff_path") or files.get("diff_path") or "",
        "raw_snapshot_path": files["snapshot_path"],
        "raw_content_path": content["raw_content_path"],
        "normalized_current_path": content["normalized_current_path"],
        "human_review_required": review["human_review_required"],
        "review_status": effective_review_status,
        "review_reason": effective_review_reason,
        "external_review_id": (external_review or {}).get("review_id", ""),
    }


def canonical_evidence_review_store_path(base_dir: Path | None = None) -> Path:
    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    return root / _CANONICAL_REVIEW_FILE


def list_canonical_evidence_records(
    *,
    base_dir: Path | None = None,
    review_file: Path | None = None,
) -> list[dict[str, Any]]:
    """Return canonical evidence record summaries with latest external review status."""

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    rows: list[dict[str, Any]] = []
    evidence_root = root / "evidence"
    if not evidence_root.exists():
        return rows
    for path in sorted(evidence_root.glob("**/evidence-record.json")):
        try:
            record = _read_json_object(path)
        except EvidenceRecordError:
            continue
        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        run = record.get("run") if isinstance(record.get("run"), dict) else {}
        review = record.get("review") if isinstance(record.get("review"), dict) else {}
        record_id = str(record.get("record_id") or "").strip()
        latest = latest_canonical_evidence_review(record_id, base_dir=root, review_file=review_file) if record_id else None
        rows.append(
            {
                "record_id": record_id,
                "record_path": _relative_or_absolute(path, root),
                "source_id": source.get("source_id", ""),
                "regulator": source.get("regulator", ""),
                "run_id": run.get("run_id", ""),
                "run_status": run.get("status", ""),
                "record_review_status": review.get("review_status", ""),
                "latest_review_decision": (latest or {}).get("decision", ""),
                "latest_review_id": (latest or {}).get("review_id", ""),
                "reviewed_at": (latest or {}).get("reviewed_at", ""),
            }
        )
    return rows


def record_canonical_evidence_review(
    evidence_record_id_or_path: str,
    *,
    decision: str,
    reviewer: str,
    note: str,
    base_dir: Path | None = None,
    review_file: Path | None = None,
) -> dict[str, Any]:
    """Append a human review decision for a complete canonical evidence record.

    The canonical ``evidence-record.json`` remains immutable. Customer brief
    gates may use this append-only review journal as the approval signal.
    """

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    normalized_decision = str(decision or "").strip().lower()
    if normalized_decision not in _REVIEW_DECISIONS:
        raise EvidenceRecordError("decision must be one of: approved, rejected, blocked")
    reviewer_name = str(reviewer or "").strip()
    if not reviewer_name:
        raise EvidenceRecordError("reviewer is required for canonical evidence review.")
    review_note = str(note or "").strip()
    if not review_note:
        raise EvidenceRecordError("note is required for canonical evidence review.")

    record, record_path = load_evidence_record(evidence_record_id_or_path, base_dir=root)
    validation = validate_evidence_record(record, base_dir=root)
    if not validation["valid"]:
        raise EvidenceRecordError("; ".join(validation["errors"]))

    reviewed_at = _utc_now()
    record_id = str(record.get("record_id") or "").strip()
    record_hash = _sha256_path(record_path)
    review_id = "evrev_" + hashlib.sha256(
        f"{record_id}|{normalized_decision}|{reviewer_name}|{reviewed_at}|{record_hash}".encode("utf-8")
    ).hexdigest()[:20]
    row = {
        "schema_version": "1.0",
        "review_id": review_id,
        "evidence_record_id": record_id,
        "evidence_record_path": _relative_or_absolute(record_path, root),
        "evidence_record_hash": f"sha256:{record_hash}",
        "decision": normalized_decision,
        "reviewer": reviewer_name,
        "note": review_note,
        "reviewed_at": reviewed_at,
        "customer_delivery_approved": False,
    }
    path = review_file or canonical_evidence_review_store_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


def load_canonical_evidence_review_records(
    *,
    base_dir: Path | None = None,
    review_file: Path | None = None,
) -> list[dict[str, Any]]:
    path = review_file or canonical_evidence_review_store_path(base_dir)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def latest_canonical_evidence_review(
    evidence_record_id: str,
    *,
    base_dir: Path | None = None,
    review_file: Path | None = None,
) -> dict[str, Any] | None:
    wanted = str(evidence_record_id or "").strip()
    if not wanted:
        return None
    for row in reversed(load_canonical_evidence_review_records(base_dir=base_dir, review_file=review_file)):
        if str(row.get("evidence_record_id") or "") == wanted:
            return row
    return None


def load_evidence_record(
    evidence_record_id_or_path: str,
    base_dir: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    """Load a canonical evidence record by record_id or evidence-record.json path."""

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    wanted = str(evidence_record_id_or_path or "").strip()
    if not wanted:
        raise EvidenceRecordError("Evidence record ID or path is required.")
    if _looks_like_source_snapshot_proof(wanted):
        raise EvidenceRecordError("Snapshot proof.json is not a canonical evidence record and is not brief-eligible.")

    maybe_path = Path(wanted)
    if maybe_path.suffix.lower() == ".json" or "/" in wanted or "\\" in wanted:
        path = _resolve_candidate_record_path(maybe_path, root)
        if path.name != "evidence-record.json":
            raise EvidenceRecordError("Input JSON is not a canonical evidence record.")
        if path.relative_to(root.resolve()).parts[:1] != ("evidence",):
            raise EvidenceRecordError("Input is not stored under the canonical evidence tree.")
        return _read_json_object(path), path

    matches: list[tuple[dict[str, Any], Path]] = []
    evidence_root = root / "evidence"
    if evidence_root.exists():
        for path in evidence_root.glob("**/evidence-record.json"):
            record = _read_json_object(path)
            if str(record.get("record_id") or "") == wanted:
                matches.append((record, path))

    if not matches:
        raise EvidenceRecordError(f"Canonical evidence record not found: {wanted}")
    if len(matches) > 1:
        raise EvidenceRecordError(f"Multiple canonical evidence records found for: {wanted}")
    return matches[0]


def _require_equal(record: dict[str, Any], key: str, expected: str, errors: list[str]) -> None:
    if record.get(key) != expected:
        errors.append(f"{key} must be {expected}.")


def _require_dict(record: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = record.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object.")
        return {}
    return value


def _require_text(
    record: dict[str, Any],
    key: str,
    errors: list[str],
    label: str | None = None,
) -> str:
    value = str(record.get(key) or "").strip()
    if not value:
        errors.append(f"{label or key} is required.")
    return value


def _require_number(record: dict[str, Any], key: str, errors: list[str], label: str) -> None:
    if not isinstance(record.get(key), int | float):
        errors.append(f"{label} is required.")


def _require_path(
    record: dict[str, Any],
    key: str,
    root: Path,
    errors: list[str],
    label: str,
) -> Path | None:
    value = str(record.get(key) or "").strip()
    if not value:
        errors.append(f"{label} is required.")
        return None
    return _resolve_existing_path(value, root, errors, label)


def _required_run_text(record: dict[str, Any], key: str) -> str:
    value = str(record.get(key) or "").strip()
    if not value:
        raise EvidenceRecordError(f"{key} is required for canonical evidence.")
    return value


def _run_status(record: dict[str, Any]) -> str:
    return str(record.get("change_status") or record.get("status") or "").strip()


def _normalize_sha256(value: Any, label: str) -> str:
    text = str(value or "").strip().lower()
    if not text:
        raise EvidenceRecordError(f"{label} is required for canonical evidence.")
    if re.fullmatch(r"[a-f0-9]{64}", text):
        text = f"sha256:{text}"
    if not _SHA256_RE.match(text):
        raise EvidenceRecordError(f"{label} must be sha256:<64 lowercase hex>.")
    return text


def _resolve_input_artifact(value: Any, root: Path, label: str) -> Path:
    text = str(value or "").strip()
    if not text:
        raise EvidenceRecordError(f"{label} is required for canonical evidence.")
    path = _safe_resolve(Path(text), root)
    if not path.exists():
        raise EvidenceRecordError(f"{label} does not exist: {text}")
    if path.is_dir():
        raise EvidenceRecordError(f"{label} must be a file: {text}")
    return path


def _copy_artifact(src: Path | None, dst: Path) -> Path:
    if src is None:
        raise EvidenceRecordError(f"Cannot copy missing artifact to {dst.name}.")
    if dst.exists():
        raise EvidenceRecordError(f"Canonical evidence artifact already exists: {dst.name}")
    shutil.copyfile(src, dst)
    return dst


def _regulator_for_run(record: dict[str, Any]) -> tuple[str, str]:
    explicit = str(record.get("regulator") or record.get("family") or "").strip()
    source_id = str(record.get("source_id") or "").lower()
    source_name = str(record.get("source_name") or "").lower()
    haystack = f"{explicit.lower()} {source_id} {source_name}"
    mapping = [
        ("cbuae", "CBUAE"),
        ("central-bank", "CBUAE"),
        ("vara", "VARA"),
        ("dfsa", "DFSA"),
        ("adgm-fsra", "ADGM FSRA"),
        ("fsra", "ADGM FSRA"),
        ("adgm", "ADGM"),
        ("difc", "DIFC"),
        ("fiu", "UAE FIU"),
        ("uaefiu", "UAE FIU"),
        ("mof", "UAE Ministry of Finance"),
        ("finance", "UAE Ministry of Finance"),
        ("sca", "SCA"),
        ("fta", "FTA"),
        ("tax", "FTA"),
        ("moj", "UAE Ministry of Justice"),
        ("gazette", "UAE Gazette"),
        ("eocn", "EOCN"),
    ]
    for token, name in mapping:
        if token in haystack:
            return _slugify(name), name
    if explicit:
        return _slugify(explicit), explicit
    market = str(record.get("market") or record.get("jurisdiction") or "unknown").strip().upper() or "UNKNOWN"
    return market.lower(), market


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def _canonical_record_id(source_id: str, run_id: str) -> str:
    seed = re.sub(r"[^A-Za-z0-9_.:-]+", "_", f"{source_id}_{run_id}").strip("_")
    return f"evr_{seed}"


def canonical_record_id(source_id: str, run_id: str) -> str:
    """Public: the canonical evidence ``record_id`` for a (source_id, run_id).

    Canonical evidence records and their human reviews key on this derived id
    (``evr_<source>_<run>``), NOT on the raw ``run_id``. Callers that hold only a
    run_id (e.g. the deadline radar, whose entries store the run_id) must resolve
    through here before looking up a review, or the lookup will never match.
    """
    return _canonical_record_id(source_id, run_id)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _change_summary(record: dict[str, Any], run_status: str) -> str:
    if str(record.get("change_summary") or "").strip():
        return str(record["change_summary"]).strip()
    if str(record.get("limitations_notes") or "").strip():
        return str(record["limitations_notes"]).strip()
    if run_status == "FIRST_SEEN":
        return "First saved official-source snapshot captured for canonical evidence review."
    if run_status == "UNCHANGED":
        return "Saved official-source snapshot matched the previous normalized content."
    return "Saved official-source snapshot changed against the previous normalized content."


def _canonical_diff_artifact(
    *,
    run_record: dict[str, Any],
    previous_path: Path | None,
    current_path: Path,
    record_dir: Path,
    root: Path,
) -> tuple[Path | None, int, int]:
    run_status = _run_status(run_record)
    if run_status != "CHANGED":
        return None, 0, 0

    existing_diff = str(run_record.get("diff_md_path") or run_record.get("diff_json_path") or "").strip()
    diff_path = record_dir / "diff.txt"
    if existing_diff:
        copied = _copy_artifact(_resolve_input_artifact(existing_diff, root, "diff_path"), diff_path)
        text = copied.read_text(encoding="utf-8", errors="replace")
    else:
        if previous_path is None:
            raise EvidenceRecordError("CHANGED canonical evidence requires previous normalized text.")
        previous_lines = previous_path.read_text(encoding="utf-8", errors="replace").splitlines()
        current_lines = current_path.read_text(encoding="utf-8", errors="replace").splitlines()
        import difflib

        diff_lines = list(
            difflib.unified_diff(
                previous_lines,
                current_lines,
                fromfile="previous.normalized.txt",
                tofile="current.normalized.txt",
                lineterm="",
            )
        )
        text = "\n".join(diff_lines) + "\n"
        diff_path.write_text(text, encoding="utf-8")
    lines_added = sum(1 for line in text.splitlines() if line.startswith("+") and not line.startswith("+++"))
    lines_removed = sum(1 for line in text.splitlines() if line.startswith("-") and not line.startswith("---"))
    return diff_path, lines_added, lines_removed


def _normalized_content_integrity_reason(
    path: Path | None, *, side: str = "current"
) -> str | None:
    """Return a clear integrity reason when normalized content is unusable.

    ``side`` names the affected path ("current" or "previous") so the reason
    string tells a reviewer which normalized snapshot failed. Returns ``None``
    for readable content.

    Two conditions fail integrity:

    * Empty / whitespace-only content. ``is_mostly_unreadable("")`` returns
      False, so a zero-length normalized.txt would otherwise hash to a valid
      sha256 and certify VERIFIED with nothing to review. Empty regulatory
      content is not certifiable. (This gate is deliberately local; the shared
      ``is_mostly_unreadable`` contract is unchanged because other callers
      depend on its empty-string behaviour.)
    * A body saturated with replacement / control characters — a mis-decoded
      or binary body (VARA mojibake incident). It hashes perfectly but must
      never be certified VERIFIED.

    Callers treat a non-None reason as an integrity failure.
    """
    field = "normalized_current_path" if side == "current" else "normalized_previous_path"
    if path is None or not path.exists() or path.is_dir():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return (
            f"content.{field} is empty or whitespace-only; "
            "content cannot be certified VERIFIED."
        )
    if is_mostly_unreadable(text):
        return (
            f"content.{field} is saturated with undecodable "
            "characters; content cannot be certified VERIFIED."
        )
    return None


def _build_quarantined_record(
    *,
    source_id: str,
    run_id: str,
    run_status: str,
    timestamp: str,
    source_name: str,
    official_url: str,
    regulator_name: str,
    current_path: Path,
    raw_path: Path,
    snapshot_path: Path,
    metadata_path: Path,
    run_record: dict[str, Any],
    root: Path,
    reason: str,
    human_review_required: bool,
) -> dict[str, Any]:
    """Build a non-VERIFIED quarantine record for undecodable normalized content."""

    return {
        "schema_version": "2.0",
        "record_id": _canonical_record_id(source_id, run_id),
        "record_status": "integrity_error",
        "source": {
            "source_id": source_id,
            "regulator": regulator_name,
            "official_url": official_url,
            "source_name": source_name,
        },
        "run": {
            "run_id": run_id,
            "timestamp": timestamp,
            "status": run_status,
        },
        "content": {
            "current_hash": f"sha256:{_sha256_path(current_path)}",
            "raw_content_path": _relative_or_absolute(raw_path, root),
            "normalized_current_path": _relative_or_absolute(current_path, root),
        },
        "change": {
            "summary": _change_summary(run_record, run_status),
            "lines_added": 0,
            "lines_removed": 0,
        },
        "files": {
            "snapshot_path": _relative_or_absolute(snapshot_path, root),
            "raw_path": _relative_or_absolute(raw_path, root),
            "normalized_path": _relative_or_absolute(current_path, root),
            "metadata_path": _relative_or_absolute(metadata_path, root),
        },
        "integrity": {
            "hash_verified": False,
            "integrity_status": "FAILED",
            "verified_at": _utc_now(),
            "reason": reason,
        },
        "review": {
            "human_review_required": bool(human_review_required),
            "review_status": "quarantined",
            "review_reason": reason,
        },
    }


def _find_previous_evidence_run(record: dict[str, Any], root: Path) -> dict[str, Any] | None:
    run_file = root / "data" / "source_runs" / "source_runs.jsonl"
    if not run_file.exists():
        return None
    source_id = str(record.get("source_id") or "")
    run_id = str(record.get("run_id") or "")
    rows: list[dict[str, Any]] = []
    for line in run_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if parsed.get("source_id") == source_id:
            rows.append(parsed)
    previous: dict[str, Any] | None = None
    for row in rows:
        if row.get("run_id") == run_id:
            break
        if row.get("change_status") not in _BLOCKED_RUN_STATUSES and row.get("snapshot_normalized_path"):
            previous = row
    return previous


def _resolve_existing_path(value: str, root: Path, errors: list[str], label: str) -> Path | None:
    try:
        resolved = _safe_resolve(Path(value), root)
    except EvidenceRecordError as exc:
        errors.append(f"{label}: {exc}")
        return None
    if not resolved.exists():
        errors.append(f"{label} does not exist: {value}")
        return None
    if resolved.name in _NON_BRIEF_PROOF_NAMES or "source_snapshots" in resolved.parts:
        errors.append(f"{label} points to source snapshot proof, not canonical evidence: {value}")
        return None
    return resolved


def _resolve_candidate_record_path(path: Path, root: Path) -> Path:
    resolved = _safe_resolve(path, root)
    if not resolved.exists():
        raise EvidenceRecordError(f"Canonical evidence record not found: {path}")
    if resolved.name in _NON_BRIEF_PROOF_NAMES or "source_snapshots" in resolved.parts:
        raise EvidenceRecordError("Snapshot proof.json is not a canonical evidence record and is not brief-eligible.")
    return resolved


def _safe_resolve(path: Path, root: Path) -> Path:
    root_resolved = root.resolve()
    resolved = path if path.is_absolute() else root / path
    resolved = resolved.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise EvidenceRecordError("Evidence record path is outside the workspace.") from exc
    return resolved


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceRecordError(f"Evidence record JSON is invalid: {path}") from exc
    if not isinstance(data, dict):
        raise EvidenceRecordError("Evidence record JSON must be an object.")
    return data


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _looks_like_source_snapshot_proof(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return normalized.endswith("/proof.json") or normalized == "proof.json" or "/source_snapshots/" in normalized
