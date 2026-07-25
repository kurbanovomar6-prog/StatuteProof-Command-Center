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

from app.evidence_records import ATTRIBUTION_HASH_METHOD, attribution_seal_payload
from app.record_hashing import RECORD_HASH_METHOD, canonical_record_hash
from app.source_runs import compute_record_hash
from app.text_normalization import NORMALIZATION_VERSION, normalize_for_change_hash

# ── check outcome vocabulary ────────────────────────────────────────────────────
STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_SKIPPED = "skipped"

# ── sealed-scope vocabulary ─────────────────────────────────────────────────────
# What a passing verification actually PROVES about this record. ``record_hash``
# (content-sha256-v1) binds only the content bytes/paths + capture metadata; the
# attribution seal (attribution-sha256-v1) additionally binds the regulator, source
# name, change summary, line counts, run status, and review status a human auditor
# READS. A legacy record that predates the attribution seal cannot bind those fields,
# so its scope is honestly reported as limited rather than as an unqualified pass.
SCOPE_FULL = "content+attribution+capture-metadata"
SCOPE_LIMITED = "content+capture-metadata"
SCOPE_CONTENT = "content"

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
    # diff_hash seals the redline (diff.txt). Additive: legacy records predate it,
    # so a submission without it simply skips the diff_bytes_match check.
    "diff_hash": (("content", "diff_hash"), ("diff_hash",)),
    "record_hash": (("record_hash",),),
    "prev_record_hash": (("prev_record_hash",),),
    # content_hash is the coverage certificate's full-document self-seal
    # (``sha256:`` + canonical_record_hash(cert minus generated_at_utc/content_hash),
    # stamped by app.coverage_certificate). The source-run trail record ALSO carries
    # a top-level content_hash with different semantics (stable_content_hash of the
    # normalized bytes) — that one is only format-checked here; the certificate
    # recompute below fires ONLY for records the cert detector recognizes.
    "content_hash": (("content_hash",),),
}


def verify_submission(
    record: Any,
    *,
    raw: str | None = None,
    normalized: str | None = None,
    diff: str | None = None,
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
            _guard(_check_attribution_seal_consistent, record, is_obj),
            _guard(_check_certificate_content_hash_self_consistent, record, is_obj),
            _guard(_check_raw_bytes, hashes, raw),
            _guard(_check_normalized_bytes, hashes, normalized),
            _guard(_check_diff_bytes, hashes, diff),
            _guard(_check_capture_metadata_consistent, record, is_obj),
            _guard(_check_normalization_reproducible, raw, normalized, record, is_obj),
        ]

        failed = any(c["status"] == STATUS_FAIL for c in checks)
        passed = any(c["status"] == STATUS_PASS for c in checks)
        verified = (not failed) and passed

        response = {
            "ok": True,
            "verified": verified,
            # Qualify WHAT the pass covers, so a record that binds only its content
            # bytes is never presented as an unqualified verified:true over the
            # regulator/change-summary/status fields it does not seal.
            "verified_scope": _verified_scope(record, checks),
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
            "verified_scope": SCOPE_CONTENT,
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
    if _is_coverage_certificate(record):
        return _pass(name, "The submitted record is a coverage certificate of the expected shape.")
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


def _carries_forgeable_attribution(record: Any) -> bool:
    """True when a record carries the DISPLAY attribution/change/status fields.

    These are the fields a human auditor reads (regulator, source name, change
    summary, run status, review status). When present WITHOUT an attribution seal,
    they are forgeable, so the pass must be qualified as limited scope.
    """
    if not isinstance(record, dict):
        return False

    def _has(block: str, key: str) -> bool:
        value = record.get(block)
        return isinstance(value, dict) and bool(str(value.get(key) or "").strip())

    return (
        _has("source", "regulator")
        or _has("source", "source_name")
        or _has("run", "status")
        or _has("change", "summary")
        or _has("review", "review_status")
    )


def _check_attribution_seal_consistent(record: Any, is_obj: bool) -> dict[str, str]:
    """Recompute the full-record ``attribution_hash`` seal (attribution-sha256-v1).

    ``record_hash`` covers only ``content`` — the regulator, source name, change
    summary, line counts, run status, and review status a human auditor READS are
    outside it, so a holder of a genuine record could forge them (flip CBUAE→VARA,
    rewrite the change summary, mark a pending record "approved") with content and
    capture metadata untouched. Records sealed with ``attribution_hash`` bind those
    fields; recompute through the SAME shared payload builder the writer used and
    FAIL on any mismatch. A record without the seal (legacy, or a non-canonical
    shape) is not failed — it is reported as skipped, and :func:`_verified_scope`
    downgrades the pass to limited scope so it is never an unqualified pass over
    unsealed attribution fields.
    """
    name = "attribution_seal_consistent"
    if not is_obj:
        return _skip(name, "No record object to recompute.")
    stored = record.get("attribution_hash")
    # The attribution seal extends the content seal (its payload embeds the content
    # block), so it is authoritative only while record_hash is present. A record with
    # no content seal is legacy/downgraded — its attribution fields are unsealed, so
    # the pass is reported as limited scope rather than held to the attribution seal.
    has_content_seal = bool(isinstance(record.get("record_hash"), str) and record["record_hash"].strip())
    if not (isinstance(stored, str) and stored.strip() and has_content_seal):
        if _carries_forgeable_attribution(record):
            return _skip(
                name,
                "This record carries no attribution_hash: its regulator, source name, "
                "change summary, line counts, run status, and review status are DISPLAY "
                "fields NOT covered by this record's seal — only the content bytes and "
                "capture metadata are cryptographically bound.",
            )
        return _skip(
            name,
            "The record carries no attribution_hash (e.g. a legacy record predating "
            "the attribution-sha256-v1 seal); nothing to self-check.",
        )
    if record.get("attribution_hash_method") != ATTRIBUTION_HASH_METHOD:
        return _fail(
            name,
            "attribution_hash_method is not the supported attribution-sha256-v1 scheme.",
        )
    stored_bare = _bare_digest(stored)
    if stored_bare is None:
        return _fail(name, "attribution_hash is not a valid sha256 digest.")
    try:
        recomputed = canonical_record_hash(attribution_seal_payload(record))
    except (ValueError, TypeError):
        return _fail(
            name,
            "The record's attribution fields could not be canonically re-hashed "
            "(they contain a value that cannot be sealed).",
        )
    if recomputed == stored_bare:
        return _pass(
            name,
            "attribution_hash recomputes from the record's regulator, source name, "
            "change summary, line counts, run status, and review status.",
        )
    return _fail(
        name,
        "attribution_hash does not recompute from the record's attribution/change/status "
        "fields — the regulator, change summary, run status, or review status was altered.",
    )


def _verified_scope(record: Any, checks: list[dict[str, str]]) -> str:
    """Report WHAT a passing verification actually binds for this record.

    ``full`` when the attribution seal recomputes; ``content+capture-metadata`` when
    the record carries forgeable attribution fields but no attribution seal (so the
    pass must not be read as covering them); ``content`` otherwise.
    """
    attribution_passed = any(
        c["name"] == "attribution_seal_consistent" and c["status"] == STATUS_PASS
        for c in checks
    )
    if attribution_passed:
        return SCOPE_FULL
    if _carries_forgeable_attribution(record):
        return SCOPE_LIMITED
    return SCOPE_CONTENT


def _is_coverage_certificate(record: Any) -> bool:
    """True for a StatuteProof coverage certificate carrying a content_hash seal.

    A coverage certificate has no current_hash/record_hash — its full-document seal
    is the top-level ``content_hash``. Keyed on the certificate's own identity
    signals (``document_type`` or a ``cov-`` id) PLUS a string ``content_hash`` so
    the certificate recompute never fires on a source-run trail record, which also
    carries a top-level ``content_hash`` but with different (bytes-hash) semantics.
    """
    if not isinstance(record, dict):
        return False
    content_hash = record.get("content_hash")
    if not isinstance(content_hash, str) or not content_hash.strip():
        return False
    return (
        record.get("document_type") == "coverage_certificate"
        or str(record.get("certificate_id") or "").startswith("cov-")
    )


def _check_certificate_content_hash_self_consistent(record: Any, is_obj: bool) -> dict[str, str]:
    """Recompute the coverage certificate's full-document ``content_hash`` seal.

    Mirrors :func:`_check_record_hash_self_consistent` for the certificate shape:
    reproduce ``canonical_record_hash`` over the certificate MINUS ``generated_at_utc``
    and ``content_hash`` — exactly the subset app.coverage_certificate sealed — and
    compare. This is what catches an edit to the negative-assurance statement prose or
    a row's continuity_status/degraded flag that leaves ``certificate_id`` unchanged.
    Skips for any record that is not a sealed certificate (never a false failure).
    """
    name = "certificate_content_hash_self_consistent"
    if not is_obj:
        return _skip(name, "No record object to recompute.")
    if not _is_coverage_certificate(record):
        return _skip(
            name,
            "The record is not a sealed coverage certificate (no content_hash seal); "
            "nothing to self-check.",
        )
    stored_bare = _bare_digest(record.get("content_hash"))
    if stored_bare is None:
        return _fail(name, "content_hash is not a valid sha256 digest.")
    sealed = {
        key: value
        for key, value in record.items()
        if key not in ("generated_at_utc", "content_hash")
    }
    try:
        recomputed = canonical_record_hash(sealed)
    except (ValueError, TypeError):
        # A non-finite float (or otherwise non-serializable value) in a submitted,
        # tampered certificate — the genuine seal never contains one. Fail closed.
        return _fail(
            name,
            "The certificate content could not be canonically re-hashed "
            "(it contains a value that cannot be sealed).",
        )
    if recomputed == stored_bare:
        return _pass(
            name,
            "content_hash recomputes from the full certificate document.",
        )
    return _fail(
        name,
        "content_hash does not recompute from the certificate document — "
        "the certificate was altered.",
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


def _check_diff_bytes(hashes: dict[str, str | None], diff: str | None) -> dict[str, str]:
    """Verify a submitted diff.txt (the sealed redline) against the record's
    diff_hash. Additive: a record without diff_hash (legacy, or a non-CHANGED run
    with no diff) simply skips — never a failure."""
    name = "diff_bytes_match"
    if diff is None:
        return _skip(name, "No diff.txt was submitted.")
    stored = hashes["diff_hash"]
    if not stored:
        return _skip(
            name,
            "The record carries no diff_hash to compare the submitted diff.txt against.",
        )
    stored_bare = _bare_digest(stored)
    if stored_bare is None:
        return _fail(name, "diff_hash is not a valid sha256 digest.")
    if _sha256_text(diff) == stored_bare:
        return _pass(name, "sha256(diff.txt) matches the record's diff_hash.")
    return _fail(name, "sha256(diff.txt) does not match the record's diff_hash.")


def _check_capture_metadata_consistent(record: Any, is_obj: bool) -> dict[str, str]:
    """Cross-check the DISPLAY capture metadata (run.timestamp, source.official_url)
    against the SEALED copies (content.captured_at, content.source_url). The sealed
    copies are covered by record_hash, so this catches an edit to a display field
    that left the sealed value untouched. Additive: skips for records that predate
    the sealed fields."""
    name = "capture_metadata_consistent"
    if not is_obj:
        return _skip(name, "No record object to check.")
    content = record.get("content")
    content = content if isinstance(content, dict) else {}
    sealed_ts = content.get("captured_at")
    sealed_url = content.get("source_url")
    if sealed_ts is None and sealed_url is None:
        return _skip(name, "The record carries no sealed captured_at/source_url (legacy record).")
    run = record.get("run")
    run = run if isinstance(run, dict) else {}
    source = record.get("source")
    source = source if isinstance(source, dict) else {}
    mismatches: list[str] = []
    if sealed_ts is not None and "timestamp" in run and run.get("timestamp") != sealed_ts:
        mismatches.append("run.timestamp does not match the sealed content.captured_at")
    if sealed_url is not None and "official_url" in source and source.get("official_url") != sealed_url:
        mismatches.append("source.official_url does not match the sealed content.source_url")
    if mismatches:
        return _fail(name, "; ".join(mismatches))
    return _pass(name, "Displayed capture time and source URL match the sealed content values.")


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
    # EV-2: a trail record's normalized_hash comes in TWO flavors — the
    # newline-preserving sha256(normalized.txt) (intake/canonical records) OR
    # stable_content_hash(normalized.txt), which whitespace-collapses (the live
    # monitoring pipeline). normalized.txt IS normalize_for_change_hash(raw), so
    # stable_content_hash(normalized.txt) reproduces the pipeline flavor exactly.
    # Accept EITHER so a GENUINE live record verifies instead of falsely reporting
    # "altered". Verifier-side only; stored formats and the sealed hash are
    # untouched. A tampered normalized.txt matches neither flavor and still fails.
    candidates = {_sha256_text(normalized)}
    try:
        from app.text_normalization import stable_content_hash as _content_hash

        flavor_b = _content_hash(normalized)
        if flavor_b:
            candidates.add(flavor_b)
    except Exception:  # noqa: BLE001 — a normalization import failure just keeps flavor-A
        pass
    if stored_bare in candidates:
        return _pass(name, "sha256(normalized.txt) matches the record's current_hash.")
    return _fail(name, "sha256(normalized.txt) does not match the record's current_hash.")


def _check_normalization_reproducible(
    raw: str | None,
    normalized: str | None,
    record: Any = None,
    is_obj: bool = False,
) -> dict[str, str]:
    """Re-derive normalization from raw.txt — a PIPELINE check, not an integrity one.

    Integrity is proven by the seals: sha256(raw.txt) == raw_hash and
    sha256(normalized.txt) == current_hash. Those two are what make tampering
    detectable, and they are unaffected by anything here.

    This check answers a different question — "does today's normalizer reproduce
    the stored normalized.txt from the stored raw.txt" — and the answer is
    legitimately NO for any record sealed under an older normalizer. Measured on
    the real store (2026-07-25): 79 of 143 sampled records failed ONLY this check
    while passing BOTH hash seals, and the same raw.txt is on record producing
    51,148 / 43,717 / 42,173 normalized chars across normalizer generations. Hard-
    gating ``verified`` on it therefore reported genuine, untampered evidence as
    unverified — and the customer-facing /verify endpoint is exactly where that
    lands, in front of an auditor.

    So: a MISMATCH is only a real finding when the record declares the normalizer
    version we are re-deriving with. Records that declare nothing predate versioned
    normalization (all 1317 stored records at the time of writing) and cannot be
    re-derived at all; they are reported as skipped, with the reason said out loud
    rather than quietly dropped.
    """
    name = "normalization_reproducible"
    if raw is None or normalized is None:
        return _skip(
            name,
            "Both raw.txt and normalized.txt are required to re-derive normalization.",
        )
    if normalize_for_change_hash(raw) == normalized:
        return _pass(
            name,
            "normalize_for_change_hash(raw.txt) reproduces normalized.txt byte-for-byte "
            f"under normalization v{NORMALIZATION_VERSION}.",
        )

    declared = _declared_normalization_version(record) if is_obj else None
    if _declares_current_normalization(declared):
        return _fail(
            name,
            f"The record declares normalization v{declared}, but "
            "normalize_for_change_hash(raw.txt) does not reproduce the submitted "
            "normalized.txt. The normalizer is not reproducing its own output.",
        )
    stamped = f"v{declared}" if declared else "no version"
    return _skip(
        name,
        f"Not re-derivable: the record carries {stamped} and this verifier runs "
        f"normalization v{NORMALIZATION_VERSION}, so a byte-for-byte re-derivation "
        "is not expected. Record integrity is unaffected — it is proven by "
        "sha256(raw.txt) and sha256(normalized.txt) against the sealed hashes above.",
    )


def _declared_normalization_version(record: Any) -> str | None:
    """The normalizer version a record was sealed under, verbatim, if any.

    Returned as text on purpose: the field is written in several shapes across
    vintages (observed in the live trail: 672 records with no value, 754 with the
    string "1.0", 4 with the integer 3). Reporting it verbatim keeps the
    verifier's message honest about what the record actually says.
    """
    if not isinstance(record, dict):
        return None
    for path in (("content", "normalization_version"), ("normalization_version",)):
        current: Any = record
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                current = None
                break
        if isinstance(current, bool):  # bool is an int subclass; never a version
            continue
        if isinstance(current, (int, float)):
            return str(current)
        if isinstance(current, str) and current.strip():
            return current.strip()
    return None


def _declares_current_normalization(declared: str | None) -> bool:
    """True when a declared version means "the version this verifier runs".

    Accepts 3, "3", "v3" and "3.0" as the same version — the field has been
    written in all of those shapes — and treats anything unparseable as NOT
    current, so an unrecognised value can never silently satisfy the check.
    """
    if not declared:
        return False
    text = declared.strip().lstrip("vV")
    major, _, minor = text.partition(".")
    if not major.isdigit():
        return False
    if minor and minor.strip("0"):  # 3.1 is not 3.0
        return False
    return int(major) == NORMALIZATION_VERSION


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
