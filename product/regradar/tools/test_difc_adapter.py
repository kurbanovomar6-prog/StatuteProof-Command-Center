"""
Validation script for the DIFCAdapter.

Usage (from product/regradar/):
    python tools/test_difc_adapter.py

Exits 0 when all URLs return quality content; exits 1 on any failure.
"""

from __future__ import annotations

import sys
import logging

# Show DEBUG output so we can see Playwright progress
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s  %(name)s  %(message)s",
)

# Keep third-party noise down
for noisy in ("urllib3", "httpcore", "httpx", "playwright"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

from app.adapters.difc import DIFCAdapter  # noqa: E402 (after logging setup)

URLS = [
    "https://www.difc.com/business/laws-and-regulations/",
    "https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection",
    # NOTE: /business/latest-news/ is a dead URL (HTTP 308 → 404) on the live
    # DIFC site.  The actual news hub is /whats-on/news/.  This test uses the
    # correct live URL so the adapter pass/fail reflects the real site state.
    "https://www.difc.com/whats-on/news/",
]

PASS_THRESHOLD = 500  # minimum chars for PASS


def run() -> int:
    adapter = DIFCAdapter()
    results: list[bool] = []

    for url in URLS:
        print(f"\n{'='*70}")
        print(f"URL: {url}")
        print("-" * 70)

        # Verify can_handle
        can = adapter.can_handle(url)
        print(f"can_handle: {can}")
        if not can:
            print("FAIL — can_handle returned False")
            results.append(False)
            continue

        text = adapter.fetch_content(url)

        if text is None:
            print("fetch_content: returned None")
            print("FAIL")
            results.append(False)
            continue

        chars = len(text)
        passed = chars >= PASS_THRESHOLD
        print(f"fetch_content: {chars} chars returned")
        print(f"--- first 400 chars ---")
        print(text[:400])
        print("---")
        print("PASS" if passed else f"FAIL — only {chars} chars (threshold {PASS_THRESHOLD})")
        results.append(passed)

    print(f"\n{'='*70}")
    passed_count = sum(results)
    total = len(results)
    print(f"Summary: {passed_count}/{total} PASS")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(run())
