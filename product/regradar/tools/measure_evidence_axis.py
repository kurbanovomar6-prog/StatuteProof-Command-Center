"""Reproducible measurement for the EVIDENCE axis.

Run the SAME command before and after a change; the numbers are comparable only
because the sample is deterministic (sorted paths, fixed cap) rather than
whatever happened to be on disk in what order.

    python3 tools/measure_evidence_axis.py            # human summary
    python3 tools/measure_evidence_axis.py --json     # machine-readable

Two independent instruments, on purpose:
  * ``run.py verify-trail`` — the founder-facing integrity sweep.
  * ``app.public_verify.verify_submission`` — the exact code path behind the
    public, no-login /verify endpoint, i.e. what a customer's auditor runs.
They answer different questions and can disagree; when they do, that disagreement
is itself the finding.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SNAPSHOT_GLOB = "data/source_snapshots/*/*/*/*/"
RECORD_NAMES = ("record.json", "proof.json", "evidence.json")
SAMPLE_CAP = 200  # deterministic sample; the axis DoD asks for >=100


def _trail_totals() -> dict:
    """Read verify-trail's MACHINE-READABLE output.

    This used to regex prose: a "Totals: N records — ..." line, plus a substring
    match for "intact" and a "(\\d+) chained" capture. Every one of those drifts
    the moment the wording changes, and the scorer downstream had no way to tell
    a reworded sentence from a broken chain. verify-trail emits the same facts as
    JSON, so the wording is free to change without moving the number.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "tools/verify_evidence_trail.py", "--json"],
            cwd=ROOT, capture_output=True, text=True, timeout=900,
        )
    except subprocess.TimeoutExpired:
        return {"error": "verify-trail timed out after 900s"}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": "verify-trail did not emit JSON",
                "tail": (proc.stdout or proc.stderr or "")[-400:]}

    totals = data.get("totals") or {}
    chain = data.get("chain") or {}
    coverage = data.get("coverage") or {}
    legacy = data.get("legacy_block") or {}
    records = int(totals.get("records") or 0)
    verified = int(totals.get("verified") or 0)
    return {
        "records": records,
        "verified": verified,
        "divergent": int(totals.get("divergent") or 0),
        "unverifiable": int(totals.get("unverifiable") or 0),
        "verified_pct": round(100.0 * verified / records, 1) if records else 0.0,
        "chain_status": chain.get("status"),
        # Unscored until now, which is precisely what made relink-gaming
        # invisible: rewriting the chain over a pruned trail keeps every in-file
        # invariant and only the head anchor notices.
        "anchor_status": chain.get("anchor_status"),
        "legacy_status": legacy.get("status"),
        "coverage": coverage,
    }


def _read_untranslated(path: Path) -> str:
    """Read text exactly as stored — no universal-newline translation."""
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return handle.read()


def _sample_dirs() -> list[Path]:
    """A deterministic sample spread ACROSS the store, not its first N entries.

    Snapshot paths sort by date, so taking a prefix samples one vintage and
    reports it as the whole. That is not a rounding error: 557 of 1317 stored
    artifacts carry no hashes at all and 532 of those were written on
    2026-07-03..05, so a prefix sample under-reports them badly. Striding keeps
    the sample reproducible (same input, same sample) while covering the range.
    """
    dirs = [d for d in sorted(ROOT.glob(SNAPSHOT_GLOB)) if (d / "normalized.txt").exists()]
    if len(dirs) <= SAMPLE_CAP:
        return dirs
    stride = len(dirs) / SAMPLE_CAP
    return [dirs[int(i * stride)] for i in range(SAMPLE_CAP)]


def _public_verify_sample() -> dict:
    """Run the customer-facing verifier over a deterministic sample."""
    from app.public_verify import verify_submission

    verified = 0
    failed = 0
    unreadable = 0
    fail_reasons: Counter = Counter()

    for d in _sample_dirs():
        record_path = next((d / n for n in RECORD_NAMES if (d / n).exists()), None)
        if record_path is None:
            continue
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
            # newline="" is load-bearing: Path.read_text() applies universal-newline
            # translation, turning a stored CRLF into LF and therefore changing the
            # bytes we hash. A customer uploads the file untranslated, so translating
            # here would fabricate raw_bytes_match failures that the real /verify
            # endpoint never sees (observed on 10 records whose raw.txt starts "\r\n").
            normalized = _read_untranslated(d / "normalized.txt")
            raw_path = d / "raw.txt"
            raw = _read_untranslated(raw_path) if raw_path.exists() else None
        except Exception as exc:
            unreadable += 1
            fail_reasons[f"unreadable:{type(exc).__name__}"] += 1
            continue

        result = verify_submission(record, raw=raw, normalized=normalized)
        if result.get("verified"):
            verified += 1
            continue
        failed += 1
        for check in result.get("checks") or []:
            if str(check.get("status", "")).lower() not in ("pass", "skipped"):
                # "name" is the stable key (app/public_verify.py emits name/status/detail);
                # "detail" is prose that moves, so never key the tally on it.
                fail_reasons[str(check.get("name") or "unnamed")] += 1

    checked = verified + failed
    # An artifact whose record_is_object check fails carries no hashes at all —
    # it is not an evidence record, and the verifier is right to reject it. Those
    # belong in their own bucket, not in the denominator of "does our evidence
    # verify", but they must stay VISIBLE: silently dropping them is how a
    # coverage number gets flattered.
    not_records = fail_reasons.get("record_is_object", 0)
    real = checked - not_records
    return {
        "sampled": checked,
        "verified": verified,
        "failed": failed,
        "unreadable": unreadable,
        "verified_pct": round(100.0 * verified / checked, 1) if checked else 0.0,
        "not_evidence_records": not_records,
        "real_evidence_records": real,
        "verified_pct_of_real": round(100.0 * verified / real, 1) if real else 0.0,
        "top_failing_checks": fail_reasons.most_common(8),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument("--skip-trail", action="store_true", help="skip the slow verify-trail sweep")
    args = parser.parse_args()

    report = {"public_verify": _public_verify_sample()}
    report["verify_trail"] = {"skipped": True} if args.skip_trail else _trail_totals()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    pv = report["public_verify"]
    print("public /verify on real stored records (the customer's auditor path)")
    print(f"  sampled     {pv['sampled']}")
    print(f"  verified    {pv['verified']}  ({pv['verified_pct']}% of all sampled)")
    print(f"  failed      {pv['failed']}")
    print(f"  of which not evidence records at all (no hashes): {pv['not_evidence_records']}")
    print(f"  => {pv['verified']}/{pv['real_evidence_records']} real evidence records "
          f"({pv['verified_pct_of_real']}%)")
    if pv["unreadable"]:
        print(f"  unreadable  {pv['unreadable']}")
    for name, count in pv["top_failing_checks"]:
        print(f"      {count:5}  {name}")

    trail = report["verify_trail"]
    print("\nrun.py verify-trail (founder-facing sweep)")
    if trail.get("skipped"):
        print("  skipped")
    elif "error" in trail:
        print(f"  ERROR: {trail['error']}")
    else:
        print(f"  {trail['records']} records — {trail['verified']} verified "
              f"({trail['verified_pct']}%), {trail['divergent']} divergent, "
              f"{trail['unverifiable']} unverifiable")
        print(f"  chain: {trail['chain']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
