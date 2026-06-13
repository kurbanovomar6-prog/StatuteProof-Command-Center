"""
source_certification.py — source readiness certification model.

Certification is intentionally stricter than a one-off source test. A source can
test successfully without being active-monitoring certified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class CertificationStatus:
    TEST_PASSED = "TEST_PASSED"
    EVIDENCE_CONFIRMED = "EVIDENCE_CONFIRMED"
    BASELINE_PENDING = "BASELINE_PENDING"
    MONITORING_CERTIFIED = "MONITORING_CERTIFIED"
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class EvidenceLevel:
    PREVIEW_ONLY = "PREVIEW_ONLY"
    BASIC_EVIDENCE = "BASIC_EVIDENCE"
    FULL_EVIDENCE = "FULL_EVIDENCE"
    CERTIFIED_EVIDENCE = "CERTIFIED_EVIDENCE"


FAILED_INTAKE_STATUSES = {
    "BLOCKED",
    "UNSUPPORTED",
    "QUALITY_DROP",
    "NAV_SHELL_ONLY",
    "JS_RENDERING_NEEDED",
    "PDF_EXTRACTION_NEEDED",
}

REVIEW_INTAKE_STATUSES = {"NEEDS_SELECTOR_REVIEW"}


@dataclass
class SourceCertification:
    source_id: str
    source_url: str
    canonical_url: str = ""
    first_test_at: str | None = None
    first_evidence_at: str | None = None
    baseline_runs_required: int = 2
    baseline_runs_completed: int = 0
    last_successful_run_at: str | None = None
    certification_status: str = CertificationStatus.CERTIFICATION_FAILED
    certification_score: int = 0
    extraction_quality_score: int = 0
    evidence_completeness_score: int = 0
    monitoring_stability_score: int = 0
    failure_reasons: list[str] = field(default_factory=list)
    remediation_hints: list[str] = field(default_factory=list)
    provider_history: list[str] = field(default_factory=list)
    hash_history: list[str] = field(default_factory=list)
    proof_paths: list[str] = field(default_factory=list)
    diff_paths: list[str] = field(default_factory=list)
    evidence_level: str = EvidenceLevel.PREVIEW_ONLY

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_url": self.source_url,
            "canonical_url": self.canonical_url,
            "first_test_at": self.first_test_at,
            "first_evidence_at": self.first_evidence_at,
            "baseline_runs_required": self.baseline_runs_required,
            "baseline_runs_completed": self.baseline_runs_completed,
            "last_successful_run_at": self.last_successful_run_at,
            "certification_status": self.certification_status,
            "certification_score": self.certification_score,
            "extraction_quality_score": self.extraction_quality_score,
            "evidence_completeness_score": self.evidence_completeness_score,
            "monitoring_stability_score": self.monitoring_stability_score,
            "failure_reasons": self.failure_reasons,
            "remediation_hints": self.remediation_hints,
            "provider_history": self.provider_history,
            "hash_history": self.hash_history,
            "proof_paths": self.proof_paths,
            "diff_paths": self.diff_paths,
            "evidence_level": self.evidence_level,
        }


def evidence_level_from_run(record: dict | None, baseline_complete: bool = False) -> str:
    if not record:
        return EvidenceLevel.PREVIEW_ONLY
    has_basic = bool(
        record.get("proof_block_path")
        and record.get("snapshot_raw_path")
        and record.get("snapshot_normalized_path")
        and record.get("normalized_hash")
    )
    has_full = bool(has_basic and record.get("snapshot_metadata_path"))
    if baseline_complete and has_full:
        return EvidenceLevel.CERTIFIED_EVIDENCE
    if has_full:
        return EvidenceLevel.FULL_EVIDENCE
    if has_basic:
        return EvidenceLevel.BASIC_EVIDENCE
    return EvidenceLevel.PREVIEW_ONLY


def build_preview_certification(
    *,
    source_id: str,
    source_url: str,
    canonical_url: str = "",
    intake_result: dict,
    quality_report: dict,
    baseline_runs_required: int = 2,
) -> dict:
    status = str(intake_result.get("status") or "")
    cert = SourceCertification(
        source_id=source_id,
        source_url=source_url,
        canonical_url=canonical_url or source_url,
        baseline_runs_required=baseline_runs_required,
        extraction_quality_score=int(quality_report.get("quality_score") or 0),
        evidence_completeness_score=0,
        monitoring_stability_score=0,
        provider_history=[p for p in [intake_result.get("provider_used") or intake_result.get("extraction_method")] if p],
        hash_history=[h for h in [intake_result.get("normalized_hash") or intake_result.get("content_hash")] if h],
        evidence_level=EvidenceLevel.PREVIEW_ONLY,
    )
    if status == "CONFIRMED_ACCESSIBLE":
        cert.certification_status = CertificationStatus.TEST_PASSED
        cert.certification_score = min(70, cert.extraction_quality_score)
        cert.remediation_hints.append("Save evidence and complete baseline runs before active monitoring certification.")
    elif status in REVIEW_INTAKE_STATUSES:
        cert.certification_status = CertificationStatus.NEEDS_HUMAN_REVIEW
        cert.certification_score = min(50, cert.extraction_quality_score)
        cert.failure_reasons.append(intake_result.get("failure_reason") or "Selector or source ambiguity remains.")
        cert.remediation_hints.append(intake_result.get("remediation_hint") or "Human selector review required.")
    else:
        cert.certification_status = CertificationStatus.CERTIFICATION_FAILED
        cert.certification_score = min(39, cert.extraction_quality_score)
        cert.failure_reasons.append(intake_result.get("failure_reason") or f"Intake status {status} cannot be certified.")
        if intake_result.get("remediation_hint"):
            cert.remediation_hints.append(intake_result["remediation_hint"])
    return cert.as_dict()


def build_certification_from_runs(
    *,
    source_id: str,
    source_url: str,
    runs: list[dict],
    baseline_runs_required: int = 2,
    quality_score: int = 0,
) -> dict:
    runs = [r for r in runs if r.get("source_id") == source_id]
    runs.sort(key=lambda r: str(r.get("timestamp_utc") or ""))
    successful = [
        r for r in runs
        if r.get("access_status") not in {"failed", "restricted", "blocked"}
        and r.get("change_status") not in {"FAILED", "QUALITY_DROP", "SOURCE_STRUCTURE_CHANGED"}
        and r.get("proof_block_path")
        and r.get("normalized_hash")
    ]
    latest = successful[-1] if successful else (runs[-1] if runs else None)
    baseline_complete = len(successful) >= baseline_runs_required
    evidence_level = evidence_level_from_run(latest, baseline_complete=baseline_complete)
    proof_paths = [str(r.get("proof_block_path")) for r in successful if r.get("proof_block_path")]
    diff_paths = [
        str(r.get("diff_json_path") or r.get("diff_md_path"))
        for r in successful
        if r.get("diff_json_path") or r.get("diff_md_path")
    ]

    cert = SourceCertification(
        source_id=source_id,
        source_url=source_url,
        canonical_url=str((latest or {}).get("final_url") or source_url),
        first_evidence_at=str(successful[0].get("timestamp_utc")) if successful else None,
        baseline_runs_required=baseline_runs_required,
        baseline_runs_completed=len(successful),
        last_successful_run_at=str(successful[-1].get("timestamp_utc")) if successful else None,
        extraction_quality_score=quality_score,
        evidence_completeness_score=100 if evidence_level in {EvidenceLevel.FULL_EVIDENCE, EvidenceLevel.CERTIFIED_EVIDENCE} else 60 if evidence_level == EvidenceLevel.BASIC_EVIDENCE else 0,
        monitoring_stability_score=min(100, int(len(successful) / max(1, baseline_runs_required) * 100)),
        provider_history=[str(r.get("fetch_method") or "") for r in successful if r.get("fetch_method")],
        hash_history=[str(r.get("normalized_hash")) for r in successful if r.get("normalized_hash")],
        proof_paths=proof_paths,
        diff_paths=diff_paths,
        evidence_level=evidence_level,
    )
    if baseline_complete:
        cert.certification_status = CertificationStatus.MONITORING_CERTIFIED
        cert.certification_score = min(100, int((cert.extraction_quality_score + cert.evidence_completeness_score + cert.monitoring_stability_score) / 3))
    elif successful:
        cert.certification_status = CertificationStatus.BASELINE_PENDING
        cert.certification_score = min(85, int((cert.extraction_quality_score + cert.evidence_completeness_score + cert.monitoring_stability_score) / 3))
        cert.remediation_hints.append("Complete repeat baseline run before monitoring certification.")
    else:
        cert.certification_status = CertificationStatus.CERTIFICATION_FAILED
        cert.certification_score = 0
        cert.failure_reasons.append("No successful evidence run with proof and normalized hash was found.")
    return cert.as_dict()
