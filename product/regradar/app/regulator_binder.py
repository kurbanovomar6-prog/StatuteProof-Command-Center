"""Regulator-ready Evidence Binder — the hand-it-to-an-examiner export.

THE ONE THING: a one-click, timestamped, hash-verified export of everything
StatuteProof captured on a chosen source over a chosen period, WITH the diffs and
an embedded, independently-checkable verification method, so an MLRO can hand it
to an examiner and it is credible WITHOUT trusting StatuteProof.

This is a period+source-scoped, multi-record extension of the self-serve Evidence
Pack (:mod:`app.evidence_pack`). It reuses that module's collector, path guards,
disclaimers, and the ``audit_export`` validators — it does not reinvent the zip /
manifest / verify machinery. What it adds on top of the Evidence Pack:

1. It INCLUDES each sealed canonical ``evidence-record.json`` (carrying the
   record's own ``record_hash`` over its ``content`` block) so the embedded
   verifier re-checks the record seal, not only the raw/normalized snapshots.
2. It includes the per-run diff artifact when one exists on the record.
3. It computes a binder-level ``binder_content_hash`` — the SHA-256 of the
   sorted list of every record's ``record_hash`` — so the binder itself is
   tamper-evident: add, drop, or alter any record and the binder hash diverges.
4. It ships a human-readable ``COVER.md`` — an honest "what changed and when"
   timeline built only from the records' own timestamps and summaries (no
   invented content), ending with the mandatory monitoring disclaimer verbatim.

Legal safety (non-negotiable): the authored, customer-facing ``COVER.md`` (and
the other authored prose) is run through the shared forbidden-claims guard
(:func:`app.legal_safety.assert_no_forbidden_claims`) before it is written into
the ZIP. The binder never asserts "certified", "court-ready", or "guarantee". An
empty range yields ``status == "empty"``, never a fake pack.

The builder never raises across its boundary: it returns
``{"status": "ok"|"empty"|"error", ...}`` so the API handler can respond without
leaking internal errors.
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
from app.evidence_pack import (
    FULL_LEGAL_DISCLAIMER,
    _collect_pack_entries,
    _naive_ts,
    _safe_arc,
    _safe_under_root,
)
from app.legal_safety import assert_no_forbidden_claims
from app.record_hashing import RECORD_HASH_METHOD

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent

# The published verification method the binder embeds and points at.
_SPEC_REFERENCE = "docs/EVIDENCE-VERIFICATION-SPEC.md"

# Mandatory short monitoring disclaimer (CLAUDE.md "Short (outreach)"). Embedded
# verbatim at the foot of COVER.md.
SHORT_MONITORING_DISCLAIMER = (
    "For monitoring information only. Not legal advice and not a guarantee of compliance."
)

# How ``binder_content_hash`` is derived, stamped into the manifest so a recipient
# can reproduce it (verify.py does exactly this).
_BINDER_HASH_METHOD = "sha256-of-sorted-record-hashes-v1"

# Keep a per-record COVER.md summary to one readable line.
_SUMMARY_MAX_CHARS = 220

# Hard cap on the number of evidence records a single binder may materialize. The
# binder loads every included record's raw + normalized + record (+ diff) bytes
# into memory before writing the ZIP, so an unbounded selection ("export a year
# across every source") could exhaust memory on the single-process server and
# take the platform down for all tenants. A binder handed to an examiner is a
# focused artifact (one or a few sources over a period), so this ceiling is well
# above any legitimate use; an oversized selection is rejected with guidance to
# narrow it rather than silently truncated (a truncated binder would be dishonest
# evidence). Enforced via the collector's ``limit`` so over-cap requests never
# load more than ``MAX_BINDER_RECORDS + 1`` records' bytes.
MAX_BINDER_RECORDS = 2000


def build_regulator_binder(
    source_ids: list[str],
    date_from: str,
    date_to: str,
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
    max_records: int = MAX_BINDER_RECORDS,
) -> dict[str, Any]:
    """Bundle a period+source-scoped, hash-verified evidence binder into a ZIP.

    For every ``record_status == "complete"`` / VERIFIED canonical evidence
    record whose capture timestamp falls in ``[date_from, date_to]`` and whose
    source is in ``source_ids``, the binder includes the sealed
    ``evidence-record.json`` (with its ``record_hash``), the ``raw.txt`` and
    ``normalized.txt`` snapshots, and the run diff when one exists — plus a
    machine ``manifest.json`` (with a binder-level content hash), a human
    ``COVER.md`` timeline, an offline ``verify.py``, and ``HOW-TO-VERIFY.md``.

    Source-scoping is data-level: a record for any source not named in
    ``source_ids`` is never included. Tenancy (owner scope) is enforced one layer
    up by the API handler via ``_entitle_source_ids`` before this is called.

    Returns
    -------
    dict
        ``{"status": "ok", "binder_path": str, "record_count": int, ...}`` on
        success, ``{"status": "empty", ...}`` when no records match, and
        ``{"status": "error", "message": str}`` on failure. Never raises.
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

        # Reuse the Evidence Pack collector: it already applies the SINGLE
        # complete/VERIFIED + in-range + source-scope + recorded-hash-consistency
        # policy, so the binder can never diverge from the pack on what evidence
        # is shippable.
        date_to_end = f"{date_to}T23:59:59"
        # Bounded collect: the collector stops after max_records + 1 entries, so an
        # oversized selection never materializes an unbounded number of records'
        # bytes in memory (the availability guard — see MAX_BINDER_RECORDS).
        base_entries = _collect_pack_entries(root, wanted, date_from, date_to_end, limit=max_records)
        if not base_entries:
            return {
                "status": "empty",
                "record_count": 0,
                "message": "No complete evidence records found for the specified period and sources.",
            }
        if len(base_entries) > max_records:
            return {
                "status": "too_large",
                "max_records": max_records,
                "message": (
                    f"This selection spans more than {max_records} captured records. "
                    "Narrow the period or the number of sources and export again — an "
                    "evidence binder for regulatory review is a focused artifact for one "
                    "or a few sources over a defined period."
                ),
            }

        entries = _augment_entries(base_entries, root)
        # Timeline + manifest order: chronological, then record_id for stability.
        entries.sort(key=lambda e: (_naive_ts(e["timestamp"]), e["record_id"]))

        binder_content_hash = _binder_content_hash([e["record_hash"] for e in entries])
        # Optional, additive: include the trail-level external RFC 3161 timestamp
        # when the operator enabled anchoring and a head-anchor sidecar exists.
        # Absence is silent (None => no manifest key, no embedded token).
        external_ts = _external_timestamp_section(root)
        manifest = _build_manifest(
            entries, wanted, date_from, date_to, binder_content_hash,
            external_ts[0] if external_ts else None,
        )
        cover = _render_cover(entries, wanted, date_from, date_to, binder_content_hash)
        how_to = _render_how_to_verify(manifest)
        verify_script = _VERIFY_SCRIPT

        # Legal-safety gate: refuse to ship any authored customer-facing text that
        # trips the shared forbidden-claims guard. COVER.md embeds per-record
        # summaries, so this also fail-closes if a source summary carried a banned
        # claim.
        assert_no_forbidden_claims(cover, label="Regulator binder cover")
        assert_no_forbidden_claims(how_to, label="Regulator binder how-to")
        assert_no_forbidden_claims(verify_script, label="Regulator binder verifier")

        binder_dir = output_dir or (root / "data" / "regulator_binders")
        binder_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        zip_name = f"regulator_binder_{date_from}_{date_to}_{stamp}.zip"
        zip_path = binder_dir / zip_name

        manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", manifest_json)
            zf.writestr("COVER.md", cover)
            zf.writestr("HOW-TO-VERIFY.md", how_to)
            zf.writestr("verify.py", verify_script)
            zf.writestr("DISCLAIMER.txt", f"{LEGAL_DISCLAIMER}\n\n{FULL_LEGAL_DISCLAIMER}\n")
            for entry in entries:
                zf.writestr(entry["raw_arcname"], entry["raw_bytes"])
                zf.writestr(entry["normalized_arcname"], entry["normalized_bytes"])
                zf.writestr(entry["record_arcname"], entry["record_bytes"])
                if entry.get("diff_arcname") and entry.get("diff_bytes") is not None:
                    zf.writestr(entry["diff_arcname"], entry["diff_bytes"])
            if external_ts is not None:
                zf.writestr(external_ts[0]["token_file"], external_ts[1])

        return {
            "status": "ok",
            "binder_path": str(zip_path.resolve()),
            "binder_filename": zip_name,
            "record_count": len(entries),
            "source_count": len({e["source_id"] for e in entries}),
            "diff_count": sum(1 for e in entries if e.get("diff_arcname")),
            "has_external_timestamp": external_ts is not None,
            "date_from": date_from,
            "date_to": date_to,
            "binder_content_hash": binder_content_hash,
            "manifest": manifest,
            "disclaimer": LEGAL_DISCLAIMER,
        }
    except Exception as exc:  # never raise across the boundary
        logger.error("build_regulator_binder: unexpected error: %s", type(exc).__name__)
        return {"status": "error", "message": str(exc)}


# ── internal helpers ────────────────────────────────────────────────────────────

def _augment_entries(base_entries: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    """Enrich each reused pack entry with its record seal + diff artifact.

    The Evidence Pack collector returns raw/normalized bytes and the sealed
    ``record_bytes`` (the ``evidence-record.json``) but not the record's own
    ``record_hash`` or diff. Parse the record once to lift those out, and read the
    diff file when the record references one.
    """
    augmented: list[dict[str, Any]] = []
    seen_arcnames: set[str] = set()
    for entry in base_entries:
        try:
            record = json.loads(entry["record_bytes"].decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            logger.warning("regulator_binder: unreadable record for %s; skipping", entry.get("record_id"))
            continue
        if not isinstance(record, dict):
            continue

        record_hash = str(record.get("record_hash") or "").strip().lower().removeprefix("sha256:")
        if not record_hash:
            # No self-seal on the record → cannot make it independently checkable.
            logger.warning("regulator_binder: record %s has no record_hash; skipping", entry.get("record_id"))
            continue

        change = record.get("change")
        if not isinstance(change, dict):
            change = {}
        files = record.get("files")
        if not isinstance(files, dict):
            files = {}
        summary = _one_line(str(change.get("summary") or ""))

        # Defensive uniqueness: two record_ids must never sanitize to the same
        # snapshot arcname, or one record's evidence would silently overwrite
        # another's in the ZIP — dishonest in an artifact whose whole point is
        # verifiability. record_ids are system-generated and unique today, so a
        # collision would signal an upstream ID-format change; skip + log rather
        # than double-write.
        if entry["record_arcname"] in seen_arcnames:
            logger.warning(
                "regulator_binder: duplicate snapshot arcname for %s; skipping to avoid overwrite",
                entry.get("record_id"),
            )
            continue
        seen_arcnames.add(entry["record_arcname"])

        merged = dict(entry)
        merged["record_hash"] = record_hash
        merged["record_hash_method"] = str(record.get("record_hash_method") or RECORD_HASH_METHOD)
        merged["summary"] = summary

        diff_rel = str(change.get("diff_path") or files.get("diff_path") or "").strip()
        if diff_rel:
            diff_path = _safe_under_root(diff_rel, root)
            if diff_path is not None and diff_path.exists():
                safe_id = _safe_arc(entry["record_id"])
                merged["diff_bytes"] = diff_path.read_bytes()
                merged["diff_arcname"] = f"snapshots/{safe_id}/diff.txt"
        augmented.append(merged)
    return augmented


def _binder_content_hash(record_hashes: list[str]) -> str:
    """SHA-256 over the sorted, newline-joined list of bare record hashes.

    Deterministic and reproducible offline (verify.py recomputes it identically):
    normalize each hash to bare lowercase hex, drop blanks, sort ascending, join
    with a single newline, and hash the UTF-8 bytes. Any record added, dropped, or
    altered changes the set of record hashes and therefore this digest.
    """
    bare = sorted(
        h.strip().lower().removeprefix("sha256:") for h in record_hashes if str(h or "").strip()
    )
    return hashlib.sha256("\n".join(bare).encode("utf-8")).hexdigest()


def _external_timestamp_section(root: Path) -> tuple[dict[str, Any], bytes] | None:
    """Return (manifest section, raw token bytes) for the trail head anchor, or None.

    Reads the ADDITIVE head-anchor sidecar (``data/evidence_chain_head.tsr.json``)
    written by :mod:`app.rfc3161_anchor` when the operator enabled anchoring. When no
    sidecar / token exists (the default), returns ``None`` and the binder simply omits
    the section — absence is silent. Never raises.

    Scope honesty: this timestamp anchors the monitored TRAIL's head ``record_hash``
    as a whole at the asserted time. It is a supplementary integrity signal; it does
    not individually attest any single record included in this binder.
    """
    try:
        from app.rfc3161_anchor import SIDECAR_TSR_NAME, read_head_anchor_sidecar

        head_file = root / "data" / "evidence_chain_head.json"
        sidecar = read_head_anchor_sidecar(head_file)
        if not sidecar:
            return None
        token_b64 = str(sidecar.get("token_b64") or "").strip()
        if not token_b64:
            return None
        import base64

        token_bytes = base64.b64decode(token_b64)
        section = {
            "token_file": f"external_timestamp/{SIDECAR_TSR_NAME}",
            "token_format": sidecar.get("token_format"),
            "tsa_url": sidecar.get("tsa_url"),
            "digest_algorithm": sidecar.get("digest_algorithm"),
            "anchored_head_record_hash": sidecar.get("anchored_head_record_hash"),
            "asserted_time_utc": sidecar.get("asserted_time_utc"),
            "requested_at": sidecar.get("requested_at"),
            "scope_note": (
                "Third-party RFC 3161 timestamp over the monitored trail's head "
                "record_hash. It anchors the trail as a whole at the asserted time; "
                "it does not individually attest any single record in this binder."
            ),
        }
        return section, token_bytes
    except Exception:
        return None


def _build_manifest(
    entries: list[dict[str, Any]],
    wanted: set[str],
    date_from: str,
    date_to: str,
    binder_content_hash: str,
    external_timestamp: dict[str, Any] | None = None,
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
            "record_hash": e["record_hash"],
            "record_hash_method": e["record_hash_method"],
            "raw_snapshot_file": e["raw_arcname"],
            "normalized_snapshot_file": e["normalized_arcname"],
            "evidence_record_file": e["record_arcname"],
        }
        if e.get("diff_arcname"):
            row["diff_file"] = e["diff_arcname"]
        records.append(row)
    manifest: dict[str, Any] = {
        "pack_type": "statuteproof_regulator_binder",
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hash_algorithm": "sha256",
        "record_hash_method": RECORD_HASH_METHOD,
        "binder_content_hash": binder_content_hash,
        "binder_content_hash_method": _BINDER_HASH_METHOD,
        "binder_content_hash_input": (
            "sha256 of the record_hash values below, normalized to bare lowercase hex, "
            "sorted ascending and joined with a single newline (\\n)."
        ),
        "date_from": date_from,
        "date_to": date_to,
        "source_ids": sorted(wanted),
        "record_count": len(records),
        "diff_count": sum(1 for r in records if r.get("diff_file")),
        "spec_reference": _SPEC_REFERENCE,
        "verification": (
            "Run `python3 verify.py` from inside this unzipped binder to recompute "
            "every snapshot SHA-256, re-seal every evidence-record.json, and "
            "recompute the binder content hash — all offline, with no StatuteProof "
            "software and no network."
        ),
        "legal_disclaimer": LEGAL_DISCLAIMER,
        "legal_notice": FULL_LEGAL_DISCLAIMER,
        "records": records,
    }
    # Additive, optional: a trail-level external RFC 3161 timestamp, included only
    # when the operator has enabled anchoring and a head-anchor sidecar exists.
    # Absence is silent (no key). It never affects the binder's verify result.
    if external_timestamp:
        manifest["external_timestamp"] = external_timestamp
    return manifest


def _render_cover(
    entries: list[dict[str, Any]],
    wanted: set[str],
    date_from: str,
    date_to: str,
    binder_content_hash: str,
) -> str:
    """Plain, honest "what changed and when" timeline. No invented content."""
    source_names = sorted({e["source_name"] for e in entries}) or sorted(wanted)
    lines = [
        "# Evidence binder for regulatory review",
        "",
        LEGAL_DISCLAIMER,
        "",
        "## What this binder covers",
        "",
        f"- Source(s): {', '.join(source_names)}",
        f"- Period (UTC): {date_from} to {date_to}",
        f"- Records captured in range: {len(entries)}",
        f"- Binder content hash (sha256): `{binder_content_hash}`",
        "",
        "Every record below is included with its raw and normalized snapshots, its "
        "sealed evidence record, and — where a change was detected — the diff. The "
        "binder content hash above is the SHA-256 of the sorted list of the record "
        "hashes; if any record is added, removed, or altered, it changes.",
        "",
        "## Timeline of captured changes",
        "",
    ]
    for e in entries:
        summary = e.get("summary") or "Captured state (no summary recorded)."
        short_hash = e["record_hash"][:12]
        lines.append(
            f"- {e['timestamp']} — {e['source_name']} — {summary} "
            f"(record `{e['record_id']}`, seal `{short_hash}…`)"
        )
    lines.extend([
        "",
        "## How to verify this binder yourself",
        "",
        "You do not have to trust StatuteProof. From inside the unzipped binder run:",
        "",
        "```",
        "python3 verify.py",
        "```",
        "",
        "It re-reads every snapshot, recomputes each SHA-256, re-seals every "
        "`evidence-record.json` (recomputing `record_hash` from its `content` block), "
        "and recomputes the binder content hash — all offline. See `HOW-TO-VERIFY.md` "
        f"and the open verification specification at `{_SPEC_REFERENCE}`.",
        "",
        "## What this binder is and is not",
        "",
        "This binder is monitoring evidence: the bytes captured from monitored "
        "official sources, the hashes recorded for them, and the diffs between "
        "captured states, so their integrity can be independently confirmed. It is "
        "not a legal opinion, not a certification, and it does not interpret the "
        "regulatory text or determine any obligation. Whether a change matters for "
        "your obligations is a question for your own qualified advisers.",
        "",
        "---",
        "",
        SHORT_MONITORING_DISCLAIMER,
        "",
    ])
    return "\n".join(lines)


def _render_how_to_verify(manifest: dict[str, Any]) -> str:
    count = manifest.get("record_count", 0)
    return f"""# How to verify this evidence binder yourself

{LEGAL_DISCLAIMER}

This binder contains {count} official-source monitoring record(s) that StatuteProof
captured over the period, together with the SHA-256 hashes it recorded at capture
time, the diffs between captured states, and each record's own self-seal. You do
not have to take any of it on trust: you can re-compute every hash yourself,
offline, with nothing but a standard Python 3 install.

## What is in this binder

- `manifest.json` — one entry per record: the raw SHA-256, the normalized SHA-256,
  the record self-seal (`record_hash`), the snapshot / evidence-record / diff
  filenames, the capture timestamp, the source, and the official URL — plus a
  binder-level `binder_content_hash` over the sorted record hashes.
- `COVER.md` — a plain, honest timeline of what changed and when for the period.
- `snapshots/<record_id>/raw.txt` — the raw captured text of the official page.
- `snapshots/<record_id>/normalized.txt` — the normalized text StatuteProof hashed
  for change detection.
- `snapshots/<record_id>/evidence-record.json` — the canonical, self-sealed record.
- `snapshots/<record_id>/diff.txt` — the diff against the previous captured state
  (present only where a change was detected).
- `verify.py` — a standalone checker (Python standard library only, no StatuteProof
  imports, no network).

## Verify with one command

From inside the unzipped binder folder:

```
python3 verify.py
```

For every record it (1) re-reads the raw and normalized snapshots and recomputes
each SHA-256; (2) re-seals the `evidence-record.json` by recomputing `record_hash`
over its `content` block exactly as the published method describes; and (3) checks
the binder-level `binder_content_hash`. It prints `PASS` / `FAIL` per check and
exits non-zero if anything fails. If a single byte of any snapshot or record is
altered, its hash changes and that check reports `FAIL`.

## Verify by hand (no scripts)

You can confirm any snapshot with your own tools, for example:

```
shasum -a 256 snapshots/<record_id>/normalized.txt
```

and check the value against `normalized_hash` for that record in `manifest.json`.
The raw side works the same way against `raw_hash`.

## The published method

The exact construction of every hash — raw, normalized, `record_hash`
(`content-sha256-v1`), the previous-hash chain, and the head anchor — is documented,
without secrets, in `{manifest.get("spec_reference", _SPEC_REFERENCE)}`. Verification
uses only standard SHA-256 over the bytes in your hand; nothing about it requires
trusting StatuteProof's servers.

## What this binder is and is not

This binder is monitoring evidence: the captured bytes, the recorded hashes, and
the diffs, so you can independently confirm the records have not been altered since
capture. It is not a legal opinion and it does not interpret the regulatory text.

---

{FULL_LEGAL_DISCLAIMER}
"""


def _one_line(text: str) -> str:
    """Collapse a summary to a single trimmed line for the COVER.md timeline."""
    collapsed = " ".join(str(text or "").split())
    if len(collapsed) > _SUMMARY_MAX_CHARS:
        collapsed = collapsed[: _SUMMARY_MAX_CHARS - 1].rstrip() + "…"
    return collapsed


# Standalone verifier shipped inside the binder. Standard library only, no app
# imports, so a recipient's auditor can run it on any Python 3 without installing
# anything. It goes beyond the Evidence Pack verifier: it also re-seals every
# included evidence-record.json and recomputes the binder content hash.
_VERIFY_SCRIPT = '''#!/usr/bin/env python3
"""Standalone StatuteProof regulator-binder verifier.

Recompute, entirely offline, (1) the SHA-256 of every snapshot in this binder,
(2) the self-seal (record_hash) of every evidence-record.json, and (3) the
binder-level content hash — and compare each against manifest.json. Standard
library only; no StatuteProof code is required and no network access is used.

Usage:  python3 verify.py        (run from inside the unzipped binder)

For monitoring information only. Not legal advice and not a guarantee of compliance.
This re-hashes the bytes in this
binder against the SHA-256 values StatuteProof recorded when it captured them, so
you can independently confirm they have not been altered. It is not a legal
opinion and not a certification.
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


def canonical_record_hash(content):
    """Reproduce app/record_hashing.py::canonical_record_hash (content-sha256-v1).

    Compact (no spaces), sorted-key, non-ASCII-preserving UTF-8 JSON of the
    record's content block, SHA-256'd. Byte-stable across machines.
    """
    payload = json.dumps(
        content, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def bare(value):
    return str(value or "").strip().lower().replace("sha256:", "")


def main():
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    records = manifest.get("records", [])
    print("Verifying %d record(s) in this regulator binder against manifest.json\\n" % len(records))
    failures = 0

    for record in records:
        record_id = record.get("record_id", "<unknown>")

        # (1) snapshot hashes
        for label, hash_key, file_key in (
            ("raw", "raw_hash", "raw_snapshot_file"),
            ("normalized", "normalized_hash", "normalized_snapshot_file"),
        ):
            rel = record.get(file_key)
            expected = bare(record.get(hash_key))
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

        # (2) record self-seal — re-hash the content block and compare to record_hash
        rec_rel = record.get("evidence_record_file")
        rec_path = HERE / rec_rel if rec_rel else None
        expected_seal = bare(record.get("record_hash"))
        if not rec_rel or rec_path is None or not rec_path.exists():
            print("FAIL  %s [seal] evidence record missing: %s" % (record_id, rec_rel))
            failures += 1
        else:
            try:
                sealed = json.loads(rec_path.read_text(encoding="utf-8"))
                content = sealed.get("content")
                method = str(sealed.get("record_hash_method") or "").strip()
                stored = bare(sealed.get("record_hash"))
                if method != "content-sha256-v1" or not isinstance(content, dict):
                    print("FAIL  %s [seal] unexpected record_hash_method: %s" % (record_id, method))
                    failures += 1
                else:
                    actual_seal = canonical_record_hash(content)
                    if actual_seal == expected_seal and actual_seal == stored:
                        print("PASS  %s [seal] record_hash=%s" % (record_id, actual_seal))
                    else:
                        print("FAIL  %s [seal] manifest=%s stored=%s recomputed=%s" % (
                            record_id, expected_seal, stored, actual_seal))
                        failures += 1
            except (ValueError, OSError) as exc:
                print("FAIL  %s [seal] could not read/parse record: %s" % (record_id, exc))
                failures += 1

    # (3) binder-level content hash over the sorted record hashes
    expected_binder = bare(manifest.get("binder_content_hash"))
    hashes = sorted(bare(r.get("record_hash")) for r in records if bare(r.get("record_hash")))
    actual_binder = hashlib.sha256("\\n".join(hashes).encode("utf-8")).hexdigest()
    print()
    if actual_binder == expected_binder:
        print("PASS  binder_content_hash=%s" % actual_binder)
    else:
        print("FAIL  binder_content_hash expected=%s actual=%s" % (expected_binder, actual_binder))
        failures += 1

    # (4) OPTIONAL: report an external RFC 3161 timestamp anchor when present.
    # Additive and advisory — it does NOT affect the pass/fail result above. This
    # standalone script stays stdlib-only, so it reports the token and shows how to
    # verify it independently rather than embedding an ASN.1 verifier.
    ext = manifest.get("external_timestamp")
    if ext:
        print()
        print("External RFC 3161 timestamp anchor present (trail-level, supplementary):")
        print("  TSA URL:                   %s" % ext.get("tsa_url"))
        print("  Asserted time (UTC):       %s" % ext.get("asserted_time_utc"))
        print("  Anchored head record_hash: %s" % ext.get("anchored_head_record_hash"))
        print("  Token file:                %s" % ext.get("token_file"))
        print("  Note: %s" % ext.get("scope_note"))
        print("  Verify independently against your own trusted TSA root(s), e.g.:")
        print("    openssl ts -verify -in %s -digest %s -CAfile <your-tsa-ca.pem>" % (
            ext.get("token_file"), ext.get("anchored_head_record_hash")))

    print()
    if failures:
        print("RESULT: FAIL - %d mismatch(es); these bytes do NOT match the recorded manifest." % failures)
        return 1
    print("RESULT: PASS - all %d record(s), their seals, and the binder hash match." % len(records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
