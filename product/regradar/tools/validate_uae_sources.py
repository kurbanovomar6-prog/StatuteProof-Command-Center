#!/usr/bin/env python3
"""Validate UAE source candidates with low-volume HTTP checks.

This is a planning tool only. It does not modify sources.json, activate
monitoring, call AI, send Telegram messages, or store full response bodies.
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_PATH = ROOT / "data" / "uae_source_candidates.json"
RESULTS_PATH = ROOT / "reports" / "sprint3c_uae_source_validation_results.json"
REPORT_PATH = ROOT / "reports" / "sprint3c_uae_source_speed_reliability_report.md"

TIMEOUT_SECONDS = 12
USER_AGENT = (
    "Mozilla/5.0 (compatible; StatuteProofSourceValidation/1.0; "
    "+https://statuteproof.com)"
)

PRIMARY_CANDIDATE_IDS = [
    "ae-cbuae-main-publications",
    "ae-cbuae-rulebook",
    "ae-cbuae-payments",
    "ae-vara-main-publications",
    "ae-vara-rulebooks",
    "ae-dfsa-rulebook",
    "ae-difc-laws",
    "ae-adgm-fsra-main",
    "ae-adgm-fsra-rulebook",
    "ae-uaefiu-publications",
    "ae-fta-legislation",
    "ae-sca-cma-regulations-circulars",
    "ae-uae-legislation-federal-laws",
    "ae-moet-aml-dnfbp",
    "ae-eocn-sanctions",
]

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
    "forbidden",
    "request blocked",
    "cloudflare ray id",
    "checking your browser",
    "captcha",
    "imperva",
    "incapsula",
)

ITEM_KEYWORDS = (
    "publication",
    "circular",
    "rulebook",
    "regulation",
    "consultation",
    "notice",
    "law",
    "decree",
    "guidance",
    "clarification",
    "decision",
    "pdf",
)


def load_candidates() -> list[dict[str, Any]]:
    rows = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    by_id = {row["candidate_id"]: row for row in rows}
    selected = [by_id[cid] for cid in PRIMARY_CANDIDATE_IDS if cid in by_id]
    if len(selected) < 15:
        p0_rows = [row for row in rows if row.get("validation_priority") == "P0"]
        for row in p0_rows:
            if row not in selected:
                selected.append(row)
            if len(selected) >= 15:
                break
    return selected[:15]


def clean_text_and_title(html: str) -> tuple[str, str, bool, bool, bool]:
    lower = html.lower()
    has_js = any(marker in lower for marker in JS_MARKERS)
    waf = any(marker in lower for marker in BLOCK_MARKERS)

    soup = BeautifulSoup(html or "", "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    has_pdf = any(
        str(a.get("href", "")).split("?", 1)[0].lower().endswith(".pdf")
        for a in soup.find_all("a", href=True)
    )

    for tag in soup(["script", "style", "noscript", "svg", "img", "iframe"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t\xa0]+", " ", text).strip()
    return title, text, has_pdf, has_js, waf


def item_level_potential(html: str, extracted_chars: int, has_pdf: bool) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    useful_links = 0
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a.get("href") or "").strip()
        label = a.get_text(" ", strip=True).lower()
        haystack = f"{href.lower()} {label}"
        if href and href not in seen and any(keyword in haystack for keyword in ITEM_KEYWORDS):
            seen.add(href)
            useful_links += 1
    if useful_links >= 8:
        return "high"
    if useful_links >= 3 or has_pdf:
        return "medium"
    if extracted_chars >= 1500:
        return "low"
    return "unknown"


def recommend_status(
    *,
    candidate: dict[str, Any],
    http_status: int | None,
    extracted_chars: int,
    has_pdf: bool,
    has_js: bool,
    waf_or_blocked: bool,
    timeout_or_error: bool,
) -> tuple[str, str]:
    if candidate.get("proposed_status") == "avoid_for_now":
        return "avoid_for_now", "Candidate is official but outside the first financial-regulatory validation scope."
    if timeout_or_error:
        return "blocked", "Timeout or connection error during conservative GET check."
    if waf_or_blocked or http_status in {401, 403, 429, 503}:
        return "needs_waf_workaround", "Blocked or WAF-like response detected during basic HTTP check."
    if has_js and extracted_chars < 1000:
        return "needs_js_rendering", "Page appears JavaScript-heavy and returned low extracted text."
    if has_pdf and extracted_chars < 1500:
        return "needs_pdf_validation", "PDF links were found but HTML text is not enough for source validation."
    if extracted_chars < 500:
        return "limited", "Very low extracted text from basic HTTP response."
    if has_pdf and candidate.get("expected_extraction") in {"html_plus_pdf", "pdf_primary"}:
        return "needs_pdf_validation", "HTML is accessible but PDF dependency should be validated before monitoring."
    if http_status and 200 <= http_status < 400:
        return "validation_pass_candidate", "Accessible via basic HTTP and produced usable extracted text."
    return "limited", "Response was reachable but needs manual review before any monitoring decision."


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    url = candidate["official_url"]
    started = time.perf_counter()
    http_status = None
    final_url = url
    content_type = ""
    response_size = 0
    title = ""
    extracted_chars = 0
    has_pdf = False
    has_js = False
    waf_or_blocked = False
    timeout_or_error = False
    error = ""
    html = ""

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        http_status = response.status_code
        final_url = response.url
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
        body = response.content or b""
        response_size = len(body)
        if "text" in content_type or "html" in content_type or not content_type:
            html = response.text
            title, text, has_pdf, has_js, waf_or_blocked = clean_text_and_title(html)
            extracted_chars = len(text)
    except requests.Timeout as exc:
        timeout_or_error = True
        error = f"timeout: {exc}"
    except requests.RequestException as exc:
        timeout_or_error = True
        error = f"{type(exc).__name__}: {exc}"

    response_time_ms = round((time.perf_counter() - started) * 1000)
    if http_status in {401, 403, 429, 503}:
        waf_or_blocked = True
    elif waf_or_blocked and extracted_chars >= 500 and "just a moment" not in title.lower():
        waf_or_blocked = False

    potential = item_level_potential(html, extracted_chars, has_pdf) if html else "unknown"
    recommended, note = recommend_status(
        candidate=candidate,
        http_status=http_status,
        extracted_chars=extracted_chars,
        has_pdf=has_pdf,
        has_js=has_js,
        waf_or_blocked=waf_or_blocked,
        timeout_or_error=timeout_or_error,
    )

    notes = [note]
    if error:
        notes.append(error[:220])
    if final_url != url:
        notes.append(f"Redirected to {final_url}")
    if content_type and "html" not in content_type and "text" not in content_type:
        notes.append(f"Non-HTML content type: {content_type}")

    return {
        "candidate_id": candidate["candidate_id"],
        "source_layer_name": candidate["source_layer_name"],
        "official_url": url,
        "category": candidate["category"],
        "commercial_value": candidate["commercial_value"],
        "proposed_status": candidate["proposed_status"],
        "expected_extraction": candidate["expected_extraction"],
        "http_status": http_status,
        "final_url": final_url,
        "response_time_ms": response_time_ms,
        "content_type": content_type,
        "response_size_bytes": response_size,
        "extracted_text_chars": extracted_chars,
        "page_title": title[:180],
        "has_pdf_links": has_pdf,
        "has_js_signals": has_js,
        "waf_or_blocked_signals": waf_or_blocked,
        "timeout_or_connection_error": timeout_or_error,
        "item_level_potential": potential,
        "recommended_next_status": recommended,
        "notes": " ".join(notes),
    }


def top_fastest(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reachable = [
        row for row in results
        if row["http_status"] and row["http_status"] < 400 and not row["timeout_or_connection_error"]
    ]
    reachable.sort(key=lambda row: row["response_time_ms"])
    return reachable[:5]


def best_candidates(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best = [
        row for row in results
        if row["recommended_next_status"] == "validation_pass_candidate"
        and row["commercial_value"] in {"Critical", "High"}
        and not row["waf_or_blocked_signals"]
    ]
    best.sort(key=lambda row: (row["response_time_ms"], -row["extracted_text_chars"]))
    return best[:8]


def write_json_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = Counter(row["recommended_next_status"] for row in results)
    payload = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_tested": len(results),
        "results": results,
        "summary_counts_by_recommended_next_status": dict(sorted(summary.items())),
        "top_fastest_sources": top_fastest(results),
        "blocked_or_waf_sources": [
            row for row in results
            if row["waf_or_blocked_signals"] or row["recommended_next_status"] in {"blocked", "needs_waf_workaround"}
        ],
        "pdf_heavy_sources": [
            row for row in results
            if row["has_pdf_links"] or row["recommended_next_status"] == "needs_pdf_validation"
        ],
        "js_required_sources": [
            row for row in results
            if row["has_js_signals"] or row["recommended_next_status"] == "needs_js_rendering"
        ],
        "best_candidates_for_activation_later": best_candidates(results),
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def md_bool(value: bool) -> str:
    return "yes" if value else "no"


def status_groups(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {
        "PDF validation needed": [],
        "JS rendering needed": [],
        "WAF workaround needed": [],
        "Manual mapping needed": [],
        "Blocked or avoid for now": [],
    }
    for row in results:
        status = row["recommended_next_status"]
        if status == "needs_pdf_validation":
            groups["PDF validation needed"].append(row)
        if status == "needs_js_rendering" or row["has_js_signals"]:
            groups["JS rendering needed"].append(row)
        if status == "needs_waf_workaround" or row["waf_or_blocked_signals"]:
            groups["WAF workaround needed"].append(row)
        if row["item_level_potential"] in {"medium", "high"} and status != "validation_pass_candidate":
            groups["Manual mapping needed"].append(row)
        if status in {"blocked", "avoid_for_now"}:
            groups["Blocked or avoid for now"].append(row)
    return groups


def write_markdown_report(payload: dict[str, Any]) -> None:
    results = payload["results"]
    counts = Counter(row["recommended_next_status"] for row in results)
    accessible = sum(1 for row in results if row["http_status"] and row["http_status"] < 400)
    waf_count = len(payload["blocked_or_waf_sources"])
    pdf_count = len(payload["pdf_heavy_sources"])
    js_count = len(payload["js_required_sources"])
    best = payload["best_candidates_for_activation_later"]

    lines: list[str] = [
        "# Sprint 3C — UAE Source Speed & Reliability Validation",
        "",
        "## 1. Verdict",
        "",
        "- This was validation-only.",
        "- No sources were activated.",
        "- No source configuration, source monitoring behavior, adapters, API behavior, or frontend files were changed.",
        f"- Candidates tested: {len(results)}.",
        f"- Basic accessibility pass: {accessible}.",
        f"- Blocked or WAF-like responses: {waf_count}.",
        f"- PDF validation needed: {pdf_count}.",
        f"- JS rendering signals observed: {js_count}.",
        "- Safest later-activation candidates are listed below, but none should be activated without a separate approval sprint.",
        "",
        "## 2. Summary table",
        "",
        "| Candidate ID | Source layer | URL | HTTP status | Response time | Extracted chars | PDF links | JS signals | WAF/blocked | Recommended next status |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in results:
        lines.append(
            "| "
            f"`{row['candidate_id']}` | "
            f"{row['source_layer_name']} | "
            f"{row['official_url']} | "
            f"{row['http_status'] if row['http_status'] is not None else 'error'} | "
            f"{row['response_time_ms']} ms | "
            f"{row['extracted_text_chars']} | "
            f"{md_bool(row['has_pdf_links'])} | "
            f"{md_bool(row['has_js_signals'])} | "
            f"{md_bool(row['waf_or_blocked_signals'])} | "
            f"{row['recommended_next_status']} |"
        )

    lines.extend([
        "",
        "## 3. Best candidates for later activation",
        "",
    ])
    if best:
        for row in best:
            lines.append(
                f"- `{row['candidate_id']}` — {row['source_layer_name']}: "
                f"HTTP {row['http_status']}, {row['response_time_ms']} ms, "
                f"{row['extracted_text_chars']} extracted chars. Next step: repeated-run and item-level validation."
            )
    else:
        lines.append("- No candidate should move forward on basic HTTP evidence alone; adapter or rendering checks are needed first.")

    lines.extend([
        "",
        "## 4. Sources requiring adapters or workarounds",
        "",
    ])
    for group, rows in status_groups(results).items():
        lines.append(f"### {group}")
        if not rows:
            lines.append("")
            lines.append("- None identified in this validation pass.")
        else:
            lines.append("")
            for row in rows:
                lines.append(f"- `{row['candidate_id']}` — {row['source_layer_name']}: {row['notes']}")
        lines.append("")

    slow = [row for row in results if row["response_time_ms"] >= 5000]
    redirects = [row for row in results if row["final_url"] != row["official_url"]]
    low_text = [row for row in results if row["extracted_text_chars"] < 500]
    generic = [row for row in results if row["item_level_potential"] in {"low", "unknown"}]

    lines.extend([
        "## 5. Network / reliability notes",
        "",
        f"- Slow responses at or above 5 seconds: {len(slow)}.",
        f"- Redirects observed: {len(redirects)}.",
        f"- Very low extracted text results: {len(low_text)}.",
        f"- Pages with low or unknown item-level potential: {len(generic)}.",
    ])
    if slow:
        lines.append("- Slow candidates: " + ", ".join(f"`{row['candidate_id']}`" for row in slow) + ".")
    if redirects:
        lines.append("- Redirect candidates: " + ", ".join(f"`{row['candidate_id']}`" for row in redirects) + ".")
    if low_text:
        lines.append("- Low-text candidates: " + ", ".join(f"`{row['candidate_id']}`" for row in low_text) + ".")
    lines.extend([
        "",
        "## 6. Recommended Sprint 3D",
        "",
    ])
    if counts.get("validation_pass_candidate", 0) >= 3:
        lines.append(
            "Run a disabled-candidate planning pass for the cleanest 3–5 validation-pass candidates, "
            "then run repeated checks before any activation decision."
        )
    else:
        lines.append(
            "Build the item-level adapter skeleton first. This validation pass shows generic URLs are too broad "
            "or too weak to justify a source configuration change by themselves."
        )
    lines.append("")
    lines.append("Do not move any candidate into active monitoring during Sprint 3D.")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    candidates = load_candidates()
    results: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        print(f"[{index}/{len(candidates)}] {candidate['candidate_id']} {candidate['official_url']}")
        results.append(validate_candidate(candidate))
        if index < len(candidates):
            time.sleep(0.75)
    payload = write_json_report(results)
    write_markdown_report(payload)
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
