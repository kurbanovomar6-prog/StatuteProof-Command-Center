"""Readable REDLINE view of a sealed change — sourced ONLY from the evidence.

WHAT THIS IS (the framing is legally load-bearing — read it).
--------------------------------------------------------------
A "redline" here is the added / removed text StatuteProof already captured into a
tamper-evident evidence record, re-rendered as structured added (green) / removed
(red) lines so a reviewer can read *what changed* at a glance. It is a MONITORING
view of a DETECTED CHANGE:

* It is NOT an instruction, obligation, deadline, or compliance action.
* It is NOT advice or a determination that any change applies to the reader.
* It is NOT a fresh diff — nothing is re-diffed against the live source. Every
  line is parsed from the SEALED diff artifact the pipeline persisted at ingest
  (``change.diff_path`` / ``files.diff_path``), so every rendered line traces to
  the record's self-seal ``record_hash`` and can be re-checked independently.

The StatuteProof-authored copy (framing, notes, labels) is passed through the
shared forbidden-claims guard (``app.legal_safety``); the OFFICIAL changed text
itself is the regulator's words and is shown verbatim (monitoring/evidence),
never guarded or altered beyond dropping unreadable bytes.

HOW THE REDLINE IS BUILT (reuse, never re-diff).
------------------------------------------------
The sealed diff artifact is written in one of two shapes the pipeline can emit
(see ``app.chunk_diff.render_diff_markdown`` and
``app.evidence_records._canonical_diff_artifact``):

1. A markdown chunk report — ``## Added Chunks`` / ``## Removed Chunks`` /
   ``## Changed Chunks`` with fenced ``text`` blocks. This is what production
   evidence carries today.
2. A difflib unified diff — ``@@`` hunks with ``+`` / ``-`` / context lines.

``parse_sealed_diff_to_redline`` handles BOTH into one ordered list of blocks.
Record resolution reuses ``app.alert_proof`` (the same loader the alert ``proof``
block is built from) so this view and the proof block can never disagree about
which sealed record an alert points to. Unreadable (binary / mis-decoded) lines
are dropped with the SAME shared predicate the customer-facing excerpt uses
(``app.text_quality``) so mojibake can never reach a customer.

Everything is bounded (line count, per-line length, block count, input bytes) and
fail-soft: a malformed diff yields ``available: False`` with an honest note, never
a raised exception and never a fabricated line.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from app.legal_safety import assert_no_forbidden_claims
from app.materiality import SHORT_DISCLAIMER
from app.text_quality import strip_unreadable_chars, unreadable_ratio

logger = logging.getLogger(__name__)

# ── Bounds (a pathological diff can never make this slow or huge) ──────────────
_MAX_INPUT_BYTES = 400_000   # chars read from the sealed diff artifact before parse
_MAX_TOTAL_LINES = 400       # added + removed lines rendered
_MAX_LINE_CHARS = 400        # per-line cap (matches app.alert_content excerpt cap)
_MAX_BLOCKS = 200            # contiguous same-op groups
_MAX_GROUPS = 200            # distinct change groups (hunks / ### Change N)

# A line this saturated with unreadable characters is binary or mis-decoded
# source — dropping it is honest; showing it is worse. The threshold and the
# character classification are the SHARED gate used by the alert excerpt and the
# adapter quality gate (app.text_quality), so this view can never disagree with
# the rest of the delivery path about "is this readable".
_UNREADABLE_LINE_RATIO = 0.05

# ── StatuteProof-authored copy (all guarded) ──────────────────────────────────
# Static, so the framing is a constant guarded ONCE at import — no per-request
# interpolation that could drift a forbidden claim into a customer's view. The
# source name is surfaced as a separate labelled field, never spliced into the
# sentence.
REDLINE_FRAMING = (
    "This is the text StatuteProof detected as changed in a monitored official "
    "source and sealed into a tamper-evident evidence record. It is shown for "
    "monitoring review only — a detected change, not an instruction, a deadline, "
    "or a determination that anything applies to you. Verify against the official "
    "source and re-check the sealed record before relying on it."
)

_NO_SEAL_NOTE = (
    "No sealed evidence record is linked to this alert, so a redline cannot be "
    "shown. Open the evidence record to review what was captured."
)
_NO_DIFF_NOTE = (
    "This alert's sealed record has no stored diff to render as a redline (for "
    "example a first-capture baseline). Open the evidence record to review it."
)
_UNPARSEABLE_NOTE = (
    "The sealed diff for this record is stored in a format that cannot be shown "
    "as a line-level redline. Open the evidence record to review the change."
)
_INTEGRITY_NOTE = (
    "This alert's stored diff no longer matches its sealed evidence record, so it "
    "is not shown as a verified redline. Open the evidence record to review it."
)
_PARTIAL_NOTE = (
    "Some changed content was not machine-readable (binary or improperly encoded "
    "source data) and was omitted from this redline."
)

# Fail-closed: authored copy must never assert a forbidden claim. Wording drift in
# any of these constants fails the import, not just a test.
for _label, _text in (
    ("Redline framing", REDLINE_FRAMING),
    ("Redline no-seal note", _NO_SEAL_NOTE),
    ("Redline no-diff note", _NO_DIFF_NOTE),
    ("Redline unparseable note", _UNPARSEABLE_NOTE),
    ("Redline partial note", _PARTIAL_NOTE),
):
    assert_no_forbidden_claims(_text, label=_label)


# ── Pure parser (no I/O) ──────────────────────────────────────────────────────

def _clean_line(raw: Any) -> str | None:
    """Return a readable, length-capped line, or ``None`` to drop it.

    ``None`` means "drop": blank after trimming, or saturated with unreadable
    characters (binary / mis-decoded). Surviving lines have stray unreadable
    bytes stripped and are capped at ``_MAX_LINE_CHARS``.
    """
    line = str(raw or "").replace("\t", " ").rstrip()
    if not line.strip():
        return None
    if unreadable_ratio(line) > _UNREADABLE_LINE_RATIO:
        return None
    line = strip_unreadable_chars(line)
    if not line.strip():
        return None
    if len(line) > _MAX_LINE_CHARS:
        line = line[: _MAX_LINE_CHARS - 1].rstrip() + "…"
    return line


class _RedlineAccumulator:
    """Collects op-tagged lines into ordered blocks under strict bounds."""

    def __init__(self) -> None:
        self.blocks: list[dict[str, Any]] = []
        self.added_lines = 0
        self.removed_lines = 0
        self.dropped_unreadable = False
        self.truncated = False

    def _full(self) -> bool:
        return (
            self.added_lines + self.removed_lines >= _MAX_TOTAL_LINES
            or len(self.blocks) >= _MAX_BLOCKS
        )

    def add_block(self, op: str, raw_lines: list[str], group: int | None) -> None:
        """Emit one contiguous same-op block; drops unreadable lines; bounded."""
        if op not in ("added", "removed"):
            return
        if self._full():
            self.truncated = True
            return
        cleaned: list[str] = []
        for raw in raw_lines:
            if self.added_lines + self.removed_lines + len(cleaned) >= _MAX_TOTAL_LINES:
                self.truncated = True
                break
            line = _clean_line(raw)
            if line is None:
                # Blank lines are structural, not mojibake — only flag true drops.
                if str(raw or "").strip():
                    self.dropped_unreadable = True
                continue
            cleaned.append(line)
        if not cleaned:
            return
        self.blocks.append({"op": op, "lines": cleaned, "group": group})
        if op == "added":
            self.added_lines += len(cleaned)
        else:
            self.removed_lines += len(cleaned)


def _looks_like_chunk_report(text: str) -> bool:
    return (
        "## Added Chunks" in text
        or "## Removed Chunks" in text
        or "## Changed Chunks" in text
    )


def _looks_like_unified_diff(text: str) -> bool:
    for line in text.splitlines():
        if line.startswith("@@ ") or line.startswith("--- ") or line.startswith("+++ "):
            return True
    return False


def _is_fence(line: str) -> bool:
    return line.lstrip().startswith("```")


def _parse_chunk_report(text: str, acc: _RedlineAccumulator) -> None:
    """Parse ``render_diff_markdown`` output into op-tagged blocks.

    Section state machine over the markdown: ``## Added Chunks`` /
    ``## Removed Chunks`` fenced blocks map to added / removed; each
    ``## Changed Chunks`` -> ``### Change N`` carries a ``Before:`` fence
    (removed) and an ``After:`` fence (added). Fenced content is split into lines
    and grouped; anything outside a fence (headers, summary, limitations) is
    ignored.
    """
    section: str | None = None          # "added" | "removed" | "changed" | None
    group: int | None = None
    pending_op: str | None = None        # within "changed": before -> removed, after -> added
    in_fence = False
    fence_lines: list[str] = []
    fence_op: str | None = None

    def flush_fence() -> None:
        nonlocal fence_lines, fence_op
        if fence_op and fence_lines:
            acc.add_block(fence_op, fence_lines, group)
        fence_lines = []
        fence_op = None

    for raw in text.splitlines():
        if _is_fence(raw):
            if in_fence:
                in_fence = False
                flush_fence()
            else:
                in_fence = True
                fence_lines = []
                if section == "added":
                    fence_op = "added"
                elif section == "removed":
                    fence_op = "removed"
                elif section == "changed":
                    fence_op = pending_op
                else:
                    fence_op = None
            continue

        if in_fence:
            fence_lines.append(raw)
            continue

        stripped = raw.strip()
        if stripped == "## Added Chunks":
            section, group, pending_op = "added", None, None
        elif stripped == "## Removed Chunks":
            section, group, pending_op = "removed", None, None
        elif stripped == "## Changed Chunks":
            section, group, pending_op = "changed", None, None
        elif stripped.startswith("## "):
            # Any other section (e.g. "## Limitations") ends chunk parsing scope.
            section, pending_op = None, None
        elif section == "changed" and stripped.startswith("### Change "):
            if len(acc.blocks) >= _MAX_GROUPS or acc.truncated:
                acc.truncated = True
            group = (group or 0) + 1
            pending_op = None
        elif section == "changed" and stripped == "Before:":
            pending_op = "removed"
        elif section == "changed" and stripped == "After:":
            pending_op = "added"

    # A truncated/malformed artifact can end inside an open fence — flush the
    # collected lines rather than silently dropping trailing changed content
    # (they were inside a ```text block, so they ARE sealed change text).
    if in_fence:
        flush_fence()


def _parse_unified_diff(text: str, acc: _RedlineAccumulator) -> None:
    """Parse a difflib unified diff into op-tagged blocks, grouped by hunk.

    ``+`` / ``-`` lines become added / removed; ``@@`` starts a new group;
    ``---`` / ``+++`` file headers and context lines are skipped. Consecutive
    same-op lines are coalesced into one block.
    """
    group = 0
    run_op: str | None = None
    run_lines: list[str] = []

    def flush_run() -> None:
        nonlocal run_op, run_lines
        if run_op and run_lines:
            acc.add_block(run_op, run_lines, group)
        run_op = None
        run_lines = []

    for raw in text.splitlines():
        if raw.startswith("@@"):
            flush_run()
            group += 1
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            flush_run()
            continue
        if raw.startswith("+"):
            op, content = "added", raw[1:]
        elif raw.startswith("-"):
            op, content = "removed", raw[1:]
        else:
            flush_run()  # context line ends the current run
            continue
        if run_op is not None and run_op != op:
            flush_run()
        run_op = op
        run_lines.append(content)
    flush_run()


def parse_sealed_diff_to_redline(diff_text: str) -> dict[str, Any]:
    """Parse a SEALED diff artifact into structured redline blocks (pure).

    Never re-diffs and never fabricates a line: only text present in the sealed
    artifact is emitted. Returns::

        {"available": bool, "format": "chunk_report"|"unified"|"none",
         "blocks": [{"op": "added"|"removed", "lines": [...], "group": int|None}],
         "added_lines": int, "removed_lines": int,
         "truncated": bool, "partial": bool, "note": str}

    ``available`` is ``True`` only when at least one readable added/removed line
    was recovered; otherwise ``note`` explains honestly why not.
    """
    text = str(diff_text or "")[:_MAX_INPUT_BYTES]
    acc = _RedlineAccumulator()

    if _looks_like_chunk_report(text):
        fmt = "chunk_report"
        _parse_chunk_report(text, acc)
    elif _looks_like_unified_diff(text):
        fmt = "unified"
        _parse_unified_diff(text, acc)
    else:
        return {
            "available": False,
            "format": "none",
            "blocks": [],
            "added_lines": 0,
            "removed_lines": 0,
            "truncated": False,
            "partial": False,
            "note": _UNPARSEABLE_NOTE,
        }

    available = bool(acc.blocks)
    note = ""
    if not available:
        note = _UNPARSEABLE_NOTE
    elif acc.dropped_unreadable:
        note = _PARTIAL_NOTE
    return {
        "available": available,
        "format": fmt,
        "blocks": acc.blocks,
        "added_lines": acc.added_lines,
        "removed_lines": acc.removed_lines,
        "truncated": acc.truncated,
        "partial": acc.dropped_unreadable,
        "note": note,
    }


# ── Evidence-record resolution + bounded read (fail-soft) ──────────────────────

def _read_sealed_diff_raw(diff_path: Any, root: Path) -> str | None:
    """Read the raw sealed diff artifact, bounded + CONFINED, or ``None``.

    Resolves ``diff_path`` (absolute, else relative to ``root``) and then
    REQUIRES the resolved path to stay inside ``root`` — a record whose
    ``diff_path`` points outside the evidence tree (``../`` or a foreign
    absolute path) is treated as having no diff rather than read. Records are
    pipeline-written, so this should never trigger; it is defence-in-depth so a
    tampered record can never turn this customer-facing view into an arbitrary
    file read. Returns the FULL raw artifact (not just the added side) because a
    redline needs the removed lines and structure too — this is why the
    added-only ``effective_dates._read_sealed_diff_text`` reader is not reused.
    """
    text = str(diff_path or "").strip()
    if not text:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = root / path
    try:
        resolved = path.resolve()
        if not resolved.is_relative_to(root.resolve()):
            return None
        if not resolved.is_file():
            return None
        with resolved.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.read(_MAX_INPUT_BYTES)
    except OSError:
        return None


def _sealed_diff_matches(record: dict[str, Any], root: Path) -> bool:
    """EV-1: False only when the stored diff.txt no longer matches the sealed
    content.diff_hash (a redline edited in place after sealing). Additive and
    fail-soft: returns True when no diff_hash is sealed (legacy records) or the
    path is unresolvable/out-of-tree (the diff reader handles those), so the ONLY
    thing this adds is a refusal to render a genuinely-tampered redline as sealed.
    Hashes the FILE BYTES — _read_sealed_diff_raw decodes errors='replace' and
    bounds its read, so its returned text cannot be hashed reliably."""
    content = record.get("content")
    diff_hash = str((content.get("diff_hash") if isinstance(content, dict) else "") or "").strip()
    if not diff_hash:
        return True
    change = record.get("change") if isinstance(record.get("change"), dict) else {}
    files = record.get("files") if isinstance(record.get("files"), dict) else {}
    ref = str(change.get("diff_path") or files.get("diff_path") or "").strip()
    if not ref:
        return True
    path = Path(ref)
    if not path.is_absolute():
        path = root / path
    try:
        resolved = path.resolve()
        if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
            return True
        return f"sha256:{hashlib.sha256(resolved.read_bytes()).hexdigest()}" == diff_hash
    except OSError:
        return True


def _empty_redline(proof: dict[str, Any] | None, match: dict[str, Any], *, note: str) -> dict[str, Any]:
    """A well-formed, unavailable redline carrying whatever pointer we have."""
    proof = proof if isinstance(proof, dict) else {}
    return {
        "available": False,
        "format": "none",
        "blocks": [],
        "added_lines": 0,
        "removed_lines": 0,
        "truncated": False,
        "partial": False,
        "note": note,
        "record_hash": str(proof.get("record_hash") or ""),
        "evidence_record_id": str(proof.get("evidence_record_id") or ""),
        "run_id": str(proof.get("run_id") or ""),
        "normalized_hash": proof.get("normalized_hash"),
        "source_name": str(match.get("source_name") or "") if isinstance(match, dict) else "",
        "source_url": str(match.get("source_url") or "") if isinstance(match, dict) else "",
        "captured_at": str(match.get("detected_at") or "") if isinstance(match, dict) else "",
        "framing": REDLINE_FRAMING,
        "disclaimer": SHORT_DISCLAIMER,
    }


def build_redline_for_match(match: dict[str, Any], *, base_dir: Path | None = None) -> dict[str, Any]:
    """Build the sealed-evidence redline for one owner-scoped routing match.

    The caller MUST pass a match resolved through the owner-scoped routing
    preview (``build_routing_preview_for_user``) so tenancy is already enforced;
    this function adds no scope of its own — it only resolves the sealed record
    the match's ``proof`` block points to, reads its diff artifact, and renders
    the redline.

    Fail-soft by contract: any unresolved / unsealed / unreadable / unparseable
    condition yields ``available: False`` with an honest note and the pointer we
    have. Never raises; never re-diffs the live source.
    """
    if not isinstance(match, dict):
        return _empty_redline(None, {}, note=_NO_SEAL_NOTE)

    proof = match.get("proof")
    if not isinstance(proof, dict):
        return _empty_redline(None, match, note=_NO_SEAL_NOTE)

    source_id = str(match.get("source_id") or "").strip()
    run_id = str(proof.get("run_id") or "").strip()
    record_hash = str(proof.get("record_hash") or "").strip()
    if not source_id or not run_id or not record_hash:
        return _empty_redline(proof, match, note=_NO_SEAL_NOTE)
    if not proof.get("diff_available"):
        return _empty_redline(proof, match, note=_NO_DIFF_NOTE)

    try:
        # Reuse the alert-proof loader + path-safety regex so this view and the
        # proof block resolve the SAME sealed record identically and neither can
        # be tricked into traversing outside evidence/<regulator>/<source>/<run>/.
        from app.alert_proof import _SAFE_SEGMENT_RE, _evidence_base_dir, _load_record

        if not _SAFE_SEGMENT_RE.match(source_id) or not _SAFE_SEGMENT_RE.match(run_id):
            return _empty_redline(proof, match, note=_NO_SEAL_NOTE)

        root = Path(base_dir) if base_dir is not None else _evidence_base_dir()
        record = _load_record(root / "evidence", source_id, run_id)
        if not isinstance(record, dict):
            return _empty_redline(proof, match, note=_NO_DIFF_NOTE)

        # Evidence-First: only a COMPLETE, integrity-VERIFIED record is shown as a
        # redline (defence-in-depth on top of the proof block's completeness check).
        if str(record.get("record_status") or "") != "complete":
            return _empty_redline(proof, match, note=_NO_DIFF_NOTE)
        integrity = record.get("integrity")
        if not isinstance(integrity, dict) or integrity.get("integrity_status") != "VERIFIED":
            return _empty_redline(proof, match, note=_NO_DIFF_NOTE)

        # EV-1: the integrity_status above is a stored STRING. Re-hash the stored
        # diff against the sealed content.diff_hash so an in-place edit to the
        # customer-facing redline is refused here, not rendered as "sealed".
        if not _sealed_diff_matches(record, root):
            return _empty_redline(proof, match, note=_INTEGRITY_NOTE)

        change_raw = record.get("change")
        change: dict[str, Any] = change_raw if isinstance(change_raw, dict) else {}
        files_raw = record.get("files")
        files: dict[str, Any] = files_raw if isinstance(files_raw, dict) else {}
        diff_text = _read_sealed_diff_raw(change.get("diff_path") or files.get("diff_path"), root)
        if not diff_text:
            return _empty_redline(proof, match, note=_NO_DIFF_NOTE)

        parsed = parse_sealed_diff_to_redline(diff_text)
    except Exception as exc:  # noqa: BLE001 — fail-soft is the contract
        logger.debug("Redline build failed (non-fatal): %s: %s", type(exc).__name__, exc)
        return _empty_redline(proof, match, note=_UNPARSEABLE_NOTE)

    envelope = _empty_redline(proof, match, note=parsed.get("note", ""))
    return {**envelope, **parsed}
