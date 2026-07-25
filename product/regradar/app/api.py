"""
RegRadar minimal API server (MVP).

Provides 3 endpoints for Telegram settings management:
  GET  /api/settings/telegram         — load public-safe settings
  POST /api/settings/telegram         — save settings
  POST /api/settings/telegram/test    — send test alert (server-side)

Uses only Python's built-in http.server — no extra dependencies.

Start with:
  python run.py api                   (default: 127.0.0.1:5001)
  python run.py api --port 8080
"""

import hashlib
import json
import logging
import os
import re
import threading
import time
from collections import defaultdict
from http.cookies import SimpleCookie
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import requests as _req

from app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    DuplicateEmailError,
    OAuthAccountError,
    create_session,
    create_google_oauth_state,
    create_user,
    delete_session,
    consume_google_oauth_state,
    exchange_google_oauth_code,
    generate_verification_token,
    consume_verification_token,
    verified_user_for_consumed_token,
    generate_password_reset_token,
    consume_password_reset_token,
    set_user_password,
    mark_email_verified,
    get_user_by_email,
    is_account_locked,
    get_user_by_id,
    google_oauth_authorization_url,
    google_oauth_available,
    link_or_create_google_user,
    make_public_user,
    normalize_email,
    record_failed_login,
    parse_session_cookie,
    require_auth,
    validate_email,
    validate_password,
    clear_failed_logins,
    verify_password,
)
from app import telegram_settings as _ts
from app import rbac_runtime
from app.config import (
    BASE_DIR,
    CONTACT_DELIVERY_DISABLED,
    TELEGRAM_ALERTS_BOT_USERNAME,
    TELEGRAM_BOT_USERNAME,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from app.email_delivery import send_verification_email as _send_verification_email
from app.email_delivery import send_password_reset_email as _send_password_reset_email
from app.profile import get_or_create_profile, update_profile
from app.telegram import send_telegram_message
from app.telegram_pairing import (
    create_pairing_code,
    get_pairing_status,
    get_telegram_link,
    touch_telegram_test_sent,
    unlink_telegram,
)
from app.user_delivery import get_user_delivery_logs, send_sample_brief_to_user
from app.alert_routing import (
    _official_alert_blocked_by_plan,
    build_routing_preview_for_user,
    find_routing_match_for_user,
    redact_decision_reviewed_for_plan,
    redact_effective_dates_for_plan,
    redact_preview_for_plan,
    send_preview_alert_to_user,
)
from app.alert_actions import save_action_log_entry, get_action_log
from app.account_export import build_account_export
from app.action_checklist import (
    FRAMING as CHECKLIST_FRAMING,
    add_checklist_item,
    delete_checklist_item,
    list_checklist_items,
    update_checklist_item,
    valid_alert_id as checklist_valid_alert_id,
)
from app.decision_records import (
    FRAMING as DECISION_FRAMING,
    KINDS as DECISION_KINDS,
    MAX_AMENDMENT_REASON_LEN as DECISION_MAX_REASON_LEN,
    MAX_DISPLAY_NAME_LEN as DECISION_MAX_NAME_LEN,
    MAX_STATEMENT_LEN as DECISION_MAX_STATEMENT_LEN,
    list_decisions,
    read_decision_head,
    seal_decision,
)
from app.public_verify import verify_submission

logger = logging.getLogger(__name__)

_TELEGRAM_TIMEOUT_S = 10
_CONTACT_QUEUE = BASE_DIR / "data" / "contact_requests.jsonl"


def _admin_email_allowlist() -> frozenset[str]:
    """Normalized founder emails permitted to reach the admin panel.

    Sourced from ``STATUTEPROOF_ADMIN_EMAILS`` (comma-separated). Empty when
    unset, so the founder admin surface is CLOSED by default until a founder
    email is explicitly configured — a deployment choice, never a hardcoded
    operator baked into the image. Never raises; a malformed entry is skipped.
    """
    raw = os.environ.get("STATUTEPROOF_ADMIN_EMAILS", "")
    out: set[str] = set()
    for part in str(raw).split(","):
        candidate = part.strip()
        if not candidate:
            continue
        try:
            out.add(normalize_email(candidate))
        except Exception:  # noqa: BLE001 — a bad allowlist entry must not crash the gate
            continue
    return frozenset(out)


def _notify_founder_registration(
    email: str, full_name: str = "", company_name: str = ""
) -> None:
    """Best-effort Telegram note to the founder when a new user registers.

    Fire-and-forget: runs in a daemon thread from _handle_auth_register and
    must NEVER raise — a Telegram outage or missing config cannot be allowed
    to affect the registration path.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        lines = ["🆕 New user registered", f"Email: {email}"]
        if full_name:
            lines.append(f"Name: {full_name}")
        if company_name:
            lines.append(f"Company: {company_name}")
        lines.append(
            f"Time (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        )
        resp = _req.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": "\n".join(lines),
                "disable_web_page_preview": True,
            },
            timeout=_TELEGRAM_TIMEOUT_S,
        )
        if not resp.json().get("ok"):
            logger.warning("Founder registration notify: Telegram API returned not-ok")
    except Exception as exc:  # noqa: BLE001 — deliberately swallow everything
        logger.warning("Founder registration notify failed: %s", type(exc).__name__)


def _notify_founder_plan_intent(email: str, plan_name: str) -> None:
    """Best-effort Telegram note to the founder when a customer records
    paid-plan intent.

    Fire-and-forget from _handle_plan_set; must NEVER raise — the customer is
    told "Our team will contact you", so the founder MUST be paged, but a
    Telegram outage or missing config cannot be allowed to fail the plan
    request.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        from app.plan import PLAN_DISPLAY, PLAN_PRICE_MONTHLY

        lines = [
            "💼 Plan intent recorded",
            f"Plan: {PLAN_DISPLAY.get(plan_name, plan_name)} ({plan_name})",
        ]
        price = PLAN_PRICE_MONTHLY.get(plan_name, 0)
        if isinstance(price, (int, float)) and price > 0:
            lines.append(f"Price: ${price}/mo")
        lines.append(f"Email: {email}")
        lines.append("Action: review and run activate-plan (DEPLOY.md §10)")
        lines.append(
            f"Time (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        )
        resp = _req.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": "\n".join(lines),
                "disable_web_page_preview": True,
            },
            timeout=_TELEGRAM_TIMEOUT_S,
        )
        if not resp.json().get("ok"):
            logger.warning("Founder plan-intent notify: Telegram API returned not-ok")
    except Exception as exc:  # noqa: BLE001 — deliberately swallow everything
        logger.warning("Founder plan-intent notify failed: %s", type(exc).__name__)

# CORS_ALLOWED_ORIGIN env var controls which origin is permitted.
# Leave unset in production (same-origin deployment) — no CORS headers will be sent.
# Set to http://localhost:5173 for local development against the Vite dev server.
# Comma-separated allowlist, e.g. "https://statuteproof.com,https://www.statuteproof.com".
# Single-value configs keep working unchanged. Unset = same-origin deployment,
# no CORS headers sent (the production default behind the reverse proxy).
_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGIN", "").split(",") if o.strip()
]

_CORS: dict[str, str] = {
    "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Credentials": "true",
}
if len(_ALLOWED_ORIGINS) == 1:
    _CORS["Access-Control-Allow-Origin"] = _ALLOWED_ORIGINS[0]


def _cors_headers(request_origin: str | None) -> dict[str, str]:
    """CORS headers for one response. With a multi-origin allowlist the
    matching request Origin is echoed; unlisted origins get no CORS grant."""
    if len(_ALLOWED_ORIGINS) <= 1:
        return _CORS
    headers = {k: v for k, v in _CORS.items()}
    if request_origin and request_origin in _ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = request_origin
        headers["Vary"] = "Origin"
    return headers

# Security headers — applied to every API response.
_SECURITY_HEADERS: dict[str, str] = {
    # API responses carry private account/evidence data — never cacheable.
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    # JSON API returns no HTML and loads no subresources — lock everything down.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
}


def _session_cookie_secure_for_host(host: str | None) -> bool:
    override = os.environ.get("STATUTEPROOF_COOKIE_SECURE", "").strip().lower()
    if override in {"1", "true", "yes", "on"}:
        return True
    if override in {"0", "false", "no", "off"}:
        return False

    normalized = str(host or "").strip().lower()
    if normalized.startswith(("localhost", "127.0.0.1", "[::1]")) or normalized == "::1":
        return False
    return True


def _truthy_param(value: object) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _same_owner(owner_user_id: object, user_id: int) -> bool:
    """Thin re-export of :func:`app.tenancy.same_owner` — the single ownership
    rule. Tolerant of int-vs-str storage and never raises (unresolvable owner →
    non-match, never attributed to the caller).
    """
    from app.tenancy import same_owner

    return same_owner(owner_user_id, user_id)


class _RateLimiter:
    """Small in-memory fixed-window limiter for MVP endpoint hardening."""

    def __init__(self, limit: int, window_seconds: int):
        self.limit = int(limit)
        self.window_seconds = int(window_seconds)
        self._hits = defaultdict(list)
        self._lock = threading.Lock()
        self._last_sweep = time.monotonic()

    def _sweep_expired(self, cutoff: float) -> None:
        """Drop keys whose entire hit window has expired.

        Called under ``self._lock``. Without this the dict grows one permanent
        entry per distinct key (e.g. per client IP) forever — a memory leak,
        since ``is_allowed`` otherwise writes back even an empty list.
        """
        stale = [k for k, v in self._hits.items() if not [ts for ts in v if ts > cutoff]]
        for k in stale:
            del self._hits[k]
        self._last_sweep = time.monotonic()

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            # Periodic full sweep so keys that stop receiving traffic are
            # eventually reclaimed (bounded to at most once per window).
            if now - self._last_sweep >= self.window_seconds:
                self._sweep_expired(cutoff)
            hits = [ts for ts in self._hits[key] if ts > cutoff]
            if len(hits) >= self.limit:
                self._hits[key] = hits
                return False
            hits.append(now)
            self._hits[key] = hits
            return True


_REGISTER_LIMITER = _RateLimiter(5, 3600)
_LOGIN_LIMITER = _RateLimiter(10, 3600)
_CONTACT_LIMITER = _RateLimiter(3, 3600)
# POST /api/plan (plan intent): a settings mutation that also pages the founder
# on the admin bot (2026-07-20 review — unthrottled, so an authenticated free
# account could loop it to bury real ops pages in the founder channel and churn
# one notify thread per request). Changing a plan is a rare, deliberate act;
# 10/hour per IP is generous for a human and caps the abuse surface.
_PLAN_INTENT_LIMITER = _RateLimiter(10, 3600)
# Founder admin panel (account roster + plan activation). Founder-only after the
# gate, but rate-limited anyway: a bounded budget caps brute-force / audit-log
# flooding attempts and keeps every call (allow AND deny) cheap to audit.
_ADMIN_LIMITER = _RateLimiter(60, 3600)
_SOURCE_TEST_LIMITER = _RateLimiter(10, 3600)
_PAIR_GENERATE_LIMITER = _RateLimiter(10, 3600)
_TELEGRAM_TEST_LIMITER = _RateLimiter(5, 3600)
_DELIVERY_TEST_BRIEF_LIMITER = _RateLimiter(5, 3600)
_DELIVERY_SEND_PREVIEW_LIMITER = _RateLimiter(10, 3600)
# Per-alert review checklist is an interactive workflow surface (ticking items,
# adding a few actions), so the budget is generous compared with delivery.
_CHECKLIST_LIMITER = _RateLimiter(120, 3600)
# Sealed-redline view: read-only per-alert render of the sealed diff. Bounded
# work (capped file read + pure parse) but touches the evidence tree, so it gets
# its own budget rather than riding an existing one.
_REDLINE_LIMITER = _RateLimiter(120, 3600)
# Sealed decision log: sealing is a deliberate, occasional act (each seal writes
# an append-only chained record), so the budget is deliberately tighter than the
# interactive checklist. NOTE: _rate_limited keys hits as "<ip>:<label>", so the
# GET (list) and POST (seal) labels each get their OWN independent 60/hour
# bucket per IP — a read burst can never starve a legitimate seal.
_DECISION_LIMITER = _RateLimiter(60, 3600)
# Canonical-evidence review queue: a heavy READ (whole-tree scan + per-record
# review-log read). Every other heavy read/export endpoint is throttled; this one
# was the lone unthrottled outlier (code review 2026-07-13), so a single logged-in
# client could loop it to pin CPU/disk. Throttled like an export.
_CANONICAL_EVIDENCE_LIMITER = _RateLimiter(60, 3600)
_BRIEFS_GENERATE_LIMITER = _RateLimiter(20, 3600)
# GET /api/evidence (full source_runs.jsonl read per request) and GET /api/briefs
# (whole alert_queue/*.json glob + parse per request) are heavy authenticated
# reads that were unthrottled (code review 2026-07-13) — a single logged-in
# client could loop either to pin disk/CPU. Same posture as the canonical review
# queue above: 60/hour, and (because _rate_limited keys hits as "<ip>:<label>")
# each gets its OWN independent per-IP bucket, so an evidence-list burst can never
# starve the briefs list or vice-versa.
_EVIDENCE_LIST_LIMITER = _RateLimiter(60, 3600)
_BRIEFS_LIST_LIMITER = _RateLimiter(60, 3600)
# Heavy export endpoints (audit vault, evidence pack, regulator binder, coverage
# certificate, monthly assurance, change-register export, evidence export). These
# build ZIPs and PDFs — meaningful disk/CPU work on the small production droplet.
# NOTE: _rate_limited keys each hit as "<ip>:<label>", so every export label gets
# its OWN independent 30/hour bucket per IP (not one shared cross-export budget).
# Per-request blast radius is bounded separately at the builder layer (e.g. the
# regulator binder caps record count via MAX_BINDER_RECORDS); if a single shared
# export budget per IP is wanted later, key this without the per-endpoint label.
_EXPORT_LIMITER = _RateLimiter(30, 3600)
# Self-service account data export (GET /api/account/export): a heavy-ish
# owner-scoped read — profile + every checklist item + the org's full sealed
# decision chain assembled into one JSON body. 10/hour is generous for a real
# "take my data out" need while bounding repeated full-chain reads per IP.
_ACCOUNT_EXPORT_LIMITER = _RateLimiter(10, 3600)
# Public, no-login evidence verifier (POST /api/verify). Verification is cheap
# (pure CPU, no disk, no evidence-store reads), but the endpoint is unauthenticated
# and internet-facing on a small VPS, so cap it per client IP to bound abuse.
_VERIFY_LIMITER = _RateLimiter(60, 3600)
# Public, no-login Auditor Evidence Room (GET /api/room/<token>). Mirrors the
# verifier's posture: unauthenticated and internet-facing, so per-IP capped. The
# view is bounded by construction (metadata-only collect with a hard record cap
# — see app.evidence_room.MAX_ROOM_RECORDS) but it does scan the evidence tree,
# so the same 60/hour ceiling applies to bound disk work from probes.
_ROOM_LIMITER = _RateLimiter(60, 3600)
# Public, no-login Stripe webhook (POST /api/stripe/webhook). Authenticated by
# the Stripe signature, not a session, so it is internet-facing and unauthenticated
# at the HTTP layer — cap per client IP to bound a flood of forged/garbage bodies
# hitting the HMAC verify. Real Stripe delivery volume for billing events is far
# below this ceiling; a burst of rejects is cheap but still worth bounding.
_STRIPE_WEBHOOK_LIMITER = _RateLimiter(120, 3600)


# Cohesive handler-method groups extracted into mixin modules (god-object
# reduction, 2026-07-21). Imported HERE — after every name the mixins read from
# app.api (auth helpers, logger, limiters, feature functions) is already bound —
# so the circular import resolves cleanly. The mixins carry ONLY moved method
# bodies; all per-request helpers (_send_json, _rate_limited, _rbac_guard, …)
# stay on _Handler and are reached via self.
from app.api_telegram import _TelegramHandlerMixin  # noqa: E402
from app.api_plan import _PlanHandlerMixin  # noqa: E402
from app.api_auth import _AuthHandlerMixin  # noqa: E402
from app.api_alerts import _AlertsHandlerMixin  # noqa: E402
from app.api_evidence import _EvidenceHandlerMixin  # noqa: E402
from app.api_reports import _ReportsHandlerMixin  # noqa: E402
from app.api_sources import _SourcesHandlerMixin  # noqa: E402
from app.api_account import _AccountHandlerMixin  # noqa: E402


class _Handler(
    _TelegramHandlerMixin,
    _PlanHandlerMixin,
    _AuthHandlerMixin,
    _AlertsHandlerMixin,
    _EvidenceHandlerMixin,
    _ReportsHandlerMixin,
    _SourcesHandlerMixin,
    _AccountHandlerMixin,
    BaseHTTPRequestHandler,
):

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002  # silence default stderr logging; params required by base class interface
        logger.debug("API %s %s", self.command, self.path)

    # ── helpers ────────────────────────────────────────────────────────────────

    def _send_json(
        self,
        data: dict,
        status: int = 200,
        extra_headers: list[tuple[str, str]] | None = None,
    ) -> None:
        # One-shot guard: never write a second response on the same connection.
        # A double response (e.g. _read_json emits 413, then the handler emits a
        # second status on the empty body) corrupts the HTTP stream the client
        # sees. The first response wins; subsequent calls are silently dropped.
        if getattr(self, "_response_sent", False):
            return
        self._response_sent = True
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in _cors_headers(self.headers.get("Origin")).items():
            self.send_header(k, v)
        for k, v in _SECURITY_HEADERS.items():
            self.send_header(k, v)
        for k, v in extra_headers or []:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(
        self,
        body: bytes,
        content_type: str,
        status: int = 200,
        extra_headers: list[tuple[str, str]] | None = None,
    ) -> None:
        """Write a raw binary response (e.g. a ZIP download) exactly once.

        Mirrors _send_json's one-shot guard, CORS, and security headers so a
        binary download shares the same response discipline.
        """
        if getattr(self, "_response_sent", False):
            return
        self._response_sent = True
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for k, v in _cors_headers(self.headers.get("Origin")).items():
            self.send_header(k, v)
        for k, v in _SECURITY_HEADERS.items():
            self.send_header(k, v)
        for k, v in extra_headers or []:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    _MAX_BODY_BYTES = 524_288  # 512 KB — reasonable for all API payloads

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        if length > self._MAX_BODY_BYTES:
            # Close the connection: the oversized body is left unread on the
            # socket, so the connection cannot be safely kept alive.
            self.close_connection = True
            self._send_json({"ok": False, "message": "Request body too large."}, 413)
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return {}

    def _read_raw_body(self) -> bytes | None:
        """Read the RAW request body bytes, honouring the shared size cap.

        Used where the exact bytes matter and must NOT be re-encoded by a JSON
        round-trip — specifically the Stripe webhook, whose signature is computed
        over the raw payload. Returns ``None`` (after emitting a 413) when the body
        exceeds ``_MAX_BODY_BYTES``, and ``b""`` when there is no body.
        """
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return b""
        if length > self._MAX_BODY_BYTES:
            self.close_connection = True
            self._send_json({"ok": False, "message": "Request body too large."}, 413)
            return None
        return self.rfile.read(length)

    def _read_json_strict(self) -> tuple[dict | None, str | None]:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}, None
        if length > self._MAX_BODY_BYTES:
            self.close_connection = True
            self._send_json({"ok": False, "message": "Request body too large."}, 413)
            return None, "Request body too large."
        try:
            data = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return None, "Invalid JSON."
        if not isinstance(data, dict):
            return None, "JSON body must be an object."
        return data, None

    def _session_cookie_header(self, session_id: str) -> str:
        cookie = SimpleCookie()
        cookie[SESSION_COOKIE_NAME] = session_id
        cookie[SESSION_COOKIE_NAME]["httponly"] = True
        cookie[SESSION_COOKIE_NAME]["samesite"] = "Strict"
        cookie[SESSION_COOKIE_NAME]["path"] = "/"
        cookie[SESSION_COOKIE_NAME]["max-age"] = str(SESSION_MAX_AGE_SECONDS)
        if _session_cookie_secure_for_host(self.headers.get("Host")):
            cookie[SESSION_COOKIE_NAME]["secure"] = True
        return cookie.output(header="").strip()

    def _clear_session_cookie_header(self) -> str:
        cookie = SimpleCookie()
        cookie[SESSION_COOKIE_NAME] = ""
        cookie[SESSION_COOKIE_NAME]["httponly"] = True
        cookie[SESSION_COOKIE_NAME]["samesite"] = "Strict"
        cookie[SESSION_COOKIE_NAME]["path"] = "/"
        cookie[SESSION_COOKIE_NAME]["max-age"] = "0"
        if _session_cookie_secure_for_host(self.headers.get("Host")):
            cookie[SESSION_COOKIE_NAME]["secure"] = True
        return cookie.output(header="").strip()

    def _client_ip(self) -> str:
        """Return the client IP from a proxy-controlled source only.

        Security / topology: production runs behind Caddy (see DEPLOY.md and
        deploy/Caddyfile). The API server binds to 127.0.0.1:5001 and Caddy's
        reverse_proxy block for ``/api/*`` **overwrites** X-Real-IP on every
        request::

            header_up -X-Real-IP           # drop any client-supplied value
            header_up X-Real-IP {remote_host}  # set the real TCP peer

        so X-Real-IP is guaranteed proxy-controlled and is the ONLY header we
        trust for the rate-limit key.

        X-Forwarded-For is deliberately NOT trusted: it is client-appendable
        and Caddy passes the inbound value through, so an attacker could mint a
        fresh rate-limit key per request (brute-force / spam bypass) and grow
        the limiter dict unbounded. When X-Real-IP is absent (a direct,
        non-proxied call — e.g. localhost dev or a probe hitting :5001), fall
        back to the socket peer, never to any client-supplied header.
        """
        real_ip = self.headers.get("X-Real-IP", "")
        if real_ip and real_ip.strip():
            return str(real_ip.strip())
        try:
            return str(self.client_address[0] or "unknown")
        except Exception:
            return "unknown"

    def _rate_limited(self, limiter: _RateLimiter, label: str) -> bool:
        key = f"{self._client_ip()}:{label}"
        if limiter.is_allowed(key):
            return False
        self._send_json(
            {"ok": False, "message": "Too many requests. Please wait before trying again."},
            429,
        )
        return True

    def _require_capability(self, user: dict, capability: str) -> bool:
        """Authorize a paid export against the user's plan capabilities.

        Reads ``app.plan.has_capability`` (backed by ``get_plan_state`` /
        ``PLAN_CAPABILITIES``). Returns ``True`` when the plan grants
        ``capability``; otherwise emits a 403 and returns ``False`` so the
        caller can ``return`` immediately. A default free (``evidence_preview``)
        account has every paid capability off, so it is rejected here before any
        export work is done. Never raises — a plan lookup failure denies access.
        """
        try:
            from app.plan import has_capability

            if has_capability(int(user["id"]), capability):
                return True
        except Exception:  # noqa: BLE001 — a broken plan lookup must fail closed
            logger.warning("capability check failed for %s", capability)
        self._send_json(
            {
                "ok": False,
                "message": "Your plan does not include this export. Upgrade your plan to continue.",
            },
            403,
        )
        return False

    def _caller_org_id(self, user: dict):
        """Resolve the caller's tenant (org) id for scoping PRIVATE per-tenant
        data — Acknowledge & Assess notes and review state. Returns the org id or
        None. Never raises; on failure returns None, and the assessment layer
        treats None as the empty legacy bucket, so a resolution failure ISOLATES
        (shows nothing) rather than leaking another tenant's notes."""
        try:
            return rbac_runtime.resolve_principal(user).org_id
        except Exception:  # noqa: BLE001 — unknown tenant must isolate, not leak
            return None

    def _rbac_guard(
        self,
        user: dict,
        action: str,
        *,
        resource_type: str = "",
        resource_id: str = "",
        fail_closed: bool = False,
    ) -> bool:
        """RBAC Stage-2 role gate for a MUTATING action. Returns True when permitted.

        Resolves the caller's Principal from org membership and evaluates the
        default-deny role matrix (``app.rbac.can`` via ``app.rbac_runtime``). EVERY
        existing account is backfilled as ``owner`` (full access), so this returns
        ``True`` and changes NOTHING for them — the only role in live data today is
        ``owner``. Only a non-owner role that lacks ``action`` (e.g. an ``auditor``
        seat attempting a mutation) is denied with 403.

        The allow/deny decision is written to the immutable access log (best-effort
        — logging never affects the outcome). Fails CLOSED on any internal RBAC
        error: the mutation is denied with a 403 UNLESS the caller still positively
        resolves to org ``owner`` (so a plumbing glitch never locks out the
        legitimate owner, and never escalates a lesser seat). ``fail_closed=True``
        callers deny even the owner. Do not revert this to fail-open — an RBAC
        evaluation error must not silently grant a mutation.
        """
        try:
            allowed, principal = rbac_runtime.evaluate(user, action)
        except Exception:  # noqa: BLE001 — RBAC must never break a live request
            # RBAC evaluation errored. This gate protects MUTATIONS only — every
            # call site passes a mutating action (settings/source/alert/review/
            # evidence-share); read-only observation uses ``_rbac_log_export``,
            # which never denies — so on error we FAIL CLOSED: deny the mutation
            # with a clean 403 rather than silently allowing it (the last security
            # fail-open in the tree). This is safe to ship even though only
            # ``owner`` seats exist in live data today: the ONLY caller re-admitted
            # is one we can still POSITIVELY resolve as the org ``owner`` — the
            # legitimate owner must never be locked out by an RBAC plumbing glitch.
            # ``resolve_principal`` is itself fail-closed (never raises; a lookup
            # failure yields role=``denied``), so this re-admits a genuine owner
            # only, never escalates a lesser (auditor/reviewer) seat.
            try:
                principal = rbac_runtime.resolve_principal(user)
            except Exception:  # noqa: BLE001 — resolution must not raise here
                principal = None
            is_owner = (
                principal is not None
                and getattr(principal, "role", None) == rbac_runtime.ROLE_OWNER
            )
            # High-stakes governance actions (minting/revoking an external
            # evidence-room credential) pass fail_closed=True and DENY even the
            # owner on error — never mint a durable external credential on a
            # plumbing failure. Everyone else fails closed unless they resolve to
            # owner.
            deny = fail_closed or not is_owner
            logger.warning(
                "rbac evaluate failed for %s; %s", action,
                "denying (fail-closed)" if deny else "allowing owner (no-regression)",
            )
            rbac_runtime.log_sensitive_action(
                user, action,
                result=rbac_runtime.RESULT_ERROR if deny else rbac_runtime.RESULT_ALLOW,
                resource_type=resource_type, resource_id=resource_id,
                principal=principal,
            )
            if deny:
                self._send_json(
                    {"ok": False, "message": "Authorization could not be verified. Please retry."},
                    403,
                )
                return False
            return True
        rbac_runtime.log_sensitive_action(
            user,
            action,
            result=rbac_runtime.RESULT_ALLOW if allowed else rbac_runtime.RESULT_DENY,
            resource_type=resource_type,
            resource_id=resource_id,
            principal=principal,
        )
        if allowed:
            return True
        self._send_json(
            {"ok": False, "message": "Your role does not permit this action."},
            403,
        )
        return False

    def _rbac_log_export(
        self,
        user: dict,
        *,
        resource_type: str = "evidence",
        resource_id: str = "",
    ) -> None:
        """Record an AUTHORIZED export to the immutable access log (Part A audit).

        Purely additive: exports are allowed for read-capable roles (incl. the
        read+export ``auditor``), so this only OBSERVES — it never denies. Wrapped
        end-to-end in ``rbac_runtime.log_sensitive_action`` so a logging failure is
        swallowed and the export proceeds exactly as before. Call it only after the
        export has passed its auth / capability / tenancy checks so the trail
        records genuine exports, not rejected attempts.
        """
        rbac_runtime.log_sensitive_action(
            user,
            rbac_runtime.EVIDENCE_EXPORT,
            result=rbac_runtime.RESULT_ALLOW,
            resource_type=resource_type,
            resource_id=resource_id,
        )

    def _entitle_source_ids(self, user: dict, requested: list) -> list[str]:
        """Clip caller-supplied source_ids to what the user is entitled to.

        Two independent restrictions are applied so a caller cannot widen their
        own scope by naming arbitrary IDs:

        1. Tenancy — a *custom* source may only be exported by the user who owns
           it (``owner_user_id``). Custom sources owned by someone else, and
           legacy custom sources with no owner recorded, are dropped. Official
           (non-custom) sources are shared and always pass this filter.
        2. Plan limit — the surviving list is truncated to the plan's
           ``source_limit`` so no request pulls more sources than the plan sells.

        Never raises — on any lookup failure it returns the tenancy-safe subset
        it could compute (falling back to an empty list), never the raw input.
        """
        try:
            user_id = int(user["id"])
        except (KeyError, TypeError, ValueError):
            return []

        clean_ids = [str(s).strip() for s in (requested or []) if str(s).strip()]
        if not clean_ids:
            return []

        # Fail-closed tenancy: drop any custom source the caller does not own.
        # This reuses the SAME denied-set semantics as _denied_custom_source_ids
        # (a source_id is denied if ANY row for it is owned by someone else),
        # rather than a last-write-wins ownership map. A duplicate or
        # attacker-injected row for the same source_id therefore cannot flip
        # ownership to widen scope — at worst it fail-closes the id. Official /
        # shared (non-custom) sources are never in the denied set, so they pass.
        denied = self._denied_custom_source_ids(user)
        entitled = [sid for sid in clean_ids if sid not in denied]

        try:
            from app.plan import source_limit_for

            limit = source_limit_for(user_id)
        except Exception:  # noqa: BLE001 — a broken plan lookup must not widen scope
            limit = 0
        if limit >= 0:
            entitled = entitled[:limit]
        return entitled

    def _denied_custom_source_ids(self, user: dict) -> set[str]:
        """Custom source_ids the caller does NOT own.

        Thin delegate to the single tenancy primitive
        (``app.tenancy.denied_custom_source_ids``) so this HTTP layer and the
        alert-routing / digest pipeline compute the denied set identically. Used
        to scope *default* (unfiltered) surfaces that would otherwise return rows
        for every source: any custom source not owned by the caller — and
        legacy/unowned custom sources — is denied so another customer's private
        source can never appear. Official (non-custom) sources are shared and are
        never denied. Never raises.
        """
        from app.tenancy import denied_custom_source_ids

        user_id = user.get("id") if isinstance(user, dict) else None
        return denied_custom_source_ids(user_id)

    def _visible_sources_for(self, user: dict, sources: list) -> list[dict]:
        """Filter a source-row list to what the caller may see (cross-tenant scope).

        ONE shared gate for EVERY authenticated source-listing surface (status,
        summary, timeline, readiness, coverage, evidence listing, …). Official /
        shared (non-``custom``) sources are public and always returned; a
        *custom* source is returned only to the user who owns it. Ownership is
        resolved with the same fail-closed semantics as
        ``_denied_custom_source_ids`` — any owner-mismatch row for a source_id
        denies it — so a duplicate or attacker-injected row can neither expose
        nor flip another tenant's private source. A future listing endpoint that
        routes its rows through this helper inherits the scoping by default.

        Never raises: rows that are not dicts are dropped; on an unreadable
        source list the denied set is empty so only official sources survive the
        ``custom``-flag check (custom rows without a resolvable owner are cut).
        """
        denied = self._denied_custom_source_ids(user)
        visible: list[dict] = []
        for s in sources:
            if not isinstance(s, dict):
                continue
            if s.get("custom") is True:
                sid = str(s.get("source_id") or "").strip()
                if not sid or sid in denied:
                    continue
            visible.append(s)
        return visible

    def _source_visible_to(self, user: dict, source_id: str) -> bool:
        """False only when ``source_id`` is a custom source owned by another tenant.

        Per-source-id guard for lookup endpoints (e.g. the timeline handler):
        official / shared sources — and any source_id that does not resolve to a
        denied *custom* source — stay visible, so this only ever *adds* a denial
        and never hides a public source. Fail-closed via
        ``_denied_custom_source_ids`` (any owner-mismatch row denies the id).
        """
        sid = str(source_id or "").strip()
        if not sid:
            return True
        return sid not in self._denied_custom_source_ids(user)

    def _evidence_source_out_of_scope(self, user: dict, evidence_id: str) -> bool:
        """True when an evidence record belongs to another tenant's custom source.

        Tenancy guard for EVERY by-id evidence endpoint — export, diff, review,
        review-history, and the assess write path (IDOR defense). It resolves the
        record's ``source_id`` from BOTH stores that a downstream handler might
        read (the run log via ``find_evidence_record`` AND the assessment store
        via ``latest_assessment_for``) and denies if EITHER resolves to a *custom*
        source owned by someone else. Consulting both is required: an assessment
        can outlive its run row (orphan), and a handler like ``review`` reads the
        assessment store directly — resolving only the run log would let an orphan
        leak. Official / shared sources, and ids that resolve nowhere, are left to
        the normal handler path, so this guard only ever *adds* a denial and never
        changes not-found/error behavior.
        """
        candidates: set[str] = set()
        try:
            from app.evidence_assessment import find_evidence_record, latest_assessment_for

            try:
                record = find_evidence_record(evidence_id)
                sid = str(record.get("source_id") or "").strip()
                if sid:
                    candidates.add(sid)
            except Exception:  # noqa: BLE001 — id may live only in the assessment store
                pass
            assessment = latest_assessment_for(evidence_id)
            if assessment:
                sid = str(assessment.get("source_id") or "").strip()
                if sid:
                    candidates.add(sid)
            # The customer-delivery export branch (build_customer_audit_pack_export
            # _response → build_risk_brief_inputs → load_evidence_record) resolves
            # a DIFFERENT id-space: a canonical record_id or a raw
            # evidence-record.json path. Resolve that space here too so the same
            # value cannot bypass this guard while the export path resolves it to
            # a victim's custom source (parity with _canonical_record_out_of_scope).
            try:
                from app.evidence_records import load_evidence_record

                canonical_record, _cpath = load_evidence_record(evidence_id)
                src = (
                    canonical_record.get("source")
                    if isinstance(canonical_record.get("source"), dict)
                    else {}
                )
                sid = str(src.get("source_id") or "").strip()
                if sid:
                    candidates.add(sid)
            except Exception:  # noqa: BLE001 — not a canonical id/path; export resolves identically
                pass
        except Exception:  # noqa: BLE001 — let the normal handler path emit 400/404
            return False
        if not candidates:
            return False
        denied = self._denied_custom_source_ids(user)
        return any(sid in denied for sid in candidates)

    def _canonical_record_out_of_scope(self, user: dict, record_id: str) -> bool:
        """True when a canonical evidence record belongs to another tenant's custom source.

        IDOR guard for the canonical review-action WRITE path. It resolves the
        target through the SAME ``load_evidence_record`` the write itself uses
        (``record_canonical_evidence_review`` → ``load_evidence_record``), which
        accepts EITHER a bare ``record_id`` OR a raw ``evidence-record.json``
        path. Resolving via that exact function guarantees resolution parity, so
        an attacker cannot bypass the guard by addressing the record with its
        path instead of its id. The record's ``source.source_id`` is denied only
        when it is a *custom* source owned by someone else. If resolution raises
        (unknown id/path), the write raises identically and mutates nothing, so
        returning False here is safe — the guard only ever *adds* a denial.
        """
        rid = str(record_id or "").strip()
        if not rid:
            return False
        try:
            from app.evidence_records import load_evidence_record

            record, _path = load_evidence_record(rid)
        except Exception:  # noqa: BLE001 — write resolves identically and no-ops → safe
            return False
        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        sid = str(source.get("source_id") or "").strip()
        if not sid:
            return False
        return sid in self._denied_custom_source_ids(user)

    def _caller_is_operator(self, user: dict) -> bool:
        """True only for a global/operator principal (org_id == GLOBAL_ORG_ID).

        A normal self-registered customer resolves to their own org (or None) and
        is ROLE_OWNER of that scope — never GLOBAL_ORG_ID — so this is the
        operator-only gate for write actions on SHARED official records whose
        effect spans every tenant. Never raises; on failure returns False (deny).
        """
        try:
            return self._caller_org_id(user) == rbac_runtime.GLOBAL_ORG_ID
        except Exception:  # noqa: BLE001 — unresolved principal is not an operator
            return False

    def _caller_is_admin(self, user: dict) -> bool:
        """True ONLY for the founder/operator — the founder admin panel gate.

        Two independent, POSITIVE signals (either suffices; both fail-safe):
        * an operator principal (GLOBAL-org scope), or
        * an account whose normalized email is in the configured founder allowlist
          (``STATUTEPROOF_ADMIN_EMAILS``).

        A normal self-registered customer resolves to their OWN org (never the
        GLOBAL scope) and is not in the allowlist, so this is False for them even
        though RBAC calls them ``owner`` of their org-of-one. That is why the admin
        panel layers this identity check on top of the ``plan.admin`` role gate:
        being an org ``owner`` is not enough to reach it. Never raises — an
        unresolved / malformed identity is never admin.
        """
        try:
            if self._caller_is_operator(user):
                return True
            email = user.get("email") if isinstance(user, dict) else None
            if not email:
                return False
            return normalize_email(email) in _admin_email_allowlist()
        except Exception:  # noqa: BLE001 — an unresolved identity is never admin
            return False

    def _admin_guard(self, user: dict, *, resource_id: str = "") -> bool:
        """Founder-only gate for the admin panel. Returns True only for the founder.

        Layered, and audited on BOTH outcomes so an admin action is never silent:

        1. Positive founder/operator identity (``_caller_is_admin``). A non-founder
           authenticated account — an ordinary customer, who is ``owner`` of its
           own org-of-one and would otherwise PASS the ``plan.admin`` role check —
           is stopped HERE, before any target lookup, with a clean, generic 403
           and an audited denial. Because it never reaches a target, it can never
           act as an existence oracle for another account.
        2. The fail-closed RBAC role gate on the owner-only ``plan.admin`` action
           (``_rbac_guard`` with ``fail_closed=True``), which also writes the
           allow/deny decision to the immutable access log and, on an RBAC
           plumbing error, DENIES rather than granting an entitlement.
        """
        if not self._caller_is_admin(user):
            rbac_runtime.log_sensitive_action(
                user,
                rbac_runtime.PLAN_ADMIN,
                result=rbac_runtime.RESULT_DENY,
                resource_type="plan",
                resource_id=str(resource_id or ""),
            )
            self._send_json({"ok": False, "message": "Not available."}, 403)
            return False
        return self._rbac_guard(
            user,
            rbac_runtime.PLAN_ADMIN,
            resource_type="plan",
            resource_id=str(resource_id or ""),
            fail_closed=True,
        )

    def _canonical_record_is_own_custom(self, user: dict, record_id: str) -> bool:
        """True when a canonical record's source is a CUSTOM source owned by the
        caller — the only non-operator case where a review decision affects solely
        the caller's own tenant (so it may bypass the operator gate). Resolves the
        record via the SAME loader the write uses. Never raises; on failure returns
        False (falls through to the operator requirement)."""
        rid = str(record_id or "").strip()
        if not rid:
            return False
        try:
            from app.evidence_records import load_evidence_record
            from app.tenancy import is_custom_source, custom_source_owner, same_owner

            record, _path = load_evidence_record(rid)
        except Exception:  # noqa: BLE001
            return False
        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        sid = str(source.get("source_id") or "").strip()
        if not sid or not is_custom_source(sid):
            return False
        user_id = user.get("id") if isinstance(user, dict) else None
        return same_owner(custom_source_owner(sid), user_id)

    def _base_url(self) -> str:
        host = self.headers.get("Host", "localhost:5001")
        scheme = "https" if not host.startswith("localhost") and not host.startswith("127.") else "http"
        return f"{scheme}://{host}"

    def _public_base_url(self) -> str:
        """Origin for links embedded in outbound EMAIL (password reset, email
        verification). Security-sensitive: the request ``Host`` header is
        attacker-controllable, so a poisoned Host would let an attacker mint a
        password-reset link pointing at a hostile domain and harvest the victim's
        single-use token (account takeover). Prefer an explicitly configured
        public origin (STATUTEPROOF_PUBLIC_BASE_URL); only fall back to the
        request Host for local/dev where none is set. In production the reverse
        proxy also host-scopes the site, so this is defence in depth that holds
        even if the API is ever exposed directly (run.py documents --host 0.0.0.0)."""
        configured = os.environ.get("STATUTEPROOF_PUBLIC_BASE_URL", "").strip().rstrip("/")
        return configured or self._base_url()

    def _disabled_endpoint(self) -> None:
        self._send_json({"ok": False, "message": "This endpoint is not available."}, 403)

    def _handle_health(self) -> None:
        """Return a health payload for uptime monitors and ops dashboards.

        ``ok`` reflects real health: it is False (and the response is HTTP 503)
        when the database is unreachable OR the last monitoring run is stale
        beyond 2x the watch interval. Uptime monitors that key on HTTP status
        therefore see failure; the dashboard (which reads ``ok`` from the JSON
        body regardless of status) shows "degraded". Only the tail of the trail
        is read, and at most twice per request (once for the last-run/changed
        figures, once for the proxy-verified fresh-alert count — never once per
        source), so an unauthenticated probe cannot force an unbounded file scan
        or a scan that grows with the source count.
        """
        import json as _json_mod
        from datetime import datetime, timezone

        from app.config import BASE_DIR as _BASE_DIR, WATCH_INTERVAL_MINUTES as _WATCH_MIN
        from app.sources import (
            get_enabled_sources,
            latest_run_status_map,
            proxy_remediation_verified,
            proxy_unblocked_remediation,
        )

        now = datetime.now(timezone.utc)
        now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Count active (enabled) sources — fast; reads sources.json once.
        # DH-5: also expose the FRESH-ALERT-ELIGIBLE count so the landing can
        # disclose it alongside "configured". The enabled count (all modes) is
        # larger than the count that actually produces alerts; showing only the
        # bigger number reads as inflated coverage.
        try:
            enabled = get_enabled_sources()
            active_count = len(enabled)
            # Mirrors pipeline._source_may_auto_alert, EXCEPT the
            # proxy-remediation branch uses the VERIFIED variant: a
            # proxy-routed remediation source is only counted after a
            # successful production run is recorded (config alone is not
            # evidence — see sources.proxy_remediation_verified). The trail
            # tail is read and parsed ONCE per request and reused for every
            # source: this endpoint is unauthenticated, so a per-source read
            # would let one anonymous probe force N bounded scans.
            # Skip the trail read entirely when no source is proxy-routed
            # (the predicate is pure config — no I/O).
            _status_map = (
                latest_run_status_map()
                if any(proxy_unblocked_remediation(s) for s in enabled)
                else {}
            )
            fresh_alert_count = sum(
                1 for s in enabled
                if (s.get("monitoring_mode") == "fresh_alert" and s.get("alert_eligible") is True)
                or proxy_remediation_verified(s, status_map=_status_map)
            )
        except Exception:
            active_count = -1
            fresh_alert_count = -1

        # Read only the tail of source_runs.jsonl for the last run timestamp and a
        # recent CHANGED count. Appends are chronological, so the newest timestamp
        # is in the tail. Uses BASE_DIR so a STATUTEPROOF_BASE_DIR override reads
        # the same tree the rest of the app writes.
        last_run_at: str = ""
        recent_changed_count = 0
        runs_file = _BASE_DIR / "data" / "source_runs" / "source_runs.jsonl"
        _TAIL_BYTES = 262_144
        try:
            if runs_file.exists():
                size = runs_file.stat().st_size
                with runs_file.open("rb") as fh:
                    if size > _TAIL_BYTES:
                        fh.seek(size - _TAIL_BYTES)
                        fh.readline()  # discard the partial first line after the seek
                    for raw in fh:
                        line = raw.decode("utf-8", "replace").strip()
                        if not line:
                            continue
                        try:
                            rec = _json_mod.loads(line)
                        except _json_mod.JSONDecodeError:
                            continue
                        ts = rec.get("timestamp_utc") or rec.get("run_at") or ""
                        if ts > last_run_at:
                            last_run_at = ts
                        if rec.get("change_status") == "CHANGED":
                            recent_changed_count += 1
        except Exception:
            pass

        db_status = "connected"
        try:
            import sqlite3 as _sqlite3
            from app.config import DB_PATH as _DB_PATH
            _c = _sqlite3.connect(_DB_PATH, check_same_thread=False)
            _c.execute("SELECT 1").fetchone()
            _c.close()
        except Exception:
            db_status = "unavailable"

        # Staleness: a recorded last run older than 2x the watch interval means the
        # monitor has stopped producing runs. No run yet (fresh deploy) is not
        # treated as stale — absence of data is not a failure signal here.
        stale = False
        if last_run_at:
            try:
                parsed = datetime.fromisoformat(last_run_at.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                age_min = (now - parsed).total_seconds() / 60.0
                stale = age_min > (2 * max(1, int(_WATCH_MIN)))
            except (ValueError, TypeError):
                stale = False

        ok = db_status == "connected" and not stale
        self._send_json(
            {
                "ok": ok,
                "version": "1.0",
                "db": db_status,
                "stale": stale,
                "sources_active": active_count,
                "sources_fresh_alert": fresh_alert_count,
                "last_run_at": last_run_at or None,
                "changed_count": recent_changed_count,
                "timestamp_utc": now_iso,
            },
            200 if ok else 503,
        )







    def _truncate(self, value, limit: int) -> str:
        return str(value or "").strip()[:limit]

    def _redirect(
        self,
        location: str,
        *,
        status: int = 302,
        extra_headers: list[tuple[str, str]] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Location", location)
        for k, v in _cors_headers(self.headers.get("Origin")).items():
            self.send_header(k, v)
        for k, v in _SECURITY_HEADERS.items():
            self.send_header(k, v)
        for k, v in extra_headers or []:
            self.send_header(k, v)
        self.end_headers()

    # ── CORS preflight ─────────────────────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in _cors_headers(self.headers.get("Origin")).items():
            self.send_header(k, v)
        for k, v in _SECURITY_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    # ── GET /api/settings/telegram ─────────────────────────────────────────────

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/auth/me":
            self._handle_auth_me()
        elif path == "/api/auth/verify-email":
            self._handle_auth_verify_email()
        elif path == "/api/auth/google/status":
            self._handle_auth_google_status()
        elif path == "/api/auth/google/start":
            self._handle_auth_google_start()
        elif path == "/api/auth/google/callback":
            self._handle_auth_google_callback()
        elif path == "/api/profile":
            self._handle_profile_get()
        elif path == "/api/account/export":
            self._handle_account_export()
        elif path == "/api/telegram/pair/status":
            self._handle_telegram_pair_status()
        elif path == "/api/delivery/logs":
            self._handle_delivery_logs()
        elif path == "/api/delivery/preview":
            self._handle_delivery_preview()
        elif path == "/api/delivery/email-status":
            self._handle_delivery_email_status()
        elif path == "/api/sources/timeline":
            self._handle_source_timeline_get()
        elif path == "/api/sources/summary":
            self._handle_sources_summary()
        elif path == "/api/sources/status":
            self._handle_sources_status()
        elif path == "/api/custom-sources":
            self._handle_custom_sources_list()
        elif path == "/api/evidence":
            self._handle_evidence_list()
        elif path == "/api/evidence/diff":
            self._handle_evidence_diff_get()
        elif path == "/api/evidence/review":
            self._handle_evidence_review_get()
        elif path == "/api/evidence/review-history":
            self._handle_evidence_review_history_get()
        elif path == "/api/evidence/export":
            self._handle_evidence_export_get()
        elif path == "/api/evidence/export-download":
            self._handle_evidence_export_download()
        elif path == "/api/reviews/queue":
            self._handle_reviews_queue_get()
        elif path == "/api/canonical-evidence":
            self._handle_canonical_evidence_get()
        elif path == "/api/audit-log":
            self._handle_audit_log_get()
        elif path == "/api/briefs":
            self._handle_briefs_list()
        elif path == "/api/plan":
            self._handle_plan_get()
        elif path == "/api/admin/accounts":
            self._handle_admin_accounts()
        elif path == "/api/alerts/action-log":
            self._handle_alert_action_log_get()
        elif path == "/api/alerts/checklist":
            self._handle_alert_checklist_get()
        elif path == "/api/alerts/redline":
            self._handle_alert_redline_get()
        elif path == "/api/alerts/decisions":
            self._handle_alert_decisions_get()
        elif path == "/api/settings/telegram":
            self._disabled_endpoint()
        elif path == "/api/reports/monthly-assurance":
            self._handle_monthly_assurance_report()
        elif path == "/api/reports/coverage-certificate":
            self._handle_coverage_certificate()
        elif path == "/api/calendar/effective-dates":
            self._handle_effective_dates_calendar()
        elif path == "/api/digest/assurance-preview":
            self._handle_assurance_digest_preview()
        elif path == "/api/verify-spec":
            self._handle_verify_spec()
        elif path == "/api/evidence-room/shares":
            self._handle_evidence_room_shares_list()
        elif path.startswith("/api/room/"):
            # Public Auditor Evidence Room — the token is the path segment.
            self._handle_room_view(path[len("/api/room/"):])
        elif path in ("/api/health", "/api/"):
            self._handle_health()
        else:
            self._send_json({"error": "not found"}, 404)

    def do_PUT(self):
        path = urlparse(self.path).path
        if path == "/api/profile":
            self._handle_profile_update()
        else:
            self._send_json({"error": "not found"}, 404)

    # ── POST endpoints ─────────────────────────────────────────────────────────

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/auth/register":
            self._handle_auth_register()
        elif path == "/api/auth/login":
            self._handle_auth_login()
        elif path == "/api/auth/logout":
            self._handle_auth_logout()
        elif path == "/api/auth/resend-verification":
            self._handle_auth_resend_verification()
        elif path == "/api/auth/forgot-password":
            self._handle_auth_forgot_password()
        elif path == "/api/auth/reset-password":
            self._handle_auth_reset_password()
        elif path == "/api/plan":
            self._handle_plan_set()
        elif path == "/api/admin/activate-plan":
            self._handle_admin_activate_plan()
        elif path == "/api/stripe/webhook":
            self._handle_stripe_webhook()
        elif path == "/api/telegram/pair/generate":
            self._handle_telegram_pair_generate()
        elif path == "/api/telegram/pair/unlink":
            self._handle_telegram_pair_unlink()
        elif path == "/api/telegram/test":
            self._handle_telegram_account_test()
        elif path == "/api/delivery/test-brief":
            self._handle_delivery_test_brief()
        elif path == "/api/delivery/send-preview-alert":
            self._handle_delivery_send_preview_alert()
        elif path == "/api/delivery/email-test-mode":
            self._handle_delivery_email_test_mode()
        elif path == "/api/delivery/email-config-check":
            self._handle_delivery_email_config_check()
        elif path == "/api/evidence/assess":
            self._handle_evidence_assess()
        elif path == "/api/evidence/export":
            self._handle_evidence_export_post()
        elif path == "/api/settings/telegram":
            self._disabled_endpoint()
        elif path == "/api/settings/telegram/test":
            self._disabled_endpoint()
        elif path == "/api/contact":
            self._handle_contact()
        elif path == "/api/source-test":
            self._handle_source_test()
        elif path == "/api/custom-sources/discover":
            self._handle_custom_source_discover()
        elif path == "/api/custom-sources/test":
            self._handle_custom_source_test()
        elif path == "/api/custom-sources":
            self._handle_custom_sources_add()
        elif path == "/api/canonical-evidence/review":
            self._handle_canonical_evidence_review_action()
        elif path == "/api/audit/vault":
            self._handle_audit_vault()
        elif path == "/api/evidence/pack":
            self._handle_evidence_pack()
        elif path == "/api/reports/regulator-binder":
            self._handle_regulator_binder()
        elif path == "/api/change-register/export":
            self._handle_change_register_export()
        elif path == "/api/alerts/action-log":
            self._handle_alert_action_log_post()
        elif path == "/api/alerts/checklist":
            self._handle_alert_checklist_add()
        elif path == "/api/alerts/checklist/update":
            self._handle_alert_checklist_update()
        elif path == "/api/alerts/decisions":
            self._handle_alert_decisions_post()
        elif path == "/api/briefs/generate":
            self._handle_briefs_generate()
        elif path == "/api/verify":
            self._handle_public_verify()
        elif path == "/api/evidence-room/shares":
            self._handle_evidence_room_share_create()
        elif path == "/api/evidence-room/shares/revoke":
            self._handle_evidence_room_share_revoke()
        # NOTE: deliberately NO route of any kind under /api/room/ here — the
        # public room is READ-ONLY by construction; a POST to it falls through
        # to the 404 below (asserted by tests/test_evidence_room.py).
        else:
            self._send_json({"error": "not found"}, 404)














    def _handle_briefs_list(self) -> None:
        """GET /api/briefs — returns alert queue entries from data/alert_queue/*.json."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_BRIEFS_LIST_LIMITER, "briefs_list"):
            return
        try:
            params = parse_qs(urlparse(self.path).query)
            market = str((params.get("market") or ["AE"])[0]).upper().strip() or "AE"
            limit_raw = (params.get("limit") or ["50"])[0]
            try:
                limit = max(1, min(int(limit_raw), 200))
            except (TypeError, ValueError):
                limit = 50

            import glob as _glob
            alert_dir = BASE_DIR / "data" / "alert_queue"
            # Tenancy: never surface a brief for another tenant's private custom
            # source (source_id + run_id + internal notes).
            denied_source_ids = self._denied_custom_source_ids(user)
            briefs: list[dict] = []
            if alert_dir.exists():
                for fpath in _glob.glob(str(alert_dir / "*.json")):
                    try:
                        with open(fpath, encoding="utf-8") as fh:
                            rec = json.load(fh)
                    except Exception:
                        continue
                    source_id = str(rec.get("source_id") or "")
                    if source_id.strip() in denied_source_ids:
                        continue
                    if not source_id.startswith(market + "-") and market != "ALL":
                        continue
                    briefs.append({
                        "alert_id": os.path.basename(fpath).removesuffix(".json"),
                        "source_id": source_id,
                        "run_id": rec.get("run_id"),
                        "change_status": rec.get("change_status"),
                        "status": rec.get("status"),
                        "human_reviewed": bool(rec.get("human_reviewed")),
                        "delivery_approved": bool(rec.get("delivery_approved")),
                        "queued_at": rec.get("queued_at"),
                        "run_at": rec.get("run_at"),
                        "normalized_hash": rec.get("normalized_hash"),
                        "notes": rec.get("notes") or "",
                        "reviewer": rec.get("reviewer") or "",
                        "reviewed_at": rec.get("reviewed_at") or "",
                        "evidence_record_id": rec.get("evidence_record_id") or "",
                    })

            briefs.sort(key=lambda b: b.get("queued_at") or "", reverse=True)
            self._send_json({
                "ok": True,
                "market": market,
                "briefs": briefs[:limit],
                "total": len(briefs),
                "disclaimer": "Not legal advice. For monitoring information only.",
            })
        except Exception as exc:
            logger.error("briefs list failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_briefs_generate(self) -> None:
        """POST /api/briefs/generate — generate a compliance brief for a source run.

        Body: {"source_id": "AE-adgm-fsra-guidance-policy", "run_id": "optional"}
        Response: {"ok": true, "brief_markdown": "...", "brief_id": "...",
                   "source_name": "...", "risk_level": "...", "summary": "..."}
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_BRIEFS_GENERATE_LIMITER, "briefs_generate"):
            return

        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return

        source_id = self._truncate(body.get("source_id"), 200)
        run_id = self._truncate(body.get("run_id"), 200) or None

        if not source_id:
            self._send_json({"ok": False, "message": "source_id is required."}, 400)
            return

        # Sanitize source_id — strip any path traversal characters before
        # it is used as a directory component on disk.
        import re as _re
        if not _re.match(r'^[\w\-\.]+$', source_id):
            self._send_json({"ok": False, "message": "Invalid source_id format."}, 400)
            return

        # Tenancy (IDOR): the caller supplies source_id directly. A brief exposes
        # the source name, official URL and diff-derived summary, so a custom
        # source owned by another tenant must never be generatable here. Official
        # / shared sources — and unknown ids — fall through to the normal path.
        if not self._source_visible_to(user, source_id):
            self._send_json({"ok": False, "message": "That source is not in your scope."}, 403)
            return

        # Entitlement: this endpoint REBUILDS the paid official-source payload on
        # demand (executive summary, business action, official URL — from the
        # run's diff artifact), so leaving it ungated re-opened the boundary the
        # preview redaction and the redline/diff 402 close. source_ids are
        # enumerable via /api/sources/status and "Monitoring Briefs" is an
        # ungated dashboard page. Same flag, same eligibility helper as delivery;
        # own custom sources stay generatable, unclassifiable ids fail CLOSED.
        if _official_alert_blocked_by_plan(int(user["id"]), source_id):
            self._send_json({
                "ok": False,
                "message": "Official-source briefs require an active plan.",
                "reason": "plan_required",
            }, 402)
            return

        try:
            import json as _json
            from datetime import datetime, timezone
            from pathlib import Path

            from app.config import ENABLE_AI_ANALYSIS

            # Locate the run record.
            run_record: dict | None = None
            source_runs_file = BASE_DIR / "data" / "source_runs" / "source_runs.jsonl"

            if run_id:
                if source_runs_file.exists():
                    with source_runs_file.open(encoding="utf-8") as fh:
                        for line in fh:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                rec = _json.loads(line)
                            except _json.JSONDecodeError:
                                continue
                            if rec.get("source_id") == source_id and rec.get("run_id") == run_id:
                                run_record = rec
                                break
            else:
                from app.source_runs import changed_runs
                rows = changed_runs(limit=200)
                for rec in rows:
                    if rec.get("source_id") == source_id:
                        run_record = rec
                        break

            if not run_record:
                msg = (
                    f"No run record found for source_id={source_id!r} run_id={run_id!r}."
                    if run_id
                    else f"No CHANGED run record found for source_id={source_id!r}."
                )
                self._send_json({"ok": False, "message": msg}, 404)
                return

            source_name = str(run_record.get("source_name") or source_id)
            official_url = str(run_record.get("official_url") or run_record.get("final_url") or "")
            actual_run_id = str(run_record.get("run_id") or "")
            change_status = str(run_record.get("change_status") or "")
            timestamp_utc = str(run_record.get("timestamp_utc") or "")

            # Build change text from diff artifact if available.
            change_text = ""
            diff_artifact: dict = {}
            diff_json_path = run_record.get("diff_json_path") or run_record.get("diff_path")
            if diff_json_path:
                diff_path = Path(diff_json_path) if Path(diff_json_path).is_absolute() else BASE_DIR / diff_json_path
                if diff_path.exists():
                    try:
                        diff_artifact = _json.loads(diff_path.read_text(encoding="utf-8"))
                        added = diff_artifact.get("added_chunks") or diff_artifact.get("added") or []
                        removed = diff_artifact.get("removed_chunks") or diff_artifact.get("removed") or []
                        changed_chunks = diff_artifact.get("changed_chunks") or diff_artifact.get("modified") or []
                        parts: list[str] = []
                        parts.extend(str(c) for c in added[:5] if c)
                        for ch in (changed_chunks[:3] if isinstance(changed_chunks, list) else []):
                            if isinstance(ch, dict):
                                parts.extend(str(b) for b in (ch.get("before") or [])[:2] if b)
                                parts.extend(str(a) for a in (ch.get("after") or [])[:2] if a)
                            else:
                                parts.append(str(ch))
                        parts.extend(str(c) for c in removed[:3] if c)
                        change_text = "\n\n".join(parts)
                    except Exception as exc:
                        logger.warning("briefs_generate: diff read failed: %s", exc)

            if not change_text:
                snap_path_rel = run_record.get("snapshot_normalized_path") or run_record.get("snapshot_raw_path")
                if snap_path_rel:
                    snap_path = Path(snap_path_rel) if Path(snap_path_rel).is_absolute() else BASE_DIR / snap_path_rel
                    if snap_path.exists():
                        try:
                            change_text = snap_path.read_text(encoding="utf-8")[:6000]
                        except Exception as exc:
                            logger.warning("briefs_generate: snapshot read failed: %s", exc)

            metadata = {
                "source_name": source_name,
                "url": official_url,
                "source_id": source_id,
                "jurisdiction": run_record.get("jurisdiction") or run_record.get("market", ""),
                "category": run_record.get("category", ""),
                "change_status": change_status,
                "extraction_quality": run_record.get("extraction_quality", ""),
                "limitations_notes": run_record.get("limitations_notes", ""),
                "output_language": "en",
            }

            brief_data: dict = {}
            method_used = "rule-based"

            if ENABLE_AI_ANALYSIS and change_text and change_text.strip():
                try:
                    from app.ai_brief import generate_ai_brief
                    brief_data = generate_ai_brief(change_text, metadata)
                    if not brief_data.get("fallback_used"):
                        method_used = "ai"
                except Exception as exc:
                    logger.warning("briefs_generate: AI failed: %s", exc)

            if not brief_data:
                try:
                    from app.alert_drafts import (
                        classify_change_type, classify_risk,
                        affected_entities_for, recommended_action_for,
                    )
                    proof_block: dict = {}
                    proof_json_path = run_record.get("proof_block_path") or run_record.get("proof_json_path")
                    if proof_json_path:
                        proof_path = Path(proof_json_path) if Path(proof_json_path).is_absolute() else BASE_DIR / proof_json_path
                        if proof_path.exists():
                            try:
                                proof_block = _json.loads(proof_path.read_text(encoding="utf-8"))
                            except Exception:
                                pass
                    change_type = classify_change_type(run_record, diff_artifact)
                    risk_lv, risk_rat, conf = classify_risk(run_record, diff_artifact, proof_block, change_type)
                    affected = affected_entities_for(run_record, change_type)
                    action = recommended_action_for(run_record, change_type, risk_lv)
                    brief_data = {
                        "risk_level": risk_lv,
                        "executive_summary": (
                            f"StatuteProof detected a change on {source_name}. "
                            f"Change type: {change_type}. {risk_rat}"
                        ),
                        "business_action_required": action,
                        "affected_entities": [affected],
                        "change_type": change_type,
                        "confidence": conf,
                        "reason": risk_rat,
                        "ai_used": False,
                        "fallback_used": True,
                    }
                except Exception as exc:
                    logger.warning("briefs_generate: rule-based failed: %s", exc)
                    brief_data = {
                        "risk_level": "REVIEW",
                        "executive_summary": f"Change detected on {source_name}. Manual review required.",
                        "business_action_required": "Review the detected change against internal compliance controls.",
                        "confidence": "LOW",
                        "ai_used": False,
                        "fallback_used": True,
                    }

            risk_level = str(brief_data.get("risk_level") or "REVIEW").upper()
            exec_summary = str(brief_data.get("executive_summary") or "")
            action_text = str(brief_data.get("business_action_required") or "")
            change_type_val = str(brief_data.get("change_type") or "")
            confidence_val = str(brief_data.get("confidence") or "")
            affected_raw = brief_data.get("affected_entities", [])
            specific_obligation = str(brief_data.get("specific_obligation") or "")

            # Legal-safety guard: exec_summary / action_text are AI- or rule-
            # generated free text (generate_ai_brief) rendered into both the
            # persisted brief and the JSON response. This is the one AI-text
            # render path that skipped the shared forbidden-claims pass. Mirror
            # alert_content SF-1: scrub any field carrying a banned claim (a
            # hallucination or a prompt-injected instruction from an adversarial
            # source) rather than silently passing it through. Replace the whole
            # field with a labeled redaction so the reader knows content was
            # withheld and the forbidden text never reaches disk or the client.
            from app.legal_safety import find_forbidden_claims

            _WITHHELD = "(withheld: content contained a prohibited compliance claim)"
            if exec_summary and find_forbidden_claims(exec_summary):
                logger.warning("briefs_generate: forbidden claim scrubbed from executive_summary")
                exec_summary = _WITHHELD
            if action_text and find_forbidden_claims(action_text):
                logger.warning("briefs_generate: forbidden claim scrubbed from business_action_required")
                action_text = _WITHHELD
            # specific_obligation and affected_entities are ALSO AI-generated
            # free text (generate_ai_brief) rendered into brief_markdown, which
            # is persisted to disk and returned in the JSON response. Screen
            # them through the same forbidden-claims pass so a hallucinated or
            # prompt-injected banned claim cannot ride either render surface.
            if specific_obligation and find_forbidden_claims(specific_obligation):
                logger.warning("briefs_generate: forbidden claim scrubbed from specific_obligation")
                specific_obligation = _WITHHELD
            if isinstance(affected_raw, list) and affected_raw:
                scrubbed_affected = []
                for entity in affected_raw:
                    entity_str = str(entity)
                    if find_forbidden_claims(entity_str):
                        logger.warning("briefs_generate: forbidden claim scrubbed from affected_entities item")
                        scrubbed_affected.append(_WITHHELD)
                    else:
                        scrubbed_affected.append(entity_str)
                affected_raw = scrubbed_affected

            # Build brief markdown.
            ts_now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            brief_id = f"brief-{source_id}-{ts_now}"

            brief_lines = [
                "# StatuteProof — Internal Brief",
                "",
                "**INTERNAL — NOT CUSTOMER DELIVERY**",
                "",
                f"Generated: {datetime.now(timezone.utc).isoformat()}",
                "",
                "## Source",
                "",
                f"- Source ID: {source_id}",
                f"- Source name: {source_name}",
                f"- Run ID: {actual_run_id}",
                f"- Timestamp: {timestamp_utc}",
                f"- URL: {official_url}",
                f"- Change status: {change_status}",
                "",
                "## Risk Assessment",
                "",
                f"- Risk level: **{risk_level}**",
                f"- Confidence: {confidence_val}",
                f"- Method: {method_used}",
                f"- Change type: {change_type_val or 'unknown'}",
                "",
                "## Executive Summary",
                "",
                exec_summary or "(not available)",
                "",
                "## Business Action Required",
                "",
                action_text or "(not available)",
                "",
            ]
            if specific_obligation:
                brief_lines.extend(["## Specific Obligation", "", specific_obligation, ""])
            if isinstance(affected_raw, list) and affected_raw:
                brief_lines.extend(["## Affected Entities", "", "\n".join(f"- {a}" for a in affected_raw), ""])
            brief_lines.extend([
                "## Disclaimer",
                "",
                (
                    "Monitoring intelligence only. Not legal advice. Not customer delivery. "
                    "Source limitations and evidence records must be reviewed before any external use."
                ),
                "",
            ])
            brief_markdown = "\n".join(brief_lines)

            # Save brief to disk (non-fatal).
            try:
                save_dir = BASE_DIR / "data" / "internal_briefs" / source_id
                save_dir.mkdir(parents=True, exist_ok=True)
                save_path = save_dir / f"{ts_now}_brief.md"
                save_path.write_text(brief_markdown, encoding="utf-8")
                logger.info("briefs_generate: saved to %s", save_path)
            except Exception as exc:
                logger.warning("briefs_generate: save failed: %s", exc)

            self._send_json({
                "ok": True,
                "brief_id": brief_id,
                "brief_markdown": brief_markdown,
                "source_name": source_name,
                "source_id": source_id,
                "run_id": actual_run_id,
                "risk_level": risk_level,
                "confidence": confidence_val,
                "change_type": change_type_val,
                "method_used": method_used,
                "summary": exec_summary[:300] if exec_summary else "",
                "recommended_action": action_text,
                "disclaimer": "Monitoring intelligence only. Not legal advice.",
            })

        except Exception as exc:
            logger.error("briefs_generate failed: %s", type(exc).__name__, exc_info=True)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_save(self) -> None:
        body = self._read_json()
        try:
            _ts.save(
                enabled=bool(body.get("enabled", False)),
                chat_id=str(body.get("chat_id", "")),
                bot_token=body.get("bot_token") or None,
            )
            self._send_json(_ts.load())
        except Exception as exc:
            logger.error("Failed to save Telegram settings: %s", exc)
            self._send_json({"error": "Не удалось сохранить настройки."}, 500)

    def _handle_test(self) -> None:
        """Send a test message via Telegram. Token stays on server."""
        token   = _ts.get_token()
        chat_id = _ts.load()["chat_id"]

        if not token or not chat_id:
            self._send_json(
                {"ok": False, "message": "Токен или Chat ID не настроены."},
                400,
            )
            return

        try:
            resp = _req.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id":    chat_id,
                    "text":       "✅ *StatuteProof* — test connection successful. Alerts will be delivered to this chat.",
                    "parse_mode": "Markdown",
                },
                timeout=_TELEGRAM_TIMEOUT_S,
            )
            data = resp.json()
            if data.get("ok"):
                self._send_json({"ok": True, "message": "Test alert sent successfully."})
            else:
                description = data.get("description", "Telegram API error")
                self._send_json({"ok": False, "message": description}, 502)

        except _req.Timeout:
            self._send_json({"ok": False, "message": f"Timeout — Telegram did not respond within {_TELEGRAM_TIMEOUT_S}s."}, 502)
        except _req.ConnectionError:
            self._send_json({"ok": False, "message": "No connection to Telegram."}, 502)
        except Exception as exc:
            logger.error("Telegram test failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)


    def _handle_contact(self) -> None:
        """Forward a demo/contact request to the admin Telegram chat."""
        if self._rate_limited(_CONTACT_LIMITER, "contact"):
            return

        body     = self._read_json()
        name     = self._truncate(body.get("name",     ""), 120)
        email    = self._truncate(body.get("email",    ""), 200)
        company  = self._truncate(body.get("company",  ""), 160)
        industry = self._truncate(body.get("industry", ""), 160)
        message  = self._truncate(body.get("message",  ""), 1000)
        markets  = self._truncate(body.get("markets",  ""), 500)
        watchlist = body.get("watchlistContext")
        safe_watchlist = None
        if isinstance(watchlist, dict):
            safe_watchlist = {}
            for key in ("companyType", "markets", "topics", "delivery"):
                value = watchlist.get(key)
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value if v)
                if value:
                    safe_watchlist[key] = self._truncate(value, 500)

        if not name or not email:
            self._send_json({"ok": False, "message": "Name and email are required."}, 400)
            return

        queued_body = dict(body)
        queued_body.update({
            "name": name,
            "email": email,
            "company": company,
            "industry": industry,
            "message": message,
            "markets": markets,
        })
        if safe_watchlist is not None:
            queued_body["watchlistContext"] = safe_watchlist
        queued = self._queue_contact_request(queued_body)

        lines = [
            "New StatuteProof demo request",
            "",
            f"Name: {name}",
            f"Email: {email}",
        ]
        if company:
            lines.append(f"Company: {company}")
        if industry:
            lines.append(f"Industry: {industry}")
        if markets:
            lines.append(f"Markets: {markets}")
        if isinstance(safe_watchlist, dict):
            lines.append("")
            lines.append("Watchlist context:")
            for label, value in (
                ("Company type", safe_watchlist.get("companyType")),
                ("Markets", safe_watchlist.get("markets")),
                ("Topics", safe_watchlist.get("topics")),
                ("Delivery", safe_watchlist.get("delivery")),
            ):
                if value:
                    lines.append(f"{label}: {value}")
        if message:
            lines += ["", f"Target markets / notes:\n{message}"]
        lines += ["", "Source: Website contact form"]

        if CONTACT_DELIVERY_DISABLED:
            logger.info("Contact form delivery disabled — queued=%s from=%s", queued, email)
            if queued:
                self._send_json({
                    "ok": True,
                    "queued": True,
                    "delivered": False,
                    "message": "Request received and queued.",
                })
            else:
                self._send_json({"ok": False, "message": "Queue write failed."}, 500)
            return

        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.error("Contact form: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
            if queued:
                self._send_json({"ok": True, "queued": True, "delivered": False})
            else:
                self._send_json({"ok": False, "message": "Delivery not configured on server."}, 500)
            return

        try:
            resp = _req.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id":    TELEGRAM_CHAT_ID,
                    "text":       "\n".join(lines),
                    "disable_web_page_preview": True,
                },
                timeout=_TELEGRAM_TIMEOUT_S,
            )
            data = resp.json()
            if data.get("ok"):
                logger.info("Contact form delivered — from=%s", email)
                self._send_json({"ok": True, "queued": queued, "delivered": True})
            else:
                description = data.get("description", "Telegram API error")
                logger.error("Contact form Telegram error: %s", description)
                if queued:
                    self._send_json({"ok": True, "queued": True, "delivered": False})
                else:
                    self._send_json({"ok": False, "message": description}, 502)
        except _req.Timeout:
            if queued:
                self._send_json({"ok": True, "queued": True, "delivered": False})
            else:
                self._send_json({"ok": False, "message": "Delivery timed out."}, 502)
        except _req.ConnectionError:
            if queued:
                self._send_json({"ok": True, "queued": True, "delivered": False})
            else:
                self._send_json({"ok": False, "message": "No connection to delivery service."}, 502)
        except Exception as exc:
            logger.error("Contact form delivery failed: %s", type(exc).__name__)
            if queued:
                self._send_json({"ok": True, "queued": True, "delivered": False})
            else:
                self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _queue_contact_request(self, body: dict) -> bool:
        """Persist contact submissions before external delivery."""
        try:
            _CONTACT_QUEUE.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "received_at": datetime.now(timezone.utc).isoformat(),
                "body": body,
            }
            with _CONTACT_QUEUE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except Exception as exc:
            logger.error("Contact form queue write failed: %s", type(exc).__name__)
            return False


















def run_server(host: str = "127.0.0.1", port: int = 5001) -> None:
    """Start the threaded HTTP API server. Stops cleanly on Ctrl-C.

    Decision 4 (production readiness sprint): the API process performs NO
    monitoring sweeps. Scheduling is a separate process — run it with
    `python run.py watch --interval N` (see deploy/ for the systemd unit).
    """
    # Decision 2: detect (never heal) trail/index divergence at startup.
    from app.consistency import check_baseline_consistency
    check_baseline_consistency()
    server = ThreadingHTTPServer((host, port), _Handler)
    print(f"StatuteProof API listening on  http://{host}:{port}/api/")
    print(f"Vite dev proxy expects it at  http://localhost:5173/api/ → http://{host}:{port}/api/")
    print("Press Ctrl-C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("\nAPI server stopped.")
