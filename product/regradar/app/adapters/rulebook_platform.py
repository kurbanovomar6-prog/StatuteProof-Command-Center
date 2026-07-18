"""
Rulebook-platform adapter — DFSA (dfsaen.thomsonreuters.com) and VARA
(rulebooks.vara.ae) shared Drupal "rulebook" theme.

Why this adapter exists
-----------------------
Both platforms serve rulebook MODULE pages as a navigation/TOC node: the
static HTML carries the site tree, version history and PDF links, while the
rule text itself lives on per-section child pages (DFSA) or behind an
"Entire section" view (VARA). The generic two-tier scraper accepts the
static shell (its visible text exceeds the low-content threshold), so the
pipeline hashed navigation chrome — the 2026-06/07 NAV_SHELL_ONLY failures
on AE-dfsa-aml-rulebook-module.

What it extracts (deterministic, static fetch only, no Playwright, no LLM)
--------------------------------------------------------------------------
1. The configured page's content region: version history / effective-from
   markers / section TOC — whatever the node serves.
2. The module's OWN current-version link from the book-navigation tree
   (matched by URL-path prefix, so other modules' version tags can never
   fire a change on this source).
3. The "Entire section" view when it is server-rendered (VARA: full
   rulebook text incl. the AML/CFT part). When that view is a JS shell
   (DFSA), it falls back to the current-version page's section TOC.
4. The version-history PDF links (sorted) — a new row appears exactly when
   an amendment takes effect.

A change alert therefore fires on: new version tag, changed section
structure, changed full text (VARA), or a new PDF version row — and NOT on
site-wide navigation noise.

Opt-in contract
---------------
can_handle() requires source["adapter_name"] == "rulebook_platform" AND an
allowlisted host. Bare-URL runs (source=None) and every existing source
keep their current fetch path untouched.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlsplit

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

# Hosts running the shared rulebook platform. Extend deliberately — every
# new host must be verified to serve the same Drupal theme blocks.
_ALLOWED_HOSTS = (
    "dfsaen.thomsonreuters.com",
    "rulebooks.vara.ae",
)

# Toolbar/breadcrumb boilerplate rendered inside the content region on every
# page of the platform. Dropped so the hash never moves on chrome tweaks.
_BOILERPLATE_LINES = {
    "entire section",
    "custom print",
    "link",
    "text only",
    "rich text",
    "print",
    "location:",
    "breadcrumb",
    "versions",
    "download",
    "view current pdf",
}

# The "Entire section" view is server-rendered on VARA (full rulebook text)
# but a JS shell on DFSA. Only accept it when it clearly carries substance.
# Per-source override: adapter_config.entire_section_min_chars — some nodes
# (e.g. the DFSA current consultation-papers listing) are legitimately small
# but fully server-rendered; the override is read ONLY from the opted-in
# source's own config, so every existing source keeps the 3000-char default
# and a byte-identical output.
_MIN_ENTIRE_SECTION_CHARS = 3000
# Floor for the override: below this a page is indistinguishable from the
# DFSA JS shell, which the default threshold exists to reject.
_MIN_ENTIRE_SECTION_FLOOR = 600


def _entire_section_min_chars(source: dict | None) -> int:
    config = (source or {}).get("adapter_config")
    if not isinstance(config, dict):
        return _MIN_ENTIRE_SECTION_CHARS
    raw = config.get("entire_section_min_chars")
    if raw is None:
        return _MIN_ENTIRE_SECTION_CHARS
    try:
        value = int(raw)
    except (TypeError, ValueError):
        logger.warning(
            "rulebook_platform: non-integer entire_section_min_chars %r "
            "on source %r — using default",
            raw, (source or {}).get("source_id"),
        )
        return _MIN_ENTIRE_SECTION_CHARS
    return max(value, _MIN_ENTIRE_SECTION_FLOOR)

# Reject the final document when it is too thin to be a meaningful
# version/structure snapshot (shell page, blocked page, moved node).
_MIN_DOCUMENT_CHARS = 900

_WS_RE = re.compile(r"[ \t\xa0]+")


def _host_of(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def _clean_lines(text: str) -> list[str]:
    """Collapse whitespace per line, drop empties, boilerplate and
    immediate duplicates (nav trees repeat section titles)."""
    lines: list[str] = []
    for raw in text.split("\n"):
        line = _WS_RE.sub(" ", raw).strip()
        if not line or len(line) <= 1:  # pager arrows ‹ › etc.
            continue
        if line.lower() in _BOILERPLATE_LINES:
            continue
        if lines and lines[-1] == line:
            continue
        lines.append(line)
    return lines


def _soup(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup


class RulebookPlatformAdapter(SourceAdapter):
    """Version/structure/full-text monitor for the shared rulebook platform."""

    name = "rulebook_platform"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        # Strict opt-in: never engage unless the source entry explicitly
        # names this adapter — protects every existing source's baseline.
        if not source or source.get("adapter_name") != self.name:
            return False
        return _host_of(url) in _ALLOWED_HOSTS

    # ── fetch helpers ─────────────────────────────────────────────────────

    def _get(self, url: str) -> str | None:
        return fetch_text_bounded(
            url,
            headers=_HEADERS,
            timeout=HTTP_TIMEOUT_S,
            label="RulebookPlatformAdapter",
            proxy=proxy_for_url(url),
        )

    def _same_host_abs(self, page_url: str, href: str) -> str | None:
        """Absolutize ``href`` and confine follow-up fetches to the source
        host — the adapter must never wander cross-domain."""
        absolute = urljoin(page_url, href)
        if _host_of(absolute) != _host_of(page_url):
            return None
        return absolute

    # ── extraction pieces ─────────────────────────────────────────────────

    @staticmethod
    def _content_region(soup: BeautifulSoup):
        main = soup.select_one("main") or soup.body
        if main is None:
            return None
        return main.select_one(".region-content") or main

    @staticmethod
    def _current_version_anchor(soup: BeautifulSoup, page_url: str):
        """The module's OWN current-version link from the book-navigation
        tree: href == <configured path> + '-ver…'. Path-prefix matching
        means other modules' version tags can never fire this source."""
        nav = soup.select_one("#block-rulebook-booknavigation")
        if nav is None:
            return None
        base_path = urlsplit(page_url).path.rstrip("/")
        if not base_path:
            return None
        prefix = base_path + "-ver"
        for anchor in nav.find_all("a", href=True):
            try:
                href_path = urlsplit(anchor["href"]).path
            except ValueError:
                continue
            if href_path.startswith(prefix):
                return anchor
        return None

    @staticmethod
    def _entire_section_href(region) -> str | None:
        for anchor in region.find_all("a", href=True):
            if anchor.get_text(" ", strip=True).strip().lower() == "entire section":
                return anchor["href"]
        return None

    def _entire_section_text(
        self, page_url: str, href: str, min_chars: int = _MIN_ENTIRE_SECTION_CHARS,
    ) -> str | None:
        target = self._same_host_abs(page_url, href)
        if target is None:
            return None
        html = self._get(target)
        if html is None:
            return None
        soup = _soup(html)
        block = soup.select_one("#block-rulebook-content")
        if block is None:
            block = self._content_region(soup)
        if block is None:
            return None
        text = "\n".join(_clean_lines(block.get_text("\n", strip=True)))
        if len(text) < min_chars:
            # JS shell (DFSA) — not usable as content.
            logger.info(
                "RulebookPlatformAdapter: entire-section view is a shell "
                "(%d chars) for %s — falling back", len(text), target,
            )
            return None
        return text

    def _version_page_toc(self, page_url: str, href: str) -> str | None:
        target = self._same_host_abs(page_url, href)
        if target is None:
            return None
        html = self._get(target)
        if html is None:
            return None
        region = self._content_region(_soup(html))
        if region is None:
            return None
        text = "\n".join(_clean_lines(region.get_text("\n", strip=True)))
        return text or None

    @staticmethod
    def _pdf_version_lines(region, page_url: str) -> list[str]:
        seen: set[str] = set()
        rows: list[str] = []
        for anchor in region.select('a[href*="net_file_store"]'):
            href = urljoin(page_url, anchor["href"])
            if href in seen:
                continue
            seen.add(href)
            rows.append(href)
        rows.sort()
        return rows

    # ── main entry point ──────────────────────────────────────────────────

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        try:
            return self._fetch_content_inner(url, source)
        except Exception as exc:  # contract: never raise
            logger.warning(
                "RulebookPlatformAdapter unexpected error for %s: %s: %s",
                url, type(exc).__name__, exc,
            )
            return None

    def _fetch_content_inner(self, url: str, source: dict | None = None) -> str | None:
        html = self._get(url)
        if html is None:
            logger.warning("RulebookPlatformAdapter: fetch failed for %s", url)
            return None

        soup = _soup(html)
        region = self._content_region(soup)
        if region is None:
            logger.warning("RulebookPlatformAdapter: no content region for %s", url)
            return None

        blocks: list[str] = [
            "Official rulebook version monitor",
            f"Source page: {url}",
        ]

        # 1. Module's own current-version marker from the navigation tree.
        current_anchor = self._current_version_anchor(soup, url)
        current_href: str | None = None
        if current_anchor is not None:
            label = _WS_RE.sub(" ", current_anchor.get_text(" ", strip=True)).strip()
            current_href = self._same_host_abs(url, current_anchor["href"])
            if label:
                blocks.append(f"Current version: {label}")
            if current_href:
                blocks.append(f"Current version URL: {current_href}")

        # 2. The configured page's own content (version history / effective
        #    dates / TOC — whatever this node serves statically).
        region_lines = _clean_lines(region.get_text("\n", strip=True))
        if region_lines:
            blocks.append("Rulebook page content:\n" + "\n".join(region_lines))

        # 3. Full text via the server-rendered entire-section view (VARA),
        #    else the current-version page's section structure (DFSA).
        entire_href = self._entire_section_href(region)
        entire_text = (
            self._entire_section_text(
                url, entire_href, min_chars=_entire_section_min_chars(source),
            )
            if entire_href
            else None
        )
        if entire_text:
            blocks.append("Full rulebook text (entire section view):\n" + entire_text)
        elif current_href and urlsplit(current_href).path != urlsplit(url).path:
            toc = self._version_page_toc(url, current_href)
            if toc:
                blocks.append("Current version structure:\n" + toc)

        # 4. Version-history document links: a new row == a new version.
        pdf_rows = self._pdf_version_lines(region, url)
        if pdf_rows:
            blocks.append("Document versions:\n" + "\n".join(pdf_rows))

        document = "\n\n".join(blocks)
        if len(document) < _MIN_DOCUMENT_CHARS:
            logger.warning(
                "RulebookPlatformAdapter: document too thin (%d chars) for %s "
                "— treating as extraction failure, not content",
                len(document), url,
            )
            return None
        return document
