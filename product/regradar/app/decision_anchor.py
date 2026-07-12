"""RFC 3161 external-anchor cadence for per-org DECISION chain heads (Stage 3).

WHAT THIS IS: the decision-log twin of :func:`app.rfc3161_anchor.anchor_head_now`.
The capture trail anchors its single global head; the sealed decision log
(``app.decision_records``) keeps ONE chain PER ORG, each with its own head file at
``data/decision_chain/<org_id>/decision_chain_head.json``. This module sweeps
those per-org heads on a cadence and hands each one to the EXISTING, unmodified
TSA machinery — :func:`app.rfc3161_anchor.maybe_anchor_head` — closing the same
relink gap for decision chains that the capture-trail anchor closes for evidence
(see the honest-scope discussion in ``app/rfc3161_anchor.py`` and
``verify_decision_head`` in ``app/decision_records.py``: an in-table chain cannot
witness its own history being rewritten; only a token StatuteProof cannot forge
can).

SAFETY POSTURE (inherited verbatim from the TSA module — nothing is re-decided
here):

* **DORMANT BY DEFAULT.** Gated on :func:`app.rfc3161_anchor.anchor_enabled`
  (the ``RFC3161_TSA_URL`` environment variable). When unset, the sweep returns
  immediately — no directory listing, no network, no thread, no file I/O — and
  reports ``skipped_dormant: True``.
* **ADDITIVE ONLY.** The only writes are the TSA machinery's own sidecars,
  placed next to each org's head file. No decision record, head file, or trail
  line is ever mutated. NOTE (verbatim-reuse consequence): the sidecar
  filenames are the machinery's fixed constants
  (``evidence_chain_head.tsr.json`` / ``evidence_chain_head.tsr``) even inside a
  ``decision_chain/<org_id>/`` directory — the per-org directory, not the
  filename, is what scopes the token. Renaming would require touching
  ``rfc3161_anchor.py`` (read-only by policy), so the name is accepted and
  documented.
* **FAIL-SOFT PER ORG.** One unreadable/corrupt head file (or one TSA failure)
  never stops the sweep — the org is skipped and the walk continues. The
  function NEVER raises; it always returns an honest summary dict.
* **BOUNDED.** At most :data:`MAX_ORGS_PER_SWEEP` directory entries are
  examined per sweep (a hostile or runaway ``decision_chain/`` directory cannot
  wedge the caller), and each TSA call is already transport-bounded inside the
  machinery (clamped timeout, 1 MB response cap, redirects refused).
* **IDEMPOTENT / TSA-FRIENDLY.** ``maybe_anchor_head`` skips the network when
  the sidecar already anchors the org's current head, so a sweep over N orgs
  whose chains have not moved makes ZERO network calls. Only orgs whose head
  advanced since the last sweep are (re-)anchored.

SCHEDULING: this is a cadence ENTRY POINT, exactly like ``anchor_head_now`` —
it is invoked from the existing daily maintenance run
(``run.py verify-trail-watch`` on ``deploy/systemd/statuteproof-verify.timer``,
see ``tools/verify_trail_watch.py``). No new timer, no scheduler thread.
"""

from __future__ import annotations

import logging
from itertools import islice
from pathlib import Path
from typing import Any

from app import decision_records, rfc3161_anchor

logger = logging.getLogger(__name__)

# Upper bound on decision_chain/ directory entries examined per sweep. Real
# deployments have a handful of orgs; the cap exists so a runaway/hostile
# directory can never turn a best-effort maintenance pass into unbounded work.
MAX_ORGS_PER_SWEEP = 10_000

# Org directory names are written by decision_records._head_file as str(int(org_id)).
# Anything longer than this is not a plausible org id (and bounds int() parsing).
_MAX_ORG_DIRNAME_LEN = 18

# Decision heads store "sha256:<64 hex>" (app.record_hashing convention); the TSA
# imprint machinery takes the BARE 64-hex digest (same value, no prefix).
_SHA256_PREFIX = "sha256:"

HEAD_FILE_NAME = "decision_chain_head.json"


def _chain_root() -> Path:
    """``<base>/data/decision_chain`` — resolved at CALL time via the owning module.

    Reading ``decision_records._BASE_DIR`` through the module attribute (never a
    from-import copy) keeps this sweep pointed at exactly the directory the
    writer uses, including when tests monkeypatch ``_BASE_DIR`` — the same
    discipline ``anchor_head_now`` applies by calling
    ``source_runs._chain_head_file()`` at call time.
    """
    return Path(decision_records._BASE_DIR) / "data" / "decision_chain"


def _org_id_from_dirname(name: str) -> int | None:
    """Parse a canonical org directory name to an int org id, or ``None``.

    The writer creates directories as ``str(int(org_id))``, so only canonical
    ASCII-decimal names are accepted: ``"42"`` yes; ``"007"``, ``"-1"``,
    ``"1.5"``, ``"abc"``, unicode digits — no (they were not written by the
    app, and a non-canonical name would resolve to a DIFFERENT path than
    ``decision_records._head_file`` uses).
    """
    if not name or len(name) > _MAX_ORG_DIRNAME_LEN or not name.isascii():
        return None
    if not name.isdigit():
        return None
    org_id = int(name)
    if str(org_id) != name:
        return None
    return org_id


def _anchor_one_org_head(org_id: int) -> bool:
    """Read one org's head file and hand its head hash to the TSA machinery.

    Returns True when a head hash was actually handed to
    :func:`rfc3161_anchor.maybe_anchor_head` (an "attempt" — the machinery
    itself is best-effort and may still decline/fail without raising), False
    when the org had nothing anchorable (missing/corrupt head file, empty
    hash). May raise only if the underlying machinery misbehaves; the caller's
    per-org guard catches that and continues the sweep.
    """
    payload = decision_records.read_decision_head(org_id)
    if not isinstance(payload, dict):
        return False

    head = str(payload.get("head_decision_hash") or "").strip().lower()
    if head.startswith(_SHA256_PREFIX):
        head = head[len(_SHA256_PREFIX):]
    if not head:
        return False

    head_path = decision_records._head_file(org_id)
    # Best-effort by contract: returns the anchor dict, a cached sidecar, or
    # None — never raises, never blocks beyond the bounded TSA timeout.
    rfc3161_anchor.maybe_anchor_head(head, head_path)
    return True


def anchor_decision_heads_now() -> dict[str, Any]:
    """Sweep every org's decision-chain head and anchor each to the TSA.

    The periodic-cadence entry point, mirroring
    :func:`app.rfc3161_anchor.anchor_head_now` for the capture trail. Intended
    production usage: called from the existing daily maintenance run
    (``run.py verify-trail-watch``); safe to call more often — unchanged heads
    are sidecar-cached and make no network calls.

    Returns an honest summary (ALWAYS — this function never raises)::

        {
          "orgs_seen": <int>,         # canonical org dirs encountered (bounded)
          "anchor_attempted": <int>,  # orgs whose head hash reached the TSA machinery
          "skipped_dormant": <bool>,  # True => RFC3161_TSA_URL unset; nothing was done
        }

    DORMANT CONTRACT: when :func:`rfc3161_anchor.anchor_enabled` is False this
    returns immediately with ``skipped_dormant: True`` — no directory listing,
    no network, no thread, no sidecar, byte-for-byte nothing on disk.
    """
    summary: dict[str, Any] = {
        "orgs_seen": 0,
        "anchor_attempted": 0,
        "skipped_dormant": False,
    }
    try:
        if not rfc3161_anchor.anchor_enabled():
            summary["skipped_dormant"] = True
            return summary

        root = _chain_root()
        if not root.is_dir():
            return summary

        # islice bounds RAW entries examined (valid or not) so even a directory
        # stuffed with junk names is bounded work. Iteration order is the OS's;
        # order is irrelevant because anchoring is idempotent per org.
        for entry in islice(root.iterdir(), int(MAX_ORGS_PER_SWEEP)):
            try:
                org_id = _org_id_from_dirname(entry.name)
                if org_id is None or not entry.is_dir():
                    continue
                summary["orgs_seen"] += 1
                if _anchor_one_org_head(org_id):
                    summary["anchor_attempted"] += 1
            except Exception:  # noqa: BLE001 — one bad org must never stop the sweep
                logger.warning(
                    "decision anchor sweep: entry %r failed (non-fatal); continuing.",
                    entry.name,
                )
                continue
    except Exception as exc:  # noqa: BLE001 — cadence entry point; never propagate
        logger.warning(
            "anchor_decision_heads_now failed: %s (partial summary returned).",
            type(exc).__name__,
        )
    return summary
