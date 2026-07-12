"""Negative-assurance monitoring digest — SILENCE-WITH-PROOF as a trust signal.

A periodic (typically weekly) customer-facing digest that reports, for a period,
the MONITORING ACTIVITY StatuteProof recorded:

  * how many monitored sources were checked, and how many recorded checks ran;
  * which changes were CAPTURED AND SEALED as cryptographic evidence records
    (each linked to its sealed record hash so a recipient can verify it);
  * which sources showed NO CHANGE DETECTED on the days checked; and
  * where coverage has GAPS or DEGRADED checks — disclosed, never hidden.

Design intent (why this exists):

    For a monitoring product, the periods where nothing changed are as important
    as the periods where something did. A digest that says "we checked N sources
    M times, sealed X changes, and detected no change in the rest" turns silence
    into an evidence-backed trust signal. It prevents empty-inbox churn WITHOUT
    ever implying safety.

The legal boundary is the entire risk and is enforced deliberately:

  * This is a record of monitoring ACTIVITY. It NEVER states or implies that the
    reader is compliant, that no action is required, that they are covered, or
    that no change occurred. A no-change result is always framed as
    "no change was DETECTED in the monitored sources in this period" — bounded to
    detection, never a truth claim about the world.
  * A source that failed to check is a GAP, not "all clear": gaps and degraded
    checks are surfaced in their own disclosed section, reusing the honest
    coverage-certificate model.
  * Every authored string is passed through ``assert_no_forbidden_claims`` (with
    a digest-specific superset of the product ban list) before it can be
    returned, so a banned or "you're safe" claim can never reach a customer even
    if wording drifts in future edits.
  * The mandatory short monitoring disclaimer is carried verbatim, alongside the
    full brief-grade disclaimer.

This module is ADDITIVE: it derives everything from real recorded runs (via the
negative-assurance coverage certificate) and real sealed evidence records. It
sends nothing and changes no existing delivery path.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.coverage_certificate import (
    _FULL_CERTIFICATE_DISCLAIMER,
    build_coverage_certificate,
)
from app.evidence_assessment import LEGAL_DISCLAIMER
from app.legal_safety import (
    FORBIDDEN_PHRASES,
    ForbiddenClaimError,
    assert_no_forbidden_claims,
    find_forbidden_claims,
)
from app.regulator_binder import SHORT_MONITORING_DISCLAIMER

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent
_EVIDENCE_REL = Path("evidence")
# Bound the sealed-change payload — the digest is a periodic summary, not a bulk
# export (the Evidence Pack / Binder exist for full handover).
_MAX_DIGEST_CHANGES = 1000

# The published, no-login verification method a recipient can use to confirm any
# sealed record independently (docs/EVIDENCE-VERIFICATION-SPEC.md, served at
# /api/verify-spec; records checkable at POST /api/verify).
_VERIFICATION_SPEC_PATH = "docs/EVIDENCE-VERIFICATION-SPEC.md"
_VERIFICATION_SPEC_URL = "/api/verify-spec"
_VERIFICATION_ENDPOINT = "/api/verify"

# ── Legal-safety guard (superset of the product ban list) ──────────────────────
# The digest inherits the ONE canonical product ban list and ADDS the
# negative-assurance-specific "you're safe" traps that would be uniquely
# dangerous for a silence-with-proof document. Additive, never a fork: the
# canonical FORBIDDEN_PHRASES is always a subset of what the digest scans, so the
# digest can only ever be STRICTER than the product minimum.
#
# Every phrase below is one the digest must NEVER author, even inside a negation.
# The authored strings are written to always frame no-change as DETECTION
# ("no change was detected in the monitored sources in this period") and to
# disclose gaps, so none of these ever appears — the list is a drift tripwire.
_ASSURANCE_EXTRA_FORBIDDEN: tuple[str, ...] = (
    "no action needed",
    "no action required",
    "no further action",
    "nothing to do",
    "you are compliant",
    "you're compliant",
    "you are covered",
    "you're covered",
    "you are safe",
    "you're safe",
    "all clear",
    "safe to ignore",
    "nothing to worry about",
    "no changes occurred",  # a truth claim; the digest only ever says "detected"
)
_ASSURANCE_FORBIDDEN: tuple[str, ...] = tuple(
    dict.fromkeys(  # de-dupe, preserve order
        p.lower() for p in (*FORBIDDEN_PHRASES, *_ASSURANCE_EXTRA_FORBIDDEN)
    )
)


# Vetted, legal-reviewed disclaimer fields. They legitimately NEGATE banned
# phrases ("does not guarantee compliance, prevent fines"), so the recursive
# digest guard skips them (the guard's disclaimer-neutralization would strip them
# anyway; excluding them keeps the content-vs-disclaimer split explicit).
_VETTED_DISCLAIMER_KEYS: frozenset[str] = frozenset(
    {"disclaimer", "disclaimer_short", "disclaimer_short_legacy"}
)

# Empty-state copy is legally load-bearing and MUST NOT drift between the two
# renderers, so it lives in one place. Each frames the empty case as monitoring
# activity, never as "all clear".
_EMPTY_CHANGES_LINE = (
    "No changes were captured and sealed for the monitored sources in this period. This reflects "
    "what was detected on the days checked; see the gaps section for any source that could not be "
    "checked."
)
_EMPTY_NO_CHANGE_LINE = (
    "No source recorded a checked-with-proof, no-change result in this period."
)
_EMPTY_GAPS_LINE = (
    "No coverage gaps, failed checks, or degraded checks were recorded for the monitored sources "
    "during this period, within the limits described in the disclaimer."
)


def find_forbidden_assurance_claims(text: str) -> list[str]:
    """Return every banned phrase (product list + digest superset) present in ``text``."""
    return find_forbidden_claims(text, phrases=_ASSURANCE_FORBIDDEN)


def _assert_legal_safe(text: str, *, label: str = "Assurance digest output") -> str:
    """Raise if ``text`` contains a banned or 'you're safe' claim; else return it.

    Fail-closed net for the FINAL authored bytes: every rendered digest string is
    passed through this before it can be returned, so a banned phrase can never
    reach a customer even if wording drifts. Uses the digest superset so it is
    strictly stronger than the product-wide ``assert_no_forbidden_claims``.
    """
    assert_no_forbidden_claims(
        text, phrases=_ASSURANCE_FORBIDDEN, exc=ForbiddenClaimError, label=label
    )
    return text


def _assert_digest_legal_safe(digest: dict[str, Any]) -> None:
    """Fail-closed sweep over EVERY authored string in the assembled digest dict.

    The raw digest dict is always returned to the caller (the API always includes
    ``payload["digest"]``), so every human-readable value it carries — including
    free-text fields that originate outside this module (a sealed record's
    ``change.summary``, a custom source's ``source_name``, a per-source
    ``gap_disclosure``) — must be provably clean, not just the two headline
    strings. Vetted disclaimer fields are skipped (they legitimately negate banned
    phrases). Raises ``ForbiddenClaimError`` before the digest can be returned.
    """
    def _walk(value: Any, key: str | None) -> None:
        if key in _VETTED_DISCLAIMER_KEYS:
            return
        if isinstance(value, str):
            if value:
                _assert_legal_safe(value, label=f"assurance digest field {key or '<value>'}")
        elif isinstance(value, dict):
            for k, v in value.items():
                _walk(v, str(k))
        elif isinstance(value, (list, tuple)):
            for item in value:
                _walk(item, key)

    _walk(digest, None)


# ── period + parsing helpers ───────────────────────────────────────────────────

def _parse_date(value: str) -> date:
    return date.fromisoformat(str(value).strip()[:10])


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _period_label(start: date, end: date) -> str:
    if start == end:
        return start.isoformat()
    return f"{start.isoformat()} to {end.isoformat()}"


def _utc_now(now: datetime) -> str:
    return now.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_prefix(record_hash: str, length: int = 12) -> str:
    """Short, display-safe prefix of a sealed record hash (keeps the algo tag)."""
    value = str(record_hash or "").strip()
    if value.startswith("sha256:"):
        digest = value[len("sha256:"):]
        return f"sha256:{digest[:length]}" if digest else ""
    return value[:length]


# ── sealed evidence-record loading (period + scope filtered) ───────────────────

def _load_sealed_change_records(
    root: Path,
    *,
    start_dt: datetime,
    end_dt: datetime,
    allowed_source_ids: set[str],
) -> list[dict[str, Any]]:
    """Return sealed CHANGED evidence records inside the period, scoped to sources.

    A record counts only when it is genuinely SEALED — ``record_status`` is
    ``complete`` and it carries a ``record_hash`` self-seal — and its run status
    is ``CHANGED`` (a captured content change, not a baseline first-seen). This is
    the SILENCE-WITH-PROOF payload: every change the digest reports links to a
    verifiable sealed record hash. Nothing is fabricated; a run that changed but
    was never sealed simply is not counted here (it still surfaces in the
    coverage summary's detected-change count for honest reconciliation).

    Scoped to ``allowed_source_ids`` so a record for a source outside the
    reported set (another tenant's custom source) can never leak in.
    """
    evidence_root = root / _EVIDENCE_REL
    if not evidence_root.exists():
        return []

    # Scope the walk to the allowed sources ONLY (layout
    # evidence/<regulator>/<source_id>/<run>/evidence-record.json) so the digest
    # never enumerates the whole cross-tenant evidence store — cost O(reported
    # scope), not O(total product evidence). Matches evidence_pack/evidence_room
    # (verify-swarm 2026-07-12). A source_id that isn't a safe path segment could
    # never have matched a real record dir, so it is skipped.
    import re as _re

    # Reject all-dot segments (".."/".") so a traversal id can't collapse the
    # per-source glob back to a whole-tree walk (verify-swarm 2026-07-12).
    _safe_segment = _re.compile(r"^(?!\.+$)[A-Za-z0-9._-]+$")
    record_paths: list[Path] = []
    for sid in sorted(allowed_source_ids):
        if _safe_segment.match(str(sid)):
            record_paths.extend(evidence_root.glob(f"*/{sid}/**/evidence-record.json"))

    out: list[dict[str, Any]] = []
    for path in sorted(record_paths):
        if len(out) >= _MAX_DIGEST_CHANGES:
            break  # bound the payload; the digest is a summary, not a bulk export
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(record, dict):
            continue
        if str(record.get("record_status") or "").strip() != "complete":
            continue
        record_hash = str(record.get("record_hash") or "").strip()
        if not record_hash.lower().startswith("sha256:"):
            continue  # not sealed → not eligible as proof

        run = record.get("run") if isinstance(record.get("run"), dict) else {}
        if str(run.get("status") or "").strip().upper() != "CHANGED":
            continue
        ts = _parse_ts(run.get("timestamp"))
        if ts is None or ts < start_dt or ts > end_dt:
            continue

        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        source_id = str(source.get("source_id") or "").strip()
        if not source_id or source_id not in allowed_source_ids:
            continue

        change = record.get("change") if isinstance(record.get("change"), dict) else {}
        integrity = record.get("integrity") if isinstance(record.get("integrity"), dict) else {}
        out.append(
            {
                "record_id": str(record.get("record_id") or "").strip(),
                "record_hash": record_hash,
                "record_hash_prefix": _hash_prefix(record_hash),
                "record_path": _relative_or_str(path, root),
                "source_id": source_id,
                "source_name": str(source.get("source_name") or source_id),
                "regulator": str(source.get("regulator") or ""),
                "official_url": str(source.get("official_url") or ""),
                "run_id": str(run.get("run_id") or ""),
                "captured_at_utc": ts.isoformat().replace("+00:00", "Z"),
                "sealed_at_utc": str(integrity.get("verified_at") or ""),
                "change_summary": str(change.get("summary") or ""),
                "lines_added": int(change.get("lines_added") or 0),
                "lines_removed": int(change.get("lines_removed") or 0),
                "verification": {
                    "record_hash": record_hash,
                    "spec": _VERIFICATION_SPEC_PATH,
                    "endpoint": _VERIFICATION_ENDPOINT,
                },
            }
        )
    out.sort(key=lambda r: (r["captured_at_utc"], r["source_id"], r["record_id"]))
    return out


def _relative_or_str(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# ── digest builder ──────────────────────────────────────────────────────────────

def build_assurance_digest(
    *,
    period_start: str,
    period_end: str,
    source_ids: list[str] | None = None,
    client_name: str = "",
    base_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a negative-assurance monitoring-activity digest for a period.

    Derives entirely from recorded evidence: the honest per-source coverage model
    (``build_coverage_certificate``) plus sealed CHANGED evidence records. It
    fabricates nothing — a source with no successful check is reported as a GAP,
    never as "no change".

    Parameters mirror ``build_coverage_certificate``: ``period_start`` /
    ``period_end`` are inclusive ISO dates. ``source_ids=None`` scopes to the
    customer's configured (enabled) sources unioned with any that ran in the
    period; an EXPLICIT empty list (``[]``) means "no sources in scope" and yields
    an honest empty digest — it is NEVER widened to the global default (the
    tenancy-critical distinction the API handler relies on). ``now`` pins the
    reference time for gap counting (defaults to UTC now).

    Returns a deterministic, machine-readable digest dict. Every human-readable
    string it carries — including free-text fields sourced from evidence records —
    has passed the fail-closed digest legal-safety guard before return.
    """
    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    reference_now = now or datetime.now(timezone.utc)

    start_date = _parse_date(period_start)
    end_date = _parse_date(period_end)
    if end_date < start_date:
        raise ValueError("period_end must be on or after period_start")
    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    end_dt = datetime(
        end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999, tzinfo=timezone.utc
    )

    # Tenancy-critical: an EXPLICIT empty scope must produce an empty digest, not
    # be delegated to build_coverage_certificate (whose ``if source_ids:`` treats
    # ``[]`` as "all configured sources", re-opening a global, cross-tenant scope).
    if source_ids is not None and len(source_ids) == 0:
        cert_rows: list[dict[str, Any]] = []
        cert_summary: dict[str, Any] = {}
        coverage_certificate_id = ""
        full_disclaimer = _FULL_CERTIFICATE_DISCLAIMER
        sealed_changes: list[dict[str, Any]] = []
    else:
        # Reuse the negative-assurance coverage certificate: it already computes the
        # honest per-source model (checks, no-change-detected, gaps, degraded) from
        # real recorded runs. The digest is a customer-facing framing OF that model
        # plus the sealed-change proof links.
        certificate = build_coverage_certificate(
            period_start=period_start,
            period_end=period_end,
            source_ids=source_ids,
            client_name=client_name,
            base_dir=base_dir,
            now=reference_now,
        )
        cert_rows = certificate.get("sources") if isinstance(certificate.get("sources"), list) else []
        cert_summary = certificate.get("summary") if isinstance(certificate.get("summary"), dict) else {}
        coverage_certificate_id = certificate.get("certificate_id", "")
        full_disclaimer = certificate.get("disclaimer", _FULL_CERTIFICATE_DISCLAIMER)
        reported_source_ids = {str(r.get("source_id") or "") for r in cert_rows if r.get("source_id")}
        sealed_changes = _load_sealed_change_records(
            root, start_dt=start_dt, end_dt=end_dt, allowed_source_ids=reported_source_ids
        )

    # A source is reported as clean "no change detected" ONLY when it was checked
    # with a proof hash AND its coverage is CONTINUOUS (no gap days, not degraded).
    # A source that also has a gap or a failed check is disclosed ONLY in the gaps
    # section — it is never folded into the clean no-change list, which would
    # understate the gap and risk reading as "all clear".
    no_change_sources = [
        _no_change_row(r)
        for r in cert_rows
        if r.get("change_state") == "UNCHANGED" and r.get("continuity_status") == "CONTINUOUS"
    ]
    gaps = [_gap_row(r) for r in cert_rows if _is_gap_or_degraded(r)]
    detected_change_sources = [
        _detected_change_row(r) for r in cert_rows if r.get("change_state") == "CHANGED"
    ]

    sources_checked = sum(1 for r in cert_rows if int(r.get("checks_in_period") or 0) > 0)
    # Counts are computed from the SAME partitioned lists the digest displays, so
    # a headline number can never diverge from the section it summarizes.
    summary = {
        "sources_monitored": len(cert_rows),
        "sources_checked": sources_checked,
        "total_checks": int(cert_summary.get("total_checks") or 0),
        "total_successful_checks": int(cert_summary.get("total_successful_checks") or 0),
        "changes_captured_and_sealed": len(sealed_changes),
        "sources_with_detected_change": len(detected_change_sources),
        "sources_no_change_detected": len(no_change_sources),
        "sources_with_gaps": int(cert_summary.get("sources_with_gaps") or 0),
        "sources_degraded": int(cert_summary.get("sources_degraded") or 0),
        "sources_no_coverage": int(cert_summary.get("sources_no_coverage") or 0),
        "total_days_with_proof_hash": int(cert_summary.get("total_days_with_proof_hash") or 0),
    }

    statement = _assurance_statement(
        client_name=client_name,
        period_label=_period_label(start_date, end_date),
        summary=summary,
    )
    verification = _verification_pointer(len(sealed_changes))

    digest = {
        "schema_version": "1.0",
        "document_type": "assurance_digest",
        "assurance_type": "negative_assurance",
        "customer_facing": True,
        "generated_at_utc": _utc_now(reference_now),
        "client_name": client_name,
        "period_label": _period_label(start_date, end_date),
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "summary": summary,
        "changes_captured_and_sealed": sealed_changes,
        "sources_no_change_detected": no_change_sources,
        "sources_with_detected_change": detected_change_sources,
        "gaps_and_degraded": gaps,
        "assurance_statement": _assert_legal_safe(statement, label="assurance_statement"),
        "verification": verification,
        "coverage_certificate_id": coverage_certificate_id,
        "disclaimer": full_disclaimer,
        "disclaimer_short": SHORT_MONITORING_DISCLAIMER,
        "disclaimer_short_legacy": LEGAL_DISCLAIMER,
    }
    digest["digest_id"] = _digest_id(digest)
    # Fail-closed: no banned or "you're safe" claim can reach the caller in ANY
    # authored field of the raw dict, including free text sourced from evidence
    # records (change summaries, source names, gap disclosures).
    _assert_digest_legal_safe(digest)
    return digest


def _is_gap_or_degraded(row: dict[str, Any]) -> bool:
    return (
        int(row.get("gap_days") or 0) > 0
        or bool(row.get("degraded"))
        or row.get("change_state") == "NO_PROOF"
        or row.get("continuity_status") in {"PARTIAL", "NO_COVERAGE"}
    )


def _no_change_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": row.get("source_id", ""),
        "source_name": row.get("source_name", "") or row.get("source_id", ""),
        "official_url": row.get("official_url", ""),
        "checks_in_period": int(row.get("checks_in_period") or 0),
        "successful_checks": int(row.get("successful_checks") or 0),
        "days_with_proof_hash": int(row.get("days_with_proof_hash") or 0),
        "first_check_utc": row.get("first_check_utc", ""),
        "last_check_utc": row.get("last_check_utc", ""),
        "last_proof_hash": row.get("last_proof_hash", ""),
        "continuity_status": row.get("continuity_status", ""),
    }


def _gap_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": row.get("source_id", ""),
        "source_name": row.get("source_name", "") or row.get("source_id", ""),
        "official_url": row.get("official_url", ""),
        "continuity_status": row.get("continuity_status", ""),
        "change_state": row.get("change_state", ""),
        "gap_days": int(row.get("gap_days") or 0),
        "max_consecutive_gap_days": int(row.get("max_consecutive_gap_days") or 0),
        "degraded": bool(row.get("degraded")),
        "failed_count": int(row.get("failed_count") or 0),
        "quality_drop_count": int(row.get("quality_drop_count") or 0),
        "gap_disclosure": row.get("gap_disclosure", ""),
    }


def _detected_change_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": row.get("source_id", ""),
        "source_name": row.get("source_name", "") or row.get("source_id", ""),
        "official_url": row.get("official_url", ""),
        "changed_count": int(row.get("changed_count") or 0),
        "last_proof_hash": row.get("last_proof_hash", ""),
    }


def _assurance_statement(
    *, client_name: str, period_label: str, summary: dict[str, Any]
) -> str:
    """The digest's headline paragraph — detection-bounded, gap-disclosing, safe."""
    who = f" for {client_name}" if client_name else ""
    checks = summary["total_checks"]
    sources_checked = summary["sources_checked"]
    sealed = summary["changes_captured_and_sealed"]
    no_change = summary["sources_no_change_detected"]

    if checks == 0:
        lead = (
            f"This monitoring digest{who} covers {period_label}. StatuteProof has no recorded "
            f"monitoring checks for the monitored sources in this period. An empty period means "
            f"no checks were recorded — it is not confirmation that no change happened, and it is "
            f"not a statement that any action is or is not required."
        )
    else:
        lead = (
            f"This digest records the official-source monitoring activity StatuteProof performed"
            f"{who} during {period_label}. Across {sources_checked} monitored source(s), "
            f"StatuteProof completed {checks} recorded check(s) in this period. "
            f"{sealed} change(s) were captured and sealed as cryptographic evidence records, "
            f"each listed below with its sealed record hash so it can be verified independently. "
            f"For {no_change} monitored source(s), no change was detected in the recorded content "
            f"on the days checked in this period."
        )

    gaps = summary["sources_with_gaps"]
    degraded = summary["sources_degraded"]
    no_cover = summary["sources_no_coverage"]
    if gaps or degraded or no_cover:
        gap_sentence = (
            f" {gaps} source(s) had one or more days without a recorded proof-hash check, "
            f"{degraded} source(s) recorded a failed or degraded check, and {no_cover} source(s) "
            f"had no successful check in this period. A source that was not successfully checked "
            f"is a monitoring gap, not a no-change result, and every such gap is disclosed in the "
            f"gaps section below for direct review."
        )
    else:
        gap_sentence = (
            " No coverage gaps, failed checks, or degraded checks were recorded for the monitored "
            "sources during this period, within the limits described in the disclaimer below."
        )

    boundary = (
        " This digest is a record of monitoring activity only. It does not confirm your compliance "
        "status, does not assert that every regulatory change has been captured, and a no-change "
        "result never means the reader is covered. A no-change result means only that no change was "
        "detected in the monitored source within the limits described below. Review the sealed "
        "evidence records, hashes, and diffs below, and verify the official sources directly before "
        "deciding what action to take."
    )
    return lead + gap_sentence + boundary


def _verification_pointer(sealed_count: int) -> dict[str, Any]:
    note = (
        f"Every one of the {sealed_count} change(s) reported in this digest is backed by a sealed "
        f"evidence record. To verify any record independently, recompute the record content hash "
        f"and compare it to the sealed record hash shown, or submit the record to the public "
        f"verification method. The open method is published at {_VERIFICATION_SPEC_PATH}."
    )
    return {
        "note": _assert_legal_safe(note, label="verification_pointer"),
        "spec_path": _VERIFICATION_SPEC_PATH,
        "spec_url": _VERIFICATION_SPEC_URL,
        "endpoint": _VERIFICATION_ENDPOINT,
    }


def _digest_id(digest: dict[str, Any]) -> str:
    """Deterministic id over period, client, sealed-change hashes, and coverage id.

    Excludes ``generated_at_utc`` so re-issuing an identical digest for the same
    evidence yields the same id — a stable reference for the customer.
    """
    seed_parts = [
        digest["period_start"],
        digest["period_end"],
        str(digest.get("client_name") or ""),
        str(digest.get("coverage_certificate_id") or ""),
    ]
    for change in digest.get("changes_captured_and_sealed", []):
        seed_parts.append(f"{change.get('record_id', '')}|{change.get('record_hash', '')}")
    seed = "\n".join(seed_parts)
    return "asr-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]


# ── rendering ───────────────────────────────────────────────────────────────────

def render_assurance_digest_markdown(digest: dict[str, Any]) -> str:
    """Render the digest as customer-facing Markdown (legal-safe, guarded)."""
    summary = digest.get("summary") if isinstance(digest.get("summary"), dict) else {}
    sealed = digest.get("changes_captured_and_sealed") if isinstance(digest.get("changes_captured_and_sealed"), list) else []
    no_change = digest.get("sources_no_change_detected") if isinstance(digest.get("sources_no_change_detected"), list) else []
    gaps = digest.get("gaps_and_degraded") if isinstance(digest.get("gaps_and_degraded"), list) else []

    lines: list[str] = [
        f"# Monitoring Activity Digest — {digest.get('period_label', 'Unknown period')}",
        "",
        "_Negative-assurance record: what was checked, what changed and was sealed, and where "
        "coverage has gaps._",
        "",
    ]
    if digest.get("client_name"):
        lines.append(f"**Client:** {digest['client_name']}")
    lines.append(f"**Digest ID:** {digest.get('digest_id', '')}")
    lines.append(f"**Period:** {digest.get('period_start', '')} to {digest.get('period_end', '')}")
    lines.append(f"**Generated:** {digest.get('generated_at_utc', '')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines += ["## What this digest reports", "", digest.get("assurance_statement", ""), ""]

    lines += [
        "## Monitoring activity this period",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Sources monitored | {summary.get('sources_monitored', 0)} |",
        f"| Sources checked | {summary.get('sources_checked', 0)} |",
        f"| Recorded checks | {summary.get('total_checks', 0)} |",
        f"| Changes captured and sealed | {summary.get('changes_captured_and_sealed', 0)} |",
        f"| Sources with no change detected | {summary.get('sources_no_change_detected', 0)} |",
        f"| Sources with one or more gap days | {summary.get('sources_with_gaps', 0)} |",
        f"| Sources with a failed/degraded check | {summary.get('sources_degraded', 0)} |",
        f"| Sources with no successful check | {summary.get('sources_no_coverage', 0)} |",
        "",
    ]

    # Changes captured and sealed — each linked to its sealed record hash.
    lines += ["## Changes captured and sealed", ""]
    if sealed:
        for change in sealed:
            lines.append(
                f"- **{_md(change.get('source_name') or change.get('source_id'))}** "
                f"({_md(change.get('regulator') or '—')}) — captured {_md(change.get('captured_at_utc'))}. "
                f"Sealed record `{_md(change.get('record_id'))}`, hash `{_md(change.get('record_hash_prefix'))}`. "
                f"{_md(change.get('change_summary') or 'Change detected against the previous sealed content.')}"
            )
    else:
        lines.append(f"- {_EMPTY_CHANGES_LINE}")
    lines.append("")

    # No change detected — silence WITH proof.
    lines += ["## No change detected (checked, with proof)", ""]
    if no_change:
        for row in no_change:
            hash_prefix = _hash_prefix(row.get("last_proof_hash", ""), 12)
            lines.append(
                f"- **{_md(row.get('source_name') or row.get('source_id'))}** — checked "
                f"{row.get('checks_in_period', 0)} time(s) across {row.get('days_with_proof_hash', 0)} "
                f"day(s) with a proof hash; no change was detected on the days checked in this period. "
                f"Latest proof hash `{_md(hash_prefix or '—')}`."
            )
    else:
        lines.append(f"- {_EMPTY_NO_CHANGE_LINE}")
    lines.append("")

    # Gaps and degraded — disclosed, never hidden.
    lines += ["## Gaps and degraded checks (disclosed)", ""]
    if gaps:
        for row in gaps:
            lines.append(
                f"- **{_md(row.get('source_name') or row.get('source_id'))}** "
                f"({_md(row.get('continuity_status') or '')}): {_md(row.get('gap_disclosure') or '')}"
            )
    else:
        lines.append(f"- {_EMPTY_GAPS_LINE}")
    lines.append("")

    # Verification pointer.
    verification = digest.get("verification") if isinstance(digest.get("verification"), dict) else {}
    lines += ["## How to verify", "", verification.get("note", ""), ""]

    body = "\n".join(lines)
    _assert_legal_safe(body, label="assurance digest markdown body")
    disclaimer = digest.get("disclaimer", "")
    short = digest.get("disclaimer_short", SHORT_MONITORING_DISCLAIMER)
    return f"{body}\n---\n\n**{short}**\n\n**Disclaimer:** {disclaimer}\n"


def render_assurance_digest_email_text(digest: dict[str, Any]) -> str:
    """Render the digest as a plain-text email body (legal-safe, guarded)."""
    summary = digest.get("summary") if isinstance(digest.get("summary"), dict) else {}
    sealed = digest.get("changes_captured_and_sealed") if isinstance(digest.get("changes_captured_and_sealed"), list) else []
    no_change = digest.get("sources_no_change_detected") if isinstance(digest.get("sources_no_change_detected"), list) else []
    gaps = digest.get("gaps_and_degraded") if isinstance(digest.get("gaps_and_degraded"), list) else []
    verification = digest.get("verification") if isinstance(digest.get("verification"), dict) else {}

    lines: list[str] = [
        f"StatuteProof — Monitoring Activity Digest ({digest.get('period_label', '')})",
    ]
    if digest.get("client_name"):
        lines.append(f"Client: {digest['client_name']}")
    lines.append("")
    lines.append(digest.get("assurance_statement", ""))
    lines.append("")
    lines.append("Monitoring activity this period:")
    lines.append(f"  - Sources monitored: {summary.get('sources_monitored', 0)}")
    lines.append(f"  - Sources checked: {summary.get('sources_checked', 0)}")
    lines.append(f"  - Recorded checks: {summary.get('total_checks', 0)}")
    lines.append(f"  - Changes captured and sealed: {summary.get('changes_captured_and_sealed', 0)}")
    lines.append(f"  - Sources with no change detected: {summary.get('sources_no_change_detected', 0)}")
    lines.append(f"  - Sources with one or more gap days: {summary.get('sources_with_gaps', 0)}")
    lines.append(f"  - Sources with a failed/degraded check: {summary.get('sources_degraded', 0)}")
    lines.append(f"  - Sources with no successful check: {summary.get('sources_no_coverage', 0)}")
    lines.append("")

    lines.append("Changes captured and sealed:")
    if sealed:
        for change in sealed:
            lines.append(
                f"  - {change.get('source_name') or change.get('source_id')} "
                f"({change.get('regulator') or '-'}): sealed record {change.get('record_id')}, "
                f"hash {change.get('record_hash_prefix')}, captured {change.get('captured_at_utc')}."
            )
    else:
        lines.append(f"  - {_EMPTY_CHANGES_LINE}")
    lines.append("")

    lines.append("No change detected (checked, with proof):")
    if no_change:
        for row in no_change:
            lines.append(
                f"  - {row.get('source_name') or row.get('source_id')}: "
                f"checked {row.get('checks_in_period', 0)} time(s); no change detected on the days "
                f"checked in this period."
            )
    else:
        lines.append(f"  - {_EMPTY_NO_CHANGE_LINE}")
    lines.append("")

    lines.append("Gaps and degraded checks (disclosed):")
    if gaps:
        for row in gaps:
            lines.append(
                f"  - {row.get('source_name') or row.get('source_id')} "
                f"({row.get('continuity_status')}): {row.get('gap_disclosure')}"
            )
    else:
        lines.append(f"  - {_EMPTY_GAPS_LINE}")
    lines.append("")

    lines.append("How to verify:")
    lines.append(f"  {verification.get('note', '')}")
    lines.append("")

    body = "\n".join(lines)
    _assert_legal_safe(body, label="assurance digest email body")
    short = digest.get("disclaimer_short", SHORT_MONITORING_DISCLAIMER)
    disclaimer = digest.get("disclaimer", "")
    return f"{body}\n{short}\n\nDisclaimer: {disclaimer}\n"


def _md(value: Any) -> str:
    """Escape pipe/newline so a value cannot break the Markdown structure."""
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")
