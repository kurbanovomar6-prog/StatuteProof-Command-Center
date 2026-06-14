"""
Tests for source quality policy warning detection.

These tests use local text/HTML only. They do not make live network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.source_quality import detect_policy_warnings


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
