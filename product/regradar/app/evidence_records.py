"""Canonical evidence-record validation and risk-brief eligibility gates.

This module is deliberately separate from source snapshot proof. A saved
``proof.json`` can support source activation review, but it is not enough to
support a customer risk brief.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


_BASE_DIR = Path(__file__).parent.parent
_SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
_ALLOWED_RUN_STATUSES = {"FIRST_SEEN", "UNCHANGED", "CHANGED", "FAILED", "QUALITY_DROP"}
_BLOCKED_RUN_STATUSES = {"FAILED", "QUALITY_DROP"}
_NON_BRIEF_PROOF_NAMES = {"proof.json"}


class EvidenceRecordError(ValueError):
    """Raised when an input is not a canonical evidence record."""


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
            _resolve_existing_path(diff_path, root, errors, "change.diff_path/files.diff_path")

    if raw_content_path is None:
        # Keep this variable used for the required-path side effect above.
        pass

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
    if review_status not in {"approved", "not_required"}:
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
        "review_status": review["review_status"],
        "review_reason": review["review_reason"],
    }


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
