"""Auditor Evidence Room — scoped, time-boxed, READ-ONLY external evidence shares.

WHAT THIS IS: an MLRO/compliance owner creates a share for their examiner or
auditor; the recipient opens one link (no account, no login) and sees ONLY the
frozen scope the owner chose — the sealed evidence records for a set of sources
over a date range, each record's seal hash and capture timestamp, a coverage
summary, and "verify independently" pointers to the public verifier. Nothing
else: no other sources, no other tenants, no account identity beyond an optional
display name the owner typed.

THIS IS A NEW EXTERNAL AUTHORIZATION SURFACE, so every default is fail-closed:

* **Token = credential, stored like a password.** The URL token is
  ``secrets.token_urlsafe(32)`` (256 bits). ONLY its SHA-256 hex is stored
  (``evidence_shares.token_hash``); the raw token is returned exactly once at
  creation and never persisted, so a database read can never yield a usable
  link. Lookup recomputes the hash and re-checks it with
  ``hmac.compare_digest`` (constant-time).
* **Scope frozen at creation.** The source_ids are entitlement-clipped at
  CREATION time (tenancy fail-closed via ``app.tenancy`` + plan source limit —
  the same two restrictions as ``app.api._Handler._entitle_source_ids``) and
  stored as a JSON array. The public endpoint reads ONLY that stored scope, so
  a share can never widen after it is sealed, and another tenant's custom
  source can never enter it — not at creation (clipped) and not later (frozen).
* **Expiry is mandatory** (default 30 days, max 90) and shares are revocable.
  Expired, revoked, and unknown tokens are all indistinguishable to the caller
  (the API returns the same 404 shape) — no existence oracle.
* **Bounded.** Creation rejects an oversized scope (mirrors
  ``regulator_binder.MAX_BINDER_RECORDS`` / ``MAX_EVIDENCE_PACK_RECORDS``); the
  room view collects metadata only (never snapshot bytes) with an early-stop
  limit, so the public endpoint can never materialize an unbounded payload.
* **Never raises across the boundary.** Every public function returns an
  ``{"ok": ...}`` envelope or ``None``; internal errors are logged server-side
  and surface as a generic failure, never a stacktrace.

Every successful or denied room view is appended to the immutable
``access_log`` (actor_user_id=None — the viewer is external) as action
``room.view`` — the audit trail of the audit. Logging is best-effort and never
changes the outcome (mirrors ``app.rbac_runtime.log_sensitive_action``).

Legal safety: the room faces an EXAMINER. Authored prose is negative-assurance
monitoring language guarded by the shared forbidden-claims check
(``app.evidence_pack.assert_no_forbidden_claims``), and the view carries BOTH
the short and the full standard disclaimers.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.access_log import RESULT_ALLOW, RESULT_DENY, append_access_log
from app.audit_export import validate_date_range, validate_source_ids
from app.db import _connect, ensure_evidence_shares_table
from app.evidence_assessment import LEGAL_DISCLAIMER
from app.evidence_pack import (
    FULL_LEGAL_DISCLAIMER,
    EvidencePackError,
    _naive_ts,
    _safe_under_root,
    assert_no_forbidden_claims,
)
from app.text_quality import is_mostly_unreadable

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent

# ── bounds ────────────────────────────────────────────────────────────────────────

# Expiry policy: mandatory, defaulted, hard-capped. There is no "forever" share —
# an examiner engagement is time-boxed, and a forgotten link must die on its own.
DEFAULT_EXPIRY_DAYS = 30
MAX_EXPIRY_DAYS = 90
MIN_EXPIRY_DAYS = 1

# Hard cap on records a single room may expose. The room is a bounded summary
# (a source or a few sources over an engagement period), not a bulk-export
# channel — the Evidence Pack / Regulator Binder exist for full-bytes handover.
# An oversized scope is rejected at CREATION (never silently truncated into a
# misleading "complete-looking" room); if the frozen scope grows past the cap
# later (more records captured in-range), the view marks itself truncated
# honestly. Mirrors regulator_binder.MAX_BINDER_RECORDS discipline.
MAX_ROOM_RECORDS = 500

# Per-record diff excerpt: bounded read (never an unbounded file into memory),
# bounded display length. The excerpt is quoted monitoring content, shown only
# when it decodes as readable text (the undecodable-content guard fails it
# closed to an empty excerpt — the VARA mojibake lesson: never ship garbled
# bytes to an external reader).
_DIFF_READ_CAP_BYTES = 8192
_DIFF_EXCERPT_MAX_CHARS = 320
_SUMMARY_MAX_CHARS = 200
_ORG_NAME_MAX_CHARS = 120

# The immutable-audit action recorded for every public room access.
ROOM_VIEW_ACTION = "room.view"

# URL tokens are token_urlsafe output — base64url alphabet only. Anything else
# (path tricks, absurd lengths) is rejected before touching the database.
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{20,200}$")

# A source_id is a single path segment interpolated into the evidence glob. It
# must be a plain directory name — no separators, traversal, or glob metachars —
# so a frozen scope id can never broaden the walk beyond its own source subtree.
# The negative lookahead rejects all-dot segments (".."/".") so a traversal id
# can't collapse the per-source glob back to a whole-tree walk (verify-swarm).
_SAFE_SOURCE_SEGMENT_RE = re.compile(r"^(?!\.+$)[A-Za-z0-9._-]+$")

# Authored, examiner-facing prose. Negative-assurance tone only: what was
# captured, how to check it — never certification, guarantees, or advice.
VERIFICATION_NOTE = (
    "Each record below carries the SHA-256 seal StatuteProof recorded at "
    "capture time. You do not have to take these values on trust: request the "
    "evidence pack for any record from the account holder and re-hash the "
    "bytes yourself with the public verifier or any standard SHA-256 tool. "
    "The open verification specification describes the exact method."
)

ROOM_HEADER_NOTE = (
    "This is a read-only view of monitoring evidence that the account holder "
    "chose to share for regulatory review. It shows what was captured from the "
    "monitored official sources in the period, with the hashes recorded at "
    "capture time. It is monitoring evidence, not a legal opinion, and it does "
    "not certify completeness of coverage."
)


# ── token handling ────────────────────────────────────────────────────────────────

def _hash_token(token: str) -> str:
    """SHA-256 hex of the URL token — the ONLY form ever stored."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _safe_user_id(user: Any) -> int | None:
    if not isinstance(user, dict):
        return None
    try:
        return int(user["id"])
    except (KeyError, TypeError, ValueError):
        return None


# ── entitlement (mirrors app.api._Handler._entitle_source_ids) ───────────────────

def _entitled_source_ids(user_id: int, requested: list) -> list[str]:
    """Clip caller-supplied source_ids to what the user is entitled to.

    Same two fail-closed restrictions as the export handlers' entitlement:

    1. Tenancy — a *custom* source may only be shared by the user who owns it;
       custom sources owned by someone else (and legacy/unowned custom sources)
       are dropped via the single tenancy primitive
       (``app.tenancy.denied_custom_source_ids``). Official/shared sources pass.
    2. Plan limit — the surviving list is truncated to the plan's
       ``source_limit`` so a share never exposes more sources than the plan sells.

    Never raises — any lookup failure yields the tenancy-safe subset it could
    compute (falling back to an empty list), never the raw input.
    """
    clean_ids = [str(s).strip() for s in (requested or []) if str(s).strip()]
    if not clean_ids:
        return []
    # De-duplicate while preserving the caller's order (a duplicated id must not
    # consume two slots of the plan limit or double-count in the frozen scope).
    seen: set[str] = set()
    unique_ids = [sid for sid in clean_ids if not (sid in seen or seen.add(sid))]

    try:
        from app.tenancy import denied_custom_source_ids

        denied = denied_custom_source_ids(user_id)
    except Exception:  # noqa: BLE001 — unreadable tenancy must not widen scope
        logger.warning("evidence_room: tenancy lookup failed; denying custom sources")
        denied = {sid for sid in unique_ids if str(sid).startswith("custom-")}
    entitled = [sid for sid in unique_ids if sid not in denied]

    try:
        from app.plan import source_limit_for

        limit = source_limit_for(user_id)
    except Exception:  # noqa: BLE001 — a broken plan lookup must not widen scope
        limit = 0
    if limit >= 0:
        entitled = entitled[:limit]
    return entitled


# ── share creation ────────────────────────────────────────────────────────────────

def create_share(
    user: Any,
    source_ids: list,
    date_from: str,
    date_to: str,
    *,
    expires_days: Any = None,
    org_display_name: str = "",
    base_dir: Path | None = None,
    max_records: int = MAX_ROOM_RECORDS,
) -> dict[str, Any]:
    """Create a sealed, time-boxed external share. Never raises.

    Returns ``{"ok": True, "share_id", "token", "expires_at", ...}`` on success —
    ``token`` is the ONE AND ONLY time the raw token exists outside the caller's
    hands; only its SHA-256 is stored. On failure returns ``{"ok": False,
    "error": <code>, "message": <safe text>}``.

    The scope (source_ids + date range) is validated, entitlement-clipped
    (tenancy + plan — see :func:`_entitled_source_ids`), bounded (an oversized
    scope is rejected, mirroring the export builders) and then FROZEN into the
    row. The public room endpoint only ever reads the frozen scope.
    """
    try:
        user_id = _safe_user_id(user)
        if user_id is None:
            return {"ok": False, "error": "forbidden", "message": "Not permitted."}

        ids_ok, ids_err = validate_source_ids(source_ids)
        if not ids_ok:
            return {"ok": False, "error": "invalid", "message": ids_err}
        valid, err = validate_date_range(str(date_from or ""), str(date_to or ""))
        if not valid:
            return {"ok": False, "error": "invalid", "message": err}

        # Expiry is mandatory policy: default when omitted, reject out-of-range
        # or non-integral values explicitly (silently clamping/coercing would
        # hide a caller bug — a "10.5-day" share is a bug, not a wish).
        if expires_days is None or (isinstance(expires_days, str) and not expires_days.strip()):
            days = DEFAULT_EXPIRY_DAYS
        elif isinstance(expires_days, bool) or not isinstance(expires_days, (int, str)):
            return {
                "ok": False,
                "error": "invalid_expiry",
                "message": f"expires_days must be a whole number of days ({MIN_EXPIRY_DAYS}-{MAX_EXPIRY_DAYS}).",
            }
        else:
            try:
                days = int(str(expires_days).strip())
            except (TypeError, ValueError):
                return {
                    "ok": False,
                    "error": "invalid_expiry",
                    "message": f"expires_days must be a whole number of days ({MIN_EXPIRY_DAYS}-{MAX_EXPIRY_DAYS}).",
                }
        if not (MIN_EXPIRY_DAYS <= days <= MAX_EXPIRY_DAYS):
            return {
                "ok": False,
                "error": "invalid_expiry",
                "message": f"expires_days must be between {MIN_EXPIRY_DAYS} and {MAX_EXPIRY_DAYS} days.",
            }

        # The optional display name is owner-authored text shown to an EXAMINER —
        # run it through the shared forbidden-claims guard before it is stored.
        display_name = str(org_display_name or "").strip()[:_ORG_NAME_MAX_CHARS]
        if display_name:
            try:
                assert_no_forbidden_claims(display_name)
            except EvidencePackError:
                return {
                    "ok": False,
                    "error": "forbidden_claim",
                    "message": (
                        "The display name contains wording StatuteProof does not "
                        "publish (e.g. compliance guarantees). Please rephrase it."
                    ),
                }

        # Entitlement at creation — the moment the scope is frozen.
        entitled = _entitled_source_ids(user_id, source_ids)
        if not entitled:
            return {
                "ok": False,
                "error": "no_entitled_sources",
                "message": "None of the requested sources are in your plan scope.",
            }

        # Bound the scope BEFORE sealing it: a share whose period+sources already
        # hold more than max_records sealed records is rejected outright, so the
        # public endpoint can never be pointed at an unbounded scope by design.
        root = base_dir or _BASE_DIR
        records = _collect_room_records(
            root, set(entitled), str(date_from), f"{date_to}T23:59:59", limit=max_records
        )
        if len(records) > max_records:
            return {
                "ok": False,
                "error": "too_large",
                "max_records": max_records,
                "message": (
                    f"This scope spans more than {max_records} sealed records. "
                    "Narrow the period or the number of sources — an evidence room "
                    "is a focused review surface for one engagement, not a bulk export."
                ),
            }

        token = secrets.token_urlsafe(32)
        token_hash = _hash_token(token)
        now = _now()
        expires_at = _iso(now + timedelta(days=days))
        created_at = _iso(now)

        ensure_evidence_shares_table()
        conn = _connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO evidence_shares
                    (token_hash, owner_user_id, org_display_name, source_ids,
                     date_from, date_to, created_at, expires_at, revoked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    token_hash,
                    user_id,
                    display_name,
                    json.dumps(entitled),
                    str(date_from),
                    str(date_to),
                    created_at,
                    expires_at,
                ),
            )
            conn.commit()
            share_id = int(cur.lastrowid or -1)
        finally:
            conn.close()

        return {
            "ok": True,
            "share_id": share_id,
            # Returned ONCE. Not stored anywhere in raw form.
            "token": token,
            "source_ids": entitled,
            "date_from": str(date_from),
            "date_to": str(date_to),
            "created_at": created_at,
            "expires_at": expires_at,
            "record_count": len(records),
            "org_display_name": display_name,
        }
    except Exception as exc:  # noqa: BLE001 — never raise across the boundary
        logger.error("evidence_room.create_share failed: %s", type(exc).__name__)
        return {"ok": False, "error": "internal", "message": "Could not create the share."}


# ── share management (owner-scoped) ───────────────────────────────────────────────

def _share_status(row: dict[str, Any], now: datetime) -> str:
    if row.get("revoked_at"):
        return "revoked"
    expires = _parse_ts(str(row.get("expires_at") or ""))
    if expires is None or expires <= now:
        return "expired"
    return "active"


def list_shares(user: Any) -> dict[str, Any]:
    """Return the caller's OWN shares (metadata only — never a token or hash)."""
    try:
        user_id = _safe_user_id(user)
        if user_id is None:
            return {"ok": True, "shares": []}
        ensure_evidence_shares_table()
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT id, org_display_name, source_ids, date_from, date_to,
                       created_at, expires_at, revoked_at
                FROM evidence_shares
                WHERE owner_user_id = ?
                ORDER BY id DESC
                LIMIT 200
                """,
                (user_id,),
            ).fetchall()
        finally:
            conn.close()
        now = _now()
        shares = []
        for r in rows:
            row = dict(r)
            try:
                ids = json.loads(str(row.get("source_ids") or "[]"))
            except (TypeError, ValueError):
                ids = []
            shares.append(
                {
                    "share_id": row["id"],
                    "org_display_name": row.get("org_display_name") or "",
                    "source_ids": ids if isinstance(ids, list) else [],
                    "date_from": row.get("date_from") or "",
                    "date_to": row.get("date_to") or "",
                    "created_at": row.get("created_at") or "",
                    "expires_at": row.get("expires_at") or "",
                    "revoked_at": row.get("revoked_at"),
                    "status": _share_status(row, now),
                }
            )
        return {"ok": True, "shares": shares}
    except Exception as exc:  # noqa: BLE001
        logger.error("evidence_room.list_shares failed: %s", type(exc).__name__)
        return {"ok": False, "error": "internal", "message": "Could not list shares."}


def revoke_share(user: Any, share_id: Any) -> dict[str, Any]:
    """Revoke one of the caller's OWN shares.

    A share not owned by the caller resolves exactly like a share that does not
    exist (``not_found``) — no existence oracle even for authenticated users.
    Revoking an already-revoked share is an idempotent success.
    """
    try:
        user_id = _safe_user_id(user)
        if user_id is None:
            return {"ok": False, "error": "not_found", "message": "Share not found."}
        try:
            sid = int(share_id)
        except (TypeError, ValueError):
            return {"ok": False, "error": "not_found", "message": "Share not found."}

        ensure_evidence_shares_table()
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT id, revoked_at FROM evidence_shares WHERE id = ? AND owner_user_id = ?",
                (sid, user_id),
            ).fetchone()
            if row is None:
                return {"ok": False, "error": "not_found", "message": "Share not found."}
            if row["revoked_at"]:
                return {"ok": True, "share_id": sid, "already_revoked": True}
            conn.execute(
                "UPDATE evidence_shares SET revoked_at = ? WHERE id = ? AND owner_user_id = ?",
                (_iso(_now()), sid, user_id),
            )
            conn.commit()
        finally:
            conn.close()
        return {"ok": True, "share_id": sid, "already_revoked": False}
    except Exception as exc:  # noqa: BLE001
        logger.error("evidence_room.revoke_share failed: %s", type(exc).__name__)
        return {"ok": False, "error": "internal", "message": "Could not revoke the share."}


# ── the public room view ──────────────────────────────────────────────────────────

def get_room_view(
    token: Any,
    *,
    base_dir: Path | None = None,
    max_records: int = MAX_ROOM_RECORDS,
) -> dict[str, Any] | None:
    """Resolve a public room token to its scoped, read-only view. Never raises.

    Returns ``None`` for EVERY failure mode — malformed token, unknown token,
    revoked share, expired share, unparsable expiry, internal error — so the
    HTTP layer can answer with one identical 404 and leak nothing about which
    case occurred. On success returns the view dict (frozen scope only).

    Every resolution attempt that reaches a stored share is appended to the
    immutable access log as ``room.view`` (allow/deny); a token that matches no
    row is logged as a deny with no resource id. Logging is best-effort and
    never changes the outcome.
    """
    try:
        raw = str(token or "").strip()
        if not _TOKEN_RE.fullmatch(raw):
            return None  # malformed — not worth a DB round-trip or a log row

        presented_hash = _hash_token(raw)
        ensure_evidence_shares_table()
        conn = _connect()
        try:
            row = conn.execute(
                """
                SELECT id, token_hash, owner_user_id, org_display_name, source_ids,
                       date_from, date_to, created_at, expires_at, revoked_at
                FROM evidence_shares
                WHERE token_hash = ?
                """,
                (presented_hash,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            _log_room_access(None, RESULT_DENY)
            return None
        share = dict(row)

        # Constant-time re-check of the hash equality (defense in depth over the
        # indexed lookup; the compared values are fixed-length digests).
        if not hmac.compare_digest(presented_hash, str(share.get("token_hash") or "")):
            _log_room_access(share.get("id"), RESULT_DENY)
            return None

        if share.get("revoked_at"):
            _log_room_access(share.get("id"), RESULT_DENY)
            return None
        expires = _parse_ts(str(share.get("expires_at") or ""))
        if expires is None or expires <= _now():  # unparsable expiry fails CLOSED
            _log_room_access(share.get("id"), RESULT_DENY)
            return None

        try:
            frozen_ids = json.loads(str(share.get("source_ids") or "[]"))
        except (TypeError, ValueError):
            frozen_ids = None
        if not isinstance(frozen_ids, list) or not frozen_ids:
            _log_room_access(share.get("id"), RESULT_DENY)
            return None
        wanted = {str(s).strip() for s in frozen_ids if str(s).strip()}

        root = base_dir or _BASE_DIR
        date_from = str(share.get("date_from") or "")
        date_to = str(share.get("date_to") or "")
        records = _collect_room_records(
            root, wanted, date_from, f"{date_to}T23:59:59", limit=max_records
        )
        truncated = len(records) > max_records
        if truncated:
            records = records[:max_records]
        records.sort(key=lambda r: str(r.get("timestamp") or ""))

        view = {
            "shared_by": str(share.get("org_display_name") or "") or None,
            "period": {"date_from": date_from, "date_to": date_to},
            "created_at": str(share.get("created_at") or ""),
            "expires_at": str(share.get("expires_at") or ""),
            "sources": _describe_sources(sorted(wanted)),
            "records": records,
            "record_count": len(records),
            "truncated": truncated,
            "coverage": _coverage_summary(records, wanted),
            "verification": {
                "verify_url": "/verify",
                "spec_url": "/api/verify-spec",
                "note": VERIFICATION_NOTE,
            },
            "note": ROOM_HEADER_NOTE,
            "disclaimer": LEGAL_DISCLAIMER,
            "legal_notice": FULL_LEGAL_DISCLAIMER,
        }

        # Legal-safety gate over the authored prose (the same shared guard the
        # evidence pack runs before shipping). Source-derived record content is
        # quoted monitoring data and is NOT scanned — a regulator's own page may
        # legitimately contain phrases StatuteProof itself must never author.
        assert_no_forbidden_claims(
            " ".join([ROOM_HEADER_NOTE, VERIFICATION_NOTE, view["shared_by"] or ""])
        )

        _log_room_access(share.get("id"), RESULT_ALLOW)
        return view
    except Exception as exc:  # noqa: BLE001 — fail closed, never raise
        logger.error("evidence_room.get_room_view failed: %s", type(exc).__name__)
        return None


# ── internal helpers ──────────────────────────────────────────────────────────────

def _parse_ts(value: str) -> datetime | None:
    """Parse a stored ISO timestamp; None when unparsable (callers fail closed)."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _log_room_access(share_id: Any, result: str) -> None:
    """Append one immutable ``room.view`` row. Best-effort, NEVER raises.

    ``actor_user_id`` is ``None`` — the viewer is an external party with no
    account. The share id is the resource, so the owner's audit trail shows
    exactly which share was opened (or probed) and when.
    """
    try:
        append_access_log(
            actor_user_id=None,
            org_id=None,
            action=ROOM_VIEW_ACTION,
            result=str(result),
            resource_type="evidence_share",
            resource_id=str(share_id) if share_id is not None else "",
        )
    except Exception:  # noqa: BLE001 — audit logging must never break the view
        logger.warning("evidence_room: access-log write failed (non-fatal)")


def _collect_room_records(
    root: Path,
    wanted: set[str],
    date_from: str,
    date_to_end: str,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Bounded, METADATA-ONLY record collection for the room view.

    Applies the exact filter discipline of
    ``app.evidence_pack._collect_pack_entries`` — only ``record_status ==
    "complete"`` records whose ``integrity`` is VERIFIED, only sources in the
    frozen ``wanted`` set, only timestamps inside the range — but never loads
    snapshot bytes: the room shows seals and summaries, not content, so the
    public endpoint stays cheap and bounded. ``limit`` stops the scan one past
    the cap so callers can detect overflow without unbounded materialization.
    """
    evidence_root = root / "evidence"
    if not evidence_root.exists():
        return []

    # Scope the filesystem walk to the frozen source_ids ONLY. The on-disk layout
    # is evidence/<regulator>/<source_id>/<run_id>/evidence-record.json, so one
    # glob per wanted source (regulator wildcard) enumerates just that source's
    # own records — never the whole cross-tenant evidence store. This bounds the
    # public endpoint's cost to O(records in the requester's frozen scope), not
    # O(total product evidence). A source_id that isn't a safe path segment is
    # skipped (it could never have matched a real record dir anyway).
    record_paths: list[Path] = []
    for source_id in sorted(wanted):
        if not _SAFE_SOURCE_SEGMENT_RE.match(source_id):
            continue
        record_paths.extend(evidence_root.glob(f"*/{source_id}/**/evidence-record.json"))

    rows: list[dict[str, Any]] = []
    for record_path in sorted(record_paths):
        if limit is not None and len(rows) > limit:
            break  # one past the cap is enough to detect overflow
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
        if source_id not in wanted:  # scope guard: never a source outside the freeze
            continue

        run = record.get("run")
        if not isinstance(run, dict):
            run = {}
        naive = _naive_ts(str(run.get("timestamp") or ""))
        if not (naive and date_from <= naive <= date_to_end):
            continue

        change = record.get("change")
        if not isinstance(change, dict):
            change = {}
        content = record.get("content")
        if not isinstance(content, dict):
            content = {}
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            continue

        rows.append(
            {
                "record_id": record_id,
                "record_hash": str(record.get("record_hash") or ""),
                "record_hash_method": str(record.get("record_hash_method") or ""),
                # The normalized-content hash recorded at capture time — the
                # value the public verifier (/verify) checks against the
                # normalized snapshot bytes. Present on every record (including
                # legacy records that predate the whole-record seal), so an
                # examiner always has a verifiable value per record.
                "normalized_hash": str(content.get("current_hash") or ""),
                "timestamp": str(run.get("timestamp") or ""),
                "run_status": str(run.get("status") or ""),
                "source_id": source_id,
                "source_name": str(source.get("source_name") or source_id),
                "regulator": str(source.get("regulator") or ""),
                "official_url": str(source.get("official_url") or ""),
                "change_summary": _one_line(str(change.get("summary") or "")),
                "lines_added": str(change.get("lines_added") or ""),
                "lines_removed": str(change.get("lines_removed") or ""),
                "diff_excerpt": _diff_excerpt(record, root),
            }
        )
    return rows


def _diff_excerpt(record: dict[str, Any], root: Path) -> str:
    """Bounded, readable excerpt of the record's diff artifact — or "".

    Fail-closed on every edge: missing/escaping/non-file path, unreadable
    bytes, or mojibake-saturated text (the shared undecodable-content
    predicate) all yield an EMPTY excerpt rather than garbage in front of an
    examiner. Reads at most ``_DIFF_READ_CAP_BYTES``.
    """
    try:
        change = record.get("change")
        files = record.get("files")
        change = change if isinstance(change, dict) else {}
        files = files if isinstance(files, dict) else {}
        rel = str(change.get("diff_path") or files.get("diff_path") or "").strip()
        if not rel:
            return ""
        path = _safe_under_root(rel, root)
        if path is None or not path.is_file():
            return ""
        with path.open("rb") as handle:
            raw = handle.read(_DIFF_READ_CAP_BYTES)
        text = raw.decode("utf-8", errors="replace").strip()
        if not text or is_mostly_unreadable(text):
            return ""
        if len(text) > _DIFF_EXCERPT_MAX_CHARS:
            text = text[: _DIFF_EXCERPT_MAX_CHARS - 1].rstrip() + "…"
        return text
    except Exception:  # noqa: BLE001 — an excerpt is a nicety, never a failure
        return ""


def _one_line(text: str) -> str:
    """Collapse a summary to a single trimmed line (mirrors regulator_binder)."""
    collapsed = " ".join(str(text or "").split())
    if len(collapsed) > _SUMMARY_MAX_CHARS:
        collapsed = collapsed[: _SUMMARY_MAX_CHARS - 1].rstrip() + "…"
    return collapsed


def _describe_sources(source_ids: list[str]) -> list[dict[str, str]]:
    """Public-safe descriptors for the frozen source ids.

    Resolves display metadata from sources.json when possible; an unresolvable
    id degrades to an id-only entry (never an error — the frozen scope is the
    truth, the catalog is just decoration). Only name/regulator/official URL are
    exposed — these describe PUBLIC official sources (or the owner's own custom
    source, which the owner chose to share).
    """
    catalog: dict[str, dict[str, str]] = {}
    try:
        from app.source_intake import load_sources_json

        for s in load_sources_json():
            if not isinstance(s, dict):
                continue
            sid = str(s.get("source_id") or "").strip()
            if sid:
                catalog[sid] = {
                    "source_name": str(s.get("name") or s.get("source_name") or sid),
                    "regulator": str(s.get("regulator") or ""),
                    "official_url": str(s.get("url") or s.get("official_url") or ""),
                }
    except Exception:  # noqa: BLE001 — catalog is decoration only
        catalog = {}
    described = []
    for sid in source_ids:
        meta = catalog.get(sid, {})
        described.append(
            {
                "source_id": sid,
                "source_name": meta.get("source_name", sid),
                "regulator": meta.get("regulator", ""),
                "official_url": meta.get("official_url", ""),
            }
        )
    return described


def _coverage_summary(records: list[dict[str, Any]], wanted: set[str]) -> dict[str, Any]:
    """Honest coverage counts for the shared scope — no completeness claims."""
    sources_with_records = {r["source_id"] for r in records}
    timestamps = sorted(str(r.get("timestamp") or "") for r in records if r.get("timestamp"))
    changed = sum(1 for r in records if str(r.get("run_status") or "").upper() == "CHANGED")
    return {
        "sources_in_scope": len(wanted),
        "sources_with_records": len(sources_with_records),
        "sources_without_records": len(wanted - sources_with_records),
        "total_records": len(records),
        "changed_records": changed,
        "first_capture": timestamps[0] if timestamps else "",
        "last_capture": timestamps[-1] if timestamps else "",
    }
