"""Effective-date / key-date calendar — a forward-looking MONITORING view.

WHAT THIS IS (read the framing carefully — it is legally load-bearing).
----------------------------------------------------------------------
A "detected key date" is a date STRING FOUND IN THE CHANGED TEXT of a monitored
official source, captured into a sealed, tamper-evident evidence record. It is a
MONITORING SIGNAL to help a human decide what to review first — nothing more:

* It is NOT the reader's legal deadline or obligation.
* It is NOT advice, a legal opinion, or a determination that a date applies to
  the reader.
* It is NOT a guarantee that the parsed date is correct, complete, or that every
  relevant date in the monitored sources was captured. Detection is best-effort
  over the monitored sources only.

Every date this module emits is framed as: "a date StatuteProof detected in the
changed text of {source} on {capture date} — verify against the official source
before relying on it." The authored framing/labels are passed through the shared
forbidden-claims guard (``app.legal_safety``) so wording drift can never ship a
forbidden claim, and the short disclaimer rides on every item and on the view.

HOW DATES ARE EXTRACTED (deterministic; reuses the existing matchers).
----------------------------------------------------------------------
The actual date/kind/excerpt capture is DELEGATED to
``app.deadline_radar.extract_deadlines`` (which itself reuses
``app.risk.derive_urgency_and_dates`` — the same capture the deadline radar and
the review-priority heuristic in ``app.materiality`` are built on). So date
regexes, deadline-kind tagging, excerpting, and calendar resolution are defined
ONCE and can never drift between this calendar and the radar. Nothing is
invented: a date is only emitted when a real date expression is present in the
changed text AND resolves to a concrete calendar date.

The CHANGED text for a record is reconstructed with the canonical diff primitive
(``app.chunk_diff.build_chunk_diff``) over the record's sealed previous/current
normalized snapshots — the same primitive the pipeline and materiality use — so
we scan exactly the added/changed side a reviewer would read.

Pure where it can be: ``extract_key_dates_from_change`` takes text and returns
dates with no I/O. The orchestration layer (``upcoming_key_dates``) reads
in-scope evidence records, enforces tenancy, bounds everything, and fails soft:
one malformed record or date is skipped, never fatal.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from app.legal_safety import assert_no_forbidden_claims

# ONE copy of the customer-facing short disclaimer (defined in app.materiality,
# which is the CLAUDE.md short-disclaimer verbatim). Reused, never re-typed.
from app.materiality import SHORT_DISCLAIMER

logger = logging.getLogger(__name__)

# Honor the shared base-dir convention so the calendar reads the same evidence
# tree the rest of the trail resolves against; overridable per call for tests.
_BASE_DIR = Path(__file__).parent.parent.resolve()

# ── Bounds (fail-soft, cannot be made slow or unbounded by pathological input) ─
_DEFAULT_HORIZON_DAYS = 90
_MAX_HORIZON_DAYS = 365
_MAX_DATES_PER_RECORD = 25
_MAX_TOTAL_DATES = 500
_MAX_RECORDS_SCANNED = 5000
_MAX_EXCERPT_CHARS = 240
_MAX_SNAPSHOT_BYTES = 200_000  # chars read from each snapshot on the fallback re-diff path
_MAX_DIFF_BYTES = 400_000      # chars read from a persisted diff artifact before parse

# ── Detected-type mapping (honest "detected type", never asserted) ────────────
# ``app.deadline_radar.extract_deadlines`` tags each date with one of these
# kinds. We map to a coarse, honest ``detected_type`` + human label. "transition"
# is surfaced honestly rather than collapsed; anything unknown is "other".
_TYPE_MAP: dict[str, tuple[str, str]] = {
    "effective": ("effective_date", "effective date"),
    "consultation_close": ("consultation_close", "consultation close"),
    "transition": ("transition", "transition period end"),
    "deadline": ("deadline", "deadline"),
}
_DEFAULT_TYPE = ("other", "date")

# Framing that rides on the whole calendar view + ICS export (not per-date).
VIEW_FRAMING = (
    "These are dates StatuteProof detected in the changed text of monitored "
    "official sources and sealed into evidence records. They are monitoring "
    "signals to help a reviewer decide what to check first — not legal "
    "deadlines, not advice, and not a guarantee any date is correct, applies to "
    "you, or that every relevant date was captured. Verify each date against the "
    "official source before relying on it."
)

# Defense-in-depth: guard the static view framing at import time too (the per-date
# framing/labels are already guarded on every emission). Wording drift in this
# constant fails the import, not just a test (code review 2026-07-12).
assert_no_forbidden_claims(VIEW_FRAMING, label="Effective-dates view framing")


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_iso_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if len(text) < 10:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _capture_date_label(captured_at: str) -> str:
    """A readable capture-date for the framing string ("2026-07-01")."""
    parsed = _parse_iso_date(captured_at)
    return parsed.isoformat() if parsed else "an earlier capture"


def _date_framing(source_label: str, capture_date: str) -> str:
    """Per-date honest framing. Authored — passed through the guard by caller."""
    return (
        f"A date StatuteProof detected in the changed text of {source_label} on "
        f"{capture_date}. This is a monitoring signal to help a reviewer decide "
        "what to check — not a legal deadline, not advice, and not a guarantee "
        "the date is correct, applies to you, or that every relevant date was "
        "captured. Verify against the official source before relying on it."
    )


def extract_key_dates_from_change(
    changed_text: str,
    *,
    source_id: str = "",
    source_name: str = "",
    regulator: str = "",
    official_url: str = "",
    evidence_record_id: str = "",
    record_hash: str = "",
    captured_at: str = "",
    max_dates: int = _MAX_DATES_PER_RECORD,
) -> list[dict[str, Any]]:
    """Extract candidate key dates from a piece of CHANGED source text.

    Pure and deterministic (no I/O): delegates date capture to
    ``app.deadline_radar.extract_deadlines`` so the calendar and the deadline
    radar share ONE matcher/parser and can never disagree on "what is a date" or
    "what calendar day does it resolve to". Never fabricates a date not present
    in ``changed_text``. Bounded by ``max_dates`` and ``_MAX_EXCERPT_CHARS``.
    Fail-soft: returns ``[]`` on any internal error.

    Each returned item carries a full verification pointer — the SEALED
    ``record_hash`` and ``evidence_record_id`` — so a reader can check the date
    against the tamper-evident evidence trail, plus the honest per-date framing
    and the short disclaimer.
    """
    try:
        from app.deadline_radar import extract_deadlines

        raw = extract_deadlines(changed_text or "")
    except Exception:  # noqa: BLE001 — extraction must never break the calendar
        logger.warning("effective-dates: extraction failed for %s", source_id)
        return []

    source_label = str(source_name or source_id or "a monitored source").strip()
    capture_date = _capture_date_label(captured_at)
    framing = _date_framing(source_label, capture_date)
    # Fail-closed: authored framing must never assert a forbidden claim.
    assert_no_forbidden_claims(framing, label="Effective-date framing")

    out: list[dict[str, Any]] = []
    for item in raw[: max(0, int(max_dates))]:
        iso = str(item.get("deadline_date") or "").strip()
        if not iso:
            continue
        detected_type, type_label = _TYPE_MAP.get(
            str(item.get("deadline_kind") or "").strip().lower(), _DEFAULT_TYPE
        )
        # The label is authored (curated set) — guard it too, cheaply.
        assert_no_forbidden_claims(type_label, label="Effective-date type label")
        excerpt = str(item.get("extracted_from_diff_excerpt") or "").strip()[:_MAX_EXCERPT_CHARS]
        out.append(
            {
                "date": iso,
                "detected_type": detected_type,
                "type_label": type_label,
                "raw_date_text": str(item.get("date_text") or "").strip(),
                "date_ambiguous": bool(item.get("date_ambiguous")),
                "excerpt": excerpt,
                "source_id": str(source_id or "").strip(),
                "source_name": str(source_name or "").strip(),
                "regulator": str(regulator or "").strip(),
                "official_url": str(official_url or "").strip(),
                "evidence_record_id": str(evidence_record_id or "").strip(),
                "record_hash": str(record_hash or "").strip(),
                "captured_at": str(captured_at or "").strip(),
                "framing": framing,
                "disclaimer": SHORT_DISCLAIMER,
            }
        )
    return out


# ── Evidence-record reads (bounded, fail-soft) ────────────────────────────────

def _resolve(root: Path, rel_or_abs: Any) -> Path | None:
    text = str(rel_or_abs or "").strip()
    if not text:
        return None
    path = Path(text)
    return path if path.is_absolute() else (root / path)


def _read_snapshot(root: Path, rel_or_abs: Any) -> str:
    """Read a normalized snapshot, capped at ``_MAX_SNAPSHOT_BYTES + 1`` chars so
    the caller can DETECT truncation (a full read is ``<= _MAX_SNAPSHOT_BYTES``)."""
    path = _resolve(root, rel_or_abs)
    if path is None or not path.exists():
        return ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.read(_MAX_SNAPSHOT_BYTES + 1)
    except OSError:
        return ""


def _read_sealed_diff_text(root: Path, rel_or_abs: Any) -> str | None:
    """Return the added/changed text of the SEALED diff artifact, or ``None`` if
    absent/unreadable.

    ``diff_path`` is the diff the canonical writer persisted over the FULL,
    untruncated snapshots at ingest (:func:`app.evidence_records._canonical_diff_artifact`),
    so reading it avoids the truncation-misalignment a re-diff of independently
    byte-capped snapshots can introduce. Handles both shapes the pipeline can write:
    a difflib unified diff (extract the added ``+`` lines) and a copied markdown
    diff report (use the report text — date extraction reads dates from the changed
    content regardless of format; diff punctuation never manufactures a date).
    """
    path = _resolve(root, rel_or_abs)
    if path is None or not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            # Read ONE char past the cap so truncation is DETECTABLE (a full,
            # untruncated diff is <= _MAX_DIFF_BYTES). Mirrors the +1 pattern in
            # _read_snapshot / the re-diff fallback in _changed_text_for_record.
            raw = fh.read(_MAX_DIFF_BYTES + 1)
    except OSError:
        return None
    if len(raw) > _MAX_DIFF_BYTES:
        # The sealed diff exceeded the read cap. Silently using the truncated
        # prefix would surface dates only from the head of the diff and MISS
        # every date in the dropped tail — a partial view that looks complete.
        # Skip this artifact instead; the caller falls back to a bounded re-diff
        # (which itself skips over-cap snapshots), so the record is dropped
        # rather than surfaced from an incomplete diff (code review 2026-07-13).
        logger.warning(
            "effective-dates: sealed diff exceeds %d chars — skipping (no partial diff)",
            _MAX_DIFF_BYTES,
        )
        return None
    added = [
        line[1:] for line in raw.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    if added:
        return "\n".join(a for a in added if a.strip())
    # Markdown chunk report (the production format): return ONLY the added/After
    # side. Returning the whole report would feed REMOVED text (## Removed Chunks
    # and the "Before:" side of ## Changed Chunks) to the date extractor, so a
    # date that a change REPEALED — e.g. "the 1 September 2026 deadline is
    # removed" — would surface on the calendar as an UPCOMING obligation. We only
    # ever surface a date from text the change ADDED (verify-swarm 2026-07-12).
    if _looks_like_chunk_report(raw):
        return _added_text_from_chunk_report(raw)
    return raw


def _looks_like_chunk_report(text: str) -> bool:
    return "## Added Chunks" in text or "## Changed Chunks" in text or "## Removed Chunks" in text


def _added_text_from_chunk_report(text: str) -> str:
    """Extract ONLY the added/After fenced text from a render_diff_markdown report.

    State machine over the report: fenced blocks under ``## Added Chunks`` and the
    ``After:`` fence of each ``## Changed Chunks`` -> ``### Change N`` are kept;
    ``## Removed Chunks`` and every ``Before:`` fence are skipped. Anything outside
    a fence (headers, summary, limitations) is ignored. Mirrors the proven
    add/remove partition in ``app.sealed_redline._parse_chunk_report`` without
    taking a dependency on it.
    """
    section: str | None = None       # "added" | "removed" | "changed" | None
    pending_op: str | None = None     # within "changed": Before->removed, After->added
    in_fence = False
    keep_fence = False
    kept: list[str] = []
    for raw_line in text.splitlines():
        if raw_line.lstrip().startswith("```"):
            if in_fence:
                in_fence = False
            else:
                in_fence = True
                if section == "added":
                    keep_fence = True
                elif section == "changed":
                    keep_fence = pending_op == "added"
                else:
                    keep_fence = False
            continue
        if in_fence:
            if keep_fence and raw_line.strip():
                kept.append(raw_line)
            continue
        stripped = raw_line.strip()
        if stripped == "## Added Chunks":
            section, pending_op = "added", None
        elif stripped == "## Removed Chunks":
            section, pending_op = "removed", None
        elif stripped == "## Changed Chunks":
            section, pending_op = "changed", None
        elif stripped.startswith("## "):
            section, pending_op = None, None
        elif section == "changed" and stripped == "Before:":
            pending_op = "removed"
        elif section == "changed" and stripped == "After:":
            pending_op = "added"
    return "\n".join(kept)


def _changed_text_for_record(record: dict[str, Any], root: Path) -> str:
    """Reconstruct the CHANGED/added text for a canonical evidence record.

    Prefers the SEALED diff at ``change.diff_path`` (computed over the FULL snapshots
    at ingest) so a date is only surfaced from text the sealed diff shows as changed.
    Falls back to a bounded re-diff of the normalized snapshots ONLY when no diff
    artifact exists — and skips that record if either snapshot was truncated on read
    (independent truncation could misalign the re-diff and surface a spurious date).
    Returns "" when there is no changed side (e.g. FIRST_SEEN records).
    """
    content = record.get("content")
    if not isinstance(content, dict):
        content = {}
    files = record.get("files")
    if not isinstance(files, dict):
        files = {}
    change = record.get("change")
    if not isinstance(change, dict):
        change = {}

    # 1. Prefer the sealed diff artifact (computed over the full snapshots).
    sealed = _read_sealed_diff_text(root, change.get("diff_path") or files.get("diff_path"))
    if sealed is not None:
        return sealed

    # 2. Fall back to a bounded re-diff of the normalized snapshots.
    current = _read_snapshot(root, content.get("normalized_current_path") or files.get("normalized_path"))
    previous = _read_snapshot(root, content.get("normalized_previous_path") or files.get("previous_path"))
    if not current or not previous:
        return ""
    # If either side exceeded the read bound it was truncated at an independent
    # point — a re-diff could misalign, so skip rather than surface a date the
    # sealed diff might not classify as changed (verify-swarm 2026-07-12).
    if len(current) > _MAX_SNAPSHOT_BYTES or len(previous) > _MAX_SNAPSHOT_BYTES:
        return ""
    try:
        from app.chunk_diff import build_chunk_diff

        artifact = build_chunk_diff(previous, current)
    except Exception:  # noqa: BLE001 — a bad diff must not break the calendar
        return ""
    parts: list[str] = list(artifact.get("added_chunks") or [])
    for changed in artifact.get("changed_chunks") or []:
        if isinstance(changed, dict):
            parts.extend(str(a) for a in (changed.get("after") or []))
    return "\n".join(p for p in parts if str(p).strip())


# ── Forward-looking calendar (tenancy-enforced, bounded, fail-soft) ───────────

def _clamp_horizon(days: Any) -> int:
    try:
        value = int(days)
    except (TypeError, ValueError):
        return _DEFAULT_HORIZON_DAYS
    if value < 1:
        return 1
    return min(value, _MAX_HORIZON_DAYS)


def _resolve_window(
    *,
    as_of: date | None,
    horizon_days: int,
    date_from: date | None,
    date_to: date | None,
) -> tuple[date, date]:
    today = as_of or _utc_today()
    start = date_from or today
    end = date_to or (start + timedelta(days=horizon_days))
    if end < start:
        end = start
    return start, end


def upcoming_key_dates(
    *,
    source_ids: Iterable[str] | None = None,
    excluded_source_ids: Iterable[str] | None = None,
    as_of: date | None = None,
    horizon_days: int = _DEFAULT_HORIZON_DAYS,
    date_from: date | None = None,
    date_to: date | None = None,
    base_dir: Path | None = None,
    max_dates: int = _MAX_TOTAL_DATES,
) -> dict[str, Any]:
    """Forward-looking key dates detected in the changed text of in-scope records.

    Read-only. Tenancy is enforced two ways, mirroring
    ``app.change_register.build_change_register_rows``:

    * ``excluded_source_ids`` (deny-list) drops any source the caller does not
      own — applied UNCONDITIONALLY, even with no allow-list, so a default view
      can never surface another tenant's private custom source.
    * ``source_ids`` (optional allow-list) restricts to named sources.

    Only ``CHANGED`` canonical evidence records are scanned (they carry a diff /
    previous side). Dates are kept when they fall inside the window
    ``[from, to]`` (default: today .. today + ``horizon_days``, clamped to
    ``_MAX_HORIZON_DAYS``). Deduplicated across records on
    ``(source_id, date, detected_type)`` keeping the EARLIEST capture (the first
    time we detected it, with its sealed hash). Bounded by ``_MAX_RECORDS_SCANNED``
    and ``max_dates``. Never raises for expected conditions.

    Returns::

        {"dates": [...], "horizon": {"from", "to", "days"},
         "generated_at": str, "framing": str, "disclaimer": str,
         "count": int, "truncated": bool}
    """
    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    horizon_days = _clamp_horizon(horizon_days)
    window_start, window_end = _resolve_window(
        as_of=as_of, horizon_days=horizon_days, date_from=date_from, date_to=date_to
    )

    allow = {str(s).strip() for s in source_ids} if source_ids is not None else None
    excluded = {str(s).strip() for s in (excluded_source_ids or set()) if str(s).strip()}

    # Discover source directories cheaply (evidence/<regulator>/<source_id> — a
    # directory enumeration, NOT a file read), skip the deny-list, honor the
    # allow-list, then read records ONLY for the in-scope sources. This bounds the
    # (expensive) record reads to the caller's own scope and avoids both the
    # whole-tree walk and list_canonical_evidence_records' per-record review-log
    # re-read — an O(N×M) cost this view never needs (verify-swarm 2026-07-12).
    evidence_root = root / "evidence"
    record_paths: list[Path] = []
    if evidence_root.exists():
        for source_dir in evidence_root.glob("*/*"):
            if not source_dir.is_dir():
                continue
            sid = source_dir.name
            if not sid or sid in excluded:
                continue  # deny-list: another tenant's source is never even read
            if allow is not None and sid not in allow:
                continue  # allow-list restricts to named sources
            record_paths.extend(source_dir.glob("**/evidence-record.json"))
    record_paths.sort()

    # key -> chosen item (earliest capture wins).
    chosen: dict[tuple[str, str, str], dict[str, Any]] = {}
    truncated = False
    scanned = 0

    for examined, record_path in enumerate(record_paths):
        if examined >= _MAX_RECORDS_SCANNED:
            truncated = True
            break
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(record, dict):
            continue

        run = record.get("run")
        if not isinstance(run, dict):
            run = {}
        if str(run.get("status") or "").strip().upper() != "CHANGED":
            continue
        source = record.get("source")
        if not isinstance(source, dict):
            source = {}
        source_id = str(source.get("source_id") or "").strip()
        # Belt-and-suspenders: the dir glob already applied the deny-/allow-list at
        # the directory level; re-check the record's own source_id so it can never
        # resolve outside the caller's scope.
        if not source_id or source_id in excluded:
            continue
        if allow is not None and source_id not in allow:
            continue
        # Evidence-First: only COMPLETE, integrity-VERIFIED records.
        if record.get("record_status") != "complete":
            continue
        integrity = record.get("integrity")
        if not isinstance(integrity, dict) or integrity.get("integrity_status") != "VERIFIED":
            continue
        scanned += 1

        captured_at = str(run.get("timestamp") or "").strip()
        record_hash = str(record.get("record_hash") or "").strip()
        evidence_record_id = str(record.get("record_id") or "").strip()

        changed_text = _changed_text_for_record(record, root)
        if not changed_text:
            continue

        try:
            candidates = extract_key_dates_from_change(
                changed_text,
                source_id=source_id or str(source.get("source_id") or ""),
                source_name=str(source.get("source_name") or "").strip(),
                regulator=str(source.get("regulator") or "").strip(),
                official_url=str(source.get("official_url") or "").strip(),
                evidence_record_id=evidence_record_id,
                record_hash=record_hash,
                captured_at=captured_at,
            )
        except Exception:  # noqa: BLE001 — one bad record can't break the view
            logger.warning("effective-dates: skipped record %s", evidence_record_id)
            continue

        for item in candidates:
            parsed = _parse_iso_date(item.get("date"))
            if parsed is None or parsed < window_start or parsed > window_end:
                continue
            key = (item.get("source_id", ""), item["date"], item.get("detected_type", ""))
            existing = chosen.get(key)
            # Earliest capture wins; break same-timestamp ties on the sealed
            # record_hash so the chosen record is fully determined by its content,
            # never by filesystem/glob iteration order (defence-in-depth on top of
            # the record_paths.sort() above).
            order = (item.get("captured_at", ""), item.get("record_hash", ""))
            if existing is None or order < (
                existing.get("captured_at", ""),
                existing.get("record_hash", ""),
            ):
                enriched = {**item, "days_until": (parsed - (as_of or _utc_today())).days}
                chosen[key] = enriched

    dates = sorted(
        chosen.values(),
        key=lambda d: (d.get("date") or "", d.get("source_name") or d.get("source_id") or "", d.get("detected_type") or ""),
    )
    if len(dates) > max_dates:
        dates = dates[:max_dates]
        truncated = True

    return {
        "dates": dates,
        "count": len(dates),
        "horizon": {
            "from": window_start.isoformat(),
            "to": window_end.isoformat(),
            "days": horizon_days,
        },
        "generated_at": _now_iso(),
        "framing": VIEW_FRAMING,
        "disclaimer": SHORT_DISCLAIMER,
        "truncated": truncated,
    }
