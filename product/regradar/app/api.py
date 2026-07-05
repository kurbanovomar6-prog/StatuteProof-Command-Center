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
    mark_email_verified,
    get_user_by_email,
    google_oauth_authorization_url,
    google_oauth_available,
    link_or_create_google_user,
    make_public_user,
    normalize_email,
    parse_session_cookie,
    require_auth,
    validate_email,
    validate_password,
    verify_password,
)
from app import telegram_settings as _ts
from app.config import (
    BASE_DIR,
    CONTACT_DELIVERY_DISABLED,
    TELEGRAM_BOT_USERNAME,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from app.email_delivery import send_verification_email as _send_verification_email
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
from app.alert_routing import build_routing_preview_for_user, send_preview_alert_to_user
from app.alert_actions import save_action_log_entry, get_action_log

logger = logging.getLogger(__name__)

_TELEGRAM_TIMEOUT_S = 10
_CONTACT_QUEUE = BASE_DIR / "data" / "contact_requests.jsonl"

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


class _RateLimiter:
    """Small in-memory fixed-window limiter for MVP endpoint hardening."""

    def __init__(self, limit: int, window_seconds: int):
        self.limit = int(limit)
        self.window_seconds = int(window_seconds)
        self._hits = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
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
_SOURCE_TEST_LIMITER = _RateLimiter(10, 3600)
_PAIR_GENERATE_LIMITER = _RateLimiter(10, 3600)
_TELEGRAM_TEST_LIMITER = _RateLimiter(5, 3600)
_DELIVERY_TEST_BRIEF_LIMITER = _RateLimiter(5, 3600)
_DELIVERY_SEND_PREVIEW_LIMITER = _RateLimiter(10, 3600)
_BRIEFS_GENERATE_LIMITER = _RateLimiter(20, 3600)


class _Handler(BaseHTTPRequestHandler):

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002  # silence default stderr logging; params required by base class interface
        logger.debug("API %s %s", self.command, self.path)

    # ── helpers ────────────────────────────────────────────────────────────────

    def _send_json(
        self,
        data: dict,
        status: int = 200,
        extra_headers: list[tuple[str, str]] | None = None,
    ) -> None:
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

    _MAX_BODY_BYTES = 524_288  # 512 KB — reasonable for all API payloads

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        if length > self._MAX_BODY_BYTES:
            self._send_json({"ok": False, "message": "Request body too large."}, 413)
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return {}

    def _read_json_strict(self) -> tuple[dict | None, str | None]:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}, None
        if length > self._MAX_BODY_BYTES:
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
        xff = self.headers.get("X-Forwarded-For", "")
        if xff:
            return str(xff.split(",")[0].strip() or "unknown")
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

    def _base_url(self) -> str:
        host = self.headers.get("Host", "localhost:5001")
        scheme = "https" if not host.startswith("localhost") and not host.startswith("127.") else "http"
        return f"{scheme}://{host}"

    def _disabled_endpoint(self) -> None:
        self._send_json({"ok": False, "message": "This endpoint is not available."}, 403)

    def _handle_health(self) -> None:
        """Return a rich health payload for uptime monitors and ops dashboards."""
        import json as _json_mod
        from datetime import datetime, timezone
        from pathlib import Path as _Path

        from app.sources import get_enabled_sources

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Count active (enabled) sources — fast; reads sources.json once.
        try:
            active_count = len(get_enabled_sources())
        except Exception:
            active_count = -1

        # Scan source_runs.jsonl for last run timestamp and CHANGED count.
        # Only reads the file once; stops if we've found what we need.
        last_run_at: str = ""
        changed_count = 0
        runs_file = _Path(__file__).resolve().parent.parent / "data" / "source_runs" / "source_runs.jsonl"
        try:
            if runs_file.exists():
                with runs_file.open(encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
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
                            changed_count += 1
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

        self._send_json(
            {
                "ok": True,
                "version": "1.0",
                "db": db_status,
                "sources_active": active_count,
                "last_run_at": last_run_at or None,
                "changed_count": changed_count,
                "timestamp_utc": now_iso,
            }
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
        elif path == "/api/sources/readiness":
            self._handle_sources_readiness()
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
        elif path == "/api/briefs":
            self._handle_briefs_list()
        elif path == "/api/plan":
            self._handle_plan_get()
        elif path == "/api/alerts/action-log":
            self._handle_alert_action_log_get()
        elif path == "/api/settings/telegram":
            self._disabled_endpoint()
        elif path == "/api/reports/monthly-assurance":
            self._handle_monthly_assurance_report()
        elif path == "/api/email/delivery-status":
            self._handle_email_delivery_status()
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
        elif path == "/api/plan":
            self._handle_plan_set()
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
        elif path == "/api/review/action":
            self._handle_review_action()
        elif path == "/api/canonical-evidence/review":
            self._handle_canonical_evidence_review_action()
        elif path == "/api/audit/vault":
            self._handle_audit_vault()
        elif path == "/api/alerts/action-log":
            self._handle_alert_action_log_post()
        elif path == "/api/briefs/generate":
            self._handle_briefs_generate()
        else:
            self._send_json({"error": "not found"}, 404)

    def _handle_auth_register(self) -> None:
        if self._rate_limited(_REGISTER_LIMITER, "auth_register"):
            return

        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return

        email = normalize_email(body.get("email", ""))
        password = str(body.get("password", ""))
        full_name = body.get("full_name") or body.get("fullName") or body.get("name")
        company_name = str(body.get("company_name", "")).strip()
        industry = str(body.get("industry", "")).strip()
        job_title = str(body.get("job_title", "")).strip()
        company_type = str(body.get("company_type", "")).strip()
        jurisdiction = str(body.get("jurisdiction", "")).strip()

        if not validate_email(email):
            self._send_json({"ok": False, "message": "Enter a valid email address."}, 400)
            return

        password_ok, password_msg = validate_password(password)
        if not password_ok:
            self._send_json({"ok": False, "message": password_msg}, 400)
            return

        try:
            user = create_user(
                email=email,
                password=password,
                full_name=full_name,
                company_name=company_name,
                industry=industry,
                job_title=job_title,
                company_type=company_type,
                jurisdiction=jurisdiction,
            )
            # Generate verification token and send email (non-blocking)
            token = generate_verification_token(int(user["id"]))
            verification_url = f"{self._base_url()}/api/auth/verify-email?token={token}"
            import threading as _threading
            _threading.Thread(
                target=_send_verification_email,
                args=(user["email"], verification_url),
                daemon=True,
            ).start()
            self._send_json(
                {"ok": True, "requires_verification": True, "email": user["email"]},
                201,
            )
        except DuplicateEmailError:
            self._send_json({"ok": False, "message": "Email is already registered."}, 409)
        except Exception as exc:
            logger.error("Auth register failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_auth_login(self) -> None:
        if self._rate_limited(_LOGIN_LIMITER, "auth_login"):
            return

        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return

        email = normalize_email(body.get("email", ""))
        password = str(body.get("password", ""))
        user = get_user_by_email(email) if validate_email(email) else None
        if not user or not user.get("is_active") or not verify_password(password, user.get("password_hash", "")):
            self._send_json({"ok": False, "message": "Invalid email or password."}, 401)
            return

        if not user.get("email_verified"):
            self._send_json(
                {
                    "ok": False,
                    "message": "Please verify your email before signing in. Check your inbox for a verification link.",
                    "requires_verification": True,
                    "email": user.get("email"),
                },
                403,
            )
            return

        try:
            session_id = create_session(int(user["id"]))
            self._send_json(
                {"ok": True, "user": make_public_user(user)},
                200,
                [("Set-Cookie", self._session_cookie_header(session_id))],
            )
        except Exception:
            logger.error("Auth login failed for email_hash=%s", hashlib.sha256(email.encode()).hexdigest()[:12])
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_auth_logout(self) -> None:
        session_id = parse_session_cookie(self.headers.get("Cookie", ""))
        if session_id:
            delete_session(session_id)
        self._send_json(
            {"ok": True},
            200,
            [("Set-Cookie", self._clear_session_cookie_header())],
        )

    def _handle_auth_verify_email(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        token = (qs.get("token") or [""])[0]
        user_id = consume_verification_token(token)
        if user_id is None:
            self._send_json(
                {"ok": False, "message": "Verification link is invalid or has expired. Please request a new one."},
                400,
            )
            return
        mark_email_verified(user_id)
        try:
            session_id = create_session(user_id)
            self._send_json(
                {"ok": True, "verified": True},
                200,
                [("Set-Cookie", self._session_cookie_header(session_id))],
            )
        except Exception:
            logger.error("Email verify session creation failed for user_id=%s", user_id)
            self._send_json(
                {"ok": False, "message": "Verification succeeded but session creation failed. Please sign in."},
                500,
            )

    def _handle_auth_resend_verification(self) -> None:
        if self._rate_limited(_REGISTER_LIMITER, "auth_resend"):
            return
        body, error = self._read_json_strict()
        if error or body is None:
            self._send_json({"ok": False, "message": "Request body with email required."}, 400)
            return
        email = normalize_email(body.get("email", ""))
        if not validate_email(email):
            self._send_json({"ok": False, "message": "Enter a valid email address."}, 400)
            return
        user = get_user_by_email(email)
        if not user:
            # Don't reveal whether email exists
            self._send_json({"ok": True, "message": "If that email is registered, a verification link has been sent."}, 200)
            return
        if user.get("email_verified"):
            self._send_json({"ok": True, "message": "Email is already verified. Please sign in."}, 200)
            return
        token = generate_verification_token(int(user["id"]))
        verification_url = f"{self._base_url()}/api/auth/verify-email?token={token}"
        import threading as _threading
        _threading.Thread(
            target=_send_verification_email,
            args=(user["email"], verification_url),
            daemon=True,
        ).start()
        self._send_json({"ok": True, "message": "Verification email sent. Check your inbox."}, 200)

    def _handle_auth_me(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        self._send_json({"ok": True, "user": make_public_user(user)})

    def _handle_auth_google_status(self) -> None:
        available = google_oauth_available()
        self._send_json(
            {
                "ok": True,
                "available": available,
                "message": (
                    "Google sign-in is configured."
                    if available
                    else "Google sign-in is not configured for this environment."
                ),
            }
        )

    def _handle_auth_google_start(self) -> None:
        if self._rate_limited(_LOGIN_LIMITER, "auth_google_start"):
            return
        if not google_oauth_available():
            self._send_json(
                {
                    "ok": False,
                    "available": False,
                    "message": "Google sign-in is not configured for this environment.",
                },
                503,
            )
            return
        params = parse_qs(urlparse(self.path).query)
        next_path = str((params.get("next") or ["/app"])[0] or "/app")
        try:
            state = create_google_oauth_state(next_path=next_path)
            self._redirect(google_oauth_authorization_url(state))
        except OAuthAccountError as exc:
            self._send_json({"ok": False, "message": "Google sign-in is not available for this account type."}, 503)
        except Exception as exc:
            logger.error("Google OAuth start failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Google sign-in could not be started."}, 500)

    def _handle_auth_google_callback(self) -> None:
        params = parse_qs(urlparse(self.path).query)
        if params.get("error"):
            self._redirect("/login?google=cancelled")
            return
        state = str((params.get("state") or [""])[0] or "").strip()
        code = str((params.get("code") or [""])[0] or "").strip()
        state_record = consume_google_oauth_state(state)
        if not state_record or not code:
            self._redirect("/login?google=failed")
            return
        try:
            claims = exchange_google_oauth_code(code)
            user = link_or_create_google_user(claims)
            if not user.get("is_active"):
                raise OAuthAccountError("Account is not active.")
            session_id = create_session(int(user["id"]))
            self._redirect(
                str(state_record.get("next_path") or "/app"),
                extra_headers=[("Set-Cookie", self._session_cookie_header(session_id))],
            )
        except OAuthAccountError:
            self._redirect("/login?google=failed")
        except Exception as exc:
            logger.error("Google OAuth callback failed: %s", type(exc).__name__)
            self._redirect("/login?google=failed")

    def _handle_profile_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            profile = get_or_create_profile(
                int(user["id"]),
                seed={
                    "company_name": user.get("company_name"),
                    "industry": user.get("industry"),
                },
            )
            self._send_json({"ok": True, "profile": profile})
        except Exception as exc:
            logger.error("Profile load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_profile_update(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return

        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return

        try:
            profile = update_profile(int(user["id"]), body)
            self._send_json({"ok": True, "profile": profile})
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("Profile update failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _telegram_instructions(self, code: str) -> str:
        if TELEGRAM_BOT_USERNAME:
            return f"Send /start {code} to @{TELEGRAM_BOT_USERNAME} in Telegram."
        return f"Send /start {code} to our Telegram bot."

    def _handle_telegram_pair_generate(self) -> None:
        if self._rate_limited(_PAIR_GENERATE_LIMITER, "telegram_pair_generate"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            result = create_pairing_code(int(user["id"]))
            self._send_json({
                "ok": True,
                "code": result["code"],
                "expires_at": result["expires_at"],
                "bot_username": TELEGRAM_BOT_USERNAME or "",
                "instructions": self._telegram_instructions(result["code"]),
            })
        except Exception as exc:
            logger.error("Telegram pair generate failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_telegram_pair_status(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            status = get_pairing_status(int(user["id"]))
            self._send_json({"ok": True, **status})
        except Exception as exc:
            logger.error("Telegram pair status failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_telegram_pair_unlink(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            unlink_telegram(int(user["id"]))
            self._send_json({"ok": True})
        except Exception as exc:
            logger.error("Telegram pair unlink failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_telegram_account_test(self) -> None:
        if self._rate_limited(_TELEGRAM_TEST_LIMITER, "telegram_account_test"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            link = get_telegram_link(int(user["id"]))
            chat_id = link.get("telegram_chat_id")
            if not chat_id:
                self._send_json({
                    "ok": False,
                    "message": "Telegram is not connected. Generate a pairing code first.",
                }, 400)
                return

            ok = send_telegram_message(
                str(chat_id),
                "✅ StatuteProof Telegram test message delivered to your connected account.",
            )
            if ok:
                touch_telegram_test_sent(int(user["id"]))
                self._send_json({"ok": True, "message": "Test message sent to your Telegram."})
            else:
                self._send_json({
                    "ok": False,
                    "message": "Could not send Telegram test message. Check bot configuration.",
                }, 502)
        except Exception as exc:
            logger.error("Account Telegram test failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_test_brief(self) -> None:
        if self._rate_limited(_DELIVERY_TEST_BRIEF_LIMITER, "delivery_test_brief"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            result = send_sample_brief_to_user(int(user["id"]))
            if result.get("ok"):
                self._send_json({
                    "ok": True,
                    "message": result.get("message", "Sample brief sent to your Telegram."),
                    "log_id": result.get("log_id"),
                })
                return

            reason = result.get("reason", "Delivery failed.")
            if reason == "Sample brief already sent today.":
                self._send_json(
                    {"ok": False, "message": reason, "reason": "already_sent_today"},
                    429,
                )
            elif reason == "Telegram not connected.":
                self._send_json(
                    {
                        "ok": False,
                        "message": "Telegram not connected. Pair your account first.",
                        "reason": "no_telegram",
                    },
                    400,
                )
            elif reason == "Telegram alerts are disabled.":
                self._send_json(
                    {
                        "ok": False,
                        "message": "Telegram alerts are disabled. Enable Telegram alerts in Settings.",
                        "reason": "telegram_disabled",
                    },
                    400,
                )
            elif reason == "Onboarding is not complete.":
                self._send_json(
                    {
                        "ok": False,
                        "message": "Complete onboarding before sending a sample brief.",
                        "reason": "onboarding_incomplete",
                    },
                    400,
                )
            else:
                self._send_json(
                    {
                        "ok": False,
                        "message": reason,
                        "reason": "delivery_failed",
                    },
                    502,
                )
        except Exception as exc:
            logger.error("Sample brief delivery failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_logs(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            params = parse_qs(urlparse(self.path).query)
            try:
                limit = int((params.get("limit") or ["20"])[0])
            except (TypeError, ValueError):
                limit = 20
            logs = get_user_delivery_logs(int(user["id"]), limit=max(1, min(limit, 50)))
            self._send_json({"ok": True, "logs": logs})
        except Exception as exc:
            logger.error("Delivery logs load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_preview(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            params = parse_qs(urlparse(self.path).query)
            try:
                days = int((params.get("days") or ["14"])[0])
            except (TypeError, ValueError):
                days = 14
            preview = build_routing_preview_for_user(int(user["id"]), days=max(1, min(days, 60)))
            self._send_json({"ok": True, "preview": preview})
        except Exception as exc:
            logger.error("Delivery preview failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_send_preview_alert(self) -> None:
        if self._rate_limited(_DELIVERY_SEND_PREVIEW_LIMITER, "delivery_send_preview_alert"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return

        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return

        alert_id = str(body.get("alert_id", "")).strip()
        if not re.match(r"^[a-zA-Z0-9_-]{1,200}$", alert_id):
            self._send_json({"ok": False, "message": "Invalid alert_id."}, 400)
            return

        try:
            result = send_preview_alert_to_user(int(user["id"]), alert_id)
            if result.get("ok"):
                self._send_json({
                    "ok": True,
                    "message": result.get("message", "Preview alert sent to your Telegram."),
                    "log_id": result.get("log_id"),
                })
                return

            code = result.get("code")
            payload = {
                "ok": False,
                "message": result.get("reason", "Delivery failed."),
                "reason": code or "delivery_failed",
            }
            if result.get("details"):
                payload["details"] = result["details"]
            if code == "duplicate":
                self._send_json(payload, 409)
            elif code == "not_found":
                self._send_json(payload, 404)
            elif code == "not_ready":
                self._send_json(payload, 400)
            elif code == "telegram_failed":
                self._send_json(payload, 502)
            else:
                self._send_json(payload, 400)
        except Exception as exc:
            logger.error("Preview alert delivery failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_alert_action_log_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        alert_id = str((params.get("alert_id") or [""])[0]).strip()
        if not alert_id:
            self._send_json({"ok": False, "message": "alert_id required."}, 400)
            return
        entries = get_action_log(int(user["id"]), alert_id)
        self._send_json({"ok": True, "entries": entries})

    def _handle_alert_action_log_post(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        alert_id = str(body.get("alert_id", "")).strip()
        decision = str(body.get("decision", "")).strip()
        notes = str(body.get("notes", "")).strip()[:2000]
        reviewer_name = str(body.get("reviewer_name", "")).strip()[:200]
        if not alert_id:
            self._send_json({"ok": False, "message": "alert_id required."}, 400)
            return
        if decision not in ("act", "monitor", "no_action"):
            self._send_json({"ok": False, "message": "decision must be act, monitor, or no_action."}, 400)
            return
        result = save_action_log_entry(int(user["id"]), alert_id, decision, notes, reviewer_name)
        if result is None:
            self._send_json({"ok": False, "message": "Could not save action log entry."}, 500)
            return
        self._send_json({"ok": True, "entry": result}, 201)

    def _handle_delivery_email_test_mode(self) -> None:
        if self._rate_limited(_DELIVERY_TEST_BRIEF_LIMITER, "delivery_email_test_mode"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        recipient = str(body.get("recipient_email") or user.get("email") or "").strip()
        try:
            from datetime import timedelta

            from app.email_delivery import deliver_weekly_brief_test_mode
            from app.weekly_brief import build_weekly_brief

            end = datetime.now(timezone.utc)
            start = end - timedelta(days=7)
            brief = build_weekly_brief(
                client_profile={
                    "client_id": f"user_{int(user['id'])}",
                    "company_name": user.get("company_name") or user.get("email") or "Pilot workspace",
                },
                market="AE",
                start=start,
                end=end,
                alerts=[],
                demo_fixture=False,
            )
            result = deliver_weekly_brief_test_mode(brief, recipient_email=recipient)
            if result.get("ok"):
                self._send_json({
                    "ok": True,
                    "message": "Email test-mode payload written to local outbox. No external email was sent.",
                    **result,
                })
                return
            self._send_json({
                "ok": False,
                "message": result.get("error_message") or "Email test-mode delivery failed.",
                **result,
            }, 400)
        except Exception as exc:
            logger.error("Email test-mode delivery failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_email_status(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.email_delivery import build_email_status_response

            self._send_json(build_email_status_response())
        except Exception as exc:
            logger.error("Email status failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_email_config_check(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.email_delivery import record_email_config_check

            result = record_email_config_check()
            status_code = 200 if result.get("status") != "configuration_required" else 400
            self._send_json(result, status_code)
        except Exception as exc:
            logger.error("Email config check failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_sources_status(self) -> None:
        """
        GET /api/sources/status?market=AE

        Returns live source run status from source_runs.jsonl merged with the
        enabled source list from sources.json.

        Requires session auth (same as all other protected endpoints).
        Returns status counts even when no runs have been recorded yet.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return

        params = parse_qs(urlparse(self.path).query)
        market = str((params.get("market") or ["AE"])[0]).upper().strip() or "AE"

        try:
            from app.source_readiness import load_market_sources
            from app.source_runs import latest_runs
            from app.source_health_timeline import build_source_timeline

            all_sources = load_market_sources(market)
            enabled_sources = [s for s in all_sources if s.get("enabled", False)]

            # latest_runs returns dict keyed by source_id (or url fallback)
            run_map = latest_runs(market)

            sources_out: list[dict] = []
            last_run_at: str | None = None

            for src in enabled_sources:
                source_id = str(src.get("source_id") or src.get("id") or "")
                name = str(src.get("name") or "")

                # Try lookup by source_id first, then by name
                run = run_map.get(source_id) or run_map.get(name)

                if run:
                    change_status = str(run.get("change_status") or "UNKNOWN")
                    run_at = str(run.get("timestamp_utc") or run.get("run_at") or "")
                    access_status = str(run.get("access_status") or "unknown")
                    extraction_quality = str(run.get("extraction_quality") or "UNKNOWN")
                    normalized_hash = str(run.get("normalized_hash") or run.get("content_hash") or "")
                    proof_path = str(run.get("proof_block_path") or "")
                    last_evidence_at = run_at if proof_path else None
                    # Track most recent run timestamp across all sources
                    if run_at and (last_run_at is None or run_at > last_run_at):
                        last_run_at = run_at
                else:
                    change_status = "NOT_RUN"
                    run_at = None
                    access_status = "unknown"
                    extraction_quality = "UNKNOWN"
                    normalized_hash = ""
                    proof_path = ""
                    last_evidence_at = None

                try:
                    timeline_event_count = int(build_source_timeline(source_id, limit=200).get("total_events") or 0)
                except Exception:
                    timeline_event_count = 0

                sources_out.append({
                    "source_id": source_id,
                    "name": name,
                    "category": str(src.get("category") or ""),
                    "url": str(src.get("url") or ""),
                    "status": str(src.get("status") or "active"),
                    "change_status": change_status,
                    "last_run_at": run_at,
                    "last_evidence_at": last_evidence_at,
                    "access_status": access_status,
                    "extraction_quality": extraction_quality,
                    "normalized_hash": normalized_hash,
                    "proof_block_path": proof_path,
                    "timeline_event_count": timeline_event_count,
                    "remediation_reason": str(src.get("remediation_reason") or src.get("notes") or src.get("scraper_notes") or ""),
                })

            # Build summary counts
            summary: dict[str, int] = {}
            for s in sources_out:
                cs = s["change_status"]
                summary[cs] = summary.get(cs, 0) + 1

            self._send_json({
                "ok": True,
                "market": market,
                "sources": sources_out,
                "summary": summary,
                "total_sources": len(sources_out),
                "last_run_at": last_run_at,
                "disclaimer": "Not legal advice. For monitoring information only.",
            })
        except Exception as exc:
            logger.error("sources/status failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_sources_summary(self) -> None:
        """GET /api/sources/summary?market=AE — canonical source counts."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        market = str((params.get("market") or ["AE"])[0]).upper().strip() or "AE"
        try:
            from app.source_summary import build_sources_summary

            self._send_json(build_sources_summary(market))
        except Exception as exc:
            logger.error("sources/summary failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_source_timeline_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        source_id = str((params.get("source_id") or params.get("id") or [""])[0]).strip()
        if not source_id:
            self._send_json({"ok": False, "message": "source_id is required."}, 400)
            return
        try:
            from app.source_health_timeline import build_source_timeline

            try:
                limit = int((params.get("limit") or ["100"])[0])
            except (TypeError, ValueError):
                limit = 100
            timeline = build_source_timeline(source_id, limit=max(1, min(limit, 200)))
            self._send_json(timeline)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("source timeline load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_list(self) -> None:
        """GET /api/evidence — returns source run records from source_runs.jsonl."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            params = parse_qs(urlparse(self.path).query)
            market = str((params.get("market") or ["AE"])[0]).upper().strip() or "AE"
            limit_raw = (params.get("limit") or ["50"])[0]
            try:
                limit = max(1, min(int(limit_raw), 200))
            except (TypeError, ValueError):
                limit = 50

            runs_path = BASE_DIR / "data" / "source_runs" / "source_runs.jsonl"
            records: list[dict] = []
            if runs_path.exists():
                with runs_path.open(encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if str(rec.get("market") or rec.get("jurisdiction") or "").upper() == market:
                            records.append({
                                "run_id": rec.get("run_id"),
                                "evidence_record_id": rec.get("run_id"),
                                "source_id": rec.get("source_id"),
                                "source_name": rec.get("source_name") or rec.get("name"),
                                "official_url": rec.get("official_url") or rec.get("final_url"),
                                "change_status": rec.get("change_status"),
                                "access_status": rec.get("access_status"),
                                "extraction_quality": rec.get("extraction_quality"),
                                "extracted_chars": rec.get("extracted_chars", 0),
                                "normalized_hash": rec.get("normalized_hash"),
                                "raw_hash": rec.get("raw_hash"),
                                "content_hash": rec.get("content_hash") or rec.get("normalized_hash"),
                                "proof_block_path": rec.get("proof_block_path"),
                                "diff_json_path": rec.get("diff_json_path"),
                                "diff_md_path": rec.get("diff_md_path"),
                                "snapshot_normalized_path": rec.get("snapshot_normalized_path"),
                                "timestamp_utc": rec.get("timestamp_utc") or rec.get("run_at"),
                                "category": rec.get("category"),
                                "error": rec.get("error"),
                            })

            records.sort(key=lambda r: r.get("timestamp_utc") or "", reverse=True)
            self._send_json({
                "ok": True,
                "market": market,
                "evidence": records[:limit],
                "total": len(records),
                "disclaimer": "Not legal advice. For monitoring information only.",
            })
        except Exception as exc:
            logger.error("evidence list failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_diff_get(self) -> None:
        """GET /api/evidence/diff?run_id=<run_id> — returns diff.md text for the given run."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        run_id = str((params.get("run_id") or [""])[0]).strip()
        if not run_id:
            self._send_json({"ok": False, "message": "run_id is required."}, 400)
            return
        try:
            runs_path = BASE_DIR / "data" / "source_runs" / "source_runs.jsonl"
            diff_md_path: str | None = None
            diff_json_path: str | None = None
            if runs_path.exists():
                with runs_path.open(encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if rec.get("run_id") == run_id:
                            diff_md_path = rec.get("diff_md_path")
                            diff_json_path = rec.get("diff_json_path")
                            break
            if not diff_md_path and not diff_json_path:
                self._send_json({"ok": False, "message": "No diff available for this run."}, 404)
                return
            candidate = diff_md_path or diff_json_path
            if not candidate:  # guaranteed by the check above; narrows type for Pyright
                self._send_json({"ok": False, "message": "No diff available for this run."}, 404)
                return
            full_path = BASE_DIR / candidate
            if not full_path.exists():
                self._send_json({"ok": False, "message": "Diff file not found on disk."}, 404)
                return
            diff_text = full_path.read_text(encoding="utf-8")
            self._send_json({
                "ok": True,
                "run_id": run_id,
                "diff_text": diff_text,
                "disclaimer": "Monitoring intelligence only. Not legal advice.",
            })
        except Exception as exc:
            logger.error("evidence diff fetch failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_review_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        evidence_id = str((params.get("evidence_record_id") or params.get("run_id") or [""])[0]).strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        try:
            from app.evidence_assessment import latest_assessment_for

            assessment = latest_assessment_for(evidence_id)
            self._send_json({
                "ok": True,
                "evidence_record_id": evidence_id,
                "assessment": assessment,
                "disclaimer": "Monitoring intelligence only. Not legal advice.",
            })
        except Exception as exc:
            logger.error("evidence review load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_review_history_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        evidence_id = str((params.get("evidence_record_id") or params.get("run_id") or [""])[0]).strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        try:
            from app.source_health_timeline import build_evidence_review_history

            history = build_evidence_review_history(evidence_id)
            self._send_json(history)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("evidence review-history load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_assess(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        try:
            from app.evidence_assessment import create_assessment

            assessment = create_assessment(
                evidence_record_id=str(body.get("evidence_record_id") or body.get("run_id") or "").strip(),
                impact_level=str(body.get("impact_level") or "").strip(),
                internal_note=str(body.get("internal_note") or body.get("note") or "").strip(),
                next_action=str(body.get("next_action") or "").strip(),
                reviewer_user_id=int(user["id"]),
                reviewer_name=str(user.get("full_name") or user.get("email") or "Reviewer"),
            )
            self._send_json({"ok": True, "assessment": assessment}, 201)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("evidence assess failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_export_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        evidence_id = str((params.get("evidence_record_id") or params.get("run_id") or [""])[0]).strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        export_format = str((params.get("format") or ["md_html"])[0]).strip() or "md_html"
        customer_delivery = _truthy_param((params.get("customer_delivery") or ["false"])[0])
        self._write_evidence_export(
            evidence_id,
            export_format=export_format,
            customer_delivery=customer_delivery,
        )

    def _handle_evidence_export_download(self) -> None:
        """GET /api/evidence/export-download?evidence_record_id=<id>&format=<pdf|md_html>
        Writes the audit pack and streams the output file to the browser as a download.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        evidence_id = str((params.get("evidence_record_id") or params.get("run_id") or [""])[0]).strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        export_format = str((params.get("format") or ["md_html"])[0]).strip() or "md_html"
        try:
            from app.audit_export import write_audit_pack, write_audit_pack_pdf
            from app.evidence_assessment import find_evidence_record, latest_assessment_for

            record = find_evidence_record(evidence_id)
            assessment = latest_assessment_for(evidence_id)

            want_pdf = export_format in {"pdf", "application/pdf"}
            if want_pdf:
                paths = write_audit_pack_pdf(record, assessment=assessment)
                file_path = BASE_DIR / paths["pdf_path"]
                content_type = "application/pdf"
                filename = file_path.name
            else:
                paths = write_audit_pack(record, assessment=assessment)
                file_path = BASE_DIR / paths["md_path"]
                content_type = "text/markdown; charset=utf-8"
                filename = file_path.name

            if not file_path.exists():
                self._send_json({"ok": False, "message": "Export file was not generated."}, 500)
                return

            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(data)))
            for k, v in _cors_headers(self.headers.get("Origin")).items():
                self.send_header(k, v)
            for k, v in _SECURITY_HEADERS.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except RuntimeError as exc:
            logger.warning("evidence export download runtime error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
        except Exception as exc:
            logger.error("evidence export download failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_reviews_queue_get(self) -> None:
        """GET /api/reviews/queue — saved evidence review queue."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        try:
            from app.review_queue import build_review_queue

            try:
                limit = int((params.get("limit") or ["50"])[0])
            except (TypeError, ValueError):
                limit = 50
            queue = build_review_queue(
                market=str((params.get("market") or ["AE"])[0]).upper().strip() or "AE",
                status=str((params.get("status") or ["pending"])[0]).strip() or "pending",
                impact_level=str((params.get("impact_level") or [""])[0]).strip() or None,
                source_health_status=str((params.get("source_health_status") or [""])[0]).strip() or None,
                change_status=str((params.get("change_status") or [""])[0]).strip() or None,
                source_id=str((params.get("source_id") or [""])[0]).strip() or None,
                limit=limit,
            )
            self._send_json(queue)
        except Exception as exc:
            logger.error("reviews/queue failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_canonical_evidence_get(self) -> None:
        """GET /api/canonical-evidence — append-only canonical evidence review state."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.review_queue import build_canonical_evidence_review_queue

            self._send_json(build_canonical_evidence_review_queue())
        except Exception as exc:
            logger.error("canonical evidence list failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_export_post(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        evidence_id = str(body.get("evidence_record_id") or body.get("run_id") or "").strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        export_format = str(body.get("format") or "md_html").strip() or "md_html"
        customer_delivery = _truthy_param(body.get("customer_delivery"))
        self._write_evidence_export(
            evidence_id,
            export_format=export_format,
            customer_delivery=customer_delivery,
        )

    def _write_evidence_export(
        self,
        evidence_id: str,
        *,
        export_format: str = "md_html",
        customer_delivery: bool = False,
    ) -> None:
        try:
            from app.audit_export import build_audit_pack_export_response, build_customer_audit_pack_export_response
            from app.evidence_assessment import find_evidence_record, latest_assessment_for

            if customer_delivery:
                response = build_customer_audit_pack_export_response(
                    evidence_id,
                    export_format=export_format,
                )
                self._send_json(response)
                return

            record = find_evidence_record(evidence_id)
            assessment = latest_assessment_for(evidence_id)
            response = build_audit_pack_export_response(
                record,
                assessment=assessment,
                export_format=export_format,
            )
            response["evidence_record_id"] = evidence_id
            self._send_json(response)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except RuntimeError as exc:
            logger.warning("evidence export runtime error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
        except Exception as exc:
            logger.error("evidence export failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_briefs_list(self) -> None:
        """GET /api/briefs — returns alert queue entries from data/alert_queue/*.json."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
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
            briefs: list[dict] = []
            if alert_dir.exists():
                for fpath in _glob.glob(str(alert_dir / "*.json")):
                    try:
                        with open(fpath, encoding="utf-8") as fh:
                            rec = json.load(fh)
                    except Exception:
                        continue
                    source_id = str(rec.get("source_id") or "")
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

    def _handle_plan_get(self) -> None:
        """GET /api/plan — returns current plan + trial state for the logged-in user."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.plan import get_plan_state
            state = get_plan_state(int(user["id"]))
            self._send_json({"ok": True, "plan": state})
        except Exception as exc:
            logger.error("plan_get failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_plan_set(self) -> None:
        """POST /api/plan — record plan intent (no payment processed)."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        plan_name = str(body.get("plan_name", "")).strip()
        try:
            from app.plan import set_plan_intent, PLAN_NAMES
            if plan_name not in PLAN_NAMES:
                self._send_json({"ok": False, "message": f"Unknown plan: {plan_name}"}, 400)
                return
            state = set_plan_intent(int(user["id"]), plan_name)
            self._send_json({
                "ok": True,
                "plan": state,
                "message": "Plan intent recorded. Our team will contact you to activate your pilot.",
                "disclaimer": "No payment has been processed. Billing is manually activated for founding pilots.",
            })
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("plan_set failed: %s", type(exc).__name__)
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


    def _handle_source_test(self) -> None:
        """
        Run a source compatibility check on a user-supplied URL.

        Uses existing test_source_url logic (SSRF-safe, no AI, no Telegram).
        Returns a standardised result for the frontend testing UI.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_SOURCE_TEST_LIMITER, "source_test"):
            return

        from app.source_tester import test_source_url, validate_public_url

        body = self._read_json()
        url  = str(body.get("url", "")).strip()

        if not url:
            self._send_json({"ok": False, "message": "URL is required."}, 400)
            return

        # Quick safety check before any network call
        safe, safety_msg = validate_public_url(url)
        if not safe:
            self._send_json({
                "ok":             False,
                "status":         "FAILED",
                "message":        f"URL failed safety check: {safety_msg}",
                "recommendation": "This URL cannot be used.",
                "extraction":     [],
                "chars":          0,
            }, 400)
            return

        try:
            result = test_source_url(url)
        except Exception as exc:
            logger.error("source-test error: %s: %s", type(exc).__name__, exc)
            self._send_json({"ok": False, "message": "Source test failed internally."}, 500)
            return

        verdict = result.get("verdict", "cannot_monitor")
        chars   = result.get("extracted_chars", 0)
        method  = result.get("recommended_method", "")
        reason  = result.get("reason", "")

        if verdict == "can_monitor":
            status         = "PASS"
            extraction     = ["HTML", "JS"] if "playwright" in method else ["HTML"]
            recommendation = "Can be monitored automatically."
        elif verdict == "needs_adapter":
            status         = "NEEDS_ADAPTER"
            extraction     = ["Limited"]
            recommendation = "Needs custom adapter for reliable extraction."
        else:
            status         = "FAILED"
            extraction     = []
            recommendation = "Not enough content to monitor reliably."

        self._send_json({
            "ok":             True,
            "status":         status,
            "extraction":     extraction,
            "chars":          chars,
            "message":        reason,
            "recommendation": recommendation,
        })


    def _handle_sources_readiness(self) -> None:
        """
        Return readiness summary for all enabled sources.

        Uses latest run records — no live fetch. Safe to call frequently.
        GET /api/sources/readiness
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.source_intake import readiness_summary, load_sources_json
            sources = load_sources_json()
            summary = readiness_summary(sources)
            self._send_json({"ok": True, **summary})
        except Exception as exc:
            logger.error("sources/readiness error: %s", exc)
            self._send_json({"ok": False, "message": "Failed to load readiness data."}, 500)

    def _handle_custom_sources_list(self) -> None:
        """
        List custom (user-added) sources for the authenticated user.

        GET /api/custom-sources
        Custom sources are identified by 'custom': True in sources.json.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.source_intake import load_sources_json
            sources = load_sources_json()
            custom = [s for s in sources if s.get("custom") is True]
            self._send_json({"ok": True, "sources": custom})
        except Exception as exc:
            logger.error("custom-sources list error: %s", exc)
            self._send_json({"ok": False, "message": "Failed to load custom sources."}, 500)

    def _handle_custom_source_discover(self) -> None:
        """
        Discover public endpoint candidates for a custom source URL.

        POST /api/custom-sources/discover
        Body: { "url": "https://...", "use_js": false }
        Returns structured no-save discovery data only. It never writes evidence
        and never marks a source ready.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_SOURCE_TEST_LIMITER, "custom_source_discover"):
            return

        body = self._read_json()
        url = str(body.get("url", "")).strip()
        if not url:
            self._send_json({"ok": False, "message": "URL is required."}, 400)
            return

        from app.source_tester import validate_public_url
        safe, safety_msg = validate_public_url(url)
        if not safe:
            self._send_json({"status": "BLOCKED", "reason": safety_msg, "ok": False}, 400)
            return

        try:
            from app.source_discovery import discover_source
            report = discover_source(
                url,
                use_js=bool(body.get("use_js") or body.get("js")),
                include_network=bool(body.get("network")),
                include_sitemap=body.get("sitemap", True) is not False,
                include_feeds=body.get("feeds", True) is not False,
                include_documents=body.get("documents", True) is not False,
                max_links=int(body.get("max_links") or 50),
                max_depth=int(body.get("max_depth") or 1),
            )
            self._send_json({
                "ok": True,
                "discovery": report,
                "evidence_written": False,
                "evidence_level": "PREVIEW_ONLY",
                "can_activate_monitoring": False,
                "message": "Discovery completed. Run a no-save Source Lab test before any evidence or activation step.",
            })
        except Exception as exc:
            logger.error("custom-source discovery error: %s: %s", type(exc).__name__, exc)
            self._send_json({"ok": False, "message": "Source discovery failed."}, 500)

    def _handle_custom_source_test(self) -> None:
        """
        Test a custom source URL using the intake layer.

        POST /api/custom-sources/test
        Body: { "url": "https://...", "name": "optional label" }
        Returns: intake result with status, quality fields, evidence level,
        can_save_for_validation, and can_activate_monitoring.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_SOURCE_TEST_LIMITER, "custom_source_test"):
            return

        body = self._read_json()
        url = str(body.get("url", "")).strip()

        if not url:
            self._send_json({"ok": False, "message": "URL is required."}, 400)
            return

        from app.source_tester import validate_public_url
        safe, safety_msg = validate_public_url(url)
        if not safe:
            self._send_json({"status": "BLOCKED", "reason": safety_msg, "ok": False}, 400)
            return

        try:
            from app.source_intake import run_source_intake, load_sources_json, STATUS_LABELS, build_source_lab_contract
            source = {"url": url, "source_id": "", "name": body.get("name", "")}
            if body.get("content_selector"):
                source["content_selector"] = str(body.get("content_selector"))
            if body.get("wait_for_selector"):
                source["wait_for_selector"] = str(body.get("wait_for_selector"))
            if body.get("expected_min_length"):
                source["expected_min_length"] = int(body.get("expected_min_length") or 0)
            if body.get("fetch_method") == "playwright":
                source["fetch_method"] = "playwright"
            if body.get("pdf_mode"):
                source["source_type"] = "pdf"
            if body.get("adapter_family"):
                source["adapter_family"] = str(body.get("adapter_family"))
            if body.get("adapter_name"):
                source["adapter_name"] = str(body.get("adapter_name"))
            adapter_config = body.get("adapter_config")
            if isinstance(adapter_config, dict):
                source["adapter_config"] = adapter_config
            all_sources = load_sources_json()
            result = run_source_intake(source, all_sources=all_sources, write_evidence=False)

            contract = build_source_lab_contract(result)
            normalized_hash = result.get("normalized_hash") or result.get("content_hash", "")
            self._send_json({
                "ok": True,
                "status": result["status"],
                "readiness_status": result["status"],
                "status_label": STATUS_LABELS.get(result["status"], result["status"]),
                "can_save_for_validation": contract["can_save_for_validation"],
                "can_activate_monitoring": contract["can_activate_monitoring"],
                "can_activate": contract["can_activate_monitoring"],
                "activation_readiness": contract["activation_readiness"],
                "baseline_runs_completed": contract["baseline_runs_completed"],
                "baseline_runs_required": contract["baseline_runs_required"],
                "source_type": "custom_public_source",
                # extraction details
                "chars": result["chars_normalized"],
                "normalized_length": result["chars_normalized"],
                "chars_raw": result["chars_raw"],
                "pdf_chars": result["pdf_chars"],
                "extraction_method": result.get("extraction_method", ""),
                "provider_used": result.get("provider_used") or result.get("extraction_method", ""),
                "adapter_used": result.get("adapter_used", False),
                "adapter_family": result.get("adapter_family", ""),
                "adapter_name": result.get("adapter_name", ""),
                "adapter_version": result.get("adapter_version", ""),
                "extraction_strategy": result.get("extraction_strategy", ""),
                "adapter_metadata": result.get("adapter_metadata", {}),
                "adapter_warnings": result.get("adapter_warnings", []),
                "dom_investigation": result.get("dom_investigation", {}),
                "normalized_hash": normalized_hash,
                "normalized_preview": result.get("normalized_preview", ""),
                # quality
                "quality": result["quality"],
                "quality_label": result["quality"],
                "quality_score": result.get("quality_score", 0),
                "quality_breakdown": result.get("quality_breakdown", {}),
                # safety flags
                "nav_shell_detected": result["nav_shell_detected"],
                "hash_collision": result["hash_collision"],
                "collision_source_id": result["collision_source_id"],
                "official_status": result.get("official_status", ""),
                "access_status": result.get("access_status", ""),
                "meaningful_content": result.get("meaningful_content", False),
                "shallow_content": result.get("shallow_content", False),
                "duplicate_hash": result.get("duplicate_hash", False),
                "noise_risk": result.get("noise_risk", "unknown"),
                "source_health_risk": result.get("source_health_risk", "unknown"),
                # failure detail
                "failure_code": result.get("failure_code", ""),
                "failure_reason": result.get("failure_reason", ""),
                "remediation_hint": result.get("remediation_hint", ""),
                "warnings": result.get("errors", []),
                "notes": result["notes"],
                # evidence status for this no-save test
                "evidence_written": False,
                "evidence_required": True,
                "proof_path": None,
                "evidence_level": result.get("evidence_level", "PREVIEW_ONLY"),
                "certification_status": result.get("certification_status", ""),
                "certification": result.get("certification", {}),
                "legal_policy_status": result.get("legal_policy_status", "PUBLIC_SOURCE_ONLY"),
            })
        except Exception as exc:
            logger.error("custom-source test error: %s: %s", type(exc).__name__, exc)
            self._send_json({"ok": False, "message": "Source test failed."}, 500)

    def _handle_custom_sources_add(self) -> None:
        """
        Add a custom source after a successful test.

        POST /api/custom-sources
        Body: { "url": "https://...", "name": "Label", "category": "financial_regulator", "jurisdiction": "AE" }
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return

        body = self._read_json()
        url = str(body.get("url", "")).strip()
        name = str(body.get("name", "")).strip() or url
        category = str(body.get("category", "custom")).strip()
        jurisdiction = str(body.get("jurisdiction", "AE")).strip()
        legal_confirmed = bool(body.get("legal_confirmed") or body.get("legalConfirmation"))

        if not url:
            self._send_json({"ok": False, "message": "URL is required."}, 400)
            return
        if not legal_confirmed:
            self._send_json({
                "ok": False,
                "message": "Legal confirmation is required before saving a custom source.",
            }, 400)
            return

        try:
            from app.source_tester import validate_public_url, source_url_exists, append_source_to_json
            from app.source_intake import run_source_intake, load_sources_json
            import hashlib

            safe, reason = validate_public_url(url)
            if not safe:
                self._send_json({"ok": False, "message": f"URL blocked: {reason}"}, 400)
                return

            if source_url_exists(url):
                self._send_json({"ok": False, "message": "This URL is already in the source list."}, 409)
                return

            intake_result = run_source_intake(
                {
                    "url": url,
                    "source_id": "",
                    "name": name,
                    "category": category,
                    "jurisdiction": jurisdiction,
                },
                all_sources=load_sources_json(),
                write_evidence=False,
            )
            if intake_result.get("status") != "CONFIRMED_ACCESSIBLE":
                self._send_json({
                    "ok": False,
                    "message": "Source cannot be saved until readiness test passes.",
                    "readiness_status": intake_result.get("status"),
                    "failure_reason": intake_result.get("failure_reason", ""),
                    "remediation_hint": intake_result.get("remediation_hint", ""),
                }, 400)
                return

            source_id = f"custom-{hashlib.sha256(url.encode()).hexdigest()[:8]}"
            new_source = {
                "source_id": source_id,
                "name": name,
                "url": url,
                "jurisdiction": jurisdiction,
                "category": category,
                "enabled": False,
                "status": "pending_validation",
                "custom": True,
                "tier": "custom",
            }
            append_source_to_json(new_source)
            self._send_json({
                "ok": True,
                "source_id": source_id,
                "message": "Custom source saved for validation. It is not active until readiness and evidence checks pass.",
            })
        except Exception as exc:
            logger.error("custom-sources add error: %s: %s", type(exc).__name__, exc)
            self._send_json({"ok": False, "message": "Failed to add source."}, 500)

    # ── GET /api/reports/monthly-assurance ────────────────────────────────────

    def _handle_monthly_assurance_report(self) -> None:
        """Return a monthly monitoring assurance report as JSON (markdown or PDF)."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        from app.monthly_assurance_report import compute_monthly_stats, render_assurance_report_markdown, generate_monthly_report_pdf
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        now = datetime.now(timezone.utc)
        try:
            year = int((qs.get("year") or [str(now.year)])[0])
            month = int((qs.get("month") or [str(now.month)])[0])
        except (ValueError, IndexError):
            self._send_json({"status": "error", "message": "Invalid year or month."}, 400)
            return
        source_ids_raw = (qs.get("source_ids") or [""])[0]
        source_ids = [s.strip() for s in source_ids_raw.split(",") if s.strip()] or None
        client_name = (qs.get("client_name") or [""])[0]
        fmt = ((qs.get("format") or ["markdown"])[0]).lower().strip()
        try:
            stats = compute_monthly_stats(source_ids, year, month)
            if fmt == "pdf":
                pdf_path = generate_monthly_report_pdf(stats, client_name=client_name)
                self._send_json({"status": "ok", "report_path": str(pdf_path)})
            else:
                report = render_assurance_report_markdown(stats, client_name=client_name)
                self._send_json({"status": "ok", "report": report, "stats": stats})
        except Exception as exc:
            logger.error("monthly-assurance error: %s", type(exc).__name__)
            self._send_json({"status": "error", "message": "Internal server error."}, 500)

    # ── GET /api/email/delivery-status ────────────────────────────────────────

    def _handle_email_delivery_status(self) -> None:
        """Return email provider configuration status (authenticated users only)."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        from app.email_delivery import validate_email_provider_config
        try:
            config = validate_email_provider_config()
            self._send_json({"status": "ok", **config})
        except Exception as exc:
            logger.error("email delivery-status error: %s", type(exc).__name__)
            self._send_json({"status": "error", "message": "Unable to retrieve email configuration."}, 500)

    # ── POST /api/review/action ───────────────────────────────────────────────

    def _handle_review_action(self) -> None:
        """Record an accountability action on a review queue item."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        from app.review_queue import record_review_action
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        record_id = str(body.get("record_id") or "").strip()
        action = str(body.get("action") or "").strip()
        # Derive user_id from the authenticated session; ignore any client-supplied value.
        user_id = str(user.get("id") or "").strip()
        reason = str(body.get("reason") or "").strip()
        if not record_id or not action or not user_id:
            self._send_json({"ok": False, "message": "record_id, action, and user_id are required."}, 400)
            return
        try:
            result = record_review_action(record_id, action, user_id, reason=reason)
            if result.get("status") == "error":
                self._send_json({"ok": False, **result}, 400)
            else:
                self._send_json({"ok": True, **result})
        except Exception as exc:
            logger.error("review action error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_canonical_evidence_review_action(self) -> None:
        """Append an approval/rejection/block decision for canonical evidence."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        record_id = str(body.get("record_id") or body.get("evidence_record_id") or "").strip()
        raw_decision = str(body.get("decision") or body.get("action") or "").strip().lower()
        decision = {
            "approve": "approved",
            "approved": "approved",
            "reject": "rejected",
            "rejected": "rejected",
            "block": "blocked",
            "blocked": "blocked",
        }.get(raw_decision, raw_decision)
        note = str(body.get("note") or body.get("reason") or "").strip()
        reviewer = str(user.get("full_name") or user.get("email") or f"user:{user.get('id')}" or "").strip()
        if not record_id or not decision or not note:
            self._send_json({"ok": False, "message": "record_id, decision, and note are required."}, 400)
            return
        try:
            from app.review_queue import record_canonical_review_action

            result = record_canonical_review_action(
                record_id,
                decision=decision,
                reviewer=reviewer,
                note=note,
            )
            if result.get("status") == "error":
                self._send_json({"ok": False, **result}, 400)
            else:
                self._send_json({"ok": True, **result})
        except Exception as exc:
            logger.error("canonical evidence review action error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    # ── POST /api/audit/vault ─────────────────────────────────────────────────

    def _handle_audit_vault(self) -> None:
        """Build a period-based audit vault ZIP from matching evidence records."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        from app.audit_export import build_period_audit_vault, validate_date_range
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        source_ids = body.get("source_ids")
        date_from = str(body.get("date_from") or "").strip()
        date_to = str(body.get("date_to") or "").strip()
        if not source_ids or not isinstance(source_ids, list):
            self._send_json({"ok": False, "message": "source_ids must be a non-empty list."}, 400)
            return
        valid, err = validate_date_range(date_from, date_to)
        if not valid:
            self._send_json({"ok": False, "message": err}, 400)
            return
        try:
            result = build_period_audit_vault(source_ids, date_from, date_to)
            if result.get("status") == "error":
                self._send_json({"ok": False, **result}, 500)
            elif result.get("status") == "empty":
                self._send_json({"ok": False, **result}, 404)
            else:
                self._send_json({"ok": True, **result})
        except Exception as exc:
            logger.error("audit vault error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)


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
