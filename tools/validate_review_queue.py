#!/usr/bin/env python3
"""Validate Global MLRO Review Queue implementation guardrails."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    required_files = [
        "product/regradar/app/review_queue.py",
        "product/regradar/web/src/components/app/ReviewQueuePage.jsx",
        "product/regradar/tests/test_ideal_product_workflow.py",
    ]
    for rel in required_files:
        if not (ROOT / rel).exists():
            errors.append(f"Missing Review Queue file: {rel}")

    api = read("product/regradar/app/api.py")
    helper = read("product/regradar/app/review_queue.py")
    page = read("product/regradar/web/src/components/app/ReviewQueuePage.jsx")
    shell = read("product/regradar/web/src/components/app/AppShell.jsx")
    sidebar = read("product/regradar/web/src/components/app/AppSidebar.jsx")
    routes = read("product/regradar/web/src/routeMap.js")

    for marker in ("/api/reviews/queue", "_handle_reviews_queue_get"):
        if marker not in api:
            errors.append(f"API missing Review Queue marker: {marker}")
    for marker in ("build_review_queue", "load_assessments", "pending_review", "customer_safe_message"):
        if marker not in helper:
            errors.append(f"Review Queue helper missing marker: {marker}")
    for marker in ("Review Queue", "No pending reviews", "Monitoring intelligence only. Not legal advice.", "No fake rows"):
        if marker not in page:
            errors.append(f"Review Queue page missing marker: {marker}")
    for marker in ("review-queue", "ReviewQueuePage"):
        if marker not in shell + sidebar + routes:
            errors.append(f"Review Queue routing/sidebar missing marker: {marker}")

    fake_markers = ("MOCK_ALERTS", "MOCK_REPORTS", "fake rows", "sample queue")
    combined = "\n".join([helper, page, api])
    for marker in fake_markers:
        if marker.lower() in combined.lower() and marker != "fake rows":
            errors.append(f"Fake/mock marker found in Review Queue implementation: {marker}")

    forbidden_claims = (
        "guaranteed compliance",
        "never miss",
        "perfect parsing",
        "legal advice included",
    )
    for phrase in forbidden_claims:
        if phrase in combined.lower():
            errors.append(f"Unsafe claim found in Review Queue implementation: {phrase}")

    if errors:
        print("Review Queue validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Review Queue validation PASSED")
    print("- Review Queue helper, API, page, route, and sidebar are present")
    print("- Queue uses evidence/assessment records and legal-safe copy")
    print("- No authenticated mock queue markers found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
