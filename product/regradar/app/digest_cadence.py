"""Configurable digest cadence + all-clear monitoring heartbeat.

This module turns the per-user routing preview
(``app.alert_routing.build_routing_preview_for_user``) into scheduled customer
delivery, governed by each customer's own profile:

  * ``digest_cadence`` — ``instant`` | ``daily`` | ``weekly``
  * ``urgent_threshold`` / ``weekly_threshold`` — relevance-score gates (0-100)

Delivery rules (all evidence-grounded — only human-reviewed, APPROVED alert
drafts that already passed the routing gate are ever considered):

  * Instant path: a matched, delivery-ready alert that is HIGH-risk OR scores at
    or above the customer's ``urgent_threshold`` fires IMMEDIATELY, one message
    per alert, reusing ``send_preview_alert_to_user`` (per-alert idempotency).
  * Digest path (daily/weekly cadence): every other matched, delivery-ready
    alert scoring at or above ``weekly_threshold`` is bundled into ONE
    risk-sorted summary message per customer per period, idempotent via the
    ``user_delivery_log`` unique idempotency key.
  * Quiet window: when a customer has nothing to deliver in a digest period, an
    "all-clear" heartbeat confirms monitoring ran — grounded in real source-run
    counts, and worded so it never claims completeness ("never miss").

Every customer-facing string here carries the standard disclaimer and is run
through the shared forbidden-claims guard before it can be sent.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from app.alert_routing import (
    _risk_rank,
    build_routing_preview_for_user,
    send_preview_alert_to_user,
    user_profile_to_routing_profile,
)
from app.change_register import assert_no_forbidden_claims
from app.evidence_assessment import LEGAL_DISCLAIMER
from app.profile import (
    CADENCE_DAILY,
    CADENCE_INSTANT,
    CADENCE_WEEKLY,
)
from app.telegram_pairing import (
    alerts_require_plan,
    get_linked_alert_user_ids,
    get_telegram_link,
    plan_eligible_user_ids,
)
from app.user_delivery import (
    create_delivery_log,
    reclaim_failed_delivery_log,
    update_delivery_log_failed,
    update_delivery_log_sent,
)

logger = logging.getLogger(__name__)

# How far back the routing preview looks for approved reviewed alerts. Matches
# the default the API uses; the reviewed-alert window is intentionally short.
DEFAULT_LOOKBACK_DAYS = 14

_CADENCE_LABEL = {
    CADENCE_INSTANT: "Instant",
    CADENCE_DAILY: "Daily",
    CADENCE_WEEKLY: "Weekly",
}

# Max bundled items rendered in one digest message (risk-sorted; the rest are
# summarised as "+N more"). Keeps the message well under Telegram's 4096 limit.
_MAX_BUNDLE_ITEMS = 20
_MESSAGE_LIMIT = 4096


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _period_key(cadence: str, now: datetime) -> str:
    """Deterministic period identifier used for digest/heartbeat idempotency."""
    if cadence == CADENCE_WEEKLY:
        # ISO year + week so the key rolls over exactly once per ISO week.
        return now.strftime("%G-W%V")
    return now.date().isoformat()


def _period_label(cadence: str, now: datetime) -> str:
    if cadence == CADENCE_WEEKLY:
        iso_year, iso_week, _ = now.isocalendar()
        return f"ISO week {iso_year}-W{iso_week:02d}"
    return now.date().isoformat()


def _is_high_risk(match: dict[str, Any]) -> bool:
    return str(match.get("risk_level") or "").strip().upper() == "HIGH"


def _is_instant(match: dict[str, Any], urgent_threshold: int) -> bool:
    """A matched alert is instant when it is HIGH-risk or clears urgent_threshold."""
    return _is_high_risk(match) or int(match.get("score") or 0) >= int(urgent_threshold)


def _sort_key(match: dict[str, Any]):
    return (
        _risk_rank(match.get("risk_level")),
        int(match.get("score") or 0),
        str(match.get("reviewed_at") or ""),
    )


def split_matches_for_cadence(
    matches: list[dict[str, Any]],
    *,
    urgent_threshold: int,
    weekly_threshold: int,
    suppress_ids: set[str] | frozenset[str] | tuple[str, ...] = (),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split delivery-ready matches into (instant, bundle), risk-sorted.

    Only ``delivery_ready`` matches whose ``alert_id`` is not in ``suppress_ids``
    are considered — so alerts already sent (instant or a prior digest) are never
    re-bundled. Pure and deterministic (no I/O): this is the unit-testable core
    of the cadence gate.
    """
    suppress = {str(i) for i in suppress_ids}
    instant: list[dict[str, Any]] = []
    bundle: list[dict[str, Any]] = []
    for match in matches:
        if not match.get("delivery_ready"):
            continue
        if str(match.get("alert_id") or "") in suppress:
            continue
        if _is_instant(match, urgent_threshold):
            instant.append(match)
        elif int(match.get("score") or 0) >= int(weekly_threshold):
            bundle.append(match)
    instant.sort(key=_sort_key, reverse=True)
    bundle.sort(key=_sort_key, reverse=True)
    return instant, bundle


# ── message rendering (customer-facing; disclaimer + forbidden-claims guard) ──


def _truncate(text: str, limit: int) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def render_digest_message(
    user_profile: dict[str, Any],
    bundle: list[dict[str, Any]],
    *,
    cadence: str,
    period_label: str,
) -> str:
    """Render ONE risk-sorted digest summary for a customer's period bundle.

    Evidence-grounded: each line restates the human-reviewed alert's source,
    market, type, risk, one-line summary, and official-source proof URL. It says
    what changed and what the reader may wish to review — never advice, never a
    guarantee. The standard disclaimer is appended and the shared
    forbidden-claims guard runs over the final text before it is returned.
    """
    label = _CADENCE_LABEL.get(cadence, "Monitoring")
    count = len(bundle)
    header_lines = [
        f"StatuteProof - {label} monitoring digest",
        period_label,
        "",
        f"{count} human-reviewed change(s) matched your saved profile:",
        "",
    ]

    from app.alert_content import impact_tag_for_delivery

    body_lines: list[str] = []
    for index, match in enumerate(bundle[:_MAX_BUNDLE_ITEMS], start=1):
        risk = str(match.get("risk_level") or "MEDIUM").upper()
        source = match.get("source_name") or "Official source"
        market = match.get("market") or match.get("jurisdiction") or "Not specified"
        change_type = match.get("change_type") or "Regulatory update"
        reviewed = str(match.get("reviewed_at") or "").split("T")[0] or "reviewed"
        summary = _truncate(match.get("executive_summary") or "", 240)
        proof = match.get("source_url") or "Source URL unavailable"
        body_lines.append(f"{index}) [{risk}] {source} ({market})")
        body_lines.append(f"   Type: {change_type} | Reviewed: {reviewed}")
        if summary:
            body_lines.append(f"   {summary}")
        # Per-recipient impact tag (additive; only when THIS customer's topics
        # overlap the source topics and a real diff excerpt backs it).
        impact = impact_tag_for_delivery(match, user_profile)
        if impact:
            body_lines.append(f"   {impact['impact_line']}")
        body_lines.append(f"   Source: {proof}")
        body_lines.append("")
    remaining = count - min(count, _MAX_BUNDLE_ITEMS)
    if remaining > 0:
        body_lines.append(f"...and {remaining} more in your dashboard.")
        body_lines.append("")

    # The legal boundary (context paragraph + disclaimer + manage line) is
    # RESERVED: it is appended AFTER the bundle body is truncated to fit, so a
    # large bundle can never truncate the mandatory "Not legal advice" boundary
    # off the end of the delivered message (BLOCK-1 fail-closed contract).
    footer_lines = [
        (
            "Each item was reviewed by a human editor and matched to your saved "
            "profile. This digest describes what changed and what you may wish to "
            "review against the official source and evidence record."
        ),
        LEGAL_DISCLAIMER,
        "Manage alerts: StatuteProof -> Integrations",
    ]

    header = "\n".join(header_lines)
    footer = "\n".join(footer_lines)
    # Reserve header + footer + the two "\n" separators joining header/body/footer.
    reserved = len(header) + len(footer) + 2
    body_budget = max(0, _MESSAGE_LIMIT - reserved)
    body = "\n".join(body_lines)
    if len(body) > body_budget:
        body = body[: max(0, body_budget - 3)].rstrip() + "..."

    message = "\n".join([header, body, footer])

    # Fail closed on the FINAL string: re-run the forbidden-claims guard on the
    # exact bytes we will send, and hard-assert the mandatory disclaimer survived.
    assert_no_forbidden_claims(message)
    if LEGAL_DISCLAIMER not in message:
        raise ValueError("Digest message is missing the mandatory legal disclaimer boundary.")
    return message


def render_heartbeat_message(
    user_profile: dict[str, Any],
    stats: dict[str, Any],
    *,
    cadence: str,
    period_label: str,
) -> str:
    """Render an all-clear heartbeat for a quiet digest window.

    Grounded strictly in recorded source-run counts (never a completeness
    claim). It reassures the customer that monitoring ran while explicitly
    stating it is not a guarantee that every possible update was captured.
    """
    label = _CADENCE_LABEL.get(cadence, "Monitoring")
    sources_checked = int(stats.get("sources_checked") or 0)
    lines = [
        f"StatuteProof - {label} monitoring update",
        period_label,
        "",
        "Monitoring is active.",
        (
            f"In this period StatuteProof checked {sources_checked} official "
            f"source(s) and no new human-reviewed changes were queued for your "
            f"{label.lower()} digest."
        ),
        "",
        (
            "This confirms your monitoring ran during the period. It is not a "
            "statement that every possible update to every source was captured; "
            "source monitoring can be affected by publication delays, access "
            "limits, or website changes. You may wish to review the official "
            "sources directly."
        ),
        LEGAL_DISCLAIMER,
        "Manage alerts: StatuteProof -> Integrations",
    ]
    message = "\n".join(lines)
    assert_no_forbidden_claims(message)
    return _truncate(message, _MESSAGE_LIMIT)


# ── grounded heartbeat stats (reads recorded source runs only) ───────────────


def build_heartbeat_stats(
    *,
    window_days: int,
    now: datetime | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Count distinct sources checked (and changes recorded) within the window.

    Reads ONLY saved source-run records via ``source_health_timeline._read_runs``
    — it never backfills or invents monitoring history. Best-effort: on any read
    error it returns zero counts rather than raising (a heartbeat must never
    break the scheduler).
    """
    from app.source_health_timeline import _BASE_DIR, _read_runs

    root = base_dir or _BASE_DIR
    reference = now or _now_utc()
    cutoff = reference - timedelta(days=max(1, int(window_days)))
    sources: set[str] = set()
    changes = 0
    try:
        for run in _read_runs(root):
            ts_raw = str(run.get("timestamp_utc") or run.get("run_at") or "")
            parsed = _parse_run_ts(ts_raw)
            if parsed is None or parsed < cutoff or parsed > reference:
                continue
            sid = str(run.get("source_id") or "").strip()
            if sid:
                sources.add(sid)
            if str(run.get("change_status") or "").upper() == "CHANGED":
                changes += 1
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("heartbeat stats read failed (non-fatal): %s", exc)
    return {
        "sources_checked": len(sources),
        "changes_in_window": changes,
        "window_days": int(window_days),
    }


def _parse_run_ts(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


# ── digest-dedup: alert_ids already delivered inside a bundle ────────────────


def get_digested_alert_ids_for_user(user_id: int) -> set[str]:
    """Return alert_ids this user has already received inside a digest bundle.

    Bundle items are delivered under one ``digest`` delivery-log row, so each
    included alert is also marked with a per-alert ``digest_alert`` row — this
    set is what suppresses a still-approved alert from re-appearing in the next
    period's bundle.
    """
    from app.db import _connect, ensure_delivery_log_table

    ensure_delivery_log_table()
    prefix = f"{int(user_id)}:digest_alert:"
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT alert_id
            FROM user_delivery_log
            WHERE user_id = ?
              AND delivery_type = 'digest_alert'
              AND status IN ('pending', 'sent')
              AND idempotency_key LIKE ?
            """,
            (int(user_id), prefix + "%"),
        ).fetchall()
        return {str(row["alert_id"]) for row in rows if row["alert_id"]}
    finally:
        conn.close()


def _digest_delivered_this_period(user_id: int, cadence: str, period_key: str) -> bool:
    """True if a digest bundle was already delivered for this (user, period).

    Guards the all-clear heartbeat: a period that already produced a digest is
    NOT a quiet window, so a later cycle (which sees every alert suppressed) must
    not contradict that digest with a "no changes" heartbeat.
    """
    from app.db import _connect, ensure_delivery_log_table

    ensure_delivery_log_table()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT 1
            FROM user_delivery_log
            WHERE idempotency_key = ?
              AND status IN ('pending', 'sent')
            LIMIT 1
            """,
            (f"{int(user_id)}:digest:{cadence}:{period_key}",),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _record_digested_alert(user_id: int, alert_id: str, *, source_id: str | None) -> None:
    """Write the per-alert dedup marker for a bundled alert (best-effort)."""
    safe_alert_id = str(alert_id or "").strip()
    if not safe_alert_id:
        return
    create_delivery_log(
        int(user_id),
        delivery_type="digest_alert",
        channel="telegram",
        status="sent",
        alert_id=safe_alert_id,
        source_id=source_id,
        idempotency_key=f"{int(user_id)}:digest_alert:{safe_alert_id}",
        metadata={"bundled": True},
    )


# ── per-user dispatch ────────────────────────────────────────────────────────


def dispatch_instant_for_user(
    user_id: int,
    *,
    days: int = DEFAULT_LOOKBACK_DAYS,
    preview: dict[str, Any] | None = None,
    send_preview_fn: Callable[[int, str], dict] | None = None,
) -> dict[str, Any]:
    """Fire every instant (HIGH-risk or >= urgent_threshold) alert immediately.

    Reuses ``send_preview_alert_to_user`` so per-alert idempotency, approval
    recheck, and delivery logging are all preserved — safe to call every cycle.
    Runs for a customer of ANY cadence (instant alerts are never withheld).
    """
    profile = user_profile_to_routing_profile(int(user_id))
    urgent = int(profile.get("urgent_threshold") or 0)
    view = preview if preview is not None else build_routing_preview_for_user(int(user_id), days)
    sender = send_preview_fn or send_preview_alert_to_user

    instant_ids = [
        str(match.get("alert_id"))
        for match in view.get("matches", [])
        if match.get("delivery_ready") and _is_instant(match, urgent)
    ]
    results: list[dict[str, Any]] = []
    for alert_id in instant_ids:
        try:
            outcome = sender(int(user_id), alert_id) or {}
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("instant dispatch failed for user=%s alert=%s: %s", user_id, alert_id, exc)
            outcome = {"ok": False, "reason": str(exc)}
        results.append({"alert_id": alert_id, **outcome})

    return {
        "user_id": int(user_id),
        "instant_candidates": len(instant_ids),
        "instant_sent": sum(1 for r in results if r.get("ok")),
        "results": results,
    }


def dispatch_digest_for_user(
    user_id: int,
    *,
    cadence: str | None = None,
    now: datetime | None = None,
    days: int = DEFAULT_LOOKBACK_DAYS,
    base_dir: Path | None = None,
    send_fn: Callable[[str, str], bool] | None = None,
    preview: dict[str, Any] | None = None,
    digested_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Send one bundle OR one all-clear heartbeat for a customer's digest period.

    Idempotent per (user, cadence, period): the ``user_delivery_log`` unique
    idempotency key means calling this repeatedly inside the same period never
    double-sends. Instant-only windows (a HIGH alert pending but nothing to
    bundle and nothing quiet) are a no-op here — the instant path owns them.
    """
    profile = user_profile_to_routing_profile(int(user_id))
    resolved_cadence = str(cadence or profile.get("digest_cadence") or CADENCE_DAILY).lower()
    if resolved_cadence not in {CADENCE_DAILY, CADENCE_WEEKLY}:
        # Instant cadence has no periodic bundle/heartbeat.
        return {"user_id": int(user_id), "cadence": resolved_cadence, "status": "no_digest_cadence"}

    reference = now or _now_utc()
    view = preview if preview is not None else build_routing_preview_for_user(int(user_id), days)
    suppress = digested_ids if digested_ids is not None else get_digested_alert_ids_for_user(int(user_id))
    instant, bundle = split_matches_for_cadence(
        view.get("matches", []),
        urgent_threshold=int(profile.get("urgent_threshold") or 0),
        weekly_threshold=int(profile.get("weekly_threshold") or 0),
        suppress_ids=suppress,
    )

    link = get_telegram_link(int(user_id))
    chat_id = link.get("telegram_chat_id")
    if not chat_id:
        # No connected Telegram — nothing to deliver. delivery_ready would
        # already be False, so bundle is empty; return without a heartbeat.
        return {"user_id": int(user_id), "cadence": resolved_cadence, "status": "telegram_not_connected"}

    sender = send_fn or _default_send_fn()
    period_key = _period_key(resolved_cadence, reference)
    period_label = _period_label(resolved_cadence, reference)

    if bundle:
        return _send_bundle(
            int(user_id),
            profile=profile,
            bundle=bundle,
            cadence=resolved_cadence,
            period_key=period_key,
            period_label=period_label,
            chat_id=str(chat_id),
            sender=sender,
        )

    if not instant:
        # A period that already produced a digest is NOT a quiet window — every
        # alert now looks suppressed, but the customer already received them.
        # Suppress the heartbeat so it can never contradict a same-period digest.
        if _digest_delivered_this_period(int(user_id), resolved_cadence, period_key):
            return {"user_id": int(user_id), "cadence": resolved_cadence, "status": "duplicate", "kind": "heartbeat_suppressed"}
        # Genuinely quiet window (nothing instant, nothing to bundle) -> heartbeat.
        window_days = 7 if resolved_cadence == CADENCE_WEEKLY else 1
        stats = build_heartbeat_stats(window_days=window_days, now=reference, base_dir=base_dir)
        return _send_heartbeat(
            int(user_id),
            profile=profile,
            stats=stats,
            cadence=resolved_cadence,
            period_key=period_key,
            period_label=period_label,
            chat_id=str(chat_id),
            sender=sender,
        )

    # Instant-only window: HIGH/urgent alerts pending but nothing to bundle and
    # not quiet. The instant path delivers those; the digest pass stays silent.
    return {"user_id": int(user_id), "cadence": resolved_cadence, "status": "instant_only"}


def _default_send_fn() -> Callable[[str, str], bool]:
    from app.telegram import send_telegram_message

    return send_telegram_message


def _send_bundle(
    user_id: int,
    *,
    profile: dict[str, Any],
    bundle: list[dict[str, Any]],
    cadence: str,
    period_key: str,
    period_label: str,
    chat_id: str,
    sender: Callable[[str, str], bool],
) -> dict[str, Any]:
    idempotency_key = f"{user_id}:digest:{cadence}:{period_key}"
    log = create_delivery_log(
        user_id,
        delivery_type="digest",
        channel="telegram",
        status="pending",
        title=f"{_CADENCE_LABEL.get(cadence, 'Monitoring')} monitoring digest",
        message_preview=f"{len(bundle)} reviewed change(s) for {period_label}",
        idempotency_key=idempotency_key,
        metadata={"cadence": cadence, "period": period_key, "alert_count": len(bundle)},
    )
    if log.get("created"):
        log_id = int(log["id"])
    else:
        reclaimed = reclaim_failed_delivery_log(idempotency_key)
        if reclaimed is None:
            return {"user_id": user_id, "cadence": cadence, "status": "duplicate", "kind": "digest"}
        log_id = reclaimed

    try:
        message = render_digest_message(profile, bundle, cadence=cadence, period_label=period_label)
    except Exception as exc:
        # Forbidden-claims guard (or a render fault) blocked this bundle. Mark
        # failed so it is not silently swallowed, and never send unguarded text.
        update_delivery_log_failed(log_id, f"Digest blocked before send: {exc}")
        logger.error("digest blocked before send for user=%s: %s", user_id, exc)
        return {"user_id": user_id, "cadence": cadence, "status": "blocked", "kind": "digest"}

    try:
        sent = sender(chat_id, message)
    except Exception as exc:
        update_delivery_log_failed(log_id, "Digest send raised an exception.")
        logger.warning("digest send raised for user=%s: %s", user_id, exc)
        return {"user_id": user_id, "cadence": cadence, "status": "failed", "kind": "digest"}

    if not sent:
        update_delivery_log_failed(log_id, "Digest send failed.")
        return {"user_id": user_id, "cadence": cadence, "status": "failed", "kind": "digest"}

    update_delivery_log_sent(log_id)
    for match in bundle:
        _record_digested_alert(user_id, str(match.get("alert_id") or ""), source_id=match.get("source_id"))
    return {
        "user_id": user_id,
        "cadence": cadence,
        "status": "sent",
        "kind": "digest",
        "alert_count": len(bundle),
        "log_id": log_id,
    }


def _send_heartbeat(
    user_id: int,
    *,
    profile: dict[str, Any],
    stats: dict[str, Any],
    cadence: str,
    period_key: str,
    period_label: str,
    chat_id: str,
    sender: Callable[[str, str], bool],
) -> dict[str, Any]:
    idempotency_key = f"{user_id}:heartbeat:{cadence}:{period_key}"
    log = create_delivery_log(
        user_id,
        delivery_type="monitoring_heartbeat",
        channel="telegram",
        status="pending",
        title=f"{_CADENCE_LABEL.get(cadence, 'Monitoring')} monitoring update",
        message_preview=f"All-clear heartbeat for {period_label}",
        idempotency_key=idempotency_key,
        metadata={"cadence": cadence, "period": period_key, **stats},
    )
    if log.get("created"):
        log_id = int(log["id"])
    else:
        reclaimed = reclaim_failed_delivery_log(idempotency_key)
        if reclaimed is None:
            return {"user_id": user_id, "cadence": cadence, "status": "duplicate", "kind": "heartbeat"}
        log_id = reclaimed

    try:
        message = render_heartbeat_message(profile, stats, cadence=cadence, period_label=period_label)
    except Exception as exc:
        update_delivery_log_failed(log_id, f"Heartbeat blocked before send: {exc}")
        logger.error("heartbeat blocked before send for user=%s: %s", user_id, exc)
        return {"user_id": user_id, "cadence": cadence, "status": "blocked", "kind": "heartbeat"}

    try:
        sent = sender(chat_id, message)
    except Exception as exc:
        update_delivery_log_failed(log_id, "Heartbeat send raised an exception.")
        logger.warning("heartbeat send raised for user=%s: %s", user_id, exc)
        return {"user_id": user_id, "cadence": cadence, "status": "failed", "kind": "heartbeat"}

    if not sent:
        update_delivery_log_failed(log_id, "Heartbeat send failed.")
        return {"user_id": user_id, "cadence": cadence, "status": "failed", "kind": "heartbeat"}

    update_delivery_log_sent(log_id)
    return {
        "user_id": user_id,
        "cadence": cadence,
        "status": "sent",
        "kind": "heartbeat",
        "sources_checked": int(stats.get("sources_checked") or 0),
        "log_id": log_id,
    }


# ── scheduler entry point ────────────────────────────────────────────────────


def run_scheduled_digests(
    *,
    now: datetime | None = None,
    days: int = DEFAULT_LOOKBACK_DAYS,
    base_dir: Path | None = None,
    send_fn: Callable[[str, str], bool] | None = None,
    user_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Dispatch instant alerts + per-cadence digests/heartbeats for all customers.

    Safe to call every scheduler cycle: instant sends are per-alert idempotent,
    and daily/weekly bundles + heartbeats are idempotent per period, so the
    period key (not a scheduler timer) enforces the cadence. Never raises — a
    single customer failure is logged and dispatch continues.
    """
    reference = now or _now_utc()
    try:
        if user_ids is not None:
            # Explicit override: operator/test driven, deliberately UNGATED
            # (mirrors deadline_radar.send_due_reminders' recipients= path).
            ids = list(user_ids)
        else:
            # Plan gate on the paid core deliverable (audit 07-20): this
            # scheduled path ships the SAME official-source content as the
            # broadcast in app/telegram.py, so it reads the same flag and the
            # same eligibility rule — otherwise a free paired account keeps
            # receiving instant alerts and digests every cycle.
            ids = get_linked_alert_user_ids()
            if alerts_require_plan():
                ids = plan_eligible_user_ids(ids)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("run_scheduled_digests: could not resolve users: %s", exc)
        return {"users": 0, "instant_sent": 0, "digests_sent": 0, "heartbeats_sent": 0, "errors": 1}

    summary = {
        "users": len(ids),
        "instant_sent": 0,
        "digests_sent": 0,
        "heartbeats_sent": 0,
        "errors": 0,
        "per_user": [],
    }
    for user_id in ids:
        try:
            profile = user_profile_to_routing_profile(int(user_id))
            cadence = str(profile.get("digest_cadence") or CADENCE_DAILY).lower()

            # Instant HIGH/urgent alerts fire for every customer, every cycle.
            instant_result = dispatch_instant_for_user(int(user_id), days=days)
            summary["instant_sent"] += int(instant_result.get("instant_sent") or 0)

            digest_result: dict[str, Any] = {"status": "instant_cadence"}
            if cadence in {CADENCE_DAILY, CADENCE_WEEKLY}:
                digest_result = dispatch_digest_for_user(
                    int(user_id),
                    cadence=cadence,
                    now=reference,
                    days=days,
                    base_dir=base_dir,
                    send_fn=send_fn,
                )
                if digest_result.get("status") == "sent":
                    if digest_result.get("kind") == "digest":
                        summary["digests_sent"] += 1
                    elif digest_result.get("kind") == "heartbeat":
                        summary["heartbeats_sent"] += 1

            summary["per_user"].append(
                {"user_id": int(user_id), "cadence": cadence, "instant": instant_result, "digest": digest_result}
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("run_scheduled_digests: user=%s failed: %s", user_id, exc)
            summary["errors"] += 1
    return summary
