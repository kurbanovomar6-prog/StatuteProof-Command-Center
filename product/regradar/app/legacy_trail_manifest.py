"""A sealed manifest over the pre-chain block of the source-run trail.

WHY THIS EXISTS. ``verify_chain`` starts at the first record carrying a
``record_hash`` and skips everything before it. Measured 2026-07-25: the live
trail holds 1430 records and the chain covers 24 of them, so 1406 records could be
deleted, reordered, or have a line removed from the middle with nothing noticing.
For a product whose claim is an evidence trail an auditor can rely on, "the oldest
99% is unprotected" is the gap that matters.

WHAT IT PROVES, AND WHAT IT DOES NOT. The manifest is a digest over the ordered
identities of the legacy records. Recomputing it detects any deletion, insertion,
reordering, or identity edit in that block SINCE THE MANIFEST WAS SEALED.

It says nothing whatsoever about whether that block was already tampered with
BEFORE sealing. Nothing can: the records predate the chain, so there is no earlier
attestation to compare against. Sealing today establishes a floor, not a history —
and the manifest records the date so a reader can see exactly which claim they are
being offered.

Identity comes from ``app.source_runs._chain_payload``, the same canonical
serialization the chain itself hashes, so the two mechanisms cannot drift into
disagreeing about what "the same record" means.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.source_runs import _BASE_DIR, _chain_payload

MANIFEST_METHOD = "legacy-block-sha256-v1"
MANIFEST_FILENAME = "legacy_trail_manifest.json"


def manifest_path(base_dir: Path | None = None) -> Path:
    root = base_dir if base_dir is not None else _BASE_DIR
    return root / "data" / "source_runs" / MANIFEST_FILENAME


def legacy_records(records: list[dict]) -> list[dict]:
    """The records before the chain begins — the ones verify_chain skips.

    The chain starts at the first record with a ``record_hash``; everything
    before that is the legacy block. A record without a hash appearing AFTER the
    chain started is a chain break, not a legacy record, and is not counted here —
    verify_chain already reports it.
    """
    block: list[dict] = []
    for record in records:
        if str(record.get("record_hash") or ""):
            break
        block.append(record)
    return block


def compute_digest(block: list[dict]) -> str:
    """Digest the ordered identities of the legacy block.

    Order is part of the digest by construction: each record's canonical payload
    is fed in sequence, so swapping two records changes the result even though the
    set of records is unchanged.
    """
    digest = hashlib.sha256()
    digest.update(f"{MANIFEST_METHOD}\n{len(block)}\n".encode("utf-8"))
    for index, record in enumerate(block):
        digest.update(f"{index}\n".encode("utf-8"))
        digest.update(_chain_payload(record).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def seal(records: list[dict], base_dir: Path | None = None) -> dict[str, Any]:
    """Write the manifest for the current legacy block. Overwrites any previous one.

    Overwriting is intentional and is why this is a founder CLI rather than
    something the pipeline does: re-sealing after a tamper would erase the very
    evidence the manifest exists to provide, so the act must be deliberate and
    attributable to a person with shell access.
    """
    block = legacy_records(records)
    payload = {
        "method": MANIFEST_METHOD,
        "record_count": len(block),
        "digest": compute_digest(block),
        "sealed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "covers": (
            "The pre-chain records of data/source_runs/source_runs.jsonl, in file "
            "order. Proves no deletion, insertion, reordering or identity edit in "
            "that block SINCE sealed_at. Says nothing about the block's integrity "
            "before that moment."
        ),
    }
    path = manifest_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def load(base_dir: Path | None = None) -> dict[str, Any] | None:
    path = manifest_path(base_dir)
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return loaded if isinstance(loaded, dict) else None


def verify(records: list[dict], base_dir: Path | None = None) -> dict[str, Any]:
    """Check the legacy block against its sealed manifest.

    Returns ``status`` one of:
      unsealed  — no manifest exists; the block is unprotected and says so
      intact    — count and digest both match
      count     — the number of legacy records changed (records added or removed)
      digest    — the count matches but an identity or the ORDER changed
      unreadable— a manifest exists but could not be parsed; treated as a failure,
                  because a corrupt seal must not read as a passing one
    """
    block = legacy_records(records)
    manifest = load(base_dir)
    if manifest is None:
        return {
            "status": "unsealed",
            "ok": False,
            "record_count": len(block),
            "detail": (
                f"{len(block)} pre-chain records are not covered by the hash chain and "
                "no manifest seals them. Deleting or reordering any of them would go "
                "undetected. Seal them with `run.py seal-legacy-trail`."
            ),
        }
    if str(manifest.get("method") or "") != MANIFEST_METHOD:
        return {
            "status": "unreadable",
            "ok": False,
            "record_count": len(block),
            "detail": f"Manifest method {manifest.get('method')!r} is not {MANIFEST_METHOD}.",
        }

    sealed_count = manifest.get("record_count")
    if not isinstance(sealed_count, int) or sealed_count != len(block):
        return {
            "status": "count",
            "ok": False,
            "record_count": len(block),
            "sealed_count": sealed_count,
            "detail": (
                f"The legacy block holds {len(block)} records; the manifest sealed "
                f"{sealed_count}. Records were added or removed after sealing."
            ),
        }

    recomputed = compute_digest(block)
    if recomputed != str(manifest.get("digest") or ""):
        return {
            "status": "digest",
            "ok": False,
            "record_count": len(block),
            "detail": (
                "The legacy block still holds the sealed number of records, but its "
                "digest changed — a record's identity or the order was altered."
            ),
        }
    return {
        "status": "intact",
        "ok": True,
        "record_count": len(block),
        "sealed_at": manifest.get("sealed_at"),
        "detail": (
            f"{len(block)} pre-chain records unchanged since "
            f"{manifest.get('sealed_at')} (order and identities)."
        ),
    }
