#!/usr/bin/env python3
"""Validate the research-only UAE source pack candidate file.

This validator intentionally checks metadata and claim safety. It does not
fetch external URLs and it does not activate sources.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_FILE = ROOT / "product/regradar/config/uae_source_candidates.json"
SOURCES_FILE = ROOT / "product/regradar/sources.json"

REQUIRED_FIELDS = {
    "source_id",
    "regulator",
    "title",
    "url",
    "source_type",
    "jurisdiction",
    "buyer_relevance",
    "why_it_matters",
    "update_frequency_guess",
    "parsing_risk",
    "official_status",
    "priority",
    "initial_status",
    "candidate_pack",
    "notes",
    "top_40_candidate",
    "top_60_candidate",
}

ALLOWED_OFFICIAL_STATUS = {"official", "officially_linked", "uncertain"}
ALLOWED_INITIAL_STATUS = {
    "candidate",
    "no_save_tested",
    "readiness_supported",
    "remediation",
    "blocked",
    "rejected",
}
ALLOWED_TEST_STATUS = {"no_save_tested"}
ALLOWED_RISK = {"low", "medium", "high", "unknown"}
ALLOWED_ACTIVATION_STATUS = {"candidate", "readiness_supported_no_save", "remediation", "rejected"}
REQUIRED_TEST_FIELDS = {
    "tested_at",
    "test_status",
    "readiness_status",
    "quality_score",
    "quality_label",
    "noise_risk",
    "source_health_risk",
    "remediation_reason",
    "remediation_hint",
    "accepted_for_default_pack",
    "accepted_pack",
    "activation_status",
}
FORBIDDEN_STATUS_WORDS = {"validated", "certified", "guaranteed", "perfect"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    errors: list[str] = []

    if not CANDIDATE_FILE.exists():
        fail(errors, f"Missing candidate file: {CANDIDATE_FILE}")
    if not SOURCES_FILE.exists():
        fail(errors, f"Missing active source registry: {SOURCES_FILE}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    data = load_json(CANDIDATE_FILE)
    if not isinstance(data, dict):
        fail(errors, "Candidate file must be a JSON object.")
        data = {}

    truth = data.get("current_customer_truth", {})
    expected_truth = {
        "enabled_uae_sources": 13,
        "readiness_supported": 9,
        "remediation": 4,
    }
    for key, expected in expected_truth.items():
        if truth.get(key) != expected:
            fail(errors, f"Current source truth mismatch for {key}: expected {expected}, got {truth.get(key)!r}")

    customer_copy = str(truth.get("customer_copy", "")).lower()
    if "13 enabled" not in customer_copy or "9 readiness-supported" not in customer_copy or "4 under extraction remediation" not in customer_copy:
        fail(errors, "Customer truth copy must preserve 13 enabled / 9 readiness-supported / 4 remediation wording.")
    if "validated" in customer_copy:
        fail(errors, "Customer truth copy must not say validated.")

    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        fail(errors, "Candidate file must include a non-empty candidates list.")
        candidates = []

    rejected = data.get("rejected", [])
    if not isinstance(rejected, list):
        fail(errors, "Rejected list must be a list.")
        rejected = []

    ids: dict[str, int] = {}
    urls: dict[str, int] = {}
    top60_count = 0
    top40_count = 0
    tested_top40_count = 0

    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            fail(errors, f"Candidate #{index} must be an object.")
            continue

        missing = sorted(REQUIRED_FIELDS - set(candidate))
        if missing:
            fail(errors, f"{candidate.get('source_id', f'candidate #{index}')} missing fields: {', '.join(missing)}")

        source_id = str(candidate.get("source_id", "")).strip()
        url = str(candidate.get("url", "")).strip()
        if not source_id:
            fail(errors, f"Candidate #{index} has blank source_id.")
        if not url.startswith("https://"):
            fail(errors, f"{source_id or index} URL must use https://, got {url!r}")

        ids[source_id] = ids.get(source_id, 0) + 1
        urls[url] = urls.get(url, 0) + 1

        if candidate.get("top_60_candidate") is True:
            top60_count += 1
            if candidate.get("official_status") == "uncertain":
                fail(errors, f"{source_id} is top_60_candidate but official_status is uncertain.")
            if candidate.get("initial_status") == "rejected":
                fail(errors, f"{source_id} is top_60_candidate but initial_status is rejected.")

        if candidate.get("top_40_candidate") is True:
            top40_count += 1
            if candidate.get("test_status") == "no_save_tested":
                tested_top40_count += 1

        official_status = candidate.get("official_status")
        if official_status not in ALLOWED_OFFICIAL_STATUS:
            fail(errors, f"{source_id} has invalid official_status: {official_status!r}")

        initial_status = str(candidate.get("initial_status", ""))
        if initial_status not in ALLOWED_INITIAL_STATUS:
            fail(errors, f"{source_id} has invalid initial_status: {initial_status!r}")
        lowered_status = initial_status.lower()
        for word in FORBIDDEN_STATUS_WORDS:
            if word in lowered_status:
                fail(errors, f"{source_id} has forbidden status word: {word}")

        if not isinstance(candidate.get("buyer_relevance"), list) or not candidate.get("buyer_relevance"):
            fail(errors, f"{source_id} must include buyer_relevance list.")
        if not isinstance(candidate.get("candidate_pack"), list) or not candidate.get("candidate_pack"):
            fail(errors, f"{source_id} must include candidate_pack list.")

        if candidate.get("test_status") is not None:
            missing_test_fields = sorted(REQUIRED_TEST_FIELDS - set(candidate))
            if missing_test_fields:
                fail(errors, f"{source_id} tested candidate missing fields: {', '.join(missing_test_fields)}")
            if candidate.get("test_status") not in ALLOWED_TEST_STATUS:
                fail(errors, f"{source_id} has invalid test_status: {candidate.get('test_status')!r}")
            if candidate.get("noise_risk") not in ALLOWED_RISK:
                fail(errors, f"{source_id} has invalid noise_risk: {candidate.get('noise_risk')!r}")
            if candidate.get("source_health_risk") not in ALLOWED_RISK:
                fail(errors, f"{source_id} has invalid source_health_risk: {candidate.get('source_health_risk')!r}")
            if candidate.get("activation_status") not in ALLOWED_ACTIVATION_STATUS:
                fail(errors, f"{source_id} has invalid activation_status: {candidate.get('activation_status')!r}")
            if not isinstance(candidate.get("quality_score"), int):
                fail(errors, f"{source_id} quality_score must be an integer.")
            if not isinstance(candidate.get("accepted_for_default_pack"), bool):
                fail(errors, f"{source_id} accepted_for_default_pack must be a boolean.")
            if not isinstance(candidate.get("accepted_pack"), list) or not candidate.get("accepted_pack"):
                fail(errors, f"{source_id} accepted_pack must be a non-empty list.")
            if candidate.get("accepted_for_default_pack") and candidate.get("noise_risk") == "high":
                fail(errors, f"{source_id} cannot be accepted with high noise risk.")
            if candidate.get("accepted_for_default_pack") and candidate.get("source_health_risk") == "high":
                fail(errors, f"{source_id} cannot be accepted with high source-health risk.")
            if candidate.get("activation_status") == "readiness_supported_no_save" and candidate.get("evidence_level") != "PREVIEW_ONLY":
                fail(errors, f"{source_id} no-save readiness must remain PREVIEW_ONLY evidence level.")
            if candidate.get("activation_status") == "readiness_supported_no_save" and candidate.get("accepted_for_default_pack") is not True:
                fail(errors, f"{source_id} readiness_supported_no_save must be explicitly accepted for default-pack consideration.")

    duplicate_ids = sorted(source_id for source_id, count in ids.items() if count > 1)
    duplicate_urls = sorted(url for url, count in urls.items() if count > 1)
    if duplicate_ids:
        fail(errors, "Duplicate candidate source IDs: " + ", ".join(duplicate_ids))
    if duplicate_urls:
        fail(errors, "Duplicate candidate URLs: " + ", ".join(duplicate_urls))

    if top60_count != 60:
        fail(errors, f"Expected exactly 60 top_60 candidates, found {top60_count}.")
    if top40_count < 40:
        fail(errors, f"Expected at least 40 top_40 candidates, found {top40_count}.")
    if top40_count >= 40 and tested_top40_count not in {0, top40_count}:
        fail(errors, f"Top-40 testing is partial: {tested_top40_count} of {top40_count} top-40 candidates have no-save test fields.")

    rejected_ids = {str(item.get("source_id", "")).strip() for item in rejected if isinstance(item, dict)}
    candidate_ids = set(ids)
    overlap = sorted(candidate_ids & rejected_ids)
    if overlap:
        fail(errors, "Rejected source appears as candidate: " + ", ".join(overlap))

    validation_summary = data.get("last_top_40_no_save_validation")
    if validation_summary is not None:
        if not isinstance(validation_summary, dict):
            fail(errors, "last_top_40_no_save_validation must be an object when present.")
        else:
            if validation_summary.get("tested_count") != tested_top40_count:
                fail(errors, "Top-40 validation summary tested_count does not match tested candidates.")
            if validation_summary.get("sources_json_changed") is not False:
                fail(errors, "Top-40 validation summary must not claim sources.json changed in this sprint.")
            if validation_summary.get("public_truth_after_validation") != "13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation":
                fail(errors, "Top-40 validation summary must preserve current public source truth.")
            if validation_summary.get("readiness_supported_no_save_count", 0) >= 40:
                fail(errors, "Validator refuses 40+ readiness claim without a separate source-readiness evidence report.")

    sources = load_json(SOURCES_FILE)
    if isinstance(sources, dict):
        active_sources = sources.get("sources", [])
    else:
        active_sources = sources
    enabled_ae = [
        source
        for source in active_sources
        if isinstance(source, dict)
        and source.get("enabled") is True
        and (source.get("jurisdiction") == "AE" or str(source.get("id", "")).startswith("AE-"))
    ]
    active = [source for source in enabled_ae if source.get("status") == "active"]
    remediation = [source for source in enabled_ae if source.get("status") == "remediation"]
    if len(enabled_ae) != 13 or len(active) != 9 or len(remediation) != 4:
        fail(
            errors,
            f"Active source truth changed unexpectedly: {len(enabled_ae)} enabled / {len(active)} active / {len(remediation)} remediation.",
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("UAE source pack candidate validation passed.")
    print(f"Candidates: {len(candidates)}")
    print(f"Top 40 candidates: {top40_count}")
    print(f"Top 60 candidates: {top60_count}")
    print(f"Rejected examples: {len(rejected)}")
    print("Current customer truth preserved: 13 enabled / 9 readiness-supported / 4 remediation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
