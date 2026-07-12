"""Public, stateless evidence-record integrity verifier.

This module backs the no-login ``POST /api/verify`` endpoint and the public
Verify page. It is the trust cornerstone described in
``docs/EVIDENCE-VERIFICATION-SPEC.md``: **anyone** can confirm the integrity of a
StatuteProof evidence record using only standard SHA-256 over the bytes THEY
hold — without a StatuteProof account and without trusting StatuteProof.

Design constraints (deliberate, non-negotiable):

* **Pure functions.** No filesystem access, no evidence-store reads, no
  database, no network, no auth, no PII. Everything operates ONLY on the
  caller-submitted ``record`` / ``raw`` / ``normalized`` data. That is the whole
  point of the moat: we verify what the USER holds, never what our server holds.
* **Fail-closed.** Malformed input yields a ``fail`` / ``skipped`` check, never
  an exception to the caller. :func:`verify_submission` never raises.
* **Real code paths, not reinvented math.** ``record_hash`` self-consistency
  reuses the product's genuine hashing functions — never a hand-rolled digest.
  The trail record uses ``app.source_runs.compute_record_hash`` (the same function
  ``tools/verify_evidence_trail.py`` uses); the canonical evidence record uses the
  shared ``app.record_hashing.canonical_record_hash`` (the SAME function its writer
  seals with). Normalization reproducibility reuses
  ``app.text_normalization.normalize_for_change_hash``.

Record-shape note: two genuine record shapes exist in the product and both are
fully self-checkable here.

* The **source-run trail record** (``data/source_runs/source_runs.jsonl`` — the
  shape the open spec §2 describes) carries bare-hex ``raw_hash`` /
  ``normalized_hash`` / ``content_hash`` / ``record_hash`` / ``prev_record_hash``
  and is self-checkable, including ``record_hash`` via ``compute_record_hash``.
* The **canonical ``evidence-record.json``** (``evidence/.../evidence-record.json``
  — the object shipped inside every Evidence Pack) carries ``sha256:``-prefixed
  ``content.current_hash`` / ``content.previous_hash`` / ``content.raw_hash`` plus a
  top-level ``record_hash`` and ``record_hash_method: content-sha256-v1``. For it,
  ``record_hash_self_consistent`` recomputes ``canonical_record_hash(content)`` and
  ``raw_bytes_match`` matches a submitted ``raw.txt`` against ``content.raw_hash``;
  all checks are genuine. A legacy canonical record predating this seal (no
  ``record_hash``) still verifies its normalized bytes and simply reports
  ``skipped`` for the self-seal — never ``fail``.

Hashes are accepted both bare and ``sha256:``-prefixed, and are always compared
as the bare 64-char lowercase digest (the spec mandates lowercase hex).
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.record_hashing import RECORD_HASH_METHOD, canonical_record_hash
from app.source_runs import compute_record_hash
from app.text_normalization import normalize_for_change_hash

# ── check outcome vocabulary ────────────────────────────────────────────────────
STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_SKIPPED = "skipped"

# Stable, published identifier for the open spec (docs/EVIDENCE-VERIFICATION-SPEC.md).
SPEC_URL = "/verify-spec"

DISCLAIMER = (
    "Verification confirms the integrity of the submitted record only. "
    "Monitoring information only. Not legal advice."
)

# A SHA-256 digest as bare lowercase hex. The canonical evidence-record.json
# stores prefixed hashes (``content.current_hash = "sha256:<hex>"``); the
# source-run trail record stores the same digests bare. Both are accepted; the
# spec mandates lowercase hex, so uppercase never validates.
_SHA256_HEX = re.compile(r"^[a-f0-9]{64}$")
_SHA256_PREFIX = "sha256:"

# The five named hashes the spec (§2) defines, resolved from whichever shape the
# caller pasted. Order of candidate paths is most-specific first.
_HASH_PATHS: dict[str, tuple[tuple[str, ...], ...]] = {
    "current_hash": (("content", "current_hash"), ("current_hash",), ("normalized_hash",)),
    "raw_hash": (("content", "raw_hash"), ("raw_hash",)),
    "previous_hash": (("content", "previous_hash"), ("previous_hash",)),
    "record_hash": (("record_hash",),),
    "prev_record_hash": (("prev_record_hash",),),
}


def verify_submission(
    record: Any,
    *,
    raw: str | None = None,
    normalized: str | None = None,
    timestamp_token: str | None = None,
    timestamp_digest: str | None = None,
) -> dict[str, Any]:
    """Verify a caller-submitted evidence record against the open spec.

    Returns the public response envelope; never raises. ``verified`` is true when
    no check failed and at least one check passed (an all-skipped result — e.g. a
    blob with no hashes — is never reported as verified).

    ``timestamp_token`` (optional) lets a caller ALSO submit an external RFC 3161
    timestamp token. When present, the response gains an additive ``external_timestamp``
    block reporting the token's own offline verification (see
    :mod:`app.rfc3161_anchor`) against the digest it should attest — the explicit
    ``timestamp_digest`` if given, else the record's ``record_hash``. This is purely
    additive: it NEVER changes the record-integrity ``verified`` gate, and its
    absence is silent (no block, no failure).
    """
    try:
        is_obj = isinstance(record, dict)
        hashes = _extract_hashes(record) if is_obj else dict.fromkeys(_HASH_PATHS, None)

        checks = [
            _guard(_check_record_is_object, record),
            _guard(_check_hash_formats, hashes, is_obj),
            _guard(_check_record_hash_self_consistent, record, hashes, is_obj),
            _guard(_check_raw_bytes, hashes, raw),
            _guard(_check_normalized_bytes, hashes, normalized),
            _guard(_check_normalization_reproducible, raw, normalized),
        ]

        failed = any(c["status"] == STATUS_FAIL for c in checks)
        passed = any(c["status"] == STATUS_PASS for c in checks)
        verified = (not failed) and passed

        response = {
            "ok": True,
            "verified": verified,
            "checks": checks,
            "spec_url": SPEC_URL,
            "disclaimer": DISCLAIMER,
        }
        if timestamp_token:
            response["external_timestamp"] = _external_timestamp_report(
                timestamp_token, timestamp_digest, hashes
            )
        return response
    except Exception:  # absolute fail-closed backstop — never leak a stacktrace
        return {
            "ok": True,
            "verified": False,
            "checks": [
                _fail(
                    "internal_error",
                    "Verification could not be completed for the submitted input.",
                )
            ],
            "spec_url": SPEC_URL,
            "disclaimer": DISCLAIMER,
        }


# ── individual checks ───────────────────────────────────────────────────────────

def _check_record_is_object(record: Any) -> dict[str, str]:
    name = "record_is_object"
    if not isinstance(record, dict):
        return _fail(name, "The submitted record is not a JSON object.")
    hashes = _extract_hashes(record)
    # The canonical shape always carries at least a normalized/current content
    # hash OR a record_hash. A blob with none of these is not a StatuteProof
    # evidence record — say so rather than pretend to verify nothing.
    if not (hashes["current_hash"] or hashes["record_hash"]):
        return _fail(
            name,
            "The record has no current_hash/normalized_hash or record_hash; "
            "it is not a StatuteProof evidence record.",
        )
    return _pass(name, "The submitted record is a JSON object of the expected shape.")


def _check_hash_formats(hashes: dict[str, str | None], is_obj: bool) -> dict[str, str]:
    name = "hash_formats"
    if not is_obj:
        return _fail(name, "No record object to read hashes from.")
    present = {key: value for key, value in hashes.items() if value}
    if not present:
        return _fail(name, "The record carries no SHA-256 hash fields to check.")
    bad = sorted(key for key, value in present.items() if _bare_digest(value) is None)
    if bad:
        return _fail(
            name,
            "Not a valid sha256:<64 lowercase hex> value: " + ", ".join(bad) + ".",
        )
    return _pass(
        name,
        "All present hash fields are valid sha256:<64 lowercase hex>: "
        + ", ".join(sorted(present))
        + ".",
    )


def _check_record_hash_self_consistent(
    record: Any,
    hashes: dict[str, str | None],
    is_obj: bool,
) -> dict[str, str]:
    name = "record_hash_self_consistent"
    if not is_obj:
        return _skip(name, "No record object to recompute.")
    stored = hashes["record_hash"]
    if not stored:
        return _skip(
            name,
            "The record carries no record_hash (e.g. a legacy record predating "
            "the content-sha256-v1 seal); nothing to self-check.",
        )
    stored_bare = _bare_digest(stored)
    if stored_bare is None:
        return _fail(name, "record_hash is not a valid sha256 digest.")

    # Branch on the sealed scheme so writer and verifier can never drift.
    #
    # Canonical evidence-record.json seals its OWN content block under the
    # published content-sha256-v1 scheme. Recompute through the SAME shared
    # function the writer used (app.record_hashing.canonical_record_hash) — never
    # reinvent the canonicalization.
    if record.get("record_hash_method") == RECORD_HASH_METHOD:
        content = record.get("content")
        if not isinstance(content, dict):
            return _fail(
                name,
                "record_hash_method is content-sha256-v1 but the record has no "
                "content block to recompute.",
            )
        if canonical_record_hash(content) == stored_bare:
            return _pass(
                name,
                "record_hash recomputes from the record's content block "
                "(content-sha256-v1).",
            )
        return _fail(
            name,
            "record_hash does not recompute from the record's content block — "
            "the record was altered.",
        )

    # Otherwise this is a source-run trail record: recompute over the record's OWN
    # prev_record_hash string exactly as the write side did
    # (source_runs._apply_chain_fields) and as the real trail verifier does
    # (tools/verify_evidence_trail.verify_chain). Reuse the product function.
    prev = record.get("prev_record_hash")
    prev = prev if isinstance(prev, str) else ""
    recomputed = compute_record_hash(record, prev)
    if recomputed.lower() == stored_bare:
        return _pass(
            name,
            "record_hash recomputes from the record's identifying fields.",
        )
    return _fail(
        name,
        "record_hash does not recompute from the record's fields — "
        "the record was altered.",
    )


def _check_raw_bytes(hashes: dict[str, str | None], raw: str | None) -> dict[str, str]:
    name = "raw_bytes_match"
    if raw is None:
        return _skip(name, "No raw.txt was submitted.")
    stored = hashes["raw_hash"]
    if not stored:
        return _skip(
            name,
            "The record carries no raw_hash to compare the submitted raw.txt against.",
        )
    stored_bare = _bare_digest(stored)
    if stored_bare is None:
        return _fail(name, "raw_hash is not a valid sha256 digest.")
    if _sha256_text(raw) == stored_bare:
        return _pass(name, "sha256(raw.txt) matches the record's raw_hash.")
    return _fail(name, "sha256(raw.txt) does not match the record's raw_hash.")


def _check_normalized_bytes(
    hashes: dict[str, str | None],
    normalized: str | None,
) -> dict[str, str]:
    name = "normalized_bytes_match"
    if normalized is None:
        return _skip(name, "No normalized.txt was submitted.")
    stored = hashes["current_hash"]
    if not stored:
        return _skip(
            name,
            "The record carries no current_hash/normalized_hash to compare the "
            "submitted normalized.txt against.",
        )
    stored_bare = _bare_digest(stored)
    if stored_bare is None:
        return _fail(name, "current_hash is not a valid sha256 digest.")
    if _sha256_text(normalized) == stored_bare:
        return _pass(name, "sha256(normalized.txt) matches the record's current_hash.")
    return _fail(name, "sha256(normalized.txt) does not match the record's current_hash.")


def _check_normalization_reproducible(
    raw: str | None,
    normalized: str | None,
) -> dict[str, str]:
    name = "normalization_reproducible"
    if raw is None or normalized is None:
        return _skip(
            name,
            "Both raw.txt and normalized.txt are required to re-derive normalization.",
        )
    if normalize_for_change_hash(raw) == normalized:
        return _pass(
            name,
            "normalize_for_change_hash(raw.txt) reproduces normalized.txt byte-for-byte.",
        )
    return _fail(
        name,
        "normalize_for_change_hash(raw.txt) does not reproduce the submitted normalized.txt.",
    )


# ── optional external RFC 3161 timestamp reporting (additive) ────────────────────

def _external_timestamp_report(
    timestamp_token: str,
    timestamp_digest: str | None,
    hashes: dict[str, str | None],
) -> dict[str, Any]:
    """Report an external RFC 3161 timestamp token offline, best-effort.

    Additive only — the caller never folds this into the record-integrity
    ``verified`` gate. Verifies the token against the digest it should attest: the
    explicit ``timestamp_digest`` when given, else the record's own ``record_hash``.
    Never raises. When the optional anchor dependency is unavailable, the token's
    own report degrades to ``skipped`` checks rather than a hard failure.
    """
    digest = _bare_digest(timestamp_digest) if timestamp_digest else _bare_digest(hashes.get("record_hash"))
    if not digest:
        return {
            "present": True,
            "verified": False,
            "detail": (
                "No record_hash (or explicit timestamp_digest) available to match the "
                "timestamp token against."
            ),
        }
    try:
        from app.rfc3161_anchor import verify_timestamp_token

        report = verify_timestamp_token(str(timestamp_token), digest)
    except Exception:
        return {"present": True, "verified": False, "detail": "Timestamp token could not be evaluated."}
    report["present"] = True
    report["checked_digest"] = digest
    return report


# ── helpers ─────────────────────────────────────────────────────────────────────

def _guard(fn, *args) -> dict[str, str]:
    """Run one check; convert any unexpected error into a fail (never propagate)."""
    try:
        return fn(*args)
    except Exception:
        return _fail(getattr(fn, "__name__", "check").removeprefix("_check_"),
                     "This check could not be evaluated for the submitted input.")


def _extract_hashes(record: dict[str, Any]) -> dict[str, str | None]:
    return {key: _first_str(record, paths) for key, paths in _HASH_PATHS.items()}


def _first_str(record: dict[str, Any], paths: tuple[tuple[str, ...], ...]) -> str | None:
    """First non-empty string found at one of the dotted ``paths``, else None."""
    for path in paths:
        current: Any = record
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                current = None
                break
        if isinstance(current, str) and current.strip():
            return current.strip()
    return None


def _bare_digest(value: Any) -> str | None:
    """Return the bare 64-char lowercase hex digest, or None if malformed.

    Strips an optional ``sha256:`` prefix (case-insensitive on the prefix only);
    the digest itself must be lowercase hex, matching the spec.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.lower().startswith(_SHA256_PREFIX):
        text = text[len(_SHA256_PREFIX):]
    return text if _SHA256_HEX.match(text) else None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pass(name: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": STATUS_PASS, "detail": detail}


def _fail(name: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": STATUS_FAIL, "detail": detail}


def _skip(name: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": STATUS_SKIPPED, "detail": detail}
