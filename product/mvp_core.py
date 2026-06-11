#!/usr/bin/env python3
"""
mvp_core.py — RegRadar MVP Pipeline v2
Crawl4AI + Playwright + Anthropic/OpenAI Fallback + SQLite + Telegram

5-step regulatory change-detection pipeline:
  1. Resilient ingestion  — Crawl4AI (playwright-backed, semantic markdown)
                            → direct Playwright + BeautifulSoup fallback
  2. Hash & store         — SQLite WAL + SHA-256 fingerprinting
  3. Paragraph diff       — unified_diff on semantic blocks, zero context lines
  4. AI compliance analysis — Anthropic claude-3-haiku → OpenAI gpt-4o-mini fallback
  5. Telegram alert routing — MEDIUM / HIGH risk only, Markdown-formatted

──────────────────────────────────────────────────────────────────────────────
INSTALLATION  (run once in your terminal before executing this script)
──────────────────────────────────────────────────────────────────────────────

    pip install playwright crawl4ai beautifulsoup4 requests python-dotenv anthropic openai
    playwright install

Optional (faster crawl4ai NLP models — recommended):

    pip install "crawl4ai[all]"
    python -m crawl4ai.download_models

──────────────────────────────────────────────────────────────────────────────
USAGE
──────────────────────────────────────────────────────────────────────────────

    python3 mvp_core.py

ENVIRONMENT  (loaded from /Users/kurbnovomar/документы/obsidian/.env)

    ANTHROPIC_API_KEY      — primary AI key  (claude-3-haiku-20240307)
    OPENAI_API_KEY         — fallback AI key (gpt-4o-mini)
    TELEGRAM_BOT_TOKEN     — Telegram Bot API token
    TELEGRAM_CHAT_ID       — target chat / channel ID
    MVP_DB_PATH            — optional SQLite path  (default: mvp_core.db)
"""

# ── stdlib ─────────────────────────────────────────────────────────────────
import asyncio
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from difflib import unified_diff
from pathlib import Path
from typing import Literal

# ── third-party ────────────────────────────────────────────────────────────
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PWTimeout, sync_playwright


# ══════════════════════════════════════════════════════════════════════════════
#  ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════

# Primary env: the shared obsidian vault (contains Telegram + Anthropic keys).
# Local .env next to this file can override individual values.
_OBSIDIAN_ENV = Path("/Users/kurbnovomar/документы/obsidian/.env")
_LOCAL_ENV    = Path(__file__).parent / ".env"

load_dotenv(_OBSIDIAN_ENV, override=False)
load_dotenv(_LOCAL_ENV,    override=True)

ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY",  "")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY",     "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "")
DB_PATH            = Path(os.getenv("MVP_DB_PATH",   "mvp_core.db"))


# ══════════════════════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════════════════════

_COLORS = {
    "INIT":  "\033[36m",    # cyan
    "OK":    "\033[32m",    # green
    "SKIP":  "\033[90m",    # dark grey
    "DELTA": "\033[33m",    # yellow
    "ALERT": "\033[31m",    # red
    "WARN":  "\033[35m",    # magenta
    "ERROR": "\033[31;1m",  # bold red
    "RESET": "\033[0m",
}


def _log(level: str, msg: str) -> None:
    ts    = datetime.now().strftime("%H:%M:%S")
    col   = _COLORS.get(level, "")
    reset = _COLORS["RESET"]
    print(f"{col}[{ts}][{level:<5}]{reset} {msg}", flush=True)


log_init  = lambda m: _log("INIT",  m)
log_ok    = lambda m: _log("OK",    m)
log_skip  = lambda m: _log("SKIP",  m)
log_delta = lambda m: _log("DELTA", m)
log_alert = lambda m: _log("ALERT", m)
log_warn  = lambda m: _log("WARN",  m)
log_err   = lambda m: _log("ERROR", m)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — RESILIENT INGESTION LAYER
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_and_clean(url: str) -> str:
    """
    Two-tier ingestion strategy:

    Tier 1 — Crawl4AI:
        Uses a headless Playwright browser under the hood.  Returns clean
        semantic markdown (headers, footers, scripts, navbars stripped
        automatically).  The markdown is post-processed into plain paragraph
        blocks separated by double newlines.

    Tier 2 — Direct Playwright + BeautifulSoup:
        Falls back when Crawl4AI is unavailable, returns an empty body, or
        raises any exception.  Runs the sync Playwright API inside a thread
        so it does not block the event loop.

    Returns clean text, paragraphs delimited by double newlines.
    Raises ValueError when both tiers return insufficient content.
    """
    # ── Tier 1: Crawl4AI ─────────────────────────────────────────────
    try:
        from crawl4ai import (
            AsyncWebCrawler,
            BrowserConfig,
            CacheMode,
            CrawlerRunConfig,
            PruningContentFilter,
        )

        browser_cfg = BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=10,
            excluded_tags=["nav", "footer", "header", "aside",
                           "script", "style", "noscript", "form",
                           "button", "input", "iframe"],
            remove_overlay_elements=True,
            wait_for="domcontentloaded",
            page_timeout=60_000,
            content_filter=PruningContentFilter(
                threshold=0.45,
                threshold_type="fixed",
                min_word_threshold=5,
            ),
        )

        log_init(f"[Crawl4AI]  →  {url}")
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)

        if result.success:
            raw_md = ""
            # Newer crawl4ai returns a MarkdownGenerationResult object;
            # older versions return a plain string.
            md_obj = getattr(result, "markdown", None)
            if md_obj is not None:
                raw_md = (
                    md_obj.raw_markdown
                    if hasattr(md_obj, "raw_markdown")
                    else str(md_obj)
                )
            clean = _clean_markdown(raw_md)
            if len(clean) >= 300:
                log_ok(
                    f"Crawl4AI extracted {len(clean):,} chars"
                    f"  ({clean.count(chr(10)*2) + 1} paragraphs)"
                )
                return clean
            log_warn("Crawl4AI returned insufficient content — switching to Playwright")
        else:
            log_warn(
                f"Crawl4AI reported failure"
                f"  ({getattr(result, 'error_message', 'unknown')}) — switching to Playwright"
            )

    except ImportError:
        log_warn("crawl4ai not installed — switching to Playwright  "
                 "(pip install crawl4ai)")
    except Exception as exc:
        log_warn(f"Crawl4AI error ({type(exc).__name__}: {exc}) — switching to Playwright")

    # ── Tier 2: Direct Playwright + BeautifulSoup ─────────────────────
    log_init(f"[Playwright]  →  {url}")
    html  = await asyncio.to_thread(_playwright_fetch_html, url)
    clean = _html_to_text(html)

    if len(clean) < 100:
        raise ValueError(
            f"Both scrapers returned insufficient content for {url}"
        )

    log_ok(
        f"Playwright extracted {len(clean):,} chars"
        f"  ({clean.count(chr(10)*2) + 1} paragraphs)"
    )
    return clean


# ── Crawl4AI markdown post-processor ─────────────────────────────────────────

def _clean_markdown(md: str) -> str:
    """
    Strip markdown syntax artifacts from Crawl4AI output and return plain
    paragraph text blocks separated by double newlines, deduped, min 40 chars.
    """
    # Multi-line code fences
    md = re.sub(r"```[\s\S]*?```", " ", md)
    # Inline code
    md = re.sub(r"`[^`\n]+`", " ", md)
    # Headers — keep text, drop the leading hashes
    md = re.sub(r"^#{1,6}\s+", "", md, flags=re.MULTILINE)
    # Setext headers (underline-style)
    md = re.sub(r"^[=\-]{3,}\s*$", "", md, flags=re.MULTILINE)
    # Horizontal rules
    md = re.sub(r"^[-*_]{3,}\s*$", "", md, flags=re.MULTILINE)
    # Markdown images
    md = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", md)
    # Markdown links → display text only
    md = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", md)
    # Bold / italic (up to triple asterisk/underscore)
    md = re.sub(r"[*_]{1,3}([^*_\n]+)[*_]{1,3}", r"\1", md)
    # Table rows (pipe-delimited)
    md = re.sub(r"^\|.*\|\s*$", "", md, flags=re.MULTILINE)
    # Blockquote markers
    md = re.sub(r"^>\s?", "", md, flags=re.MULTILINE)
    # Bullet / numbered list markers
    md = re.sub(r"^[\s]*[-*+]\s+", "", md, flags=re.MULTILINE)
    md = re.sub(r"^[\s]*\d+\.\s+", "", md, flags=re.MULTILINE)

    blocks: list[str] = []
    seen:   set[str]  = set()

    for chunk in md.split("\n\n"):
        text = " ".join(chunk.split()).strip()
        if len(text) >= 40 and text not in seen:
            blocks.append(text)
            seen.add(text)

    return "\n\n".join(blocks)


# ── Playwright sync fetcher (runs in thread via asyncio.to_thread) ─────────

def _playwright_fetch_html(url: str) -> str:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        ctx  = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()
        try:
            page.goto(url, timeout=60_000, wait_until="domcontentloaded")
            page.wait_for_timeout(2_000)
            html = page.content()
        except PWTimeout:
            raise TimeoutError(f"Page did not load within 60 s: {url}")
        finally:
            ctx.close()
            browser.close()

    if not html or len(html) < 200:
        raise ValueError(f"Empty or near-empty response from {url}")
    return html


def _html_to_text(html: str) -> str:
    """BeautifulSoup semantic paragraph extraction — Playwright fallback path."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "head",
                     "nav", "footer", "header", "aside",
                     "form", "button", "input", "iframe"]):
        tag.decompose()

    blocks: list[str] = []
    seen:   set[str]  = set()

    for el in soup.find_all(
        ["p", "li", "td", "th", "h1", "h2", "h3", "h4", "h5",
         "article", "section", "blockquote", "dd", "dt"]
    ):
        text = el.get_text(separator=" ", strip=True)
        if len(text) < 40 or text in seen:
            continue
        seen.add(text)
        blocks.append(text)

    if not blocks:
        body   = soup.get_text(separator="\n")
        blocks = [ln.strip() for ln in body.splitlines() if len(ln.strip()) >= 40]

    return "\n\n".join(blocks)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — DATABASE LAYER & PERSISTENT SHA-256 HASHING
# ══════════════════════════════════════════════════════════════════════════════

DocumentState = Literal["NEW_DOCUMENT", "NO_CHANGE", "DETECTED_DELTA"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    url        TEXT        UNIQUE NOT NULL,
    content    TEXT        NOT NULL,
    sha_hash   VARCHAR(64) NOT NULL,
    updated_at TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def upsert_document(url: str, content: str) -> tuple[DocumentState, str]:
    """
    Compute SHA-256 of `content` and compare against the stored hash for `url`.

    Returns
    -------
    ("NEW_DOCUMENT",   "")           first time we see this URL; baseline stored
    ("NO_CHANGE",      "")           hash matches; nothing to do
    ("DETECTED_DELTA", <old_text>)   hash changed; old text returned for diff
    """
    sha  = hashlib.sha256(content.encode("utf-8")).hexdigest()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT sha_hash, content FROM documents WHERE url = ?", (url,)
        ).fetchone()

        if row is None:
            conn.execute(
                "INSERT INTO documents (url, content, sha_hash, updated_at)"
                " VALUES (?, ?, ?, ?)",
                (url, content, sha, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return "NEW_DOCUMENT", ""

        if row["sha_hash"] == sha:
            return "NO_CHANGE", ""

        old_content = row["content"]
        conn.execute(
            "UPDATE documents SET content = ?, sha_hash = ?, updated_at = ?"
            " WHERE url = ?",
            (content, sha, datetime.utcnow().isoformat(), url),
        )
        conn.commit()
        return "DETECTED_DELTA", old_content
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — HIGH-FIDELITY PARAGRAPH DIFF ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def calculate_delta(old_text: str, new_text: str) -> str:
    """
    Semantic paragraph-level diff using difflib.unified_diff.

    Algorithm:
      1. Split both texts on '\\n\\n' to obtain semantic paragraph sequences.
      2. Run unified_diff with n=0 (zero context lines) — only changed rows.
      3. Extract lines starting with '-' (removed) and '+' (added).
      4. Discard micro-fragments shorter than 20 chars (formatting artifacts).
      5. Return a structured delta string with === REMOVED === / === ADDED ===
         sections, or "" when no meaningful mutations exist.

    Unchanged paragraphs are entirely discarded to protect AI token limits.
    """
    old_paras = [p.strip() for p in old_text.split("\n\n") if p.strip()]
    new_paras = [p.strip() for p in new_text.split("\n\n") if p.strip()]

    diff = list(unified_diff(
        old_paras,
        new_paras,
        fromfile="previous_version",
        tofile="current_version",
        lineterm="",
        n=0,
    ))

    if not diff:
        return ""

    removed = [
        ln[1:].strip() for ln in diff
        if ln.startswith("-") and not ln.startswith("---")
    ]
    added = [
        ln[1:].strip() for ln in diff
        if ln.startswith("+") and not ln.startswith("+++")
    ]

    removed = [p for p in removed if len(p) > 20]
    added   = [p for p in added   if len(p) > 20]

    if not removed and not added:
        return ""

    parts: list[str] = []
    if removed:
        parts.append("=== REMOVED ===\n" + "\n\n".join(removed))
    if added:
        parts.append("=== ADDED ===\n"   + "\n\n".join(added))

    return "\n\n".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — AI COMPLIANCE ANALYSIS  (Anthropic → OpenAI safe fallback)
# ══════════════════════════════════════════════════════════════════════════════

_ANALYSIS_PROMPT = """\
You are a B2B Regulatory Compliance Expert for a financial institution \
operating in CIS countries (Russia, Kazakhstan, Azerbaijan, Belarus, Uzbekistan).

A regulatory document has changed. Below is ONLY the extracted delta — the exact \
paragraphs that were removed or added. Analyse this delta alone; do not speculate \
about content not shown.

DELTA:
{delta}

Respond with ONLY a valid JSON object — no markdown fences, no prose, no extra keys:
{{"risk_level": "LOW" | "MEDIUM" | "HIGH", \
"executive_summary": "2-3 sentences explaining what changed and why it matters \
to a compliance officer", \
"business_action_required": "one concrete action the compliance team must \
complete within 30 days"}}
"""

_MAX_DELTA_CHARS = 8_000   # stay within context budget, save tokens


def analyze_compliance_delta(delta_text: str) -> dict:
    """
    Pass only the delta to the LLM and return a structured compliance assessment.

    Preference chain
    ----------------
    1. Anthropic  claude-3-haiku-20240307   — if ANTHROPIC_API_KEY is set
       Falls through on AuthenticationError or any other exception.
    2. OpenAI     gpt-4o-mini              — if OPENAI_API_KEY is set
       Uses response_format=json_object for deterministic JSON output.
    3. RuntimeError                        — no credentials configured

    Returns dict with keys:
        risk_level             — "LOW" | "MEDIUM" | "HIGH"
        executive_summary      — str
        business_action_required — str
    """
    prompt = _ANALYSIS_PROMPT.format(delta=delta_text[:_MAX_DELTA_CHARS])

    # ── 1. Anthropic claude-3-haiku ───────────────────────────────────
    if ANTHROPIC_API_KEY:
        try:
            import anthropic

            client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model      = "claude-3-haiku-20240307",
                max_tokens = 512,
                messages   = [{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            log_ok("AI analysis via Anthropic claude-3-haiku-20240307")
            return _parse_ai_json(raw)

        except anthropic.AuthenticationError as exc:
            log_warn(f"Anthropic authentication failed ({exc}) — trying OpenAI")
        except Exception as exc:
            log_warn(
                f"Anthropic error ({type(exc).__name__}: {exc}) — trying OpenAI"
            )

    # ── 2. OpenAI gpt-4o-mini fallback ───────────────────────────────
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI

            client   = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model           = "gpt-4o-mini",
                max_tokens      = 512,
                response_format = {"type": "json_object"},
                messages        = [{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()
            log_ok("AI analysis via OpenAI gpt-4o-mini")
            return _parse_ai_json(raw)

        except Exception as exc:
            log_warn(f"OpenAI error ({type(exc).__name__}: {exc})")

    # ── 3. No credentials ────────────────────────────────────────────
    raise RuntimeError(
        "No AI credentials configured. "
        "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file."
    )


def _parse_ai_json(raw: str) -> dict:
    """
    Parse and normalise the raw LLM response into a clean dict.
    Strips markdown code fences that some models emit despite instructions.
    """
    if raw.startswith("```"):
        parts = raw.split("```")
        raw   = parts[1] if len(parts) > 1 else raw
        if raw.lower().startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)

    result["risk_level"] = result.get("risk_level", "LOW").upper().strip()
    if result["risk_level"] not in ("LOW", "MEDIUM", "HIGH"):
        result["risk_level"] = "LOW"

    return result


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5 — B2B STRUCTURED TELEGRAM ALERT ROUTING
# ══════════════════════════════════════════════════════════════════════════════

_RISK_BADGE = {
    "HIGH":   "🔴 HIGH RISK",
    "MEDIUM": "🟡 MEDIUM RISK",
    "LOW":    "🟢 LOW RISK",
}
_ALERT_THRESHOLD = {"MEDIUM", "HIGH"}


def dispatch_telegram_alert(analysis: dict, url: str) -> None:
    """
    Route a beautifully formatted Markdown alert to the configured Telegram
    chat when risk_level is MEDIUM or HIGH.

    Silently skips if:
      - risk_level is LOW
      - TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is absent from the environment

    Raises requests.HTTPError on a 4xx / 5xx Telegram API response.
    """
    risk = analysis.get("risk_level", "LOW")

    if risk not in _ALERT_THRESHOLD:
        log_skip(f"Risk {risk} — Telegram alert not required")
        return

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log_warn(
            "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — skipping alert"
        )
        return

    badge   = _RISK_BADGE.get(risk, risk)
    summary = analysis.get("executive_summary",        "N/A")
    action  = analysis.get("business_action_required", "N/A")
    ts      = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def _esc(s: str) -> str:
        return (
            s.replace("_", "\\_")
             .replace("*", "\\*")
             .replace("`", "\\`")
             .replace("[", "\\[")
        )

    text = (
        f"*⚡ RegRadar — Regulatory Change Detected*\n\n"
        f"*Risk Level:* {badge}\n"
        f"*Source URL:*\n`{url}`\n\n"
        f"*Executive Summary:*\n{_esc(summary)}\n\n"
        f"*Required Compliance Action (within 30 days):*\n{_esc(action)}\n\n"
        f"_{ts} · RegRadar MVP v2_"
    )

    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id":                  TELEGRAM_CHAT_ID,
            "text":                     text,
            "parse_mode":               "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    resp.raise_for_status()
    log_alert(
        f"Telegram alert dispatched — risk={risk}  chat={TELEGRAM_CHAT_ID}"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTION
# ══════════════════════════════════════════════════════════════════════════════

TARGET_URLS: list[str] = [
    # Central Bank of Russia — press releases & circulars
    "https://cbr.ru/press/pr/",
    # Ministry of Finance Russia — normative documents
    "https://minfin.gov.ru/ru/document/",
    # National Bank of Kazakhstan — regulatory legal base
    "https://nationalbank.kz/ru/link/normativnaya-pravovaya-baza",
]


def _banner() -> None:
    width = 66
    ai_label = (
        "Anthropic  claude-3-haiku-20240307" if ANTHROPIC_API_KEY else
        "OpenAI  gpt-4o-mini"               if OPENAI_API_KEY     else
        "⚠  NO AI KEY CONFIGURED"
    )
    tg_label = (
        f"chat {TELEGRAM_CHAT_ID}" if TELEGRAM_BOT_TOKEN else "⚠  not configured"
    )
    print("─" * width)
    print("  RegRadar MVP Core Pipeline  v2")
    print(f"  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    print(f"  DB:       {DB_PATH.resolve()}")
    print(f"  AI:       {ai_label}")
    print(f"  Telegram: {tg_label}")
    print(f"  Targets:  {len(TARGET_URLS)} URL(s)")
    print("─" * width)


async def _run_pipeline(url: str) -> str:
    """Execute all 5 steps for a single URL. Returns a final state string."""

    # ── Step 1: Ingest ──────────────────────────────────────────────
    content = await fetch_and_clean(url)

    # ── Step 2: Hash & store ────────────────────────────────────────
    log_init("Fingerprinting and storing…")
    state, old_content = upsert_document(url, content)

    if state == "NEW_DOCUMENT":
        log_ok("NEW_DOCUMENT — baseline fingerprinted and stored")
        return state

    if state == "NO_CHANGE":
        log_skip("SHA-256 hash unchanged — no action needed")
        return state

    # state == "DETECTED_DELTA"
    log_delta(f"Content changed  →  {url}")

    # ── Step 3: Paragraph diff ──────────────────────────────────────
    log_init("Computing paragraph-level diff…")
    delta = calculate_delta(old_content, content)

    if not delta:
        log_skip(
            "SHA changed but unified_diff found no semantic paragraph mutations "
            "— skipping AI step (whitespace / formatting-only change)"
        )
        return "DETECTED_DELTA_EMPTY_DIFF"

    log_ok(f"Delta: {len(delta):,} chars of meaningful change")
    preview = delta[:300].replace("\n", " ")
    print(f"    Preview: {preview}…")

    # ── Step 4: AI analysis ─────────────────────────────────────────
    log_init("Running AI compliance analysis…")
    analysis = analyze_compliance_delta(delta)
    risk     = analysis["risk_level"]
    summary  = analysis.get("executive_summary",        "")
    action   = analysis.get("business_action_required", "")
    log_ok(f"Analysis complete  →  risk_level={risk}")
    print(f"    Summary: {summary[:180]}")
    print(f"    Action:  {action[:180]}")

    # ── Step 5: Telegram ────────────────────────────────────────────
    log_init("Routing Telegram notification…")
    dispatch_telegram_alert(analysis, url)

    if risk in _ALERT_THRESHOLD:
        log_alert(f"{risk} RISK DELTA DISPATCHED  →  {url}")

    return f"DETECTED_DELTA:{risk}"


async def main() -> None:
    _banner()

    results: dict[str, str] = {}
    ok  = 0
    err = 0

    for url in TARGET_URLS:
        print()
        try:
            results[url]  = await _run_pipeline(url)
            ok           += 1

        except KeyboardInterrupt:
            log_warn("Interrupted by user (Ctrl+C)")
            sys.exit(0)

        except TimeoutError as exc:
            log_err(f"Timeout — {exc}")
            results[url] = "ERROR:TIMEOUT"
            err         += 1

        except json.JSONDecodeError as exc:
            log_err(f"AI returned invalid JSON — {exc}")
            results[url] = "ERROR:BAD_JSON"
            err         += 1

        except requests.HTTPError as exc:
            log_err(f"Telegram API error — {exc}")
            results[url] = "ERROR:TELEGRAM"
            err         += 1

        except RuntimeError as exc:
            log_err(str(exc))
            results[url] = "ERROR:CONFIG"
            err         += 1

        except Exception as exc:
            log_err(f"{type(exc).__name__}: {exc}")
            results[url] = f"ERROR:{type(exc).__name__}"
            err         += 1

    # ── Summary report ───────────────────────────────────────────────
    width = 66
    print()
    print("─" * width)
    print("  PIPELINE SUMMARY")
    print("─" * width)
    for u, s in results.items():
        short = u.replace("https://", "").rstrip("/")[:50]
        print(f"  {s:<34}  {short}")
    print("─" * width)
    print(
        f"  Completed: {ok+err} URL(s)  |  OK: {ok}  |  Errors: {err}"
    )
    print("─" * width)

    sys.exit(0 if err == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
