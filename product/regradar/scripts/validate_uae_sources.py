#!/usr/bin/env python3
"""
Manual UAE official source expansion validation.

This script tests official UAE regulatory source pages and writes source
readiness evidence. It does not modify sources.json by default and does not
activate monitoring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters.uae_fsra_circulars import (  # noqa: E402
    DEFAULT_FSRA_CIRCULARS_URL,
    extract_fsra_circular_items,
)
from app.adapters.uae_cbuae_rulebook import (  # noqa: E402
    DEFAULT_CBUAE_RULEBOOK_UPDATES_URL,
    extract_cbuae_rulebook_update_items,
)
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA  # noqa: E402
from app.extractors import extract_best_text  # noqa: E402

TODAY = date.today().isoformat()

TARGET_SOURCES = [
    {
        "source_id": "ae-vara-rulebooks",
        "official_name": "VARA Rulebooks / Rulebook Updates",
        "official_url": "https://rulebooks.vara.ae/",
        "category": "virtual_assets",
        "buyer_profiles": ["vasp", "crypto", "virtual_assets", "aml_compliance"],
        "expected": "VARA rulebook portal and rulebook sections",
    },
    {
        "source_id": "ae-adgm-fsra-circulars",
        "official_name": "ADGM FSRA Circulars / Publications",
        "official_url": DEFAULT_FSRA_CIRCULARS_URL,
        "category": "financial_services",
        "buyer_profiles": ["adgm", "fsra", "fintech", "payments", "vasp"],
        "expected": "HTML listing with item/document links",
        "proof_target": True,
    },
    {
        "source_id": "ae-cbuae-rulebook-aml-payments",
        "official_name": "CBUAE Rulebook / AML-CFT / Payments",
        "official_url": "https://rulebook.centralbank.ae/",
        "category": "banking_payments",
        "buyer_profiles": ["payments", "fintech", "aml", "banking"],
        "expected": "rulebook sections and publications",
    },
    {
        "source_id": "ae-fiu-publications",
        "official_name": "UAE FIU Publications / Typologies",
        "official_url": "https://www.uaefiu.gov.ae/en/publications/",
        "category": "aml_fiu",
        "buyer_profiles": ["aml", "fiu", "mlro", "vasp", "payments"],
        "expected": "publication/typology index",
    },
    {
        "source_id": "ae-dfsa-consultations-notices",
        "official_name": "DFSA Consultations / Notices / Rulebook Updates",
        "official_url": "https://www.dfsa.ae/rules-and-guidance",
        "category": "difc_dfsa",
        "buyer_profiles": ["difc", "dfsa", "financial_services", "legal"],
        "expected": "consultation paper listing",
    },
    {
        "source_id": "ae-difc-laws-data-protection",
        "official_name": "DIFC Laws / DIFC Data Protection",
        "official_url": "https://www.difc.com/business/laws-and-regulations/",
        "category": "difc_laws",
        "buyer_profiles": ["difc", "dfsa", "data_protection", "legal"],
        "expected": "law and guidance pages",
    },
    {
        "source_id": "ae-adgm-data-protection",
        "official_name": "ADGM Office of Data Protection Guidance",
        "official_url": "https://www.adgm.com/operating-in-adgm/office-of-data-protection",
        "category": "data_protection",
        "buyer_profiles": ["adgm", "data_protection", "privacy", "dpo"],
        "expected": "guidance pages/document links",
    },
    {
        "source_id": "ae-fta-tax-guides",
        "official_name": "FTA Public Clarifications / Tax Guides",
        "official_url": "https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx",
        "category": "tax",
        "buyer_profiles": ["tax", "corporate", "corporate_tax"],
        "expected": "tax guide/public clarification listing",
    },
    {
        "source_id": "ae-uaeiec-sanctions-tfs",
        "official_name": "Executive Office / UAEIEC Sanctions / TFS",
        "official_url": "https://www.uaeiec.gov.ae/en-us/un-page",
        "category": "sanctions_tfs",
        "buyer_profiles": ["aml", "sanctions", "fiu", "mlro", "vasp", "payments"],
        "expected": "sanctions/TFS list and update links",
    },
    {
        "source_id": "ae-moet-aml-dnfbp",
        "official_name": "Ministry of Economy AML / TFS / DNFBP",
        "official_url": "https://www.moet.gov.ae/en/aml",
        "category": "aml_dnfbp",
        "buyer_profiles": ["aml", "dnfbp", "mlro", "corporate"],
        "expected": "AML/DNFBP guidance pages",
    },
    {
        "source_id": "ae-legislation-portal",
        "official_name": "UAE Legislation Portal item-level laws/decrees",
        "official_url": "https://uaelegislation.gov.ae/en",
        "category": "legislation",
        "buyer_profiles": ["legal", "compliance", "tax", "data_protection", "financial_services"],
        "expected": "item-level laws/decrees",
    },
    {
        "source_id": "ae-dubai-official-gazette",
        "official_name": "Dubai Official Gazette",
        "official_url": "https://dlp.dubai.gov.ae/",
        "category": "gazette",
        "buyer_profiles": ["legal", "compliance", "corporate"],
        "expected": "issue/year pages and PDF links",
    },
]

HEADERS = {
    "User-Agent": REQUESTS_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

DATE_RE = re.compile(
    r"\b("
    r"\d{1,2}\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|"
    r"Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|"
    r"Dec|December)\s+\d{4}|"
    r"\d{4}-\d{2}-\d{2}|"
    r"\d{1,2}/\d{1,2}/\d{4}"
    r")\b",
    re.IGNORECASE,
)


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except Exception:
        return []


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    return []


def _flatten_sources(data: object) -> list[dict]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        sources = data.get("sources")
        if isinstance(sources, list):
            return [item for item in sources if isinstance(item, dict)]
        return [item for item in data.values() if isinstance(item, dict)]
    return []


def _normalize_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = re.sub(r"/+", "/", parsed.path).rstrip("/")
    return f"{scheme}://{netloc}{path}"


def _clean(value: str | None, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _domain(url: str | None) -> str:
    try:
        return urlparse(url or "").netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _candidate_metadata() -> dict[str, dict]:
    candidates = _as_list(_load_json(ROOT / "data" / "uae_source_candidates.json"))
    out: dict[str, dict] = {}
    for item in candidates:
        if not isinstance(item, dict):
            continue
        for key in (
            item.get("candidate_id"),
            item.get("source_id"),
            _normalize_url(item.get("official_url") or item.get("url")),
        ):
            if key:
                out[str(key)] = item
    return out


def _source_registry() -> list[dict]:
    return _flatten_sources(_load_json(ROOT / "sources.json"))


def _find_registry_status(target: dict, registry: list[dict]) -> str | None:
    target_url = _normalize_url(target.get("official_url"))
    target_domain = _domain(target.get("official_url"))
    target_name = (target.get("official_name") or "").lower()
    for source in registry:
        url = _normalize_url(source.get("url") or source.get("official_url"))
        if target_url and url == target_url:
            return _registry_label(source)
    for source in registry:
        url_domain = _domain(source.get("url") or source.get("official_url"))
        name = str(source.get("name") or source.get("official_name") or "").lower()
        if target_domain and target_domain == url_domain and (
            target_name[:12] in name or name[:12] in target_name
        ):
            return _registry_label(source)
    return None


def _registry_label(source: dict) -> str:
    raw = str(source.get("status") or source.get("enabled") or "registered").lower()
    if raw in {"active", "true"}:
        return "enabled_in_existing_registry"
    if raw in {"false", "disabled"}:
        return "disabled_in_existing_registry"
    return raw


def _fetch(url: str) -> dict:
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=HTTP_TIMEOUT_S,
            allow_redirects=True,
        )
        return {
            "ok": True,
            "status": response.status_code,
            "final_url": response.url,
            "content_type": response.headers.get("content-type", ""),
            "html": response.text or "",
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "final_url": url,
            "content_type": "",
            "html": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _extract_date(text: str) -> str | None:
    match = DATE_RE.search(text or "")
    return match.group(1) if match else None


def _generic_items(html: str, base_url: str, limit: int = 30) -> list[dict]:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    items: list[dict] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        title = _clean(anchor.get_text(" ", strip=True), 220)
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urljoin(base_url, href)
        if not title or len(title) < 8:
            continue
        title_l = title.lower()
        if title_l in {
            "read more",
            "learn more",
            "contact us",
            "privacy policy",
            "business",
            "business areas",
            "public register",
            "public registers",
            "legal framework",
            "laws and regulations",
            "news and publications",
            "news & insights",
            "publications",
            "setting up",
            "operating in",
            "overview",
            "grow in uae",
            "legislations",
            "advanced search",
        }:
            continue

        parent = anchor
        for _ in range(3):
            if parent.parent is None:
                break
            parent = parent.parent
            if parent.name in {"article", "li", "tr", "section", "div"}:
                break
        context = _clean(parent.get_text(" ", strip=True), 500)
        url_l = url.lower()
        context_l = context.lower()
        strong_marker = any(
            token in url_l or token in title_l
            for token in (
                "consultation",
                "publication",
                "circular",
                "rule",
                "law",
                "guide",
                "clarification",
                "notice",
                "pdf",
                "regulation",
                "sanction",
                "gazette",
            )
        )
        if not strong_marker and not _extract_date(context):
            continue

        key = f"{title.lower()}|{url.lower()}"
        if key in seen:
            continue
        seen.add(key)
        items.append(
            {
                "title": title,
                "date": _extract_date(context),
                "url": url,
                "document_url": url if url_l.split("?", 1)[0].endswith((".pdf", ".doc", ".docx")) else None,
                "raw_text_snippet": context,
            }
        )
        if len(items) >= limit:
            break
    return items


def _classify_method(content_type: str, text_chars: int, item_count: int, pdf_count: int) -> str:
    content_type_l = (content_type or "").lower()
    if "pdf" in content_type_l:
        return "PDF-only"
    if item_count >= 3:
        return "table/list-based HTML"
    if pdf_count > 0 and item_count > 0:
        return "HTML with document links"
    if text_chars >= 1000:
        return "HTML extractable"
    if text_chars < 300:
        return "navigation-only or JS-rendered"
    return "HTML partial"


def _recommended_status(http_status: int | None, text_chars: int, item_count: int, method: str, error: str | None) -> str:
    if error:
        return "access_limited"
    if http_status in {401, 403, 429}:
        return "access_limited"
    if http_status is None or http_status >= 500:
        return "blocked_deferred"
    if http_status >= 400:
        return "blocked_deferred"
    if item_count >= 3 and text_chars >= 1000:
        return "active_candidate"
    if item_count >= 1:
        return "under_validation"
    if "navigation-only" in method:
        return "navigation_only"
    if text_chars >= 1000:
        return "needs_adapter"
    if text_chars >= 250:
        return "under_validation"
    return "mapped_only"


def _limitations(target: dict, status: str, text_chars: int, item_count: int, fetch_result: dict) -> list[str]:
    notes: list[str] = []
    if fetch_result.get("error"):
        notes.append(f"Request error from current infrastructure: {fetch_result['error']}")
    if fetch_result.get("status") in {401, 403, 429}:
        notes.append(f"HTTP {fetch_result['status']} indicates access limitation or blocking.")
    if item_count == 0:
        notes.append("No reliable item-level rows or document links were isolated by generic extraction.")
    if text_chars < 1000:
        notes.append("Extracted text is below the content-rich threshold for monitoring readiness.")
    if status == "active_candidate":
        notes.append("Reachable and itemized, but not active until repeated proof/diff validation passes.")
    if target["source_id"] == "ae-fta-tax-guides":
        notes.append("FTA/tax.gov.ae may require access and repeated-run validation from deployment infrastructure.")
    if target["source_id"] == "ae-legislation-portal":
        notes.append("Root portal validation is insufficient; item-level laws/decrees must be tested separately.")
    if target["source_id"] == "ae-vara-rulebooks":
        notes.append("VARA official portal is the validation target; rulebook/update item paths require separate discovery and adapter validation before activation.")
    if target["source_id"] == "ae-cbuae-rulebook-aml-payments":
        notes.append("CBUAE AML/CFT and payments pages require item-level publication mapping.")
    if target["source_id"] == "ae-adgm-fsra-circulars":
        notes.append("FSRA circulars prototype did not isolate enough circular rows; source remains adapter/proof target work, not active.")
    if target["source_id"] == "ae-dfsa-consultations-notices":
        notes.append("DFSA pages may return WAF/access limitation from current infrastructure; do not activate without a reliable official item source.")
    if target["source_id"] == "ae-dubai-official-gazette":
        notes.append("Dubai legislation portal root is not enough; official gazette issue/year/PDF item paths must be isolated before activation.")
    return notes or ["Limitations require operator review before pilot activation."]


def _next_action(status: str, target: dict) -> str:
    if target.get("proof_target"):
        return "Repeat FSRA row extraction over scheduled runs and validate true proof/diff before activation."
    if status == "active_candidate":
        return "Run repeated proof/diff validation before considering activation."
    if status == "under_validation":
        return "Run repeated extraction and map item-level titles, dates, and source proof URLs."
    if status == "needs_adapter":
        return "Build source-specific adapter prototype and validate row/document extraction."
    if status in {"access_limited", "blocked_deferred"}:
        return "Defer activation; test approved access strategy without bypassing WAF/CAPTCHA."
    if status == "navigation_only":
        return "Identify SSR/API/document endpoints or mark as deferred."
    return "Keep mapped only until technical validation is complete."


def _apply_source_specific_status(target: dict, status: str, item_count: int) -> str:
    source_id = target["source_id"]
    if source_id == "ae-vara-rulebooks":
        # The tested URL is the official portal, not a proven rulebook row index.
        return "under_validation" if item_count else "needs_adapter"
    if source_id == "ae-dubai-official-gazette":
        # DLP root reachability is not item-level official gazette readiness.
        return "under_validation" if item_count else "mapped_only"
    return status


def _hash_items(items: list[dict]) -> str:
    payload = json.dumps(
        [
            {
                "title": item.get("title"),
                "date": item.get("date"),
                "url": item.get("url"),
                "document_url": item.get("document_url"),
            }
            for item in items
        ],
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _run_proof_target() -> dict:
    fsra_first = extract_fsra_circular_items()
    fsra_second = extract_fsra_circular_items()
    fsra_attempt = _build_proof_payload(
        proof_target="ae-adgm-fsra-circulars",
        proof_label="ADGM FSRA Circulars",
        source_page_url=DEFAULT_FSRA_CIRCULARS_URL,
        first=fsra_first,
        second=fsra_second,
        recommended_status="active_candidate" if fsra_first.get("item_count", 0) >= 3 else "needs_adapter",
        next_action="Create a stronger FSRA circular row adapter or isolate a publication endpoint before activation.",
        selected=False,
    )
    if fsra_first.get("item_count", 0) >= 3:
        fsra_attempt["selected"] = True
        fsra_attempt["selection_reason"] = "Preferred proof target produced structured circular rows."
        return fsra_attempt

    cbuae_first = extract_cbuae_rulebook_update_items()
    cbuae_second = extract_cbuae_rulebook_update_items()
    cbuae = _build_proof_payload(
        proof_target="ae-cbuae-rulebook-aml-payments",
        proof_label="CBUAE Rulebook revision updates",
        source_page_url=DEFAULT_CBUAE_RULEBOOK_UPDATES_URL,
        first=cbuae_first,
        second=cbuae_second,
        recommended_status="active_candidate" if cbuae_first.get("item_count", 0) >= 3 else "under_validation",
        next_action="Run scheduled proof/diff validation on CBUAE revision rows before activation.",
        selected=True,
    )
    cbuae["selection_reason"] = (
        "Preferred FSRA circulars target did not produce enough item rows; "
        "CBUAE Rulebook revision updates produced the strongest high-value row extraction candidate."
    )
    cbuae["fsra_attempt"] = fsra_attempt
    return cbuae


def _build_proof_payload(
    proof_target: str,
    proof_label: str,
    source_page_url: str,
    first: dict,
    second: dict,
    recommended_status: str,
    next_action: str,
    selected: bool,
) -> dict:
    first_items = first.get("items") or []
    second_items = second.get("items") or []
    first_titles = [item.get("title") for item in first_items[:3]]
    second_titles = [item.get("title") for item in second_items[:3]]
    first_urls = [item.get("url") for item in first_items[:3]]
    second_urls = [item.get("url") for item in second_items[:3]]
    return {
        "proof_target": proof_target,
        "proof_label": proof_label,
        "source_page_url": source_page_url,
        "first_run": first,
        "second_run": second,
        "same_run_stability": {
            "item_count_stable": first.get("item_count") == second.get("item_count"),
            "first_3_titles_stable": first_titles == second_titles,
            "first_3_urls_stable": first_urls == second_urls,
            "row_hash_stable": _hash_items(first_items) == _hash_items(second_items),
            "first_run_hash": _hash_items(first_items),
            "second_run_hash": _hash_items(second_items),
        },
        "limitation_notes": [
            "Same-run stability confirms deterministic extraction only.",
            "True change-diff still requires future scheduled comparison over time.",
            "The adapter/proof extraction is a prototype and is not wired into production monitoring.",
        ],
        "recommended_status": recommended_status,
        "next_validation_action": next_action,
        "selected": selected,
    }


def validate_sources() -> tuple[list[dict], dict]:
    metadata = _candidate_metadata()
    registry = _source_registry()
    results: list[dict] = []

    proof = _run_proof_target()
    proof_items = proof.get("first_run", {}).get("items") or []

    for target in TARGET_SOURCES:
        fetch_result = _fetch(target["official_url"])
        html = fetch_result.get("html") or ""
        extraction = extract_best_text(html, target["official_url"]) if html else {
            "text": "",
            "method": "none",
            "extracted_chars": 0,
            "quality": "failed",
        }
        items = _generic_items(html, fetch_result.get("final_url") or target["official_url"])
        if target["source_id"] == proof.get("proof_target") and proof_items:
            items = proof_items

        pdf_count = sum(1 for item in items if item.get("document_url") and str(item["document_url"]).lower().endswith(".pdf"))
        method = _classify_method(fetch_result.get("content_type") or "", extraction["extracted_chars"], len(items), pdf_count)
        status = _recommended_status(
            fetch_result.get("status"),
            extraction["extracted_chars"],
            len(items),
            method,
            fetch_result.get("error"),
        )
        status = _apply_source_specific_status(target, status, len(items))
        candidate = metadata.get(target["source_id"]) or metadata.get(_normalize_url(target["official_url"])) or {}
        limitations = _limitations(target, status, extraction["extracted_chars"], len(items), fetch_result)
        if candidate.get("risk_notes"):
            limitations.append(f"Candidate data note: {candidate['risk_notes']}")

        results.append(
            {
                "source_id": target["source_id"],
                "official_name": target["official_name"],
                "official_url": target["official_url"],
                "final_url": fetch_result.get("final_url"),
                "category": target["category"],
                "buyer_profiles": target["buyer_profiles"],
                "official_url_verification": {
                    "official_domain": _domain(target["official_url"]),
                    "http_reachable": bool(fetch_result.get("status") and fetch_result["status"] < 400),
                    "registry_status": _find_registry_status(target, registry),
                    "candidate_present": bool(candidate),
                },
                "http_status": fetch_result.get("status"),
                "content_type": fetch_result.get("content_type"),
                "extracted_chars": extraction["extracted_chars"],
                "extractor_method": extraction.get("method"),
                "item_count": len(items),
                "sample_items": items[:3],
                "extraction_method": method,
                "limitations": limitations,
                "recommended_status": status,
                "proof_target_boolean": target["source_id"] == proof.get("proof_target"),
                "adapter_created_boolean": target["source_id"] in {
                    "ae-adgm-fsra-circulars",
                    "ae-cbuae-rulebook-aml-payments",
                },
                "next_action": _next_action(status, target),
            }
        )
    return results, proof


def _status_counts(results: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        status = result["recommended_status"]
        counts[status] = counts.get(status, 0) + 1
    return counts


def _write_json(path: Path, results: list[dict], proof: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": "No source was activated. All recommendations require further proof/diff validation.",
        "sources": results,
        "status_counts": _status_counts(results),
        "proof_target": proof,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _md_escape(value: object) -> str:
    text = _clean(str(value or ""))
    return text.replace("|", "\\|")


def _write_markdown(path: Path, results: list[dict], proof: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = _status_counts(results)
    lines: list[str] = [
        "# UAE Official Source Expansion Validation",
        "",
        "## 1. Verdict",
        "",
        "No UAE source was activated in this sprint. The best current recommendation is to keep the tested sources in validation states until repeated extraction and proof/diff evidence is available. Mapped is not active; under validation is not active; needs adapter is not active.",
        "",
        "## 2. Sources tested",
        "",
    ]
    for result in results:
        lines.append(f"- {result['source_id']}: {result['official_name']} ({result['official_url']})")

    lines.extend(
        [
            "",
            "## 3. Official URL verification",
            "",
            "| Source | Official domain | HTTP reachable | Candidate data | Registry status |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for result in results:
        verify = result["official_url_verification"]
        lines.append(
            "| {source} | {domain} | {reachable} | {candidate} | {registry} |".format(
                source=_md_escape(result["source_id"]),
                domain=_md_escape(verify["official_domain"]),
                reachable="yes" if verify["http_reachable"] else "no",
                candidate="yes" if verify["candidate_present"] else "no",
                registry=_md_escape(verify.get("registry_status") or "not matched"),
            )
        )

    lines.extend(
        [
            "",
            "## 4. Extraction results table",
            "",
            "| Source | HTTP | Chars | Items | Method | Recommended status |",
            "|---|---:|---:|---:|---|---|",
        ]
    )
    for result in results:
        lines.append(
            "| {source} | {http} | {chars} | {items} | {method} | {status} |".format(
                source=_md_escape(result["source_id"]),
                http=_md_escape(result.get("http_status")),
                chars=result["extracted_chars"],
                items=result["item_count"],
                method=_md_escape(result["extraction_method"]),
                status=_md_escape(result["recommended_status"]),
            )
        )

    lines.extend(["", "## 5. Source-by-source findings", ""])
    for result in results:
        lines.extend(
            [
                f"### {result['official_name']}",
                "",
                f"- Source ID: `{result['source_id']}`",
                f"- Official URL: {result['official_url']}",
                f"- HTTP status: {result.get('http_status')}",
                f"- Extracted text length: {result['extracted_chars']}",
                f"- Item/document candidates: {result['item_count']}",
                f"- Recommended status: `{result['recommended_status']}`",
                f"- Next action: {result['next_action']}",
                "- Limitations:",
            ]
        )
        for note in result["limitations"]:
            lines.append(f"  - {note}")
        if result["sample_items"]:
            lines.append("- Sample items:")
            for item in result["sample_items"]:
                title = _clean(item.get("title"), 160)
                url = item.get("url") or item.get("document_url") or ""
                lines.append(f"  - {title} - {url}")
        lines.append("")

    proof_items = proof.get("first_run", {}).get("items") or []
    stability = proof.get("same_run_stability", {})
    fsra_attempt = proof.get("fsra_attempt") or {}
    lines.extend(
        [
            "## 6. Proof target selection",
            "",
            f"Selected proof target: `{proof.get('proof_target')}` - {proof.get('proof_label')}.",
            "",
            proof.get("selection_reason") or "The selected source produced the strongest row/item extraction evidence in this run.",
            "",
            "## 7. Adapter prototypes created",
            "",
            "- `app/adapters/uae_fsra_circulars.py` was created as a manually callable prototype.",
            "- `app/adapters/uae_cbuae_rulebook.py` was created as a manually callable prototype.",
            "- These prototypes are not registered in the production adapter registry and do not activate monitoring.",
            "",
            "## 8. Proof target row/item extraction result",
            "",
            f"- Source page: {proof.get('source_page_url')}",
            f"- First-run item count: {proof.get('first_run', {}).get('item_count')}",
            f"- Second-run item count: {proof.get('second_run', {}).get('item_count')}",
            f"- Recommended status: `{proof.get('recommended_status')}`",
            "",
        ]
    )
    if fsra_attempt:
        lines.extend(
            [
                "Preferred FSRA target attempt:",
                "",
                f"- FSRA first-run item count: {fsra_attempt.get('first_run', {}).get('item_count')}",
                f"- FSRA recommendation: `{fsra_attempt.get('recommended_status')}`",
                f"- FSRA next action: {fsra_attempt.get('next_validation_action')}",
                "",
            ]
        )

    lines.extend(
        [
            "| Title | Date | URL | Document |",
            "|---|---|---|---|",
        ]
    )
    for item in proof_items[:5]:
        lines.append(
            "| {title} | {date} | {url} | {doc} |".format(
                title=_md_escape(item.get("title")),
                date=_md_escape(item.get("date") or ""),
                url=_md_escape(item.get("url") or ""),
                doc=_md_escape(item.get("document_url") or ""),
            )
        )

    lines.extend(
        [
            "",
            "## 9. Same-run stability / proof-diff result",
            "",
            f"- Item count stable: {stability.get('item_count_stable')}",
            f"- First 3 titles stable: {stability.get('first_3_titles_stable')}",
            f"- First 3 URLs stable: {stability.get('first_3_urls_stable')}",
            f"- Row hash stable: {stability.get('row_hash_stable')}",
            "",
            "This is same-run stability proof only. True change-diff still requires future scheduled comparison against a later snapshot.",
            "",
            "## 10. Recommended status changes",
            "",
        ]
    )
    for status, count in sorted(counts.items()):
        lines.append(f"- `{status}`: {count}")

    lines.extend(
        [
            "",
            "No source should be marked active from this sprint alone.",
            "",
            "## 11. Sources NOT to activate yet",
            "",
        ]
    )
    for result in results:
        lines.append(f"- `{result['source_id']}` remains `{result['recommended_status']}` until proof/diff validation is complete.")

    lines.extend(
        [
            "",
            "## 12. Next validation actions",
            "",
            "- Run scheduled FSRA circulars proof/diff validation on multiple days.",
            "- Build targeted adapters for high-value sources where generic extraction returned navigation-only or low-quality content.",
            "- Validate item-level titles, dates, source proof URLs, and document/PDF handling before any activation.",
            "- Keep limitations near every public source-readiness claim.",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_proof_reports(markdown_path: Path, json_path: Path, proof: dict) -> tuple[Path, Path]:
    slug = re.sub(r"[^a-z0-9]+", "_", str(proof.get("proof_target") or "proof").lower()).strip("_")
    proof_json = json_path.with_name(f"source_validation_{slug}_proof_{TODAY}.json")
    proof_md = markdown_path.with_name(f"source_validation_{slug}_proof_{TODAY}.md")
    proof_json.write_text(json.dumps(proof, indent=2, ensure_ascii=False), encoding="utf-8")

    first_items = proof.get("first_run", {}).get("items") or []
    stability = proof.get("same_run_stability", {})
    lines = [
        f"# {proof.get('proof_label') or 'Source'} Proof Target",
        "",
        "## 1. Verdict",
        "",
        f"Selected proof target: {proof.get('proof_label')}. This does not activate monitoring. Same-run stability was checked; true proof/diff requires future scheduled comparison.",
        "",
        "## 2. Extraction result",
        "",
        f"- Source page: {proof.get('source_page_url')}",
        f"- First-run item count: {proof.get('first_run', {}).get('item_count')}",
        f"- Second-run item count: {proof.get('second_run', {}).get('item_count')}",
        f"- Recommended status: `{proof.get('recommended_status')}`",
        "",
        "## 3. Sample rows",
        "",
    ]
    for item in first_items[:5]:
        lines.extend(
            [
                f"- Title: {item.get('title')}",
                f"  - Date: {item.get('date') or 'not detected'}",
                f"  - URL: {item.get('url')}",
                f"  - Document URL: {item.get('document_url') or 'not detected'}",
            ]
        )
    lines.extend(
        [
            "",
            "## 4. Same-run stability",
            "",
            f"- Item count stable: {stability.get('item_count_stable')}",
            f"- First 3 titles stable: {stability.get('first_3_titles_stable')}",
            f"- First 3 URLs stable: {stability.get('first_3_urls_stable')}",
            f"- Row hash stable: {stability.get('row_hash_stable')}",
            "",
            "## 5. Limitations",
            "",
        ]
    )
    for note in proof.get("limitation_notes") or []:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## 6. Next validation action",
            "",
            proof.get("next_validation_action") or "Run repeated proof/diff validation before activation.",
        ]
    )
    proof_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return proof_json, proof_md


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UAE official source expansion targets.")
    parser.add_argument(
        "--output",
        default=f"reports/source_validation_uae_expansion_{TODAY}.json",
        help="JSON report output path.",
    )
    parser.add_argument(
        "--markdown",
        default=f"reports/source_validation_uae_expansion_{TODAY}.md",
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--write-registry",
        action="store_true",
        help="Reserved for future use. This sprint does not modify sources.json.",
    )
    args = parser.parse_args()

    if args.write_registry:
        print("--write-registry is intentionally disabled in this sprint; no registry files will be changed.")

    results, proof = validate_sources()
    output = Path(args.output)
    markdown = Path(args.markdown)
    _write_json(output, results, proof)
    _write_markdown(markdown, results, proof)
    proof_json, proof_md = _write_proof_reports(markdown, output, proof)

    print("source_id | URL | HTTP | extracted_chars | item_count | recommended_status")
    for result in results:
        print(
            "{source_id} | {url} | {http} | {chars} | {items} | {status}".format(
                source_id=result["source_id"],
                url=result["official_url"],
                http=result.get("http_status"),
                chars=result["extracted_chars"],
                items=result["item_count"],
                status=result["recommended_status"],
            )
        )
    print(f"Wrote JSON report: {output}")
    print(f"Wrote Markdown report: {markdown}")
    print(f"Wrote proof JSON: {proof_json}")
    print(f"Wrote proof Markdown: {proof_md}")
    print(f"Status counts: {_status_counts(results)}")
    if not any(result["recommended_status"] == "active_candidate" for result in results):
        print("Warning: no active_candidate sources found. No activation should be recommended.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
