"""Auto DOM investigation helpers for Source Lab.

The investigator does not fetch pages. It inspects already-fetched/rendered HTML
and recommends an extraction strategy that Source Lab can test safely. Browser
fetching stays in scraper/source_intake so this module remains deterministic and
unit-testable.
"""

from __future__ import annotations

from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin


_SPACE_RE = re.compile(r"\s+")
_PDF_RE = re.compile(r"\.pdf($|[?#])", re.IGNORECASE)
_NAV_WORDS = {
    "home",
    "about",
    "services",
    "search",
    "contact",
    "login",
    "privacy",
    "accessibility",
}
_CHROME_SELECTORS = ["script", "style", "noscript"]


def _clean(value: str | None) -> str:
    return _SPACE_RE.sub(" ", value or "").strip()


def _node_text(node) -> str:
    return _clean(node.get_text(" ", strip=True) if node else "")


def _selector_for(node) -> str:
    if not node:
        return ""
    if node.get("id"):
        return f"#{node.get('id')}"
    attrs = node.attrs or {}
    for attr in ("data-icms-list", "data-list", "data-testid", "role"):
        if attr in attrs:
            value = attrs.get(attr)
            return f"[{attr}]" if value in {"", None} else f"[{attr}='{value}']"
    classes = node.get("class") or []
    if classes:
        return "." + ".".join(str(c) for c in classes[:2])
    return node.name or ""


def _base_payload(url: str, soup: BeautifulSoup) -> dict:
    title = _node_text(soup.select_one("title")) or _node_text(soup.select_one("h1"))
    return {
        "final_url": url,
        "page_title": title,
        "detected_page_type": "unknown",
        "recommended_adapter_family": "",
        "recommended_adapter_name": "",
        "wait_selector": "",
        "content_selector": "",
        "item_selector": "",
        "fallback_selectors": [],
        "selectors_considered": [],
        "selector_confidence": 0,
        "why_selector_was_chosen": "",
        "nav_shell_risk": "unknown",
        "noise_risk": "unknown",
        "source_health_risk": "unknown",
        "failure_reason": "",
        "remediation_hint": "",
        "can_no_save_test": False,
        "can_save_evidence": False,
        "warnings": [],
    }


def _nav_shell_risk(soup: BeautifulSoup) -> tuple[str, str]:
    body = soup.body or soup
    text = _node_text(body).lower()
    words = [w.strip(".,:;()[]{}") for w in text.split()]
    if not words:
        return "high", "No visible text was found."
    nav_count = sum(1 for word in words if word in _NAV_WORDS)
    ratio = nav_count / max(1, len(words))
    substantive_sentences = len([part for part in re.split(r"[.!?]\s+", text) if len(part.split()) >= 10])
    if len(text) >= 500 and ratio < 0.15:
        return "low", ""
    if len(text) < 160 or ratio >= 0.35 or substantive_sentences == 0:
        return "high", "Rendered content looks like navigation/search shell rather than source content."
    if ratio >= 0.18:
        return "medium", ""
    return "low", ""


def _candidate_selectors(soup: BeautifulSoup) -> list[str]:
    candidates: list[str] = []
    for selector in (
        "article",
        "main",
        ".summary",
        ".page-summary",
        "[data-summary]",
        "[role='main']",
        "[data-icms-list]",
        ".content",
        ".page-content",
        ".container",
        "table",
        "adgm-page > span",
    ):
        if soup.select_one(selector):
            candidates.append(selector)
    return candidates


def _listing_container(soup: BeautifulSoup):
    for selector in ("[data-icms-list]", ".icms-list", ".listing", ".list", ".cards", "main"):
        node = soup.select_one(selector)
        if node:
            item_count = len(node.select("article, li, tr, .card, .item, a[href]"))
            if item_count >= 3:
                return node, selector, item_count
    return None, "", 0


def investigate_html(html: str, *, url: str = "") -> dict:
    """Inspect HTML and recommend Source Lab extraction strategy."""
    soup = BeautifulSoup(html or "", "html.parser")
    for selector in _CHROME_SELECTORS:
        for node in soup.select(selector):
            node.decompose()

    result = _base_payload(url, soup)
    result["selectors_considered"] = _candidate_selectors(soup)
    nav_risk, nav_reason = _nav_shell_risk(soup)
    result["nav_shell_risk"] = nav_risk
    if nav_reason:
        result["failure_reason"] = nav_reason
        result["remediation_hint"] = "Use a more precise content/listing selector or treat the source as remediation."

    anchors = list(soup.select("a[href]"))
    pdf_links = [a for a in anchors if _PDF_RE.search(str(a.get("href") or ""))]
    table = soup.select_one("table")
    custom_element = soup.select_one("adgm-page, dfsa-page, sca-page")
    listing_node, listing_selector, listing_count = _listing_container(soup)
    summary = soup.select_one("section.summary, .summary, .page-summary, [data-summary]")
    article = soup.select_one("article")
    main = soup.select_one("main")

    if table:
        result.update(
            {
                "detected_page_type": "table",
                "recommended_adapter_family": "table",
                "recommended_adapter_name": "table",
                "wait_selector": "table",
                "content_selector": "table",
                "item_selector": "tr",
                "selector_confidence": 82,
                "why_selector_was_chosen": "A table with rows was detected.",
                "noise_risk": "medium",
                "source_health_risk": "medium",
                "can_no_save_test": True,
                "can_save_evidence": nav_risk != "high",
            }
        )
    elif len(pdf_links) >= 2:
        result.update(
            {
                "detected_page_type": "pdf_listing",
                "recommended_adapter_family": "pdf_listing",
                "recommended_adapter_name": "pdf_listing",
                "wait_selector": "main, a[href$='.pdf']",
                "content_selector": _selector_for(main) or "main",
                "item_selector": "a[href]",
                "selector_confidence": 80,
                "why_selector_was_chosen": f"{len(pdf_links)} PDF/document links were detected.",
                "noise_risk": "medium",
                "source_health_risk": "medium",
                "can_no_save_test": True,
                "can_save_evidence": nav_risk != "high",
            }
        )
    elif listing_node and listing_count >= 3:
        result.update(
            {
                "detected_page_type": "listing",
                "recommended_adapter_family": "listing",
                "recommended_adapter_name": "listing",
                "wait_selector": listing_selector,
                "content_selector": listing_selector,
                "item_selector": "article, li, tr, .card, .item, a[href]",
                "fallback_selectors": [listing_selector, "main", "article, li, tr, .card, .item"],
                "selector_confidence": 78,
                "why_selector_was_chosen": f"Detected {listing_count} likely listing items.",
                "noise_risk": "medium",
                "source_health_risk": "medium",
                "can_no_save_test": True,
                "can_save_evidence": nav_risk != "high",
            }
        )
    elif custom_element:
        selector = _selector_for(custom_element)
        result.update(
            {
                "detected_page_type": "custom_element",
                "recommended_adapter_family": "custom_element",
                "recommended_adapter_name": "custom_element",
                "wait_selector": selector,
                "content_selector": selector,
                "selector_confidence": 72,
                "why_selector_was_chosen": "A regulator custom element was detected.",
                "noise_risk": "medium",
                "source_health_risk": "medium",
                "can_no_save_test": True,
                "can_save_evidence": nav_risk != "high",
            }
        )
    elif summary or article or main:
        if summary:
            selector = ".summary"
            selected = summary
        else:
            selector = "article" if article else "main"
            selected = article or main
        text = _node_text(selected)
        link_count = len(selected.select("a[href]")) if selected else 0
        is_dfsa_summary = "dfsa.ae" in (url or "").lower() and summary is not None and link_count >= 1
        result.update(
            {
                "detected_page_type": "listing" if is_dfsa_summary else "article",
                "recommended_adapter_family": "dfsa_notice_listing" if is_dfsa_summary else "static_html",
                "recommended_adapter_name": "dfsa_notice_listing" if is_dfsa_summary else "static_html",
                "wait_selector": selector,
                "content_selector": selector,
                "item_selector": "a[href]" if is_dfsa_summary else "",
                "selector_confidence": 84 if is_dfsa_summary else 86 if len(text) >= 250 else 72,
                "why_selector_was_chosen": "DFSA summary block with regulatory links was detected." if is_dfsa_summary else f"{selector} contains the densest visible content block.",
                "noise_risk": "medium" if is_dfsa_summary else "low" if nav_risk == "low" else "medium",
                "source_health_risk": "medium" if is_dfsa_summary else "low" if nav_risk == "low" else "medium",
                "can_no_save_test": bool(text),
                "can_save_evidence": nav_risk != "high" and len(text) >= 250,
            }
        )
    else:
        result.update(
            {
                "detected_page_type": "unknown",
                "failure_reason": result["failure_reason"] or "No reliable content container was detected.",
                "remediation_hint": "Use Playwright DOM inspection and configure a source-specific adapter.",
                "source_health_risk": "high",
                "noise_risk": "high",
            }
        )

    if not result["fallback_selectors"]:
        result["fallback_selectors"] = [s for s in result["selectors_considered"][:4] if s]

    if result["nav_shell_risk"] == "high":
        result["can_save_evidence"] = False

    if pdf_links:
        result["warnings"].append(f"Detected {len(pdf_links)} PDF/document link(s).")
        result.setdefault("metadata", {})
        result["metadata"] = {
            "pdf_links": [
                {"title": _node_text(anchor), "url": urljoin(url, str(anchor.get("href") or ""))}
                for anchor in pdf_links[:20]
            ]
        }

    return result
