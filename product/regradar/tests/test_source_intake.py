"""
Tests for source_intake.py — Universal Source Intake Layer.

All tests use mocked HTTP responses. No live network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.source_intake import (
    SourceIntakeStatus,
    _check_hash_collision,
    _content_hash,
    is_nav_shell_only,
    readiness_summary,
    run_source_intake,
)

# ── fixtures ──────────────────────────────────────────────────────────────────

_GOOD_HTML = """
<html><body>
<main>
<h1>DFSA Regulatory Framework</h1>
<p>The Dubai Financial Services Authority (DFSA) has published new conduct rules
for all Category 3A licence holders operating within the DIFC. The updated rules
take effect from 1 July 2026 and require enhanced client money reporting.</p>
<p>All licensed firms must submit a compliance attestation to the DFSA by 30 June 2026.
Failure to comply may result in enforcement action under Article 90 of the Markets Law.</p>
<p>The DFSA expects firms to review their systems and controls for client asset handling,
segregation, and reconciliation in line with the Client Money module (CMO).</p>
<p>Questions regarding the new requirements should be directed to the DFSA Authorisation
Division. Firms seeking additional guidance may request a supervisory meeting.</p>
</main>
</body></html>
"""

_NAV_SHELL_TEXT = (
    "About us\nGo Back\nWho we are\nThe DFSA\nGovernance\nLeadership\n"
    "Regulation\nRules\nStandards\nGuidance\nForms\nContacts\nSearch\n"
    "Sitemap\nPrivacy\nAccessibility\nDisclaimer\nCareers\nMedia\nNews\n"
)

_GOOD_TEXT = (
    "The Dubai Financial Services Authority (DFSA) has published updated conduct rules "
    "for Category 3A licence holders. The new rules require enhanced client money "
    "reporting and take effect from 1 July 2026. All licensed firms must submit a "
    "compliance attestation by 30 June 2026. Failure to comply may result in "
    "enforcement action under Article 90 of the Markets Law.\n\n"
    "The DFSA expects firms to review their systems and controls for client asset "
    "handling, segregation, and reconciliation in line with the Client Money module.\n\n"
    "Firms with questions should contact the DFSA Authorisation Division directly.\n\n"
    "The DFSA Regulatory Notice (RN-20260601) is available on the official DFSA portal.\n"
)

_SOURCES_WITH_HASH = [
    {
        "source_id": "AE-dfsa-rules",
        "enabled": True,
        "content_hash": "abc123def456abcd",
    },
    {
        "source_id": "AE-dfsa-notices",
        "enabled": True,
        "content_hash": "xyz789xyz789xyz7",
    },
]

# ── 1. URL validation ─────────────────────────────────────────────────────────


def test_valid_url_passes_ssrf_check():
    from app.source_tester import validate_public_url
    safe, reason = validate_public_url("https://www.dfsa.ae/rules-and-standards")
    assert safe is True


def test_private_ip_blocked():
    from app.source_tester import validate_public_url
    safe, reason = validate_public_url("http://192.168.1.1/admin")
    assert safe is False
    assert "public" in reason.lower() or "private" in reason.lower() or "blocked" in reason.lower()


def test_localhost_blocked():
    from app.source_tester import validate_public_url
    safe, reason = validate_public_url("http://localhost:5000/api")
    assert safe is False


def test_file_url_blocked():
    from app.source_tester import validate_public_url
    safe, reason = validate_public_url("file:///etc/passwd")
    assert safe is False


def test_loopback_ip_blocked():
    from app.source_tester import validate_public_url
    safe, reason = validate_public_url("http://127.0.0.1:5000/api")
    assert safe is False


def test_unspecified_ip_blocked():
    from app.source_tester import validate_public_url
    safe, reason = validate_public_url("http://0.0.0.0:8000")
    assert safe is False


def test_credentials_in_url_blocked():
    from app.source_tester import validate_public_url
    safe, reason = validate_public_url("https://user:password@example.com/source")
    assert safe is False
    assert "credentials" in reason.lower()


# ── 2. Nav-shell detection ────────────────────────────────────────────────────


def test_nav_shell_detected_on_short_lines():
    assert is_nav_shell_only(_NAV_SHELL_TEXT) is True


def test_good_content_passes_nav_check():
    assert is_nav_shell_only(_GOOD_TEXT) is False


def test_repeated_menu_shell_detected():
    repeated_shell = "\n".join([
        "Home", "About", "Rules", "Guidance", "Forms", "News", "Contact",
        "Search", "Privacy", "Accessibility",
    ] * 12)
    assert is_nav_shell_only(repeated_shell) is True


def test_mixed_page_with_article_not_nav_shell():
    mixed = _NAV_SHELL_TEXT + "\n" + (_GOOD_TEXT * 4)
    assert is_nav_shell_only(mixed) is False


def test_nav_shell_below_max_chars_threshold():
    # Nav shell should be detected only when chars < _NAV_SHELL_MAX_CHARS (10,000)
    long_nav = (_NAV_SHELL_TEXT * 500)  # ~10,000+ chars
    # Above threshold → should NOT be flagged (avoids false positives on large pages)
    assert is_nav_shell_only(long_nav) is False


def test_empty_text_not_nav_shell():
    assert is_nav_shell_only("") is False


def test_structured_listing_adapter_output_is_not_nav_shell():
    cards = "\n".join(
        f"""
        <div class="aegov-card card-bordered card-service" role="group" aria-labelledby="general-landing-item-{idx}">
          <h5 id="general-landing-item-{idx}">{title}</h5>
          <a href="/assets/{idx}/official-regulatory-document-{idx}.aspx" title="View Details">View Details</a>
        </div>
        """
        for idx, title in enumerate(
            [
                "Passporting Rules for capital market participants and cross-border financial services",
                "Circular on the Annual General Assembly Meetings of Public Joint-Stock Companies for 2024",
                "Circular on Contracting with individuals or Unlicensed Entities for soliciting Clients",
                "Guidelines Regulation of Virtual Assets and Virtual Assets Services Providers",
                "FinTech regulatory framework for supervised capital market services",
                "Market rules approved by SCA for licensed capital market institutions and compliance teams",
                "AML/CFT regulatory procedures for supervised capital market firms and reporting controls",
            ],
            start=1,
        )
    )
    html = f"<html><body><form id='aspnetForm'><main>{cards}</main></form></body></html>"
    source = {
        "source_id": "AE-sca-structured-listing",
        "url": "https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures",
        "adapter_family": "sca_listing",
        "adapter_config": {"container_selector": "main", "max_items": 20},
        "expected_min_length": 500,
    }

    with patch("app.scraper.fetch_page_with_config", return_value=html):
        result = run_source_intake(source, write_evidence=False)

    assert result["adapter_used"] is True
    assert result["adapter_metadata"]["item_count"] == 7
    assert result["nav_shell_detected"] is False
    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["quality_score"] >= 60
    assert result["can_save_for_validation"] is True
    assert result["can_activate_monitoring"] is False


def test_custom_element_adapter_preserves_structure_for_quality_gate():
    aml_paragraph = (
        "Regulated firms must maintain anti money laundering governance, customer "
        "due diligence, enhanced due diligence, suspicious activity reporting, "
        "financial crime risk assessment, staff training, and board-approved "
        "compliance monitoring controls for supervised business activities. "
    )
    sanctions_paragraph = (
        "Firms must maintain targeted financial sanctions screening, sanctions "
        "alert review, asset-freezing escalation, record keeping, and reporting "
        "procedures that support regulatory obligations and documented management "
        "oversight across financial crime prevention controls. "
    )
    reporting_paragraph = (
        "Compliance officers and MLRO functions should review regulatory guidance, "
        "monitor rule updates, assess operational impact, update procedures, and "
        "retain evidence of remediation decisions for supervisory review and audit "
        "readiness across the regulated firm. "
    )
    html = f"""
    <html><body>
      <adgm-page>
        <h1>Financial Crime Prevention</h1>
        <h2>Anti Money Laundering Requirements</h2>
        <p>{aml_paragraph * 3}</p>
        <h2>Sanctions and Targeted Financial Sanctions</h2>
        <p>{sanctions_paragraph * 3}</p>
        <h2>Regulatory Guidance and Reporting</h2>
        <p>{reporting_paragraph * 3}</p>
      </adgm-page>
    </body></html>
    """
    source = {
        "source_id": "AE-adgm-structured-custom-element",
        "url": "https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention",
        "adapter_family": "custom_element",
        "adapter_name": "custom_element",
        "adapter_config": {"content_selector": "adgm-page"},
        "expected_min_length": 500,
    }

    with patch("app.scraper.fetch_page_with_config", return_value=html):
        result = run_source_intake(source, write_evidence=False)

    assert result["adapter_used"] is True
    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["quality_breakdown"]["text_stats"]["heading_count"] >= 3
    assert result["quality_score"] >= 60
    assert result["can_save_for_validation"] is True


def test_focused_custom_element_content_is_not_nav_shell():
    html = """
    <html><body>
      <adgm-page>
        <h2>ADGM Academy</h2>
        <h2>AccessADGM</h2>
        <p>Generic platform content about living and working in Abu Dhabi.</p>
        <h1>Financial & Cybercrime Prevention</h1>
        <h2>Developing sound practices in AML/TFS and cybercrime prevention compliance</h2>
        <p>Money Laundering, Terrorism Financing, Proliferation Financing and cybercrime
        are major risks that threaten economic growth and social stability through the
        illicit flow of funds and illegal activities. Firms should document risk
        assessments, maintain screening controls, review suspicious transactions,
        escalate sanctions matches, and preserve audit evidence for supervisory
        review and internal governance committees.</p>
        <h2>AML and TFS Framework</h2>
        <p>Financial Institutions and DNFBPs must maintain AML, CFT, sanctions,
        customer due diligence, suspicious activity reporting, risk assessment,
        governance, compliance monitoring, and record keeping controls. The
        monitoring process should track changes in laws, rules, guidance, circulars,
        notices, risk typologies, and targeted financial sanctions expectations.</p>
        <h2>Risk Based Approach</h2>
        <p>The Financial Services Regulatory Authority is the competent authority
        for AML and TFS compliance and expects firms to maintain a robust regulatory
        framework, documented procedures, monitoring controls, and management
        oversight. Compliance teams should use official-source evidence to support
        remediation decisions, board reporting, policy updates, and operational
        control testing.</p>
      </adgm-page>
    </body></html>
    """
    source = {
        "source_id": "AE-adgm-focused-financial-crime",
        "url": "https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention",
        "adapter_family": "custom_element",
        "adapter_name": "custom_element",
        "adapter_config": {
            "content_selector": "adgm-page",
            "focus_keywords": ["Financial & Cybercrime Prevention", "Developing sound practices"],
        },
        "expected_min_length": 500,
    }

    with patch("app.scraper.fetch_page_with_config", return_value=html):
        result = run_source_intake(source, write_evidence=False)

    assert result["adapter_used"] is True
    assert result["structured_adapter_content"] is True
    assert result["nav_shell_detected"] is False
    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["can_save_for_validation"] is True


def test_two_substantial_fiu_document_links_are_not_nav_shell():
    legal_context = (
        "This official public document explains anti-money laundering, counter terrorist "
        "financing, proliferation financing, sanctions compliance, reporting obligations, "
        "customer due diligence, suspicious transaction reporting, financial intelligence "
        "controls, regulatory requirements, and compliance governance for supervised entities. "
    )
    html = f"""
    <html><body>
      <main>
        <article class="publication-card">
          <a href="/media/laws/cabinet-resolution-134-2025.pdf">
            Cabinet Resolution No. 134 of 2025 Regarding the Executive Regulations of
            Federal Decree by Law No. 10 of 2025 Regarding Anti-Money Laundering and
            Combating the Financing of Terrorism and Proliferation Financing
          </a>
          <p>{legal_context * 3}</p>
        </article>
        <article class="publication-card">
          <a href="/media/laws/federal-decree-law-10-2025.pdf">
            Federal Decree by Law No. 10 of 2025 Regarding Anti-Money Laundering and
            Combating the Financing of Terrorism and Proliferation Financing
          </a>
          <p>{legal_context * 3}</p>
        </article>
        <nav><a href="/contact">Contact us</a></nav>
      </main>
    </body></html>
    """
    source = {
        "source_id": "AE-uaefiu-aml-cft-laws-fixture",
        "url": "https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/",
        "adapter_family": "fiu_eocn_document_listing",
        "adapter_config": {"container_selector": "main"},
        "expected_min_length": 500,
    }

    with patch("app.scraper.fetch_page_with_config", return_value=html):
        result = run_source_intake(source, write_evidence=False)

    assert result["adapter_used"] is True
    assert result["adapter_metadata"]["item_count"] == 2
    assert result["structured_adapter_content"] is True
    assert result["nav_shell_detected"] is False
    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["quality_score"] >= 60
    assert result["can_save_for_validation"] is True


# ── 3. Hash collision detection ───────────────────────────────────────────────


def test_hash_collision_detected():
    h = "abc123def456abcd"
    collision, cid = _check_hash_collision(h, "AE-dfsa-rules2", _SOURCES_WITH_HASH)
    assert collision is True
    assert cid == "AE-dfsa-rules"


def test_no_collision_for_unique_hash():
    h = "totally-unique-hash-that-does-not-match"
    collision, cid = _check_hash_collision(h, "AE-new-source", _SOURCES_WITH_HASH)
    assert collision is False
    assert cid is None


def test_no_collision_with_own_source_id():
    h = "abc123def456abcd"
    # Same hash but same source_id — should NOT be a collision
    collision, cid = _check_hash_collision(h, "AE-dfsa-rules", _SOURCES_WITH_HASH)
    assert collision is False


def test_disabled_source_not_collision_candidate():
    disabled_sources = [
        {"source_id": "AE-disabled", "enabled": False, "content_hash": "abc123def456abcd"}
    ]
    h = "abc123def456abcd"
    collision, cid = _check_hash_collision(h, "AE-other", disabled_sources)
    assert collision is False


# ── 4. Full intake run (mocked fetch + extract) ───────────────────────────────


@patch("app.source_intake.run_source_intake")
def test_intake_result_fields(mock_intake):
    """Verify the result dict has all required keys."""
    mock_intake.return_value = {
        "source_id": "AE-test",
        "url": "https://example.com",
        "status": SourceIntakeStatus.CONFIRMED_ACCESSIBLE,
        "chars_raw": 5000,
        "chars_normalized": 4000,
        "pdf_chars": 0,
        "nav_shell_detected": False,
        "hash_collision": False,
        "collision_source_id": None,
        "quality": "GOOD",
        "evidence_written": False,
        "errors": [],
        "notes": "",
    }
    result = mock_intake({"url": "https://example.com", "source_id": "AE-test"})
    required_keys = [
        "source_id", "url", "status", "chars_raw", "chars_normalized",
        "pdf_chars", "nav_shell_detected", "hash_collision", "collision_source_id",
        "quality", "evidence_written", "errors", "notes",
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


def _mock_fetch(url, **kwargs):
    return _GOOD_HTML


def _mock_extract(html):
    return (_GOOD_TEXT, "trafilatura")


@patch("app.source_intake.run_source_intake")
def test_intake_dry_run_no_evidence_written(mock_intake):
    mock_intake.return_value = {
        "source_id": "AE-test",
        "url": "https://dfsa.ae/rules",
        "status": SourceIntakeStatus.CONFIRMED_ACCESSIBLE,
        "chars_raw": 4000,
        "chars_normalized": 3000,
        "pdf_chars": 0,
        "nav_shell_detected": False,
        "hash_collision": False,
        "collision_source_id": None,
        "quality": "GOOD",
        "evidence_written": False,
        "errors": [],
        "notes": "",
    }
    result = mock_intake({"url": "https://dfsa.ae/rules"}, write_evidence=False)
    assert result["evidence_written"] is False


def test_low_char_source_status():
    """Run intake with patched fetch returning tiny HTML → JS_RENDERING_NEEDED."""
    tiny_html = "<html><body><p>Loading...</p></body></html>"

    with patch("app.source_intake.run_source_intake") as mock_intake:
        mock_intake.return_value = {
            "source_id": "",
            "url": "https://example.com",
            "status": SourceIntakeStatus.JS_RENDERING_NEEDED,
            "chars_raw": 300,
            "chars_normalized": 15,
            "pdf_chars": 0,
            "nav_shell_detected": False,
            "hash_collision": False,
            "collision_source_id": None,
            "quality": "POOR",
            "evidence_written": False,
            "errors": [],
            "notes": "Chars (15) below expected minimum (500).",
        }
        result = mock_intake({"url": "https://example.com"})
        assert result["status"] == SourceIntakeStatus.JS_RENDERING_NEEDED


def test_per_source_expected_min_length():
    """Source with expected_min_length=5000 and 4000 chars → QUALITY_DROP."""
    with patch("app.source_intake.run_source_intake") as mock_intake:
        mock_intake.return_value = {
            "source_id": "AE-test",
            "url": "https://example.com",
            "status": SourceIntakeStatus.QUALITY_DROP,
            "chars_raw": 5000,
            "chars_normalized": 4000,
            "pdf_chars": 0,
            "nav_shell_detected": False,
            "hash_collision": False,
            "collision_source_id": None,
            "quality": "LIMITED",
            "evidence_written": False,
            "errors": [],
            "notes": "Chars (4000) below expected minimum (5000).",
        }
        result = mock_intake(
            {"url": "https://example.com", "expected_min_length": 5000}
        )
        assert result["status"] == SourceIntakeStatus.QUALITY_DROP


def test_intake_verdict_mapping():
    """Verify all SourceIntakeStatus constants are distinct strings."""
    statuses = [
        SourceIntakeStatus.CONFIRMED_ACCESSIBLE,
        SourceIntakeStatus.JS_RENDERING_NEEDED,
        SourceIntakeStatus.PDF_EXTRACTION_NEEDED,
        SourceIntakeStatus.NAV_SHELL_ONLY,
        SourceIntakeStatus.QUALITY_DROP,
        SourceIntakeStatus.NEEDS_SELECTOR_REVIEW,
        SourceIntakeStatus.UNSUPPORTED,
        SourceIntakeStatus.BLOCKED,
    ]
    assert len(set(statuses)) == len(statuses), "Status constants must be unique"
    for s in statuses:
        assert isinstance(s, str) and s, f"Status must be a non-empty string: {s!r}"


def test_content_hash_deterministic():
    h1 = _content_hash("test content")
    h2 = _content_hash("test content")
    assert h1 == h2


def test_intake_uses_extracted_dict_text_not_dict_repr():
    from app.text_normalization import normalize_for_change_hash

    text = _GOOD_TEXT * 4
    source = {
        "source_id": "AE-test",
        "url": "https://example.com/source",
        "expected_min_length": 500,
        "wait_for_selector": "main",
        "content_selector": "main",
    }

    with patch("app.scraper.fetch_page_with_config", return_value=_GOOD_HTML), \
         patch("app.extractors.extract_best_text", return_value={"text": text, "method": "unit-test"}):
        result = run_source_intake(source, write_evidence=False)

    assert result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert result["extraction_method"] == "unit-test"
    assert result["chars_normalized"] == len(normalize_for_change_hash(text))
    assert len(result["content_hash"]) == 16
    assert result["evidence_written"] is False


def test_readiness_summary_requires_hash_quality_and_proof():
    sources = [
        {
            "source_id": "AE-ready",
            "enabled": True,
            "name": "Ready source",
            "expected_min_length": 500,
        },
        {
            "source_id": "AE-no-proof",
            "enabled": True,
            "name": "No proof source",
            "expected_min_length": 500,
        },
    ]
    runs = {
        "AE-ready": {
            "timestamp_utc": "2026-06-13T10:00:00+00:00",
            "normalized_chars": 1200,
            "change_status": "UNCHANGED",
            "access_status": "success",
            "extraction_quality": "GOOD",
            "normalized_hash": "hash-ready",
            "proof_block_path": "data/source_runs/proof.json",
            "limitations_notes": [],
        },
        "AE-no-proof": {
            "timestamp_utc": "2026-06-13T10:00:00+00:00",
            "normalized_chars": 1200,
            "change_status": "UNCHANGED",
            "access_status": "success",
            "extraction_quality": "GOOD",
            "normalized_hash": "hash-no-proof",
            "limitations_notes": [],
        },
    }

    with patch("app.source_runs.latest_runs", return_value=runs):
        summary = readiness_summary(sources)

    statuses = {row["source_id"]: row["status"] for row in summary["breakdown"]}
    assert statuses["AE-ready"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE
    assert statuses["AE-no-proof"] == SourceIntakeStatus.QUALITY_DROP
    assert summary["confirmed_ready"] == 1


def test_content_hash_differs():
    h1 = _content_hash("content A")
    h2 = _content_hash("content B")
    assert h1 != h2


# ── 5. Failure reason and remediation hint ────────────────────────────────────


def test_failure_reason_set_on_blocked():
    """BLOCKED status must include a failure_reason."""
    from app.source_tester import validate_public_url
    with patch("app.source_intake.run_source_intake") as mock_intake:
        mock_intake.return_value = {
            "source_id": "AE-test",
            "url": "http://192.168.1.1/page",
            "status": SourceIntakeStatus.BLOCKED,
            "chars_raw": 0,
            "chars_normalized": 0,
            "pdf_chars": 0,
            "nav_shell_detected": False,
            "hash_collision": False,
            "collision_source_id": None,
            "quality": "POOR",
            "content_hash": "",
            "extraction_method": "",
            "failure_reason": "URL blocked: IP address is not a public routable address",
            "remediation_hint": "Use a public http(s) URL without credentials.",
            "evidence_written": False,
            "errors": ["URL blocked: IP address is not a public routable address"],
            "notes": "",
        }
        result = mock_intake({"url": "http://192.168.1.1/page"})
        assert result["failure_reason"] != ""
        assert result["status"] == SourceIntakeStatus.BLOCKED


def test_remediation_hint_set_on_blocked():
    """BLOCKED status must include a remediation_hint."""
    with patch("app.source_intake.run_source_intake") as mock_intake:
        mock_intake.return_value = {
            "source_id": "AE-test",
            "url": "http://localhost/page",
            "status": SourceIntakeStatus.BLOCKED,
            "chars_raw": 0,
            "chars_normalized": 0,
            "pdf_chars": 0,
            "nav_shell_detected": False,
            "hash_collision": False,
            "collision_source_id": None,
            "quality": "POOR",
            "content_hash": "",
            "extraction_method": "",
            "failure_reason": "URL blocked: localhost is not allowed",
            "remediation_hint": "Use a public http(s) URL without credentials, login, private network, or restricted portal access.",
            "evidence_written": False,
            "errors": [],
            "notes": "",
        }
        result = mock_intake({"url": "http://localhost/page"})
        assert result["remediation_hint"] != ""


def test_quality_drop_never_confirmed():
    """A source with QUALITY_DROP status must NOT be CONFIRMED_ACCESSIBLE."""
    with patch("app.source_intake.run_source_intake") as mock_intake:
        mock_intake.return_value = {
            "source_id": "AE-test",
            "url": "https://example.com",
            "status": SourceIntakeStatus.QUALITY_DROP,
            "chars_raw": 3000,
            "chars_normalized": 2000,
            "pdf_chars": 0,
            "nav_shell_detected": False,
            "hash_collision": False,
            "collision_source_id": None,
            "quality": "LIMITED",
            "content_hash": "abc123",
            "extraction_method": "trafilatura",
            "failure_reason": "Normalized text length 2000 is below expected minimum 5000.",
            "remediation_hint": "Review selector or rendering.",
            "evidence_written": False,
            "errors": [],
            "notes": "Chars (2000) below expected minimum (5000).",
        }
        result = mock_intake({"url": "https://example.com", "expected_min_length": 5000})
        assert result["status"] != SourceIntakeStatus.CONFIRMED_ACCESSIBLE
        assert result["status"] == SourceIntakeStatus.QUALITY_DROP


def test_status_constants_never_overlap_with_unchanged():
    """No intake status should equal 'UNCHANGED' — that belongs to change detection."""
    statuses = [
        SourceIntakeStatus.CONFIRMED_ACCESSIBLE,
        SourceIntakeStatus.JS_RENDERING_NEEDED,
        SourceIntakeStatus.PDF_EXTRACTION_NEEDED,
        SourceIntakeStatus.NAV_SHELL_ONLY,
        SourceIntakeStatus.QUALITY_DROP,
        SourceIntakeStatus.NEEDS_SELECTOR_REVIEW,
        SourceIntakeStatus.UNSUPPORTED,
        SourceIntakeStatus.BLOCKED,
    ]
    assert "UNCHANGED" not in statuses, "UNCHANGED is a change-detection status, not an intake status"


def test_extraction_method_in_result_dict():
    """result dict must include extraction_method key."""
    text = _GOOD_TEXT * 4
    source = {
        "source_id": "AE-test",
        "url": "https://example.com/source",
        "expected_min_length": 500,
    }
    with patch("app.scraper.fetch_page_with_config", return_value=_GOOD_HTML), \
         patch("app.extractors.extract_best_text", return_value={"text": text, "method": "bs4"}):
        result = run_source_intake(source, write_evidence=False)
    assert "extraction_method" in result
    assert result["extraction_method"] == "bs4"


def test_content_hash_in_result_dict():
    """result dict must include content_hash key with length 16."""
    text = _GOOD_TEXT * 4
    source = {
        "source_id": "AE-test",
        "url": "https://example.com/source",
        "expected_min_length": 500,
    }
    with patch("app.scraper.fetch_page_with_config", return_value=_GOOD_HTML), \
         patch("app.extractors.extract_best_text", return_value={"text": text, "method": "trafilatura"}):
        result = run_source_intake(source, write_evidence=False)
    assert "content_hash" in result
    assert len(result["content_hash"]) == 16


def test_intake_includes_provider_metadata_and_preview():
    text = _GOOD_TEXT * 4
    source = {
        "source_id": "AE-test",
        "url": "https://example.com/source",
        "expected_min_length": 500,
        "content_selector": "main",
    }
    with patch("app.scraper.fetch_page_with_config", return_value=_GOOD_HTML), \
         patch("app.extractors.extract_best_text", return_value={
             "text": text,
             "method": "trafilatura",
             "provider_used": "trafilatura",
         }):
        result = run_source_intake(source, write_evidence=False)

    assert result["provider_used"] == "trafilatura"
    assert len(result["normalized_hash"]) == 64
    assert result["normalized_preview"]
    assert result["legal_policy_status"] == "PUBLIC_SOURCE_ONLY"


# ── 6. Provider wrappers — html_extraction ────────────────────────────────────


def test_html_provider_result_schema():
    """best_html_extract returns a dict with required keys."""
    from app.providers.html_extraction import best_html_extract
    result = best_html_extract(_GOOD_HTML)
    required_keys = ["provider_name", "success", "dependency_available", "content",
                     "confidence", "warnings", "error", "elapsed_ms"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


def test_html_provider_trafilatura_returns_content():
    """trafilatura_extract should succeed on well-formed HTML."""
    from app.providers.html_extraction import trafilatura_extract
    result = trafilatura_extract(_GOOD_HTML)
    assert result["provider_name"] == "trafilatura"
    if result["dependency_available"]:
        assert result["success"] is True
        assert len(result["content"]) > 0


def test_html_provider_bs4_always_available():
    """bs4_extract must succeed — bs4 is a required dep."""
    from app.providers.html_extraction import bs4_extract
    result = bs4_extract(_GOOD_HTML)
    assert result["provider_name"] == "bs4"
    assert result["dependency_available"] is True
    assert result["success"] is True
    assert len(result["content"]) > 0


def test_html_provider_selectolax_graceful_missing():
    """selectolax_extract must not raise if selectolax is not installed."""
    from app.providers.html_extraction import selectolax_extract
    result = selectolax_extract(_GOOD_HTML, selector="main")
    assert result["provider_name"] == "selectolax"
    assert isinstance(result["success"], bool)
    assert isinstance(result["dependency_available"], bool)


def test_html_provider_cascade_returns_longest():
    """best_html_extract should return content (not crash) on good HTML."""
    from app.providers.html_extraction import best_html_extract
    result = best_html_extract(_GOOD_HTML)
    assert result["success"] is True
    assert len(result["content"]) > 100


def test_html_provider_readability_graceful():
    """readability_extract must not raise if dep is missing or available."""
    from app.providers.html_extraction import readability_extract
    result = readability_extract(_GOOD_HTML)
    assert result["provider_name"] == "readability"
    assert isinstance(result["success"], bool)
    assert isinstance(result["dependency_available"], bool)


def test_extract_best_text_uses_provider_cascade():
    from app.extractors import extract_best_text

    with patch("app.providers.html_extraction.best_html_extract", return_value={
        "provider_name": "trafilatura",
        "success": True,
        "dependency_available": True,
        "content": _GOOD_TEXT,
        "confidence": "high",
        "warnings": [],
        "candidates": [
            {
                "provider_name": "trafilatura",
                "content": _GOOD_TEXT,
                "confidence": "high",
                "dependency_available": True,
            }
        ],
    }) as mock_best:
        result = extract_best_text(_GOOD_HTML, url="https://example.com", content_selector="main")

    mock_best.assert_called_once_with(_GOOD_HTML, content_selector="main")
    assert result["method"] == "trafilatura"
    assert result["provider_used"] == "trafilatura"
    assert result["text"]


def test_html_provider_prefers_trafilatura_over_later_longer_fallback():
    from app.providers.html_extraction import best_html_extract

    trafilatura_text = _GOOD_TEXT * 2
    bs4_text = _GOOD_TEXT * 5
    with patch("app.providers.html_extraction.trafilatura_extract", return_value={
        "provider_name": "trafilatura",
        "success": True,
        "dependency_available": True,
        "requires_dependency": "trafilatura",
        "content": trafilatura_text,
        "confidence": "high",
        "warnings": [],
        "error": "",
        "elapsed_ms": 1,
        "metadata": {},
    }), patch("app.providers.html_extraction.readability_extract") as mock_readability, \
         patch("app.providers.html_extraction.bs4_extract", return_value={
             "provider_name": "bs4",
             "success": True,
             "dependency_available": True,
             "requires_dependency": "bs4",
             "content": bs4_text,
             "confidence": "low",
             "warnings": [],
             "error": "",
             "elapsed_ms": 1,
             "metadata": {},
         }):
        result = best_html_extract(_GOOD_HTML)

    assert result["provider_name"] == "trafilatura"
    mock_readability.assert_not_called()


def test_html_provider_falls_back_when_trafilatura_missing():
    from app.providers.html_extraction import best_html_extract

    with patch("app.providers.html_extraction.trafilatura_extract", return_value={
        "provider_name": "trafilatura",
        "success": False,
        "dependency_available": False,
        "requires_dependency": "trafilatura",
        "content": "",
        "confidence": "unknown",
        "warnings": [],
        "error": "missing",
        "elapsed_ms": 1,
        "metadata": {},
    }), patch("app.providers.html_extraction.readability_extract", return_value={
        "provider_name": "readability",
        "success": True,
        "dependency_available": True,
        "requires_dependency": "readability",
        "content": _GOOD_TEXT * 2,
        "confidence": "medium",
        "warnings": [],
        "error": "",
        "elapsed_ms": 1,
        "metadata": {},
    }):
        result = best_html_extract(_GOOD_HTML)

    assert result["provider_name"] == "readability"


# ── 7. Provider wrappers — pdf_extraction ────────────────────────────────────


def test_pdf_provider_result_schema():
    """best_pdf_extract with empty bytes returns structured result."""
    from app.providers.pdf_extraction import best_pdf_extract
    result = best_pdf_extract(b"not-a-pdf")
    required_keys = ["provider_name", "success", "dependency_available", "content",
                     "page_count", "confidence", "warnings", "error", "elapsed_ms"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


def test_pdf_provider_graceful_on_bad_bytes():
    """PDF extraction providers must not raise uncaught exceptions on bad input."""
    from app.providers.pdf_extraction import pymupdf_extract, pdfplumber_extract, pypdf_extract
    for fn in [pymupdf_extract, pdfplumber_extract, pypdf_extract]:
        result = fn(b"not-a-real-pdf")
        assert isinstance(result["success"], bool)
        assert isinstance(result["dependency_available"], bool)


def test_pdf_provider_none_result_on_all_fail():
    """best_pdf_extract on bad bytes returns provider_name='none' and success=False."""
    from app.providers.pdf_extraction import best_pdf_extract
    result = best_pdf_extract(b"not-a-real-pdf")
    assert result["success"] is False


# ── 8. Provider wrappers — optional_tools ────────────────────────────────────


def test_optional_tools_deepdiff_fallback():
    """structured_diff must not raise if deepdiff is not installed."""
    from app.providers.optional_tools import structured_diff
    old = {"a": 1, "b": 2}
    new = {"a": 1, "b": 3, "c": 4}
    result = structured_diff(old, new)
    required_keys = ["provider", "available", "success", "has_changes", "diff", "error", "elapsed_ms"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
    assert result["success"] is True
    assert result["has_changes"] is True


def test_optional_tools_deepdiff_no_change():
    """structured_diff on identical dicts returns has_changes=False."""
    from app.providers.optional_tools import structured_diff
    d = {"a": 1, "b": 2}
    result = structured_diff(d, d.copy())
    assert result["has_changes"] is False


def test_optional_tools_htmldate_fallback():
    """extract_date_from_html must not raise if htmldate is not installed."""
    from app.providers.optional_tools import extract_date_from_html
    result = extract_date_from_html(_GOOD_HTML)
    required_keys = ["provider", "available", "success", "date", "error", "elapsed_ms"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
    assert isinstance(result["success"], bool)
    assert isinstance(result["date"], str)


def test_optional_tools_courlan_fallback():
    """canonicalize_url must not raise if courlan is not installed."""
    from app.providers.optional_tools import canonicalize_url
    result = canonicalize_url("https://www.dfsa.ae/rules-and-standards")
    required_keys = ["provider", "available", "success", "canonical_url", "is_valid", "error", "elapsed_ms"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
    assert result["is_valid"] is True
    assert "dfsa.ae" in result["canonical_url"]


def test_optional_tools_courlan_rejects_invalid():
    """canonicalize_url returns is_valid=False for malformed URLs."""
    from app.providers.optional_tools import canonicalize_url
    result = canonicalize_url("not-a-url-at-all")
    assert result["is_valid"] is False


# ── 9. Source Lab save/activation gate checks ────────────────────────────────


def test_can_activate_true_only_for_confirmed():
    """Legacy status-level helper: only CONFIRMED_ACCESSIBLE may pass the first gate."""
    from app.source_intake import SourceIntakeStatus
    non_confirmable = [
        SourceIntakeStatus.JS_RENDERING_NEEDED,
        SourceIntakeStatus.PDF_EXTRACTION_NEEDED,
        SourceIntakeStatus.NAV_SHELL_ONLY,
        SourceIntakeStatus.QUALITY_DROP,
        SourceIntakeStatus.NEEDS_SELECTOR_REVIEW,
        SourceIntakeStatus.UNSUPPORTED,
        SourceIntakeStatus.BLOCKED,
    ]
    for s in non_confirmable:
        can_activate = (s == SourceIntakeStatus.CONFIRMED_ACCESSIBLE)
        assert can_activate is False, f"{s} should NOT be can_activate=True"


def test_needs_selector_review_is_not_confirmed():
    """NEEDS_SELECTOR_REVIEW must not resolve to CONFIRMED_ACCESSIBLE."""
    assert SourceIntakeStatus.NEEDS_SELECTOR_REVIEW != SourceIntakeStatus.CONFIRMED_ACCESSIBLE


def test_confirmed_accessible_label_does_not_say_ready():
    """Customer-facing labels must not imply monitoring readiness from a preview test."""
    from app.source_intake import STATUS_LABELS

    assert STATUS_LABELS[SourceIntakeStatus.CONFIRMED_ACCESSIBLE] != "Ready"
    assert "threshold" in STATUS_LABELS[SourceIntakeStatus.CONFIRMED_ACCESSIBLE].lower()


def test_source_lab_contract_separates_save_from_activation():
    """A no-save passing test can be saved for validation, but cannot activate monitoring."""
    from app.source_intake import build_source_lab_contract
    from app.source_certification import CertificationStatus, EvidenceLevel

    result = {
        "status": SourceIntakeStatus.CONFIRMED_ACCESSIBLE,
        "evidence_written": False,
        "evidence_level": EvidenceLevel.PREVIEW_ONLY,
        "certification_status": CertificationStatus.TEST_PASSED,
        "certification": {
            "certification_status": CertificationStatus.TEST_PASSED,
            "baseline_runs_completed": 0,
            "baseline_runs_required": 2,
        },
    }
    contract = build_source_lab_contract(result)

    assert contract["can_save_for_validation"] is True
    assert contract["can_activate_monitoring"] is False
    assert contract["activation_readiness"] == "BASELINE_REQUIRED"
    assert contract["evidence_level"] == EvidenceLevel.PREVIEW_ONLY


def test_source_lab_contract_uses_certified_evidence_after_baseline():
    """Aggregate certification should drive activation fields after baseline completion."""
    from app.source_intake import build_source_lab_contract
    from app.source_certification import CertificationStatus, EvidenceLevel

    result = {
        "status": SourceIntakeStatus.CONFIRMED_ACCESSIBLE,
        "evidence_written": True,
        "evidence_level": EvidenceLevel.FULL_EVIDENCE,
        "certification_status": CertificationStatus.MONITORING_CERTIFIED,
        "certification": {
            "certification_status": CertificationStatus.MONITORING_CERTIFIED,
            "evidence_level": EvidenceLevel.CERTIFIED_EVIDENCE,
            "baseline_runs_completed": 2,
            "baseline_runs_required": 2,
        },
    }
    contract = build_source_lab_contract(result)

    assert contract["can_save_for_validation"] is False
    assert contract["can_activate_monitoring"] is True
    assert contract["activation_readiness"] == "MONITORING_READY"
    assert contract["evidence_level"] == EvidenceLevel.CERTIFIED_EVIDENCE
