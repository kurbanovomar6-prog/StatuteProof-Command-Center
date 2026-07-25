"""The public verifier must separate INTEGRITY from pipeline REPRODUCIBILITY.

Why this file exists
--------------------
``normalization_reproducible`` used to hard-gate ``verified``. It re-derives
normalize_for_change_hash(raw.txt) and compares it to the submitted
normalized.txt — a statement about the NORMALIZER, not about the evidence. Any
record sealed under an older normalizer legitimately fails it, so the public,
no-login /verify endpoint reported genuine untampered evidence as unverified.

Measured on the real store before the fix (tools/measure_evidence_axis.py):
41 of 143 sampled records verified; 79 of them failed ONLY this check while
passing BOTH hash seals. After the fix: 120 of 143, and the remaining 23 are
records that carry no hashes at all, which the verifier is right to reject.

The safety property these tests pin: loosening reproducibility must NOT loosen
tamper detection. Tampering with either artifact still breaks a hash seal, and
a record that DECLARES the current normalizer version is still held to it.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.public_verify import verify_submission  # noqa: E402
from app.text_normalization import (  # noqa: E402
    NORMALIZATION_VERSION,
    normalize_for_change_hash,
)

RAW = "Circular No. 7 of 2026\n\n   Applies to all licensed firms.\n\nEffective 1 August 2026.\n"


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _statuses(result: dict) -> dict[str, str]:
    return {check["name"]: check["status"] for check in result["checks"]}


def _record(normalized: str, **extra) -> dict:
    record = {"raw_hash": _sha(RAW), "current_hash": _sha(normalized)}
    record.update(extra)
    return record


# ── a record the CURRENT normalizer produced ────────────────────────────────


def test_current_version_record_reproduces_and_verifies():
    normalized = normalize_for_change_hash(RAW)
    result = verify_submission(
        _record(normalized, normalization_version=NORMALIZATION_VERSION),
        raw=RAW,
        normalized=normalized,
    )

    assert result["verified"] is True
    assert _statuses(result)["normalization_reproducible"] == "pass"


def test_a_record_declaring_the_current_version_is_still_held_to_it():
    """If the record says it was sealed under today's normalizer and today's
    normalizer does not reproduce it, that IS a real defect — keep failing."""
    normalized = "text that today's normalizer would never produce from RAW"
    result = verify_submission(
        _record(normalized, normalization_version=NORMALIZATION_VERSION),
        raw=RAW,
        normalized=normalized,
    )

    assert _statuses(result)["normalization_reproducible"] == "fail"
    assert result["verified"] is False


# ── legacy records: sealed before normalization was versioned ───────────────


def test_legacy_record_verifies_on_its_seals_alone():
    """All 1317 stored records carry no normalization_version. They cannot be
    re-derived, and the seals are what prove them."""
    normalized = "OLD normalizer output — collapses differently than v%d" % NORMALIZATION_VERSION
    result = verify_submission(_record(normalized), raw=RAW, normalized=normalized)

    statuses = _statuses(result)
    assert statuses["normalization_reproducible"] == "skipped"
    assert statuses["raw_bytes_match"] == "pass"
    assert statuses["normalized_bytes_match"] == "pass"
    assert result["verified"] is True


def test_the_skip_says_why_instead_of_going_quiet():
    """A silent skip would hide the limitation from the auditor reading this."""
    normalized = "OLD normalizer output"
    result = verify_submission(_record(normalized), raw=RAW, normalized=normalized)

    detail = next(
        c["detail"] for c in result["checks"] if c["name"] == "normalization_reproducible"
    )
    assert "no version" in detail
    assert f"v{NORMALIZATION_VERSION}" in detail
    assert "integrity" in detail.lower()


def test_a_record_from_an_older_declared_version_is_skipped_not_failed():
    normalized = "v1-era output"
    result = verify_submission(
        _record(normalized, normalization_version=1), raw=RAW, normalized=normalized
    )

    assert _statuses(result)["normalization_reproducible"] == "skipped"
    assert result["verified"] is True


# ── the safety property: tampering is still caught ──────────────────────────


def test_tampering_with_normalized_text_still_fails():
    """The whole point of the seals. Loosening reproducibility must not let a
    modified normalized.txt through."""
    normalized = normalize_for_change_hash(RAW)
    record = _record(normalized)  # seals the ORIGINAL bytes

    result = verify_submission(record, raw=RAW, normalized=normalized + " INSERTED")

    assert _statuses(result)["normalized_bytes_match"] == "fail"
    assert result["verified"] is False


def test_tampering_with_raw_text_still_fails():
    normalized = normalize_for_change_hash(RAW)
    record = _record(normalized)

    result = verify_submission(record, raw=RAW + "\nINSERTED CLAUSE", normalized=normalized)

    assert _statuses(result)["raw_bytes_match"] == "fail"
    assert result["verified"] is False


def test_a_blob_with_no_hashes_is_not_an_evidence_record():
    """23 of 143 stored artifacts carry null hashes. Rejecting them is correct;
    this pins that the fix did not quietly start accepting them."""
    result = verify_submission(
        {"normalized_hash": None, "raw_hash": None, "official_url": "https://x.example"},
        raw=RAW,
        normalized="whatever",
    )

    assert _statuses(result)["record_is_object"] == "fail"
    assert result["verified"] is False
