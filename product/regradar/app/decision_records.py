"""Sealed individual-accountability decision log — Stage 1 (INERT, additive).

WHAT THIS IS: a per-org, append-only, hash-chained log of a reviewer's OWN
sign-off decisions. A user records, in THEIR OWN WORDS, what they reviewed and
what they decided; StatuteProof seals that statement — unchanged — with the SAME
``content-sha256-v1`` primitive the canonical evidence records use
(:func:`app.record_hashing.canonical_record_hash`), chains it to the org's
previous decision, and time-stamps it. A sealed decision record round-trips
through :func:`app.public_verify.verify_submission` with ZERO changes to the
verifier, because it IS the same ``{content, record_hash, record_hash_method}``
envelope shape.

WHAT THIS IS NOT (legal framing, load-bearing — see CLAUDE.md): StatuteProof
NEVER prescribes, suggests, scores, or assesses the decision. ``statement`` and
``amendment_reason`` are the user's words, stored verbatim — they are never
guarded, rewritten, or truncated (oversize input is REJECTED, not silently
trimmed, because these are the user's sealed words). The only StatuteProof-
authored copy in this feature is the ``FRAMING`` block below, which is held to
the product-wide forbidden-claims guard AT IMPORT.

CHAIN MODEL: one chain PER ORG (never global — a shared head would leak
activity across tenants; never per-user — the org is the accountability
boundary). ``chain_seq`` is computed as MAX+1 inside ``BEGIN IMMEDIATE`` and
``UNIQUE(org_id, chain_seq)`` turns a lost race into an ``IntegrityError`` that
is retried a bounded number of times, so two concurrent seals can never fork
the chain. The current head is mirrored best-effort to
``data/decision_chain/<org_id>/decision_chain_head.json`` (same semantics as
``app.source_runs._write_chain_head``; RFC 3161 anchoring of decision heads is
a Stage-3 concern and deliberately absent here).

IMMUTABILITY: the ``decision_records`` table carries ``BEFORE UPDATE`` /
``BEFORE DELETE`` triggers that ``RAISE(ABORT, …)`` (``app/db.py``), and this
module exposes ONLY insert + read functions — there is no update or delete
anywhere. Corrections are NEW sealed records carrying
``supersedes_decision_id`` + ``amendment_reason``; the original stays.

INERT IN STAGE 1: no endpoint calls this module yet (wiring, RBAC enforcement
via ``review.submit``, and live alert-proof binding are Stage 2). Every
function is fail-soft — bad input returns a benign value, and the access-log
append is best-effort and never blocks a seal.

NO AGGREGATE ROW CAP — DELIBERATE: unlike ``app.action_checklist`` (a workflow
aid with a per-user cap), an accountability log must never refuse to record a
legitimate decision because a quota was hit — a silently-dropped sign-off is a
worse failure than table growth. Every field is tightly bounded (a record is
≤ ~70KB worst case), and abuse control belongs to the Stage-2 API layer (RBAC
``review.submit`` gate + the product-wide rate limiter), not to this store.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.db import _connect, ensure_decision_table
from app.legal_safety import assert_no_forbidden_claims
from app.materiality import SHORT_DISCLAIMER
from app.record_hashing import RECORD_HASH_METHOD, canonical_record_hash

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0"

# ── bounds (REJECT oversize — never truncate the user's sealed words) ────────────
MAX_STATEMENT_LEN = 4000          # the user's decision, in their own words
MAX_AMENDMENT_REASON_LEN = 2000   # the user's correction reason, their words
MAX_DISPLAY_NAME_LEN = 120        # a person's name, bounded
MAX_LIST_LIMIT = 200              # list_decisions page bound
MAX_ID_LEN = 200                  # decision_id / alert_id / evidence_record_id

# ``reviewed`` is a verbatim copy of the alert's proof block ("what they saw").
# Stage 1 takes it as a caller-supplied dict; these bounds validate the SHAPE
# (flat, string keys, scalar values) without ever rewriting a value.
_MAX_REVIEWED_KEYS = 32
_MAX_REVIEWED_KEY_LEN = 64
_MAX_REVIEWED_STR_LEN = 2000
_MAX_CHECKLIST_ITEM_IDS = 100

# Bounded retry for the chain-seq race (BEGIN IMMEDIATE + UNIQUE(org_id, chain_seq)).
_SEAL_ATTEMPTS = 5

# ── kind: user-selected NEUTRAL log-type label ONLY (never app-assessed) ─────────
KIND_REVIEWED = "reviewed"
KIND_ACKNOWLEDGED = "acknowledged"
KIND_ESCALATED = "escalated"
KIND_NO_CHANGE_NEEDED = "no_change_needed"
KIND_ACTION_RECORDED = "action_recorded"
KINDS: tuple[str, ...] = (
    KIND_REVIEWED,
    KIND_ACKNOWLEDGED,
    KIND_ESCALATED,
    KIND_NO_CHANGE_NEEDED,
    KIND_ACTION_RECORDED,
)

# access-log action vocabulary (free-text ``action`` column; namespaced).
ACTION_SEAL = "decision.seal"

# Head-file location mirrors app.source_runs: derived from STATUTEPROOF_BASE_DIR
# so all stores relocate together (and tests can monkeypatch ``_BASE_DIR``).
_BASE_DIR = Path(
    os.environ.get("STATUTEPROOF_BASE_DIR") or Path(__file__).parent.parent
).resolve()

# ── app-authored framing — the ONLY StatuteProof words in this feature ───────────
# Guarded AT IMPORT (below) so a wording drift into a forbidden claim breaks the
# build, not a customer. The disclaimer reuses SHORT_DISCLAIMER verbatim — the
# vetted constant is never retyped.
FRAMING: dict[str, str] = {
    "title": "Your decision record",
    "subtitle": (
        "Seal your own review decision for this change into the evidence record. "
        "You author the wording; StatuteProof records and time-stamps it, unchanged."
    ),
    "empty": (
        "No sealed decisions yet. When you have reviewed this change, you can "
        "record your own decision and seal it into the evidence record."
    ),
    "statement_label": "Your decision, in your own words",
    "statement_placeholder": "Record what you reviewed and the decision you are making.",
    "kind_label": "How you want to log this",
    "seal_button": "Seal my decision",
    "confirm_title": "Seal this decision?",
    "confirm_body": (
        "Once sealed, this decision is time-stamped and cannot be edited. If you "
        "need to correct it later, you can add a new, linked entry — the original "
        "stays in the record."
    ),
    "amend_button": "Record a correction",
    "amend_note": (
        "This adds a new sealed entry that references the earlier one. The earlier "
        "decision remains unchanged in the record."
    ),
    "who_note": (
        "Your name and account are recorded with the decision so the record shows "
        "who reviewed it."
    ),
    "disclaimer": (
        "You author this decision; StatuteProof records your words without changing "
        "them and does not review, suggest, or assess the decision. "
        + SHORT_DISCLAIMER
    ),
}


def _guard_framing_at_import() -> None:
    """Fail the IMPORT if any app-authored string drifts into a forbidden claim.

    Import-time (not request-time) so a bad edit is caught by the first test or
    process start that touches this module — a banned phrase can never sit
    dormant until a customer sees it. Only StatuteProof-authored copy is
    guarded; the user's ``statement`` / ``amendment_reason`` are deliberately
    NEVER passed through any guard (their words, verbatim).
    """
    for key, value in FRAMING.items():
        assert_no_forbidden_claims(value, label=f"decision framing[{key}]")
    for kind_label in KINDS:
        assert_no_forbidden_claims(
            kind_label.replace("_", " "), label=f"decision kind[{kind_label}]"
        )


_guard_framing_at_import()


# ── small helpers ─────────────────────────────────────────────────────────────────

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decided_at_utc() -> str:
    """Authoritative decision time, inside the sealed content (Z-suffixed UTC)."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _decision_id(
    org_id: int,
    user_id: int,
    decided_at_utc: str,
    prev_decision_hash: str,
    alert_id: str,
    chain_seq: int,
) -> str:
    """``dec_<org>_<seq>_<sha256(f'{org}|{user}|{at}|{prev}|{alert}')[:20]>``."""
    seed = f"{org_id}|{user_id}|{decided_at_utc}|{prev_decision_hash}|{alert_id}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"dec_{org_id}_{chain_seq}_{digest}"


def _validated_reviewed_copy(reviewed: Any) -> dict[str, Any] | None:
    """Return a verbatim copy of the caller-supplied proof block, or ``None``.

    Shape-validates WITHOUT altering values: a non-empty flat dict with string
    keys and scalar values (str/int/float/bool/None), all bounded. Validation
    only REJECTS — it never rewrites — because ``reviewed`` is the record of
    what the reviewer actually saw (the alert's proof block, copied verbatim).
    """
    if not isinstance(reviewed, dict) or not reviewed:
        return None
    if len(reviewed) > _MAX_REVIEWED_KEYS:
        return None
    copy: dict[str, Any] = {}
    for key, value in reviewed.items():
        if not isinstance(key, str) or not key or len(key) > _MAX_REVIEWED_KEY_LEN:
            return None
        if isinstance(value, str):
            if len(value) > _MAX_REVIEWED_STR_LEN:
                return None
        elif not (value is None or isinstance(value, (bool, int, float))):
            return None
        copy[key] = value
    return copy


def _validated_checklist_ref(ref: Any) -> tuple[bool, dict[str, Any] | None]:
    """Validate the optional checklist reference: ``(ok, normalized_or_None)``.

    Shape: ``{"alert_id": str, "item_ids": [int, ...]}`` (both optional inside
    the dict), referencing the user's own ``app.action_checklist`` items.
    ``None`` is valid (no reference). Anything malformed rejects the seal.
    """
    if ref is None:
        return True, None
    if not isinstance(ref, dict) or not set(ref) <= {"alert_id", "item_ids"}:
        return False, None
    alert_id = ref.get("alert_id") or ""
    if not isinstance(alert_id, str) or len(alert_id) > MAX_ID_LEN:
        return False, None
    raw_ids = ref.get("item_ids")
    raw_ids = [] if raw_ids is None else raw_ids
    if not isinstance(raw_ids, list) or len(raw_ids) > _MAX_CHECKLIST_ITEM_IDS:
        return False, None
    item_ids: list[int] = []
    for value in raw_ids:
        if isinstance(value, bool) or not isinstance(value, int):
            return False, None
        item_ids.append(value)
    return True, {"alert_id": alert_id, "item_ids": item_ids}


def _parse_envelope(record_json: Any) -> dict[str, Any] | None:
    """Parse a stored ``record_json`` into the sealed envelope dict, or ``None``."""
    try:
        parsed = json.loads(record_json)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _record_access_log(user_id: int, decision_id: str, result: str = "allow") -> None:
    """Append one immutable access-log row for a seal. NEVER raises.

    Best-effort observation (exactly the ``app.action_checklist`` pattern):
    delegates to the shared ``rbac_runtime.log_sensitive_action`` so the org
    principal is resolved and the row lands the SAME way as every other
    sensitive action. A logging failure is swallowed here so it can never block
    or fail a seal that already committed.
    """
    try:
        from app import rbac_runtime

        rbac_runtime.log_sensitive_action(
            {"id": int(user_id)},
            ACTION_SEAL,
            result=result,
            resource_type="decision",
            resource_id=str(decision_id or ""),
        )
    except Exception:  # noqa: BLE001 — audit logging must NEVER break the action
        logger.warning("decision access-log write failed for %s (non-fatal)", ACTION_SEAL)


# ── head file (mirrors app.source_runs._write_chain_head semantics) ──────────────

def _head_file(org_id: int) -> Path:
    """``data/decision_chain/<org_id>/decision_chain_head.json`` (int → path-safe)."""
    return _BASE_DIR / "data" / "decision_chain" / str(int(org_id)) / "decision_chain_head.json"


def _write_decision_head(
    org_id: int, *, decision_id: str, chain_seq: int, decision_hash: str
) -> None:
    """Persist the org's current chain head to its anchor file. Best-effort.

    ADDITIVE signal, never a gate: a failed write is non-fatal — the seal has
    already committed to the append-only table, which remains the truth. No TSA
    call here; Stage 3 will anchor decision heads via
    ``rfc3161_anchor.maybe_anchor_head``.
    """
    try:
        path = _head_file(org_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "org_id": int(org_id),
            "decision_id": str(decision_id),
            "chain_seq": int(chain_seq),
            "head_decision_hash": str(decision_hash),
            "updated_at": _now_utc(),
            "last_update_kind": "append",
        }
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        tmp.replace(path)
    except Exception:  # noqa: BLE001 — the head mirror must never fail a seal
        logger.warning("decision chain head write failed for org=%s (non-fatal)", org_id)


def read_decision_head(org_id: int) -> dict[str, Any] | None:
    """Return the org's head-file payload dict, or ``None``. Never raises."""
    try:
        path = _head_file(int(org_id))
    except (TypeError, ValueError):
        return None
    try:
        if not path.exists():
            return None
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


# ── seal (the ONLY write; there is deliberately no update/delete anywhere) ───────

def _build_sealed_record(
    *,
    org_id: int,
    user_id: int,
    chain_seq: int,
    prev_hash: str,
    decided_at: str,
    display_name: str,
    reviewed: dict[str, Any],
    kind: str,
    statement: str,
    checklist_ref: dict[str, Any] | None,
    supersedes: str,
    amendment_reason: str,
    alert_id: str,
) -> tuple[dict[str, Any], str]:
    """Assemble the canonical sealed record: ``(envelope, record_json)``.

    Pure construction over ALREADY-VALIDATED inputs. Everything load-bearing
    lives INSIDE ``content`` (including ``prev_decision_hash`` and the
    authoritative ``decided_at_utc``), sealed with the SHARED
    ``canonical_record_hash`` — an auditor can recompute the digest with
    standard SHA-256 over the compact, sorted-key JSON of the content block.
    """
    decision_id = _decision_id(
        org_id, user_id, decided_at, prev_hash, alert_id, chain_seq
    )
    content: dict[str, Any] = {
        "decision_id": decision_id,
        "org_id": org_id,
        "chain_seq": chain_seq,
        "prev_decision_hash": prev_hash,
        "decided_by": {"user_id": user_id, "display_name": display_name},
        "decided_at_utc": decided_at,
        "reviewed": reviewed,
        "decision": {
            "kind": kind,
            "statement": statement,
            "checklist_ref": checklist_ref,
        },
        "supersedes_decision_id": supersedes or None,
        "amendment_reason": amendment_reason or None,
    }
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision_id": decision_id,
        "record_hash": "sha256:" + canonical_record_hash(content),
        "record_hash_method": RECORD_HASH_METHOD,
        "content": content,
    }
    return record, json.dumps(record, ensure_ascii=False, sort_keys=True)


def seal_decision(
    user_id: int,
    org_id: int,
    *,
    display_name: str,
    reviewed: dict[str, Any],
    kind: str,
    statement: str,
    checklist_ref: dict[str, Any] | None = None,
    supersedes_decision_id: str = "",
    amendment_reason: str = "",
) -> dict[str, Any] | None:
    """Seal one user-authored decision into the org's append-only chain.

    Returns the full sealed record (the ``{content, record_hash,
    record_hash_method}`` envelope) or ``None`` on invalid input / failure —
    fail-soft, never raises across the boundary.

    Validation REJECTS rather than rewrites: an oversize ``statement`` /
    ``amendment_reason`` / ``display_name`` returns ``None`` (these are the
    user's sealed words — silent truncation would seal something the user did
    not write). ``kind`` must be one of the five neutral labels.
    ``supersedes_decision_id`` must name an existing decision in the SAME org
    (checked inside the seal transaction; a foreign or unknown id gets the same
    ``None`` — no cross-org existence oracle) and travels with a non-empty
    ``amendment_reason`` (both or neither).

    Concurrency: chain_seq is computed as MAX+1 inside ``BEGIN IMMEDIATE``;
    losing the ``UNIQUE(org_id, chain_seq)`` race re-reads the head and retries
    (bounded), so concurrent seals serialize instead of forking. On success the
    head file is mirrored and a ``decision.seal`` access-log row is appended,
    both best-effort.
    """
    try:
        uid = int(user_id)
        oid = int(org_id)
    except (TypeError, ValueError):
        return None
    if uid <= 0 or oid < 0:
        return None

    name = str(display_name or "").strip()
    if len(name) > MAX_DISPLAY_NAME_LEN:
        return None

    kind_clean = str(kind or "").strip()
    if kind_clean not in KINDS:
        return None

    if not isinstance(statement, str) or not statement.strip():
        return None
    if len(statement) > MAX_STATEMENT_LEN:
        return None  # REJECT oversize — never truncate the user's sealed words

    reviewed_copy = _validated_reviewed_copy(reviewed)
    if reviewed_copy is None:
        return None
    alert_id = str(reviewed_copy.get("alert_id") or "")
    evidence_record_id = str(reviewed_copy.get("evidence_record_id") or "")
    if len(alert_id) > MAX_ID_LEN or len(evidence_record_id) > MAX_ID_LEN:
        return None

    ref_ok, ref_copy = _validated_checklist_ref(checklist_ref)
    if not ref_ok:
        return None

    supersedes = str(supersedes_decision_id or "").strip()
    if len(supersedes) > MAX_ID_LEN:
        return None
    amendment = "" if amendment_reason is None else amendment_reason
    if not isinstance(amendment, str):
        return None
    if len(amendment) > MAX_AMENDMENT_REASON_LEN:
        return None  # REJECT oversize — the correction reason is sealed verbatim
    # A correction carries its reason; a reason without a target is meaningless.
    if bool(supersedes) != bool(amendment.strip()):
        return None

    decided_at = _decided_at_utc()
    sealed_record: dict[str, Any] | None = None

    try:
        ensure_decision_table()
        conn = _connect()
        try:
            for _attempt in range(_SEAL_ATTEMPTS):
                try:
                    # BEGIN IMMEDIATE takes the write lock NOW, so the head read
                    # and the insert are atomic against other writers — the seq
                    # race is closed by construction; UNIQUE(org_id, chain_seq)
                    # is the belt-and-braces backstop that triggers the retry.
                    conn.execute("BEGIN IMMEDIATE")
                    if supersedes:
                        exists = conn.execute(
                            "SELECT 1 FROM decision_records"
                            " WHERE org_id = ? AND decision_id = ?",
                            (oid, supersedes),
                        ).fetchone()
                        if exists is None:
                            # Unknown OR another org's decision: identical None,
                            # no cross-org existence oracle.
                            conn.rollback()
                            return None
                    head = conn.execute(
                        "SELECT chain_seq, decision_hash FROM decision_records"
                        " WHERE org_id = ? ORDER BY chain_seq DESC LIMIT 1",
                        (oid,),
                    ).fetchone()
                    chain_seq = (int(head["chain_seq"]) + 1) if head is not None else 1
                    prev_hash = str(head["decision_hash"]) if head is not None else ""

                    record, record_json = _build_sealed_record(
                        org_id=oid,
                        user_id=uid,
                        chain_seq=chain_seq,
                        prev_hash=prev_hash,
                        decided_at=decided_at,
                        display_name=name,
                        reviewed=reviewed_copy,
                        kind=kind_clean,
                        statement=statement,
                        checklist_ref=ref_copy,
                        supersedes=supersedes,
                        amendment_reason=amendment,
                        alert_id=alert_id,
                    )
                    decision_id = record["decision_id"]
                    record_hash = record["record_hash"]

                    conn.execute(
                        """
                        INSERT INTO decision_records
                            (decision_id, org_id, chain_seq, decided_by_user_id,
                             alert_id, evidence_record_id, prev_decision_hash,
                             decision_hash, record_json, sealed_at, supersedes_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            decision_id, oid, chain_seq, uid,
                            alert_id, evidence_record_id, prev_hash,
                            record_hash, record_json, _now_utc(), supersedes,
                        ),
                    )
                    conn.commit()
                    sealed_record = record
                    break
                except sqlite3.IntegrityError:
                    # Lost the UNIQUE(org_id, chain_seq) race — re-read the head
                    # and retry with the new prev hash (bounded attempts).
                    conn.rollback()
                except sqlite3.OperationalError:
                    # Busy/locked beyond the timeout — retry within the bound.
                    conn.rollback()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 — write must never raise across the boundary
        logger.warning("seal_decision failed: %s", type(exc).__name__)
        return None

    if sealed_record is None:
        logger.warning("seal_decision exhausted %d attempts for org=%s", _SEAL_ATTEMPTS, oid)
        return None

    content = sealed_record["content"]
    _write_decision_head(
        oid,
        decision_id=sealed_record["decision_id"],
        chain_seq=content["chain_seq"],
        decision_hash=sealed_record["record_hash"],
    )
    _record_access_log(uid, sealed_record["decision_id"])
    return sealed_record


# ── reads (org-scoped; cross-org resolves to nothing — no oracle) ────────────────

def list_decisions(
    org_id: int, alert_id: str | None = None, limit: int = 200
) -> list[dict[str, Any]]:
    """Return the org's sealed decision records in chain order (bounded).

    Org-scoped by ``org_id = ?`` on every query; ``alert_id`` optionally narrows
    to one alert. Each element is the full sealed envelope (parsed from
    ``record_json``). Fail-soft: bad input or any error yields ``[]``.
    """
    try:
        oid = int(org_id)
    except (TypeError, ValueError):
        return []
    try:
        capped = max(1, min(int(limit), MAX_LIST_LIMIT))
    except (TypeError, ValueError):
        capped = MAX_LIST_LIMIT
    if alert_id is not None:
        if not isinstance(alert_id, str) or not alert_id or len(alert_id) > MAX_ID_LEN:
            return []
    try:
        ensure_decision_table()
        conn = _connect()
        try:
            if alert_id is not None:
                rows = conn.execute(
                    "SELECT record_json FROM decision_records"
                    " WHERE org_id = ? AND alert_id = ?"
                    " ORDER BY chain_seq ASC LIMIT ?",
                    (oid, alert_id, capped),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT record_json FROM decision_records"
                    " WHERE org_id = ?"
                    " ORDER BY chain_seq ASC LIMIT ?",
                    (oid, capped),
                ).fetchall()
        finally:
            conn.close()
        records = []
        for row in rows:
            parsed = _parse_envelope(row["record_json"])
            if parsed is not None:
                records.append(parsed)
        return records
    except Exception as exc:  # noqa: BLE001 — read must never raise across the boundary
        logger.warning("list_decisions failed: %s", type(exc).__name__)
        return []


def get_decision(org_id: int, decision_id: str) -> dict[str, Any] | None:
    """Return ONE sealed decision record, org-scoped, or ``None``.

    A cross-org (or unknown) ``decision_id`` matches zero rows and returns the
    SAME ``None`` — no existence oracle. Fail-soft, never raises.
    """
    try:
        oid = int(org_id)
    except (TypeError, ValueError):
        return None
    did = str(decision_id or "").strip()
    if not did or len(did) > MAX_ID_LEN:
        return None
    try:
        ensure_decision_table()
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT record_json FROM decision_records"
                " WHERE org_id = ? AND decision_id = ?",
                (oid, did),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return _parse_envelope(row["record_json"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_decision failed: %s", type(exc).__name__)
        return None


# ── chain verification (recompute every seal + prev linkage) ─────────────────────

def verify_decision_chain(org_id: int) -> dict[str, Any]:
    """Recompute every seal and the prev linkage for one org's chain.

    Returns ``{"ok": bool, "checked": int, "broken_at": chain_seq | None,
    "reason": str | None}``. Walks the chain in sequence order and stops at the
    FIRST broken record: an unparseable/tampered ``record_json`` (the seal no
    longer recomputes), a row/envelope mismatch, an org or sequence anomaly, or
    a ``prev_decision_hash`` that does not point at the previous record's seal.
    Fail-soft: storage errors report not-ok, never raise.
    """
    result: dict[str, Any] = {"ok": False, "checked": 0, "broken_at": None, "reason": None}
    try:
        oid = int(org_id)
    except (TypeError, ValueError):
        result["reason"] = "invalid_org_id"
        return result

    prev_hash = ""
    expected_seq = 1
    checked = 0
    try:
        ensure_decision_table()
        conn = _connect()
        try:
            # Stream the cursor (never fetchall): each record_json can be tens
            # of KB, and a long chain must not become a memory amplification
            # vector for a diagnostic that only needs one row at a time.
            cursor = conn.execute(
                "SELECT decision_id, chain_seq, decision_hash, record_json"
                " FROM decision_records WHERE org_id = ?"
                " ORDER BY chain_seq ASC",
                (oid,),
            )
            for row in cursor:
                seq = int(row["chain_seq"])
                reason, head_hash = _check_sealed_row(
                    row, prev_hash=prev_hash, expected_seq=expected_seq, org_id=oid
                )
                if reason is not None:
                    return {"ok": False, "checked": checked, "broken_at": seq, "reason": reason}
                prev_hash = head_hash
                expected_seq = seq + 1
                checked += 1
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 — verification is diagnostic, never raises
        logger.warning("verify_decision_chain failed: %s", type(exc).__name__)
        result["reason"] = "storage_error"
        result["checked"] = checked
        return result
    return {"ok": True, "checked": checked, "broken_at": None, "reason": None}


def _check_sealed_row(
    row: Any, *, prev_hash: str, expected_seq: int, org_id: int
) -> tuple[str | None, str]:
    """Check ONE stored row against its own seal and its chain position.

    Returns ``(None, record_hash)`` when intact, else ``(reason, "")``. The
    seal recompute goes through the SAME shared ``canonical_record_hash`` the
    writer used — writer and verifier can never drift.
    """
    envelope = _parse_envelope(row["record_json"])
    if envelope is None:
        return "record_json_unparseable", ""
    if envelope.get("record_hash_method") != RECORD_HASH_METHOD:
        return "record_hash_method_mismatch", ""
    content = envelope.get("content")
    if not isinstance(content, dict):
        return "content_missing", ""
    stored = str(envelope.get("record_hash") or "")
    bare = stored[len("sha256:"):] if stored.startswith("sha256:") else stored
    if canonical_record_hash(content) != bare:
        return "seal_mismatch", ""
    if str(row["decision_hash"]) != stored:
        return "row_hash_mismatch", ""
    if content.get("org_id") != org_id:
        return "org_mismatch", ""
    row_decision_id = str(row["decision_id"])
    if (
        content.get("decision_id") != row_decision_id
        or envelope.get("decision_id") != row_decision_id
    ):
        return "decision_id_mismatch", ""
    if content.get("chain_seq") != int(row["chain_seq"]):
        return "sequence_mismatch", ""
    if int(row["chain_seq"]) != expected_seq:
        return "sequence_gap", ""
    if content.get("prev_decision_hash") != prev_hash:
        return "prev_link_mismatch", ""
    return None, stored
