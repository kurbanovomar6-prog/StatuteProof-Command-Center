#!/usr/bin/env python3
"""Validate MVP-T trust workflow guardrails."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    required_files = [
        "product/regradar/app/evidence_assessment.py",
        "product/regradar/app/audit_export.py",
        "product/regradar/app/email_delivery.py",
        "product/regradar/tests/test_mvp_trust_workflow.py",
        "docs/mvp-trust-sprint-plan.md",
        "docs/mvp-trust-gap-implementation-map.md",
    ]
    for rel in required_files:
        if not (ROOT / rel).exists():
            errors.append(f"Missing MVP trust file: {rel}")

    dashboard = read("product/regradar/web/src/components/app/DashboardHome.jsx")
    sources = read("product/regradar/web/src/components/app/SourcesPage.jsx")
    evidence = read("product/regradar/web/src/components/app/EvidencePage.jsx")
    api = read("product/regradar/app/api.py")

    if "MOCK_ALERTS" in dashboard:
        errors.append("DashboardHome.jsx must not import/render MOCK_ALERTS in authenticated dashboard.")
    if "MOCK_SOURCES" in sources:
        errors.append("SourcesPage.jsx must not import/render MOCK_SOURCES in authenticated source map.")
    if "silent fallback" in evidence.lower() or "catch(() => {})" in evidence:
        errors.append("EvidencePage.jsx must not silently fall back to sample evidence.")

    expected_api_routes = [
        "/api/evidence/assess",
        "/api/evidence/review",
        "/api/evidence/export",
        "/api/delivery/email-status",
        "/api/delivery/email-test-mode",
        "/api/delivery/email-config-check",
    ]
    for route in expected_api_routes:
        if route not in api:
            errors.append(f"Missing MVP trust API route: {route}")

    required_copy = [
        "Monitoring intelligence only. Not legal advice.",
        "Acknowledge & Assess",
        "SAMPLE / DEMO",
    ]
    combined = "\n".join([evidence, api, read("product/regradar/app/audit_export.py") if (ROOT / "product/regradar/app/audit_export.py").exists() else ""])
    for phrase in required_copy:
        if phrase not in combined:
            errors.append(f"Missing trust workflow copy marker: {phrase}")

    if errors:
        print("MVP trust workflow validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("MVP trust workflow validation PASSED")
    print("- Authenticated dashboard mock-data guard passed")
    print("- Evidence assessment/export/email test-mode files present")
    print("- Trust API route markers present")
    print("- Legal-safe/SAMPLE copy markers present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
