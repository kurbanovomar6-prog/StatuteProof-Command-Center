"""
Tests for source quality policy warning detection.

These tests use local text/HTML only. They do not make live network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.source_quality import build_quality_score, detect_policy_warnings


def test_policy_warnings_do_not_block_public_page_with_login_chrome():
    text = (
        "Anti-Money Laundering and Terrorist Financing guidance for regulated firms. "
        "The authority publishes regulations, notices, AML controls, sanctions screening "
        "requirements, reporting procedures, and compliance guidance. "
    ) * 20
    html = """
    <html><body>
      <nav><a href="/login">Login</a></nav>
      <main><p>Anti-Money Laundering and Terrorist Financing guidance for regulated firms.</p></main>
      <script src="/assets/recaptcha-loader.js"></script>
    </body></html>
    """

    assert detect_policy_warnings(text, html) == []


def test_policy_warnings_detect_real_password_login_form():
    text = "Log in Username Password"
    html = """
    <html><body>
      <form action="/login">
        <input name="username" />
        <input type="password" name="password" />
      </form>
    </body></html>
    """

    assert "login" in detect_policy_warnings(text, html)


def test_policy_warnings_detect_visible_captcha_wall():
    text = "Please verify you are human before continuing."
    html = "<html><body>Please verify you are human before continuing.</body></html>"

    assert "captcha" in detect_policy_warnings(text, html)


def test_aml_typology_language_counts_as_regulatory_density():
    text = (
        "UAE FIU typology report on anti money laundering, terrorist financing, "
        "proliferation financing, sanctions evasion, suspicious transaction reporting, "
        "national risk assessment, financial intelligence, and compliance controls. "
    ) * 20

    report = build_quality_score(
        url="https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/",
        fetch_success=True,
        normalized_text=text,
        normalized_hash="a" * 64,
        canonical_url="https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/",
        provider_confidence="explicit_adapter",
    )

    assert report["components"]["regulatory_content_density"] >= 5


def test_fiu_typology_listing_titles_count_as_regulatory_density():
    text = "\n".join(
        [
            "FIU/EOCN document listing items",
            "Environmental Crime Typologies",
            "Financing of terrorism typologies and risk indicators",
            "Money laundering through dealers in precious metals and stones",
            "National risk assessment report",
            "Suspicious transaction reporting indicators",
        ]
        * 10
    )

    report = build_quality_score(
        url="https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/",
        fetch_success=True,
        normalized_text=text,
        normalized_hash="a" * 64,
        canonical_url="https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/",
        provider_confidence="explicit_adapter",
    )

    assert report["components"]["regulatory_content_density"] >= 5


def test_virtual_asset_and_capital_market_language_counts_as_regulatory_density():
    text = (
        "VARA rulebook requirements for virtual asset service providers, "
        "licensed activities, custody services, exchange services, advisory services, "
        "market conduct, client asset safeguards, securities markets, commodities "
        "markets, public joint stock companies, prospectus disclosures, and issuer "
        "obligations. "
    ) * 20

    report = build_quality_score(
        url="https://rulebooks.vara.ae/rulebook/virtual-assets-and-related-activities-regulations-2023",
        fetch_success=True,
        normalized_text=text,
        normalized_hash="a" * 64,
        canonical_url="https://rulebooks.vara.ae/rulebook/virtual-assets-and-related-activities-regulations-2023",
        provider_confidence="explicit_adapter",
    )

    assert report["components"]["regulatory_content_density"] >= 5


def test_virtual_asset_marketing_guidance_language_counts_as_regulatory_density():
    text = (
        "VARA marketing guidance for virtual asset services, promotions, "
        "advertisements, client communications, token issuance, exchange services, "
        "custody services, advisory services, virtual asset service providers, "
        "market conduct, administrative orders, investor protection, risk warnings, "
        "and disclosure obligations. "
    ) * 20

    report = build_quality_score(
        url="https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_388_VER1.pdf",
        fetch_success=True,
        normalized_text=text,
        normalized_hash="a" * 64,
        canonical_url="https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_388_VER1.pdf",
        provider_confidence="explicit_adapter",
    )

    assert report["components"]["regulatory_content_density"] >= 5


def test_company_auditor_and_economic_substance_language_counts_as_regulatory_density():
    text = (
        "Ministry of Economy legislation for companies, commercial agencies, "
        "auditors, auditing accounts, beneficial owner registers, economic "
        "substance regulations, competition controls, consumer protection, "
        "cooperative associations, corporate governance, and compliance "
        "obligations. "
    ) * 20

    report = build_quality_score(
        url="https://www.moet.gov.ae/companies-legislations",
        fetch_success=True,
        normalized_text=text,
        normalized_hash="a" * 64,
        canonical_url="https://www.moet.gov.ae/companies-legislations",
        provider_confidence="explicit_adapter",
    )

    assert report["components"]["regulatory_content_density"] >= 5
