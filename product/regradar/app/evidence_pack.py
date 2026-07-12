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
* A forbidden-claims guard (reusing the shared ``_FORBIDDEN_PHRASES`` tuple from
  ``app.monthly_assurance_report``) runs over the authored prose before it is
  written into the ZIP; a banned claim refuses the pack.
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
from app.monthly_assurance_report import _FORBIDDEN_PHRASES

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

    Reuses the exact ``_FORBIDDEN_PHRASES`` tuple shared across the product. The
    standard disclaimers legitimately *deny* forbidden claims (they contain
    "legal advice", "guarantee compliance", "prevent fines" in negated form), so
    both known-safe disclaimer strings are neutralized before scanning — the
    disclaimer can never trip its own guard, while any other banned phrase in
    authored prose still raises.
    """
    lowered = (
        str(text or "")
        .lower()
        .replace(LEGAL_DISCLAIMER.lower(), " ")
        .replace(FULL_LEGAL_DISCLAIMER.lower(), " ")
    )
    hits = sorted({phrase for phrase in _FORBIDDEN_PHRASES if phrase in lowered})
    if hits:
        raise EvidencePackError(
            "Evidence pack prose contains forbidden claim(s): " + ", ".join(hits)
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

    safe_id = _safe_arc(record_id)
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
        "raw_bytes": raw_bytes,
        "normalized_bytes": normalized_bytes,
        "record_bytes": record_path.read_bytes(),
        "raw_arcname": f"snapshots/{safe_id}/raw.txt",
        "normalized_arcname": f"snapshots/{safe_id}/normalized.txt",
        "record_arcname": f"snapshots/{safe_id}/evidence-record.json",
    }


def _build_manifest(
    entries: list[dict[str, Any]],
    wanted: set[str],
    date_from: str,
    date_to: str,
) -> dict[str, Any]:
    records = [
        {
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
        for e in entries
    ]
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
- `verify.py` — a standalone checker (Python standard library only, no
  StatuteProof imports).

## Verify with one command

From inside the unzipped pack folder:

```
python3 verify.py
```

For every record it re-reads the two snapshot files, recomputes each SHA-256,
and compares the result to `manifest.json`. It prints `PASS` when the bytes
match the recorded hash and `FAIL` when they do not, then exits non-zero if any
record fails. If a single byte of a snapshot is altered, its hash changes and
that record reports `FAIL`.

## Verify by hand (no scripts)

You can also confirm any record with your own tools, for example:

```
shasum -a 256 snapshots/<record_id>/normalized.txt
```

and check the value against `normalized_hash` for that record in
`manifest.json`. The raw side works the same way against `raw_hash`.

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
hashes recorded in manifest.json. Standard library only; no StatuteProof code
is required and no network access is used.

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


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    records = manifest.get("records", [])
    print("Verifying %d evidence record(s) against manifest.json\\n" % len(records))
    failures = 0
    for record in records:
        record_id = record.get("record_id", "<unknown>")
        for label, hash_key, file_key in (
            ("raw", "raw_hash", "raw_snapshot_file"),
            ("normalized", "normalized_hash", "normalized_snapshot_file"),
        ):
            rel = record.get(file_key)
            expected = str(record.get(hash_key) or "").lower().replace("sha256:", "")
            target = HERE / rel if rel else None
            if not rel or target is None or not target.exists():
                print("FAIL  %s [%s] snapshot file missing: %s" % (record_id, label, rel))
                failures += 1
                continue
            actual = sha256_file(target)
            if actual == expected:
                print("PASS  %s [%s] sha256=%s" % (record_id, label, actual))
            else:
                print("FAIL  %s [%s] expected=%s actual=%s" % (record_id, label, expected, actual))
                failures += 1
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
