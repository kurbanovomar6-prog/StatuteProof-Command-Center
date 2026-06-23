"""New coverage tests added 2026-06-22.

Three focused unit tests covering:
1. Telegram pairing code format (generate_pairing_code)
2. mask_chat_id masking logic
3. validate_email acceptance and rejection
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Ensure app package is importable when running from the tests/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.telegram_pairing import generate_pairing_code, mask_chat_id
from app.auth import validate_email


# ---------------------------------------------------------------------------
# Test 1: pairing code format
# ---------------------------------------------------------------------------

_CODE_RE = re.compile(r"^SP-[A-Z2-9]{6}$")


def test_generate_pairing_code_returns_sp_format():
    """generate_pairing_code must return a string matching SP-XXXXXX."""
    for _ in range(20):
        code = generate_pairing_code()
        assert _CODE_RE.match(code), f"Code {code!r} does not match SP-XXXXXX format"
        assert code.startswith("SP-")
        assert len(code) == 9  # "SP-" (3) + 6 chars


def test_generate_pairing_code_returns_distinct_values():
    """generate_pairing_code should produce distinct codes across calls."""
    codes = {generate_pairing_code() for _ in range(10)}
    # With a 32-symbol alphabet and 6 positions there are ~10^9 combos;
    # getting 10 identical codes from 10 draws is astronomically unlikely.
    assert len(codes) > 1, "generate_pairing_code returned identical codes for every call"


# ---------------------------------------------------------------------------
# Test 2: mask_chat_id masking
# ---------------------------------------------------------------------------

def test_mask_chat_id_masks_long_id():
    """Long chat IDs should be masked with **** prefix and last 4 digits exposed."""
    result = mask_chat_id("1234567890")
    assert result is not None
    # Last 4 digits must be visible
    assert result.endswith("7890"), f"Expected last 4 digits '7890', got {result!r}"
    # Everything before the last 4 must be asterisks
    prefix = result[:-4]
    assert all(c == "*" for c in prefix), f"Prefix should be all '*', got {prefix!r}"
    # Total length preserved
    assert len(result) == len("1234567890")


def test_mask_chat_id_returns_none_for_empty():
    """mask_chat_id should return None when given None or empty string."""
    assert mask_chat_id(None) is None
    assert mask_chat_id("") is None


def test_mask_chat_id_all_stars_for_short_id():
    """IDs of 4 chars or fewer should be entirely masked."""
    result = mask_chat_id("1234")
    assert result is not None
    assert all(c == "*" for c in result), f"Short ID should be all '*', got {result!r}"
    assert len(result) == 4


def test_mask_chat_id_minimum_four_star_prefix():
    """Prefix must be at least 4 asterisks for IDs longer than 4 chars.

    mask_chat_id uses max(4, len-4) stars followed by the last 4 chars,
    so a 6-char input produces '****' + last-4 = 8 chars total.
    """
    result = mask_chat_id("123456")  # 6 chars -> max(4, 6-4)=4 stars + last 4 digits
    assert result is not None
    assert result.endswith("3456"), f"Expected last 4 chars '3456', got {result!r}"
    prefix = result[:-4]
    assert len(prefix) >= 4
    assert all(c == "*" for c in prefix), f"Prefix should be all '*', got {prefix!r}"


# ---------------------------------------------------------------------------
# Test 3: validate_email
# ---------------------------------------------------------------------------

_VALID_EMAILS = [
    "user@example.com",
    "user.name+tag@subdomain.example.org",
    "USER@EXAMPLE.COM",           # validate_email normalises to lower-case
    "u@x.io",
]

_INVALID_EMAILS = [
    "",
    "not-an-email",
    "@nodomain.com",
    "noatsign.com",
    "spaces in@address.com",
    "missing@tld",
]


def test_validate_email_accepts_valid_addresses():
    """validate_email must return True for well-formed email addresses."""
    for email in _VALID_EMAILS:
        assert validate_email(email) is True, f"Expected True for {email!r}"


def test_validate_email_rejects_invalid_addresses():
    """validate_email must return False for malformed email addresses."""
    for email in _INVALID_EMAILS:
        assert validate_email(email) is False, f"Expected False for {email!r}"
