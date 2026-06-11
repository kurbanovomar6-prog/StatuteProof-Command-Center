"""
RegRadar — source audit and adapter-queue engine.

No AI, no Telegram, no DB writes, no sources.json modification.
One failing source never stops the audit.

Public API
----------
run_audit()              → list[dict]   audit every source in sources.json
print_audit_report()     → None         full terminal report
print_adapter_queue()    → None         filtered + sorted adapter queue
export_audit_json()      → Path         write reports/source_audit_YYYY-MM-DD.json
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from app.health import _check_one         # uses same adapter+scraper stack as pipeline
from app.sources import load_sources

logger = logging.getLogger(__name__)

_REPORTS_DIR = Path(__file__).parent.parent / "reports"

# 1 000 chars → good enough; below this → needs adapter
_GOOD_THRESHOLD = 1_000

_IMPORTANT_CATEGORIES: frozenset[str] = frozenset({
    "central_bank",
    "aml",
    "financial_regulator",
    "tax",
    "legal_database",
    "legal_acts",
    "finance_ministry",
    "ministry_finance",
    "international",
    "international_standard_setter",
})

# Source statuses that are externally restricted — not actionable via local adapter
_RESTRICTED_STATUSES: frozenset[str] = frozenset({
    "disabled_external_access",   # geo-block / JS SPA / protocol error
    "disabled_navigation_only",   # navigation-only extraction trap
})

# Adapter-queue sort key (lower = shown first)
# key = (group, content_state) → int
_QUEUE_RANK: dict[tuple[str, str], int] = {
    ("enabled",  "failed"):      1,
    ("enabled",  "low_content"): 2,
    ("limited",  "low_content"): 3,
    ("disabled", "failed"):      4,
    ("disabled", "low_content"): 5,
}

_SEP  = "─" * 68
_SEP2 = "═" * 68


# ── Internal helpers ──────────────────────────────────────────────────────────

def _audit_quality(chars: int) -> str:
    """Apply the 1 000-char threshold used by the audit (stricter than health.py)."""
    if chars >= _GOOD_THRESHOLD:
        return "good"
    if chars > 0:
        return "low_content"
    return "failed"


def _requires_adapter(chars: int, error: str | None) -> bool:
    if error:
        return True          # fetch failed entirely
    return chars < _GOOD_THRESHOLD


def _priority(source: dict, chars: int, error: str | None) -> str:
    status = source.get("status", "active")

    # Externally restricted sources are documented but not adapter-fixable — always LOW
    if status in _RESTRICTED_STATUSES:
        return "LOW"

    enabled   = source.get("enabled", False)
    category  = source.get("category", "")
    important = category in _IMPORTANT_CATEGORIES
    failing   = bool(error) or chars == 0
    needs     = chars < _GOOD_THRESHOLD

    if enabled and failing:
        return "HIGH"
    if enabled and needs and important:
        return "HIGH"
    if enabled and needs:
        return "MEDIUM"
    if not enabled and important and (failing or needs):
        return "MEDIUM"
    if not enabled and status == "limited" and needs:
        return "MEDIUM"
    return "LOW"


def _suggest_next_step(source: dict, chars: int, error: str | None) -> str:
    status = source.get("status", "active")

    # Externally restricted — specific guidance, not a generic adapter task
    if status == "disabled_external_access":
        return (
            "Externally inaccessible (geo-block / JS SPA zero-extraction / protocol error). "
            "Build a jurisdiction-proxied adapter or locate an alternate official endpoint "
            "(e.g. SharePoint path, Arabic/English subpage, API, RSS feed)."
        )
    if status == "disabled_navigation_only":
        return (
            "SPA site renders identical navigation-only text on every page. "
            "Build a source-specific adapter targeting the regulatory publications "
            "or circulars API endpoint directly."
        )

    enabled  = source.get("enabled", False)
    category = source.get("category", "")

    # No adapter needed
    if not _requires_adapter(chars, error):
        if not enabled:
            return "Keep disabled until client requests this jurisdiction/source."
        return "No action needed — extraction quality is sufficient."

    # Fetch completely failed — diagnose the error type
    if error:
        err = error.lower()
        if any(k in err for k in ("name_not_resolved", "gaierror", "nameresolution", "name resolution")):
            return "Find correct official URL or updated domain."
        if any(k in err for k in ("ssl", "certificate", "cert_")):
            return "Check alternate official domain, http/https variant, or browser-accessible URL."
        if "timeout" in err:
            return "Site may be slow or unreliable; test manually and consider a retry adapter."
        return "Investigate error; test URL manually then build adapter if page loads in browser."

    # Extracted something but below threshold
    if category in ("central_bank", "aml", "financial_regulator"):
        return "Build source-specific adapter or locate official press/regulatory API endpoint."
    if category in ("tax", "legal_database", "legal_acts"):
        return (
            "Search for official legal acts endpoint or check whether site publishes "
            "regulatory updates through PDF documents."
        )
    if category in ("finance_ministry", "ministry_finance"):
        return "Investigate public sitemap/API/PDF links or build source-specific adapter."
    if category in ("international", "international_standard_setter"):
        return "Check for RSS feed or publications API; build lightweight adapter."
    return "Investigate public sitemap/API/PDF links or build source-specific adapter."


def _queue_group(source: dict) -> str:
    if source.get("enabled"):
        return "enabled"
    if source.get("status") == "limited":
        return "limited"
    return "disabled"


def _queue_sort_key(record: dict) -> tuple[int, int]:
    content_state = "failed" if record["extraction_quality"] == "failed" else "low_content"
    group_rank    = _QUEUE_RANK.get((_queue_group(record["_source"]), content_state), 99)
    prio_rank     = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(record["priority"], 3)
    return (group_rank, prio_rank)


# ── Core audit engine ─────────────────────────────────────────────────────────

def _audit_one(source: dict) -> dict[str, Any]:
    """Run health check on one source and return an audit record. Never raises."""
    health = _check_one(source)

    chars   = health["extracted_chars"]
    method  = health["extraction_method"]
    error   = health.get("error")

    quality     = _audit_quality(chars)
    needs       = _requires_adapter(chars, error)
    verdict     = "can_monitor" if not needs else ("cannot_monitor" if quality == "failed" else "needs_adapter")
    prio        = _priority(source, chars, error) if needs else "NONE"
    next_step   = _suggest_next_step(source, chars, error)

    return {
        "name":                source.get("name", source.get("url", "?")),
        "url":                 source.get("url", ""),
        "jurisdiction":        source.get("jurisdiction", ""),
        "category":            source.get("category", ""),
        "enabled":             source.get("enabled", False),
        "source_status":       source.get("status", "active"),
        "extracted_chars":     chars,
        "extraction_quality":  quality,
        "best_extractor":      method,
        "verdict":             verdict,
        "requires_adapter":    needs,
        "priority":            prio,
        "suggested_next_step": next_step,
        "error":               error,
        # kept only for sort-key; excluded from JSON export
        "_source":             source,
    }


def run_audit(verbose: bool = True) -> list[dict]:
    """
    Audit every source in sources.json.

    One failed source never stops the run.
    No AI, no Telegram, no DB writes.
    """
    sources = load_sources()
    total   = len(sources)
    results = []

    for idx, source in enumerate(sources, 1):
        name   = source.get("name", source.get("url", "?"))
        marker = "enabled" if source.get("enabled") else "disabled"

        if verbose:
            print(f"  [{idx:2}/{total}] {name[:52]}  ({marker}) …", flush=True)

        try:
            record = _audit_one(source)
        except Exception as exc:
            logger.error("source-audit: unexpected error for %r: %s", name, exc)
            enabled = source.get("enabled", False)
            record = {
                "name":                name,
                "url":                 source.get("url", ""),
                "jurisdiction":        source.get("jurisdiction", ""),
                "category":            source.get("category", ""),
                "enabled":             enabled,
                "source_status":       source.get("status", "active"),
                "extracted_chars":     0,
                "extraction_quality":  "failed",
                "best_extractor":      "none",
                "verdict":             "cannot_monitor",
                "requires_adapter":    True,
                "priority":            "HIGH" if enabled else "MEDIUM",
                "suggested_next_step": "Investigate unexpected audit error; test URL manually.",
                "error":               f"{type(exc).__name__}: {exc}",
                "_source":             source,
            }

        results.append(record)

        if verbose:
            chars   = record["extracted_chars"]
            quality = record["extraction_quality"]
            adp_tag = "⚠  needs_adapter" if record["requires_adapter"] else "✓  ok"
            print(f"           {quality:12}  {chars:6,}c  {adp_tag}", flush=True)

    return results


# ── Terminal reporters ─────────────────────────────────────────────────────────

def print_audit_report(records: list[dict]) -> None:
    total     = len(records)
    good      = sum(1 for r in records if r["extraction_quality"] == "good")
    low       = sum(1 for r in records if r["extraction_quality"] == "low_content")
    failed    = sum(1 for r in records if r["extraction_quality"] == "failed")
    needs_adp = sum(1 for r in records if r["requires_adapter"])
    disabled  = sum(1 for r in records if not r["enabled"])

    print()
    print(_SEP2)
    print("  StatuteProof — Source Audit Report")
    print(_SEP2)
    print(f"  Total sources     : {total}")
    print(f"  Good (≥1 000 ch)  : {good}")
    print(f"  Low content       : {low}")
    print(f"  Failed            : {failed}")
    print(f"  Needs adapter     : {needs_adp}")
    print(f"  Disabled          : {disabled}")
    print(_SEP2)

    for r in records:
        en_tag  = "enabled"  if r["enabled"] else "disabled"
        adp_tag = "yes" if r["requires_adapter"] else "no"
        prio    = f"  Priority: {r['priority']}" if r["requires_adapter"] else ""
        print()
        print(f"  {r['name'][:62]}")
        print(f"  {r['jurisdiction']} — {r['category']} — {en_tag}")
        print(f"  Quality: {r['extraction_quality']}")
        print(f"  Extracted: {r['extracted_chars']:,} chars")
        print(f"  Best extractor: {r['best_extractor']}")
        print(f"  Verdict: {r['verdict']}")
        print(f"  Requires adapter: {adp_tag}{prio}")
        if r["requires_adapter"]:
            print(f"  Suggested next step: {r['suggested_next_step']}")
        if r["error"]:
            print(f"  Error: {r['error'][:100]}")

    print()
    print(_SEP2)


def print_adapter_queue(records: list[dict]) -> None:
    # Split: known restrictions (documented, not locally fixable) vs actionable tasks
    restricted_items = [
        r for r in records
        if r.get("source_status", "") in _RESTRICTED_STATUSES
    ]
    queue = [
        r for r in records
        if r["requires_adapter"]
        and r.get("source_status", "") not in _RESTRICTED_STATUSES
    ]
    queue.sort(key=_queue_sort_key)

    high   = sum(1 for r in queue if r["priority"] == "HIGH")
    medium = sum(1 for r in queue if r["priority"] == "MEDIUM")
    low_n  = sum(1 for r in queue if r["priority"] == "LOW")

    print()
    print(_SEP2)
    print("  StatuteProof — Adapter Queue")
    print(_SEP2)
    print(f"  Actionable adapter tasks : {len(queue)}")
    print(f"  HIGH priority            : {high}")
    print(f"  MEDIUM priority          : {medium}")
    print(f"  LOW priority             : {low_n}")
    print(f"  Known restrictions       : {len(restricted_items)}  (geo-block / JS SPA / protocol — documented)")
    print(_SEP2)

    for rank, r in enumerate(queue, 1):
        en_tag = "enabled" if r["enabled"] else "disabled"
        print()
        print(f"  #{rank}  {r['name'][:60]}")
        print(f"       {r['jurisdiction']} — {r['category']}")
        print(f"  Status      : {en_tag} / {r['source_status']}")
        print(f"  Quality     : {r['extraction_quality']}")
        print(f"  Extracted   : {r['extracted_chars']:,} chars")
        print(f"  Extractor   : {r['best_extractor']}")
        if r["error"]:
            print(f"  Error       : {r['error'][:80]}")
        print(f"  Priority    : {r['priority']}")
        print(f"  Next step   : {r['suggested_next_step']}")

    if restricted_items:
        print()
        print(_SEP)
        print("  KNOWN RESTRICTIONS  (externally blocked — not actionable via local adapter)")
        print(_SEP)
        for r in restricted_items:
            print()
            print(f"  {r['name'][:62]}")
            print(f"  {r['jurisdiction']} — {r['category']} — {r['source_status']}")
            print(f"  Next step : {r['suggested_next_step']}")

    print()
    print(_SEP2)


# ── JSON export ───────────────────────────────────────────────────────────────

def export_audit_json(records: list[dict], reports_dir: Path | None = None) -> Path:
    """
    Write reports/source_audit_YYYY-MM-DD.json.
    Strips the internal _source key — no secrets in the output.
    """
    out_dir = reports_dir or _REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"source_audit_{date.today().isoformat()}.json"

    clean = [{k: v for k, v in r.items() if k != "_source"} for r in records]

    payload = {
        "generated":     date.today().isoformat(),
        "total":         len(clean),
        "needs_adapter": sum(1 for r in clean if r["requires_adapter"]),
        "good":          sum(1 for r in clean if r["extraction_quality"] == "good"),
        "low_content":   sum(1 for r in clean if r["extraction_quality"] == "low_content"),
        "failed":        sum(1 for r in clean if r["extraction_quality"] == "failed"),
        "sources":       clean,
    }

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
