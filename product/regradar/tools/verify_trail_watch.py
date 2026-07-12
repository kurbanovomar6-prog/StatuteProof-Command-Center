"""
tools/verify_trail_watch.py — continuous self-check for the "evidence-backed" claim.

StatuteProof tells customers that hashes prove content. Nothing enforces that
promise unless something *re-checks* it on a schedule. This thin wrapper runs
the read-only evidence-trail verifier (``tools/verify_evidence_trail.py``) and,
on ANY divergence — a stored snapshot hash that no longer matches its bytes, OR
a broken tamper-evident chain link — pages the founder via
``app.ops_alert.notify_founder``. On an all-clear trail it exits 0 quietly.

Runs unattended on a systemd timer
(``deploy/systemd/statuteproof-verify.{service,timer}``), so two properties are
non-negotiable:

  * READ-ONLY over the evidence trail. It only calls
    ``verify_evidence_trail.verify_trail`` (read-only) and posts a Telegram
    message. It never mutates the trail, a record, or a head file. One
    ADDITIVE exception rides on this timer: the dormant-by-default RFC 3161
    decision-head anchor sweep (``app.decision_anchor``). With
    ``RFC3161_TSA_URL`` unset (the default) it is a complete no-op; when an
    operator opts in, it writes ONLY additive timestamp sidecars next to each
    org's decision-chain head file — the same cadence role the capture trail's
    ``rfc3161_anchor.anchor_head_now`` is documented for, reusing this existing
    daily timer instead of inventing a new one.
  * The founder alert is strictly BEST-EFFORT. ``notify_founder`` already never
    raises; this wrapper additionally guards the call so a Telegram/network
    failure can never turn a watchdog run into a crash.

Exit codes (mirror ``verify-trail`` / ``heartbeat-check``):
  0  trail is clean (verified and/or unverifiable records only).
  1  at least one divergence (hash mismatch or broken chain) — founder alerted.
  2  bad CLI arguments (argparse).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path bootstrap — make app/ and the sibling tool importable when run
# directly (python tools/verify_trail_watch.py) as well as via run.py.
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).resolve().parent
_PRODUCT_DIR = _TOOLS_DIR.parent  # .../product/regradar
if str(_PRODUCT_DIR) not in sys.path:
    sys.path.insert(0, str(_PRODUCT_DIR))

from app import ops_alert  # noqa: E402  (module import so notify_founder is patchable)
from tools import verify_evidence_trail as vt  # noqa: E402

logger = logging.getLogger(__name__)

# How many diverging records to name in the alert body before summarising the
# rest as a count — keeps the Telegram message concise and legible.
_MAX_DETAIL_LINES = 8


def build_divergence_summary(report: "vt.TrailReport") -> str:
    """Build a concise, plain-text founder alert describing what diverged.

    Sent through ``notify_founder`` with no parse mode, so no escaping is needed
    and a stray character in a source id or reason can never break delivery.
    """
    lines = ["\U0001F6A8 StatuteProof evidence trail INTEGRITY FAILURE"]

    if report.divergent:
        lines.append(
            f"{len(report.divergent)} record(s) diverged "
            "(stored hash no longer matches stored bytes):"
        )
        for r in report.divergent[:_MAX_DETAIL_LINES]:
            lines.append(f"  • {r.source_id} / {r.run_id}: {r.reason}")
        extra = len(report.divergent) - _MAX_DETAIL_LINES
        if extra > 0:
            lines.append(f"  … and {extra} more")

    if not report.chain.ok:
        c = report.chain
        lines.append(
            f"Hash chain BROKEN at chained index {c.break_index} "
            f"({c.break_source_id} / {c.break_run_id}): {c.reason}"
        )

    lines.append(
        "The evidence trail can no longer be trusted. Run `run.py verify-trail` "
        "and investigate before delivering any brief."
    )
    return "\n".join(lines)


def _anchor_decision_heads_best_effort() -> dict | None:
    """Run the dormant-by-default decision-head anchor sweep. NEVER raises.

    ``app.decision_anchor.anchor_decision_heads_now`` is itself fail-soft and
    dormant unless ``RFC3161_TSA_URL`` is set; the guard here is
    defence-in-depth so even an import failure can never crash the watchdog or
    change its exit code. Returns the sweep summary, or ``None`` on failure.
    """
    try:
        from app import decision_anchor

        summary = decision_anchor.anchor_decision_heads_now()
        if not summary.get("skipped_dormant"):
            logger.info("decision-head anchor sweep: %s", summary)
        return summary
    except Exception:  # noqa: BLE001 — an add-on pass must never break the watchdog
        logger.warning(
            "verify-trail-watch: decision-head anchor sweep failed — swallowed"
        )
        return None


def _alert_best_effort(summary: str) -> bool:
    """Page the founder without ever letting a failure propagate.

    ``ops_alert.notify_founder`` is already best-effort (returns False, never
    raises). The extra guard is defence-in-depth so this watchdog cannot crash
    even if the alert implementation is swapped for one that misbehaves.
    """
    try:
        return bool(ops_alert.notify_founder(summary))
    except Exception:  # noqa: BLE001 — a watchdog must never crash on its own alert
        logger.warning(
            "verify-trail-watch: founder alert raised unexpectedly — swallowed"
        )
        return False


def run_watch(argv: list[str] | None = None) -> int:
    """Verify the trail; page the founder on ANY divergence; return an exit code.

    ``--source-id`` scopes the per-record snapshot-hash checks to one source;
    the tamper-evident chain is always verified over the full trail (it is
    global), so a broken chain is caught regardless of the filter.
    """
    parser = argparse.ArgumentParser(
        prog="verify-trail-watch",
        description=(
            "Continuously self-check the evidence trail; page the founder "
            "(best-effort) on any hash mismatch or broken chain link."
        ),
    )
    parser.add_argument(
        "--source-id",
        default=None,
        help="Restrict per-record hash checks to one source (chain stays global).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also emit the full integrity report as JSON.",
    )
    args = parser.parse_args(argv)

    report = vt.verify_trail(source_id=args.source_id)

    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2, sort_keys=True))

    if report.ok:
        if not args.json:
            print("verify-trail-watch: evidence trail intact — no divergence.")
        exit_code = 0
    else:
        summary = build_divergence_summary(report)
        if not args.json:
            print(summary, file=sys.stderr)
        _alert_best_effort(summary)
        exit_code = 1

    # Dormant-by-default RFC 3161 decision-head anchor sweep (additive sidecars
    # only; complete no-op unless RFC3161_TSA_URL is set). Runs on BOTH the
    # clean and the divergent path, deliberately AFTER the verdict and the
    # founder alert so a slow TSA can never delay an integrity page, and it
    # never affects the verdict or exit code.
    _anchor_decision_heads_best_effort()

    return exit_code


if __name__ == "__main__":
    sys.exit(run_watch())
