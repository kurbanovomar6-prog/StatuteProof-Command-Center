#!/usr/bin/env python3
"""HTML-only proof/diff validation for selected ADGM/FSRA URLs.

This is a validation/reporting tool only. It does not edit source
configuration, activate monitoring, download PDFs, parse PDFs, call AI, send
alerts, or store full HTML bodies.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "reports" / "sprint3h_adgm_fsra_html_proof_diff_results.json"
REPORT_PATH = ROOT / "reports" / "sprint3h_adgm_fsra_html_proof_diff_report.md"

RUNS_PER_URL = 2
REQUEST_TIMEOUT_SECONDS = 12
SHORT_SPACING_SECONDS = 0.75
USER_AGENT = (
    "Mozilla/5.0 (compatible; StatuteProofADGMProofDiffValidation/1.0; "
    "+https://statuteproof.com)"
)

TARGET_URLS = [
    {
        "label": "AML Framework consultation announcement",
        "url": "https://www.adgm.com/media/announcements/adgm-fsra-launches-consultation-on-enhancements-to-its-aml-framework",
    },
    {
        "label": "Staking of Virtual Assets final framework announcement",
        "url": "https://www.adgm.com/media/announcements/adgm-fsra-finalises-regulatory-framework-for-the-staking-of-virtual-assets",
    },
    {
        "label": "Cyber Risk Management framework announcement",
        "url": "https://www.adgm.com/media/announcements/adgms-fsra-issues-cyber-risk-management-framework",
    },
    {
        "label": "FSRA Circulars listing page",
        "url": "https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars",
    },
]

NOISY_LINE_PATTERNS = (
    r"^about$",
    r"^business$",
    r"^contact.*support$",
    r"^discover$",
    r"^eservices$",
    r"^overview$",
    r"^privacy policy$",
    r"^terms and conditions$",
    r"^cookies policy$",
    r"^sitemap$",
    r"^all rights reserved$",
    r"^download arabic$",
    r"^view all$",
    r"^read more$",
    r"^learn more$",
    r"^search$",
    r"^submit$",
)

BLOCK_MARKERS = (
    "access denied",
    "request blocked",
    "cloudflare ray id",
    "checking your browser",
    "captcha",
    "imperva",
    "incapsula",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_html(url: str) -> dict[str, Any]:
    started = time.perf_counter()
    result: dict[str, Any] = {
        "url": url,
        "http_status": None,
        "final_url": url,
        "response_time_ms": 0,
        "content_type": "",
        "response_size_bytes": 0,
        "html": "",
        "error": "",
        "timeout_or_connection_error": False,
    }
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        result["http_status"] = response.status_code
        result["final_url"] = response.url
        result["content_type"] = response.headers.get("content-type", "").split(";", 1)[0].strip()
        result["response_size_bytes"] = len(response.content or b"")
        if "html" in result["content_type"] or "text" in result["content_type"] or not result["content_type"]:
            result["html"] = response.text
    except requests.Timeout as exc:
        result["timeout_or_connection_error"] = True
        result["error"] = f"timeout: {exc}"
    except requests.RequestException as exc:
        result["timeout_or_connection_error"] = True
        result["error"] = f"{type(exc).__name__}: {exc}"

    result["response_time_ms"] = round((time.perf_counter() - started) * 1000)
    return result


def normalize_visible_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    seen: set[str] = set()
    compiled_noise = [re.compile(pattern, re.I) for pattern in NOISY_LINE_PATTERNS]
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        if len(line) <= 2:
            continue
        if any(pattern.search(line) for pattern in compiled_noise):
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)
    return "\n".join(lines)


def text_hash(text: str) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_pdf_link(url: str) -> bool:
    return ".pdf" in urlparse(url).path.lower()


def is_official_document_link(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return (
        host == "adgm.com"
        or host.endswith(".adgm.com")
        or host.endswith("thomsonreuters.com")
    )


def extract_page(html: str, base_url: str) -> dict[str, Any]:
    lower = html.lower()
    soup = BeautifulSoup(html or "", "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    document_links: list[dict[str, Any]] = []
    pdf_links = set()
    for tag in soup.find_all("a", href=True):
        href = str(tag.get("href", "")).strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        if is_pdf_link(absolute):
            pdf_links.add(absolute)
        if is_official_document_link(absolute):
            text = tag.get_text(" ", strip=True)
            if text or is_pdf_link(absolute):
                document_links.append(
                    {
                        "text": text[:180],
                        "url": absolute,
                        "is_pdf": is_pdf_link(absolute),
                    }
                )

    for tag in soup(["script", "style", "noscript", "svg", "img", "iframe"]):
        tag.decompose()

    visible_text = soup.get_text("\n", strip=True)
    visible_text = re.sub(r"\n{3,}", "\n\n", visible_text)
    visible_text = re.sub(r"[ \t\xa0]+", " ", visible_text).strip()
    normalized = normalize_visible_text(visible_text)
    waf = any(marker in lower for marker in BLOCK_MARKERS)

    return {
        "page_title": title[:180],
        "extracted_text_chars": len(visible_text),
        "normalized_text_chars": len(normalized),
        "normalized_text_signature": text_hash(normalized),
        "has_pdf_links": bool(pdf_links),
        "pdf_link_count": len(pdf_links),
        "outbound_official_document_links": dedupe_links(document_links)[:25],
        "waf_or_blocked_signals": waf,
    }


def dedupe_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    rows = []
    for link in links:
        key = link["url"]
        if key in seen:
            continue
        seen.add(key)
        rows.append(link)
    return rows


def guess_item_type(url: str, title: str, label: str) -> str:
    haystack = f"{url} {title} {label}".lower()
    if "circulars" in haystack:
        return "circular_listing"
    if "consultation" in haystack:
        return "consultation_announcement"
    if "cyber" in haystack:
        return "guidance_announcement"
    if "framework" in haystack or "finalises" in haystack or "finalizes" in haystack:
        return "regulatory_framework_announcement"
    return "unknown"


def proof_quality_for(result: dict[str, Any]) -> str:
    if result["http_status"] is None or int(result["http_status"]) >= 400:
        return "unsuitable"
    if result["waf_or_blocked_signals"]:
        return "weak"
    if not result["signature_stable_across_runs"] or not result["title_stable_across_runs"]:
        return "weak"
    if result["normalized_text_chars"] >= 1800:
        return "strong"
    if result["normalized_text_chars"] >= 800:
        return "usable"
    return "weak"


def monitoring_suitability_for(result: dict[str, Any]) -> str:
    if result["proof_quality"] in {"unsuitable", "weak"}:
        return "unsuitable"
    if result["item_type_guess"] == "circular_listing":
        return "suitable_listing_needs_row_extraction"
    if result["item_type_guess"] in {
        "consultation_announcement",
        "regulatory_framework_announcement",
        "guidance_announcement",
    }:
        return "announcement_only_not_primary_source"
    return "needs_manual_mapping"


def recommended_action_for(result: dict[str, Any]) -> str:
    suitability = result["monitoring_suitability"]
    if suitability == "suitable_listing_needs_row_extraction":
        return "Run HTML-only row-extraction validation to isolate dated circular items before any activation decision."
    if suitability == "announcement_only_not_primary_source":
        return "Use as a source transparency/proof example; identify the underlying listing or rulebook source before monitored-source design."
    if suitability == "needs_manual_mapping":
        return "Map the official listing or item structure manually before proof/diff validation."
    return "Do not use for monitored-source design without further validation."


def limitation_notes_for(result: dict[str, Any]) -> list[str]:
    notes = [
        "HTML-only validation; full HTML body was not stored.",
        "PDF links were counted but not downloaded or parsed.",
    ]
    if result["has_pdf_links"]:
        notes.append("Linked PDF/document content is deferred for later validation.")
    if result["monitoring_suitability"] == "announcement_only_not_primary_source":
        notes.append("Media announcement pages are not ideal primary monitoring sources.")
    if result["monitoring_suitability"] == "suitable_listing_needs_row_extraction":
        notes.append("Listing page requires row-level extraction before monitoring design.")
    return notes


def run_url(target: dict[str, str]) -> dict[str, Any]:
    runs = []
    for run_number in range(1, RUNS_PER_URL + 1):
        print(f"Checking {run_number}/{RUNS_PER_URL}: {target['url']}")
        fetched = fetch_html(target["url"])
        extracted = extract_page(fetched["html"], fetched["final_url"])
        waf = bool(extracted["waf_or_blocked_signals"])
        if fetched["http_status"] in {401, 403, 429, 503}:
            waf = True
        elif waf and extracted["normalized_text_chars"] >= 1000:
            title = str(extracted["page_title"]).lower()
            if not any(marker in title for marker in ("access denied", "captcha", "cloudflare")):
                waf = False
        runs.append(
            {
                "run_number": run_number,
                "checked_at_utc": utc_now(),
                "url": target["url"],
                "final_url": fetched["final_url"],
                "http_status": fetched["http_status"],
                "response_time_ms": fetched["response_time_ms"],
                "content_type": fetched["content_type"],
                "response_size_bytes": fetched["response_size_bytes"],
                "page_title": extracted["page_title"],
                "extracted_text_chars": extracted["extracted_text_chars"],
                "normalized_text_chars": extracted["normalized_text_chars"],
                "normalized_text_signature": extracted["normalized_text_signature"],
                "has_pdf_links": extracted["has_pdf_links"],
                "pdf_link_count": extracted["pdf_link_count"],
                "pdf_downloaded": False,
                "pdf_parsed": False,
                "outbound_official_document_links": extracted["outbound_official_document_links"],
                "waf_or_blocked_signals": waf,
                "timeout_or_connection_error": fetched["timeout_or_connection_error"],
                "error": fetched["error"][:260],
            }
        )
        if run_number < RUNS_PER_URL:
            time.sleep(SHORT_SPACING_SECONDS)

    titles = [run["page_title"] for run in runs]
    signatures = [run["normalized_text_signature"] for run in runs if run["normalized_text_signature"]]
    latest = runs[-1]
    result = {
        "label": target["label"],
        "url": target["url"],
        "page_title": latest["page_title"],
        "item_type_guess": guess_item_type(target["url"], latest["page_title"], target["label"]),
        "http_status": latest["http_status"],
        "average_response_time_ms": round(mean([run["response_time_ms"] for run in runs])),
        "content_type": latest["content_type"],
        "extracted_text_chars": latest["extracted_text_chars"],
        "normalized_text_chars": latest["normalized_text_chars"],
        "normalized_text_signature": latest["normalized_text_signature"],
        "signature_stable_across_runs": len(set(signatures)) == 1 if signatures else False,
        "title_stable_across_runs": len(set(titles)) == 1,
        "has_pdf_links": latest["has_pdf_links"],
        "pdf_link_count": latest["pdf_link_count"],
        "pdf_downloaded": False,
        "pdf_parsed": False,
        "outbound_official_document_links": latest["outbound_official_document_links"],
        "waf_or_blocked_signals": any(run["waf_or_blocked_signals"] for run in runs),
        "runs": runs,
    }
    result["proof_quality"] = proof_quality_for(result)
    result["monitoring_suitability"] = monitoring_suitability_for(result)
    result["limitation_notes"] = limitation_notes_for(result)
    result["recommended_next_action"] = recommended_action_for(result)
    result["proof_artifact"] = {
        "source_name": "ADGM/FSRA HTML validation candidate",
        "official_url": target["url"],
        "final_url": latest["final_url"],
        "checked_at_utc": latest["checked_at_utc"],
        "fetch_method": "requests_html_only",
        "extraction_method": "beautifulsoup_visible_text_normalized",
        "normalized_text_signature": latest["normalized_text_signature"],
        "normalized_text_chars": latest["normalized_text_chars"],
        "pdf_links_count": latest["pdf_link_count"],
        "pdf_downloaded": False,
        "pdf_parsed": False,
        "proof_quality": result["proof_quality"],
        "limitations": result["limitation_notes"],
    }
    return result


def build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Sprint 3H — ADGM/FSRA HTML Proof/Diff Validation Report",
        "",
        "## 1. Verdict",
        "",
        "- This was validation-only.",
        "- No sources were activated.",
        "- PDF scanning was avoided; PDF links were counted only.",
        f"- URLs tested: {payload['urls_tested']}.",
        "- Stable normalized HTML signatures: "
        + ", ".join(short_title(row) for row in payload["results"] if row["signature_stable_across_runs"]),
        "- Future proof/diff candidates are listed below as candidates only, not active sources.",
        "- Announcement pages are useful proof examples but are not ideal primary monitoring sources.",
        "",
        "## 2. URL test results",
        "",
        "| URL / short title | Type | HTTP status | Extracted HTML chars | Signature stable | PDF links | Proof quality | Monitoring suitability | Recommended next action |",
        "| --- | --- | ---: | ---: | --- | ---: | --- | --- | --- |",
    ]
    for row in payload["results"]:
        lines.append(
            "| {title} | {item_type} | {status} | {chars} | {stable} | {pdf_count} | {quality} | {suitability} | {action} |".format(
                title=md_cell(f"{row['label']} ({row['url']})"),
                item_type=row["item_type_guess"],
                status=row["http_status"] if row["http_status"] is not None else "error",
                chars=row["extracted_text_chars"],
                stable=yes_no(row["signature_stable_across_runs"]),
                pdf_count=row["pdf_link_count"],
                quality=row["proof_quality"],
                suitability=row["monitoring_suitability"],
                action=md_cell(row["recommended_next_action"]),
            )
        )

    lines.extend(["", "## 3. Best candidates", ""])
    if payload["stable_html_candidates"]:
        lines.append("HTML/source-transparency candidates:")
        for row in payload["stable_html_candidates"]:
            lines.append(
                f"- `{row['url']}` — {row['monitoring_suitability']}; candidate for future monitored source design only after upstream listing validation."
            )
    else:
        lines.append("- No standalone HTML item page is ready as a primary monitored-source design.")
    if payload["listing_candidates_needing_row_extraction"]:
        lines.append("")
        lines.append("Listing row-extraction candidates:")
        for row in payload["listing_candidates_needing_row_extraction"]:
            lines.append(f"- `{row['url']}` — ready for row-extraction validation.")

    lines.extend(
        [
            "",
            "## 4. Announcement-page limitation",
            "",
            "ADGM/FSRA announcement pages are useful as examples and proof/diff candidates, but they may not be the best primary monitoring source because they are media announcements. The better primary source may be the FSRA circulars listing, public consultations listing, rulebook/listing pages, or row-level extraction from official listings.",
            "",
            "## 5. PDF-deferred notes",
            "",
            "PDF links were counted but not downloaded or parsed in this sprint.",
        ]
    )
    if payload["pdf_deferred_links_summary"]:
        for row in payload["pdf_deferred_links_summary"]:
            lines.append(f"- `{row['url']}` — {row['pdf_link_count']} PDF/document link(s) deferred.")
    else:
        lines.append("- No PDF links were detected on the tested HTML output.")

    lines.extend(
        [
            "",
            "## 6. Recommended Sprint 3I",
            "",
            payload["recommended_next_sprint"],
        ]
    )
    return "\n".join(lines) + "\n"


def short_title(row: dict[str, Any]) -> str:
    return row["label"]


def md_cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).replace("|", "\\|").replace("\n", " ")).strip()


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def main() -> None:
    results = [run_url(target) for target in TARGET_URLS]
    stable_html_candidates = [
        row for row in results
        if row["proof_quality"] in {"strong", "usable"}
        and row["signature_stable_across_runs"]
        and row["monitoring_suitability"] == "announcement_only_not_primary_source"
    ]
    listing_candidates = [
        row for row in results
        if row["monitoring_suitability"] == "suitable_listing_needs_row_extraction"
    ]
    announcement_only = [
        row for row in results
        if row["monitoring_suitability"] == "announcement_only_not_primary_source"
    ]
    pdf_deferred = [
        {
            "url": row["url"],
            "label": row["label"],
            "pdf_link_count": row["pdf_link_count"],
            "links": [
                link for link in row["outbound_official_document_links"]
                if link["is_pdf"]
            ][:10],
        }
        for row in results if row["has_pdf_links"]
    ]

    payload = {
        "run_timestamp_utc": utc_now(),
        "urls_tested": len(TARGET_URLS),
        "results": results,
        "stable_html_candidates": stable_html_candidates,
        "listing_candidates_needing_row_extraction": listing_candidates,
        "announcement_only_candidates": announcement_only,
        "pdf_deferred_links_summary": pdf_deferred,
        "recommended_next_sprint": "Sprint 3I should validate FSRA circular listing row extraction, HTML-only. Do not activate the source until row extraction, proof/diff output, and limitation notes are tested.",
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(build_report(payload), encoding="utf-8")
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
