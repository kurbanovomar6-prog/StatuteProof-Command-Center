"""
Paragraph-level diff helpers for normalized source snapshots.

The output is deliberately simple and durable: enough to support human review
and future alert drafts without pretending to be a semantic legal diff.
"""

from __future__ import annotations

from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any


_MAX_STORED_CHUNKS = 50
_MAX_CHARS_PER_CHUNK = 1_200
_MIN_MEANINGFUL_CHARS = 20


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _split_chunks(text: str) -> list[str]:
    clean = (text or "").strip()
    if not clean:
        return []

    chunks = [part.strip() for part in clean.split("\n\n") if part.strip()]
    if len(chunks) <= 1:
        chunks = [line.strip() for line in clean.splitlines() if line.strip()]
    return chunks


def _cap_text(text: str) -> str:
    if len(text) <= _MAX_CHARS_PER_CHUNK:
        return text
    return text[:_MAX_CHARS_PER_CHUNK].rstrip() + "..."


def _cap_chunks(chunks: list[str]) -> list[str]:
    return [_cap_text(chunk) for chunk in chunks[:_MAX_STORED_CHUNKS]]


def _meaningful_chunks(chunks: list[str]) -> list[str]:
    return [chunk for chunk in chunks if len(chunk.strip()) >= _MIN_MEANINGFUL_CHARS]


def build_chunk_diff(previous_text: str, current_text: str) -> dict[str, Any]:
    previous_chunks = _split_chunks(previous_text)
    current_chunks = _split_chunks(current_text)

    if previous_chunks == current_chunks:
        return {
            "added_chunks": [],
            "removed_chunks": [],
            "changed_chunks": [],
            "unchanged_count": len(current_chunks),
            "added_count": 0,
            "removed_count": 0,
            "changed_count": 0,
            "meaningful_change_detected": False,
            "diff_summary": "No normalized text changes detected.",
            "diff_quality": "GOOD",
            "truncated": False,
        }

    matcher = SequenceMatcher(a=previous_chunks, b=current_chunks, autojunk=False)
    added: list[str] = []
    removed: list[str] = []
    changed: list[dict[str, list[str]]] = []
    unchanged_count = 0
    added_count = 0
    removed_count = 0
    changed_count = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        before = previous_chunks[i1:i2]
        after = current_chunks[j1:j2]
        if tag == "equal":
            unchanged_count += i2 - i1
        elif tag == "insert":
            added_count += len(after)
            added.extend(_meaningful_chunks(after))
        elif tag == "delete":
            removed_count += len(before)
            removed.extend(_meaningful_chunks(before))
        elif tag == "replace":
            changed_count += max(len(before), len(after))
            if _meaningful_chunks(before) or _meaningful_chunks(after):
                changed.append({
                    "before": _cap_chunks(before),
                    "after": _cap_chunks(after),
                })

    stored_added = _cap_chunks(added)
    stored_removed = _cap_chunks(removed)
    stored_changed = changed[:_MAX_STORED_CHUNKS]
    truncated = (
        len(added) > len(stored_added)
        or len(removed) > len(stored_removed)
        or len(changed) > len(stored_changed)
    )
    meaningful = bool(stored_added or stored_removed or stored_changed)
    quality = "GOOD" if meaningful else "LIMITED"
    summary = (
        f"{added_count} added, {removed_count} removed, {changed_count} changed chunks; "
        f"{unchanged_count} unchanged."
    )
    if not meaningful:
        summary += " Differences were below the chunk significance threshold."

    return {
        "added_chunks": stored_added,
        "removed_chunks": stored_removed,
        "changed_chunks": stored_changed,
        "unchanged_count": unchanged_count,
        "added_count": added_count,
        "removed_count": removed_count,
        "changed_count": changed_count,
        "meaningful_change_detected": meaningful,
        "diff_summary": summary,
        "diff_quality": quality,
        "truncated": truncated,
    }


def build_incomplete_diff(
    *,
    previous_run_id: str | None,
    current_run_id: str | None,
    previous_snapshot_normalized_path: str | None,
    current_snapshot_normalized_path: str | None,
    limitation: str,
) -> dict[str, Any]:
    return {
        "previous_run_id": previous_run_id,
        "current_run_id": current_run_id,
        "previous_snapshot_normalized_path": previous_snapshot_normalized_path,
        "current_snapshot_normalized_path": current_snapshot_normalized_path,
        "added_chunks": [],
        "removed_chunks": [],
        "changed_chunks": [],
        "unchanged_count": 0,
        "added_count": 0,
        "removed_count": 0,
        "changed_count": 0,
        "meaningful_change_detected": False,
        "diff_summary": limitation,
        "diff_quality": "INCOMPLETE",
        "limitations": [limitation],
        "generated_at_utc": utc_now(),
    }


def render_diff_markdown(diff_artifact: dict[str, Any]) -> str:
    lines = [
        "# Source Diff",
        "",
        f"- Previous run: {diff_artifact.get('previous_run_id') or 'unavailable'}",
        f"- Current run: {diff_artifact.get('current_run_id') or 'unavailable'}",
        f"- Quality: {diff_artifact.get('diff_quality') or 'UNKNOWN'}",
        f"- Meaningful change: {diff_artifact.get('meaningful_change_detected')}",
        f"- Summary: {diff_artifact.get('diff_summary') or ''}",
        "",
    ]

    if diff_artifact.get("limitations"):
        lines.append("## Limitations")
        for note in diff_artifact["limitations"]:
            lines.append(f"- {note}")
        lines.append("")

    if diff_artifact.get("added_chunks"):
        lines.append("## Added Chunks")
        for chunk in diff_artifact["added_chunks"]:
            lines.extend(["", "```text", chunk, "```"])
        lines.append("")

    if diff_artifact.get("removed_chunks"):
        lines.append("## Removed Chunks")
        for chunk in diff_artifact["removed_chunks"]:
            lines.extend(["", "```text", chunk, "```"])
        lines.append("")

    if diff_artifact.get("changed_chunks"):
        lines.append("## Changed Chunks")
        for idx, item in enumerate(diff_artifact["changed_chunks"], start=1):
            lines.extend(["", f"### Change {idx}", "", "Before:", "```text"])
            lines.append("\n\n".join(item.get("before") or []))
            lines.extend(["```", "", "After:", "```text"])
            lines.append("\n\n".join(item.get("after") or []))
            lines.append("```")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
