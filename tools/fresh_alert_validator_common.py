"""Shared checks for registry-backed fresh-alert source validators."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGRADAR_ROOT = ROOT / "product/regradar"
SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")


def resolve_regradar_path(value: str, regradar_root: Path = REGRADAR_ROOT) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    parts = path.parts
    if len(parts) >= 2 and parts[0] == "product" and parts[1] == "regradar":
        return ROOT / path
    return regradar_root / path


def normalized_sha256(value: str) -> str:
    folded = value.strip().lower()
    if folded.startswith("sha256:"):
        return folded.removeprefix("sha256:")
    return folded


def _parse_int_field(source: dict, field: str, label: str, default: int) -> tuple[int, list[str]]:
    raw = source.get(field)
    if raw in (None, ""):
        return default, []
    if isinstance(raw, bool):
        return default, [f"{label}: {field} must be an integer"]
    try:
        return int(raw), []
    except (TypeError, ValueError):
        return default, [f"{label}: {field} must be an integer"]


def validate_baseline_runs(source: dict, label: str) -> list[str]:
    failures: list[str] = []
    baseline_completed, field_failures = _parse_int_field(
        source, "baseline_runs_completed", label, 0
    )
    failures.extend(field_failures)
    baseline_required, field_failures = _parse_int_field(
        source, "baseline_runs_required", label, 2
    )
    failures.extend(field_failures)
    if failures:
        return failures

    baseline_required = max(2, baseline_required)
    if baseline_completed < baseline_required:
        failures.append(f"{label}: baseline {baseline_completed}/{baseline_required} is incomplete")
    return failures


def validate_fresh_alert_artifacts(
    source: dict,
    regradar_root: Path = REGRADAR_ROOT,
) -> list[str]:
    """Return evidence artifact failures for a fresh_alert source."""

    source_id = str(source.get("source_id") or "").strip()
    label = source_id or str(source.get("url") or "<missing source_id>")
    failures: list[str] = []

    if not source_id:
        failures.append(f"{label}: fresh_alert missing source_id")

    proof_value = str(source.get("proof_path") or "").strip()
    normalized_value = str(source.get("normalized_text_path") or "").strip()
    hash_value = str(source.get("normalized_hash") or "").strip()

    proof_path = resolve_regradar_path(proof_value, regradar_root) if proof_value else None
    normalized_path = (
        resolve_regradar_path(normalized_value, regradar_root) if normalized_value else None
    )

    if not proof_value:
        failures.append(f"{label}: fresh_alert lacks proof_path")
    elif not proof_path or not proof_path.is_file():
        failures.append(f"{label}: proof_path does not exist ({proof_value})")

    if not normalized_value:
        failures.append(f"{label}: fresh_alert lacks normalized_text_path")
    elif not normalized_path or not normalized_path.is_file():
        failures.append(f"{label}: normalized_text_path does not exist ({normalized_value})")

    if not hash_value:
        failures.append(f"{label}: fresh_alert lacks normalized_hash")
    elif not SHA256_RE.fullmatch(hash_value.lower()):
        failures.append(f"{label}: normalized_hash must be a SHA-256 hex digest")
    elif normalized_path and normalized_path.is_file():
        actual_hash = hashlib.sha256(normalized_path.read_bytes()).hexdigest()
        if normalized_sha256(hash_value) != actual_hash:
            failures.append(f"{label}: normalized_hash does not match normalized_text_path")

    if proof_path and proof_path.is_file():
        try:
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append(f"{label}: proof_path is not valid JSON")
        else:
            for field in ("source_id", "snapshot_normalized_path", "normalized_hash"):
                if not str(proof.get(field) or "").strip():
                    failures.append(f"{label}: proof_path missing {field}")
            proof_source_id = str(proof.get("source_id") or "").strip()
            if source_id and proof_source_id and proof_source_id != source_id:
                failures.append(f"{label}: proof_path source_id does not match registry")
            proof_normalized_path = str(proof.get("snapshot_normalized_path") or "").strip()
            if proof_normalized_path and proof_normalized_path != normalized_value:
                failures.append(
                    f"{label}: proof_path snapshot_normalized_path does not match registry"
                )
            proof_hash = str(proof.get("normalized_hash") or "").strip()
            if proof_hash and hash_value and normalized_sha256(proof_hash) != normalized_sha256(hash_value):
                failures.append(f"{label}: proof_path normalized_hash does not match registry")

    return failures
