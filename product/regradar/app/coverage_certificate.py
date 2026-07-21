"""Negative-assurance coverage certificate — the MLRO-liability answer.

A per-period, customer-facing certificate that states, for each monitored
official source, HOW OFTEN it was checked, the FIRST and LAST recorded check,
how many distinct UTC days carried a cryptographic proof hash, and — crucially —
where the recorded evidence has GAPS (days with no successful check, stale
sources, or FAILED / QUALITY_DROP runs).

Design intent (why this exists):

    An MLRO cannot rely on "we monitor everything". They need a document that
    says exactly WHAT WAS CHECKED and, honestly, WHAT WAS NOT. This certificate
    is deliberately a *negative-assurance* instrument: it confirms the checks
    that were performed and discloses every gap. It makes NO claim of complete
    coverage, NO guarantee, and is NOT legal advice or a compliance
    certification. Those boundaries are enforced three ways:

      1. A standard disclaimer (full + short) is embedded in every rendering.
      2. A forbidden-claims guard (reusing the shared _FORBIDDEN_PHRASES tuple
         from app.monthly_assurance_report) runs over every rendered string and
         raises before any output that contains a banned phrase can be returned.
      3. Every asserted number is derived only from real recorded source-run
         evidence (data/source_runs/source_runs.jsonl). Nothing is backfilled,
         estimated, or implied — a source with no runs in the period is shown as
         NO_COVERAGE, not silently omitted.

The certificate is a promotion of the operator-only verified monitoring digest
(app.verified_monitoring_digest) into a customer-facing continuity record.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.evidence_assessment import LEGAL_DISCLAIMER
from app.legal_safety import find_forbidden_claims as _find_forbidden_claims
from app.monthly_assurance_report import _FORBIDDEN_PHRASES
from app.record_hashing import canonical_record_hash
from app.source_health_timeline import source_health_customer_message

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent
_REPORTS_DIR = _BASE_DIR / "reports"
_SOURCE_RUNS_REL = Path("data") / "source_runs" / "source_runs.jsonl"

_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# The full certificate disclaimer mirrors the brief-grade disclaimer defined in
# CLAUDE.md. A coverage certificate is a formal customer document, so it carries
# the full text (not just the short LEGAL_DISCLAIMER line).
_FULL_CERTIFICATE_DISCLAIMER = (
    "StatuteProof reports are generated from monitored official-source records and are provided "
    "for information and compliance review support only. StatuteProof reports do not constitute "
    "legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof "
    "does not replace qualified legal counsel, compliance professionals, MLROs, or other "
    "professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify "
    "that all regulatory updates have been captured. Source monitoring may be affected by "
    "publication delays, website changes, PDF formatting, access limits, or source structure "
    "changes. Users should verify official source material directly and review evidence records, "
    "hashes, timestamps, and diffs before relying on a report. Users should consult qualified "
    "legal or compliance professionals before making regulatory, filing, operational, or customer "
    "decisions based on a report."
)

# Reuse the shared forbidden-phrases guard from the monthly assurance report and
# extend it with the remaining banned claims from CLAUDE.md that are relevant to
# a coverage/assurance document. Kept lowercase; the guard compares case-folded.
# These are NEEDLES: the guard searches for them in generated body text. The
# vetted standard disclaimer (which legitimately NEGATES some of these, e.g.
# "does not guarantee compliance") is excluded from the haystack — the same
# content-vs-disclaimer split the monthly assurance report test uses.
_EXTRA_FORBIDDEN = (
    "ai lawyer",
    "replace lawyers",
    "official partner",
    "stay compliant automatically",
    "never miss an update",
    "complete coverage",
    "full coverage of all",
    "all regulatory updates captured",
    "guarantee complete",
)
_ALL_FORBIDDEN: tuple[str, ...] = tuple(
    dict.fromkeys(  # de-dupe while preserving order
        p.lower() for p in (*_FORBIDDEN_PHRASES, *_EXTRA_FORBIDDEN)
    )
)


def contains_forbidden_claim(text: str) -> str | None:
    """Return the first forbidden phrase found in ``text``, or None if clean.

    Thin adapter over the ONE canonical guard in ``app.legal_safety``, passing
    this module's superset of needles. It used to be a bare ``lower()`` +
    substring scan, so the certificate — the most audit-facing artefact the
    product emits — silently missed the whitespace-collapse, homoglyph folding
    and inflection matching applied everywhere else: "StatuteProof guarantees
    compliance." and "We guarantee\\ncompliance." rendered clean here while the
    same strings were blocked on every other delivery path. The canonical guard
    also neutralizes the product's fixed disclaimers and directly-negated
    occurrences, so the vetted denial wording still cannot trip its own guard.
    Do not reintroduce a local scan here.
    """
    hits = set(_find_forbidden_claims(text, phrases=_ALL_FORBIDDEN))
    # Preserve the historical return contract: the FIRST needle in _ALL_FORBIDDEN
    # order, not an alphabetical pick.
    for phrase in _ALL_FORBIDDEN:
        if phrase in hits:
            return phrase
    return None


def _assert_legal_safe(text: str) -> str:
    """Raise ValueError if ``text`` contains a forbidden claim; else return it.

    A programming-error safety net: rendered customer output is passed through
    this before it is returned, so a banned phrase can never reach a customer
    even if wording drifts in future edits.
    """
    hit = contains_forbidden_claim(text)
    if hit is not None:
        raise ValueError(
            f"Coverage certificate output contains forbidden claim {hit!r}; refusing to render."
        )
    return text


# ── period helpers ────────────────────────────────────────────────────────────

def month_period(year: int, month: int) -> tuple[str, str]:
    """Return (period_start, period_end) ISO dates for a calendar month."""
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"


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
    if start.year == end.year and start.month == end.month and start.day == 1:
        last_day = calendar.monthrange(start.year, start.month)[1]
        if end.day == last_day:
            return f"{_MONTH_NAMES[start.month]} {start.year}"
    return f"{start.isoformat()} to {end.isoformat()}"


# ── evidence loading (base_dir-scoped for tests) ───────────────────────────────

def _load_runs_by_source(root: Path) -> dict[str, list[dict[str, Any]]]:
    path = root / _SOURCE_RUNS_REL
    if not path.exists():
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    # Stream line-by-line — never materialize the whole (unbounded, ever-growing)
    # run log into memory at once. This reader is exercised on every coverage
    # certificate AND every assurance-digest preview (verify-swarm 2026-07-12;
    # matches the audit_export._fetch_runs_for_vault streaming fix).
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("coverage certificate: skipping unparseable source_runs line in %s", path)
                    continue
                if not isinstance(parsed, dict):
                    continue
                source_id = str(parsed.get("source_id") or "").strip()
                if source_id:
                    out.setdefault(source_id, []).append(parsed)
    except OSError:
        return out
    return out


def enabled_source_ids(base_dir: Path | None = None) -> list[str]:
    """The customer's CONFIGURED/subscribed source set (enabled sources).

    Returns the deterministic ``make_source_id`` for every ``enabled=True`` source
    in ``sources.json`` so the ids line up with the ``source_runs`` record keys.
    This is what scopes the default customer certificate: a configured source that
    went fully dark for the whole period MUST still surface (as NO_COVERAGE)
    rather than being silently dropped, which is the entire point of a
    negative-assurance instrument. Best-effort — any read/parse error yields an
    empty list (the caller then falls back to run-derived ids).
    """
    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    path = root / "sources.json"
    try:
        from app.source_runs import make_source_id
        from app.sources import get_enabled_sources

        return sorted({make_source_id(src) for src in get_enabled_sources(path)})
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("coverage certificate: enabled-source scope read failed: %s", exc)
        return []


def _load_sources(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "sources.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    rows = payload.get("sources", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or row.get("id") or "").strip()
        if source_id:
            out[source_id] = row
    return out


# ── gap analysis ───────────────────────────────────────────────────────────────

def _max_consecutive_gap_days(
    proof_dates: set[date], start_date: date, end_effective: date
) -> int:
    """Largest run of consecutive calendar days in the period with NO proof check.

    Includes the leading gap (period start → first proof day) and the trailing
    gap (last proof day → effective period end), so a source that stopped being
    checked mid-period shows a real gap rather than looking continuous.
    """
    if end_effective < start_date:
        return 0
    if not proof_dates:
        return (end_effective - start_date).days + 1
    days = sorted(d for d in proof_dates if start_date <= d <= end_effective)
    if not days:
        return (end_effective - start_date).days + 1
    max_gap = (days[0] - start_date).days  # leading gap
    for earlier, later in zip(days, days[1:]):
        max_gap = max(max_gap, (later - earlier).days - 1)
    max_gap = max(max_gap, (end_effective - days[-1]).days)  # trailing gap
    return max(0, max_gap)


def _has_proof_hash(run: dict[str, Any]) -> bool:
    return bool(run.get("normalized_hash") or run.get("content_hash"))


def _is_skipped_cycle(run: dict[str, Any]) -> bool:
    """True for a trail record written for a cycle in which the source was NOT
    fetched (circuit breaker open). Evidence of a non-check, never a check."""
    return (
        str(run.get("failure_code") or "").upper() == "CIRCUIT_OPEN"
        or str(run.get("access_status") or "").lower() == "circuit_open"
    )


def _run_ts(run: dict[str, Any]) -> datetime | None:
    return _parse_ts(run.get("timestamp_utc") or run.get("run_at"))


def _source_continuity(
    *,
    source_id: str,
    source: dict[str, Any],
    runs: list[dict[str, Any]],
    start_dt: datetime,
    end_dt: datetime,
    start_date: date,
    end_effective_date: date,
    expected_days: int,
) -> dict[str, Any]:
    """Build one per-source continuity row from recorded runs in the period."""
    in_period: list[tuple[datetime, dict[str, Any]]] = []
    skipped_cycles = 0
    for run in runs:
        ts = _run_ts(run)
        if ts is None or ts < start_dt or ts > end_dt:
            continue
        # A cycle skipped by the circuit breaker issued no request at all: it
        # proves the ABSENCE of a check and must never be counted or dated as
        # one (it would inflate "recorded checks" and reset the staleness
        # clock for exactly the sources that went dark).
        if _is_skipped_cycle(run):
            skipped_cycles += 1
            continue
        in_period.append((ts, run))
    in_period.sort(key=lambda pair: pair[0])

    proof_dates: set[date] = set()
    changed_count = 0
    first_seen_count = 0
    failed_count = 0
    quality_drop_count = 0
    last_proof_hash = ""
    last_change_status = ""
    degraded_reasons: list[str] = []

    for ts, run in in_period:
        status = str(run.get("change_status") or "").upper()
        last_change_status = status or last_change_status
        if _has_proof_hash(run):
            proof_dates.add(ts.date())
            last_proof_hash = str(run.get("normalized_hash") or run.get("content_hash") or "")
        if status == "CHANGED":
            changed_count += 1
        elif status == "FIRST_SEEN":
            first_seen_count += 1
        elif status == "FAILED":
            failed_count += 1
            reason = str(run.get("limitations_notes") or run.get("error") or "").strip()
            if reason:
                degraded_reasons.append(reason)
        elif status == "QUALITY_DROP":
            quality_drop_count += 1
            reason = str(run.get("limitations_notes") or run.get("error") or "").strip()
            if reason:
                degraded_reasons.append(reason)

    checks_in_period = len(in_period)
    successful_checks = sum(1 for _, run in in_period if _has_proof_hash(run))
    days_with_proof = len(proof_dates)
    first_check = in_period[0][0].isoformat().replace("+00:00", "Z") if in_period else ""
    last_check = in_period[-1][0].isoformat().replace("+00:00", "Z") if in_period else ""
    gap_days = max(0, expected_days - days_with_proof)
    max_gap = _max_consecutive_gap_days(proof_dates, start_date, end_effective_date)
    degraded = (failed_count + quality_drop_count) > 0

    # Days the last check trails the effective period end — a staleness signal.
    if in_period:
        last_check_gap_days = max(0, (end_effective_date - in_period[-1][0].date()).days)
    else:
        last_check_gap_days = expected_days

    if successful_checks == 0:
        change_state = "NO_PROOF"
    elif changed_count > 0:
        change_state = "CHANGED"
    else:
        change_state = "UNCHANGED"

    if successful_checks == 0:
        continuity_status = "NO_COVERAGE"
    elif gap_days == 0 and not degraded:
        continuity_status = "CONTINUOUS"
    else:
        continuity_status = "PARTIAL"

    gap_disclosure = _gap_disclosure(
        change_state=change_state,
        continuity_status=continuity_status,
        gap_days=gap_days,
        max_gap=max_gap,
        failed_count=failed_count,
        quality_drop_count=quality_drop_count,
        skipped_cycles=skipped_cycles,
        last_check_gap_days=last_check_gap_days,
        degraded_reasons=degraded_reasons,
    )

    official_url = (
        source.get("url")
        or (in_period[-1][1].get("official_url") if in_period else "")
        or (in_period[-1][1].get("final_url") if in_period else "")
        or ""
    )
    source_name = (
        source.get("name")
        or (in_period[-1][1].get("source_name") if in_period else "")
        or source_id
    )

    return {
        "source_id": source_id,
        "source_name": source_name,
        "official_url": official_url,
        "checks_in_period": checks_in_period,
        "skipped_cycles": skipped_cycles,
        "successful_checks": successful_checks,
        "first_check_utc": first_check,
        "last_check_utc": last_check,
        "days_with_proof_hash": days_with_proof,
        "expected_days": expected_days,
        "gap_days": gap_days,
        "max_consecutive_gap_days": max_gap,
        "last_check_gap_days": last_check_gap_days,
        "changed_count": changed_count,
        "first_seen_count": first_seen_count,
        "failed_count": failed_count,
        "quality_drop_count": quality_drop_count,
        "degraded": degraded,
        "change_state": change_state,
        "continuity_status": continuity_status,
        "last_change_status": last_change_status,
        "last_proof_hash": last_proof_hash,
        "gap_disclosure": gap_disclosure,
        "degraded_reasons": degraded_reasons[:5],
    }


def _gap_disclosure(
    *,
    change_state: str,
    continuity_status: str,
    gap_days: int,
    max_gap: int,
    failed_count: int,
    quality_drop_count: int,
    skipped_cycles: int,
    last_check_gap_days: int,
    degraded_reasons: list[str],
) -> str:
    """Plain-English, honest per-source gap statement (no over-promise)."""
    skipped_sentence = (
        f"{skipped_cycles} monitoring cycle(s) were skipped and the source was not fetched "
        f"(recorded in the evidence trail); those cycles are not counted as checks."
        if skipped_cycles
        else ""
    )
    if continuity_status == "NO_COVERAGE":
        text = (
            "No successful check with a proof hash was recorded for this source during the period. "
            "Treat this source as UNVERIFIED for the period and review it directly."
        )
        return f"{text} {skipped_sentence}".strip() if skipped_sentence else text
    parts: list[str] = []
    if gap_days > 0:
        parts.append(
            f"{gap_days} day(s) in the period have no recorded proof-hash check "
            f"(longest uninterrupted gap: {max_gap} day(s))."
        )
    if failed_count:
        parts.append(f"{failed_count} check(s) FAILED and produced no usable content.")
    if quality_drop_count:
        parts.append(
            f"{quality_drop_count} check(s) recorded a quality drop; extraction may need manual review."
        )
    if skipped_sentence:
        parts.append(skipped_sentence)
    if last_check_gap_days > 0:
        parts.append(
            f"The last recorded check trails the end of the period by {last_check_gap_days} day(s)."
        )
    if not parts:
        return (
            "A proof-hash check was recorded on every day of the period; no gaps or degraded "
            "checks were recorded for this source, within the limits described in the disclaimer."
        )
    return " ".join(parts)


# ── certificate builder ────────────────────────────────────────────────────────

def build_coverage_certificate(
    *,
    period_start: str,
    period_end: str,
    source_ids: list[str] | None = None,
    client_name: str = "",
    base_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a negative-assurance coverage certificate for a period.

    Parameters
    ----------
    period_start, period_end:
        Inclusive ISO dates (``YYYY-MM-DD``). ``period_end`` must be >= start.
    source_ids:
        Sources to certify. ``None`` scopes the certificate to the customer's
        CONFIGURED source set (``enabled=True`` in ``sources.json``) unioned with
        any source that recorded a run in the period — so a configured source that
        went fully dark all period still surfaces as NO_COVERAGE rather than being
        silently omitted. Explicitly named sources with no runs in the period are
        likewise listed (as NO_COVERAGE) so gaps are never hidden.
    client_name:
        Optional customer name for the certificate header.
    base_dir:
        Artifact root (defaults to the repo root). Overridden in tests.
    now:
        Reference "now" for gap counting (defaults to current UTC). Future days
        beyond ``now`` are never counted as gaps.

    Returns
    -------
    dict
        Machine-readable certificate. Deterministic given the same evidence,
        period, source set, and ``now``.
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
    end_effective_date = min(end_date, reference_now.date())
    expected_days = max(0, (end_effective_date - start_date).days + 1) if end_effective_date >= start_date else 0

    runs_by_source = _load_runs_by_source(root)
    sources = _load_sources(root)

    ran_in_period = {
        sid
        for sid, runs in runs_by_source.items()
        if any(
            (ts := _run_ts(run)) is not None and start_dt <= ts <= end_dt
            for run in runs
        )
    }
    if source_ids:
        target_ids = [str(sid).strip() for sid in source_ids if str(sid).strip()]
    else:
        # Default (customer) path: scope to the CONFIGURED/subscribed source set
        # so a source that went fully dark all period surfaces as NO_COVERAGE
        # instead of being silently omitted (negative assurance must never hide a
        # gap). Union with any source that actually recorded a run in the period
        # so nothing monitored is dropped either. When no sources.json is
        # configured, this collapses to the historical run-derived behaviour.
        configured = set(enabled_source_ids(root))
        target_ids = sorted(configured | ran_in_period)

    rows = [
        _source_continuity(
            source_id=sid,
            source=sources.get(sid, {}),
            runs=runs_by_source.get(sid, []),
            start_dt=start_dt,
            end_dt=end_dt,
            start_date=start_date,
            end_effective_date=end_effective_date,
            expected_days=expected_days,
        )
        for sid in target_ids
    ]
    rows.sort(key=lambda row: (row["change_state"] != "CHANGED", row["source_id"]))

    summary = _summary(rows)
    statement = _negative_assurance_statement(
        client_name=client_name,
        period_label=_period_label(start_date, end_date),
        summary=summary,
    )

    certificate = {
        "schema_version": "1.0",
        "document_type": "coverage_certificate",
        "assurance_type": "negative_assurance",
        "customer_facing": True,
        "generated_at_utc": _utc_now(reference_now),
        "client_name": client_name,
        "period_label": _period_label(start_date, end_date),
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "period_days": expected_days,
        "summary": summary,
        "sources": rows,
        "negative_assurance_statement": statement,
        "disclaimer": _FULL_CERTIFICATE_DISCLAIMER,
        "disclaimer_short": LEGAL_DISCLAIMER,
    }
    certificate["certificate_id"] = _certificate_id(certificate)
    certificate["content_hash"] = _content_hash(certificate)
    return certificate


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sources_total": len(rows),
        "sources_changed": sum(1 for r in rows if r["change_state"] == "CHANGED"),
        "sources_unchanged_with_proof": sum(1 for r in rows if r["change_state"] == "UNCHANGED"),
        "sources_no_coverage": sum(1 for r in rows if r["change_state"] == "NO_PROOF"),
        "sources_with_gaps": sum(1 for r in rows if r["gap_days"] > 0),
        "sources_degraded": sum(1 for r in rows if r["degraded"]),
        "sources_continuous": sum(1 for r in rows if r["continuity_status"] == "CONTINUOUS"),
        "total_checks": sum(r["checks_in_period"] for r in rows),
        "total_skipped_cycles": sum(r.get("skipped_cycles", 0) for r in rows),
        "total_successful_checks": sum(r["successful_checks"] for r in rows),
        "total_days_with_proof_hash": sum(r["days_with_proof_hash"] for r in rows),
    }


def _negative_assurance_statement(
    *, client_name: str, period_label: str, summary: dict[str, Any]
) -> str:
    who = f" for {client_name}" if client_name else ""
    total = summary["sources_total"]
    checks = summary["total_checks"]
    changed = summary["sources_changed"]
    unchanged = summary["sources_unchanged_with_proof"]

    lead = (
        f"This coverage certificate records the official-source monitoring checks StatuteProof "
        f"performed{who} during {period_label}. StatuteProof performed {checks} recorded check(s) "
        f"across {total} monitored source(s). Of these, {changed} source(s) had at least one "
        f"detected content change during the period, and {unchanged} source(s) were checked with "
        f"no detected change on the days checked (each source's proof hashes and check dates are "
        f"listed below)."
    )

    gaps = summary["sources_with_gaps"]
    degraded = summary["sources_degraded"]
    no_cover = summary["sources_no_coverage"]
    flagged = gaps or degraded or no_cover
    if flagged:
        gap_sentence = (
            f" {gaps} source(s) show one or more days without a recorded proof-hash check, "
            f"{degraded} source(s) recorded a failed or degraded check, and {no_cover} source(s) "
            f"had no successful check in the period. These gaps are disclosed in the per-source "
            f"table below and should be reviewed."
        )
    else:
        gap_sentence = (
            " No coverage gaps, failed checks, or degraded checks were recorded for the monitored "
            "sources during this period, within the limits described in the disclaimer below."
        )

    boundary = (
        " This certificate states only what was checked and which gaps exist in the recorded "
        "evidence. It does not assert that every regulatory update was captured, and it is not a "
        "compliance certification, a legal opinion, or a substitute for professional advice from "
        "qualified legal or compliance advisers. Review the underlying evidence records, hashes, "
        "and timestamps, and verify official sources directly before relying on this certificate. "
        "See the full disclaimer below."
    )
    return lead + gap_sentence + boundary


def _certificate_id(certificate: dict[str, Any]) -> str:
    """Deterministic id over the period, client, and each source's proof state.

    Excludes generated_at_utc so re-issuing an identical certificate for the same
    evidence yields the same id (a stable reference for the customer/audit).
    """
    seed_parts = [
        certificate["period_start"],
        certificate["period_end"],
        certificate.get("client_name") or "",
    ]
    for row in certificate["sources"]:
        seed_parts.append(
            "|".join(
                [
                    row["source_id"],
                    str(row["successful_checks"]),
                    str(row["days_with_proof_hash"]),
                    str(row["gap_days"]),
                    row["change_state"],
                    row["last_proof_hash"],
                ]
            )
        )
    seed = "\n".join(seed_parts)
    return "cov-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]


def _assert_hashable_types(value: Any, path: str = "certificate") -> None:
    """Guard: every leaf in the sealed certificate subset must be str/int/bool/None.

    ``canonical_record_hash`` only rejects NON-finite floats (NaN/Infinity); a
    FINITE float would serialize fine there but its ``repr`` is not guaranteed
    byte-identical across languages, so an independent auditor (jq/Go/JS) could not
    reproduce the digest — a silently unverifiable seal. Refuse to seal instead.
    ``bool`` is a subclass of ``int`` and is allowed; a genuine certificate carries
    only strings, ints, bools, and null, so this guard holds without coercion.
    """
    if value is None or isinstance(value, (str, bool, int)):
        # bool/int both caught here; a float is NOT an int subclass, so it falls through.
        return
    if isinstance(value, dict):
        for key, sub in value.items():
            _assert_hashable_types(sub, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, sub in enumerate(value):
            _assert_hashable_types(sub, f"{path}[{index}]")
        return
    raise TypeError(
        f"Coverage certificate field {path} has non-sealable type "
        f"{type(value).__name__!r}; the content_hash seal requires str/int/bool/null only "
        "(floats are forbidden — their repr is not reproducible across languages)."
    )


def _content_hash(certificate: dict[str, Any]) -> str:
    """Full-document self-seal over the WHOLE certificate.

    Unlike :func:`_certificate_id` (which hashes only a fixed subset of fields and
    is kept unchanged for back-compat), this covers every field — the
    ``negative_assurance_statement`` prose, the disclaimer, and each row's
    ``continuity_status`` / ``degraded`` / ``last_check_utc`` / ``checks_in_period``
    — so altering any of them changes the seal. Excludes ``generated_at_utc`` (so an
    identical re-issue for the same evidence seals identically) and ``content_hash``
    itself. Reuses the shared ``canonical_record_hash`` so the public verifier
    (:mod:`app.public_verify`) recomputes the SAME digest.
    """
    sealed = {
        key: value
        for key, value in certificate.items()
        if key not in ("generated_at_utc", "content_hash")
    }
    _assert_hashable_types(sealed)
    return "sha256:" + canonical_record_hash(sealed)


def _utc_now(now: datetime) -> str:
    return now.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ── rendering ──────────────────────────────────────────────────────────────────

_CONTINUITY_LABEL = {
    "CONTINUOUS": "Continuous",
    "PARTIAL": "Partial — gap disclosed",
    "NO_COVERAGE": "No coverage",
}
_CHANGE_LABEL = {
    "CHANGED": "Change detected",
    "UNCHANGED": "No change on days checked",
    "NO_PROOF": "No proof this period",
}


def render_coverage_certificate_markdown(certificate: dict[str, Any]) -> str:
    """Render the certificate as customer-facing Markdown (legal-safe)."""
    summary = certificate.get("summary") if isinstance(certificate.get("summary"), dict) else {}
    rows = certificate.get("sources") if isinstance(certificate.get("sources"), list) else []

    lines: list[str] = [
        f"# Coverage Certificate — {certificate.get('period_label', 'Unknown period')}",
        "",
        "_Negative-assurance monitoring coverage record._",
        "",
    ]
    if certificate.get("client_name"):
        lines.append(f"**Client:** {certificate['client_name']}")
    lines.append(f"**Certificate ID:** {certificate.get('certificate_id', '')}")
    lines.append(f"**Period:** {certificate.get('period_start', '')} to {certificate.get('period_end', '')}")
    lines.append(f"**Generated:** {certificate.get('generated_at_utc', '')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Negative-assurance statement
    lines += ["## Coverage Statement", "", certificate.get("negative_assurance_statement", ""), ""]

    # Summary table
    lines += [
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Sources in this certificate | {summary.get('sources_total', 0)} |",
        f"| Sources with a detected change | {summary.get('sources_changed', 0)} |",
        f"| Sources checked, no detected change | {summary.get('sources_unchanged_with_proof', 0)} |",
        f"| Sources with no successful check | {summary.get('sources_no_coverage', 0)} |",
        f"| Sources with one or more gap days | {summary.get('sources_with_gaps', 0)} |",
        f"| Sources with a failed/degraded check | {summary.get('sources_degraded', 0)} |",
        f"| Total recorded checks | {summary.get('total_checks', 0)} |",
        f"| Cycles skipped, source not fetched | {summary.get('total_skipped_cycles', 0)} |",
        f"| Total days with a proof hash | {summary.get('total_days_with_proof_hash', 0)} |",
        "",
    ]

    # Per-source continuity table
    lines += [
        "## Per-Source Continuity",
        "",
        "| Source | Official URL | Checks | First check | Last check | Days w/ proof | Gap days | Status | Result |",
        "|--------|--------------|-------:|-------------|------------|--------------:|---------:|--------|--------|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("source_name") or row.get("source_id")),
                    _md_cell(row.get("official_url") or "—"),
                    str(row.get("checks_in_period", 0)),
                    _md_cell(row.get("first_check_utc") or "—"),
                    _md_cell(row.get("last_check_utc") or "—"),
                    str(row.get("days_with_proof_hash", 0)),
                    str(row.get("gap_days", 0)),
                    _CONTINUITY_LABEL.get(row.get("continuity_status", ""), row.get("continuity_status", "")),
                    _CHANGE_LABEL.get(row.get("change_state", ""), row.get("change_state", "")),
                ]
            )
            + " |"
        )
    lines.append("")

    # Gap disclosure detail — never hide a gap.
    flagged = [
        r for r in rows
        if r.get("gap_days", 0) > 0
        or r.get("degraded")
        or r.get("skipped_cycles", 0) > 0
        or r.get("change_state") == "NO_PROOF"
    ]
    lines += ["## Gap & Degradation Disclosure", ""]
    if flagged:
        for row in flagged:
            lines.append(
                f"- **{_md_cell(row.get('source_name') or row.get('source_id'))}** "
                f"({_CONTINUITY_LABEL.get(row.get('continuity_status', ''), '')}): "
                f"{row.get('gap_disclosure', '')}"
            )
    else:
        lines.append(
            "- No coverage gaps, failed checks, or degraded checks were recorded for the sources in this "
            "certificate during this period, within the limits described in the disclaimer."
        )
    lines.append("")

    # Guard the GENERATED body only; the standard disclaimer is a vetted constant
    # that legitimately negates banned phrases ("does not guarantee compliance").
    body = "\n".join(lines)
    _assert_legal_safe(body)
    disclaimer = certificate.get("disclaimer", _FULL_CERTIFICATE_DISCLAIMER)
    return f"{body}\n---\n\n**Disclaimer:** {disclaimer}\n"


def _md_cell(value: Any) -> str:
    """Escape pipe characters so a value cannot break the Markdown table."""
    return str(value if value is not None else "").replace("|", "\\|")


def render_coverage_certificate_html(certificate: dict[str, Any]) -> str:
    """Render the certificate as a standalone HTML document (legal-safe)."""
    # Reuse the assurance report's Markdown→HTML converter (DRY) so the
    # certificate shares the same table/paragraph styling.
    from app.monthly_assurance_report import _markdown_to_html

    # render_coverage_certificate_markdown already guards the generated body; the
    # conversion is mechanical, so the derived HTML inherits that guarantee. The
    # full doc is not re-guarded because it embeds the vetted disclaimer.
    markdown = render_coverage_certificate_markdown(certificate)
    return _markdown_to_html(
        markdown, title=f"Coverage Certificate — {certificate.get('period_label', '')}"
    )


# ── file exports ────────────────────────────────────────────────────────────────

def _default_stem(certificate: dict[str, Any]) -> str:
    return f"coverage_certificate_{certificate.get('period_start', '')}_{certificate.get('period_end', '')}"


def export_coverage_certificate_json(
    certificate: dict[str, Any], output_path: Path | None = None
) -> Path:
    """Write the machine-readable certificate JSON. Returns the path."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = output_path or (_REPORTS_DIR / f"{_default_stem(certificate)}.json")
    # Guard the human-readable strings inside the JSON payload too.
    _assert_legal_safe(certificate.get("negative_assurance_statement", ""))
    path.write_text(
        json.dumps(certificate, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    return path.resolve()


def export_coverage_certificate_html(
    certificate: dict[str, Any], output_path: Path | None = None
) -> Path:
    """Write the certificate HTML. Returns the path."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = output_path or (_REPORTS_DIR / f"{_default_stem(certificate)}.html")
    path.write_text(render_coverage_certificate_html(certificate), encoding="utf-8")
    return path.resolve()


def generate_coverage_certificate_pdf(
    certificate: dict[str, Any], output_path: Path | None = None
) -> Path:
    """Render the certificate as PDF via Playwright, falling back to HTML.

    Returns the path to the generated file (PDF, or an .html fallback when
    Playwright is unavailable — mirrors generate_monthly_report_pdf).
    """
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = output_path or (_REPORTS_DIR / f"{_default_stem(certificate)}.pdf")
    html_doc = render_coverage_certificate_html(certificate)
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.set_content(html_doc, wait_until="networkidle")
            page.pdf(
                path=str(path),
                format="A4",
                print_background=True,
                margin={"top": "18mm", "right": "14mm", "bottom": "18mm", "left": "14mm"},
            )
            browser.close()
        return path.resolve()
    except Exception as exc:
        logger.warning(
            "generate_coverage_certificate_pdf: Playwright unavailable (%s), writing HTML fallback",
            exc,
        )
        html_path = path.with_suffix(".html")
        html_path.write_text(html_doc, encoding="utf-8")
        return html_path.resolve()
