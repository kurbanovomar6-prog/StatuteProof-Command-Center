"""
Read-only evidence-trail integrity verifier.

This is the keystone that proves the StatuteProof product promise: *hashes
prove content*. For every source run that stored snapshot files, this tool
re-reads the stored snapshot bytes and recomputes — using the SAME hashing
functions the pipeline uses (``app.text_normalization``) — the hashes the
record claims. A divergence means the stored bytes no longer match the stored
hash: either the snapshot was corrupted/tampered with, or the record's hash is
wrong. Either way the evidence record can no longer be trusted.

Guarantees / non-goals:
  * READ-ONLY. It never writes, moves, deletes, or repairs anything.
  * No network. It only touches the local evidence trail on disk.
  * It reuses ``app.source_runs`` for trail reading and path resolution, so it
    verifies the exact same records and snapshot files the pipeline writes.

Verification model (both hash flavors the codebase produces are accepted):

  raw_hash
      sha256 of the exact ``raw.txt`` bytes (``_raw_hash`` in source_runs).

  normalized_hash — two legitimate flavors exist in the trail:
      A. monitor/intake path (``record_from_source_result``):
             stable_normalized_hash(raw)  ==  sha256(normalize_for_change_hash(raw))
         which also equals sha256 of the stored ``normalized.txt`` bytes.
      B. rebaseline path (``rebaseline_source`` overwrites the field):
             stable_content_hash(normalize_for_change_hash(raw))
      Because ``normalize_for_change_hash`` is idempotent, both flavors reduce
      to functions of the stored ``normalized.txt`` bytes alone — so the stored
      normalized_hash is recomputed strictly from that file (any tampering with
      it breaks every candidate). Two independent checks then close the gaps:
        * raw_hash proves ``raw.txt`` was not altered, and
        * normalize(raw.txt) == normalized.txt proves the two snapshots are
          mutually consistent (a swapped raw.txt whose normalization no longer
          matches the stored normalized.txt is caught even here).

Outcomes per record:
  verified      — every stored hash that could be checked matched.
  divergent     — at least one stored hash did NOT match the stored bytes.
  unverifiable  — no snapshot paths, or the referenced snapshot files are
                  missing (legacy/compacted records). Never counted as failed.

Exit codes:
  0  no divergence found (records may be verified and/or unverifiable).
  1  at least one divergence found.
  2  bad CLI arguments.

Usage:
    python tools/verify_evidence_trail.py
    python tools/verify_evidence_trail.py --json
    python tools/verify_evidence_trail.py --source-id AE-vara-rulebook
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# sys.path bootstrap — make app/ importable when run directly from the repo
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).resolve().parent
_PRODUCT_DIR = _TOOLS_DIR.parent  # .../product/regradar
if str(_PRODUCT_DIR) not in sys.path:
    sys.path.insert(0, str(_PRODUCT_DIR))


# ---------------------------------------------------------------------------
# imports (after sys.path is set)
# ---------------------------------------------------------------------------

from app import source_runs  # noqa: E402  (module import so tests can patch dirs)
from app.source_runs import compute_record_hash  # noqa: E402
from app.text_normalization import (  # noqa: E402
    normalize_for_change_hash,
    stable_content_hash,
)


# ---------------------------------------------------------------------------
# result model
# ---------------------------------------------------------------------------

# Verification status constants for a single record.
STATUS_VERIFIED = "verified"
STATUS_DIVERGENT = "divergent"
STATUS_UNVERIFIABLE = "unverifiable"


@dataclass(frozen=True)
class HashCheck:
    """The result of verifying one stored hash against its snapshot bytes."""

    kind: str  # "raw" | "normalized"
    snapshot_path: str
    stored_hash: str
    recomputed_hash: str  # the primary recomputed candidate (for reporting)
    matched: bool


@dataclass
class RecordResult:
    """The verification outcome for a single trail record."""

    source_id: str
    run_id: str
    status: str
    checks: list[HashCheck] = field(default_factory=list)
    reason: str | None = None  # why unverifiable / what diverged

    def as_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "run_id": self.run_id,
            "status": self.status,
            "reason": self.reason,
            "checks": [
                {
                    "kind": c.kind,
                    "snapshot_path": c.snapshot_path,
                    "stored_hash": c.stored_hash,
                    "recomputed_hash": c.recomputed_hash,
                    "matched": c.matched,
                }
                for c in self.checks
            ],
        }


# Chain verification status constants.
CHAIN_OK = "ok"
CHAIN_BROKEN = "broken"
CHAIN_EMPTY = "empty"  # no chained records present (all legacy / empty trail)


@dataclass
class ChainResult:
    """Outcome of verifying the tamper-evident hash chain over the trail.

    The chain is verified in file order (the order records were appended), which
    is exactly how it is constructed: every record's ``prev_record_hash`` points
    at the record_hash of the immediately preceding chained trail line. Only the
    FIRST broken link is reported — once the chain breaks, everything after it is
    already unprovable, so the first break is the actionable fact.
    """

    status: str = CHAIN_EMPTY
    checked: int = 0  # number of chained records verified before the break/end
    break_index: int | None = None  # 0-based index (among chained records) of the break
    break_source_id: str | None = None
    break_run_id: str | None = None
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.status != CHAIN_BROKEN

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "ok": self.ok,
            "checked": self.checked,
            "break_index": self.break_index,
            "break_source_id": self.break_source_id,
            "break_run_id": self.break_run_id,
            "reason": self.reason,
        }


def verify_chain(records: list[dict]) -> ChainResult:
    """Verify the tamper-evident hash chain over the trail records in order.

    Tolerates legacy pre-chain records: the chain "starts" at the first record
    that carries a ``record_hash``. From that point every record must satisfy
    two invariants, or the FIRST failing record is reported:

      1. ``prev_record_hash`` equals the previous chained record's stored
         ``record_hash`` ("" for the first chained record), and
      2. ``record_hash`` recomputes from the record's identifying fields
         (via ``source_runs.compute_record_hash``).

    Inserting, deleting, reordering, or editing any identifying field of a
    chained record breaks one of these invariants at that record. A legacy
    record appearing AFTER the chain has started (i.e. a chained record without
    a record_hash) is itself a break — the chain must be continuous once begun.
    """
    result = ChainResult()
    prev_hash = ""
    started = False
    chained_seen = 0

    for record in records:
        stored_hash = str(record.get("record_hash") or "")

        if not started:
            if not stored_hash:
                # Legacy pre-chain record before the chain begins — skip.
                continue
            started = True

        source_id = str(record.get("source_id") or "")
        run_id = str(record.get("run_id") or "")

        # A record with no record_hash after the chain has started breaks it.
        if not stored_hash:
            result.status = CHAIN_BROKEN
            result.checked = chained_seen
            result.break_index = chained_seen
            result.break_source_id = source_id
            result.break_run_id = run_id
            result.reason = "chained trail contains a record with no record_hash"
            return result

        # Invariant 1: prev pointer must match the prior record_hash.
        stored_prev = str(record.get("prev_record_hash") or "")
        if stored_prev != prev_hash:
            expected_disp = (prev_hash[:16] + "…") if prev_hash else '""'
            got_disp = (stored_prev[:16] + "…") if stored_prev else '""'
            result.status = CHAIN_BROKEN
            result.checked = chained_seen
            result.break_index = chained_seen
            result.break_source_id = source_id
            result.break_run_id = run_id
            result.reason = (
                "prev_record_hash does not match the preceding record_hash "
                f"(expected {expected_disp}, got {got_disp})"
            )
            return result

        # Invariant 2: record_hash must recompute from identifying fields.
        recomputed = compute_record_hash(record, stored_prev)
        if recomputed != stored_hash:
            result.status = CHAIN_BROKEN
            result.checked = chained_seen
            result.break_index = chained_seen
            result.break_source_id = source_id
            result.break_run_id = run_id
            result.reason = (
                "record_hash does not recompute from identifying fields "
                f"(stored {stored_hash[:16]}…, recomputed {recomputed[:16]}…)"
            )
            return result

        chained_seen += 1
        prev_hash = stored_hash

    result.checked = chained_seen
    result.status = CHAIN_OK if chained_seen else CHAIN_EMPTY
    return result


@dataclass
class TrailReport:
    """Aggregate verification report over the whole evidence trail."""

    records: list[RecordResult] = field(default_factory=list)
    chain: ChainResult = field(default_factory=ChainResult)

    @property
    def verified(self) -> list[RecordResult]:
        return [r for r in self.records if r.status == STATUS_VERIFIED]

    @property
    def divergent(self) -> list[RecordResult]:
        return [r for r in self.records if r.status == STATUS_DIVERGENT]

    @property
    def unverifiable(self) -> list[RecordResult]:
        return [r for r in self.records if r.status == STATUS_UNVERIFIABLE]

    @property
    def ok(self) -> bool:
        """True when no record diverged AND the hash chain is intact.

        Unverifiable records do not fail. A broken chain (tamper-evident
        append-only violation) does fail — but an empty/all-legacy chain is
        fine (nothing to prove yet).
        """
        return not self.divergent and self.chain.ok

    def per_source(self) -> dict[str, dict[str, int]]:
        """Per-source tally of verified / divergent / unverifiable counts."""
        tally: dict[str, dict[str, int]] = {}
        for r in self.records:
            bucket = tally.setdefault(
                r.source_id or "(unknown)",
                {STATUS_VERIFIED: 0, STATUS_DIVERGENT: 0, STATUS_UNVERIFIABLE: 0},
            )
            bucket[r.status] += 1
        return tally

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "totals": {
                "records": len(self.records),
                STATUS_VERIFIED: len(self.verified),
                STATUS_DIVERGENT: len(self.divergent),
                STATUS_UNVERIFIABLE: len(self.unverifiable),
            },
            "chain": self.chain.as_dict(),
            "per_source": self.per_source(),
            "records": [r.as_dict() for r in self.records],
        }


# ---------------------------------------------------------------------------
# snapshot IO (read-only, via source_runs path resolution)
# ---------------------------------------------------------------------------

def _resolve_snapshot(rel_path: str | None) -> Path | None:
    """Resolve a stored (relative) snapshot path to an absolute Path or None.

    Reuses ``source_runs._path_from_rel`` so the base-dir anchoring — and its
    path-traversal guard — is identical to the write side. Tests patch the
    ``source_runs`` module dirs, so this resolves against the isolated trail.
    """
    return source_runs._path_from_rel(rel_path)


def _read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decode(data: bytes) -> str:
    # Snapshots are written as UTF-8 text; decode the same way for re-normalizing.
    return data.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# per-record verification
# ---------------------------------------------------------------------------

def _normalized_candidates(normalized_bytes: bytes) -> set[str]:
    """All legitimate recomputed hash values a stored normalized_hash may equal.

    Recomputed strictly from the stored ``normalized.txt`` bytes — the file that
    the ``normalized_hash`` actually backs — so any tampering with that file
    breaks every candidate and surfaces as a divergence. This is sound because
    ``normalize_for_change_hash`` is idempotent: normalizing already-normalized
    text is a no-op, so both stored flavors reduce to functions of the stored
    normalized bytes:

      * flavor A (monitor/intake path, ``record_from_source_result``):
            stored == sha256(normalize_for_change_hash(raw))
                   == sha256(normalized.txt bytes)          [idempotent]
      * flavor B (rebaseline path, ``rebaseline_source`` overwrites the field):
            stored == stable_content_hash(normalize_for_change_hash(raw))
                   == stable_content_hash(normalized.txt)   [idempotent]
    """
    normalized_text = _decode(normalized_bytes)

    candidates: set[str] = set()

    # flavor A: sha256 of the normalized bytes (also == stable_normalized_hash
    # of the normalized text, since normalization is idempotent).
    candidates.add(_sha256(normalized_bytes))

    # flavor B: whitespace-collapsed content hash of the normalized text.
    flavor_b = stable_content_hash(normalized_text)
    if flavor_b:
        candidates.add(flavor_b)

    return candidates


def verify_record(record: dict) -> RecordResult:
    """Verify one trail record's stored hashes against its snapshot bytes."""
    source_id = str(record.get("source_id") or "")
    run_id = str(record.get("run_id") or "")

    raw_rel = record.get("snapshot_raw_path")
    norm_rel = record.get("snapshot_normalized_path")

    # No snapshot paths at all → legacy / compact (heartbeat) record: skip.
    if not raw_rel and not norm_rel:
        return RecordResult(
            source_id=source_id,
            run_id=run_id,
            status=STATUS_UNVERIFIABLE,
            reason="no snapshot paths recorded",
        )

    checks: list[HashCheck] = []
    diverged: list[str] = []
    checked_any = False
    missing: list[str] = []

    raw_path = _resolve_snapshot(raw_rel)
    norm_path = _resolve_snapshot(norm_rel)
    raw_bytes = _read_bytes(raw_path) if raw_path is not None else None
    norm_bytes = _read_bytes(norm_path) if norm_path is not None else None

    # ── raw_hash: sha256 of the exact raw.txt bytes ───────────────────────
    stored_raw_hash = record.get("raw_hash")
    if stored_raw_hash:
        if raw_bytes is None:
            missing.append(f"raw snapshot missing ({raw_rel})")
        else:
            recomputed = _sha256(raw_bytes)
            matched = recomputed == stored_raw_hash
            checks.append(
                HashCheck(
                    kind="raw",
                    snapshot_path=str(raw_rel),
                    stored_hash=str(stored_raw_hash),
                    recomputed_hash=recomputed,
                    matched=matched,
                )
            )
            checked_any = True
            if not matched:
                diverged.append("raw_hash != sha256(raw.txt)")

    # ── normalized_hash: match any legitimate recomputed flavor ───────────
    stored_norm_hash = record.get("normalized_hash")
    if stored_norm_hash:
        if norm_bytes is None:
            missing.append(f"normalized snapshot missing ({norm_rel})")
        else:
            # Recompute strictly from the normalized.txt bytes (the file the
            # hash backs) so tampering with that file is always detected.
            candidates = _normalized_candidates(norm_bytes)
            matched = stored_norm_hash in candidates
            # Report flavor A (sha256 of the normalized bytes) as the recompute.
            primary = _sha256(norm_bytes)
            checks.append(
                HashCheck(
                    kind="normalized",
                    snapshot_path=str(norm_rel),
                    stored_hash=str(stored_norm_hash),
                    recomputed_hash=primary,
                    matched=matched,
                )
            )
            checked_any = True
            if not matched:
                diverged.append("normalized_hash matches no recomputed flavor")

    # ── cross-consistency: normalized.txt must be the normalization of raw.txt
    # Catches a raw.txt that was swapped for different content whose normalized
    # form no longer matches the stored normalized.txt (even independent of the
    # stored hashes). Only meaningful when both snapshot files are present.
    if raw_bytes is not None and norm_bytes is not None:
        rederived = normalize_for_change_hash(_decode(raw_bytes))
        stored_normalized = _decode(norm_bytes)
        if rederived != stored_normalized:
            checked_any = True
            diverged.append("normalize(raw.txt) != normalized.txt")

    if diverged:
        return RecordResult(
            source_id=source_id,
            run_id=run_id,
            status=STATUS_DIVERGENT,
            checks=checks,
            reason="; ".join(diverged),
        )

    if not checked_any:
        # Snapshot paths were recorded but the files/hashes could not be
        # checked (files gone, or no hashes stored) → unverifiable, not failed.
        reason = "; ".join(missing) if missing else "no verifiable hashes on record"
        return RecordResult(
            source_id=source_id,
            run_id=run_id,
            status=STATUS_UNVERIFIABLE,
            checks=checks,
            reason=reason,
        )

    return RecordResult(
        source_id=source_id,
        run_id=run_id,
        status=STATUS_VERIFIED,
        checks=checks,
        reason="; ".join(missing) if missing else None,
    )


# ---------------------------------------------------------------------------
# trail-level verification
# ---------------------------------------------------------------------------

def verify_trail(source_id: str | None = None) -> TrailReport:
    """Walk the evidence trail and verify every record's snapshot hashes.

    Reads records via ``source_runs._read_runs`` so the same trail file (and
    the same cache/inode semantics) the pipeline writes is what we verify.
    ``source_id`` optionally restricts the per-record snapshot-hash checks to
    one source.

    The tamper-evident hash chain (G-hashchain) is verified over the FULL
    trail in file order regardless of ``source_id`` — the chain is global (each
    record links to the immediately preceding trail line), so a source filter
    cannot be applied without breaking the linkage. The chain result therefore
    always reflects the whole trail.
    """
    all_records = list(source_runs._read_runs())

    report = TrailReport()
    for record in all_records:
        if source_id and str(record.get("source_id") or "") != source_id:
            continue
        report.records.append(verify_record(record))

    report.chain = verify_chain(all_records)
    return report


# ---------------------------------------------------------------------------
# CLI rendering
# ---------------------------------------------------------------------------

def _chain_lines(chain: ChainResult) -> list[str]:
    """Render the hash-chain verdict block."""
    out: list[str] = []
    if chain.status == CHAIN_OK:
        out.append(f"Hash chain: intact — {chain.checked} chained record(s) verified.")
    elif chain.status == CHAIN_EMPTY:
        out.append("Hash chain: none (no chained records yet — legacy/empty trail).")
    else:  # CHAIN_BROKEN
        out.append("Hash chain: BROKEN — tamper-evident linkage failed.")
        out.append(
            f"  ✗ first break at chained index {chain.break_index} "
            f"({chain.break_source_id} / {chain.break_run_id}): {chain.reason}"
        )
        out.append(f"  {chain.checked} record(s) verified before the break.")
    return out


def _render_text(report: TrailReport) -> str:
    lines: list[str] = []
    lines.append("StatuteProof — Evidence Trail Integrity Verifier")
    lines.append("=" * 64)
    if not report.records:
        lines.append("No source run records found in the evidence trail.")
        lines.append("")
        lines.extend(_chain_lines(report.chain))
        lines.append("")
        lines.append(f"RESULT: {'PASS' if report.ok else 'FAIL'}")
        return "\n".join(lines)

    per_source = report.per_source()
    for sid in sorted(per_source):
        counts = per_source[sid]
        divergent = counts[STATUS_DIVERGENT]
        verdict = "FAIL" if divergent else "pass"
        lines.append(
            f"  [{verdict}] {sid:<40} "
            f"verified={counts[STATUS_VERIFIED]} "
            f"divergent={divergent} "
            f"unverifiable={counts[STATUS_UNVERIFIABLE]}"
        )

    # Detail every divergence — this is the actionable part.
    if report.divergent:
        lines.append("")
        lines.append("DIVERGENCES (stored hash does not match stored bytes):")
        for r in report.divergent:
            lines.append(f"  ✗ {r.source_id} / {r.run_id}: {r.reason}")
            for c in r.checks:
                if not c.matched:
                    lines.append(
                        f"      {c.kind}: stored={c.stored_hash[:16]}… "
                        f"recomputed={c.recomputed_hash[:16]}… "
                        f"({c.snapshot_path})"
                    )

    lines.append("")
    lines.extend(_chain_lines(report.chain))
    lines.append("")
    lines.append(
        f"Totals: {len(report.records)} records — "
        f"{len(report.verified)} verified, "
        f"{len(report.divergent)} divergent, "
        f"{len(report.unverifiable)} unverifiable"
    )
    lines.append(f"RESULT: {'PASS' if report.ok else 'FAIL'}")
    return "\n".join(lines)


def run_cli(argv: list[str] | None = None) -> int:
    """Parse args, verify the trail, print the report, return an exit code."""
    parser = argparse.ArgumentParser(
        prog="verify-trail",
        description="Read-only evidence-trail hash integrity verifier.",
    )
    parser.add_argument(
        "--source-id",
        default=None,
        help="Verify only records for this source_id.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full report as JSON instead of a text summary.",
    )
    parser.add_argument(
        "--chain",
        action="store_true",
        help=(
            "Verify only the tamper-evident hash chain (skip the per-record "
            "snapshot-hash checks). Exit 1 if the chain is broken."
        ),
    )
    args = parser.parse_args(argv)

    report = verify_trail(source_id=args.source_id)

    if args.chain:
        # Chain-only mode: the verdict is the chain's, not the per-record checks.
        if args.json:
            print(json.dumps(report.chain.as_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("StatuteProof — Evidence Trail Hash Chain")
            print("=" * 64)
            for line in _chain_lines(report.chain):
                print(line)
            print("")
            print(f"RESULT: {'PASS' if report.chain.ok else 'FAIL'}")
        return 0 if report.chain.ok else 1

    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_render_text(report))

    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(run_cli())
