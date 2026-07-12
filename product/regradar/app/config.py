"""
RegRadar v3 — centralised configuration.

All values come from environment variables so the same codebase runs
locally with a .env file and in any CI/cloud environment without changes.

Feature flags default to disabled so the system works out-of-the-box
without any API keys.  Keys are never printed to the console.
"""

import os
from pathlib import Path

# Load .env from project root.
#
# override=True ensures the project .env always wins over any pre-existing
# shell environment variables with the same name.  Without this, a stale
# TELEGRAM_BOT_TOKEN exported in the shell (e.g. from a previous project or
# a system-wide profile) silently shadows the value in .env, causing the
# wrong bot to be used.
_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(_DOTENV_PATH, override=True)
except Exception:
    pass

# ── paths ─────────────────────────────────────────────────────────────────────

# Honors STATUTEPROOF_BASE_DIR so all stores (trail, DB, outbox, API readers)
# resolve the same tree — source_runs already did; config/email did not
# (split-brain found in the 2026-07-06 evaluation, finding N2).
BASE_DIR = Path(os.getenv("STATUTEPROOF_BASE_DIR") or Path(__file__).parent.parent).resolve()

# `or` (not a getenv default): an empty/blank env value must fall back too.
DB_PATH = os.getenv("REGRADAR_DB_PATH") or str(BASE_DIR / "regradar.db")

# ── scraper ───────────────────────────────────────────────────────────────────

# Playwright page-load timeout in ms (Tier 2 fallback)
PAGE_TIMEOUT_MS: int = int(os.getenv("REGRADAR_TIMEOUT_MS", "30000"))

# requests.get() timeout in seconds (Tier 1 fast path)
HTTP_TIMEOUT_S: int = int(os.getenv("REGRADAR_HTTP_TIMEOUT_S", "15"))

# Realistic browser User-Agent shared across both scraping tiers
REQUESTS_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# ── AI analysis ───────────────────────────────────────────────────────────────

# Set ENABLE_AI_ANALYSIS=true to activate Claude-based compliance analysis.
# If the key is missing or the API call fails, pipeline falls back to
# rule-based scoring automatically — no crash, no data loss.
ENABLE_AI_ANALYSIS: bool = os.getenv("ENABLE_AI_ANALYSIS", "false").lower() == "true"
ANTHROPIC_API_KEY:  str  = os.getenv("ANTHROPIC_API_KEY", "")

# Minimum rule-based risk level required before calling AI.
# LOW changes skip AI entirely — no wasted credits on noise.
AI_MIN_RISK_FOR_ANALYSIS: str = os.getenv("AI_MIN_RISK_FOR_ANALYSIS", "MEDIUM").upper()

# Maximum Claude API calls allowed per batch run (run.py all / watch iteration).
# When the limit is reached, remaining sources use rule-based fallback.
AI_MAX_CALLS_PER_RUN: int = int(os.getenv("AI_MAX_CALLS_PER_RUN", "3"))

# ── Telegram alerts ───────────────────────────────────────────────────────────

# Set ENABLE_TELEGRAM_ALERTS=true to push MEDIUM/HIGH alerts to Telegram.
# If credentials are missing or the POST fails, the pipeline continues
# normally — the Telegram step never blocks or crashes the main flow.
ENABLE_TELEGRAM_ALERTS: bool = os.getenv("ENABLE_TELEGRAM_ALERTS", "false").lower() == "true"

# Admin/founder bot — used ONLY for contact-form notifications to the founder.
TELEGRAM_BOT_TOKEN:     str  = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID:       str  = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_BOT_USERNAME:  str  = os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")

# Customer-facing alerts bot — used for customer account pairing and regulatory
# change alerts. Shown on the website. Separate from the founder admin bot.
# Falls back to TELEGRAM_BOT_TOKEN if not set (single-bot legacy mode).
TELEGRAM_ALERTS_BOT_TOKEN:    str = os.getenv("TELEGRAM_ALERTS_BOT_TOKEN", "").strip() or os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALERTS_BOT_USERNAME: str = os.getenv("TELEGRAM_ALERTS_BOT_USERNAME", "").strip().lstrip("@") or os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")

# Contact-form smoke tests can queue requests without sending Telegram.
# This affects only /api/contact delivery; monitoring alerts and telegram-test
# still use the Telegram settings above.
CONTACT_DELIVERY_DISABLED: bool = (
    os.getenv("REGRADAR_CONTACT_DELIVERY_DISABLED", "false").lower()
    in {"1", "true", "yes", "on"}
)

# ── scheduler ─────────────────────────────────────────────────────────────────

# How often watch mode re-checks all enabled sources (minutes).
# Override with: WATCH_INTERVAL_MINUTES=30
WATCH_INTERVAL_MINUTES: int = int(os.getenv("WATCH_INTERVAL_MINUTES", "60"))

# ── multilingual AI output ────────────────────────────────────────────────────

# Language code for AI-generated compliance summaries (default: English).
# The AI reads source text in any language and writes summaries in this language.
AI_OUTPUT_LANGUAGE: str = os.getenv("AI_OUTPUT_LANGUAGE", "en")

# When True, detect source language before sending text to AI.
# Provides the AI with a language hint for better prompting.
AI_DETECT_LANGUAGE: bool = os.getenv("AI_DETECT_LANGUAGE", "true").lower() == "true"

# Language code for AI Compliance Brief output (default: English).
# Separate from AI_OUTPUT_LANGUAGE so brief language can differ from
# the pipeline summary language if needed.
AI_BRIEF_LANGUAGE: str = os.getenv("AI_BRIEF_LANGUAGE", "en")

# ── source discovery (deep mode) ─────────────────────────────────────────────

# Maximum links stored from a single sitemap or feed (caps memory, not fetches).
DISCOVERY_MAX_LINKS: int = int(os.getenv("DISCOVERY_MAX_LINKS", "50"))

# Maximum document URLs sampled per source in deep discovery mode.
DISCOVERY_MAX_SAMPLE_DOCS: int = int(os.getenv("DISCOVERY_MAX_SAMPLE_DOCS", "3"))

# Maximum document download size in MB for sample extraction.
DOCUMENT_MAX_DOWNLOAD_MB: int = int(os.getenv("DOCUMENT_MAX_DOWNLOAD_MB", "15"))

# When true, deep discovery runs even without the --deep CLI flag.
# Default false: deep mode is always opt-in.
ENABLE_DEEP_SOURCE_DISCOVERY: bool = (
    os.getenv("ENABLE_DEEP_SOURCE_DISCOVERY", "false").lower() == "true"
)

# ── optional extraction layer ─────────────────────────────────────────────────

# Enable experimental Crawl4AI extractor (re-fetches the URL via headless
# browser; only used when Trafilatura + readability both return low-quality).
# Requires: pip install crawl4ai
ENABLE_CRAWL4AI_EXTRACTOR: bool = (
    os.getenv("ENABLE_CRAWL4AI_EXTRACTOR", "false").lower() == "true"
)

# ── external RFC 3161 timestamp anchor (DORMANT by default) ───────────────────
#
# Optional third-party trusted-timestamp anchor for the evidence chain head. When
# RFC3161_TSA_URL is UNSET (the default), the anchor is a complete no-op: no
# network, no threads, no files, and the capture pipeline is byte-for-byte
# unchanged. There is NO default TSA — nothing calls out unless an operator
# explicitly configures one. See app/rfc3161_anchor.py and
# docs/EVIDENCE-VERIFICATION-SPEC.md §5.
#
# To enable, point at a public RFC 3161 TSA (e.g. https://freetsa.org/tsr) and,
# for signed offline verification, keep RFC3161_TSA_CERT_REQ=true so the token
# embeds the TSA certificate. Enabling also requires the optional `asn1crypto`
# dependency (see requirements.txt); `cryptography` is already present in prod.
RFC3161_TSA_URL: str = os.getenv("RFC3161_TSA_URL", "").strip()
try:
    RFC3161_TSA_TIMEOUT_S: float = float(os.getenv("RFC3161_TSA_TIMEOUT_S", "10"))
except ValueError:
    # Never crash the process at import on a malformed timeout. The anchor module's
    # own _timeout_s() reads + clamps this at call time; these constants document the
    # env contract (rfc3161_anchor.py reads os.environ directly, not these).
    RFC3161_TSA_TIMEOUT_S = 10.0
RFC3161_TSA_CERT_REQ: bool = os.getenv("RFC3161_TSA_CERT_REQ", "true").lower() != "false"
RFC3161_TSA_POLICY_OID: str = os.getenv("RFC3161_TSA_POLICY_OID", "").strip()
ENABLE_RFC3161_ANCHOR: bool = bool(RFC3161_TSA_URL)

# ── web server ────────────────────────────────────────────────────────────────

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-to-a-random-64-char-string")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING").upper()
LOG_DIR: str = os.getenv("LOG_DIR", "logs")

# ── startup validation ────────────────────────────────────────────────────────


def validate_config() -> list[str]:
    """Return list of critical configuration warnings."""
    warnings: list[str] = []
    if not SECRET_KEY or SECRET_KEY == "change-me-to-a-random-64-char-string":
        warnings.append(
            "SECRET_KEY is not set or is the default placeholder — set a real secret before production use."
        )
    if len(SECRET_KEY) < 32:
        warnings.append(
            f"SECRET_KEY is too short ({len(SECRET_KEY)} chars) — use at least 32 random chars."
        )
    return warnings
