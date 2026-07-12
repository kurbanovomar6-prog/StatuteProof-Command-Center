"""Sealed evidence-record linkage for routed alerts (additive ``proof`` block).

Every routing/preview match may carry a ``proof`` block that binds the alert
to its canonical evidence record so a customer can verify the alert
independently:

    {
        "evidence_record_id": "evr_<source>_<run>",
        "record_hash": "sha256:<64 hex>",   # the record's self-seal
        "run_id": "<run id>",
        "diff_available": bool,             # a stored diff artifact exists
        "normalized_hash": "sha256:<64 hex>",  # content.current_hash
    }

Scope honesty: this is hash integrity of the captured bytes — it is never
legal proof, never a compliance determination, and never legal advice.

Contract:

* Additive only — no existing routing/preview field changes.
* Bounded — one targeted glob (regulator wildcard only) + one JSON read per
  candidate; no full evidence-tree scan.
* Fail-soft — a candidate with no resolvable record (missing, unreadable,
  quarantined, or unsealed legacy record) yields ``None`` and the alert flows
  exactly as before. This function never raises.

Only sealed, ``record_status == "complete"`` records are surfaced: the
customer-facing affordance says "sealed evidence record", so an unsealed
legacy record or a quarantined ``integrity_error`` record must yield ``None``
rather than an overstated claim.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Path segments interpolated into the evidence glob must be plain directory
# names — no separators, traversal, or glob metacharacters. Matches the real
# id charsets (source ids: "AE-adgm-fsra-rulebooks"; run ids: uuid hex[:8]).
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")

# Snapshot artifact keys whose parent directory is the run id — the layout the
# pipeline writes: data/source_snapshots/<date>/<MARKET>/<source_id>/<run_id>/<file>
# (see app.source_runs._snapshot_paths).
_SNAPSHOT_PATH_KEYS = (
    "snapshot_normalized_path",
    "snapshot_raw_path",
    "snapshot_pdf_text_path",
)


def _evidence_base_dir() -> Path:
    """The root that holds the canonical ``evidence/`` tree.

    Read at call time from app.evidence_records so this module can never
    disagree with the writer about where canonical records live (and so tests
    that isolate that base dir isolate this lookup too).
    """
    from app.evidence_records import _BASE_DIR

    return _BASE_DIR


def run_id_from_proof_block(proof_block: dict[str, Any] | None) -> str:
    """Recover the run id from the snapshot layout carried in a proof block.

    Snapshot artifacts live at ``.../<source_id>/<run_id>/<file>``, so the run
    id is the immediate parent directory of any snapshot path. Returns ``""``
    when no snapshot path is present (e.g. a fabricated or degraded proof
    block) — the caller treats that as "no linkage".
    """
    if not isinstance(proof_block, dict):
        return ""
    for key in _SNAPSHOT_PATH_KEYS:
        value = str(proof_block.get(key) or "").strip()
        if not value:
            continue
        parts = Path(value).parts
        if len(parts) >= 2:
            return str(parts[-2])
    return ""


def _load_record(evidence_root: Path, source_id: str, run_id: str) -> dict[str, Any] | None:
    """One targeted glob + one JSON read: evidence/<regulator>/<source>/<run>/."""
    if not evidence_root.exists():
        return None
    for path in sorted(evidence_root.glob(f"*/{source_id}/{run_id}/evidence-record.json")):
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def build_proof_for_candidate(
    candidate: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Return the sealed-evidence ``proof`` block for a routed alert candidate.

    Returns ``None`` — and the alert flows unchanged — whenever the linkage
    cannot be established honestly: no source/run identity, no canonical
    record on disk, a quarantined record, or a record without its self-seal.
    """
    try:
        if not isinstance(candidate, dict):
            return None
        proof_block = candidate.get("proof_block")
        if not isinstance(proof_block, dict):
            proof_block = {}
        source_id = str(candidate.get("source_id") or proof_block.get("source_id") or "").strip()
        run_id = run_id_from_proof_block(proof_block)
        if not source_id or not run_id:
            return None
        if not _SAFE_SEGMENT_RE.match(source_id) or not _SAFE_SEGMENT_RE.match(run_id):
            return None

        root = Path(base_dir) if base_dir is not None else _evidence_base_dir()
        record = _load_record(root / "evidence", source_id, run_id)
        if record is None:
            return None

        # Only a complete, sealed record is presentable as "sealed evidence".
        if str(record.get("record_status") or "") != "complete":
            return None
        record_id = str(record.get("record_id") or "").strip()
        record_hash = str(record.get("record_hash") or "").strip()
        if not record_id or not record_hash:
            return None

        content = record.get("content")
        if not isinstance(content, dict):
            content = {}
        change = record.get("change")
        if not isinstance(change, dict):
            change = {}
        files = record.get("files")
        if not isinstance(files, dict):
            files = {}
        return {
            "evidence_record_id": record_id,
            "record_hash": record_hash,
            "run_id": run_id,
            "diff_available": bool(change.get("diff_path") or files.get("diff_path")),
            "normalized_hash": str(content.get("current_hash") or "") or None,
        }
    except Exception as exc:  # defensive: fail-soft is the contract
        logger.debug(
            "Alert proof lookup failed (non-fatal): %s: %s", type(exc).__name__, exc
        )
        return None
