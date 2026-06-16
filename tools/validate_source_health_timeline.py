#!/usr/bin/env python3
"""Validate source-health timeline and evidence review-history guardrails."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    required_files = [
        "product/regradar/app/source_health_timeline.py",
        "product/regradar/tests/test_source_health_timeline.py",
        "docs/source-health-timeline-review-history-plan.md",
        "docs/source-health-timeline-model-spec.md",
        "docs/source-health-timeline-current-state.md",
    ]
    for rel in required_files:
        if not (ROOT / rel).exists():
            errors.append(f"Missing source-health timeline file: {rel}")

    api = read("product/regradar/app/api.py")
    helper = read("product/regradar/app/source_health_timeline.py")
    sources_page = read("product/regradar/web/src/components/app/SourcesPage.jsx")
    evidence_page = read("product/regradar/web/src/components/app/EvidencePage.jsx")
    assessment = read("product/regradar/app/evidence_assessment.py")

    for route in ("/api/sources/timeline", "/api/evidence/review-history"):
        if route not in api:
            errors.append(f"Missing timeline API route: {route}")

    required_helper_markers = [
        "build_source_timeline",
        "build_evidence_review_history",
        "source_health_customer_message",
        "HASH_DRIFT",
        "REMEDIATION_REQUIRED",
        "NO_HISTORY",
    ]
    for marker in required_helper_markers:
        if marker not in helper:
            errors.append(f"Timeline helper missing marker: {marker}")

    required_source_ui = [
        "View timeline",
        "timelineEventCount",
        "lastEvidenceAt",
        "remediationReason",
        "No timeline data yet",
    ]
    for marker in required_source_ui:
        if marker not in sources_page:
            errors.append(f"Sources page missing timeline UI marker: {marker}")

    required_evidence_ui = [
        "Review History",
        "reviewHistory",
        "assessment_impact_level",
        "No review history has been recorded yet",
    ]
    for marker in required_evidence_ui:
        if marker not in evidence_page:
            errors.append(f"Evidence page missing review-history UI marker: {marker}")

    fake_markers = [
        "MOCK_TIMELINE",
        "sampleTimeline",
        "fake timeline",
        "fake review history",
        "demo timeline event",
    ]
    combined = "\n".join([helper, sources_page, evidence_page, api])
    for marker in fake_markers:
        if marker.lower() in combined.lower():
            errors.append(f"Fake timeline marker found: {marker}")

    forbidden_claims = [
        "never miss",
        "guaranteed compliance",
        "perfect parsing",
        "provides legal advice",
        "is legal advice",
    ]
    for phrase in forbidden_claims:
        if phrase in combined.lower():
            errors.append(f"Unsafe customer-facing claim found: {phrase}")

    if "find_evidence_record" not in assessment or "validate_saved_evidence" not in assessment:
        errors.append("Acknowledge & Assess must remain guarded by saved evidence lookup/proof validation.")

    if errors:
        print("Source-health timeline validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Source-health timeline validation PASSED")
    print("- Timeline helper and routes present")
    print("- Sources page timeline UI markers present")
    print("- Evidence page review-history markers present")
    print("- Remediation/hash-drift/no-history messaging present")
    print("- No fake timeline markers or forbidden claims found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
