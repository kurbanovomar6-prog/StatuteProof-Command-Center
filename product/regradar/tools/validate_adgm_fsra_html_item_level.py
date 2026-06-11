#!/usr/bin/env python3
"""HTML-only ADGM/FSRA item-level validation.

This validation tool is intentionally separate from active monitoring. It does
not edit source configuration, download PDFs, parse PDFs, store response
bodies, send alerts, call AI, or activate any source.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
UNDER_VALIDATION_PATH = ROOT / "data" / "uae_under_validation_sources.json"
CANDIDATES_PATH = ROOT / "data" / "uae_source_candidates.json"
SPRINT_3E_REPORT_PATH = ROOT / "reports" / "sprint3e_under_validation_stability_report.md"
RESULTS_PATH = ROOT / "reports" / "sprint3f_adgm_fsra_html_item_level_results.json"
REPORT_PATH = ROOT / "reports" / "sprint3f_adgm_fsra_html_item_level_report.md"

REQUEST_TIMEOUT_SECONDS = 12
SHORT_SPACING_SECONDS = 0.5
MAX_DISCOVERED_ITEMS = 20
MAX_REPEATED_ITEMS = 10
RUNS_PER_ITEM = 3
MIN_USEFUL_HTML_CHARS = 900
USER_AGENT = (
    "Mozilla/5.0 (compatible; StatuteProofADGMHtmlValidation/1.0; "
    "+https://statuteproof.com)"
)

ITEM_KEYWORDS = (
    "circular",
    "consultation",
    "consultations",
    "guidance",
    "notice",
    "notices",
    "publication",
    "publications",
    "rulebook",
    "rules",
    "regulation",
    "regulations",
    "financial-services-regulatory-authority",
    "fsra",
)

GENERIC_PATH_PARTS = {
    "",
    "about",
    "contact-us",
    "careers",
    "media",
    "events",
    "setting-up",
    "operating-in-adgm",
    "privacy-policy",
    "terms-and-conditions",
}

JS_MARKERS = (
    "__next_data__",
    "webpack",
    "reactroot",
    "ng-version",
    "id=\"app\"",
    "id=\"root\"",
    "enable javascript",
    "please enable javascript",
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


def read_json(path: Path) -> Any:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def is_adgm_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host == "adgm.com" or host.endswith(".adgm.com")


def is_pdf_like_url(url: str) -> bool:
    parsed = urlparse(url)
    return ".pdf" in parsed.path.lower()


def normalize_url(url: str) -> str:
    clean, _fragment = urldefrag(url)
    return clean.rstrip("/")


def load_discovery_sources() -> list[dict[str, str]]:
    sources: dict[str, dict[str, str]] = {}

    for row in read_json(UNDER_VALIDATION_PATH):
        haystack = " ".join(
            str(row.get(key, ""))
            for key in ("candidate_id", "name", "source_layer_name", "url")
        ).lower()
        if "fsra" not in haystack and "financial services regulatory" not in haystack:
            continue
        url = row.get("url")
        if not url or not is_adgm_url(url):
            continue
        sources[normalize_url(url)] = {
            "url": normalize_url(url),
            "source_layer": row.get("source_layer_name", row.get("name", "ADGM/FSRA")),
            "source": "uae_under_validation_sources",
        }

    for row in read_json(CANDIDATES_PATH):
        haystack = " ".join(
            str(row.get(key, ""))
            for key in ("candidate_id", "official_name", "source_layer_name", "official_url")
        ).lower()
        if "fsra" not in haystack and "financial services regulatory" not in haystack:
            continue
        url = row.get("official_url")
        if not url or not is_adgm_url(url):
            continue
        sources.setdefault(
            normalize_url(url),
            {
                "url": normalize_url(url),
                "source_layer": row.get("source_layer_name", "ADGM/FSRA"),
                "source": "uae_source_candidates",
            },
        )

    if SPRINT_3E_REPORT_PATH.exists():
        report_text = SPRINT_3E_REPORT_PATH.read_text(encoding="utf-8")
        for url in sorted(set(re.findall(r"https://www\.adgm\.com/[^\s|`)]+", report_text))):
            sources.setdefault(
                normalize_url(url),
                {
                    "url": normalize_url(url),
                    "source_layer": "ADGM/FSRA Sprint 3E reference",
                    "source": "sprint3e_report",
                },
            )

    return list(sources.values())


def normalize_visible_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    seen = set()
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)
    return "\n".join(lines)


def content_signature(text: str) -> str | None:
    normalized = normalize_visible_text(text)
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


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


def extract_page(html: str) -> dict[str, Any]:
    lower = html.lower()
    soup = BeautifulSoup(html or "", "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    anchors = []
    pdf_links = []
    for tag in soup.find_all("a", href=True):
        href = str(tag.get("href", "")).strip()
        text = tag.get_text(" ", strip=True)
        if not href:
            continue
        anchors.append({"href": href, "text": text[:220]})
        clean_path = href.split("?", 1)[0].lower()
        if clean_path.endswith(".pdf"):
            pdf_links.append(href)

    for tag in soup(["script", "style", "noscript", "svg", "img", "iframe"]):
        tag.decompose()
    visible_text = soup.get_text("\n", strip=True)
    visible_text = re.sub(r"\n{3,}", "\n\n", visible_text)
    visible_text = re.sub(r"[ \t\xa0]+", " ", visible_text).strip()

    return {
        "page_title": title[:180],
        "visible_text": visible_text,
        "extracted_html_text_chars": len(visible_text),
        "content_signature": content_signature(visible_text),
        "anchors": anchors,
        "has_pdf_links": bool(pdf_links),
        "pdf_link_count": len(set(pdf_links)),
        "has_js_signals": any(marker in lower for marker in JS_MARKERS),
        "waf_or_blocked_signals": any(marker in lower for marker in BLOCK_MARKERS),
    }


def guess_item_type(url: str, title: str, link_text: str = "") -> str:
    haystack = f"{url} {title} {link_text}".lower()
    if "circular" in haystack:
        return "circular"
    if "consultation" in haystack:
        return "consultation"
    if "guidance" in haystack or "guide" in haystack:
        return "guidance"
    if "rulebook" in haystack or "rule-book" in haystack or "rules" in haystack:
        return "rulebook"
    if "notice" in haystack:
        return "notice"
    return "unknown"


def link_score(url: str, text: str) -> int:
    parsed = urlparse(url)
    path = parsed.path.lower().strip("/")
    if not is_adgm_url(url):
        return -20
    if path.split("/")[-1] in GENERIC_PATH_PARTS:
        return -5
    if is_pdf_like_url(url):
        return -10
    haystack = f"{path} {text}".lower()
    score = 0
    score += sum(4 for keyword in ITEM_KEYWORDS if keyword in haystack)
    score += min(path.count("/"), 5)
    if "financial-services-regulatory-authority" in haystack:
        score += 4
    if text and len(text) >= 12:
        score += 1
    return score


def discover_item_urls(discovery_sources: list[dict[str, str]]) -> list[dict[str, Any]]:
    discovered: dict[str, dict[str, Any]] = {}
    for source in discovery_sources:
        seed_url = source["url"]
        print(f"Discovering ADGM links from {seed_url}")
        fetched = fetch_html(seed_url)
        extracted = extract_page(fetched["html"])
        if fetched["http_status"] is None or not fetched["html"]:
            continue
        for anchor in extracted["anchors"]:
            raw_href = anchor["href"]
            if raw_href.startswith(("mailto:", "tel:", "javascript:")):
                continue
            absolute = normalize_url(urljoin(fetched["final_url"], raw_href))
            if not is_adgm_url(absolute):
                continue
            if is_pdf_like_url(absolute):
                continue
            score = link_score(absolute, anchor["text"])
            if score < 4:
                continue
            existing = discovered.get(absolute)
            row = {
                "item_url": absolute,
                "source_layer": source["source_layer"],
                "discovered_from": seed_url,
                "link_text": anchor["text"],
                "discovery_score": score,
            }
            if not existing or score > int(existing["discovery_score"]):
                discovered[absolute] = row
        time.sleep(SHORT_SPACING_SECONDS)

    rows = sorted(
        discovered.values(),
        key=lambda item: (-int(item["discovery_score"]), item["item_url"]),
    )
    return rows[:MAX_DISCOVERED_ITEMS]


def confidence_for_item(row: dict[str, Any]) -> tuple[str, str]:
    status = row.get("http_status")
    text_chars = int(row.get("extracted_html_text_chars") or 0)
    title = str(row.get("title_text") or "")
    item_type = row.get("item_type_guess")
    path_depth = urlparse(str(row.get("item_url", ""))).path.strip("/").count("/")
    if status is None or int(status) >= 400:
        return "low", "HTTP check failed or returned an error status."
    if row.get("waf_or_blocked_signals"):
        return "low", "Blocked/WAF-like content was detected."
    if text_chars >= 1800 and title and item_type != "unknown" and path_depth >= 2:
        return "high", "Official ADGM HTML page with useful text, title, and regulatory URL signals."
    if text_chars >= MIN_USEFUL_HTML_CHARS and title:
        return "medium", "Official ADGM HTML page with useful text but item type or depth remains uncertain."
    return "low", "HTML text is thin or item-level signals are weak."


def test_item_once(item: dict[str, Any]) -> dict[str, Any]:
    fetched = fetch_html(item["item_url"])
    extracted = extract_page(fetched["html"])
    status = fetched["http_status"]
    waf = bool(extracted["waf_or_blocked_signals"])
    if status in {401, 403, 429, 503}:
        waf = True
    elif waf and extracted["extracted_html_text_chars"] >= 1000:
        title = str(extracted["page_title"]).lower()
        if not any(marker in title for marker in ("access denied", "captcha", "cloudflare")):
            waf = False

    row = {
        "item_url": item["item_url"],
        "source_layer": item["source_layer"],
        "discovered_from": item["discovered_from"],
        "item_title": extracted["page_title"] or item.get("link_text", ""),
        "link_text": item.get("link_text", ""),
        "item_type_guess": guess_item_type(
            item["item_url"],
            extracted["page_title"],
            item.get("link_text", ""),
        ),
        "http_status": status,
        "final_url": fetched["final_url"],
        "response_time_ms": fetched["response_time_ms"],
        "content_type": fetched["content_type"],
        "response_size_bytes": fetched["response_size_bytes"],
        "extracted_html_text_chars": extracted["extracted_html_text_chars"],
        "title_text": extracted["page_title"],
        "content_signature": extracted["content_signature"],
        "has_pdf_links": extracted["has_pdf_links"],
        "pdf_link_count": extracted["pdf_link_count"],
        "pdf_downloaded": False,
        "pdf_parsed": False,
        "has_js_signals": extracted["has_js_signals"],
        "waf_or_blocked_signals": waf,
        "timeout_or_connection_error": fetched["timeout_or_connection_error"],
        "error": fetched["error"][:260],
        "limitation_notes": "HTML-only validation. PDF links were counted but not downloaded or parsed.",
    }
    confidence, reason = confidence_for_item(row)
    row["item_level_confidence"] = confidence
    row["why_confidence_assigned"] = reason
    return row


def stable_unique(values: list[Any]) -> bool:
    return len({json.dumps(value, sort_keys=True) for value in values}) <= 1


def suitability_for_repeated(runs: list[dict[str, Any]]) -> str:
    successes = [
        run for run in runs
        if not run["timeout_or_connection_error"]
        and run["http_status"] is not None
        and 200 <= int(run["http_status"]) < 400
    ]
    if len(successes) != len(runs):
        return "unsuitable"
    if any(run["waf_or_blocked_signals"] for run in runs):
        return "unsuitable"

    title_stable = stable_unique([run["title_text"] for run in runs])
    signature_stable = stable_unique([run["content_signature"] for run in runs if run["content_signature"]])
    pdf_stable = stable_unique([run["pdf_link_count"] for run in runs])
    avg_chars = round(mean([int(run["extracted_html_text_chars"] or 0) for run in runs]))
    pdf_seen = any(run["has_pdf_links"] for run in runs)
    item_types = {run["item_type_guess"] for run in runs}

    if not title_stable or not signature_stable:
        return "needs_manual_mapping"
    if avg_chars < MIN_USEFUL_HTML_CHARS and pdf_seen:
        return "needs_pdf_validation_later"
    if avg_chars < MIN_USEFUL_HTML_CHARS:
        return "unsuitable"
    if pdf_seen and pdf_stable:
        return "suitable_html_with_pdf_links_ignored"
    if item_types == {"unknown"}:
        return "needs_manual_mapping"
    return "suitable_html_item"


def repeated_check(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = sorted(
        items,
        key=lambda row: (
            {"high": 0, "medium": 1, "low": 2}.get(str(row["item_level_confidence"]), 3),
            -int(row["extracted_html_text_chars"] or 0),
            row["item_url"],
        ),
    )[:MAX_REPEATED_ITEMS]

    summaries = []
    for item in selected:
        runs = []
        for run_number in range(1, RUNS_PER_ITEM + 1):
            print(f"Repeated check {run_number}/{RUNS_PER_ITEM}: {item['item_url']}")
            run = test_item_once(item)
            run["run_number"] = run_number
            run["timestamp_utc"] = utc_now()
            runs.append(run)
            if run_number < RUNS_PER_ITEM:
                time.sleep(SHORT_SPACING_SECONDS)

        successes = [
            run for run in runs
            if not run["timeout_or_connection_error"]
            and run["http_status"] is not None
            and 200 <= int(run["http_status"]) < 400
        ]
        summary = {
            "item_url": item["item_url"],
            "item_title": runs[-1]["item_title"],
            "item_type_guess": runs[-1]["item_type_guess"],
            "runs": runs,
            "runs_passed": len(successes),
            "status_stable": stable_unique([run["http_status"] for run in runs]),
            "title_stable": stable_unique([run["title_text"] for run in runs]),
            "html_content_signature_stable": stable_unique(
                [run["content_signature"] for run in runs if run["content_signature"]]
            ),
            "pdf_link_count_stable": stable_unique([run["pdf_link_count"] for run in runs]),
            "waf_seen": any(run["waf_or_blocked_signals"] for run in runs),
            "average_extracted_html_text_chars": round(
                mean([int(run["extracted_html_text_chars"] or 0) for run in runs])
            ),
            "suitability_verdict": suitability_for_repeated(runs),
        }
        summaries.append(summary)
    return summaries


def build_report(results: dict[str, Any]) -> str:
    lines = [
        "# Sprint 3F — ADGM/FSRA HTML Item-Level Validation Report",
        "",
        "## 1. Verdict",
        "",
        "- This was validation-only.",
        "- No sources were activated.",
        "- PDF scanning was avoided; PDF links were counted only.",
        f"- ADGM/FSRA discovered HTML item-level candidates: {results['discovered_item_count']}.",
        f"- Item-level URLs tested repeatedly: {results['tested_item_count']}.",
        (
            "- HTML item-level monitoring potential: "
            f"{len(results['suitable_html_item_candidates'])} candidate(s) ready for proof/diff test."
        ),
        "",
        "## 2. Discovered HTML item-level candidates",
        "",
        "| Item title | Item URL | Item type | HTTP status | Extracted HTML chars | PDF links present | PDF parsed? | Item-level confidence | Notes |",
        "| --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for item in results["item_results"]:
        lines.append(
            "| {title} | {url} | {item_type} | {status} | {chars} | {pdf} | No | {confidence} | {notes} |".format(
                title=md_cell(item["item_title"] or item["link_text"] or "Untitled"),
                url=md_cell(item["item_url"]),
                item_type=item["item_type_guess"],
                status=item["http_status"] if item["http_status"] is not None else "error",
                chars=item["extracted_html_text_chars"],
                pdf="yes" if item["has_pdf_links"] else "no",
                confidence=item["item_level_confidence"],
                notes=md_cell(item["why_confidence_assigned"]),
            )
        )

    lines.extend([
        "",
        "## 3. Repeated-run results",
        "",
        "| Item URL | Runs passed | Status stable | Title stable | HTML content signature stable | PDF link count stable | Suitability verdict |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ])
    for row in results["repeated_run_summary"]:
        lines.append(
            "| {url} | {passed}/{total} | {status} | {title} | {signature} | {pdf} | {verdict} |".format(
                url=md_cell(row["item_url"]),
                passed=row["runs_passed"],
                total=RUNS_PER_ITEM,
                status=yes_no(row["status_stable"]),
                title=yes_no(row["title_stable"]),
                signature=yes_no(row["html_content_signature_stable"]),
                pdf=yes_no(row["pdf_link_count_stable"]),
                verdict=row["suitability_verdict"],
            )
        )

    lines.extend([
        "",
        "## 4. Best ADGM/FSRA HTML candidates for future proof/diff test",
        "",
    ])
    if results["suitable_html_item_candidates"]:
        for row in results["suitable_html_item_candidates"]:
            lines.append(
                f"- `{row['item_url']}` — {row['suitability_verdict']}; ready for proof/diff test."
            )
    else:
        lines.append("- None. No ADGM/FSRA HTML item should move to proof/diff test from this run.")

    lines.extend([
        "",
        "## 5. PDF-deferred candidates",
        "",
    ])
    if results["pdf_deferred_items"]:
        for row in results["pdf_deferred_items"]:
            lines.append(f"- `{row['item_url']}` — needs_pdf_validation_later.")
    else:
        lines.append("- None.")

    lines.extend([
        "",
        "## 6. Limitations",
        "",
        "- PDF content was intentionally not scanned.",
        "- HTML-only validation may miss document text inside PDFs.",
        "- Rulebook pages may require a separate item-level adapter later.",
        "- Generic listing pages are not enough for customer-ready monitoring.",
        "- Item-level discovery is incomplete and limited to a small, conservative crawl.",
        "",
        "## 7. Recommended Sprint 3G",
        "",
        "Run ADGM/FSRA HTML proof/diff testing for the best 1-3 HTML item-level URLs only after this validation identifies stable, useful pages. Do not move to source activation until proof/diff output is tested.",
    ])
    return "\n".join(lines) + "\n"


def md_cell(value: Any) -> str:
    text = str(value).replace("|", "\\|").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def main() -> None:
    discovery_sources = load_discovery_sources()
    print(f"Loaded {len(discovery_sources)} ADGM/FSRA discovery source(s)")

    discovered = discover_item_urls(discovery_sources)
    print(f"Discovered {len(discovered)} candidate HTML item URL(s)")

    item_results = []
    for index, item in enumerate(discovered, start=1):
        print(f"Testing discovered item {index}/{len(discovered)}: {item['item_url']}")
        item_results.append(test_item_once(item))
        time.sleep(SHORT_SPACING_SECONDS)

    repeated_summary = repeated_check(item_results)
    suitable = [
        row for row in repeated_summary
        if row["suitability_verdict"] in {
            "suitable_html_item",
            "suitable_html_with_pdf_links_ignored",
        }
        and not row["waf_seen"]
    ]
    pdf_deferred = [
        row for row in repeated_summary
        if row["suitability_verdict"] == "needs_pdf_validation_later"
    ]
    uncertain = [
        row for row in repeated_summary
        if row["suitability_verdict"] not in {
            "suitable_html_item",
            "suitable_html_with_pdf_links_ignored",
            "needs_pdf_validation_later",
        }
    ]

    results = {
        "run_timestamp_utc": utc_now(),
        "discovery_sources": discovery_sources,
        "discovered_item_count": len(discovered),
        "tested_item_count": len(repeated_summary),
        "item_results": item_results,
        "repeated_run_summary": repeated_summary,
        "suitable_html_item_candidates": suitable,
        "pdf_deferred_items": pdf_deferred,
        "unsuitable_or_uncertain_items": uncertain,
        "summary_counts": dict(Counter(row["suitability_verdict"] for row in repeated_summary)),
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(build_report(results), encoding="utf-8")
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
