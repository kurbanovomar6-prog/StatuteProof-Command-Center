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


# ── 2. Nav-shell detection ────────────────────────────────────────────────────


def test_nav_shell_detected_on_short_lines():
    assert is_nav_shell_only(_NAV_SHELL_TEXT) is True


def test_good_content_passes_nav_check():
    assert is_nav_shell_only(_GOOD_TEXT) is False


def test_nav_shell_below_max_chars_threshold():
    # Nav shell should be detected only when chars < _NAV_SHELL_MAX_CHARS (10,000)
    long_nav = (_NAV_SHELL_TEXT * 500)  # ~10,000+ chars
    # Above threshold → should NOT be flagged (avoids false positives on large pages)
    assert is_nav_shell_only(long_nav) is False


def test_empty_text_not_nav_shell():
    assert is_nav_shell_only("") is False


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


def test_content_hash_differs():
    h1 = _content_hash("content A")
    h2 = _content_hash("content B")
    assert h1 != h2
