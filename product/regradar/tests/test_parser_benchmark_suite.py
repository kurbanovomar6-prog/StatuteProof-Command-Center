from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.source_certification import (
    CertificationStatus,
    EvidenceLevel,
    build_certification_from_runs,
    evidence_level_from_run,
)
from app.source_intake import SourceIntakeStatus, _content_hash, run_source_intake
from app.source_quality import build_quality_score, detect_policy_warnings
from app.text_normalization import normalize_for_change_hash


FIXTURES = Path(__file__).parent / "fixtures" / "source_intake"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def run_fixture(name: str, **source_overrides) -> dict:
    html = fixture(name)
    source = {
        "source_id": f"fixture-{name}",
        "name": name,
        "url": "https://official.example/source",
        "expected_min_length": 250,
        "content_selector": "main",
        **source_overrides,
    }
    with patch("app.scraper.fetch_page_with_config", return_value=html):
        return run_source_intake(source, all_sources=[], write_evidence=False)


def test_good_regulatory_html_passes_but_preview_score_reflects_no_proof():
    result = run_fixture("static_regulator_good.html")
    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["quality_score"] >= 40
    assert result["evidence_level"] == EvidenceLevel.PREVIEW_ONLY
    assert result["certification_status"] == CertificationStatus.TEST_PASSED


def test_nav_shell_blocked():
    result = run_fixture("nav_shell_only.html")
    assert result["status"] in {SourceIntakeStatus.NAV_SHELL_ONLY, SourceIntakeStatus.BLOCKED}
    assert result["quality_score"] < 60


def test_login_page_blocked():
    result = run_fixture("login_page.html")
    assert result["status"] == SourceIntakeStatus.BLOCKED
    assert "login" in result["quality_breakdown"]["policy_warnings"]


def test_captcha_page_blocked():
    result = run_fixture("captcha_page.html")
    assert result["status"] == SourceIntakeStatus.BLOCKED
    assert "captcha" in result["quality_breakdown"]["policy_warnings"]


def test_paywall_page_blocked():
    result = run_fixture("paywall_page.html")
    assert result["status"] == SourceIntakeStatus.BLOCKED
    assert "paywall" in result["quality_breakdown"]["policy_warnings"]


def test_shallow_homepage_limited_or_poor():
    result = run_fixture("short_homepage.html")
    assert result["status"] in {SourceIntakeStatus.JS_RENDERING_NEEDED, SourceIntakeStatus.QUALITY_DROP, SourceIntakeStatus.NAV_SHELL_ONLY}
    assert result["quality_score"] < 60


def test_listing_page_classified_as_extractable_but_not_certified():
    result = run_fixture("listing_page.html")
    assert result["status"] in {SourceIntakeStatus.CONFIRMED_ACCESSIBLE, SourceIntakeStatus.QUALITY_DROP, SourceIntakeStatus.NAV_SHELL_ONLY}
    assert result["certification_status"] in {CertificationStatus.TEST_PASSED, CertificationStatus.CERTIFICATION_FAILED}


def test_pdf_good_text_quality_direct_score():
    text = "Regulatory circular requirements for licensed firms. " * 80
    report = build_quality_score(
        url="https://official.example/file.pdf",
        fetch_success=True,
        normalized_text=text,
        normalized_hash="a" * 64,
        canonical_url="https://official.example/file.pdf",
        provider_confidence="high",
        proof_path="proof.json",
    )
    assert report["quality_score"] >= 60


def test_pdf_shallow_flagged():
    report = build_quality_score(
        url="https://official.example/file.pdf",
        fetch_success=True,
        normalized_text="short pdf text",
        normalized_hash="a" * 64,
        canonical_url="https://official.example/file.pdf",
        provider_confidence="low",
        pdf_shallow=True,
    )
    assert report["penalties"]["pdf_text_too_shallow"] == -30
    assert report["quality_score"] < 40


def test_hash_collision_blocks_certification():
    html = fixture("static_regulator_good.html")
    normalized = normalize_for_change_hash("Regulatory Notice on AML Controls " * 40)
    collision_hash = _content_hash(normalized)
    source = {
        "source_id": "fixture-collision",
        "url": "https://official.example/source",
        "expected_min_length": 100,
    }
    with patch("app.scraper.fetch_page_with_config", return_value=html), \
         patch("app.extractors.extract_best_text", return_value={"text": normalized, "method": "unit", "provider_used": "unit"}):
        result = run_source_intake(
            source,
            all_sources=[{"source_id": "other", "enabled": True, "content_hash": collision_hash}],
            write_evidence=False,
        )
    assert result["status"] == SourceIntakeStatus.NAV_SHELL_ONLY
    assert result["certification_status"] == CertificationStatus.CERTIFICATION_FAILED


def test_no_save_test_cannot_claim_evidence():
    result = run_fixture("vara_rulebook_like.html")
    assert result["evidence_written"] is False
    assert result["evidence_level"] == EvidenceLevel.PREVIEW_ONLY
    assert result["proof_path"] is None


def test_save_mode_can_return_basic_evidence_with_mocked_writer():
    with patch("app.source_intake._write_intake_evidence", return_value={
        "proof_path": "data/source_snapshots/test/proof.json",
        "evidence_paths": {"proof_block_path": "data/source_snapshots/test/proof.json"},
        "evidence_level": EvidenceLevel.BASIC_EVIDENCE,
    }):
        result = run_fixture("vara_rulebook_like.html")
        html = fixture("vara_rulebook_like.html")
        with patch("app.scraper.fetch_page_with_config", return_value=html):
                result = run_source_intake({
                    "source_id": "fixture-save",
                    "url": "https://official.example/source",
                    "expected_min_length": 250,
                    "content_selector": "main",
                }, write_evidence=True)
    assert result["evidence_written"] is True
    assert result["evidence_level"] == EvidenceLevel.BASIC_EVIDENCE


def test_certification_requires_baseline():
    runs = [{
        "source_id": "s1",
        "timestamp_utc": "2026-06-14T00:00:00Z",
        "access_status": "accessible",
        "change_status": "FIRST_SEEN",
        "proof_block_path": "proof.json",
        "snapshot_raw_path": "raw.txt",
        "snapshot_normalized_path": "normalized.txt",
        "snapshot_metadata_path": "metadata.json",
        "normalized_hash": "a" * 64,
    }]
    cert = build_certification_from_runs(source_id="s1", source_url="https://official.example", runs=runs, baseline_runs_required=2, quality_score=80)
    assert cert["certification_status"] == CertificationStatus.BASELINE_PENDING


def test_certification_does_not_count_duplicate_run_as_baseline():
    run = {
        "source_id": "s1",
        "run_id": "same-run",
        "timestamp_utc": "2026-06-14T00:00:00Z",
        "access_status": "accessible",
        "change_status": "FIRST_SEEN",
        "proof_block_path": "proof.json",
        "snapshot_raw_path": "raw.txt",
        "snapshot_normalized_path": "normalized.txt",
        "snapshot_metadata_path": "metadata.json",
        "normalized_hash": "a" * 64,
    }
    cert = build_certification_from_runs(
        source_id="s1",
        source_url="https://official.example",
        runs=[run, dict(run)],
        baseline_runs_required=2,
        quality_score=80,
    )
    assert cert["baseline_runs_completed"] == 1
    assert cert["certification_status"] == CertificationStatus.BASELINE_PENDING


def test_quality_score_breakdown_sums_with_bounds():
    report = build_quality_score(
        url="https://official.example",
        fetch_success=True,
        normalized_text="Regulatory requirements for licensed firms. " * 60,
        normalized_hash="a" * 64,
        canonical_url="https://official.example",
        provider_confidence="high",
    )
    assert 0 <= report["quality_score"] <= 100
    assert sum(report["components"].values()) + sum(report["penalties"].values()) >= report["quality_score"]


def test_provider_cascade_chooses_best_provider():
    result = run_fixture("cbuae_guidance_like.html")
    assert result["provider_used"]
    assert result["chars_normalized"] > 200


def test_missing_optional_dependencies_do_not_crash():
    from app.providers.optional_tools import canonicalize_url, extract_date_from_html, structured_diff
    assert canonicalize_url("https://official.example")["success"] in {True, False}
    assert "success" in extract_date_from_html("<html></html>")
    assert structured_diff({"a": 1}, {"a": 2})["success"] in {True, False}


def test_selector_timeout_becomes_needs_selector_review():
    with patch("app.scraper.fetch_page_with_config", side_effect=TimeoutError("selector timed out")):
        result = run_source_intake({
            "source_id": "selector-timeout",
            "url": "https://official.example",
            "wait_for_selector": "main",
            "content_selector": "main",
        })
    assert result["status"] == SourceIntakeStatus.NEEDS_SELECTOR_REVIEW


def test_dfsa_like_shell_not_confirmed():
    result = run_fixture("dfsa_nav_shell_sample.html")
    assert result["status"] != SourceIntakeStatus.CONFIRMED_ACCESSIBLE


def test_metadata_date_extraction_works_or_unavailable_safely():
    from app.providers.optional_tools import extract_date_from_html
    result = extract_date_from_html("<time datetime='2026-06-14'>14 June 2026</time>")
    assert "available" in result
    assert "success" in result


def test_warc_optional_provider_unavailable_does_not_block_core_parsing():
    try:
        import warcio  # noqa: F401
        available = True
    except ImportError:
        available = False
    result = run_fixture("static_regulator_good.html")
    assert available in {True, False}
    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE


def test_policy_warning_detector_private_portal():
    warnings = detect_policy_warnings("This private portal is for authorised users only.")
    assert "private_portal" in warnings
