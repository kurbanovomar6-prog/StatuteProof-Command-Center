"""
HTML listing adapter — opt-in, requests-only extraction of a configured
content region (``adapter_config.content_selector``) from a static
official listing page.

Why this adapter exists
-----------------------
The monitoring pipeline's generic path (run_pipeline → fetch_page →
extract_best_text) ignores per-source ``content_selector`` config — that
config is only honored on the Source Lab intake path. For listing pages
whose real content is a small server-rendered region buried in heavy
site chrome, the generic path either hashes navigation noise or, worse,
escalates to Playwright and extracts whatever the rendered DOM variant
serves that day (OFAC recent-actions: 441-char low_content runs on prod
while the static HTML carried the full dated listing in
``.view-content`` all along; MENAFATF: 106-char category hub).

What it extracts (deterministic, static fetch only, no Playwright, no LLM)
--------------------------------------------------------------------------
The first-tier static HTML is fetched with the shared SSRF-guarded
helpers, the configured CSS selector is applied, and the selected
region's cleaned line text is returned. A selector miss or a too-thin
region returns None so the pipeline falls back to the generic scraper —
selector drift therefore degrades loudly (QUALITY_DROP / low_content in
the sweep) instead of silently hashing chrome.

Opt-in contract
---------------
can_handle() requires source["adapter_name"] == "html_listing" AND an
allowlisted host AND a non-empty adapter_config.content_selector. Bare
URL runs (source=None) and every existing source keep their current
fetch path untouched.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup  # type: ignore

from app.adapters.base import (
    SourceAdapter,
    fetch_text_bounded,
    proxy_for_url,
)
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": REQUESTS_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Hosts allowed to opt in. Extend deliberately — every new host must be
# verified to serve the listing server-side in the static HTML.
#
# adgm.com (added 2026-07-25, verified on a live fetch): the enforcement /
# alerts / judgments listings are fully server-rendered, but inside CUSTOM
# ELEMENTS (``<adgm-table-row>`` / ``<adgm-table-cell>``) rather than a
# ``<table>``, so the generic extractor sees only the page shell and the
# readiness gate scores the page NAV_SHELL_ONLY. A ``content_selector`` of
# ``adgm-table-row`` recovers the dated rows verbatim — verified against
# FSRA Regulatory Actions (11 rows incl. "08 Jan 2026 … Wealthface Limited"),
# FSRA Regulatory Alerts (40 rows), RA Regulatory Actions (11 rows incl.
# "26 Jan 2026" UBO fine) and ADGM Courts Judgments (11 rows incl.
# "20 Jul 2026 ADGMCFI-2020-020 NMC Healthcare"). No headless browser needed.
_ALLOWED_HOSTS = (
    "ofac.treasury.gov",
    "menafatf.org",
    "adgm.com",
    # Added 2026-07-25, each verified on a live fetch to serve its dated rows in
    # the static HTML:
    # main.un.org — the 1267/ISIL & Al-Qaida Committee press-release table
    #   (<table><tr>, 21 rows, "SC/16407 8 July 2026 … Committee Amends One
    #   Entry"). Committee designations and amendments drive screening duties.
    # cbben.thomsonreuters.com — the CBB (Bahrain) rulebook "View Updates"
    #   change-log (.view-content/.views-row, 10 rows over a 30-day window,
    #   "Amendments to the Customer Due Diligence and Suspicious Transactions
    #   Reporting Requirements_14 July 2026"). Change-logs are the highest-value
    #   shape: one page carries every dated amendment.
    "main.un.org",
    "cbben.thomsonreuters.com",
    # Added 2026-07-25. Both are the SAME Drupal "view_revision_updates" view as
    # the already-monitored cbben (CBB) / rulebooks.vara.ae / rulebook.centralbank.ae
    # change-logs — the highest-value page shape there is, because one page carries
    # every dated amendment instead of forcing a diff of a whole rulebook. Verified
    # on a live fetch through THIS adapter (.view-content), not from documentation:
    # dfsaen.thomsonreuters.com — 40 rows / 1,846 chars, e.g. "W1143/2026 — Globus
    #   Payments Limited (DIFC) | 22 July 2026" (waiver & modification notices) and
    #   "Consultation Paper No. 174 - Miscellaneous Changes | 09 July 2026".
    # qfcra-en.thomsonreuters.com — 40 rows / 2,317 chars, e.g. "GENE 8.1.1
    #   Introduction | 01 May 2026". NOTE: only the BARE URL works on this instance;
    #   ?f_days=on&changed=-30 day returns 200 with ZERO rows (its date filter
    #   accepts only the form's own options), so the row must not carry that param.
    "dfsaen.thomsonreuters.com",
    "qfcra-en.thomsonreuters.com",
    # moj.gov.ae (added 2026-07-25): the AML/CFT legislation page is server-rendered
    # in Bootstrap accordions (.accordion-item), which the generic extractor reads as
    # collapsed chrome. Verified: 5,254 chars covering Federal Decree-Law 10/2025
    # (AML), Cabinet Resolution 134/2025 (executive regulations) and Cabinet
    # Resolution 74/2020 (terrorist lists).
    "moj.gov.ae",
)

# Reject a selected region too thin to be a meaningful listing snapshot
# (selector drift, moved node, stripped page) — fall back loudly instead.
_MIN_REGION_CHARS = 300

_WS_RE = re.compile(r"[ \t\xa0]+")


def _host_of(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def _host_allowed(host: str) -> bool:
    return any(host == h or host.endswith("." + h) for h in _ALLOWED_HOSTS)


def _content_selector(source: dict | None) -> str:
    config = (source or {}).get("adapter_config")
    if not isinstance(config, dict):
        return ""
    return str(config.get("content_selector") or "").strip()


def _clean_lines(text: str) -> list[str]:
    """Collapse whitespace per line, drop empties and immediate duplicates."""
    lines: list[str] = []
    for raw in text.split("\n"):
        line = _WS_RE.sub(" ", raw).strip()
        if not line or len(line) <= 1:
            continue
        if lines and lines[-1] == line:
            continue
        lines.append(line)
    return lines


class HtmlListingAdapter(SourceAdapter):
    """Selector-scoped static listing monitor (opt-in per source)."""

    name = "html_listing"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        # Strict opt-in: never engage unless the source entry explicitly
        # names this adapter — protects every existing source's baseline.
        if not source or source.get("adapter_name") != self.name:
            return False
        if not _content_selector(source):
            return False
        return _host_allowed(_host_of(url))

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        try:
            return self._fetch_content_inner(url, source)
        except Exception as exc:  # contract: never raise
            logger.warning(
                "HtmlListingAdapter unexpected error for %s: %s: %s",
                url, type(exc).__name__, exc,
            )
            return None

    def _fetch_content_inner(self, url: str, source: dict | None) -> str | None:
        selector = _content_selector(source)
        if not selector:
            return None
        html = fetch_text_bounded(
            url,
            headers=_HEADERS,
            timeout=HTTP_TIMEOUT_S,
            label="HtmlListingAdapter",
            proxy=proxy_for_url(url),
        )
        if html is None:
            logger.warning("HtmlListingAdapter: fetch failed for %s", url)
            return None
        return self.extract(html, url, selector)

    # ── extraction (pure, fixture-testable) ──────────────────────────────

    @staticmethod
    def extract(html: str, url: str, selector: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        try:
            regions = soup.select(selector)
        except Exception as exc:
            logger.warning(
                "HtmlListingAdapter: bad selector %r for %s: %s",
                selector, url, exc,
            )
            return None
        if not regions:
            logger.warning(
                "HtmlListingAdapter: selector %r matched nothing at %s "
                "— possible selector drift, falling back",
                selector, url,
            )
            return None

        lines: list[str] = []
        for region in regions:
            lines.extend(_clean_lines(region.get_text("\n", strip=True)))
        content = "\n".join(lines)
        if len(content) < _MIN_REGION_CHARS:
            logger.warning(
                "HtmlListingAdapter: region too thin (%d chars) for %s "
                "— treating as extraction failure, not content",
                len(content), url,
            )
            return None

        blocks = [
            "Official listing monitor\n"
            f"Source page: {url}",
            f"Content selector: {selector}\n"
            f"Listing lines: {len(lines)}",
            "Listing content:\n" + content,
        ]
        return "\n\n".join(blocks)
