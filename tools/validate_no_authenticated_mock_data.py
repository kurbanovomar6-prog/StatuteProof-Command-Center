#!/usr/bin/env python3
"""Block unlabeled mock/sample imports in authenticated app pages."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "product" / "regradar" / "web" / "src" / "components" / "app"


FORBIDDEN_IMPORTS = {
    "MOCK_ALERTS",
    "MOCK_REPORTS",
    "MOCK_SOURCES",
}

AUTHENTICATED_PAGES = [
    "AlertsPage.jsx",
    "ReportsPage.jsx",
    "AIBriefPage.jsx",
    "DashboardHome.jsx",
    "SourcesPage.jsx",
    "EvidencePage.jsx",
    "ReviewQueuePage.jsx",
]


def main() -> int:
    errors: list[str] = []
    for page in AUTHENTICATED_PAGES:
        path = APP_DIR / page
        if not path.exists():
            errors.append(f"Missing authenticated page: {page}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_IMPORTS:
            if token in text:
                errors.append(f"{page} references forbidden authenticated mock token: {token}")
        lowered = text.lower()
        if "fallback" in lowered and "mock" in lowered:
            errors.append(f"{page} appears to contain a mock fallback.")

    dashboard = (APP_DIR / "DashboardHome.jsx").read_text(encoding="utf-8")
    for marker in ("SOURCE_READINESS_SUMMARY", "PACK_STATS"):
        if marker in dashboard:
            errors.append(f"DashboardHome.jsx still contains hardcoded source truth marker: {marker}")

    if errors:
        print("Authenticated mock-data validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Authenticated mock-data validation PASSED")
    print("- No forbidden MOCK_ALERTS/MOCK_REPORTS/MOCK_SOURCES tokens in authenticated pages")
    print("- Dashboard source truth is not held in deprecated JSX constants")
    print("- No mock fallback markers found in authenticated pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
