"""
source_intake.py — Universal Source Intake Layer

Extends source_tester.py with:
  - Nav-shell detection (catches DFSA-class hash collisions)
  - Per-source config application (wait_for_selector, content_selector)
  - Richer status vocabulary for dashboard display
  - Hash collision detection across enabled sources
  - Optional evidence write (write_evidence=True)

Public API
----------
run_source_intake(source, all_sources=None, write_evidence=False) → dict
is_nav_shell_only(text, threshold=0.65) → bool
classify_intake_status(result_dict) → str

Status constants are on SourceIntakeStatus.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from app.source_tester import validate_public_url
from app.text_normalization import normalize_for_change_hash

logger = logging.getLogger(__name__)

# ── paths ─────────────────────────────────────────────────────────────────────

_SOURCES_PATH = Path(__file__).parent.parent / "sources.json"

# ── status vocabulary ─────────────────────────────────────────────────────────


class SourceIntakeStatus:
    CONFIRMED_ACCESSIBLE = "CONFIRMED_ACCESSIBLE"
    JS_RENDERING_NEEDED = "JS_RENDERING_NEEDED"
    PDF_EXTRACTION_NEEDED = "PDF_EXTRACTION_NEEDED"
    NAV_SHELL_ONLY = "NAV_SHELL_ONLY"
    QUALITY_DROP = "QUALITY_DROP"
    NEEDS_SELECTOR_REVIEW = "NEEDS_SELECTOR_REVIEW"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED = "BLOCKED"


# Human-readable labels for dashboard display
STATUS_LABELS: dict[str, str] = {
    SourceIntakeStatus.CONFIRMED_ACCESSIBLE: "Ready",
    SourceIntakeStatus.JS_RENDERING_NEEDED: "JS rendering needed",
    SourceIntakeStatus.PDF_EXTRACTION_NEEDED: "PDF extraction needed",
    SourceIntakeStatus.NAV_SHELL_ONLY: "Remediation needed",
    SourceIntakeStatus.QUALITY_DROP: "Quality check",
    SourceIntakeStatus.NEEDS_SELECTOR_REVIEW: "Selector review",
    SourceIntakeStatus.UNSUPPORTED: "Not supported",
    SourceIntakeStatus.BLOCKED: "Blocked",
}

STATUS_SEVERITY: dict[str, str] = {
    SourceIntakeStatus.CONFIRMED_ACCESSIBLE: "good",
    SourceIntakeStatus.JS_RENDERING_NEEDED: "warning",
    SourceIntakeStatus.PDF_EXTRACTION_NEEDED: "warning",
    SourceIntakeStatus.NAV_SHELL_ONLY: "critical",
    SourceIntakeStatus.QUALITY_DROP: "warning",
    SourceIntakeStatus.NEEDS_SELECTOR_REVIEW: "warning",
    SourceIntakeStatus.UNSUPPORTED: "error",
    SourceIntakeStatus.BLOCKED: "error",
}

# ── thresholds ────────────────────────────────────────────────────────────────

_GLOBAL_MIN_CHARS = 500
_NAV_SHELL_LINE_RATIO = 0.65   # ratio of short lines that triggers nav-shell flag
_NAV_SHELL_SHORT_WORDS = 8     # lines with < this many words count as "nav items"
_NAV_SHELL_MAX_CHARS = 10_000  # above this char count, skip nav-shell check

# ── nav-shell detection ───────────────────────────────────────────────────────


def is_nav_shell_only(text: str, threshold: float = _NAV_SHELL_LINE_RATIO) -> bool:
    """
    Detect whether extracted text is primarily navigation shell content.

    A nav-shell is characterized by many short lines (menu items, breadcrumbs,
    link labels) and few substantive sentences. DFSA's extracted content is a
    clear example: "About us Go Back Who we are The DFSA Governance..."

    Returns True only when:
    - Total chars is below _NAV_SHELL_MAX_CHARS (avoids false positives on big pages)
    - Short-line ratio exceeds threshold

    Short line = fewer than _NAV_SHELL_SHORT_WORDS words.
    """
    text = text.strip()
    if not text:
        return False
    if len(text) >= _NAV_SHELL_MAX_CHARS:
        return False

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False

    short = sum(1 for ln in lines if len(ln.split()) < _NAV_SHELL_SHORT_WORDS)
    ratio = short / len(lines)
    return ratio >= threshold


# ── hash helpers ─────────────────────────────────────────────────────────────


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _check_hash_collision(
    text_hash: str,
    source_id: str,
    all_sources: list[dict],
) -> tuple[bool, str | None]:
    """
    Check whether `text_hash` matches the stored hash of any other enabled source.

    Returns (collision_found, colliding_source_id | None).
    Requires all_sources to have 'source_id' and 'content_hash' fields.
    """
    for s in all_sources:
        if not s.get("enabled"):
            continue
        if s.get("source_id") == source_id:
            continue
        if s.get("content_hash") == text_hash:
            return True, s["source_id"]
    return False, None


# ── main intake function ──────────────────────────────────────────────────────


def run_source_intake(
    source: dict,
    all_sources: list[dict] | None = None,
    write_evidence: bool = False,
) -> dict:
    """
    Run a full intake check on a source entry.

    Parameters
    ----------
    source : dict
        A sources.json entry. Required keys: 'url'. Optional: 'source_id',
        'expected_min_length', 'wait_for_selector', 'content_selector', 'fetch_method'.
    all_sources : list[dict] | None
        All enabled sources (for hash collision check). Pass the full sources.json list.
    write_evidence : bool
        If True, write raw/normalized snapshots and proof.json. Requires DB access.

    Returns
    -------
    dict with fields:
        source_id, url, status, chars_raw, chars_normalized, pdf_chars,
        nav_shell_detected, hash_collision, collision_source_id, quality,
        evidence_written, errors, notes
    """
    url = source.get("url", "")
    source_id = source.get("source_id", "")
    expected_min = source.get("expected_min_length", _GLOBAL_MIN_CHARS)
    wait_selector = source.get("wait_for_selector")
    content_selector = source.get("content_selector")
    fetch_method = source.get("fetch_method")

    result: dict = {
        "source_id": source_id,
        "url": url,
        "status": SourceIntakeStatus.UNSUPPORTED,
        "chars_raw": 0,
        "chars_normalized": 0,
        "pdf_chars": 0,
        "nav_shell_detected": False,
        "hash_collision": False,
        "collision_source_id": None,
        "quality": "POOR",
        "content_hash": "",
        "extraction_method": "",
        "failure_reason": "",
        "remediation_hint": "",
        "evidence_written": False,
        "errors": [],
        "notes": "",
    }

    # ── 1. URL safety ─────────────────────────────────────────────────────────
    safe, reason = validate_public_url(url)
    if not safe:
        result["status"] = SourceIntakeStatus.BLOCKED
        result["failure_reason"] = reason
        result["remediation_hint"] = "Use a public http(s) URL without credentials, login, private network, or restricted portal access."
        result["errors"].append(f"URL blocked: {reason}")
        return result

    # ── 2. Fetch ──────────────────────────────────────────────────────────────
    try:
        from app.scraper import fetch_page_with_config
        html = fetch_page_with_config(
            url,
            wait_for_selector=wait_selector,
            content_selector=content_selector,
            force_playwright=(fetch_method == "playwright"),
        )
    except Exception as exc:
        if wait_selector or content_selector or fetch_method == "playwright":
            result["status"] = SourceIntakeStatus.NEEDS_SELECTOR_REVIEW
            result["remediation_hint"] = "Review the configured wait_for_selector/content_selector before activation."
        else:
            result["status"] = SourceIntakeStatus.BLOCKED
            result["remediation_hint"] = "Confirm the source is public and technically accessible."
        result["failure_reason"] = f"Fetch failed: {exc}"
        result["errors"].append(f"Fetch failed: {exc}")
        return result

    result["chars_raw"] = len(html)

    # ── 3. Extract text ───────────────────────────────────────────────────────
    try:
        from app.extractors import extract_best_text
        extracted = extract_best_text(html)
        if isinstance(extracted, tuple):
            text = str(extracted[0] or "")
            result["extraction_method"] = str(extracted[1] or "")
        elif isinstance(extracted, dict):
            text = str(extracted.get("text") or "")
            result["extraction_method"] = str(extracted.get("method") or extracted.get("source") or "")
        else:
            text = str(extracted or "")
    except Exception as exc:
        result["errors"].append(f"Extraction failed: {exc}")
        text = ""

    normalized_text = normalize_for_change_hash(text)
    result["chars_normalized"] = len(normalized_text)

    # ── 4. Nav-shell detection ────────────────────────────────────────────────
    nav_shell = is_nav_shell_only(normalized_text)
    result["nav_shell_detected"] = nav_shell

    # ── 5. Hash collision check ───────────────────────────────────────────────
    content_hash = _content_hash(normalized_text)
    result["content_hash"] = content_hash
    collision_id: str | None = None
    if all_sources and source_id:
        collision, collision_id = _check_hash_collision(content_hash, source_id, all_sources)
        result["hash_collision"] = collision
        result["collision_source_id"] = collision_id
    else:
        collision = False

    # ── 6. PDF chars (best-effort — reuse cached if available) ───────────────
    pdf_chars = source.get("pdf_chars", 0)
    result["pdf_chars"] = pdf_chars

    # ── 7. Status verdict ─────────────────────────────────────────────────────
    chars = result["chars_normalized"]

    if nav_shell or collision:
        result["status"] = SourceIntakeStatus.NAV_SHELL_ONLY
        result["failure_reason"] = "Extracted content is a navigation shell or collides with another source hash."
        result["remediation_hint"] = "Configure a precise content_selector or adapter before marking this source ready."
    elif chars == 0 or result["chars_raw"] < 200:
        result["status"] = SourceIntakeStatus.BLOCKED
        result["failure_reason"] = "No meaningful extractable content was found."
        result["remediation_hint"] = "Confirm the URL is public, accessible, and not a private portal or blocked page."
    elif chars < 100:
        result["status"] = SourceIntakeStatus.JS_RENDERING_NEEDED
        result["failure_reason"] = "Extracted text is too small for reliable monitoring."
        result["remediation_hint"] = "Use Playwright rendering and a stable content selector."
    elif chars < 500 and pdf_chars == 0:
        result["status"] = SourceIntakeStatus.JS_RENDERING_NEEDED
        result["failure_reason"] = "Extracted text is below the minimum reliable threshold."
        result["remediation_hint"] = "Use Playwright rendering and a stable content selector."
    elif chars < 500 and pdf_chars > 1000:
        result["status"] = SourceIntakeStatus.PDF_EXTRACTION_NEEDED
        result["failure_reason"] = "HTML text is thin but PDF text appears available."
        result["remediation_hint"] = "Add a PDF extraction path before activating monitoring."
    elif chars < expected_min:
        result["status"] = SourceIntakeStatus.QUALITY_DROP
        result["failure_reason"] = f"Normalized text length {chars} is below expected minimum {expected_min}."
        result["remediation_hint"] = "Review selector, rendering, or source structure before activation."
    elif chars < 1000 and not wait_selector:
        result["status"] = SourceIntakeStatus.NEEDS_SELECTOR_REVIEW
        result["failure_reason"] = "Text is present but too thin without an explicit selector."
        result["remediation_hint"] = "Add wait_for_selector/content_selector and retest."
    else:
        result["status"] = SourceIntakeStatus.CONFIRMED_ACCESSIBLE

    # ── 8. Quality label ──────────────────────────────────────────────────────
    total = chars + pdf_chars
    if total >= 5_000 and result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE:
        result["quality"] = "GOOD"
    elif result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE:
        result["quality"] = "ACCEPTABLE"
    elif total >= 1_000:
        result["quality"] = "LIMITED"
    else:
        result["quality"] = "POOR"

    # ── 9. Notes ──────────────────────────────────────────────────────────────
    notes_parts = []
    if nav_shell:
        notes_parts.append("Nav-shell detected — extracted text is primarily short navigation items.")
    if collision:
        notes_parts.append(f"Hash collision with {collision_id} — both sources extract identical content.")
    if chars < expected_min and not nav_shell and not collision:
        notes_parts.append(f"Chars ({chars}) below expected minimum ({expected_min}).")
    if pdf_chars > 0:
        notes_parts.append(f"PDF content available: {pdf_chars:,} chars.")
    result["notes"] = " ".join(notes_parts)

    # ── 10. Evidence write (optional) ────────────────────────────────────────
    if write_evidence and result["status"] == SourceIntakeStatus.CONFIRMED_ACCESSIBLE:
        try:
            _write_intake_evidence(source_id, url, html, normalized_text, content_hash)
            result["evidence_written"] = True
        except Exception as exc:
            result["errors"].append(f"Evidence write failed: {exc}")

    return result


def _write_intake_evidence(
    source_id: str, url: str, html: str, text: str, content_hash: str
) -> None:
    """Write raw/normalized snapshot for the intake result."""
    import datetime
    from app.source_runs import _write_snapshots

    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = f"intake-{now.strftime('%Y%m%dT%H%M%SZ')}"
    jur = source_id.split("-")[0] if "-" in source_id else "XX"

    _write_snapshots(
        timestamp_utc=timestamp_utc,
        market=jur,
        source_id=source_id,
        run_id=run_id,
        raw_text=html,
        normalized_text=text,
        pdf_text="",
        metadata={
            "source_id": source_id,
            "url": url,
            "run_id": run_id,
            "content_hash": content_hash,
            "intake_mode": True,
        },
    )


# ── batch readiness summary ───────────────────────────────────────────────────


def load_sources_json() -> list[dict]:
    if not _SOURCES_PATH.exists():
        return []
    with open(_SOURCES_PATH, encoding="utf-8") as f:
        return json.load(f)


def readiness_summary(sources: list[dict] | None = None) -> dict:
    """
    Return a readiness summary for all enabled sources.

    Uses stored run data (source_runs.jsonl) rather than live fetch.
    Falls back to sources.json 'status' field if no run record exists.
    """
    if sources is None:
        sources = load_sources_json()

    enabled = [s for s in sources if s.get("enabled")]

    try:
        from app.source_runs import latest_runs
        runs = latest_runs()
    except Exception:
        runs = {}

    breakdown = []
    ready = 0
    remediation = 0

    hash_to_source_ids: dict[str, list[str]] = {}
    for sid, run in runs.items():
        h = run.get("normalized_hash")
        if h:
            hash_to_source_ids.setdefault(str(h), []).append(str(sid))
    colliding_source_ids = {
        sid
        for source_ids in hash_to_source_ids.values()
        if len(set(source_ids)) > 1
        for sid in source_ids
    }

    for s in enabled:
        sid = s.get("source_id", "")
        run = runs.get(sid)
        failure_reason = ""
        remediation_hint = ""

        if run:
            chars = int(run.get("normalized_chars") or run.get("extracted_chars") or 0)
            last_run = run.get("timestamp_utc", "")[:10] if run.get("timestamp_utc") else ""
            change_status = str(run.get("change_status") or "")
            access_status = str(run.get("access_status") or "")
            quality = str(run.get("extraction_quality") or "")
            normalized_hash = run.get("normalized_hash")
            proof_path = run.get("proof_block_path")
            limitations = " ".join(str(x) for x in (run.get("limitations_notes") or []))
            expected_min = int(s.get("expected_min_length") or _GLOBAL_MIN_CHARS)

            bad_change = change_status in {"FAILED", "QUALITY_DROP", "SOURCE_STRUCTURE_CHANGED"}
            bad_access = access_status in {"failed", "blocked", "restricted"}
            bad_quality = quality not in {"GOOD", "MEDIUM", "ACCEPTABLE"}
            collision = sid in colliding_source_ids
            nav_shell = "nav" in limitations.lower() and "shell" in limitations.lower()

            if bad_change or bad_access:
                status = SourceIntakeStatus.BLOCKED
                failure_reason = f"Latest run status is not usable: change_status={change_status}, access_status={access_status}."
                remediation_hint = "Fix source access or extraction before marking this source ready."
                remediation += 1
            elif nav_shell or collision:
                status = SourceIntakeStatus.NAV_SHELL_ONLY
                failure_reason = "Latest run appears to be a nav shell or shares a normalized hash with another source."
                remediation_hint = "Add a precise selector/adapter and rerun evidence validation."
                remediation += 1
            elif bad_quality or chars < expected_min or not normalized_hash or not proof_path:
                status = SourceIntakeStatus.QUALITY_DROP
                failure_reason = "Latest run does not meet extraction quality, hash, length, or proof artifact requirements."
                remediation_hint = "Rerun source validation and confirm normalized hash plus proof artifact exist."
                remediation += 1
            else:
                status = SourceIntakeStatus.CONFIRMED_ACCESSIBLE
                ready += 1
        else:
            status = SourceIntakeStatus.UNSUPPORTED
            last_run = ""
            remediation += 1
            chars = 0
            failure_reason = "No stored source run record exists."
            remediation_hint = "Run a safe source validation with evidence recording before activation."

        breakdown.append({
            "source_id": sid,
            "name": s.get("name", ""),
            "status": status,
            "status_label": STATUS_LABELS.get(status, status),
            "severity": STATUS_SEVERITY.get(status, "error"),
            "chars": chars,
            "last_run": last_run,
            "failure_reason": failure_reason,
            "remediation_hint": remediation_hint,
        })

    return {
        "total_enabled": len(enabled),
        "confirmed_ready": ready,
        "remediation_needed": remediation,
        "breakdown": breakdown,
    }
