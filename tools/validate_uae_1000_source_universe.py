#!/usr/bin/env python3
"""Validate the UAE 1000-source universe mapping.

This validator protects the distinction between source research candidates and
monitoring-active sources. It must not allow candidate mapping to inflate the
active source truth.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "product/regradar/config/uae_1000_source_universe_candidates.json"
TOP250 = ROOT / "product/regradar/config/uae_top_250_activation_queue.json"
SOURCES = ROOT / "product/regradar/sources.json"
FINAL_REPORT = ROOT / "docs/uae-1000-source-expansion-final-report.md"

EXPECTED_TRUTH = (81, 80, 1)
REQUIRED_FIELDS = {
    "source_id",
    "regulator_source_owner",
    "source_family",
    "official_url",
    "final_url",
    "source_type",
    "why_official_public",
    "buyer_relevance",
    "mlro_usefulness_score",
    "compliance_usefulness_score",
    "update_importance",
    "expected_adapter",
    "expected_strategy",
    "risk",
    "risk_reason",
    "duplicate_candidate",
    "activation_priority",
    "status",
}
FORBIDDEN_POSITIVE_CLAIMS = (
    "complete uae coverage",
    "guaranteed compliance",
    "perfect parsing",
    "never miss updates",
    "regulator certified",
    "legal advice",
)
SAFE_LEGAL_CONTEXT = ("not legal advice", "does not constitute legal advice")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def source_truth() -> tuple[int, int, int]:
    rows = load_json(SOURCES)
    enabled = [
        row for row in rows
        if isinstance(row, dict)
        and row.get("jurisdiction") == "AE"
        and row.get("enabled") is True
    ]
    active = [row for row in enabled if row.get("status") in {"active", "readiness_supported"}]
    remediation = [row for row in enabled if row.get("status") == "remediation"]
    return len(enabled), len(active), len(remediation)


def canonical_url(value: str) -> str:
    parsed = urlparse(value)
    return parsed._replace(fragment="").geturl().rstrip("/")


def unsafe_claim(text: str, claim: str) -> bool:
    lower = text.lower()
    start = 0
    while True:
        idx = lower.find(claim, start)
        if idx == -1:
            return False
        context = lower[max(0, idx - 120): idx + len(claim) + 120]
        if claim == "legal advice" and any(marker in context for marker in SAFE_LEGAL_CONTEXT):
            start = idx + len(claim)
            continue
        if any(marker in context for marker in ("no ", "not ", "avoid", "forbidden", "prohibited", "did we make")):
            start = idx + len(claim)
            continue
        return True


def main() -> int:
    errors: list[str] = []

    if not UNIVERSE.exists():
        errors.append("Missing uae_1000_source_universe_candidates.json")
    if not TOP250.exists():
        errors.append("Missing uae_top_250_activation_queue.json")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    universe = load_json(UNIVERSE)
    top = load_json(TOP250)
    candidates = universe.get("candidates") or []
    rejected = universe.get("rejected") or []
    summary = universe.get("universe_summary") or {}
    top_queue = top.get("top_250_activation_queue") or []

    if tuple(source_truth()) != EXPECTED_TRUTH:
        errors.append(f"sources.json truth changed; expected {EXPECTED_TRUTH}, got {source_truth()}")

    if summary.get("active_sources_added") != 0 or summary.get("sources_json_changed") is not False:
        errors.append("Universe mapping must not claim active source additions or sources.json changes.")

    if int(summary.get("total_records") or 0) < 1000:
        errors.append("Universe must contain at least 1000 candidate/rejection records.")
    if int(summary.get("total_candidates") or 0) < 700:
        errors.append("Universe must contain at least 700 candidate records.")
    if int(summary.get("non_duplicate_candidate_urls") or 0) < 700:
        errors.append("Universe must contain at least 700 non-duplicate candidate URLs.")
    if int(summary.get("total_rejected") or 0) < 100:
        errors.append("Universe must contain at least 100 rejected records with reasons.")

    source_ids: set[str] = set()
    urls: set[str] = set()
    for idx, row in enumerate(candidates, start=1):
        missing = sorted(REQUIRED_FIELDS - set(row))
        if missing:
            errors.append(f"Candidate #{idx} missing required fields: {', '.join(missing)}")
            continue
        sid = str(row.get("source_id") or "")
        url = canonical_url(str(row.get("official_url") or ""))
        if not sid.startswith("AE-"):
            errors.append(f"Candidate source_id must start with AE-: {sid}")
        if sid in source_ids:
            errors.append(f"Duplicate candidate source_id: {sid}")
        source_ids.add(sid)
        if not url.startswith("https://"):
            errors.append(f"Candidate official_url must be HTTPS: {url}")
        if url in urls:
            errors.append(f"Duplicate candidate official_url: {url}")
        urls.add(url)
        if row.get("status") == "active":
            errors.append(f"Universe candidate must not be marked active: {sid}")

    for idx, row in enumerate(rejected, start=1):
        if not row.get("rejection_reason"):
            errors.append(f"Rejected record #{idx} missing rejection_reason")
        if row.get("status") != "rejected":
            errors.append(f"Rejected record #{idx} must use status=rejected")

    if len(top_queue) != 250:
        errors.append(f"Top-250 queue must contain 250 records, got {len(top_queue)}")
    for idx, row in enumerate(top_queue, start=1):
        for field in ("rank", "source_id", "official_url", "source_family", "expected_adapter", "no_save_command_config"):
            if field not in row:
                errors.append(f"Top-250 row #{idx} missing {field}")
        if row.get("rank") != idx:
            errors.append(f"Top-250 row rank mismatch at #{idx}")

    if FINAL_REPORT.exists():
        text = FINAL_REPORT.read_text(encoding="utf-8", errors="ignore").lower()
        for claim in FORBIDDEN_POSITIVE_CLAIMS:
            if unsafe_claim(text, claim):
                errors.append(f"Unsafe positive claim in final report: {claim}")

    if errors:
        for error in errors[:80]:
            print(f"ERROR: {error}")
        if len(errors) > 80:
            print(f"ERROR: {len(errors) - 80} additional errors omitted")
        return 1

    print("UAE 1000-source universe validation PASSED")
    print(f"- Records: {summary.get('total_records')}")
    print(f"- Candidates: {summary.get('total_candidates')}")
    print(f"- Rejected: {summary.get('total_rejected')}")
    print("- Top-250 queue present")
    print("- sources.json truth preserved: 81/80/1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
