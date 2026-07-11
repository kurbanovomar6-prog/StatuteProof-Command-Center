"""
RegRadar v8 — Smart Source Onboarding.

Public API
----------
validate_public_url(url)   → (bool, str)   SSRF-safe URL validation; no network calls.
test_source_url(url)       → dict           Full extraction diagnostic.
source_url_exists(url)     → bool           Check sources.json for duplicate URL.
append_source_to_json(src) → bool           Safely append a new source to sources.json.

Constraints
-----------
• No AI calls.
• No Telegram calls.
• No DB writes.
• URL safety is validated before any HTTP request is made.
"""

from __future__ import annotations

import fcntl
import ipaddress
import json
import logging
import os
import socket
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.adapters.base import fetch_text_bounded_status
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA
from app.extractors import extract_best_text
from app.scraper import _fetch_via_playwright, is_low_content_html

logger = logging.getLogger(__name__)

# ── paths ─────────────────────────────────────────────────────────────────────

_SOURCES_PATH = Path(__file__).parent.parent / "sources.json"

# ── extraction quality thresholds ─────────────────────────────────────────────

_GOOD_CHARS = 1_000   # ≥ this → "good"
_LOW_CHARS  =   100   # ≥ this (but < _GOOD_CHARS) → "low_content"
                      # < this → "failed"

# ── URL safety ────────────────────────────────────────────────────────────────

_BLOCKED_HOSTNAMES: frozenset[str] = frozenset({
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "broadcasthost",
})


def _is_non_public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True for any address that must not be reached over the public internet."""
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_multicast
    )


def validate_public_url(url: str) -> tuple[bool, str]:
    """
    Validate `url` is safe to fetch — blocks SSRF vectors.

    Validation order (no HTTP requests made here):
      1. URL is non-empty.
      2. Scheme is http or https (rejects file://, ftp://, data:, etc.).
      3. Hostname is present.
      4. Hostname is not a known loopback alias (localhost, etc.).
      5. If hostname is a bare IP → checked against private/reserved/loopback ranges.
      6. If hostname is a domain → DNS-resolved; all returned IPs are checked.
         Unresolvable domains are allowed — the HTTP request will fail naturally.

    Returns
    -------
    (True, "URL is safe") on success.
    (False, reason_string) on rejection.
    """
    if not url or not url.strip():
        return False, "URL is empty"

    url = url.strip()

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Malformed URL — could not parse"

    if parsed.scheme not in ("http", "https"):
        scheme = parsed.scheme or (url.split(":")[0] if ":" in url else url)
        return False, (
            f"Scheme {scheme!r} is not allowed; "
            "only http:// and https:// are accepted"
        )

    # urlparse lowercases the hostname and strips IPv6 brackets
    host = parsed.hostname
    if not host:
        return False, "URL has no hostname"

    if parsed.username or parsed.password:
        return False, "URLs with embedded credentials are not allowed"

    if host in _BLOCKED_HOSTNAMES:
        return False, f"Hostname {host!r} is a loopback / internal address"

    # Bare IP address in the URL
    try:
        ip_obj = ipaddress.ip_address(host)
        if _is_non_public(ip_obj):
            return False, f"IP address {host} is not a public routable address"
        return True, "URL is safe"
    except ValueError:
        pass  # Not a bare IP — treat as a domain name

    # Resolve domain and check every returned IP
    try:
        for _fam, _typ, _proto, _cname, sockaddr in socket.getaddrinfo(host, None):
            resolved = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(resolved)
                if _is_non_public(ip_obj):
                    return False, (
                        f"Hostname {host!r} resolves to non-public IP {resolved}"
                    )
            except ValueError:
                continue  # skip non-parseable entries
    except socket.gaierror:
        pass  # DNS lookup failed — allow; HTTP request will fail cleanly

    return True, "URL is safe"


# ── link counter ──────────────────────────────────────────────────────────────

def _count_links(html: str, base_url: str) -> int:
    """
    Return the count of unique valid HTTP(S) href links found in `html`.

    Only counts, never fetches.  Relative URLs are normalised against
    `base_url`.  Fragment-only, javascript:, mailto:, and data: hrefs
    are excluded.
    """
    if not html:
        return 0

    soup = BeautifulSoup(html, "html.parser")
    seen:  set[str] = set()
    count: int      = 0

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(
            ("#", "javascript:", "mailto:", "tel:", "data:")
        ):
            continue
        try:
            full = urljoin(base_url, href)
            p    = urlparse(full)
            if p.scheme in ("http", "https") and p.netloc and full not in seen:
                seen.add(full)
                count += 1
        except Exception:
            continue

    return count


# ── verdict builder ───────────────────────────────────────────────────────────

def _build_verdict(
    url:             str,
    safe_url:        bool,
    http_status:     int | None,
    extracted_chars: int,
    links_found:     int,
    actual_method:   str,
    fetch_ok:        bool,
) -> dict:
    """Map extraction metrics to the standardised diagnostic result dict."""

    # Complete fetch failure
    if not fetch_ok:
        return {
            "url":                  url,
            "safe_url":             safe_url,
            "status":               "failed",
            "http_status":          http_status,
            "extracted_chars":      0,
            "links_found":          links_found,
            "extraction_quality":   "failed",
            "recommended_status":   "disabled",
            "recommended_enabled":  False,
            "recommended_method":   "failed",
            "verdict":              "cannot_monitor",
            "reason": (
                "Page could not be fetched (network error, complete block, "
                "or unsupported content type)."
            ),
        }

    if extracted_chars >= _GOOD_CHARS:
        quality    = "good"
        rec_status = "active"
        rec_en     = True
        # actual_method tracks whether requests or Playwright produced the content
        rec_method = actual_method if actual_method in ("generic", "playwright") else "generic"
        verdict    = "can_monitor"
        reason     = (
            f"Extracted {extracted_chars:,} chars — "
            "sufficient for reliable generic monitoring."
        )

    elif extracted_chars >= _LOW_CHARS:
        quality    = "low_content"
        rec_status = "limited"
        rec_en     = False
        rec_method = "needs_adapter"
        verdict    = "needs_adapter"
        reason     = (
            f"Extracted only {extracted_chars:,} chars — "
            f"below the monitoring threshold ({_GOOD_CHARS:,}). "
            "A custom source adapter may improve extraction quality."
        )

    else:
        quality    = "failed"
        rec_status = "disabled"
        rec_en     = False
        rec_method = "failed"
        verdict    = "cannot_monitor"
        reason     = (
            f"Extracted only {extracted_chars:,} chars — "
            "too little for reliable monitoring. "
            "The site may be heavily JS-rendered, behind a paywall, "
            "or protected by a bot filter."
        )

    return {
        "url":                  url,
        "safe_url":             safe_url,
        "status":               "ok",
        "http_status":          http_status,
        "extracted_chars":      extracted_chars,
        "links_found":          links_found,
        "extraction_quality":   quality,
        "recommended_status":   rec_status,
        "recommended_enabled":  rec_en,
        "recommended_method":   rec_method,
        "verdict":              verdict,
        "reason":               reason,
    }


# ── main diagnostic entry point ───────────────────────────────────────────────

def test_source_url(
    url: str,
    include_documents: bool = False,
    include_text: bool = False,
) -> dict:
    """
    Run a full extraction diagnostic on `url`.

    Safe for any user-supplied URL — SSRF validation runs before the first
    network call.  No AI, no Telegram, no DB writes.

    Flow
    ----
    1. validate_public_url()          — reject dangerous URLs immediately
    2. fetch_text_bounded_status()    — Tier 1; SSRF-guarded per-hop, captures
                                        http_status + HTML
    3. is_low_content_html()          — decide whether to escalate to Playwright
    4. _fetch_via_playwright()  — Tier 2 fallback when Tier 1 is insufficient
    5. _count_links()           — count href links for diagnostics
    6. extract_text()           — measure clean extracted chars
    7. _build_verdict()         — map metrics to standardised result
    8. extract_documents_from_page()  — optional, when include_documents=True

    Parameters
    ----------
    include_documents : bool
        When True, discover and extract up to 3 PDF links from the page.
        Adds ``document_info`` key to the result dict.
    include_text : bool
        When True, include the extracted page text for hashing/report evidence.

    Returns
    -------
    dict with keys:
        url, safe_url, status, http_status, extracted_chars, links_found,
        extraction_quality, recommended_status, recommended_enabled,
        recommended_method, verdict, reason
        [+ document_info when include_documents=True]
    """
    # ── 1. Safety validation (no network calls yet) ───────────────────
    safe, safety_msg = validate_public_url(url)
    if not safe:
        return {
            "url":                  url,
            "safe_url":             False,
            "status":               "failed",
            "http_status":          None,
            "extracted_chars":      0,
            "links_found":          0,
            "extraction_quality":   "failed",
            "recommended_status":   "disabled",
            "recommended_enabled":  False,
            "recommended_method":   "failed",
            "verdict":              "cannot_monitor",
            "reason":               f"URL failed safety validation: {safety_msg}",
        }

    # ── 2. Tier 1 — SSRF-guarded bounded fetch ───────────────────────
    # Routes through app.adapters.base.fetch_text_bounded_status, which
    # follows redirects MANUALLY, re-validates and IP-pins every hop before
    # connecting, and caps the decompressed body at 10 MB. This URL is
    # user-supplied via the authenticated /api source-test endpoint, so a
    # one-shot validate_public_url() check (kept above as defence-in-depth)
    # is not enough — a live DNS-rebind or a 30x redirect toward a
    # private/loopback/metadata address must be refused per-hop. The helper
    # never raises: it returns (status, text) where text is None on any
    # failure, non-200 status, oversized body, or an SSRF-blocked hop.
    status, tier1_html = fetch_text_bounded_status(
        url,
        headers={
            "User-Agent":      REQUESTS_UA,
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        },
        timeout=HTTP_TIMEOUT_S,
        label="test_source",
    )
    http_status: int | None = status
    if tier1_html is None:
        if status is None:
            logger.info(
                "test_source: Tier 1 fetch failed or blocked for %s — will try Playwright",
                url,
            )
            print(
                "  Tier 1 (guarded fetch) failed or blocked — escalating to Playwright",
                flush=True,
            )
        else:
            logger.info("test_source: Tier 1 HTTP %d for %s", status, url)

    # ── 3. Evaluate Tier 1 quality; escalate to Playwright if needed ──
    raw_html:      str | None = None
    actual_method: str        = "failed"

    if tier1_html and not is_low_content_html(tier1_html):
        raw_html      = tier1_html
        actual_method = "generic"
    else:
        if tier1_html:
            print(
                f"  Tier 1 rejected (low visible content < 500 chars) "
                f"— Playwright fallback triggered",
                flush=True,
            )
        try:
            raw_html      = _fetch_via_playwright(url)
            actual_method = "playwright"
        except Exception as pw_exc:
            logger.warning(
                "test_source: Playwright failed: %s: %s",
                type(pw_exc).__name__, pw_exc,
            )
            if tier1_html:
                # Best-effort: Tier 1 HTML despite low quality
                raw_html      = tier1_html
                actual_method = "generic"
            # else: raw_html stays None → fetch_ok=False

    # ── 4. Count links ────────────────────────────────────────────────
    links_found = _count_links(raw_html or "", url)

    # ── 5. Extract and measure clean text ────────────────────────────
    extraction_candidates:    list[dict] = []
    extraction_method_detail: str        = "none"
    extracted_chars: int                 = 0

    if raw_html:
        _extr                    = extract_best_text(raw_html, url)
        extracted_chars          = _extr["extracted_chars"]
        extraction_candidates    = _extr["candidates"]
        extraction_method_detail = _extr["method"]
        extracted_text           = _extr.get("text", "")
    else:
        extracted_text           = ""

    # ── 6. Build and return verdict ───────────────────────────────────
    verdict = _build_verdict(
        url             = url,
        safe_url        = True,
        http_status     = http_status,
        extracted_chars = extracted_chars,
        links_found     = links_found,
        actual_method   = actual_method,
        fetch_ok        = raw_html is not None,
    )
    verdict["extraction_candidates"]    = extraction_candidates
    verdict["extraction_method_detail"] = extraction_method_detail
    verdict["fetch_method"]             = actual_method

    if raw_html:
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            title = soup.find("title")
            verdict["title"] = title.get_text(" ", strip=True) if title else None
        except Exception:
            verdict["title"] = None
    else:
        verdict["title"] = None

    if include_text:
        verdict["extracted_text"] = extracted_text

    # ── 7. Optional document extraction ──────────────────────────────────
    if include_documents and raw_html:
        try:
            from app.document_extractor import extract_documents_from_page
            verdict["document_info"] = extract_documents_from_page(
                raw_html, url, max_docs=3,
            )
        except Exception as exc:
            logger.warning("test_source_url: document extraction error: %s", exc)
            verdict["document_info"] = {"error": str(exc)}

    return verdict


# ── sources.json helpers ──────────────────────────────────────────────────────

def source_url_exists(url: str) -> bool:
    """
    Return True when `url` already exists in sources.json.

    URL comparison is normalised (trailing slash stripped on both sides).
    Returns False on any read/parse error — never raises.
    """
    norm = url.rstrip("/")
    try:
        raw     = _SOURCES_PATH.read_text(encoding="utf-8")
        entries = json.loads(raw)
        return any(
            isinstance(e, dict) and e.get("url", "").rstrip("/") == norm
            for e in entries
        )
    except Exception:
        return False


def append_source_to_json(source: dict) -> bool:
    """
    Append `source` to sources.json atomically and race-safely.

    - Holds an exclusive advisory lock (``fcntl.flock``) across the whole
      read-modify-write, so a concurrent add cannot interleave between the
      duplicate check and the write. This closes the read-then-write TOCTOU that
      a bare ``read_text`` / ``write_text`` pair left open (two adds racing could
      both pass the duplicate check and one could clobber the other's row).
    - Rejects a duplicate by URL *or* by ``source_id`` — uniqueness is enforced
      on both keys, not just URL, so a second row can never shadow, collide with,
      or silently duplicate an existing source_id.
    - Publishes the new contents via a temp file + atomic ``os.replace`` under the
      lock, so a concurrent reader never observes a half-written file.

    Returns True on success, False on any error or duplicate.  Never raises.
    """
    url = source.get("url", "").rstrip("/")
    source_id = str(source.get("source_id") or "").strip()

    try:
        _SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
        # ``r+`` requires the file to exist; seed an empty array if it is missing
        # so the locked read-modify-write below has something to open.
        if not _SOURCES_PATH.exists():
            _SOURCES_PATH.write_text("[]\n", encoding="utf-8")

        with _SOURCES_PATH.open("r+", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                raw = fh.read()
                entries = json.loads(raw) if raw.strip() else []

                if not isinstance(entries, list):
                    logger.error(
                        "append_source_to_json: sources.json top level is not a list"
                    )
                    return False

                # Duplicate guard on BOTH url and source_id. TOCTOU-safe: we hold
                # the exclusive lock across this check and the write below.
                for e in entries:
                    if not isinstance(e, dict):
                        continue
                    if url and e.get("url", "").rstrip("/") == url:
                        logger.warning(
                            "append_source_to_json: duplicate URL %r — not added", url
                        )
                        return False
                    if source_id and str(e.get("source_id") or "").strip() == source_id:
                        logger.warning(
                            "append_source_to_json: duplicate source_id %r — not added",
                            source_id,
                        )
                        return False

                entries.append(source)

                # Atomic publish: write a sibling temp file, fsync, then rename
                # over the original inode while still holding the lock.
                tmp = _SOURCES_PATH.with_name(_SOURCES_PATH.name + ".tmp")
                with tmp.open("w", encoding="utf-8") as out:
                    out.write(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(tmp, _SOURCES_PATH)
                logger.info("append_source_to_json: added %r to sources.json", url)
                return True
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)

    except Exception as exc:
        logger.error(
            "append_source_to_json: %s: %s", type(exc).__name__, exc
        )
        return False
