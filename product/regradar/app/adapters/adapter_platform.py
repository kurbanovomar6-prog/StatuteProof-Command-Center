"""Source Lab adapter families for official-source onboarding.

This module is deliberately small and dependency-light. It does not fetch pages;
it only turns already-fetched HTML into stable normalized text plus adapter
metadata. Fetch safety, evidence writing, nav-shell checks, and activation gates
remain owned by source_intake.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


ADAPTER_VERSION = "adapter-platform-1.0"
_SPACE_RE = re.compile(r"\s+")
_DATE_RE = re.compile(
    r"\b("
    r"\d{1,2}\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|"
    r"Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|"
    r"Dec|December)\s+\d{4}|"
    r"\d{4}|"
    r"\d{4}-\d{2}-\d{2}|"
    r"\d{1,2}/\d{1,2}/\d{4}"
    r")\b",
    re.IGNORECASE,
)
_DOCUMENT_EXT_RE = re.compile(r"\.(pdf|docx?|xlsx?)($|[?#])", re.IGNORECASE)
_DEFAULT_EXCLUDE_SELECTORS = ["script", "style", "noscript"]
_GENERIC_NAV_TITLES = {
    "home",
    "search",
    "contact",
    "contact us",
    "privacy",
    "privacy policy",
    "accessibility",
    "login",
    "services",
    "news",
}


@dataclass
class AdapterResult:
    text: str = ""
    adapter_family: str = ""
    adapter_name: str = ""
    adapter_version: str = ADAPTER_VERSION
    extraction_strategy: str = ""
    items: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    failure_reason: str = ""
    remediation_hint: str = ""
    noise_risk: str = "unknown"
    source_health_risk: str = "unknown"
    metadata: dict = field(default_factory=dict)

    @property
    def item_count(self) -> int:
        return len(self.items)

    def as_metadata(self) -> dict:
        return {
            "adapter_family": self.adapter_family,
            "adapter_name": self.adapter_name,
            "adapter_version": self.adapter_version,
            "extraction_strategy": self.extraction_strategy,
            "item_count": self.item_count,
            "warnings": self.warnings,
            "failure_reason": self.failure_reason,
            "remediation_hint": self.remediation_hint,
            "noise_risk": self.noise_risk,
            "source_health_risk": self.source_health_risk,
            "metadata": self.metadata,
        }


def _clean(value: str | None, *, limit: int | None = None) -> str:
    text = _SPACE_RE.sub(" ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _row_hash(*parts: str | None) -> str:
    payload = "|".join(_clean(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()[:16]


def _extract_date(text: str | None) -> str:
    matches = [match.group(1) for match in _DATE_RE.finditer(text or "")]
    if not matches:
        return ""
    rich_matches = [
        value for value in matches
        if any(ch.isalpha() for ch in value) or "/" in value or "-" in value
    ]
    return max(rich_matches or matches, key=len)


def _is_noise_title(title: str | None) -> bool:
    cleaned = _clean(title).lower()
    return not cleaned or cleaned in _GENERIC_NAV_TITLES or len(cleaned) < 4


def _soup(html: str, exclude_selectors: list[str] | None = None) -> BeautifulSoup:
    soup = BeautifulSoup(html or "", "html.parser")
    selectors = [*_DEFAULT_EXCLUDE_SELECTORS, *(exclude_selectors or [])]
    for selector in selectors:
        for node in soup.select(selector):
            node.decompose()
    return soup


def _node_text(node, *, separator: str = "\n", limit: int | None = None) -> str:
    return _clean(node.get_text(separator, strip=True) if node else "", limit=limit)


def _structured_node_text(node, *, limit: int | None = None) -> str:
    """Return monitorable block text while preserving heading/list boundaries."""
    if not node:
        return ""
    parts: list[str] = []
    for block in node.select("h1, h2, h3, h4, h5, h6, p, li, th, td, caption, dt, dd, blockquote"):
        text = _clean(block.get_text(" ", strip=True))
        if not text:
            continue
        if parts and (text == parts[-1] or text in parts[-1]):
            continue
        parts.append(text)
    if not parts:
        raw = node.get_text("\n", strip=True)
        parts = [_clean(line) for line in raw.splitlines() if _clean(line)]
    text = "\n".join(parts)
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _focus_text(text: str, config: dict | None = None) -> str:
    config = config or {}
    raw_keywords = config.get("focus_keywords") or config.get("focus_keyword") or []
    if isinstance(raw_keywords, str):
        keywords = [raw_keywords]
    elif isinstance(raw_keywords, list):
        keywords = [str(item) for item in raw_keywords if str(item).strip()]
    else:
        keywords = []
    if not keywords:
        return text
    lines = text.splitlines()
    lowered_keywords = [keyword.casefold() for keyword in keywords]
    for index, line in enumerate(lines):
        folded = line.casefold()
        if any(keyword in folded for keyword in lowered_keywords):
            return "\n".join(lines[index:]).strip()
    return text


class BaseHtmlAdapter:
    family = "static_html"
    name = "static_html"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        raise NotImplementedError

    def _empty(self, reason: str, hint: str) -> AdapterResult:
        return AdapterResult(
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            failure_reason=reason,
            remediation_hint=hint,
            source_health_risk="medium",
        )


class StaticHtmlAdapter(BaseHtmlAdapter):
    family = "static_html"
    name = "static_html"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        config = config or {}
        selector = str(config.get("content_selector") or config.get("selector") or "article, main").strip()
        soup = _soup(html, config.get("exclude_selectors") or ["header", "nav", "footer", "form", ".search"])
        node = soup.select_one(selector)
        if not node and "," in selector:
            for candidate in [part.strip() for part in selector.split(",") if part.strip()]:
                node = soup.select_one(candidate)
                if node:
                    selector = candidate
                    break
        if not node:
            node = soup.select_one("article") or soup.select_one("main") or soup.body
            selector = node.name if node else selector
        text = _focus_text(_structured_node_text(node), config)
        if not text:
            return self._empty("No static HTML content was isolated.", "Review content_selector or use a listing/table adapter.")
        return AdapterResult(
            text=text,
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            noise_risk="low" if len(text) >= 1000 else "medium",
            source_health_risk="low",
            metadata={"content_selector": selector, "url": url, "focus_keywords": config.get("focus_keywords") or config.get("focus_keyword") or []},
        )


class PlaywrightSelectorAdapter(StaticHtmlAdapter):
    family = "playwright_selector"
    name = "playwright_selector"


class CustomElementAdapter(BaseHtmlAdapter):
    family = "custom_element"
    name = "custom_element"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        config = config or {}
        selector = str(config.get("content_selector") or config.get("selector") or "").strip()
        if not selector:
            return self._empty("Missing content selector.", "Configure content_selector for the custom element.")

        soup = _soup(html, config.get("exclude_selectors"))
        node = soup.select_one(selector)
        if not node:
            return self._empty("Custom element selector was not found.", "Review wait/content selector with Playwright rendering.")

        text = _focus_text(_structured_node_text(node), config)
        if not text:
            return self._empty("Custom element selector returned empty text.", "Review rendered DOM and selector specificity.")

        return AdapterResult(
            text=text,
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            noise_risk="medium" if len(text) < 1000 else "low",
            source_health_risk="medium",
            metadata={"selector": selector, "url": url, "focus_keywords": config.get("focus_keywords") or config.get("focus_keyword") or []},
        )


class ListingAdapter(BaseHtmlAdapter):
    family = "listing"
    name = "listing"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        config = config or {}
        soup = _soup(html, config.get("exclude_selectors"))
        container_selector = str(config.get("container_selector") or "main").strip()
        container = soup.select_one(container_selector) if container_selector else soup
        warnings: list[str] = []
        if not container:
            warnings.append(f"Configured container_selector {container_selector!r} was not found; used body/main fallback.")
            container = soup.select_one("main") or soup.body or soup

        item_selector = str(config.get("item_selector") or "article, li, tr, .item, .card").strip()
        nodes = list(container.select(item_selector))
        if not nodes and container.name in {"article", "li", "tr", "div", "section", "main"}:
            nodes = [container]

        max_items = int(config.get("max_items") or 100)
        title_selector = str(config.get("title_selector") or "a, h1, h2, h3, h4").strip()
        date_selector = str(config.get("date_selector") or "").strip()
        url_selector = str(config.get("url_selector") or "a[href]").strip()
        category_selector = str(config.get("category_selector") or "").strip()
        items: list[dict] = []
        seen: set[str] = set()

        for node in nodes:
            title_node = node.select_one(title_selector) if title_selector else None
            url_node = node.select_one(url_selector) if url_selector else None
            if node.name == "a" and node.get("href"):
                if "a" in title_selector:
                    title_node = title_node or node
                if "a" in url_selector:
                    url_node = url_node or node
            date_node = node.select_one(date_selector) if date_selector else None
            category_node = node.select_one(category_selector) if category_selector else None
            title = _node_text(title_node, limit=240) or _node_text(node, limit=240)
            href = (url_node.get("href") if url_node else "") or ""
            item_url = urljoin(url, href.strip()) if href else ""
            date = _node_text(date_node, limit=80) if date_node else ""
            category = _node_text(category_node, limit=120) if category_node else ""
            context = _node_text(node, separator=" ", limit=700)

            if len(title) < int(config.get("min_title_chars") or 4):
                continue
            key = f"{title.lower()}|{item_url.lower()}|{date.lower()}"
            if key in seen:
                continue
            seen.add(key)
            item = {
                "title": title,
                "date": date,
                "url": item_url,
                "category": category,
                "raw_text_snippet": context,
            }
            item["row_hash"] = _row_hash(title, date, item_url, category)
            items.append(item)
            if len(items) >= max_items:
                break

        if bool(config.get("sort_items", True)):
            items.sort(key=lambda row: ((row.get("date") or ""), (row.get("title") or ""), (row.get("url") or "")))

        if not items:
            return self._empty("No listing items were isolated.", "Review item_selector/title_selector or treat source as remediation.")

        lines = ["Source listing items"]
        for item in items:
            lines.append(f"- Title: {item['title']}")
            if item.get("date"):
                lines.append(f"  Date: {item['date']}")
            if item.get("category"):
                lines.append(f"  Category: {item['category']}")
            if item.get("url"):
                lines.append(f"  URL: {item['url']}")
            lines.append(f"  Row hash: {item['row_hash']}")

        return AdapterResult(
            text="\n".join(lines).strip(),
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            items=items,
            warnings=warnings,
            noise_risk="medium" if len(items) < 5 else "low",
            source_health_risk="medium",
            metadata={
                "container_selector": container_selector,
                "item_selector": item_selector,
                "title_selector": title_selector,
                "url": url,
            },
        )


class TableAdapter(BaseHtmlAdapter):
    family = "table"
    name = "table"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        config = config or {}
        soup = _soup(html, config.get("exclude_selectors"))
        table_selector = str(config.get("table_selector") or "table").strip()
        table = soup.select_one(table_selector)
        if not table:
            return self._empty("Table selector was not found.", "Review table_selector or use a listing adapter.")

        rows = []
        for tr in table.select("tr"):
            cells = [_clean(cell.get_text(" ", strip=True)) for cell in tr.select("th, td")]
            cells = [cell for cell in cells if cell]
            if cells:
                rows.append(cells)
        if len(rows) < 2:
            return self._empty("Table did not contain enough rows.", "Review table structure or selector.")

        headers = rows[0]
        body_rows = rows[1:]
        if bool(config.get("sort_rows", False)):
            body_rows.sort(key=lambda row: " | ".join(row))

        items: list[dict] = []
        for row in body_rows:
            payload = dict(zip(headers, row, strict=False))
            payload["row_hash"] = _row_hash(*row)
            items.append(payload)

        lines = ["Source table", " | ".join(headers)]
        for row in body_rows:
            lines.append(" | ".join(row))

        return AdapterResult(
            text="\n".join(lines).strip(),
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            items=items,
            noise_risk="low" if len(items) >= 2 else "medium",
            source_health_risk="medium",
            metadata={"table_selector": table_selector, "url": url},
        )


class ScaListingAdapter(ListingAdapter):
    family = "sca_listing"
    name = "sca_listing"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        incoming_config = dict(config or {})
        output_max_items = int(incoming_config.get("max_items") or 120)
        cfg = {
            "container_selector": "main",
            "item_selector": "article, li, tr, .decision, .aegov-card[aria-labelledby], .card, .item, [data-icms-item], a[href]",
            "title_selector": "h1, h2, h3, h4, h5, [data-icms-title], a",
            "date_selector": "time, .date, [data-date]",
            "url_selector": "a[href]",
            "exclude_selectors": ["header", "nav", "footer", ".search", "script", "style", "noscript"],
            "sort_items": True,
            "max_items": max(output_max_items, int(incoming_config.get("candidate_scan_limit") or 500)),
        }
        cfg.update(incoming_config)
        cfg["max_items"] = max(output_max_items, int(incoming_config.get("candidate_scan_limit") or 500))
        result = super().extract(html, url=url, config=cfg)
        result.adapter_family = self.family
        result.adapter_name = self.name
        result.extraction_strategy = f"adapter:{self.name}"
        if result.items:
            by_title: dict[str, dict] = {}

            def _candidate_score(row: dict) -> int:
                date = str(row.get("date") or "")
                context = str(row.get("raw_text_snippet") or "")
                date_score = 0
                if date:
                    date_score = 2 if any(ch.isalpha() for ch in date) or "/" in date or "-" in date else 1
                return (
                    int(bool(row.get("url"))) * 2
                    + date_score * 3
                    + min(len(context) // 120, 3)
                )

            for item in result.items:
                title = item.get("title") or ""
                item_url = item.get("url") or ""
                context = item.get("raw_text_snippet") or ""
                text = f"{title} {context}".lower()
                if _is_noise_title(title):
                    continue
                if not any(token in text for token in ("decision", "regulation", "circular", "rules", "rule", "procedure", "law", "aml", "cft", "market", "chairman", "fintech", "virtual asset", "passporting")):
                    continue
                if not item.get("date"):
                    item["date"] = _extract_date(context)
                if str(item_url).strip().lower().startswith(("javascript:", "javascipt:", "#")):
                    item["url"] = ""
                    item_url = ""
                item["row_hash"] = _row_hash(title, item.get("date"), item_url, item.get("category"))
                key = title.lower()
                current = by_title.get(key)
                if current:
                    current_score = _candidate_score(current)
                    item_score = _candidate_score(item)
                    if item_score <= current_score:
                        continue
                by_title[key] = item
            filtered = list(by_title.values())[:output_max_items]
            result.items = filtered
            result.text = _format_items("SCA listing items", filtered)
            result.noise_risk = "medium" if len(filtered) < 5 else "low"
            result.source_health_risk = "medium"
            if not filtered:
                result.failure_reason = "No SCA regulatory listing items were isolated."
                result.remediation_hint = "Review rendered item selectors or official list data source."
        return result


class RulebookModuleAdapter(BaseHtmlAdapter):
    family = "dfsa_rulebook"
    name = "dfsa_rulebook"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        config = config or {}
        soup = _soup(html, config.get("exclude_selectors"))
        container = soup.select_one(str(config.get("container_selector") or "main, article").strip()) or soup
        items: list[dict] = []
        seen: set[str] = set()
        for anchor in container.select("a[href]"):
            title = _node_text(anchor, separator=" ", limit=260)
            href = (anchor.get("href") or "").strip()
            title_l = title.lower()
            if _is_noise_title(title) or not href:
                continue
            if not any(token in title_l for token in ("module", "rulebook", "aml", "gen", "cob", "prudential", "markets")):
                continue
            item_url = urljoin(url, href)
            key = f"{title_l}|{item_url.lower()}"
            if key in seen:
                continue
            seen.add(key)
            item = {"title": title, "url": item_url, "category": "rulebook_module"}
            item["row_hash"] = _row_hash(title, item_url, item["category"])
            items.append(item)
        if not items:
            return self._empty("No rulebook modules were isolated.", "Review module selectors or source URL.")
        return AdapterResult(
            text=_format_items("Rulebook modules", items),
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            items=items,
            noise_risk="medium",
            source_health_risk="medium",
            metadata={"container_selector": config.get("container_selector") or "main, article", "url": url},
        )


class DocumentListingAdapter(BaseHtmlAdapter):
    family = "document_listing"
    name = "document_listing"
    allowed_tokens: tuple[str, ...] = ("regulation", "guidance", "publication", "report", "rulebook", "aml", "cft")
    heading = "Document listing items"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        config = config or {}
        soup = _soup(html, config.get("exclude_selectors") or ["nav", "footer", "form", ".search"])
        container_selector = str(config.get("container_selector") or "main").strip()
        container = soup.select_one(container_selector) if container_selector else soup
        if not container:
            container = soup.select_one("main") or soup.body or soup
        items: list[dict] = []
        seen: set[str] = set()
        for anchor in container.select("a[href]"):
            title = _node_text(anchor, separator=" ", limit=260)
            href = (anchor.get("href") or "").strip()
            if _is_noise_title(title) or not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            item_url = urljoin(url, href)
            context_node = anchor.parent or anchor
            context = _node_text(context_node, separator=" ", limit=700)
            combined = f"{title} {href} {context}".lower()
            title_href = f"{title} {href}".lower()
            is_document = bool(_DOCUMENT_EXT_RE.search(href))
            has_signal = any(token in title_href for token in self.allowed_tokens)
            if not is_document and not has_signal:
                continue
            key = f"{title.lower()}|{item_url.lower()}"
            if key in seen:
                continue
            seen.add(key)
            item = {
                "title": title,
                "date": _extract_date(context),
                "url": item_url,
                "document_url": item_url if is_document else "",
                "category": "document" if is_document else "listing_item",
                "raw_text_snippet": context,
            }
            item["row_hash"] = _row_hash(title, item.get("date"), item_url)
            items.append(item)
        if bool(config.get("sort_items", True)):
            items.sort(key=lambda row: ((row.get("date") or ""), (row.get("title") or ""), (row.get("url") or "")))
        if not items:
            return self._empty("No document/listing items were isolated.", "Review document link selectors or official source page.")
        return AdapterResult(
            text=_format_items(self.heading, items),
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            items=items,
            noise_risk="medium" if len(items) < 5 else "low",
            source_health_risk="medium",
            metadata={"container_selector": container_selector, "url": url},
        )


class CbuaeDocumentListingAdapter(DocumentListingAdapter):
    family = "cbuae_document_listing"
    name = "cbuae_document_listing"
    heading = "CBUAE document listing items"
    allowed_tokens = ("regulation", "guidance", "payment", "aml", "cft", "licensed", "financial", "consultation", "publication")


class FiuEocnDocumentListingAdapter(DocumentListingAdapter):
    family = "fiu_eocn_document_listing"
    name = "fiu_eocn_document_listing"
    heading = "FIU/EOCN document listing items"
    allowed_tokens = ("fiu", "goaml", "aml", "cft", "sanction", "tfs", "typolog", "publication", "guidance", "report")


class EocnNewsListingAdapter(BaseHtmlAdapter):
    family = "eocn_news_listing"
    name = "eocn_news_listing"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        config = config or {}
        soup = _soup(html, config.get("exclude_selectors") or ["header", "nav", "footer", "form", ".main-menu", ".site-map"])
        container_selector = str(config.get("container_selector") or "#NewsContainer").strip()
        container = soup.select_one(container_selector) if container_selector else soup
        if not container:
            return self._empty("EOCN news container was not found.", "Review #NewsContainer after Playwright rendering.")

        item_selector = str(config.get("item_selector") or ".item.default-section, .item").strip()
        title_selector = str(config.get("title_selector") or ".item-title-container[href], a[href*='/news/']").strip()
        date_selector = str(config.get("date_selector") or ".item-date").strip()
        brief_selector = str(config.get("brief_selector") or ".item-brief").strip()
        max_items = int(config.get("max_items") or 50)
        items: list[dict] = []
        seen: set[str] = set()

        for node in container.select(item_selector):
            title_node = node.select_one(title_selector)
            if not title_node:
                continue
            href = (title_node.get("href") or "").strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            if "/news/" not in href.lower():
                continue
            title = _clean(title_node.get("title") or title_node.get_text(" ", strip=True), limit=260)
            if _is_noise_title(title):
                continue
            item_url = urljoin(url, href)
            date_node = node.select_one(date_selector) if date_selector else None
            brief_node = node.select_one(brief_selector) if brief_selector else None
            date = _clean(date_node.get_text(" ", strip=True), limit=80) if date_node else ""
            brief = _clean(brief_node.get_text(" ", strip=True), limit=700) if brief_node else ""
            context = brief or _node_text(node, separator=" ", limit=700)
            key = f"{title.lower()}|{item_url.lower()}|{date.lower()}"
            if key in seen:
                continue
            seen.add(key)
            item = {
                "title": title,
                "date": date,
                "url": item_url,
                "category": "news",
                "raw_text_snippet": context,
            }
            item["row_hash"] = _row_hash(title, date, item_url, context)
            items.append(item)
            if len(items) >= max_items:
                break

        if not items:
            return self._empty("No EOCN news items were isolated.", "Review EOCN news card selectors or mark source as remediation.")

        return AdapterResult(
            text=_format_items("EOCN news listing items", items),
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            items=items,
            noise_risk="medium" if len(items) < 5 else "low",
            source_health_risk="medium",
            metadata={
                "container_selector": container_selector,
                "item_selector": item_selector,
                "title_selector": title_selector,
                "url": url,
            },
        )


class VaraPdfListingAdapter(DocumentListingAdapter):
    family = "vara_pdf_listing"
    name = "vara_pdf_listing"
    heading = "VARA PDF/rulebook listing items"
    allowed_tokens = ("rulebook", "aml", "cft", "company", "enforcement", "order", "regulatory", "framework", "virtual asset")


class PdfListingAdapter(DocumentListingAdapter):
    family = "pdf_listing"
    name = "pdf_listing"
    heading = "PDF listing items"
    allowed_tokens = ("pdf", "rulebook", "regulation", "guidance", "consultation", "aml", "cft", "report", "publication")

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        result = super().extract(html, url=url, config=config)
        if result.items:
            result.items = [item for item in result.items if item.get("document_url") or str(item.get("url") or "").lower().endswith(".pdf")]
            result.text = _format_items(self.heading, result.items)
            if not result.items:
                result.failure_reason = "No PDF document links were isolated."
                result.remediation_hint = "Review document selectors or use a normal document listing adapter."
        return result


class PdfDocumentAdapter(BaseHtmlAdapter):
    family = "pdf_document"
    name = "pdf_document"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        text = _clean(html)
        if len(text) < int((config or {}).get("min_chars") or 500):
            return self._empty("PDF text is too shallow for monitoring.", "Use a better PDF extractor or mark scanned/OCR-needed PDF as remediation.")
        return AdapterResult(
            text=text,
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            noise_risk="low",
            source_health_risk="medium",
            metadata={"url": url, "pdf_text_chars": len(text)},
        )


class RegisterAdapter(TableAdapter):
    family = "register"
    name = "register"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        cfg = {"table_selector": "table", "sort_rows": True}
        cfg.update(config or {})
        result = super().extract(html, url=url, config=cfg)
        result.adapter_family = self.family
        result.adapter_name = self.name
        result.extraction_strategy = f"adapter:{self.name}"
        result.metadata["register_limitations"] = "Register pages may require pagination/filter coverage before activation."
        return result


class SitemapFeedAdapter(DocumentListingAdapter):
    family = "sitemap_feed"
    name = "sitemap_feed"
    heading = "Sitemap/feed URL items"
    allowed_tokens = ("http", "xml", "rss", "feed", "regulation", "rulebook", "guidance")


class PublicJsonApiAdapter(BaseHtmlAdapter):
    family = "public_json_api"
    name = "public_json_api"

    def extract(self, html: str, *, url: str = "", config: dict | None = None) -> AdapterResult:
        text = _clean(html)
        if not text.startswith(("{", "[")):
            return self._empty("Public JSON/API adapter received non-JSON text.", "Use only public unauthenticated JSON endpoints with this adapter.")
        return AdapterResult(
            text=text,
            adapter_family=self.family,
            adapter_name=self.name,
            extraction_strategy=f"adapter:{self.name}",
            noise_risk="low",
            source_health_risk="medium",
            metadata={"url": url, "format": "json"},
        )


class RenderedDomEvidenceAdapter(StaticHtmlAdapter):
    family = "rendered_dom_evidence"
    name = "rendered_dom_evidence"


class AdgmFsraListingAdapter(DocumentListingAdapter):
    family = "adgm_fsra_listing"
    name = "adgm_fsra_listing"
    heading = "ADGM/FSRA listing items"
    allowed_tokens = ("fsra", "adgm", "aml", "financial crime", "guidance", "rule", "regulation", "consultation", "circular")


class DfsaNoticeListingAdapter(DocumentListingAdapter):
    family = "dfsa_notice_listing"
    name = "dfsa_notice_listing"
    heading = "DFSA notice/enforcement listing items"
    allowed_tokens = ("dfsa", "mlro", "letter", "notice", "enforcement", "regulatory action", "aml", "financial crime", "sanction")


_GENERIC_CONTEXT_SNIPPETS = {
    "view",
    "view details",
    "read more",
    "learn more",
    "download",
    "open",
}


def _is_meaningful_context(snippet: str, title: str) -> bool:
    cleaned = _clean(snippet)
    if not cleaned or cleaned == title:
        return False
    folded = cleaned.casefold()
    if folded in _GENERIC_CONTEXT_SNIPPETS:
        return False
    return len(cleaned) >= 40 or len(cleaned.split()) >= 8


def _format_items(heading: str, items: list[dict]) -> str:
    if not items:
        return ""
    lines = [heading]
    for item in items:
        lines.append(f"- Title: {item.get('title') or ''}")
        if item.get("date"):
            lines.append(f"  Date: {item['date']}")
        if item.get("category"):
            lines.append(f"  Category: {item['category']}")
        if item.get("url"):
            lines.append(f"  URL: {item['url']}")
        if item.get("document_url"):
            lines.append(f"  Document URL: {item['document_url']}")
        snippet = _clean(item.get("raw_text_snippet") or "", limit=900)
        title = _clean(item.get("title") or "")
        if snippet and title and title in snippet:
            snippet = _clean(snippet.replace(title, "", 1), limit=900)
        if _is_meaningful_context(snippet, title):
            lines.append(f"  Context: {snippet}")
        if item.get("row_hash"):
            lines.append(f"  Row hash: {item['row_hash']}")
    return "\n".join(lines).strip()


_ADAPTERS: dict[str, BaseHtmlAdapter] = {
    "static_html": StaticHtmlAdapter(),
    "playwright_selector": PlaywrightSelectorAdapter(),
    "custom_element": CustomElementAdapter(),
    "listing": ListingAdapter(),
    "table": TableAdapter(),
    "pdf_document": PdfDocumentAdapter(),
    "pdf_listing": PdfListingAdapter(),
    "register": RegisterAdapter(),
    "sitemap_feed": SitemapFeedAdapter(),
    "public_json_api": PublicJsonApiAdapter(),
    "rendered_dom_evidence": RenderedDomEvidenceAdapter(),
    "adgm_fsra_listing": AdgmFsraListingAdapter(),
    "dfsa_notice_listing": DfsaNoticeListingAdapter(),
    "sca_listing": ScaListingAdapter(),
    "dfsa_rulebook": RulebookModuleAdapter(),
    "cbuae_document_listing": CbuaeDocumentListingAdapter(),
    "fiu_eocn_document_listing": FiuEocnDocumentListingAdapter(),
    "eocn_news_listing": EocnNewsListingAdapter(),
    "vara_pdf_listing": VaraPdfListingAdapter(),
}


def get_adapter(adapter_family: str | None = None, adapter_name: str | None = None) -> BaseHtmlAdapter | None:
    key = (adapter_name or adapter_family or "").strip()
    return _ADAPTERS.get(key)


def extract_with_adapter(
    html: str,
    *,
    url: str = "",
    adapter_family: str | None = None,
    adapter_name: str | None = None,
    adapter_config: dict | None = None,
) -> AdapterResult:
    adapter = get_adapter(adapter_family=adapter_family, adapter_name=adapter_name)
    if not adapter:
        key = adapter_name or adapter_family or ""
        return AdapterResult(
            adapter_family=adapter_family or "",
            adapter_name=adapter_name or "",
            extraction_strategy=f"adapter:{key}" if key else "",
            failure_reason=f"Unknown adapter: {key}" if key else "No adapter configured.",
            remediation_hint="Use a configured adapter family such as static_html, custom_element, listing, table, pdf_listing, register, sca_listing, dfsa_rulebook, cbuae_document_listing, fiu_eocn_document_listing, eocn_news_listing, or vara_pdf_listing.",
            source_health_risk="medium",
        )
    try:
        return adapter.extract(html, url=url, config=adapter_config or {})
    except Exception as exc:
        return AdapterResult(
            adapter_family=adapter.family,
            adapter_name=adapter.name,
            extraction_strategy=f"adapter:{adapter.name}",
            failure_reason=f"Adapter failed: {type(exc).__name__}",
            remediation_hint="Review adapter config and fixture coverage before activation.",
            warnings=[str(exc)],
            source_health_risk="medium",
        )
