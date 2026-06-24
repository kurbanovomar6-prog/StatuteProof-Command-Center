"""
Validate FTA candidate sources and promote passing ones to 'active' status.

Runs each of the 6 FTA candidate URLs through FTAAdapter.fetch_content(),
checks is_quality_content(), and updates sources.json for those that pass.
"""

from __future__ import annotations

import json
import logging
import sys
import os

# Make app imports work regardless of cwd
sys.path.insert(0, "/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar")
os.chdir("/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar")

from app.adapters.fta import FTAAdapter
from app.adapters.base import is_quality_content

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)

CANDIDATE_URLS = [
    "https://tax.gov.ae/en/legislation.aspx",
    "https://tax.gov.ae/en/taxes/vat/guides.references.aspx",
    "https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx",
    "https://tax.gov.ae/en/media.centre.aspx",
    "https://tax.gov.ae/en/legislation/corporate-tax.aspx",
    "https://tax.gov.ae/en/taxes/vat/vat-public-clarifications.aspx",
]

SOURCES_JSON = (
    "/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar/sources.json"
)


def validate_all() -> dict[str, dict]:
    """Run each candidate URL through the FTA adapter. Return results keyed by URL."""
    adapter = FTAAdapter()
    results: dict[str, dict] = {}

    print("\n── FTA Candidate Baseline Validation ──────────────────────────────────")
    for url in CANDIDATE_URLS:
        print(f"\n  Fetching: {url}")
        try:
            content = adapter.fetch_content(url)
        except Exception as exc:
            content = None
            print(f"    Exception: {type(exc).__name__}: {exc}")

        chars = len(content) if content else 0
        passed = is_quality_content(content)

        if content is None:
            reason = "adapter returned None (timeout, HTTP error, or low-content fallback)"
        elif chars < 500:
            reason = f"only {chars} chars — below 500-char minimum"
        elif not passed:
            reason = "fewer than 3 non-empty paragraphs"
        else:
            reason = "OK"

        status = "PASS" if passed else "FAIL"
        print(f"    {status}  {chars:,} chars  — {reason}")

        results[url] = {
            "chars": chars,
            "passed": passed,
            "reason": reason,
        }

    return results


def promote_passing_sources(results: dict[str, dict]) -> int:
    """
    Update sources.json: set status='active' for every URL that passed.

    Returns the number of sources promoted.
    """
    passing_urls = {url for url, r in results.items() if r["passed"]}
    if not passing_urls:
        return 0

    with open(SOURCES_JSON, "r", encoding="utf-8") as fh:
        sources = json.load(fh)

    promoted = 0
    for source in sources:
        if source.get("url") in passing_urls and source.get("status") == "candidate":
            source["status"] = "active"
            promoted += 1

    with open(SOURCES_JSON, "w", encoding="utf-8") as fh:
        json.dump(sources, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # Validate JSON round-trips correctly
    with open(SOURCES_JSON, "r", encoding="utf-8") as fh:
        json.load(fh)  # raises on invalid JSON

    return promoted


def summary(results: dict[str, dict], promoted: int, sources_path: str) -> None:
    """Print final summary."""
    total = len(results)
    passed = sum(1 for r in results.values() if r["passed"])

    print("\n── Results ─────────────────────────────────────────────────────────────")
    print(f"  Passed:   {passed}/{total}")
    print(f"  Promoted: {promoted} source(s) set to 'active'")

    # Report active + enabled totals
    with open(sources_path, "r", encoding="utf-8") as fh:
        sources = json.load(fh)
    active_count = sum(1 for s in sources if s.get("status") == "active")
    enabled_count = sum(1 for s in sources if s.get("enabled") is True)
    print(f"  sources.json — active: {active_count}, enabled: {enabled_count}")
    print("────────────────────────────────────────────────────────────────────────\n")


def main() -> None:
    results = validate_all()
    promoted = promote_passing_sources(results)
    summary(results, promoted, SOURCES_JSON)


if __name__ == "__main__":
    main()
