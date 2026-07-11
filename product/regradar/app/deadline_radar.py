"""Effective-date & deadline radar.

Turns a concrete future date carried by a *real* detected change into a
persistent, deduplicated deadline record, and fires lead-time reminders
(30 / 7 / 1 days out) through the existing Telegram / email channels.

Design mirrors ``app.evidence_assessment`` (filesystem-backed JSONL, keyed by
``evidence_record_id``). It joins two pieces of already-proven data:

* ``app.risk.derive_urgency_and_dates`` — the concrete calendar date(s) a
  change carries, captured (not thrown away) from the diff text; and
* the caller's ``evidence_record_id`` (the source-run ``run_id`` used across the
  trail — the same key ``app.evidence_assessment`` records against).

Legal-safety contract (mandatory):

* **Evidence-grounded** — a deadline is persisted ONLY when it was extracted
  from a real diff/evidence excerpt AND carries a non-empty ``evidence_record_id``
  AND resolves to a concrete calendar date. Nothing is inferred; the exact diff
  excerpt is stored on every record so the date can be verified against the
  evidence trail.
* **Disclaimer** — every customer-facing reminder carries ``LEGAL_DISCLAIMER``.
* **No forbidden claims** — every rendered reminder is run through the shared
  forbidden-claims guard (``app.change_register.assert_no_forbidden_claims``)
  before any bytes can leave the process. Reminders describe *what changed / what
  you may wish to review*; they never give advice or promise an outcome.
"""

from __future__ import annotations

import calendar
import fcntl
import hashlib
import json
import logging
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.evidence_assessment import LEGAL_DISCLAIMER

logger = logging.getLogger(__name__)

# Honor STATUTEPROOF_BASE_DIR so the register lives alongside the source-run
# trail it keys off (app.source_runs resolves the same way). Callers may still
# override per-call via ``base_dir`` (used throughout the tests).
_BASE_DIR = Path(os.environ.get("STATUTEPROOF_BASE_DIR") or Path(__file__).parent.parent).resolve()
_REGISTER_DIRNAME = "deadline_register"

# Lead-time stages (days before the date) at which a reminder fires. Fired once
# per stage per deadline — see ``due_reminders``.
LEAD_STAGES: tuple[int, ...] = (30, 7, 1)

_ALLOWED_KINDS = frozenset({"effective", "consultation_close", "transition", "deadline"})
_OPEN_STATUSES = frozenset({"", "open"})

# Specificity ranking for de-duplication: one real-world date can match several
# capture patterns at once (e.g. "comments are due by 30 September 2026" hits both
# consultation_close AND the generic deadline pattern). When two captures resolve
# to the SAME calendar date we keep the most specific kind — a named lifecycle
# kind (consultation_close / effective / transition) always beats a bare
# "deadline" — so one date yields one record and one reminder per lead stage.
_KIND_SPECIFICITY = {
    "effective": 3,
    "consultation_close": 3,
    "transition": 3,
    "deadline": 1,
}


def _kind_specificity(kind: str) -> int:
    return _KIND_SPECIFICITY.get(str(kind or "").strip().lower(), 0)

_KIND_LABEL = {
    "effective": "effective date",
    "consultation_close": "consultation close",
    "transition": "transition end",
    "deadline": "deadline",
}

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}


# ── time helpers ──────────────────────────────────────────────────────────────

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_iso_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if len(text) < 10:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _parse_deadline_date(date_text: str) -> date | None:
    """Resolve a captured date span to a concrete calendar date, or ``None``.

    Handles the forms captured by ``app.risk._DL_DATE``: ``1 September 2026``,
    ``(end of) September 2026`` (resolved to the last day of the month),
    ``01/09/2026`` (day-first — the convention used across the monitored
    UK/DIFC/EU-style sources), and ISO ``2026-09-01``. Returns ``None`` for an
    impossible date (e.g. 31 February) so nothing invalid is ever persisted.
    """
    low = " ".join(str(date_text or "").split()).lower()
    if not low:
        return None

    end_of = low.startswith("end of ")
    if end_of:
        low = low[len("end of "):].strip()

    # ISO 2026-09-01
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", low)
    if m:
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # 1 September 2026
    m = re.fullmatch(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", low)
    if m and m.group(2) in _MONTHS:
        return _safe_date(int(m.group(3)), _MONTHS[m.group(2)], int(m.group(1)))

    # (end of) September 2026 — a bare month/year resolves to the last day of
    # the month: for a deadline that is the safe "by" interpretation, and for an
    # effective/consultation/transition month it is the concrete boundary date.
    m = re.fullmatch(r"([a-z]+)\s+(\d{4})", low)
    if m and m.group(1) in _MONTHS:
        year = int(m.group(2))
        month = _MONTHS[m.group(1)]
        last_day = calendar.monthrange(year, month)[1]
        return _safe_date(year, month, last_day)

    # 01/09/2026 or 01-09-2026 (day-first)
    m = re.fullmatch(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})", low)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        if year < 100:
            year += 2000
        # Day-first by convention; only swap when that is impossible but the
        # transposed reading is valid (e.g. a US-formatted 09/15/2026).
        if month > 12 and day <= 12:
            day, month = month, day
        return _safe_date(year, month, day)

    return None


# ── extraction (evidence-grounded) ────────────────────────────────────────────

def _is_ambiguous_numeric_date(date_text: str) -> bool:
    """True for a purely numeric ``d/m`` (or ``d-m``) form that is dd/mm↔mm/dd ambiguous.

    ``01/09/2026`` is read day-first by convention, but the very same digits are a
    valid month-first date, so a human should verify it against the source. A form
    where one component exceeds 12 (``15/09/2026``) is NOT ambiguous — only one
    reading is possible — and named-month / ISO forms are never ambiguous.
    """
    low = " ".join(str(date_text or "").split()).lower()
    m = re.fullmatch(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})", low)
    if not m:
        return False
    first, second = int(m.group(1)), int(m.group(2))
    return first <= 12 and second <= 12 and first != second


def extract_deadlines(diff_text: str) -> list[dict[str, Any]]:
    """Return concrete future-or-dated deadlines carried by the change text.

    Delegates date capture to ``app.risk.derive_urgency_and_dates`` (so the
    urgency ladder and the deadline radar never drift), then resolves each
    captured span to a concrete calendar date. Spans that do not resolve to a
    real date are dropped — nothing invented.

    Deduplicated on the RESOLVED calendar date (not on kind): a single real-world
    date that matches several patterns collapses to ONE entry, keeping the most
    specific kind (see ``_KIND_SPECIFICITY``). This is what stops one date from
    producing two deadline records — and therefore two reminders per lead stage.

    Each item::

        {"deadline_date": "YYYY-MM-DD", "deadline_kind": str,
         "extracted_from_diff_excerpt": str, "urgency": str, "date_text": str,
         "date_ambiguous": bool}
    """
    from app.risk import derive_urgency_and_dates

    _, captures = derive_urgency_and_dates(diff_text or "")
    # Dedupe so one phrase matching several patterns does not create duplicate
    # reminders, WITHOUT collapsing two genuinely distinct obligations that fall
    # on the same date. Rule: for each date keep every DISTINCT kind at the
    # highest specificity present, and drop only lower-specificity kinds (a bare
    # "deadline" folds into a co-located "effective"/"consultation_close", but an
    # "effective" date and a "consultation_close" date on the same day are two
    # separate records). Identical (date, kind) collapses to the first match.
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    max_spec_by_date: dict[str, int] = {}
    for cap in captures:
        date_text = cap.get("date_text", "")
        parsed = _parse_deadline_date(date_text)
        if parsed is None:
            continue
        iso = parsed.isoformat()
        kind = cap.get("kind", "deadline")
        key = (iso, kind)
        if key not in by_key:
            by_key[key] = {
                "deadline_date": iso,
                "deadline_kind": kind,
                "extracted_from_diff_excerpt": (cap.get("excerpt") or date_text or "").strip(),
                "urgency": cap.get("urgency", ""),
                "date_text": date_text,
                "date_ambiguous": _is_ambiguous_numeric_date(date_text),
            }
        max_spec_by_date[iso] = max(max_spec_by_date.get(iso, 0), _kind_specificity(kind))
    return [
        candidate
        for (iso, kind), candidate in by_key.items()
        if _kind_specificity(kind) >= max_spec_by_date[iso]
    ]


# ── register store (mirror of evidence_assessment.assessments.jsonl) ──────────

def deadline_register_path(base_dir: Path | None = None) -> Path:
    root = base_dir or _BASE_DIR
    return root / "data" / _REGISTER_DIRNAME / "deadlines.jsonl"


def deadline_reminders_path(base_dir: Path | None = None) -> Path:
    root = base_dir or _BASE_DIR
    return root / "data" / _REGISTER_DIRNAME / "reminders.jsonl"


def _deadline_id(evidence_record_id: str, deadline_date: str, deadline_kind: str) -> str:
    seed = f"{evidence_record_id}|{deadline_date}|{deadline_kind}"
    return "deadline-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def load_deadlines(base_dir: Path | None = None) -> list[dict[str, Any]]:
    return _load_jsonl(deadline_register_path(base_dir))


def record_deadline(
    *,
    evidence_record_id: str,
    deadline_date: str,
    deadline_kind: str,
    extracted_from_diff_excerpt: str,
    source_id: str = "",
    regulator: str = "",
    source_name: str = "",
    official_url: str = "",
    status: str = "open",
    date_text: str = "",
    date_ambiguous: bool = False,
    base_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Persist one evidence-grounded deadline; return it (or the existing dupe).

    Raises ``ValueError`` when the evidence-grounding contract is violated:
    a deadline MUST carry a non-empty ``evidence_record_id``, a real diff
    excerpt, a supported ``deadline_kind`` and a parseable ISO ``deadline_date``.

    Idempotent: a second call with the same ``(evidence_record_id, date, kind)``
    returns the already-stored record without appending a duplicate line.
    """
    ev_id = str(evidence_record_id or "").strip()
    if not ev_id:
        raise ValueError("evidence_record_id is required (deadline must be evidence-grounded)")

    excerpt = str(extracted_from_diff_excerpt or "").strip()
    if not excerpt:
        raise ValueError("extracted_from_diff_excerpt is required (deadline must be evidence-grounded)")

    kind = str(deadline_kind or "").strip().lower()
    if kind not in _ALLOWED_KINDS:
        raise ValueError(f"Unknown deadline_kind: {deadline_kind!r}")

    parsed = _parse_iso_date(deadline_date)
    if parsed is None:
        raise ValueError(f"deadline_date is not a valid calendar date: {deadline_date!r}")
    iso = parsed.isoformat()

    did = _deadline_id(ev_id, iso, kind)

    existing = next((row for row in load_deadlines(base_dir) if row.get("deadline_id") == did), None)
    if existing is not None:
        return existing

    detected_at = now_utc()
    record = {
        "deadline_id": did,
        "evidence_record_id": ev_id,
        "source_id": str(source_id or "").strip(),
        "source_name": str(source_name or "").strip(),
        "regulator": str(regulator or "").strip(),
        "official_url": str(official_url or "").strip(),
        "deadline_date": iso,
        "deadline_kind": kind,
        "extracted_from_diff_excerpt": excerpt,
        # Keep the raw captured text next to the parsed ISO date so the reminder
        # can show exactly what the source said, and flag numeric dd/mm↔mm/dd
        # forms for human verification (human_review_required is always set too).
        "raw_date_text": str(date_text or "").strip(),
        "date_ambiguous": bool(date_ambiguous),
        "status": str(status or "open").strip() or "open",
        "detected_at": detected_at,
        "human_review_required": True,
        "legal_disclaimer": LEGAL_DISCLAIMER,
    }
    _append_jsonl(deadline_register_path(base_dir), record)
    return record


def record_deadlines_for_change(
    *,
    evidence_record_id: str,
    source_id: str = "",
    regulator: str = "",
    source_name: str = "",
    official_url: str = "",
    added_blocks: list[Any] | None = None,
    diff_text: str = "",
    as_of: date | None = None,
    include_past: bool = False,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Extract deadlines from a change and persist the future ones.

    ``added_blocks`` (the ADDED side of the diff) or ``diff_text`` supplies the
    evidence-grounded text. Only concrete dates on/after ``as_of`` (today, UTC)
    are persisted unless ``include_past`` is set — a date already in the past is
    not an upcoming deadline. Never raises for expected conditions; a single bad
    record is skipped so one malformed date cannot break the pipeline.
    """
    text = diff_text or ""
    if added_blocks:
        text = "\n".join(str(b) for b in added_blocks if str(b).strip())
    if not text.strip():
        return []

    today = as_of or _today()
    persisted: list[dict[str, Any]] = []
    for item in extract_deadlines(text):
        dd = _parse_iso_date(item["deadline_date"])
        if dd is None:
            continue
        if not include_past and dd < today:
            continue
        try:
            record = record_deadline(
                evidence_record_id=evidence_record_id,
                deadline_date=item["deadline_date"],
                deadline_kind=item["deadline_kind"],
                extracted_from_diff_excerpt=item["extracted_from_diff_excerpt"],
                source_id=source_id,
                regulator=regulator,
                source_name=source_name,
                official_url=official_url,
                date_text=item.get("date_text", ""),
                date_ambiguous=bool(item.get("date_ambiguous")),
                base_dir=base_dir,
            )
        except ValueError as exc:
            logger.warning("deadline radar: skipped a date (%s)", exc)
            continue
        if record is not None:
            persisted.append(record)
    return persisted


def upcoming_deadlines(
    *,
    as_of: date | None = None,
    include_past: bool = False,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Return open deadlines with a ``days_until`` field, soonest first.

    Past deadlines are excluded unless ``include_past`` is set. Read-only.
    """
    today = as_of or _today()
    rows: list[dict[str, Any]] = []
    for entry in load_deadlines(base_dir):
        if str(entry.get("status") or "").strip().lower() not in _OPEN_STATUSES:
            continue
        dd = _parse_iso_date(entry.get("deadline_date"))
        if dd is None:
            continue
        days_until = (dd - today).days
        if not include_past and days_until < 0:
            continue
        rows.append({**entry, "days_until": days_until})
    rows.sort(key=lambda r: (r.get("deadline_date") or "", r.get("deadline_id") or ""))
    return rows


# ── reminders ─────────────────────────────────────────────────────────────────

def _reminded_stages(deadline_id: str, base_dir: Path | None = None) -> set[int]:
    stages: set[int] = set()
    for row in _load_jsonl(deadline_reminders_path(base_dir)):
        if row.get("deadline_id") == deadline_id:
            try:
                stages.add(int(row.get("lead_stage")))
            except (TypeError, ValueError):
                continue
    return stages


def due_reminders(
    *,
    as_of: date | None = None,
    lead_stages: tuple[int, ...] = LEAD_STAGES,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Open deadlines whose most-urgent lead stage is due and not yet fired.

    For a deadline ``d`` days out, the target stage is the SMALLEST configured
    stage ``S`` with ``d <= S`` (the most urgent applicable window). It fires
    once; the reminders log records the fired stage so it never re-fires, and a
    larger stage never fires after a smaller one has (target only shrinks as the
    date approaches). Past deadlines (``d < 0``) never fire.
    """
    today = as_of or _today()
    stages_asc = sorted(set(int(s) for s in lead_stages))
    out: list[dict[str, Any]] = []
    for entry in load_deadlines(base_dir):
        if str(entry.get("status") or "").strip().lower() not in _OPEN_STATUSES:
            continue
        dd = _parse_iso_date(entry.get("deadline_date"))
        if dd is None:
            continue
        days_until = (dd - today).days
        if days_until < 0:
            continue
        active = [s for s in stages_asc if days_until <= s]
        if not active:
            continue
        target = active[0]
        if target in _reminded_stages(str(entry.get("deadline_id") or ""), base_dir):
            continue
        out.append({**entry, "lead_stage": target, "days_until": days_until})
    out.sort(key=lambda r: (r.get("deadline_date") or "", r.get("deadline_id") or ""))
    return out


def render_reminder_message(entry: dict[str, Any]) -> str:
    """Render the customer-facing reminder text.

    Evidence-grounded and legal-safe: it states the monitored date and the exact
    diff excerpt it came from, deep-links to the evidence record, and carries the
    disclaimer. It describes what changed / what the reader may wish to review —
    never advice, never a guarantee. The shared forbidden-claims guard runs over
    the final text before it is returned.
    """
    from app.change_register import assert_no_forbidden_claims

    stage = entry.get("lead_stage")
    days_until = entry.get("days_until")
    kind_label = _KIND_LABEL.get(str(entry.get("deadline_kind")), str(entry.get("deadline_kind") or "date"))
    source = str(entry.get("source_name") or entry.get("source_id") or "monitored source").strip()
    regulator = str(entry.get("regulator") or "").strip()
    reg_suffix = f" ({regulator})" if regulator else ""
    ev_id = str(entry.get("evidence_record_id") or "").strip()
    official_url = str(entry.get("official_url") or "").strip()
    excerpt = str(entry.get("extracted_from_diff_excerpt") or "").strip()

    raw_date_text = str(entry.get("raw_date_text") or "").strip()
    date_ambiguous = bool(entry.get("date_ambiguous"))

    when = (
        f"{days_until} day(s) away"
        if isinstance(days_until, int)
        else "approaching"
    )
    # Surface the parsed ISO date AND the raw text the source used, so the reader
    # can verify the parse against the original wording.
    monitored_line = f"Monitored {kind_label}: {entry.get('deadline_date')}"
    if raw_date_text and raw_date_text.lower() != str(entry.get("deadline_date") or "").lower():
        monitored_line += f" (source text: \"{raw_date_text}\")"
    lines = [
        f"StatuteProof deadline radar — a monitored {kind_label} is {when}.",
        "",
        f"Source: {source}{reg_suffix}",
        monitored_line,
    ]
    if date_ambiguous:
        lines.append(
            "Date format is ambiguous (day/month vs month/day); read here as "
            "day-first. Verify the exact date against the official source."
        )
    if isinstance(stage, int):
        lines.append(f"Lead-time reminder: {stage}-day stage")
    if excerpt:
        lines.append(f"Detected in change: {excerpt}")
    if ev_id:
        lines.append(f"Evidence record: {ev_id}")
    if official_url:
        lines.append(f"Official source: {official_url}")
    lines += [
        "",
        "This is a monitoring reminder that a change to a monitored official "
        "source referenced this date. You may wish to review the evidence record "
        "and the official source before it is reached.",
        "",
        LEGAL_DISCLAIMER,
    ]
    message = "\n".join(lines)
    assert_no_forbidden_claims(message)
    return message


def build_reminder_email(entry: dict[str, Any]) -> dict[str, Any]:
    """Build an email payload for a deadline reminder via the existing channel.

    Reuses ``app.email_delivery.build_monitoring_brief_email`` so the mandatory
    disclaimer is guaranteed to be present in both text and HTML bodies.
    """
    from app.email_delivery import build_monitoring_brief_email

    body = render_reminder_message(entry)
    source = str(entry.get("source_name") or entry.get("source_id") or "monitored source").strip()
    return build_monitoring_brief_email(
        brief_markdown=body,
        source_name=source,
        risk_level="",
    )


def send_due_reminders(
    *,
    as_of: date | None = None,
    lead_stages: tuple[int, ...] = LEAD_STAGES,
    base_dir: Path | None = None,
    send_fn: Callable[[str, str], bool] | None = None,
    recipients: list[str] | None = None,
    now_fn: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Fire due lead-time reminders through the Telegram channel; dedupe by stage.

    A reminder for a given ``(deadline, stage)`` is logged (and therefore never
    re-sent) ONLY after at least one recipient delivery succeeds — mirroring the
    alert-durability rule (never mark a reminder "sent" that was not delivered),
    so a transient outage or a not-yet-linked customer base retries next pass.

    ``send_fn`` and ``recipients`` are injectable for tests; in production they
    default to ``app.telegram.send_telegram_message`` and the subscribed
    customers (``app.telegram_pairing.get_all_linked_chat_ids``) — the same
    channel customer alerts use.
    """
    due = due_reminders(as_of=as_of, lead_stages=lead_stages, base_dir=base_dir)
    summary: dict[str, Any] = {"due": len(due), "sent": [], "skipped_no_recipients": 0, "failed": 0}
    if not due:
        return summary

    if send_fn is None:
        from app.telegram import send_telegram_message as send_fn  # type: ignore
    if recipients is None:
        try:
            from app.telegram_pairing import get_all_linked_chat_ids
            recipients = [str(c) for c in (get_all_linked_chat_ids() or [])]
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("deadline radar: could not resolve recipients: %s", exc)
            recipients = []

    stamp_fn = now_fn or now_utc

    for entry in due:
        try:
            message = render_reminder_message(entry)
        except Exception as exc:
            logger.warning("deadline radar: reminder blocked before send (%s)", exc)
            summary["failed"] += 1
            continue

        if not recipients:
            summary["skipped_no_recipients"] += 1
            continue

        delivered = 0
        for chat_id in recipients:
            try:
                if send_fn(str(chat_id), message):
                    delivered += 1
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("deadline radar: reminder send failed for %s: %s", chat_id, exc)

        if delivered <= 0:
            summary["failed"] += 1
            continue

        _append_jsonl(
            deadline_reminders_path(base_dir),
            {
                "deadline_id": entry.get("deadline_id"),
                "evidence_record_id": entry.get("evidence_record_id"),
                "lead_stage": int(entry.get("lead_stage")),
                "days_until": entry.get("days_until"),
                "recipients_delivered": delivered,
                "sent_at": stamp_fn(),
            },
        )
        summary["sent"].append(
            {
                "deadline_id": entry.get("deadline_id"),
                "lead_stage": int(entry.get("lead_stage")),
                "recipients_delivered": delivered,
            }
        )

    return summary
