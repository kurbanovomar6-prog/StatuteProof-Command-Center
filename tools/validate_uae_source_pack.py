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
ALLOWED_ACTIVATION_STATUS = {
    "candidate",
    "readiness_supported_no_save",
    "baseline_pending",
    "activation_ready",
    "remediation",
    "rejected",
    "blocked",
}
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
SELECTOR_INVESTIGATION_FIELDS = {
    "selector_investigated",
    "recommended_url",
    "recommended_wait_selector",
    "recommended_content_selector",
    "recommended_next_action",
}
SAVED_BASELINE_FIELDS = {
    "saved_baseline_at",
    "proof_path",
    "normalized_text_path",
    "evidence_level",
    "baseline_runs_completed",
    "baseline_runs_required",
    "can_activate_monitoring",
}
ADGM_FSRA_SCA_PREFIXES = ("AE-adgm", "AE-sca")
EXPECTED_ENABLED_UAE_SOURCES = 79
EXPECTED_READINESS_SUPPORTED = 78
EXPECTED_REMEDIATION = 1
EXPECTED_CUSTOMER_COPY = (
    f"{EXPECTED_ENABLED_UAE_SOURCES} enabled UAE sources; "
    f"{EXPECTED_READINESS_SUPPORTED} readiness-supported; "
    f"{EXPECTED_REMEDIATION} under extraction remediation"
)
CLAIM_SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
]
FORBIDDEN_MARKETING_CLAIMS = {
    "40+ monitored sources",
    "40+ sources monitored",
    "40+ active sources",
    "60 validated sources",
    "60 monitored sources",
    "60 active sources",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_claim_scan_files() -> list[Path]:
    files: list[Path] = []
    for path in CLAIM_SCAN_PATHS:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists():
            files.append(path)
    return files


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
        "enabled_uae_sources": EXPECTED_ENABLED_UAE_SOURCES,
        "readiness_supported": EXPECTED_READINESS_SUPPORTED,
        "remediation": EXPECTED_REMEDIATION,
    }
    for key, expected in expected_truth.items():
        if truth.get(key) != expected:
            fail(errors, f"Current source truth mismatch for {key}: expected {expected}, got {truth.get(key)!r}")

    customer_copy = str(truth.get("customer_copy", "")).lower()
    if (
        f"{EXPECTED_ENABLED_UAE_SOURCES} enabled" not in customer_copy
        or f"{EXPECTED_READINESS_SUPPORTED} readiness-supported" not in customer_copy
        or f"{EXPECTED_REMEDIATION} under extraction remediation" not in customer_copy
    ):
        fail(errors, f"Customer truth copy must preserve {EXPECTED_CUSTOMER_COPY} wording.")
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
    adgm_sca_investigated_count = 0

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
                note = " ".join(
                    str(candidate.get(key, ""))
                    for key in ("remediation_hint", "recommended_next_action", "recommendation")
                ).lower()
                if "filter" not in note and "listing" not in note and "noise" not in note:
                    fail(errors, f"{source_id} cannot be accepted with high noise risk without a filter/noise note.")
            if candidate.get("accepted_for_default_pack") and candidate.get("source_health_risk") == "high":
                note = " ".join(
                    str(candidate.get(key, ""))
                    for key in ("remediation_reason", "remediation_hint", "recommended_next_action")
                ).lower()
                if "remediation" not in note and "adapter" not in note and "manual" not in note:
                    fail(errors, f"{source_id} cannot be accepted with high source-health risk without remediation note.")
            if candidate.get("activation_status") == "readiness_supported_no_save" and candidate.get("evidence_level") != "PREVIEW_ONLY":
                fail(errors, f"{source_id} no-save readiness must remain PREVIEW_ONLY evidence level.")

        if source_id.startswith(ADGM_FSRA_SCA_PREFIXES) and candidate.get("selector_investigated") is True:
            adgm_sca_investigated_count += 1
            missing_selector_fields = sorted(SELECTOR_INVESTIGATION_FIELDS - set(candidate))
            if missing_selector_fields:
                fail(errors, f"{source_id} selector-investigated candidate missing fields: {', '.join(missing_selector_fields)}")
            if candidate.get("test_status") == "no_save_tested":
                for risk_field in ("noise_risk", "source_health_risk"):
                    if candidate.get(risk_field) not in ALLOWED_RISK:
                        fail(errors, f"{source_id} selector-tested candidate has invalid {risk_field}: {candidate.get(risk_field)!r}")
            if candidate.get("activation_status") == "rejected" and candidate.get("accepted_for_default_pack") is True:
                fail(errors, f"{source_id} rejected candidate cannot be accepted for default pack.")

        if candidate.get("saved_baseline_attempted") is True:
            missing_saved_fields = sorted(SAVED_BASELINE_FIELDS - set(candidate))
            if missing_saved_fields:
                fail(errors, f"{source_id} saved-baseline candidate missing fields: {', '.join(missing_saved_fields)}")
            baseline_completed = int(candidate.get("baseline_runs_completed") or 0)
            baseline_required = int(candidate.get("baseline_runs_required") or 2)
            can_activate = candidate.get("can_activate_monitoring")
            evidence_level = candidate.get("evidence_level")
            if can_activate not in {True, False}:
                fail(errors, f"{source_id} can_activate_monitoring must be boolean.")
            if can_activate and baseline_completed < baseline_required:
                fail(errors, f"{source_id} cannot activate before required baselines are complete.")
            if can_activate and evidence_level != "CERTIFIED_EVIDENCE":
                fail(errors, f"{source_id} cannot activate without CERTIFIED_EVIDENCE.")
            if evidence_level in {"FULL_EVIDENCE", "CERTIFIED_EVIDENCE"}:
                if not candidate.get("proof_path") or not candidate.get("normalized_text_path"):
                    fail(errors, f"{source_id} evidence level {evidence_level} requires proof_path and normalized_text_path.")
                if baseline_completed < 1:
                    fail(errors, f"{source_id} full evidence requires at least one completed baseline run.")
            if evidence_level == "PREVIEW_ONLY" and candidate.get("proof_path"):
                fail(errors, f"{source_id} PREVIEW_ONLY saved-baseline attempt must not include proof_path.")
            if candidate.get("activation_status") == "baseline_pending" and can_activate:
                fail(errors, f"{source_id} baseline_pending candidate cannot activate monitoring.")
            if candidate.get("activation_status") == "baseline_pending" and baseline_completed >= baseline_required:
                fail(errors, f"{source_id} baseline_pending has completed baselines; review activation status.")
            if candidate.get("activation_status") == "activation_ready":
                if not can_activate:
                    fail(errors, f"{source_id} activation_ready candidate must set can_activate_monitoring true.")
                if baseline_completed < baseline_required:
                    fail(errors, f"{source_id} activation_ready candidate requires completed baselines.")
                if evidence_level != "CERTIFIED_EVIDENCE":
                    fail(errors, f"{source_id} activation_ready candidate requires CERTIFIED_EVIDENCE.")
                if candidate.get("noise_risk") == "high" or candidate.get("source_health_risk") == "high":
                    fail(errors, f"{source_id} activation_ready candidate cannot have unresolved high noise/source-health risk.")

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
            if validation_summary.get("public_truth_after_validation") != EXPECTED_CUSTOMER_COPY:
                fail(errors, "Top-40 validation summary must preserve current public source truth.")
            if validation_summary.get("readiness_supported_no_save_count", 0) >= 40:
                fail(errors, "Validator refuses 40+ readiness claim without a separate source-readiness evidence report.")

    selector_summary = data.get("last_adgm_fsra_sca_selector_remediation")
    if selector_summary is not None:
        if not isinstance(selector_summary, dict):
            fail(errors, "last_adgm_fsra_sca_selector_remediation must be an object when present.")
        else:
            if selector_summary.get("sources_json_changed") is not False:
                fail(errors, "ADGM/FSRA + SCA remediation summary must not claim sources.json changed.")
            if selector_summary.get("public_truth_after_validation") != EXPECTED_CUSTOMER_COPY:
                fail(errors, "ADGM/FSRA + SCA remediation summary must preserve current public source truth.")
            if selector_summary.get("tested_count", 0) < 1:
                fail(errors, "ADGM/FSRA + SCA remediation summary must record tested candidates.")
            if adgm_sca_investigated_count < 10:
                fail(errors, f"Expected ADGM/FSRA + SCA selector investigation metadata, found {adgm_sca_investigated_count} candidates.")

    saved_summary = data.get("last_adgm_fsra_sca_saved_baseline")
    if saved_summary is not None:
        if not isinstance(saved_summary, dict):
            fail(errors, "last_adgm_fsra_sca_saved_baseline must be an object when present.")
        else:
            if saved_summary.get("saved_checks_run_count") != 4:
                fail(errors, "Saved baseline summary must be scoped to exactly four checks.")
            if saved_summary.get("sources_json_changed") is not False:
                fail(errors, "Saved baseline summary must not claim sources.json changed.")
            if saved_summary.get("public_truth_after_validation") != EXPECTED_CUSTOMER_COPY:
                fail(errors, "Saved baseline summary must preserve current public source truth.")
            if int(saved_summary.get("monitoring_ready_count") or 0) != 0:
                fail(errors, "Saved baseline summary must not claim monitoring-ready sources from this sprint.")

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
    if (
        len(enabled_ae) != EXPECTED_ENABLED_UAE_SOURCES
        or len(active) != EXPECTED_READINESS_SUPPORTED
        or len(remediation) != EXPECTED_REMEDIATION
    ):
        fail(
            errors,
            f"Active source truth changed unexpectedly: {len(enabled_ae)} enabled / {len(active)} active / {len(remediation)} remediation.",
        )

    for path in iter_claim_scan_files():
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        for claim in FORBIDDEN_MARKETING_CLAIMS:
            if claim in text:
                fail(errors, f"Forbidden customer-facing 40/60 marketing claim in {path.relative_to(ROOT)}: {claim}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("UAE source pack candidate validation passed.")
    print(f"Candidates: {len(candidates)}")
    print(f"Top 40 candidates: {top40_count}")
    print(f"Top 60 candidates: {top60_count}")
    print(f"Rejected examples: {len(rejected)}")
    print(
        "Current customer truth preserved: "
        f"{EXPECTED_ENABLED_UAE_SOURCES} enabled / "
        f"{EXPECTED_READINESS_SUPPORTED} readiness-supported / "
        f"{EXPECTED_REMEDIATION} remediation."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
