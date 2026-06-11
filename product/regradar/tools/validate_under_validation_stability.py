#!/usr/bin/env python3
"""Repeated-run validation for disabled UAE under-validation candidates.

This tool is intentionally read-only with respect to source configuration. It
does not edit sources.json, activate monitoring, call AI, send Telegram
messages, or store full response bodies.
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

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "uae_under_validation_sources.json"
RESULTS_PATH = ROOT / "reports" / "sprint3e_under_validation_stability_results.json"
REPORT_PATH = ROOT / "reports" / "sprint3e_under_validation_stability_report.md"

RUNS_PER_CANDIDATE = 3
REQUEST_TIMEOUT_SECONDS = 12
SHORT_SPACING_SECONDS = 0.75
USER_AGENT = (
    "Mozilla/5.0 (compatible; StatuteProofStabilityValidation/1.0; "
    "+https://statuteproof.com)"
)

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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_candidates() -> list[dict[str, Any]]:
    rows = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    selected = [
        row for row in rows
        if row.get("enabled") is False and row.get("status") == "under_validation"
    ]
    return selected


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


def signature(text: str) -> str | None:
    normalized = normalize_visible_text(text)
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_response(html: str) -> dict[str, Any]:
    lower = html.lower()
    has_js = any(marker in lower for marker in JS_MARKERS)
    waf = any(marker in lower for marker in BLOCK_MARKERS)
    soup = BeautifulSoup(html or "", "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    pdf_links = []
    for tag in soup.find_all("a", href=True):
        href = str(tag.get("href", "")).split("?", 1)[0].lower()
        if href.endswith(".pdf"):
            pdf_links.append(tag.get("href"))

    for tag in soup(["script", "style", "noscript", "svg", "img", "iframe"]):
        tag.decompose()

    visible_text = soup.get_text("\n", strip=True)
    visible_text = re.sub(r"\n{3,}", "\n\n", visible_text)
    visible_text = re.sub(r"[ \t\xa0]+", " ", visible_text).strip()

    return {
        "page_title": title[:180],
        "visible_text": visible_text,
        "extracted_text_chars": len(visible_text),
        "content_signature": signature(visible_text),
        "has_pdf_links": bool(pdf_links),
        "pdf_link_count": len(set(pdf_links)),
        "has_js_signals": has_js,
        "waf_or_blocked_signals": waf,
    }


def run_single_check(candidate: dict[str, Any], run_number: int) -> dict[str, Any]:
    url = candidate["url"]
    started = time.perf_counter()
    http_status = None
    final_url = url
    content_type = ""
    response_size = 0
    timeout_or_error = False
    error = ""
    extracted = {
        "page_title": "",
        "extracted_text_chars": 0,
        "content_signature": None,
        "has_pdf_links": False,
        "pdf_link_count": 0,
        "has_js_signals": False,
        "waf_or_blocked_signals": False,
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
        http_status = response.status_code
        final_url = response.url
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
        response_size = len(response.content or b"")
        if "html" in content_type or "text" in content_type or not content_type:
            extracted = extract_response(response.text)
    except requests.Timeout as exc:
        timeout_or_error = True
        error = f"timeout: {exc}"
    except requests.RequestException as exc:
        timeout_or_error = True
        error = f"{type(exc).__name__}: {exc}"

    response_time_ms = round((time.perf_counter() - started) * 1000)
    waf = bool(extracted["waf_or_blocked_signals"])
    title = str(extracted["page_title"]).lower()
    extracted_chars = int(extracted["extracted_text_chars"] or 0)
    if http_status in {401, 403, 429, 503}:
        waf = True
    elif waf and extracted_chars >= 500 and "just a moment" not in title:
        waf = False

    return {
        "candidate_id": candidate["candidate_id"],
        "source_layer_name": candidate["source_layer_name"],
        "official_url": url,
        "run_number": run_number,
        "timestamp_utc": utc_now(),
        "http_status": http_status,
        "final_url": final_url,
        "response_time_ms": response_time_ms,
        "content_type": content_type,
        "response_size_bytes": response_size,
        "extracted_text_chars": extracted_chars,
        "page_title": extracted["page_title"],
        "content_signature": extracted["content_signature"],
        "has_pdf_links": extracted["has_pdf_links"],
        "pdf_link_count": extracted["pdf_link_count"],
        "has_js_signals": extracted["has_js_signals"],
        "waf_or_blocked_signals": waf,
        "timeout_or_connection_error": timeout_or_error,
        "error": error[:260],
    }


def stable_unique(values: list[Any]) -> bool:
    return len({json.dumps(value, sort_keys=True) for value in values}) <= 1


def aggregate_candidate(candidate: dict[str, Any], runs: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [
        run for run in runs
        if not run["timeout_or_connection_error"]
        and run["http_status"] is not None
        and 200 <= int(run["http_status"]) < 400
    ]
    failures = [run for run in runs if run not in successful]
    response_times = [int(run["response_time_ms"]) for run in runs]
    extracted_counts = [int(run["extracted_text_chars"]) for run in runs]
    titles = [run["page_title"] for run in runs]
    signatures = [run["content_signature"] for run in runs if run["content_signature"]]
    pdf_counts = [run["pdf_link_count"] for run in runs]
    status_codes = sorted({str(run["http_status"]) if run["http_status"] is not None else "error" for run in runs})
    waf_seen = any(run["waf_or_blocked_signals"] for run in runs)
    pdf_seen = any(run["has_pdf_links"] for run in runs)
    pdf_stable: bool | str = stable_unique(pdf_counts) if pdf_seen else "unknown"
    title_stable = stable_unique(titles)
    content_stable = bool(signatures) and stable_unique(signatures)

    verdict, action = classify_candidate(
        candidate=candidate,
        runs=runs,
        successful_count=len(successful),
        waf_seen=waf_seen,
        title_stable=title_stable,
        content_stable=content_stable,
        pdf_seen=pdf_seen,
        pdf_stable=pdf_stable,
        average_chars=round(mean(extracted_counts)) if extracted_counts else 0,
    )

    return {
        "candidate_id": candidate["candidate_id"],
        "name": candidate["name"],
        "source_layer_name": candidate["source_layer_name"],
        "official_url": candidate["url"],
        "category": candidate["category"],
        "enabled": candidate["enabled"],
        "status": candidate["status"],
        "runs": runs,
        "success_count": len(successful),
        "failure_count": len(failures),
        "status_codes_seen": status_codes,
        "average_response_time_ms": round(mean(response_times)) if response_times else 0,
        "min_response_time_ms": min(response_times) if response_times else 0,
        "max_response_time_ms": max(response_times) if response_times else 0,
        "average_extracted_chars": round(mean(extracted_counts)) if extracted_counts else 0,
        "title_stable": title_stable,
        "content_signature_stable": content_stable,
        "pdf_links_stable": pdf_stable,
        "waf_seen": waf_seen,
        "repeated_run_verdict": verdict,
        "recommended_next_action": action,
    }


def classify_candidate(
    *,
    candidate: dict[str, Any],
    runs: list[dict[str, Any]],
    successful_count: int,
    waf_seen: bool,
    title_stable: bool,
    content_stable: bool,
    pdf_seen: bool,
    pdf_stable: bool | str,
    average_chars: int,
) -> tuple[str, str]:
    if successful_count == 0:
        return "blocked", "Do not proceed. Source failed all repeated checks."
    if waf_seen:
        return "needs_waf_workaround", "Do not proceed until WAF/403 behavior is resolved and repeated checks pass."
    if successful_count < len(runs):
        return "unstable", "Repeat validation later; not all checks succeeded."
    if average_chars < 1000:
        return "manual_review_required", "Text volume is low; inspect official page structure manually."
    if pdf_seen and pdf_stable is not True:
        return "needs_pdf_validation", "PDF links were present but not stable across repeated checks."
    if pdf_seen and candidate.get("extraction_expectation") in {"html_plus_pdf", "pdf_primary"}:
        return "needs_pdf_validation", "Run PDF link resolution and document extraction validation before any activation decision."
    layer_name = candidate.get("source_layer_name", "").lower()
    if "rulebook" in layer_name or "item-level" in candidate.get("limitation_notes", "").lower() or "item-level" in candidate.get("next_validation_action", "").lower():
        return "needs_item_level_validation", "Repeated checks are stable; map item-level URLs before activation review."
    if not title_stable or not content_stable:
        return "unstable", "Title or normalized content signature changed across repeated checks."
    if "item-level" in candidate.get("limitation_notes", "").lower() or "item-level" in candidate.get("next_validation_action", "").lower():
        return "needs_item_level_validation", "Repeated checks are stable; map item-level URLs before activation review."
    return "stable_candidate", "Ready for activation decision review after source transparency and proof/diff checks."


def run_validation(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_results = []
    total_runs = len(candidates) * RUNS_PER_CANDIDATE
    run_index = 0
    for candidate in candidates:
        runs = []
        for run_number in range(1, RUNS_PER_CANDIDATE + 1):
            run_index += 1
            print(f"[{run_index}/{total_runs}] {candidate['candidate_id']} run {run_number}")
            runs.append(run_single_check(candidate, run_number))
            if run_index < total_runs:
                time.sleep(SHORT_SPACING_SECONDS)
        candidate_results.append(aggregate_candidate(candidate, runs))
    return candidate_results


def best_candidates(candidate_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        row for row in candidate_results
        if row["repeated_run_verdict"] == "stable_candidate"
        and row["success_count"] == RUNS_PER_CANDIDATE
        and not row["waf_seen"]
    ]
    rows.sort(key=lambda row: row["average_response_time_ms"])
    return rows


def write_json_report(candidate_results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["repeated_run_verdict"] for row in candidate_results)
    payload = {
        "run_timestamp_utc": utc_now(),
        "total_candidates_tested": len(candidate_results),
        "runs_per_candidate": RUNS_PER_CANDIDATE,
        "aggregate_summary": dict(sorted(counts.items())),
        "candidate_results": candidate_results,
        "best_candidates_for_activation_decision_later": best_candidates(candidate_results),
        "candidates_not_ready": [
            row for row in candidate_results
            if row["repeated_run_verdict"] in {"needs_waf_workaround", "unstable", "blocked", "manual_review_required"}
        ],
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def yn(value: Any) -> str:
    if value == "unknown":
        return "unknown"
    return "yes" if bool(value) else "no"


def grouped(candidate_results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {
        "needs item-level validation": [],
        "needs PDF validation": [],
        "needs WAF workaround": [],
        "unstable/blocked": [],
        "manual review required": [],
    }
    for row in candidate_results:
        verdict = row["repeated_run_verdict"]
        if verdict == "needs_item_level_validation":
            groups["needs item-level validation"].append(row)
        elif verdict == "needs_pdf_validation":
            groups["needs PDF validation"].append(row)
        elif verdict == "needs_waf_workaround":
            groups["needs WAF workaround"].append(row)
        elif verdict in {"unstable", "blocked"}:
            groups["unstable/blocked"].append(row)
        elif verdict == "manual_review_required":
            groups["manual review required"].append(row)
    return groups


def write_markdown_report(payload: dict[str, Any]) -> None:
    results = payload["candidate_results"]
    stableish = payload["best_candidates_for_activation_decision_later"]
    not_ready = payload["candidates_not_ready"]

    lines: list[str] = [
        "# Sprint 3E — Under-Validation Source Stability Report",
        "",
        "## 1. Verdict",
        "",
        "- This was validation-only.",
        "- No sources were activated.",
        f"- Candidates tested: {payload['total_candidates_tested']}.",
        f"- Repeated runs per candidate: {payload['runs_per_candidate']}.",
        "- Candidates that look stable enough for later activation decision review are listed below; none are active.",
        f"- Candidates not ready: {len(not_ready)}.",
        "",
        "## 2. Candidate stability table",
        "",
        "| Candidate | URL | Runs passed | Status codes seen | Avg response time | Avg extracted chars | PDF links stable | WAF seen | Content signature stable | Verdict | Recommended next action |",
        "| --- | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in results:
        lines.append(
            "| "
            f"`{row['candidate_id']}` | "
            f"{row['official_url']} | "
            f"{row['success_count']}/{payload['runs_per_candidate']} | "
            f"{', '.join(row['status_codes_seen'])} | "
            f"{row['average_response_time_ms']} ms | "
            f"{row['average_extracted_chars']} | "
            f"{yn(row['pdf_links_stable'])} | "
            f"{yn(row['waf_seen'])} | "
            f"{yn(row['content_signature_stable'])} | "
            f"{row['repeated_run_verdict']} | "
            f"{row['recommended_next_action']} |"
        )

    lines.extend([
        "",
        "## 3. Stable candidates for later activation decision",
        "",
    ])
    if stableish:
        for row in stableish:
            lines.append(
                f"- `{row['candidate_id']}` — {row['source_layer_name']}: "
                f"{row['success_count']}/{payload['runs_per_candidate']} checks passed, "
                f"average {row['average_response_time_ms']} ms, "
                f"average {row['average_extracted_chars']} extracted chars, verdict `{row['repeated_run_verdict']}`. "
                "Ready for activation decision review, not active."
            )
    else:
        lines.append("- None. No candidate should move to activation decision review from this run.")

    lines.extend([
        "",
        "## 4. Candidates requiring more work",
        "",
    ])
    for group_name, rows in grouped(results).items():
        lines.append(f"### {group_name}")
        lines.append("")
        if not rows:
            lines.append("- None.")
        else:
            for row in rows:
                lines.append(f"- `{row['candidate_id']}` — {row['recommended_next_action']}")
        lines.append("")

    lines.extend([
        "## 5. Activation decision gate for future Sprint 3F",
        "",
        "Before any source can be activated, all of the following must be true:",
        "",
        "- Repeated stability pass.",
        "- Item-level URL confirmed.",
        "- Extraction quality above threshold.",
        "- Proof/diff output tested.",
        "- Limitation note written.",
        "- Source transparency report updated.",
        "- Human review gate confirmed.",
        "",
        "## 6. Recommended Sprint 3F",
        "",
    ])
    if stableish:
        lines.append(
            "Run activation-decision review for the safest 1-3 candidates only. "
            "Do not activate all five at once. Prioritize candidates with stable repeated checks and clear item-level mapping."
        )
    else:
        lines.append(
            "Run item-level validation first. Generic source pages are not ready for activation decision review."
        )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    candidates = load_candidates()
    if not candidates:
        raise SystemExit("No disabled under-validation candidates found.")
    results = run_validation(candidates)
    payload = write_json_report(results)
    write_markdown_report(payload)
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
