#!/usr/bin/env python3
"""Validate backend/frontend plan and pricing consistency."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "product" / "regradar"))

from app.plan import PLAN_CAPABILITIES, PLAN_PRICE_MONTHLY  # noqa: E402


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    frontend_caps = read("product/regradar/web/src/data/planCapabilities.js")
    pricing_page = read("product/regradar/web/src/components/PricingPage.jsx")
    choose_plan = read("product/regradar/web/src/components/app/ChoosePlanPage.jsx")
    billing = read("product/regradar/web/src/components/app/BillingPage.jsx")
    review_queue_page = ROOT / "product/regradar/web/src/components/app/ReviewQueuePage.jsx"
    api = read("product/regradar/app/api.py")

    if PLAN_PRICE_MONTHLY.get("starter_pilot") != 199:
        errors.append("Backend starter_pilot price must be 199.")
    if PLAN_PRICE_MONTHLY.get("professional") != 399:
        errors.append("Backend professional/UAE Monitor price must be 399.")
    if PLAN_CAPABILITIES["professional"].get("source_limit") != 80:
        errors.append("Backend professional source_limit must be 80.")
    if PLAN_CAPABILITIES["professional"].get("retention_days") != 180:
        errors.append("Backend professional retention_days must be 180.")
    if not PLAN_CAPABILITIES["professional"].get("audit_export"):
        errors.append("Backend professional audit_export must reflect audit export availability.")
    if not PLAN_CAPABILITIES["professional"].get("pdf_export"):
        errors.append("Backend professional pdf_export must be true because real PDF generation exists.")
    if "def write_audit_pack_pdf" not in read("product/regradar/app/audit_export.py"):
        errors.append("Backend claims PDF export but write_audit_pack_pdf is missing.")
    if "format=pdf" not in api and '"pdf"' not in api:
        errors.append("Backend claims PDF export but API does not reference PDF format.")

    required_frontend_markers = [
        "starter_pilot: '$199'",
        "professional: '$399'",
        "sourceLimit: 80",
        "retentionDays: 180",
        "auditExport: true",
        "pdfExport: true",
    ]
    for marker in required_frontend_markers:
        if marker not in frontend_caps:
            errors.append(f"Frontend planCapabilities missing marker: {marker}")

    combined_public = "\n".join([frontend_caps, pricing_page, choose_plan, billing])
    for forbidden in ("$349", "$749"):
        if forbidden in combined_public:
            errors.append(f"Forbidden unimplemented public price found: {forbidden}")

    if "High-risk review queue" in combined_public:
        if not review_queue_page.exists() or "/api/reviews/queue" not in api:
            errors.append("High-risk review queue is claimed but Review Queue route/API is missing.")

    if "365 days" in combined_public and PLAN_CAPABILITIES["professional"].get("retention_days") != 365:
        errors.append("Frontend claims 365 days retention but backend does not encode 365 days.")

    if errors:
        print("Plan/pricing consistency validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Plan/pricing consistency validation PASSED")
    print("- Backend/frontend prices agree on $199/$399/custom")
    print("- UAE Monitor source limit and retention agree")
    print("- Review Queue claim is backed by route/API")
    print("- PDF export claim is backed by implementation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
