"""
XML feed adapter — opt-in monitor for machine-readable official feeds
(RSS 2.0 / RSS 1.0 RDF / Atom) and the UN Security Council consolidated
sanctions list XML.

Why this adapter exists
-----------------------
The generic two-tier scraper is HTML-shaped: ``is_low_content_html()``
measures text inside semantic HTML tags (p/h1/li/td/...), which an XML
feed simply does not have, so Tier 1 is always rejected and the fetch
escalates to Playwright — where Chromium either renders its XML-viewer
chrome (hashing viewer UI, not feed content: the 266-char UAE-FIU runs)
or aborts on a download-attachment redirect (the UN list 302s to a signed
Azure blob served as an attachment). The 2026-07 candidate sweep showed
both failure shapes: FAILED/0 chars (UN, BIS) and low_content (UAE FIU).

What it extracts (deterministic, requests-only, no Playwright, no LLM)
----------------------------------------------------------------------
* RSS/Atom feeds → one line per item: ``title | date | link``, sorted by
  link (feed servers reorder by date between runs; link slugs are stable
  once published — same guarantee FCARSSAdapter relies on), deduplicated,
  capped at ``_MAX_ITEMS``.
* UN CONSOLIDATED_LIST → a structured summary: per-kind entry counts, a
  SHA-256 digest over every entry's stable identity row
  (``DATAID|VERSIONNUM|REFERENCE_NUMBER|LISTED_ON|last-updated``), and a
  bounded "most recently updated entries" listing so a digest change
  always ships a human-readable diff excerpt. The root ``dateGenerated``
  attribute is EXCLUDED on purpose: it moves on every regeneration even
  when no entry changed, and hashing it would alert on nothing. The
  normalized output changes exactly when the entry set changes (add /
  remove / re-version / re-date) — never on regeneration noise, and never
  as a 2.2 MB full-text diff.

Opt-in contract
---------------
can_handle() requires source["adapter_name"] == "xml_feed" AND an
allowlisted host. Bare-URL runs (source=None) and every existing source
keep their current fetch path untouched.
"""

from __future__ import annotations

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from app.adapters.base import (
    MAX_FETCH_BYTES,
    SourceAdapter,
    fetch_bytes_bounded,
)
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": REQUESTS_UA,
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.5",
    "Accept-Language": "en-US,en;q=0.9",
}

# Hosts allowed to opt in. Extend deliberately — every new host must be a
# verified official feed endpoint. Matching is exact-or-subdomain.
_ALLOWED_HOSTS = (
    "scsanctions.un.org",
    "bis.org",
    "uaefiu.gov.ae",
    "webgate.ec.europa.eu",
)

# Bounded output: feeds are capped per item count and per field length so a
# runaway feed can never bloat snapshots or diffs.
_MAX_ITEMS = 100
_MAX_FIELD_CHARS = 300

# UN list: how many most-recently-updated entries to render as the
# human-readable excerpt next to the digest.
_UN_RECENT_ENTRIES = 30

_WS_RE = re.compile(r"\s+")

# Entity-expansion guard: a DOCTYPE (and therefore any ENTITY declaration)
# has no business in an official feed payload; refusing it outright closes
# billion-laughs / external-entity tricks without needing defusedxml. The
# WHOLE buffer is scanned (not a prefix): XML permits arbitrary comments and
# processing-instructions in the prolog BEFORE the DOCTYPE, so a >4KB comment
# would legally push a billion-laughs DOCTYPE past any bounded prefix window
# and reach ET.fromstring() unfiltered (security review, 2026-07-18). The
# buffer is already capped at ≤10MB by fetch_bytes_bounded, so a full
# substring scan costs milliseconds.


def _host_of(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def _host_allowed(host: str) -> bool:
    return any(host == h or host.endswith("." + h) for h in _ALLOWED_HOSTS)


def _clean(text: str | None) -> str:
    return _WS_RE.sub(" ", text or "").strip()[:_MAX_FIELD_CHARS]


def _local(tag: object) -> str:
    """Namespace-free, lowercased element tag name."""
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].lower()


class XmlFeedAdapter(SourceAdapter):
    """Deterministic monitor for official XML feeds (opt-in per source)."""

    name = "xml_feed"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        # Strict opt-in: never engage unless the source entry explicitly
        # names this adapter — protects every existing source's baseline.
        if not source or source.get("adapter_name") != self.name:
            return False
        return _host_allowed(_host_of(url))

    # ── main entry point ──────────────────────────────────────────────────

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:  # noqa: ARG002
        try:
            return self._fetch_content_inner(url)
        except Exception as exc:  # contract: never raise
            logger.warning(
                "XmlFeedAdapter unexpected error for %s: %s: %s",
                url, type(exc).__name__, exc,
            )
            return None

    def _fetch_content_inner(self, url: str) -> str | None:
        data = fetch_bytes_bounded(
            url,
            headers=_HEADERS,
            timeout=HTTP_TIMEOUT_S,
            max_bytes=MAX_FETCH_BYTES,
            label="XmlFeedAdapter",
        )
        # NOTE on redirects: fetch_bytes_bounded follows redirects with the
        # per-hop SSRF guard (the UN URL 302s to a signed Azure blob and is
        # vetted hop-by-hop). No egress proxy: none of the allowlisted feed
        # hosts are WAF-blocked, so these fetches are always direct+pinned.
        if data is None:
            logger.warning("XmlFeedAdapter: fetch failed for %s", url)
            return None

        text = self.parse_payload(data, url)
        if text is None:
            logger.warning("XmlFeedAdapter: no parseable feed content for %s", url)
        return text

    # ── parsing (pure, fixture-testable) ──────────────────────────────────

    @staticmethod
    def parse_payload(data: bytes, url: str) -> str | None:
        """Turn raw feed bytes into normalized monitor text. Never raises."""
        # Scan the ENTIRE bounded buffer — a DOCTYPE can be pushed arbitrarily
        # deep by a legal prolog comment, so a prefix window is bypassable.
        if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
            logger.warning(
                "XmlFeedAdapter: refusing payload with DOCTYPE/ENTITY "
                "declaration from %s", url,
            )
            return None
        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            logger.warning("XmlFeedAdapter: XML parse error for %s: %s", url, exc)
            return None

        if _local(root.tag) == "consolidated_list":
            return XmlFeedAdapter._un_consolidated_text(root, url)
        return XmlFeedAdapter._feed_text(root, url)

    # ── UN consolidated sanctions list ────────────────────────────────────

    @staticmethod
    def _un_entry_rows(root: ET.Element) -> tuple[dict[str, int], list[tuple[str, ...]]]:
        """
        Collect one stable identity row per listed party.

        Row = (last_updated, reference, kind, display_name, listed_on,
        dataid, versionnum). last_updated is the lexicographic max of the
        entry's LAST_DAY_UPDATED/VALUE ISO dates ("" when never amended).
        """
        counts: dict[str, int] = {}
        rows: list[tuple[str, ...]] = []
        for kind, container_tag, entry_tag in (
            ("individual", "INDIVIDUALS", "INDIVIDUAL"),
            ("entity", "ENTITIES", "ENTITY"),
        ):
            container = root.find(container_tag)
            if container is None:
                continue
            entries = container.findall(entry_tag)
            counts[kind] = len(entries)
            for el in entries:
                dataid = _clean(el.findtext("DATAID"))
                version = _clean(el.findtext("VERSIONNUM"))
                ref = _clean(el.findtext("REFERENCE_NUMBER"))
                listed = _clean(el.findtext("LISTED_ON"))
                names = [
                    _clean(el.findtext(t))
                    for t in ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME")
                ]
                display = " ".join(n for n in names if n)
                updated_values = sorted(
                    _clean(v.text)
                    for upd in el.findall("LAST_DAY_UPDATED")
                    for v in upd.findall("VALUE")
                    if _clean(v.text)
                )
                last_updated = updated_values[-1] if updated_values else ""
                rows.append((last_updated, ref, kind, display, listed, dataid, version))
        return counts, rows

    @staticmethod
    def _un_consolidated_text(root: ET.Element, url: str) -> str | None:
        counts, rows = XmlFeedAdapter._un_entry_rows(root)
        if not rows:
            return None

        # Digest input: every entry's identity row, sorted — changes exactly
        # when an entry is added, removed, re-versioned, or re-dated.
        digest_rows = sorted(
            f"{dataid}|{version}|{ref}|{listed}|{updated}"
            for (updated, ref, _kind, _display, listed, dataid, version) in rows
        )
        digest = hashlib.sha256("\n".join(digest_rows).encode("utf-8")).hexdigest()

        # Human-readable excerpt: most recently amended entries first, with a
        # full deterministic tiebreak so equal dates can never reorder.
        recent = sorted(rows, key=lambda r: (r[0], r[1], r[5]), reverse=True)
        recent_lines = [
            f"{ref or '(no reference)'} | {kind} | {display or '(unnamed)'}"
            f" | listed {listed or '?'} | updated {updated or '(never)'}"
            f" | id {dataid} v{version}"
            for (updated, ref, kind, display, listed, dataid, version)
            in recent[:_UN_RECENT_ENTRIES]
        ]

        blocks = [
            "UN Security Council Consolidated Sanctions List — structured feed monitor\n"
            f"Source page: {url}",
            f"Individuals listed: {counts.get('individual', 0)}\n"
            f"Entities listed: {counts.get('entity', 0)}\n"
            f"Total entries: {len(rows)}",
            "Entry-set digest (sha256 over sorted id|version|reference|listed|updated rows):\n"
            + digest,
            f"Most recently updated entries (top {_UN_RECENT_ENTRIES}):\n"
            + "\n".join(recent_lines),
        ]
        return "\n\n".join(blocks)

    # ── RSS / RDF / Atom feeds ────────────────────────────────────────────

    @staticmethod
    def _feed_items(root: ET.Element) -> list[tuple[str, str, str]]:
        """(link, title, date) per item/entry, namespace-agnostic."""
        items: list[tuple[str, str, str]] = []
        seen: set[tuple[str, str]] = set()
        for el in root.iter():
            if _local(el.tag) not in ("item", "entry"):
                continue
            title = ""
            link = ""
            date = ""
            for child in el:
                local = _local(child.tag)
                text = _clean(child.text)
                if local == "title" and not title:
                    title = text
                elif local == "link" and not link:
                    # RSS: <link>text</link>; Atom: <link href="..."/>
                    link = text or _clean(child.get("href"))
                elif local in ("pubdate", "date", "updated", "published") and not date:
                    date = text
            if not title and not link:
                continue
            key = (link, title)
            if key in seen:
                continue
            seen.add(key)
            items.append((link, title, date))
        return items

    @staticmethod
    def _feed_title(root: ET.Element) -> str:
        for el in root.iter():
            local = _local(el.tag)
            if local in ("item", "entry"):
                break
            if local == "title":
                return _clean(el.text)
        return ""

    @staticmethod
    def _feed_text(root: ET.Element, url: str) -> str | None:
        items = XmlFeedAdapter._feed_items(root)
        if not items:
            return None
        # Sort by link, then title: feed servers reorder items by date
        # between runs; link slugs are immutable once published, so this is
        # the stability guarantee (same rationale as FCARSSAdapter).
        items.sort()
        items = items[:_MAX_ITEMS]
        lines = [
            f"{title or '(untitled)'} | {date or '(no date)'} | {link or '(no link)'}"
            for (link, title, date) in items
        ]
        title = XmlFeedAdapter._feed_title(root)
        blocks = [
            "Official feed monitor (RSS/Atom)\n"
            f"Source page: {url}",
            f"Feed title: {title or '(none)'}\n"
            f"Items captured: {len(lines)}",
            "Items (sorted by link):\n" + "\n".join(lines),
        ]
        return "\n\n".join(blocks)
