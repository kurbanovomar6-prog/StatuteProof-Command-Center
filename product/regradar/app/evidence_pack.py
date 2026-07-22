"""Self-serve Evidence Pack with a standalone "verify-it-yourself" bundle.

This is the customer-facing evidence moat: for a date range and a set of source
IDs, bundle the raw + normalized official-source snapshots that StatuteProof
captured (from the canonical ``evidence/`` tree — see
``app/evidence_records.py``) into a single sealed ZIP archive that carries:

1. ``manifest.json`` — every record's raw SHA-256, normalized SHA-256,
   snapshot filenames, timestamp, source, official URL, and run status.
2. ``verify.py`` — a small, stdlib-only, no-app-imports script the CUSTOMER'S
   OWN auditor runs to re-read every included snapshot, recompute its SHA-256
   exactly the way the product recorded it, and print PASS/FAIL per record.
3. ``HOW-TO-VERIFY.md`` — plain instructions for independent re-hashing.

Legal safety (non-negotiable):

* Every customer-facing artifact carries the standard disclaimer.
* A forbidden-claims guard (delegating to the ONE canonical guard in
  ``app.legal_safety``) runs over the authored prose before it is written into
  the ZIP; a banned claim refuses the pack.
* Evidence-grounded only: the pack ships bytes StatuteProof actually captured
  and the SHA-256 it recorded at capture time. It asserts what changed / what a
  reviewer may wish to check — never advice, never a guarantee. The pack is
  monitoring evidence, not a legal opinion.

The builder never raises: it returns ``{"status": "ok"|"empty"|"error", ...}``
so the API handler can respond without leaking internal errors.
"""

from __future__ import annotations

import hashlib
import json
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.audit_export import validate_date_range, validate_source_ids
from app.evidence_assessment import LEGAL_DISCLAIMER
from app.legal_safety import assert_no_forbidden_claims as _assert_no_forbidden_claims

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent

# Brief-grade standard disclaimer (docs/CLAUDE.md "Full (briefs)"). Included in
# full so the pack stands on its own for a customer's auditor.
FULL_LEGAL_DISCLAIMER = (
    "StatuteProof reports are generated from monitored official-source records "
    "and are provided for information and compliance review support only. "
    "StatuteProof reports do not constitute legal advice, regulatory advice, "
    "compliance certification, or a legal opinion. StatuteProof does not replace "
    "qualified legal counsel, compliance professionals, MLROs, or other "
    "professional advisers. StatuteProof does not guarantee compliance, prevent "
    "fines, or certify that all regulatory updates have been captured. Source "
    "monitoring may be affected by publication delays, website changes, PDF "
    "formatting, access limits, or source structure changes. Users should verify "
    "official source material directly and review evidence records, hashes, "
    "timestamps, and diffs before relying on a report. Users should consult "
    "qualified legal or compliance professionals before making regulatory, "
    "filing, operational, or customer decisions based on a report."
)

# Hard cap on the number of evidence records a single pack may materialize. The
# pack loads every included record's raw + normalized + record bytes into memory
# before writing the ZIP, so an unbounded selection ("export a year across every
# source") could exhaust memory on the single-process server and take the
# platform down for all tenants. A self-serve evidence pack is a focused artifact
# (a source or a few sources over a period), so this ceiling is well above any
# legitimate use; an oversized selection is rejected with guidance to narrow it
# rather than silently truncated (a truncated pack would be misleading evidence
# shipped under a clean manifest). Enforced via the collector's ``limit`` so
# over-cap requests never load more than ``MAX_EVIDENCE_PACK_RECORDS + 1``
# records' bytes. Mirrors ``regulator_binder.MAX_BINDER_RECORDS``.
MAX_EVIDENCE_PACK_RECORDS = 2000


class EvidencePackError(ValueError):
    """Raised when authored pack prose would contain a forbidden claim."""


def assert_no_forbidden_claims(text: str) -> None:
    """Raise ``EvidencePackError`` if a forbidden phrase appears in ``text``.

    Thin adapter over the ONE canonical guard in ``app.legal_safety`` — it only
    swaps in this module's exception type and label. It used to carry its own
    ``lower()`` + substring scan, so the pack README/verify script AND the
    customer-facing Evidence Room (which re-exports this function) silently
    missed the whitespace-collapse, homoglyph folding and inflection matching
    that ``legal_safety`` applies: "StatuteProof guarantees compliance." and
    "We guarantee\\ncompliance." shipped from here while the same strings were
    blocked on every other delivery path. The canonical guard also neutralizes
    the product's fixed disclaimers (which legitimately DENY banned claims), so
    a disclaimer still cannot trip its own guard. Do not reintroduce a local
    scan here.
    """
    _assert_no_forbidden_claims(
        text, exc=EvidencePackError, label="Evidence pack prose"
    )


def build_evidence_pack(
    source_ids: list[str],
    date_from: str,
    date_to: str,
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
    max_records: int = MAX_EVIDENCE_PACK_RECORDS,
) -> dict[str, Any]:
    """Bundle canonical evidence for ``source_ids`` in a date range into a ZIP.

    Only ``record_status == "complete"`` records whose ``integrity`` is VERIFIED
    are included, and only when the normalized snapshot bytes on disk still hash
    to the SHA-256 the record recorded at capture time (a record that no longer
    matches its own recorded hash is skipped, never shipped as clean evidence).

    Returns
    -------
    dict
        ``{"status": "ok", "pack_path": str, "record_count": int, ...}`` on
        success, ``{"status": "empty", ...}`` when no records match,
        ``{"status": "too_large", "max_records": int, ...}`` when the selection
        exceeds ``max_records`` (availability guard — see
        ``MAX_EVIDENCE_PACK_RECORDS``), and ``{"status": "error", "message":
        str}`` on failure. Never raises.
    """
    try:
        root = base_dir or _BASE_DIR

        ids_ok, ids_err = validate_source_ids(source_ids)
        if not ids_ok:
            return {"status": "error", "message": ids_err}

        valid, err = validate_date_range(date_from, date_to)
        if not valid:
            return {"status": "error", "message": err}

        wanted = {str(s).strip() for s in source_ids if str(s).strip()}
        if not wanted:
            return {"status": "error", "message": "source_ids must be a non-empty list."}

        date_to_end = f"{date_to}T23:59:59"
        # Bounded collect: the collector stops after max_records + 1 entries, so an
        # oversized selection never materializes an unbounded number of records'
        # bytes in memory (the availability guard — see MAX_EVIDENCE_PACK_RECORDS).
        entries = _collect_pack_entries(root, wanted, date_from, date_to_end, limit=max_records)
        if not entries:
            return {
                "status": "empty",
                "record_count": 0,
                "message": "No complete evidence records found for the specified period and sources.",
            }
        if len(entries) > max_records:
            return {
                "status": "too_large",
                "max_records": max_records,
                "message": (
                    f"This selection spans more than {max_records} captured records. "
                    "Narrow the period or the number of sources and export again — a "
                    "self-serve evidence pack is a focused artifact for a source or a "
                    "few sources over a defined period."
                ),
            }

        manifest = _build_manifest(entries, wanted, date_from, date_to)

        # External RFC 3161 chain-head token (ADDITIVE): when the operator has
        # the trusted-timestamp anchor enabled and a token exists, ship the
        # sidecars so the recipient holds the third-party timestamp — not just
        # our word for the capture time. Scope honesty: the token attests the
        # evidence-chain HEAD hash at anchor time, not each individual diff.
        _tsr_path = root / "data" / "evidence_chain_head.tsr"
        _tsr_json_path = root / "data" / "evidence_chain_head.tsr.json"
        # Read both sidecar payloads ONCE, up front: the anchor thread
        # atomically replaces these files, so two separate zf.write() calls
        # could capture the token from anchor N and the sidecar from N+1.
        _tsr_bytes: bytes | None = None
        _tsr_json_bytes: bytes | None = None
        try:
            _tsr_bytes = _tsr_path.read_bytes()
        except OSError:
            _tsr_bytes = None
        if _tsr_bytes is not None:
            try:
                _tsr_json_bytes = _tsr_json_path.read_bytes()
            except OSError:
                _tsr_json_bytes = None
        _ship_tsr = _tsr_bytes is not None
        if _ship_tsr:
            manifest["external_timestamp"] = {
                "included": True,
                "token_file": "timestamp/evidence_chain_head.tsr",
                "sidecar_file": (
                    "timestamp/evidence_chain_head.tsr.json"
                    if _tsr_json_bytes is not None
                    else None
                ),
                "scope": (
                    "RFC 3161 timestamp token over the evidence-chain HEAD "
                    "hash at anchor time — NOT over any individual record's "
                    "record_hash. To verify: use `openssl ts -verify` against "
                    "your own trusted TSA roots, or submit the token to the "
                    "public verifier with timestamp_digest set to the "
                    "anchored_head_record_hash value from the .tsr.json "
                    "sidecar. Checking it against a record's own record_hash "
                    "will honestly FAIL — the token attests the chain head."
                ),
            }

        readme = _render_how_to_verify(manifest)
        verify_script = _VERIFY_SCRIPT

        # Legal-safety gate: refuse to ship a pack whose authored prose trips the
        # shared forbidden-claims guard.
        assert_no_forbidden_claims(readme)
        assert_no_forbidden_claims(verify_script)

        pack_dir = output_dir or (root / "data" / "evidence_packs")
        pack_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        zip_name = f"evidence_pack_{date_from}_{date_to}_{stamp}.zip"
        zip_path = pack_dir / zip_name

        manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", manifest_json)
            zf.writestr("HOW-TO-VERIFY.md", readme)
            zf.writestr("verify.py", verify_script)
            zf.writestr("DISCLAIMER.txt", f"{LEGAL_DISCLAIMER}\n\n{FULL_LEGAL_DISCLAIMER}\n")
            for entry in entries:
                zf.writestr(entry["raw_arcname"], entry["raw_bytes"])
                zf.writestr(entry["normalized_arcname"], entry["normalized_bytes"])
                zf.writestr(entry["record_arcname"], entry["record_bytes"])
                if entry.get("diff_arcname") and entry.get("diff_bytes") is not None:
                    zf.writestr(entry["diff_arcname"], entry["diff_bytes"])
            if _ship_tsr and _tsr_bytes is not None:
                zf.writestr("timestamp/evidence_chain_head.tsr", _tsr_bytes)
                if _tsr_json_bytes is not None:
                    zf.writestr("timestamp/evidence_chain_head.tsr.json", _tsr_json_bytes)

        return {
            "status": "ok",
            "pack_path": str(zip_path.resolve()),
            "pack_filename": zip_name,
            "record_count": len(entries),
            "source_count": len({e["source_id"] for e in entries}),
            "date_from": date_from,
            "date_to": date_to,
            "manifest": manifest,
            "disclaimer": LEGAL_DISCLAIMER,
        }
    except Exception as exc:  # never raise across the boundary
        logger.error("build_evidence_pack: unexpected error: %s", type(exc).__name__)
        return {"status": "error", "message": str(exc)}


# ── internal helpers ────────────────────────────────────────────────────────────

def _collect_pack_entries(
    root: Path,
    wanted: set[str],
    date_from: str,
    date_to_end: str,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return verified, in-range, source-scoped evidence entries for the pack.

    ``limit`` bounds how many entries are materialized: once ``limit + 1`` entries
    have been collected the scan stops early, so a caller can detect an oversized
    selection (``len(result) > limit``) and reject it WITHOUT ever loading the
    snapshot bytes of an unbounded number of records into memory. ``None`` (the
    default) preserves the original collect-everything behavior.
    """
    evidence_root = root / "evidence"
    if not evidence_root.exists():
        return []

    # Scope the filesystem walk to the wanted source_ids ONLY. The on-disk layout
    # is evidence/<regulator>/<source_id>/<run_id>/evidence-record.json, so one
    # glob per wanted source enumerates just that source's own records — never the
    # entire cross-tenant evidence store on every export request. Bounds cost to
    # O(records in the requested scope), not O(total product evidence)
    # (verification-swarm 2026-07-12; matches evidence_room._collect_room_records).
    # A source_id that isn't a safe single path segment could never have matched a
    # real record dir anyway, so it is skipped.
    import re as _re

    # Reject all-dot segments (".."/"." ) — the negative lookahead stops a
    # traversal id from collapsing the per-source glob back to a whole-tree walk
    # (verify-swarm 2026-07-12).
    _safe_segment = _re.compile(r"^(?!\.+$)[A-Za-z0-9._-]+$")
    record_paths: list[Path] = []
    for source_id in sorted(wanted):
        if _safe_segment.match(str(source_id)):
            record_paths.extend(evidence_root.glob(f"*/{source_id}/**/evidence-record.json"))

    entries: list[dict[str, Any]] = []
    for record_path in sorted(record_paths):
        if limit is not None and len(entries) > limit:
            break  # one past the cap is enough for the caller to detect overflow
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("evidence_pack: skipping unreadable/corrupt evidence record %s", record_path)
            continue
        if not isinstance(record, dict):
            continue
        if record.get("record_status") != "complete":
            continue
        integrity = record.get("integrity")
        if not isinstance(integrity, dict):
            integrity = {}
        if integrity.get("integrity_status") != "VERIFIED" or integrity.get("hash_verified") is not True:
            continue

        source = record.get("source")
        if not isinstance(source, dict):
            source = {}
        source_id = str(source.get("source_id") or "").strip()
        if source_id not in wanted:  # source-scoping: never leak another source
            continue

        run = record.get("run")
        if not isinstance(run, dict):
            run = {}
        naive = _naive_ts(str(run.get("timestamp") or ""))
        if not (naive and date_from <= naive <= date_to_end):
            continue

        entry = _entry_from_record(record, record_path, root, source_id, source, run)
        if entry is not None:
            entries.append(entry)
    return entries


def _entry_from_record(
    record: dict[str, Any],
    record_path: Path,
    root: Path,
    source_id: str,
    source: dict[str, Any],
    run: dict[str, Any],
) -> dict[str, Any] | None:
    """Read + hash the snapshots for one record; None if inconsistent/unreadable."""
    content = record.get("content")
    if not isinstance(content, dict):
        content = {}
    files = record.get("files")
    if not isinstance(files, dict):
        files = {}
    change = record.get("change")
    if not isinstance(change, dict):
        change = {}
    record_id = str(record.get("record_id") or "").strip()
    if not record_id:
        return None

    raw_path = _safe_under_root(str(files.get("raw_path") or content.get("raw_content_path") or ""), root)
    normalized_path = _safe_under_root(
        str(files.get("normalized_path") or content.get("normalized_current_path") or ""), root
    )
    if raw_path is None or normalized_path is None:
        return None
    if not raw_path.exists() or not normalized_path.exists():
        return None

    raw_bytes = raw_path.read_bytes()
    normalized_bytes = normalized_path.read_bytes()
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    normalized_hash = hashlib.sha256(normalized_bytes).hexdigest()

    # The recorded normalized hash the product certified at capture time. If the
    # bytes on disk no longer match it, the record is inconsistent — skip it
    # rather than ship tampered evidence under a clean manifest.
    recorded = str(content.get("current_hash") or "").strip().lower().removeprefix("sha256:")
    if recorded and recorded != normalized_hash:
        logger.warning("build_evidence_pack: skipping %s (normalized bytes != recorded hash)", record_id)
        return None

    # Same protection for the RAW capture. The manifest and HOW-TO-VERIFY tell the
    # auditor these are the hashes recorded at capture time, so a post-capture
    # edit to raw.txt must never ship as PASS. Compare disk bytes to the sealed
    # content.raw_hash and skip on mismatch; use the recorded value in the manifest.
    recorded_raw = str(content.get("raw_hash") or "").strip().lower().removeprefix("sha256:")
    if recorded_raw and recorded_raw != raw_hash:
        logger.warning("build_evidence_pack: skipping %s (raw bytes != recorded raw_hash)", record_id)
        return None
    if recorded_raw:
        raw_hash = recorded_raw

    safe_id = _safe_arc(record_id)

    # Sealed-diff parity with the Regulator Binder: for a CHANGED record the
    # pipeline persisted a diff.txt (the sealed redline) and sealed its SHA-256 as
    # content.diff_hash. Ship that diff.txt and surface its hash + the previous
    # hash + the record self-seal so a customer's auditor can run the SAME sealed-
    # diff check (app.public_verify) the binder advertises — WITHOUT the pack and
    # binder disagreeing about what is verifiable. FIRST_SEEN records carry no diff
    # and must never be forced to (below stays None → no diff shipped).
    recorded_diff = str(content.get("diff_hash") or "").strip().lower().removeprefix("sha256:")
    previous_hash = str(content.get("previous_hash") or "").strip().lower().removeprefix("sha256:")
    record_hash = str(record.get("record_hash") or "").strip().lower().removeprefix("sha256:")
    diff_bytes: bytes | None = None
    diff_arcname: str | None = None
    diff_hash: str | None = None
    if recorded_diff:
        diff_path = _safe_under_root(str(change.get("diff_path") or files.get("diff_path") or ""), root)
        if diff_path is not None and diff_path.exists():
            candidate = diff_path.read_bytes()
            # Same protection as raw/normalized: a diff.txt whose bytes no longer
            # match the sealed content.diff_hash is tampered evidence — skip the
            # whole record rather than ship a redline that fails its own seal.
            if hashlib.sha256(candidate).hexdigest() != recorded_diff:
                logger.warning(
                    "build_evidence_pack: skipping %s (diff bytes != recorded diff_hash)", record_id
                )
                return None
            diff_bytes = candidate
            diff_arcname = f"snapshots/{safe_id}/diff.txt"
            diff_hash = recorded_diff

    return {
        "record_id": record_id,
        "source_id": source_id,
        "source_name": str(source.get("source_name") or source_id),
        "regulator": str(source.get("regulator") or ""),
        "official_url": str(source.get("official_url") or ""),
        "run_id": str(run.get("run_id") or ""),
        "run_status": str(run.get("status") or ""),
        "timestamp": str(run.get("timestamp") or ""),
        "raw_hash": raw_hash,
        "normalized_hash": normalized_hash,
        "record_hash": record_hash,
        "previous_hash": previous_hash,
        "diff_hash": diff_hash,
        "raw_bytes": raw_bytes,
        "normalized_bytes": normalized_bytes,
        "record_bytes": record_path.read_bytes(),
        "diff_bytes": diff_bytes,
        "raw_arcname": f"snapshots/{safe_id}/raw.txt",
        "normalized_arcname": f"snapshots/{safe_id}/normalized.txt",
        "record_arcname": f"snapshots/{safe_id}/evidence-record.json",
        "diff_arcname": diff_arcname,
    }


def _build_manifest(
    entries: list[dict[str, Any]],
    wanted: set[str],
    date_from: str,
    date_to: str,
) -> dict[str, Any]:
    records = []
    for e in entries:
        row = {
            "record_id": e["record_id"],
            "source_id": e["source_id"],
            "source_name": e["source_name"],
            "regulator": e["regulator"],
            "official_url": e["official_url"],
            "run_id": e["run_id"],
            "run_status": e["run_status"],
            "timestamp": e["timestamp"],
            "raw_hash": e["raw_hash"],
            "normalized_hash": e["normalized_hash"],
            "raw_snapshot_file": e["raw_arcname"],
            "normalized_snapshot_file": e["normalized_arcname"],
            "evidence_record_file": e["record_arcname"],
        }
        # The record self-seal, when present (legacy records predate it and are
        # simply omitted — the pack stays valid without it).
        if e.get("record_hash"):
            row["record_hash"] = e["record_hash"]
        # CHANGED records: the sealed redline + its hash + the previous-state hash,
        # so verify.py and app.public_verify can run the sealed-diff check.
        if e.get("previous_hash"):
            row["previous_hash"] = e["previous_hash"]
        if e.get("diff_arcname") and e.get("diff_hash"):
            row["diff_hash"] = e["diff_hash"]
            row["diff_file"] = e["diff_arcname"]
        records.append(row)
    return {
        "pack_type": "statuteproof_evidence_pack",
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hash_algorithm": "sha256",
        "date_from": date_from,
        "date_to": date_to,
        "source_ids": sorted(wanted),
        "record_count": len(records),
        "verification": (
            "Run `python3 verify.py` from inside this unzipped pack to recompute "
            "each SHA-256 and compare it against this manifest. No StatuteProof "
            "software is required."
        ),
        "legal_disclaimer": LEGAL_DISCLAIMER,
        "legal_notice": FULL_LEGAL_DISCLAIMER,
        "records": records,
    }


def _render_how_to_verify(manifest: dict[str, Any]) -> str:
    count = manifest.get("record_count", 0)
    ext = manifest.get("external_timestamp") or {}
    external_timestamp_section = ""
    if ext.get("included"):
        external_timestamp_section = """
## External RFC 3161 timestamp (included)

`timestamp/evidence_chain_head.tsr` is an RFC 3161 token from a third-party
Time-Stamping Authority over the evidence-chain HEAD hash at anchor time. It
attests the chain head existed no later than the TSA-signed time — it is
**not a per-record stamp**, so checking it against any individual record's
`record_hash` will honestly report a mismatch.

To inspect it locally:

```
openssl ts -reply -in timestamp/evidence_chain_head.tsr -token_in -text
```

To verify it on the public verify page: upload the `.tsr` token AND paste the
`anchored_head_record_hash` value from
`timestamp/evidence_chain_head.tsr.json` into the timestamp-digest field —
that hash is the exact value the token attests.
"""
    return f"""# How to verify this evidence pack yourself

{LEGAL_DISCLAIMER}

This pack contains {count} official-source monitoring snapshot record(s) that
StatuteProof captured, together with the SHA-256 hashes it recorded at capture
time. You do not have to take those hashes on trust: you can re-compute them
yourself, offline, with nothing but a standard Python 3 install.

## What is in this pack

- `manifest.json` — one entry per record: the raw SHA-256, the normalized
  SHA-256, the snapshot filenames, the capture timestamp, the source, the
  official URL, and the run status.
- `snapshots/<record_id>/raw.txt` — the raw captured text of the official page.
- `snapshots/<record_id>/normalized.txt` — the normalized text StatuteProof
  hashed for change detection.
- `snapshots/<record_id>/evidence-record.json` — the canonical record for
  provenance.
- `snapshots/<record_id>/diff.txt` — the sealed redline (the diff against the
  previous captured state), present only for records where a change was detected.
  Its SHA-256 is recorded as `diff_hash` in `manifest.json`.
- `verify.py` — a standalone checker (Python standard library only, no
  StatuteProof imports).

## Verify with one command

From inside the unzipped pack folder:

```
python3 verify.py
```

For every record it re-reads the snapshot files (and, where a change was
detected, the sealed `diff.txt`), recomputes each SHA-256, and compares the
result to the SEALED hash inside that record's `evidence-record.json` content
block — the value the record self-seal proves has not been altered (the
`manifest.json` copy is unsealed and is used only as a fallback for legacy
records). It prints `PASS` when the bytes match the sealed hash and `FAIL` when
they do not, then exits non-zero if any record fails. If a single byte of a
snapshot or diff is altered — or the sealed hash it is checked against is
edited — that record reports `FAIL`.

## Verify by hand (no scripts)

You can also confirm any record with your own tools, for example:

```
shasum -a 256 snapshots/<record_id>/normalized.txt
```

and check the value against the sealed `content.current_hash` for that record in
`snapshots/<record_id>/evidence-record.json` (its `manifest.json` copy,
`normalized_hash`, is identical on a genuine pack). The raw side works the same
way against the sealed `content.raw_hash`.
{external_timestamp_section}
## What this pack is and is not

This pack is monitoring evidence: the bytes captured from monitored official
sources and the hashes recorded for them, so you can independently confirm the
snapshots have not been altered since capture. It is not a legal opinion and it
does not interpret the regulatory text. It shows what was captured and lets you
check it; whether any change matters for your obligations is a question for your
own qualified advisers.

---

{FULL_LEGAL_DISCLAIMER}
"""


# Standalone verifier shipped inside the pack. Standard library only, no app
# imports, so a customer's auditor can run it on any Python 3 without installing
# anything. Keep it small and self-contained.
_VERIFY_SCRIPT = '''#!/usr/bin/env python3
"""Standalone StatuteProof evidence-pack verifier.

Recompute the SHA-256 of every snapshot in this pack and compare it against the
SEALED hash inside that record's bundled evidence-record.json content block
(content.raw_hash / content.current_hash / content.diff_hash) — the value whose
authenticity the record self-seal below proves. The per-record hashes in
manifest.json are unsealed and are used only as a fallback for legacy records
that carry no such sealed content hash. For each record it also recomputes the
record SELF-SEAL over the bundled evidence-record.json content block, recomputes the
full-record ATTRIBUTION seal (regulator, source name, change summary, line
counts, run status, review status) where present, and cross-checks the displayed
capture time / source URL against the sealed copies. Standard library only; no
StatuteProof code is required and no network access is used.

Usage:  python3 verify.py        (run from inside the unzipped pack)

Monitoring intelligence only. Not legal advice. This re-hashes the bytes in this
pack against the SHA-256 values StatuteProof recorded when it captured them, so
you can independently confirm they have not been altered. It is not a legal
opinion.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# The full-record attribution seal scheme. Kept byte-identical to
# app.evidence_records.ATTRIBUTION_HASH_METHOD so this standalone verifier
# recognizes exactly the records the product sealed.
ATTRIBUTION_HASH_METHOD = "attribution-sha256-v1"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_record_hash(content):
    """Bare lowercase-hex SHA-256 of a record's content block.

    Byte-identical to app.record_hashing.canonical_record_hash: compact,
    sorted-key, non-ASCII-preserving, NaN-rejecting UTF-8 JSON. Inlined here so
    the standalone verifier needs no StatuteProof code to reproduce the seal.
    """
    payload = json.dumps(
        content, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _bare_digest(value):
    """Strip an optional sha256: prefix and lowercase; returns "" for non-str."""
    text = str(value or "").strip()
    if text.lower().startswith("sha256:"):
        text = text[len("sha256:"):]
    return text.lower()


def sealed_snapshot_hash(bundled, sealed_paths, manifest_record, manifest_key):
    """Resolve the AUTHORITATIVE expected hash for a snapshot.

    The bundled evidence-record.json content block is the SEALED authority for
    the snapshot hashes: check_record_seal proves it recomputes from record_hash,
    so content.raw_hash / content.current_hash / content.diff_hash cannot be
    rewritten without failing that seal. Its hash is therefore the source of
    truth, resolved most-specific-first in the SAME order the online verifier
    uses (app.public_verify._HASH_PATHS).

    manifest.json is UNSEALED: the per-record raw_hash/normalized_hash/diff_hash
    pasted there can be edited to match fabricated snapshot bytes, so it is used
    ONLY as a fallback for a legacy record whose bundled evidence-record.json
    carries no such content hash. Returns (expected_bare_hex, "sealed" |
    "manifest" | "").
    """
    if isinstance(bundled, dict):
        for path in sealed_paths:
            cursor = bundled
            found = True
            for key in path:
                if isinstance(cursor, dict) and key in cursor:
                    cursor = cursor[key]
                else:
                    found = False
                    break
            if found and isinstance(cursor, str) and cursor.strip():
                return _bare_digest(cursor), "sealed"
    fallback = manifest_record.get(manifest_key)
    if isinstance(fallback, str) and fallback.strip():
        return _bare_digest(fallback), "manifest"
    return "", ""


def check_record_seal(record_id, record):
    """Recompute the record self-seal over the bundled content block.

    Mirrors app.public_verify._check_record_hash_self_consistent for the
    published content-sha256-v1 scheme: recompute canonical_record_hash(content)
    and compare it to the record's own top-level record_hash. Any edit to the
    bundled evidence-record.json content changes the recomputed hash and reports
    FAIL. A legacy record with no seal, or an unrecognized scheme, is skipped
    (never failed). Returns 1 on FAIL, else 0.
    """
    stored = record.get("record_hash")
    if not stored:
        print("SKIP  %s [record_seal] no record_hash (legacy record); nothing to self-check" % record_id)
        return 0
    if record.get("record_hash_method") != "content-sha256-v1":
        print("SKIP  %s [record_seal] unrecognized record_hash_method; skipping self-seal" % record_id)
        return 0
    content = record.get("content")
    if not isinstance(content, dict):
        print("FAIL  %s [record_seal] record_hash_method is content-sha256-v1 but no content block" % record_id)
        return 1
    if canonical_record_hash(content) == _bare_digest(stored):
        print("PASS  %s [record_seal] record_hash recomputes from the sealed content block" % record_id)
        return 0
    print("FAIL  %s [record_seal] record_hash does NOT recompute from content - the record was altered" % record_id)
    return 1


def check_capture_metadata(record_id, record):
    """Cross-check displayed capture metadata against the SEALED copies.

    Mirrors app.public_verify._check_capture_metadata_consistent: the sealed
    content.captured_at / content.source_url are covered by record_hash, so a
    display-only edit to run.timestamp or source.official_url (that left the
    sealed value untouched) is caught here. Skips records predating the sealed
    fields. Returns 1 on FAIL, else 0.
    """
    content = record.get("content")
    content = content if isinstance(content, dict) else {}
    sealed_ts = content.get("captured_at")
    sealed_url = content.get("source_url")
    if sealed_ts is None and sealed_url is None:
        print("SKIP  %s [capture_metadata] no sealed captured_at/source_url (legacy record)" % record_id)
        return 0
    run = record.get("run")
    run = run if isinstance(run, dict) else {}
    source = record.get("source")
    source = source if isinstance(source, dict) else {}
    mismatches = []
    if sealed_ts is not None and "timestamp" in run and run.get("timestamp") != sealed_ts:
        mismatches.append("run.timestamp != sealed content.captured_at")
    if sealed_url is not None and "official_url" in source and source.get("official_url") != sealed_url:
        mismatches.append("source.official_url != sealed content.source_url")
    if mismatches:
        print("FAIL  %s [capture_metadata] %s" % (record_id, "; ".join(mismatches)))
        return 1
    print("PASS  %s [capture_metadata] displayed capture time and source URL match the sealed values" % record_id)
    return 0


def _carries_forgeable_attribution(record):
    """True if the record displays attribution fields NOT covered by record_hash.

    Mirrors app.public_verify._carries_forgeable_attribution: the regulator,
    source name, run status, change summary, and review status are DISPLAY fields
    the content-only record_hash leaves forgeable. When a record shows any of them
    but carries no attribution seal, a bare PASS would over-claim, so the caller
    reports limited scope instead of an unqualified PASS.
    """
    def _has(block, key):
        value = record.get(block)
        return isinstance(value, dict) and bool(str(value.get(key) or "").strip())

    return (
        _has("source", "regulator")
        or _has("source", "source_name")
        or _has("run", "status")
        or _has("change", "summary")
        or _has("review", "review_status")
    )


def attribution_seal_payload(record):
    """Canonical payload sealed by attribution_hash.

    Byte-identical to app.evidence_records.attribution_seal_payload: binds the
    display/attribution/narrative fields (regulator, source name, run status,
    change summary + line counts, review status) alongside the already-sealed
    content block. Scalars are coerced to str/int so canonical_record_hash (which
    forbids floats) produces a byte-stable, standard-tool-reproducible payload.
    Inlined here so the standalone verifier needs no StatuteProof code.
    """
    def _dict(key):
        value = record.get(key)
        return value if isinstance(value, dict) else {}

    content = _dict("content")
    source = _dict("source")
    run = _dict("run")
    change = _dict("change")
    review = _dict("review")

    def _int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    return {
        "content": content,
        "source_regulator": str(source.get("regulator") or ""),
        "source_name": str(source.get("source_name") or ""),
        "run_status": str(run.get("status") or ""),
        "change_summary": str(change.get("summary") or ""),
        "change_lines_added": _int(change.get("lines_added")),
        "change_lines_removed": _int(change.get("lines_removed")),
        "review_status": str(review.get("review_status") or ""),
    }


def check_attribution_seal(record_id, record):
    """Recompute the full-record attribution_hash over the bundled record.

    Mirrors app.public_verify._check_attribution_seal_consistent. record_hash
    covers only the content block, so the regulator, source name, change summary,
    line counts, run status, and review status a human READS are forgeable by a
    holder of a genuine record (flip CBUAE->VARA, rewrite the change summary, mark
    a pending record "approved") with content and capture metadata untouched.
    Records sealed with attribution_hash bind those fields; recompute through the
    SAME payload builder the writer used and FAIL on any mismatch.

    A record without the attribution seal is NOT passed: if it displays forgeable
    attribution fields it is reported as limited scope (an explicit SKIP that names
    what is unsealed, never an unqualified PASS over forgeable fields); a legacy
    record with no such fields is a plain SKIP. Returns 1 on FAIL, else 0.
    """
    stored = record.get("attribution_hash")
    # The attribution seal extends the content seal (its payload embeds the content
    # block), so it is authoritative only while record_hash is present.
    has_content_seal = isinstance(record.get("record_hash"), str) and bool(record["record_hash"].strip())
    if not (isinstance(stored, str) and stored.strip() and has_content_seal):
        if _carries_forgeable_attribution(record):
            print(
                "SKIP  %s [attribution_seal] LIMITED SCOPE: no attribution_hash - this "
                "record's regulator, source name, change summary, line counts, run "
                "status, and review status are DISPLAY fields NOT covered by its seal; "
                "only the content bytes and capture metadata are cryptographically bound"
                % record_id
            )
        else:
            print(
                "SKIP  %s [attribution_seal] no attribution_hash (legacy record); nothing to self-check"
                % record_id
            )
        return 0
    if record.get("attribution_hash_method") != ATTRIBUTION_HASH_METHOD:
        print("FAIL  %s [attribution_seal] unrecognized attribution_hash_method; refusing to trust seal" % record_id)
        return 1
    try:
        recomputed = canonical_record_hash(attribution_seal_payload(record))
    except (ValueError, TypeError):
        print("FAIL  %s [attribution_seal] attribution fields could not be canonically re-hashed" % record_id)
        return 1
    if recomputed == _bare_digest(stored):
        print(
            "PASS  %s [attribution_seal] attribution_hash recomputes from the record's "
            "regulator, source name, change summary, line counts, run status, and review status"
            % record_id
        )
        return 0
    print(
        "FAIL  %s [attribution_seal] attribution_hash does NOT recompute - the regulator, "
        "change summary, run status, or review status was altered" % record_id
    )
    return 1


def main():
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    records = manifest.get("records", [])
    print("Verifying %d evidence record(s) against the SEALED evidence records\\n" % len(records))
    failures = 0
    for record in records:
        record_id = record.get("record_id", "<unknown>")

        # Load the bundled evidence-record.json FIRST: its content block is the
        # SEALED authority for every snapshot hash. check_record_seal (below)
        # proves it recomputes from record_hash, so content.raw_hash /
        # content.current_hash / content.diff_hash cannot be rewritten without
        # failing that seal. The per-record hashes in manifest.json are UNSEALED:
        # comparing snapshot bytes to them would let a holder of a genuine pack
        # fabricate raw.txt and edit ONLY the manifest hash to match, laundering
        # forged official-source text through a clean PASS. So the sealed value is
        # the authority; the manifest hash is a fallback only for legacy records.
        rec_rel = record.get("evidence_record_file")
        rec_target = (HERE / rec_rel) if rec_rel else None
        bundled = None
        if rec_target is not None and rec_target.exists():
            try:
                loaded = json.loads(rec_target.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                loaded = None
            if isinstance(loaded, dict):
                bundled = loaded

        for label, sealed_paths, manifest_key, file_key in (
            ("raw", (("content", "raw_hash"), ("raw_hash",)),
             "raw_hash", "raw_snapshot_file"),
            ("normalized",
             (("content", "current_hash"), ("current_hash",), ("normalized_hash",)),
             "normalized_hash", "normalized_snapshot_file"),
        ):
            rel = record.get(file_key)
            expected, origin = sealed_snapshot_hash(bundled, sealed_paths, record, manifest_key)
            target = HERE / rel if rel else None
            if not rel or target is None or not target.exists():
                print("FAIL  %s [%s] snapshot file missing: %s" % (record_id, label, rel))
                failures += 1
                continue
            actual = sha256_file(target)
            if expected and actual == expected:
                print("PASS  %s [%s] sha256=%s (matches %s hash)" % (record_id, label, actual, origin))
            else:
                print("FAIL  %s [%s] expected=%s actual=%s" % (record_id, label, expected, actual))
                failures += 1
        # Sealed diff (the redline) for CHANGED records only. FIRST_SEEN records
        # carry no diff_file and are correctly skipped here — a first capture has
        # nothing to diff against. A single altered byte of diff.txt fails this.
        diff_rel = record.get("diff_file")
        if diff_rel:
            expected, origin = sealed_snapshot_hash(
                bundled, (("content", "diff_hash"), ("diff_hash",)), record, "diff_hash"
            )
            target = HERE / diff_rel
            if not target.exists():
                print("FAIL  %s [diff] sealed diff file missing: %s" % (record_id, diff_rel))
                failures += 1
            else:
                actual = sha256_file(target)
                if expected and actual == expected:
                    print("PASS  %s [diff] sha256=%s (matches %s hash)" % (record_id, actual, origin))
                else:
                    print("FAIL  %s [diff] expected=%s actual=%s" % (record_id, expected, actual))
                    failures += 1
        # Record self-seal + capture-metadata cross-check over the bundled
        # evidence-record.json. Re-hashing the snapshots proves the bytes are
        # intact; this proves the RECORD binding them (its content block — which
        # supplies the SEALED snapshot hashes above — and the capture time /
        # source URL it displays) has not been altered either.
        if rec_rel:
            if rec_target is None or not rec_target.exists():
                print("FAIL  %s [record_seal] evidence-record.json missing: %s" % (record_id, rec_rel))
                failures += 1
            elif bundled is None:
                print("FAIL  %s [record_seal] evidence-record.json is not readable JSON" % record_id)
                failures += 1
            else:
                failures += check_record_seal(record_id, bundled)
                failures += check_capture_metadata(record_id, bundled)
                failures += check_attribution_seal(record_id, bundled)
    print()
    if failures:
        print("RESULT: FAIL - %d hash mismatch(es); these bytes do NOT match the recorded manifest." % failures)
        return 1
    print("RESULT: PASS - all %d record(s) match the recorded SHA-256 hashes." % len(records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def _naive_ts(ts: str) -> str:
    """Strip a trailing 'Z' or UTC offset so naive string comparison is correct.

    Mirrors ``audit_export._naive_ts``: canonical records store offset-aware or
    'Z'-suffixed timestamps, but the pack date bounds are naive.
    """
    ts = ts.strip()
    if not ts:
        return ts
    if ts.endswith("Z"):
        return ts[:-1]
    t_idx = ts.find("T")
    tail = ts[t_idx:] if t_idx != -1 else ts
    for sign in ("+", "-"):
        pos = tail.rfind(sign)
        if pos != -1:
            return (ts[:t_idx] if t_idx != -1 else "") + tail[:pos]
    return ts


def _safe_under_root(rel: str, root: Path) -> Path | None:
    """Resolve ``rel`` under ``root``; None if empty or escaping the workspace."""
    text = str(rel or "").strip()
    if not text:
        return None
    candidate = Path(text)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


def _safe_arc(value: str) -> str:
    """Sanitize a record_id for use as a ZIP path segment."""
    safe = "".join(c if (c.isalnum() or c in "._-") else "_" for c in value)
    return safe.strip("._-")[:120] or "record"
