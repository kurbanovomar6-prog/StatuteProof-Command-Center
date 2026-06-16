#!/usr/bin/env python3
"""Validate real PDF audit-pack export wiring and customer-safe claims."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "product" / "regradar"))

from app.plan import PLAN_CAPABILITIES  # noqa: E402


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    audit_export = read("product/regradar/app/audit_export.py")
    api = read("product/regradar/app/api.py")
    api_js = read("product/regradar/web/src/api.js")
    evidence_page = read("product/regradar/web/src/components/app/EvidencePage.jsx")
    reports_page = read("product/regradar/web/src/components/app/ReportsPage.jsx")
    pricing_page = read("product/regradar/web/src/components/PricingPage.jsx")
    billing_page = read("product/regradar/web/src/components/app/BillingPage.jsx")
    choose_plan = read("product/regradar/web/src/components/app/ChoosePlanPage.jsx")
    frontend_caps = read("product/regradar/web/src/data/planCapabilities.js")
    tests = read("product/regradar/tests/test_pdf_audit_export.py")

    if "def write_audit_pack_pdf" not in audit_export:
        errors.append("audit_export.py is missing write_audit_pack_pdf.")
    if "page.pdf(" not in audit_export:
        errors.append("audit_export.py does not call Playwright page.pdf.")
    if "PDF export could not be generated" not in audit_export:
        errors.append("PDF generation failure is not surfaced clearly.")
    if "LEGAL_DISCLAIMER" not in audit_export:
        errors.append("PDF audit export metadata must include the legal disclaimer.")

    if "export_format" not in api or "format" not in api or "build_audit_pack_export_response" not in api:
        errors.append("API export route does not support PDF format selection.")
    if "exportAuditPack(evidenceRecordId, format" not in api_js:
        errors.append("Frontend API client does not pass an export format.")
    if "Export PDF audit pack" not in evidence_page:
        errors.append("Evidence page is missing PDF export action.")
    if "Export PDF audit pack" not in reports_page:
        errors.append("Reports page is missing PDF export action.")

    if not PLAN_CAPABILITIES["professional"].get("pdf_export"):
        errors.append("Backend professional/UAE Monitor plan must expose pdf_export after implementation.")
    if "pdfExport: true" not in frontend_caps:
        errors.append("Frontend planCapabilities must expose pdfExport: true.")
    if "PDF audit pack" not in pricing_page + billing_page + choose_plan:
        errors.append("Plan/pricing pages must mention PDF audit pack export after implementation.")

    required_tests = [
        "test_pdf_export_creates_real_pdf_and_metadata",
        "test_demo_pdf_export_is_labeled_sample_demo",
        "test_markdown_html_export_still_omits_pdf_by_default",
        "test_pdf_export_response_reports_pdf_status_and_paths",
    ]
    for marker in required_tests:
        if marker not in tests:
            errors.append(f"Missing PDF audit export test: {marker}")

    customer_facing = "\n".join([evidence_page, reports_page, pricing_page, billing_page, choose_plan])
    for forbidden in (
        "court-admissible",
        "guaranteed compliance",
        "perfect parsing",
        "never miss",
        "regulator certified",
        "complete UAE coverage",
    ):
        if forbidden.lower() in customer_facing.lower():
            errors.append(f"Forbidden customer-facing claim found: {forbidden}")

    if "Monitoring intelligence only. Not legal advice." not in customer_facing + audit_export:
        errors.append("PDF/audit export surfaces must keep the legal boundary disclaimer.")

    if errors:
        print("PDF audit export validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PDF audit export validation PASSED")
    print("- Real PDF generation path is present")
    print("- API/frontend PDF export wiring is present")
    print("- Plan/pricing PDF claim matches implementation")
    print("- Customer-facing forbidden claims are absent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
