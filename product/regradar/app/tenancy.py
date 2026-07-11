"""Single tenancy primitive — the ONE owner-scoping rule, shared everywhere.

StatuteProof's sources.json is a flat global list with no tenancy layer, so
"which custom sources may this user see" was historically re-derived ad hoc in
each handler. That let adjacent code paths (evidence endpoints, then the review
queue, then the delivery/routing pipeline) leak one tenant's PRIVATE custom
source to another. This module is the single, fail-closed source of truth so
every content path — HTTP handlers, the alert-routing pipeline, digests, exports
— computes the denied set the SAME way.

Rule: an *official* / shared (non-``custom``) source is public and visible to
everyone. A *custom* source is visible ONLY to the user recorded as its
``owner_user_id``. Ownership is fail-closed — a custom source whose owner cannot
be resolved to the caller (missing owner, unparsable owner, a duplicate/attacker
row with a different owner) is DENIED, never attributed.

Any new code that resolves a caller-supplied source_id / run_id /
evidence_record_id / record_id back to stored data MUST scope it through
``denied_custom_source_ids`` (or a helper built on it), keyed on the RESOLVED
record's source_id — never on caller input.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def same_owner(owner_user_id: object, user_id: object) -> bool:
    """True when a stored ``owner_user_id`` matches ``user_id``.

    Tolerant of int-vs-str storage (sources.json is hand-editable) and never
    raises: an owner value that can't be coerced to an int is a non-match, so it
    is never attributed to the caller.
    """
    if owner_user_id is None:
        return False
    try:
        return int(owner_user_id) == int(user_id)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


def denied_custom_source_ids(user_id: object) -> set[str]:
    """Custom source_ids the given user does NOT own (fail-closed).

    Returns the set of *custom* source_ids that must be hidden from ``user_id``:
    every custom source owned by someone else, plus legacy/unowned custom
    sources. Official (non-``custom``) sources are shared and never appear here.
    Never raises — on an unreadable source list it returns an empty set, which is
    the SAME fallback used by every caller (so an unreadable list degrades to
    "no custom sources visible" rather than leaking).

    A source_id is denied if ANY row for it is owned by another user (not a
    last-write-wins map), so a duplicate or attacker-injected row can never flip
    ownership to widen scope — at worst it fail-closes the id.
    """
    try:
        uid: object = int(user_id)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        # No usable user id → attribute nothing; deny every custom source.
        uid = -1
    denied: set[str] = set()
    try:
        from app.source_intake import load_sources_json

        for s in load_sources_json():
            if not isinstance(s, dict) or s.get("custom") is not True:
                continue
            sid = str(s.get("source_id") or "").strip()
            if sid and not same_owner(s.get("owner_user_id"), uid):
                denied.add(sid)
    except Exception:  # noqa: BLE001 — unreadable list → no per-source exclusion
        logger.warning("tenancy: could not load sources.json for owner filter")
    return denied


def is_custom_source(source_id: object) -> bool:
    """True when ``source_id`` is a customer's PRIVATE custom source.

    Custom source_ids follow the deterministic ``"custom-" + sha256(url)[:8]``
    convention (see ``_handle_custom_sources_add``), so this holds even when
    ``sources.json`` is unreadable — which makes the automated-delivery path
    fail CLOSED (a ``custom-`` source is never mistaken for a shareable official
    one just because the source list could not be read). Also True when a
    resolvable row is explicitly flagged ``custom``.
    """
    sid = str(source_id or "").strip()
    if not sid:
        return False
    if sid.startswith("custom-"):
        return True
    try:
        from app.source_intake import load_sources_json

        for s in load_sources_json():
            if isinstance(s, dict) and str(s.get("source_id") or "").strip() == sid:
                return s.get("custom") is True
    except Exception:  # noqa: BLE001 — unreadable list → treat as non-custom (prefix already handled)
        return False
    return False


def custom_source_owner(source_id: object) -> int | None:
    """Return the SINGLE unambiguous ``owner_user_id`` of a custom source, or None.

    None means the source is official/shared, unknown, unreadable, OR a custom
    source with an ambiguous owner — more than one distinct owner across matching
    rows, or a row whose owner cannot be resolved to an int. This mirrors the
    fail-closed "any conflicting row denies" rule of ``denied_custom_source_ids``:
    since this drives DELIVERY routing (Telegram alerts, deadline reminders), a
    duplicate/attacker row must never be able to misroute one tenant's private
    alert to another. Callers on the delivery path must treat a None owner for a
    ``is_custom_source`` id as "deliver to nobody" (fail closed), never broadcast.
    """
    sid = str(source_id or "").strip()
    if not sid:
        return None
    owners: set[int] = set()
    saw_unresolvable = False
    try:
        from app.source_intake import load_sources_json

        for s in load_sources_json():
            if (
                isinstance(s, dict)
                and str(s.get("source_id") or "").strip() == sid
                and s.get("custom") is True
            ):
                try:
                    owners.add(int(s.get("owner_user_id")))  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    saw_unresolvable = True
    except Exception:  # noqa: BLE001 — unreadable list → unattributable
        return None
    if saw_unresolvable or len(owners) != 1:
        return None
    return next(iter(owners))


def source_visible_to(user_id: object, source_id: str) -> bool:
    """False only when ``source_id`` is a custom source owned by another user.

    Official / shared sources — and any source_id that does not resolve to a
    denied custom source — stay visible, so this only ever *adds* a denial.
    """
    sid = str(source_id or "").strip()
    if not sid:
        return True
    return sid not in denied_custom_source_ids(user_id)
