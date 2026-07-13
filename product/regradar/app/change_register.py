"""Regulatory Change Register — one structured export of every detected change.

This module is pure assembly. It introduces **no new data model**: it joins the
canonical evidence records (``app.evidence_records.list_canonical_evidence_records``),
the human Acknowledge & Assess notes (``app.evidence_assessment.latest_assessment_for``),
and the alert action decisions (``app.alert_actions.get_action_log`` — act / monitor /
no_action) into one table and renders it as CSV, XLSX, and HTML.

Legal-safety contract (mandatory):

* Every customer-facing render carries the standard disclaimer
  (``LEGAL_DISCLAIMER``).
* The forbidden-claims guard reused from
  ``app.monthly_assurance_report._FORBIDDEN_PHRASES`` runs over every rendered
  output; a match raises before the bytes can leave the process.
* Rows are **evidence-grounded**: each field is copied from a real canonical
  evidence record, a human assessment, or an action-log decision. Nothing is
  invented, nothing is phrased as advice or a guarantee, and every row carries
  a proof reference (the canonical ``evidence-record.json`` path + hash).
"""

from __future__ import annotations

import csv
import html
import io
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.alert_actions import get_action_log
from app.evidence_assessment import LEGAL_DISCLAIMER, latest_assessment_for
from app.evidence_records import (
    EvidenceRecordError,
    latest_canonical_evidence_review,
    list_canonical_evidence_records,
    load_evidence_record,
)
from app.monthly_assurance_report import _FORBIDDEN_PHRASES

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent
_REGISTER_TITLE = "StatuteProof Regulatory Change Register"
# DoS width cap for a register export when both bounds are supplied. Matches the
# audit-vault cap so the two paid exports impose the same per-request ceiling.
MAX_REGISTER_RANGE_DAYS = 366
# DoS record cap (mirrors app.evidence_pack.MAX_EVIDENCE_PACK_RECORDS): the
# register join is O(N×M) — it loads every canonical evidence-record.json and,
# per record, re-reads the whole run-log risk index plus assessment/action-log
# joins. The date-range width cap above does not bound record COUNT (a dense
# tree can hold thousands of records inside a single day), so cap the number of
# canonical records a single export will walk. Over-cap requests are REJECTED
# with a clear message (narrow the filters), never silently truncated — a
# partial register that looks complete is a worse failure than a refused one.
# Kept in step with app.effective_dates._MAX_RECORDS_SCANNED, which bounds the
# same evidence tree for the sibling key-dates view.
MAX_REGISTER_RECORDS = 5000
_NOT_SCORED = "NOT_SCORED"
_EMPTY_CELL = "—"

# Ordered (row-key, display header) pairs. This single spec drives the column
# order and headers for CSV, XLSX, and HTML so the three renders never drift.
_COLUMNS: tuple[tuple[str, str], ...] = (
    ("date", "Date"),
    ("source_name", "Source"),
    ("regulator_code", "Regulator"),
    ("change_summary", "Change summary"),
    ("normalized_hash", "Normalized hash"),
    ("risk_level", "Risk level"),
    ("reviewer", "Reviewer"),
    ("impact_action", "Impact / action decision"),
    ("next_action", "Next action"),
    ("status", "Status"),
    ("proof_reference", "Proof reference"),
)

# Type alias for the action-log lookup so it can be injected in tests without
# touching the global monitoring DB.
ActionLogLookup = Callable[[int, str], list[dict[str, Any]]]


class ChangeRegisterError(ValueError):
    """Raised when a rendered change register would contain a forbidden claim."""


class ChangeRegisterTooLargeError(ValueError):
    """Raised when a register export would exceed ``MAX_REGISTER_RECORDS`` records.

    Distinct from :class:`ChangeRegisterError` (a legal-safety guard) so the
    export layer can return a clear "narrow your filters" message instead of a
    generic failure — and so a caller can tell a size rejection apart from a
    forbidden-claim rejection. Never results in a partial/truncated register.
    """


# ── date-range validation (register-specific: lenient, optional bounds) ────────

def validate_register_date_range(date_from: str, date_to: str) -> tuple[bool, str]:
    """Validate an *optional* YYYY-MM-DD range for the register.

    Either bound may be empty (unbounded on that side). When both are given,
    ``date_from`` must not be after ``date_to`` and the range must not span more
    than ``MAX_REGISTER_RANGE_DAYS`` days (a DoS guard). This is deliberately
    more lenient than the audit-vault validator: a change register is an
    "export everything in scope" artifact, so future/past window caps are not
    imposed here — only the width cap when both bounds are supplied.
    """
    d_from = _parse_optional_date(date_from)
    if d_from is False:
        return False, f"date_from '{date_from}' is not a valid YYYY-MM-DD date."
    d_to = _parse_optional_date(date_to)
    if d_to is False:
        return False, f"date_to '{date_to}' is not a valid YYYY-MM-DD date."
    if isinstance(d_from, date) and isinstance(d_to, date):
        if d_from > d_to:
            return False, "date_from must not be after date_to."
        # DoS width cap: only enforceable when BOTH bounds are given (an
        # unbounded side stays unbounded, matching the register's lenient shape).
        if (d_to - d_from).days > MAX_REGISTER_RANGE_DAYS:
            return False, f"Date range must not exceed {MAX_REGISTER_RANGE_DAYS} days per request."
    return True, ""


def _parse_optional_date(value: str) -> date | None | bool:
    """Return a date, ``None`` for empty, or ``False`` for an invalid string."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return False


# ── row assembly (the join) ───────────────────────────────────────────────────

def build_change_register_rows(
    *,
    user_id: int | None = None,
    date_from: str = "",
    date_to: str = "",
    source_id: str = "",
    regulator: str = "",
    base_dir: Path | None = None,
    review_file: Path | None = None,
    action_log_lookup: ActionLogLookup | None = None,
    excluded_source_ids: set[str] | None = None,
    org_id: Any = None,
) -> list[dict[str, Any]]:
    """Assemble one register row per canonical evidence record.

    The join, per record:

    * canonical evidence record → date, source, regulator, change summary,
      normalized hash, proof reference, run/review status;
    * latest human assessment (``latest_assessment_for``) → reviewer, impact
      level, next action;
    * alert action log (``get_action_log`` scoped to ``user_id``) → the
      act / monitor / no_action decision.

    ``source_id`` / ``regulator`` filter the rows; the date range filters on the
    evidence record's run timestamp. ``excluded_source_ids`` is a tenancy guard:
    rows whose ``source_id`` is in that set are dropped *unconditionally* — even
    when no ``source_id`` filter is supplied — so a default (unscoped) export can
    never surface another customer's private custom source. Never raises for a
    single bad record — an unreadable record is skipped so one corrupt file
    cannot break the export.
    """
    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    lookup = action_log_lookup if action_log_lookup is not None else get_action_log

    # Record-count cap FIRST (before the per-record joins and even the run-log
    # risk-index read): materialize the lightweight summary list and refuse an
    # oversize export outright rather than doing — or worse, silently truncating
    # — an unbounded O(N×M) walk. Never truncates: a partial register that looks
    # complete would be a legal-safety hazard in an evidence product.
    summaries = list_canonical_evidence_records(base_dir=root, review_file=review_file)
    if len(summaries) > MAX_REGISTER_RECORDS:
        raise ChangeRegisterTooLargeError(
            f"This change register would span {len(summaries)} evidence records, "
            f"over the {MAX_REGISTER_RECORDS}-record per-export cap. Narrow the "
            f"date range, source, or regulator filter and export again. No partial "
            f"register was produced."
        )

    run_risk_index = _build_run_risk_index(root)

    from_bound = _parse_optional_date(date_from)
    to_bound = _parse_optional_date(date_to)
    source_filter = str(source_id or "").strip()
    regulator_filter = str(regulator or "").strip().lower()
    excluded = {str(s).strip() for s in (excluded_source_ids or set()) if str(s).strip()}

    rows: list[dict[str, Any]] = []
    for summary in summaries:
        record = _load_full_record(summary, root)
        if record is None:
            continue

        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        run = record.get("run") if isinstance(record.get("run"), dict) else {}
        content = record.get("content") if isinstance(record.get("content"), dict) else {}
        change = record.get("change") if isinstance(record.get("change"), dict) else {}
        review = record.get("review") if isinstance(record.get("review"), dict) else {}

        record_id = str(record.get("record_id") or summary.get("record_id") or "").strip()
        run_id = str(run.get("run_id") or summary.get("run_id") or "").strip()
        timestamp = str(run.get("timestamp") or "").strip()
        row_source_id = str(source.get("source_id") or "").strip()

        # Filters ---------------------------------------------------------------
        # Tenancy exclusion first: a custom source the caller does not own must
        # never appear, regardless of the (optional) source_id / regulator filter.
        if row_source_id and row_source_id in excluded:
            continue
        if source_filter and row_source_id != source_filter:
            continue
        if regulator_filter:
            reg_value = str(source.get("regulator") or "").strip().lower()
            if reg_value != regulator_filter:
                continue
        if not _in_date_range(timestamp, from_bound, to_bound):
            continue

        # Human assessment join (assessments are keyed by run_id; fall back to
        # record_id in case a reviewer assessed by the canonical id) -----------
        # Forward org_id unconditionally: an unresolved caller (org_id=None) must
        # scope to the empty legacy bucket (isolate), never fall back to
        # _NO_ORG_FILTER, which would leak another tenant's impact/reviewer/
        # next_action into this downloadable CSV/XLSX/HTML register.
        assessment = (
            latest_assessment_for(run_id, base_dir=root, org_id=org_id) if run_id else None
        ) or (
            latest_assessment_for(record_id, base_dir=root, org_id=org_id) if record_id else None
        ) or {}

        # Action-log decision join (scoped to the requesting client) -----------
        # A customer's act/monitor/no_action decision is stored under the alert
        # DRAFT id (app.alert_drafts.make_draft_alert_id), NOT under record_id or
        # run_id. Re-derive that draft id from this record's (source_id, run_id,
        # normalized_hash) so the join actually matches; keep record_id/run_id as
        # extra fallbacks in case a decision was ever logged against them.
        draft_alert_id = _draft_alert_id_for_record(
            source_id=str(source.get("source_id") or "").strip(),
            run_id=run_id,
            normalized_hash=str(content.get("current_hash") or "").strip(),
        )
        action_decision = _latest_action_decision(
            lookup, user_id, [draft_alert_id, record_id, run_id]
        )

        canonical_review = (
            latest_canonical_evidence_review(record_id, base_dir=root, review_file=review_file)
            if record_id
            else None
        ) or {}

        impact_level = str(assessment.get("impact_level") or "").strip()
        reviewer = (
            str(assessment.get("reviewer_name") or "").strip()
            or str(canonical_review.get("reviewer") or "").strip()
        )

        rows.append(
            {
                "date": timestamp,
                "source_name": str(source.get("source_name") or source.get("source_id") or "").strip(),
                "source_id": str(source.get("source_id") or "").strip(),
                "regulator_code": str(source.get("regulator") or "").strip(),
                "official_url": str(source.get("official_url") or "").strip(),
                "change_summary": str(change.get("summary") or "").strip(),
                "normalized_hash": str(content.get("current_hash") or "").strip(),
                "risk_level": run_risk_index.get(run_id, _NOT_SCORED) or _NOT_SCORED,
                "reviewer": reviewer,
                "impact_level": impact_level,
                "action_decision": action_decision,
                "impact_action": _format_impact_action(impact_level, action_decision),
                "next_action": str(assessment.get("next_action") or "").strip(),
                "status": _resolve_status(summary, review, assessment, run, record),
                "record_id": record_id,
                "run_id": run_id,
                "record_status": str(record.get("record_status") or "").strip(),
                "proof_reference": _proof_reference(summary, record_id),
                "diff_path": str(change.get("diff_path") or "").strip(),
            }
        )

    rows.sort(key=lambda r: (r.get("date") or "", r.get("record_id") or ""), reverse=True)
    return rows


def _load_full_record(summary: dict[str, Any], root: Path) -> dict[str, Any] | None:
    """Load the full evidence-record.json for a list summary row, or None."""
    key = str(summary.get("record_path") or summary.get("record_id") or "").strip()
    if not key:
        return None
    try:
        record, _ = load_evidence_record(key, base_dir=root)
        return record
    except EvidenceRecordError:
        # Fall back to the record_id if the path lookup failed for any reason.
        record_id = str(summary.get("record_id") or "").strip()
        if record_id and record_id != key:
            try:
                record, _ = load_evidence_record(record_id, base_dir=root)
                return record
            except EvidenceRecordError:
                return None
        return None


def _build_run_risk_index(root: Path) -> dict[str, str]:
    """Best-effort map of run_id → risk_level from saved source runs.

    Read-only enrichment. The canonical evidence record does not carry a risk
    score, so we surface a risk level only when the monitoring pipeline actually
    computed and stored one for that run. Absent → ``NOT_SCORED`` (never
    invented). Never raises.
    """
    index: dict[str, str] = {}
    runs_path = root / "data" / "source_runs" / "source_runs.jsonl"
    if not runs_path.exists():
        return index
    try:
        for line in runs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            run_id = str(row.get("run_id") or "").strip()
            risk = str(row.get("risk_level") or "").strip()
            if run_id and risk:
                index[run_id] = risk.upper()
    except OSError as exc:  # pragma: no cover - defensive
        logger.warning("change register risk index read failed: %s", exc)
    return index


def _draft_alert_id_for_record(
    *, source_id: str, run_id: str, normalized_hash: str
) -> str:
    """Re-derive the dashboard's real alert id for a canonical evidence record.

    The alert draft id is seeded from the BARE normalized hash the monitoring
    pipeline stored on the run (``app.alert_drafts.make_draft_alert_id`` →
    ``sha256(source_id|run_id|normalized_hash)``). The canonical record persists
    that same hash as ``content.current_hash`` in ``sha256:<hex>`` form, so the
    ``sha256:`` prefix is stripped before re-deriving — otherwise the id never
    matches the one the action log is keyed by. Returns ``""`` when any input is
    missing (the caller then falls back to record_id / run_id).
    """
    if not (source_id and run_id and normalized_hash):
        return ""
    bare_hash = normalized_hash.removeprefix("sha256:").strip()
    if not bare_hash:
        return ""
    from app.alert_drafts import make_draft_alert_id

    return make_draft_alert_id(source_id, run_id, bare_hash)


def _latest_action_decision(
    lookup: ActionLogLookup,
    user_id: int | None,
    alert_ids: list[str],
) -> str:
    """Return the most recent act/monitor/no_action decision for this record.

    ``get_action_log`` is scoped to ``(user_id, alert_id)``, so the decision is
    always the requesting client's own review action. Returns "" when there is
    no user context or no logged decision.
    """
    if user_id is None:
        return ""
    best_decision = ""
    best_created = ""
    seen: set[str] = set()
    for alert_id in alert_ids:
        aid = str(alert_id or "").strip()
        if not aid or aid in seen:
            continue
        seen.add(aid)
        try:
            entries = lookup(int(user_id), aid)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("change register action-log lookup failed: %s", exc)
            continue
        for entry in entries or []:
            created = str(entry.get("created_at") or "")
            if created >= best_created:
                best_created = created
                best_decision = str(entry.get("decision") or "").strip()
    return best_decision


def _format_impact_action(impact_level: str, action_decision: str) -> str:
    impact = impact_level.strip() or _EMPTY_CELL
    action = action_decision.strip() or _EMPTY_CELL
    return f"impact: {impact} / action: {action}"


def _resolve_status(
    summary: dict[str, Any],
    review: dict[str, Any],
    assessment: dict[str, Any],
    run: dict[str, Any],
    record: dict[str, Any],
) -> str:
    """Pick the most authoritative workflow status available for the row."""
    for candidate in (
        summary.get("latest_review_decision"),
        review.get("review_status"),
        summary.get("record_review_status"),
        assessment.get("assessment_status"),
        record.get("record_status"),
        run.get("status"),
    ):
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


def _proof_reference(summary: dict[str, Any], record_id: str) -> str:
    path = str(summary.get("record_path") or "").strip()
    if path and record_id:
        return f"{record_id} ({path})"
    return record_id or path


def _in_date_range(
    timestamp: str,
    from_bound: date | None | bool,
    to_bound: date | None | bool,
) -> bool:
    """Inclusive date-range test on an ISO run timestamp (date portion only)."""
    day = _timestamp_date(timestamp)
    if day is None:
        # No parseable date → only excluded when a bound is actually set.
        return not (isinstance(from_bound, date) or isinstance(to_bound, date))
    if isinstance(from_bound, date) and day < from_bound:
        return False
    if isinstance(to_bound, date) and day > to_bound:
        return False
    return True


def _timestamp_date(timestamp: str) -> date | None:
    text = str(timestamp or "").strip()
    if len(text) < 10:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


# ── forbidden-claims guard ─────────────────────────────────────────────────────

def assert_no_forbidden_claims(text: str) -> None:
    """Raise ``ChangeRegisterError`` if any forbidden phrase appears in ``text``.

    Reuses the exact ``_FORBIDDEN_PHRASES`` guard from the monthly assurance
    report so the register and the assurance report share one banned-claim list.

    The standard disclaimer legitimately *denies* forbidden claims — it contains
    "Not legal advice", which embeds the banned substring "legal advice". Like
    the monthly assurance report (which scans the content section only), the
    known-safe disclaimer text is neutralized before scanning so the disclaimer
    can never trip its own guard, while any *other* occurrence of a banned
    phrase in row content still raises.
    """
    lowered = str(text or "").lower().replace(LEGAL_DISCLAIMER.lower(), " ")
    hits = [phrase for phrase in _FORBIDDEN_PHRASES if phrase in lowered]
    if hits:
        raise ChangeRegisterError(
            "Change register output contains forbidden claim(s): " + ", ".join(sorted(hits))
        )


# ── metadata ───────────────────────────────────────────────────────────────────

def _register_meta(
    rows: list[dict[str, Any]],
    *,
    date_from: str,
    date_to: str,
    source_id: str,
    regulator: str,
) -> dict[str, str]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "row_count": str(len(rows)),
        "date_from": str(date_from or "").strip() or "(unbounded)",
        "date_to": str(date_to or "").strip() or "(unbounded)",
        "source_id": str(source_id or "").strip() or "(all)",
        "regulator": str(regulator or "").strip() or "(all)",
    }


# ── renderers ──────────────────────────────────────────────────────────────────

def render_change_register_csv(rows: list[dict[str, Any]], meta: dict[str, str]) -> str:
    """Render the register as CSV with a commented disclaimer preamble."""
    buf = io.StringIO()
    buf.write(f"# {_REGISTER_TITLE}\n")
    buf.write(f"# Disclaimer: {LEGAL_DISCLAIMER}\n")
    buf.write(
        "# Generated: {generated_at_utc} | Rows: {row_count} | "
        "Range: {date_from}..{date_to} | Source: {source_id} | "
        "Regulator: {regulator}\n".format(**meta)
    )
    writer = csv.writer(buf)
    writer.writerow([header for _, header in _COLUMNS])
    for row in rows:
        writer.writerow([_csv_safe(_cell(row, key)) for key, _ in _COLUMNS])
    text = buf.getvalue()
    assert_no_forbidden_claims(text)
    return text


def render_change_register_xlsx(rows: list[dict[str, Any]], meta: dict[str, str]) -> bytes:
    """Render the register as an XLSX workbook (bytes)."""
    from openpyxl import Workbook  # lazy import — only needed for XLSX
    from openpyxl.styles import Font

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Change Register"

    # The meta line carries free-form filter values (source_id / regulator), so
    # it MUST be guarded like every other cell — otherwise a forbidden phrase
    # injected via a filter ships in XLSX while CSV/HTML correctly raise.
    meta_line = (
        "Generated: {generated_at_utc} | Rows: {row_count} | "
        "Range: {date_from}..{date_to} | Source: {source_id} | "
        "Regulator: {regulator}".format(**meta)
    )
    guard_parts: list[str] = [_REGISTER_TITLE, LEGAL_DISCLAIMER, meta_line]
    worksheet.append([_REGISTER_TITLE])
    worksheet["A1"].font = Font(bold=True, size=14)
    worksheet.append([f"Disclaimer: {LEGAL_DISCLAIMER}"])
    worksheet.append([meta_line])
    worksheet.append([])

    header_row_idx = worksheet.max_row + 1
    worksheet.append([header for _, header in _COLUMNS])
    for cell in worksheet[header_row_idx]:
        cell.font = Font(bold=True)

    for row in rows:
        # openpyxl writes a string beginning with '=' (or +, -, @) as a live
        # FORMULA, so the same formula-injection guard the CSV renderer uses must
        # be applied here too — human-authored cells (reviewer notes, next action)
        # reach this export.
        values = [_csv_safe(_cell(row, key)) for key, _ in _COLUMNS]
        worksheet.append(values)
        guard_parts.extend(values)

    assert_no_forbidden_claims("\n".join(guard_parts))

    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def render_change_register_html(rows: list[dict[str, Any]], meta: dict[str, str]) -> str:
    """Render the register as a self-contained HTML document.

    The disclaimer appears in both the header banner and the footer legal
    boundary, and the forbidden-claims guard runs over the final markup.
    """
    header_cells = "".join(f"<th>{html.escape(header)}</th>" for _, header in _COLUMNS)
    if rows:
        body_rows = "\n".join(
            "<tr>"
            + "".join(f"<td>{html.escape(_cell(row, key))}</td>" for key, _ in _COLUMNS)
            + "</tr>"
            for row in rows
        )
    else:
        span = len(_COLUMNS)
        body_rows = (
            f'<tr><td class="empty" colspan="{span}">'
            "No detected changes match this range and filter. "
            "This register is empty but valid.</td></tr>"
        )

    meta_line = (
        "Generated {generated_at_utc} &middot; {row_count} row(s) &middot; "
        "Range {date_from} to {date_to} &middot; Source {source_id} &middot; "
        "Regulator {regulator}"
    ).format(**{k: html.escape(v) for k, v in meta.items()})

    doc = (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(_REGISTER_TITLE)}</title>"
        "<style>"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;"
        "line-height:1.5;max-width:1180px;margin:36px auto;padding:0 22px;color:#0b1524;}"
        "h1{border-bottom:3px solid #16d9f5;padding-bottom:10px;margin-bottom:6px;}"
        ".disclaimer{background:#eef7ff;border:1px solid #cfe6fb;border-radius:8px;"
        "padding:10px 14px;margin:14px 0;font-weight:600;color:#0b3a63;}"
        ".meta{color:#5a6b80;font-size:13px;margin:8px 0 18px;}"
        "table{border-collapse:collapse;width:100%;font-size:13px;}"
        "th,td{border:1px solid #d8dee6;padding:7px 9px;text-align:left;vertical-align:top;}"
        "th{background:#f3f6f9;font-weight:700;}"
        "tbody tr:nth-child(even){background:#fafcfe;}"
        "td.empty{text-align:center;color:#5a6b80;font-style:italic;padding:22px;}"
        "footer{margin-top:22px;padding-top:14px;border-top:1px solid #d8dee6;"
        "color:#5a6b80;font-size:12px;}"
        "</style></head><body>\n"
        f"<h1>{html.escape(_REGISTER_TITLE)}</h1>\n"
        f'<div class="disclaimer">{html.escape(LEGAL_DISCLAIMER)}</div>\n'
        f'<p class="meta">{meta_line}</p>\n'
        "<table><thead><tr>"
        f"{header_cells}"
        "</tr></thead><tbody>\n"
        f"{body_rows}\n"
        "</tbody></table>\n"
        "<footer>"
        f"{html.escape(LEGAL_DISCLAIMER)} "
        "This register is assembled from monitored official-source evidence records "
        "for internal compliance review. It does not determine legal obligations, "
        "certify compliance, or replace qualified legal or compliance advice. "
        "Verify each entry against its referenced evidence record before relying on it."
        "</footer>\n"
        "</body></html>\n"
    )
    assert_no_forbidden_claims(doc)
    return doc


def _cell(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None:
        return ""
    return str(value)


# CSV formula-injection triggers: a cell that begins with any of these is treated
# as a formula by Excel/Sheets/LibreOffice. Human-authored fields (reviewer notes,
# next actions) reach this export, so they must be neutralized.
_CSV_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    """Neutralize CSV formula injection by prefixing a formula-trigger cell with a
    single quote, so a spreadsheet renders it as text rather than executing it."""
    if value and value[0] in _CSV_FORMULA_TRIGGERS:
        return "'" + value
    return value


# ── top-level export (writes CSV + XLSX + HTML) ────────────────────────────────

def build_change_register_export(
    *,
    user_id: int | None = None,
    date_from: str = "",
    date_to: str = "",
    source_id: str = "",
    regulator: str = "",
    export_format: str = "all",
    base_dir: Path | None = None,
    output_dir: Path | None = None,
    review_file: Path | None = None,
    action_log_lookup: ActionLogLookup | None = None,
    excluded_source_ids: set[str] | None = None,
    org_id: Any = None,
) -> dict[str, Any]:
    """Build the register and write the requested formats to disk.

    ``export_format`` accepts ``csv``, ``xlsx``, ``html``, or ``all`` (default).
    An empty result set is not an error: it produces an empty-but-valid register
    (headers + disclaimer, zero data rows) so the caller always gets a file.

    Returns a status dict (never raises for expected conditions):
    ``{"status": "ok", "row_count": int, "exports": {...}, "disclaimer": str}``
    or ``{"status": "error", "message": str}``.
    """
    try:
        root = Path(base_dir) if base_dir is not None else _BASE_DIR
        requested = _requested_formats(export_format)
        if not requested:
            return {
                "status": "error",
                "message": "Unsupported format. Use csv, xlsx, html, or all.",
            }

        valid, err = validate_register_date_range(date_from, date_to)
        if not valid:
            return {"status": "error", "message": err}

        rows = build_change_register_rows(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            source_id=source_id,
            regulator=regulator,
            base_dir=root,
            review_file=review_file,
            action_log_lookup=action_log_lookup,
            excluded_source_ids=excluded_source_ids,
            org_id=org_id,
        )
        meta = _register_meta(
            rows,
            date_from=date_from,
            date_to=date_to,
            source_id=source_id,
            regulator=regulator,
        )

        out_dir = output_dir or (root / "reports" / "change_registers")
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        stem = f"change_register_{stamp}"

        exports: dict[str, str] = {}
        if "csv" in requested:
            csv_path = out_dir / f"{stem}.csv"
            csv_path.write_text(render_change_register_csv(rows, meta), encoding="utf-8")
            exports["csv_path"] = _rel(csv_path, root)
        if "html" in requested:
            html_path = out_dir / f"{stem}.html"
            html_path.write_text(render_change_register_html(rows, meta), encoding="utf-8")
            exports["html_path"] = _rel(html_path, root)
        if "xlsx" in requested:
            xlsx_path = out_dir / f"{stem}.xlsx"
            xlsx_path.write_bytes(render_change_register_xlsx(rows, meta))
            exports["xlsx_path"] = _rel(xlsx_path, root)

        return {
            "status": "ok",
            "row_count": len(rows),
            "exports": exports,
            "meta": meta,
            "disclaimer": LEGAL_DISCLAIMER,
            "message": (
                "Change register exported for internal compliance review."
                if rows
                else "No detected changes matched; an empty but valid register was exported."
            ),
        }
    except ChangeRegisterTooLargeError as exc:
        logger.warning("change register rejected (over record cap): %s", exc)
        return {"status": "error", "message": str(exc)}
    except ChangeRegisterError as exc:
        logger.error("change register blocked by forbidden-claims guard: %s", exc)
        return {"status": "error", "message": str(exc)}
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("build_change_register_export unexpected error: %s", exc)
        return {"status": "error", "message": "Failed to build change register."}


def _requested_formats(export_format: str) -> set[str]:
    fmt = str(export_format or "all").strip().lower()
    if fmt in {"", "all"}:
        return {"csv", "xlsx", "html"}
    wanted = {part.strip() for part in fmt.replace("+", ",").split(",") if part.strip()}
    allowed = {"csv", "xlsx", "html"}
    return wanted & allowed


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)
