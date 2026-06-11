"""
RegRadar — source readiness report module.

Public API
----------
customer_quality(chars)            -> "GOOD" | "MEDIUM" | "THIN" | "FAILED"
customer_quality_label(q)          -> human label with icon
load_market_sources(jurisdiction)  -> list[dict]
load_latest_audit(jurisdiction)    -> dict  (name -> audit record)
build_readiness_report(jur, prof)  -> dict  (full readiness report)
render_readiness_terminal(report)  -> None  (print to stdout)
export_readiness_html(report)      -> Path  (write HTML to reports/)
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Quality thresholds ────────────────────────────────────────────────────────

GOOD_CHARS   = 2_000
MEDIUM_CHARS = 800

# ── Priority category groups ──────────────────────────────────────────────────

_P0_CATS: frozenset[str] = frozenset({
    "central_bank", "aml", "financial_regulator",
})
_P1_CATS: frozenset[str] = frozenset({
    "finance_ministry", "ministry_finance", "legal_acts", "legal_database",
})
_P2_CATS: frozenset[str] = frozenset({
    "company_registry",
})

_RESTRICTED_STATUSES: frozenset[str] = frozenset({
    "disabled_external_access",
    "disabled_navigation_only",
})

# ── Paths ─────────────────────────────────────────────────────────────────────

_BASE_DIR    = Path(__file__).parent.parent
_SOURCES_JSON = _BASE_DIR / "sources.json"
_REPORTS_DIR  = _BASE_DIR / "reports"

# ── ANSI helpers (terminal) ───────────────────────────────────────────────────

_R      = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_CYAN   = "\033[36m"


# ── Quality helpers ───────────────────────────────────────────────────────────

def customer_quality(chars: int) -> str:
    """Return GOOD / MEDIUM / THIN / FAILED based on extracted character count."""
    if chars >= GOOD_CHARS:
        return "GOOD"
    if chars >= MEDIUM_CHARS:
        return "MEDIUM"
    if chars > 0:
        return "THIN"
    return "FAILED"


def customer_quality_label(q: str) -> str:
    """Return human-readable label with icon for a quality string."""
    return {
        "GOOD":   "✅ Good",
        "MEDIUM": "⚡ Medium",
        "THIN":   "⚠ Thin",
        "FAILED": "❌ Failed",
    }.get(q, q)


# ── Source loading ────────────────────────────────────────────────────────────

def load_market_sources(jurisdiction: str) -> list[dict]:
    """Load all sources from sources.json filtered by jurisdiction code (e.g. 'AE')."""
    try:
        raw: list[dict] = json.loads(_SOURCES_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("load_market_sources: cannot read sources.json: %s", exc)
        return []
    jur = jurisdiction.upper()
    return [s for s in raw if s.get("jurisdiction", "").upper() == jur]


def load_latest_audit(jurisdiction: str) -> dict[str, dict]:
    """
    Load the most recent source_audit_*.json and return a dict keyed by
    source name → audit record, filtered to the given jurisdiction.
    """
    if not _REPORTS_DIR.exists():
        return {}
    audit_files = sorted(_REPORTS_DIR.glob("source_audit_*.json"), reverse=True)
    if not audit_files:
        return {}
    latest = audit_files[0]
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("load_latest_audit: cannot read %s: %s", latest, exc)
        return {}
    sources: list[dict] = data.get("sources", [])
    jur = jurisdiction.upper()
    return {
        s["name"]: s
        for s in sources
        if s.get("jurisdiction", "").upper() == jur
    }


# ── Report builder ────────────────────────────────────────────────────────────

def build_readiness_report(
    jurisdiction: str,
    profile: str = "fintech",
    record_run: bool = False,
) -> dict:
    """
    Build a full source readiness report dict for the given market+profile.

    When record_run=True, live source diagnostics are run for active sources and
    appended to the source run history JSONL. Externally restricted sources are
    recorded without a network call.
    """
    from app.source_runs import (
        append_run,
        latest_runs,
        make_source_id,
        record_from_source_result,
        restricted_record,
    )
    from app.source_tester import test_source_url

    jur = jurisdiction.upper()
    all_sources = load_market_sources(jur)
    audit_map   = load_latest_audit(jur)
    history_map = latest_runs(jur)
    run_id = f"{jur}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"

    p0: list[dict] = []
    p1: list[dict] = []
    p2: list[dict] = []
    blocked: list[dict] = []

    sources_active = 0
    sources_blocked = 0
    sources_restricted = 0
    limitations: list[str] = []

    for src in all_sources:
        name     = src.get("name", "")
        cat      = src.get("category", "other")
        status   = src.get("status", "active")
        url      = src.get("url", "")

        audit_rec = audit_map.get(name, {})
        chars = int(audit_rec.get("extracted_chars", 0) or 0)
        error = audit_rec.get("error") or ""
        quality = customer_quality(chars)

        entry: dict[str, Any] = {
            "source_id": make_source_id(src),
            "name":     name,
            "category": cat,
            "url":      url,
            "status":   status,
            "chars":    chars,
            "quality":  quality,
            "quality_label": customer_quality_label(quality),
            "error":    error or None,
            "limitations": [],
            "last_run": None,
            "change_status": None,
            "pdf_links_count": 0,
            "pdf_extracted_chars": 0,
        }

        if status in _RESTRICTED_STATUSES:
            sources_blocked += 1
            if status == "disabled_external_access":
                sources_restricted += 1
                entry["limitations"].append("Geo-blocked or JS SPA — requires dedicated adapter or alternative source.")
            elif status == "disabled_navigation_only":
                entry["limitations"].append("Navigation-only SPA — content not extractable without a custom adapter.")

            if record_run and status == "disabled_navigation_only":
                try:
                    result = test_source_url(url, include_documents=True, include_text=True)
                    run_record = append_run(record_from_source_result(
                        run_id=run_id,
                        source=src,
                        result=result,
                        limitations_notes=entry["limitations"],
                    ))
                except Exception as exc:
                    run_record = append_run(restricted_record(
                        run_id=run_id,
                        source=src,
                        limitations_notes=entry["limitations"] + [f"Diagnostic failed: {type(exc).__name__}: {exc}"],
                    ))
                _apply_run_record(entry, run_record)
                history_map[entry["source_id"]] = run_record
            elif record_run:
                run_record = append_run(restricted_record(
                    run_id=run_id,
                    source=src,
                    limitations_notes=entry["limitations"],
                ))
                _apply_run_record(entry, run_record)
                history_map[entry["source_id"]] = run_record
            else:
                hist = history_map.get(entry["source_id"])
                if hist:
                    _apply_run_record(entry, hist)

            blocked.append(entry)
            limitations.append(f"{name}: {entry['limitations'][0]}")
            continue

        sources_active += 1

        if record_run:
            try:
                result = test_source_url(url, include_documents=True, include_text=True)
            except Exception as exc:
                result = {
                    "url": url,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "extracted_chars": 0,
                    "extraction_quality": "failed",
                    "recommended_method": "failed",
                }
            run_record = append_run(record_from_source_result(
                run_id=run_id,
                source=src,
                result=result,
                limitations_notes=[],
            ))
            _apply_run_record(entry, run_record)
            history_map[entry["source_id"]] = run_record
            chars = entry["chars"]
            quality = entry["quality"]
        else:
            hist = history_map.get(entry["source_id"])
            if hist:
                _apply_run_record(entry, hist)
                chars = entry["chars"]
                quality = entry["quality"]

        if quality == "THIN":
            entry["limitations"].append(f"Low content ({chars} chars) — may be a listing page.")
        elif quality == "FAILED":
            entry["limitations"].append("Extraction failed — check source availability or adapter.")
        if error and not entry.get("error"):
            entry["error"] = error
        if entry.get("error"):
            entry["limitations"].append(f"Last error: {str(entry['error'])[:120]}")

        if cat in _P0_CATS:
            p0.append(entry)
        elif cat in _P1_CATS:
            p1.append(entry)
        else:
            p2.append(entry)

    pilot_sources = p0 + p1
    good_or_medium = [s for s in pilot_sources if s["quality"] in ("GOOD", "MEDIUM")]
    pilot_ready    = len(good_or_medium) >= 4

    if len([s for s in p0 if s["quality"] in ("GOOD", "MEDIUM")]) >= 2:
        pilot_verdict = "FREE_CHECK_READY"
        pilot_note = (
            f"Core regulatory sources ({jur}) are extracting cleanly. "
            "A free source check can be offered to prospects immediately: "
            "3-5 sources tested, readiness snapshot, limitations disclosed."
        )
    elif pilot_ready:
        pilot_verdict = "PILOT_READY"
        pilot_note = (
            f"Sufficient P0/P1 sources active for a paid pilot ({len(good_or_medium)} GOOD/MEDIUM). "
            "Recommend offering a 2-week pilot with CBUAE + VARA + UAEFIU as the P0 core."
        )
    else:
        pilot_verdict = "NEEDS_MORE_WORK"
        pilot_note = (
            f"Only {len(good_or_medium)} P0/P1 sources are GOOD/MEDIUM. "
            "Resolve blocked sources or add alternative coverage before pilot."
        )

    return {
        "market":             jur,
        "profile":            profile,
        "generated_at":       datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources_active":     sources_active,
        "sources_blocked":    sources_blocked,
        "sources_restricted": sources_restricted,
        "p0_sources":         p0,
        "p1_sources":         p1,
        "p2_sources":         p2,
        "blocked_sources":    blocked,
        "pilot_ready":        pilot_ready,
        "pilot_verdict":      pilot_verdict,
        "pilot_note":         pilot_note,
        "limitations":        limitations,
        "record_run":         record_run,
        "run_id":             run_id if record_run else None,
    }


def _apply_run_record(entry: dict, record: dict) -> None:
    """Overlay source run evidence onto a readiness row."""
    entry["last_run"] = record.get("timestamp_utc")
    entry["change_status"] = record.get("change_status")
    entry["chars"] = int(record.get("extracted_chars") or 0)
    entry["quality"] = record.get("extraction_quality") or entry.get("quality")
    entry["quality_label"] = customer_quality_label(entry["quality"])
    entry["pdf_links_count"] = int(record.get("pdf_links_count") or 0)
    entry["pdf_extracted_chars"] = int(record.get("pdf_extracted_chars") or 0)
    if record.get("error"):
        entry["error"] = record["error"]
    note = record.get("limitations_notes")
    if note and note not in entry["limitations"]:
        entry["limitations"].append(note)


# ── Terminal renderer ─────────────────────────────────────────────────────────

def _quality_color(q: str) -> str:
    return {
        "GOOD":   _GREEN,
        "MEDIUM": _YELLOW,
        "THIN":   _YELLOW,
        "FAILED": _RED,
    }.get(q, _DIM)


def render_readiness_terminal(report: dict) -> None:
    """Print a formatted terminal report for the readiness dict."""
    sep  = "─" * 68
    sep2 = "═" * 68

    print(sep2)
    print(f"  {_BOLD}StatuteProof — Source Readiness Report{_R}  "
          f"{_CYAN}{report['market']}{_R} / {_DIM}{report['profile']}{_R}")
    print(f"  {_DIM}Generated: {report['generated_at']}{_R}")
    print(sep2)

    verdict = report["pilot_verdict"]
    vcolor = _GREEN if verdict == "FREE_CHECK_READY" else (_YELLOW if verdict == "PILOT_READY" else _RED)
    print(f"\n  Verdict: {vcolor}{_BOLD}{verdict}{_R}")
    print(f"  {report['pilot_note']}\n")

    print(f"  Active sources : {_GREEN}{report['sources_active']}{_R}")
    print(f"  Blocked sources: {_RED}{report['sources_blocked']}{_R}")
    print()

    def _print_group(label: str, sources: list[dict]) -> None:
        if not sources:
            return
        print(f"  {_BOLD}{label}{_R}")
        print(sep)
        for s in sources:
            q   = s["quality"]
            col = _quality_color(q)
            ql  = s["quality_label"]
            c   = s["chars"]
            cat = s["category"]
            change = s.get("change_status") or "—"
            pdf_c = int(s.get("pdf_extracted_chars") or 0)
            print(f"  {col}{ql:<14}{_R}  {s['name']:<40}  "
                  f"{_DIM}{c:>7,}c{_R}  {_DIM}{change:<12}{_R}  [{cat}]")
            if pdf_c:
                print(f"    {_DIM}PDF text: {pdf_c:,} chars from {s.get('pdf_links_count', 0)} discovered PDF link(s){_R}")
            for lim in s.get("limitations", []):
                print(f"    {_DIM}⚠ {lim}{_R}")
        print()

    _print_group("P0 — Core Regulatory (central_bank / aml / financial_regulator)",
                 report["p0_sources"])
    _print_group("P1 — Legislative / Ministry",
                 report["p1_sources"])
    _print_group("P2 — Supporting Sources",
                 report["p2_sources"])

    if report["blocked_sources"]:
        print(f"  {_BOLD}Blocked / Restricted{_R}")
        print(sep)
        for s in report["blocked_sources"]:
            print(f"  {_RED}❌ {s['name']:<42}{_R}  [{s['status']}]")
            for lim in s.get("limitations", []):
                print(f"    {_DIM}{lim}{_R}")
        print()

    if report["limitations"]:
        print(f"  {_BOLD}Known Limitations{_R}")
        print(sep)
        for lim in report["limitations"]:
            print(f"  • {_DIM}{lim}{_R}")
        print()

    print(sep2)
    print(f"  {_DIM}Not legal advice. For internal use only.{_R}\n")


# ── HTML export ───────────────────────────────────────────────────────────────

def _q_badge(q: str) -> str:
    styles = {
        "GOOD":   "background:#0d7a4e;color:#d4fce8",
        "MEDIUM": "background:#7a5f00;color:#fff3b0",
        "THIN":   "background:#7a3a00;color:#ffe0b0",
        "FAILED": "background:#7a0000;color:#ffd0d0",
    }
    labels = {
        "GOOD": "✅ Good", "MEDIUM": "⚡ Medium",
        "THIN": "⚠ Thin", "FAILED": "❌ Failed",
    }
    style = styles.get(q, "background:#333;color:#ccc")
    label = labels.get(q, q)
    return f'<span style="padding:2px 8px;border-radius:4px;font-size:0.82em;{style}">{label}</span>'


def _status_badge(status: str) -> str:
    if status in ("disabled_external_access", "disabled_navigation_only"):
        return '<span style="padding:2px 8px;border-radius:4px;font-size:0.82em;background:#7a0000;color:#ffd0d0">❌ Blocked</span>'
    return '<span style="padding:2px 8px;border-radius:4px;font-size:0.82em;background:#0d4a7a;color:#b0d8ff">✔ Active</span>'


def _source_rows(sources: list[dict], priority_label: str) -> str:
    rows = []
    for s in sources:
        lims = "; ".join(s.get("limitations", [])) or "—"
        change = s.get("change_status") or "—"
        pdf_chars = int(s.get("pdf_extracted_chars") or 0)
        rows.append(
            f"<tr>"
            f"<td>{s['name']}</td>"
            f"<td><code>{s['category']}</code></td>"
            f"<td>{priority_label}</td>"
            f"<td>{_status_badge(s['status'])}</td>"
            f"<td>{_q_badge(s['quality'])}</td>"
            f"<td>{change}</td>"
            f"<td style='text-align:right'>{s['chars']:,}</td>"
            f"<td style='text-align:right'>{pdf_chars:,}</td>"
            f"<td style='color:#8bb'>{lims}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def export_readiness_html(report: dict) -> Path:
    """Generate a self-contained dark-themed HTML report and return its path."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    date_str  = datetime.now().strftime("%Y-%m-%d")
    market    = report["market"]
    fname     = f"source_readiness_{market}_{date_str}.html"
    out_path  = _REPORTS_DIR / fname

    verdict    = report["pilot_verdict"]
    vcolor_css = (
        "#16D9F5" if verdict == "FREE_CHECK_READY" else
        "#f5c616" if verdict == "PILOT_READY" else
        "#f55"
    )

    # Combine all active source rows
    all_rows = (
        _source_rows(report["p0_sources"], "P0")
        + "\n"
        + _source_rows(report["p1_sources"], "P1")
        + "\n"
        + _source_rows(report["p2_sources"], "P2")
        + "\n"
        + _source_rows(report["blocked_sources"], "Blocked")
    )

    lim_items = "".join(
        f"<li>{lim}</li>" for lim in report["limitations"]
    ) or "<li>No critical limitations detected.</li>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>StatuteProof — Source Readiness {market}</title>
<style>
  :root {{
    --bg:    #07111F;
    --bg2:   #0d1e2e;
    --bg3:   #122030;
    --cyan:  #16D9F5;
    --text:  #c8d8e8;
    --dim:   #6a8aaa;
    --border:#1e3040;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Segoe UI',Arial,sans-serif;
         font-size:14px; line-height:1.6; padding:32px 24px; }}
  header {{ border-bottom:1px solid var(--border); padding-bottom:16px; margin-bottom:24px; }}
  .brand {{ color:var(--cyan); font-size:1.5em; font-weight:700; letter-spacing:1px; }}
  .subtitle {{ color:var(--dim); font-size:0.9em; margin-top:4px; }}
  h2 {{ color:var(--cyan); font-size:1em; text-transform:uppercase;
        letter-spacing:1px; margin:24px 0 8px; }}
  .verdict {{ font-size:1.2em; font-weight:700; color:{vcolor_css}; margin:8px 0; }}
  .pilot-note {{ background:var(--bg2); border:1px solid var(--border);
                 border-left:3px solid {vcolor_css}; padding:12px 16px;
                 border-radius:4px; margin:12px 0 20px; color:var(--text); }}
  .stats {{ display:flex; gap:24px; margin-bottom:20px; }}
  .stat {{ background:var(--bg2); border:1px solid var(--border);
           border-radius:6px; padding:12px 20px; min-width:140px; }}
  .stat-num {{ font-size:2em; font-weight:700; color:var(--cyan); }}
  .stat-label {{ color:var(--dim); font-size:0.82em; }}
  table {{ width:100%; border-collapse:collapse; margin-bottom:24px; }}
  th {{ background:var(--bg3); color:var(--cyan); text-align:left;
        padding:8px 10px; font-size:0.82em; text-transform:uppercase;
        letter-spacing:0.5px; border-bottom:1px solid var(--border); }}
  td {{ padding:8px 10px; border-bottom:1px solid var(--border);
        vertical-align:top; }}
  tr:hover td {{ background:var(--bg2); }}
  code {{ background:var(--bg3); padding:1px 5px; border-radius:3px;
          font-size:0.82em; color:#9dbfe0; }}
  ul {{ padding-left:20px; }}
  li {{ margin-bottom:4px; color:var(--dim); }}
  .disclaimer {{ margin-top:32px; padding:12px 16px; background:var(--bg2);
                 border:1px solid var(--border); border-radius:4px;
                 color:var(--dim); font-size:0.82em; }}
  footer {{ margin-top:32px; color:var(--dim); font-size:0.78em;
            border-top:1px solid var(--border); padding-top:12px; }}
</style>
</head>
<body>
<header>
  <div class="brand">StatuteProof</div>
  <div class="subtitle">
    Source Readiness Report &mdash; {market} ({report['profile']})
    &nbsp;&bull;&nbsp; Generated: {report['generated_at']}
  </div>
</header>

<h2>Executive Summary</h2>
<div class="verdict">{verdict.replace("_", " ")}</div>
<div class="pilot-note">{report['pilot_note']}</div>

<div class="stats">
  <div class="stat">
    <div class="stat-num">{report['sources_active']}</div>
    <div class="stat-label">Active Sources</div>
  </div>
  <div class="stat">
    <div class="stat-num">{report['sources_blocked']}</div>
    <div class="stat-label">Blocked / Restricted</div>
  </div>
</div>

<h2>Source Readiness Table</h2>
<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Category</th>
      <th>Priority</th>
      <th>Status</th>
      <th>Quality</th>
      <th>Change</th>
      <th style="text-align:right">Chars</th>
      <th style="text-align:right">PDF chars</th>
      <th>Limitations</th>
    </tr>
  </thead>
  <tbody>
{all_rows}
  </tbody>
</table>

<h2>Pilot Source Set — {market} Fintech (P0)</h2>
<p style="color:var(--dim);margin-bottom:12px">
  P0 sources are the minimum viable monitoring set for a paid pilot.
  They cover central banking, AML/CFT, and financial regulation.
</p>
<table>
  <thead>
    <tr><th>Name</th><th>Category</th><th>Quality</th><th>Chars</th></tr>
  </thead>
  <tbody>
{"".join(f"<tr><td>{s['name']}</td><td><code>{s['category']}</code></td><td>{_q_badge(s['quality'])}</td><td style='text-align:right'>{s['chars']:,}</td></tr>" for s in report['p0_sources'])}
  </tbody>
</table>

<h2>Known Limitations</h2>
<ul>{lim_items}</ul>

<h2>Pilot Recommendation</h2>
<div class="pilot-note">
  <strong>Verdict:</strong> {verdict.replace("_", " ")}<br>
  {report['pilot_note']}
</div>

<div class="disclaimer">
  &#9888; <strong>Not legal advice.</strong>
  This report reflects automated extraction quality testing only.
  Source availability and content may change without notice.
  This document is for internal StatuteProof use and prospect evaluation only.
  It does not constitute legal, regulatory, or compliance advice.
</div>

<footer>
  StatuteProof &mdash; Regulatory Intelligence Platform &mdash; {report['generated_at']}
</footer>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    logger.info("export_readiness_html: wrote %s", out_path)
    return out_path
