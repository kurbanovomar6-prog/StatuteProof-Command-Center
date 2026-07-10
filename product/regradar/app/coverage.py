"""
RegRadar — Coverage Dashboard.

Generates an operational coverage report by jurisdiction, region and
category.  Uses the latest source-audit JSON from reports/ when
available; falls back to sources.json metadata when no audit exists.

No AI.  No Telegram.  No DB writes.  No sources.json modification.
One failed source never breaks the report.

Public API
----------
generate_coverage_report(use_existing_audit=True)  → dict
print_coverage_report(report, jurisdiction=None, category=None)  → None
export_coverage_json(report)                        → Path
build_coverage_html(report)                         → str
export_coverage_html(report)                        → Path
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import date
from pathlib import Path

from app.sources import load_sources

logger = logging.getLogger(__name__)

_REPORTS_DIR = Path(__file__).parent.parent / "reports"

# ── Jurisdiction / region metadata ────────────────────────────────────────────

_JURISDICTION_NAME: dict[str, str] = {
    "RU":  "Russia",
    "KZ":  "Kazakhstan",
    "AZ":  "Azerbaijan",
    "BY":  "Belarus",
    "UZ":  "Uzbekistan",
    "GE":  "Georgia",
    "AM":  "Armenia",
    "INT": "International",
    "TR":  "Türkiye",
    "AE":  "UAE",
    "SA":  "Saudi Arabia",
    "SG":  "Singapore",
}

_REGION: dict[str, str] = {
    "RU":  "Eastern Europe",
    "BY":  "Eastern Europe",
    "KZ":  "Central Asia",
    "UZ":  "Central Asia",
    "AZ":  "South Caucasus",
    "GE":  "South Caucasus",
    "AM":  "South Caucasus",
    "INT": "International",
    "TR":  "Middle East & Türkiye",
    "AE":  "Middle East & Türkiye",
    "SA":  "Middle East & Türkiye",
    "SG":  "Asia-Pacific",
}

_CATEGORY_LABEL: dict[str, str] = {
    "central_bank":                 "Central Bank",
    "finance_ministry":             "Finance Ministry",
    "aml":                          "AML / Financial Intelligence",
    "financial_regulator":          "Financial Regulator",
    "international":                "International Organisation",
    "international_standard_setter":"International Standard Setter",
    "legal_acts":                   "Legal Acts Database",
    "ministry_finance":             "Ministry of Finance",
    "tax":                          "Tax Authority",
    "data_protection":              "Data Protection / Privacy",
    "company_regulator":            "Business / Company Regulator",
    "cyber":                        "Cyber & Digital Regulation",
    "competition":                  "Competition & Consumer Authority",
}

# ── Scoring constants ─────────────────────────────────────────────────────────

# Points awarded per source based on (quality, enabled) combination.
# Max possible per enabled source  = 4  (good + enabled)
# Max possible per disabled source = 2  (good + disabled)
#
# Scoring rationale (documented for clients):
#   good + enabled    → 4  perfect operational readiness
#   good + disabled   → 2  quality confirmed, not yet activated
#   low_content + en  → 1  active but needs improvement
#   low_content + dis → 0  not in use, low quality
#   failed + enabled  → -1 active source is broken (worst case)
#   failed + disabled → 0  inactive failure, no impact
#   unknown + enabled → 2  benefit of the doubt for active (metadata-only)
#   unknown + disabled→ 1  benefit of the doubt for mapped inventory
#
# Sources with status in _EXCLUDED_FROM_SCORE are excluded from BOTH numerator
# and denominator — they are documented as externally restricted (geo-block,
# JS SPA with zero extraction, HTTP2 protocol errors) and cannot be fixed by
# a local adapter.  They are shown in reports under a separate "restricted" count.

_PTS: dict[tuple[str, bool], float] = {
    ("good",         True):  4.0,
    ("good",         False): 2.0,
    ("low_content",  True):  1.0,
    ("low_content",  False): 0.0,
    ("failed",       True): -1.0,
    ("failed",       False): 0.0,
    ("unknown",      True):  2.0,
    ("unknown",      False): 1.0,
}

# Source statuses that are excluded from both numerator and denominator.
# These represent genuine external access restrictions, not fixable by an adapter.
_EXCLUDED_FROM_SCORE: frozenset[str] = frozenset({
    "disabled_external_access",   # geo-block / JS SPA zero-extraction / protocol error
    "disabled_navigation_only",   # SPA returns only navigation text, not regulatory content
})


def _source_pts(rec: dict) -> float:
    if rec.get("source_status", "") in _EXCLUDED_FROM_SCORE:
        return 0.0
    q  = rec.get("extraction_quality", "unknown")
    en = bool(rec.get("enabled", False))
    return _PTS.get((q, en), 0.0)


def _source_scores(rec: dict) -> bool:
    """True if this source participates in the coverage score denominator."""
    return rec.get("source_status", "") not in _EXCLUDED_FROM_SCORE


def _max_pts(enabled: int, disabled: int) -> float:
    """Theoretical max if every scoreable enabled source were good and disabled were good."""
    return float(4 * enabled + 2 * disabled)


def _score(pts_total: float, max_pts: float) -> int:
    if max_pts <= 0:
        return 0
    return max(0, min(100, round(pts_total / max_pts * 100)))


def _score_label(s: int) -> str:
    if s >= 85:
        return "strong"
    if s >= 65:
        return "usable"
    if s >= 40:
        return "limited"
    return "weak"


def _coverage_level_label(score_label: str, restricted_count: int, total: int = 0) -> str:
    """
    Downgrade the score label when a jurisdiction's externally restricted sources
    make up a large fraction of its total inventory, even if scored sources pass.

    Threshold: restricted_count / total ≥ 50 % AND ≥ 4 restricted sources.
    This prevents AE (3 restricted out of 10 = 30 %) from being downgraded while
    correctly flagging SA (5 of 7 = 71 %) as limited coverage.
    """
    if restricted_count < 4:
        return score_label
    if total > 0 and (restricted_count / total) < 0.5:
        return score_label
    if score_label in ("strong", "usable"):
        return "limited"
    return score_label


# ── Audit JSON loader ─────────────────────────────────────────────────────────

def _load_latest_audit_json() -> tuple[dict | None, Path | None]:
    """
    Find the most recent source_audit_*.json in reports/.

    Returns (parsed_dict, path) or (None, None) when no file exists.
    """
    if not _REPORTS_DIR.exists():
        return None, None

    candidates = sorted(
        _REPORTS_DIR.glob("source_audit_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None, None

    path = candidates[0]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data, path
    except Exception as exc:
        logger.warning("coverage: could not load audit JSON %s: %s", path, exc)
        return None, None


# ── Group metrics builder ─────────────────────────────────────────────────────

def _group_metrics(records: list[dict]) -> dict:
    """Compute coverage metrics for a list of audit/metadata records."""
    total      = len(records)
    restricted = sum(1 for r in records if r.get("source_status", "") in _EXCLUDED_FROM_SCORE)

    # Scoring uses only non-restricted sources for the denominator
    scored     = [r for r in records if _source_scores(r)]
    sc_enabled = sum(1 for r in scored if r.get("enabled"))
    sc_disabled = len(scored) - sc_enabled

    # Inventory counts span ALL records (including restricted) for accurate reporting
    enabled   = sc_enabled   # restricted sources are never enabled, so this is consistent
    disabled  = total - enabled - restricted   # non-restricted disabled
    good      = sum(1 for r in records if r.get("extraction_quality") == "good")
    low       = sum(1 for r in records if r.get("extraction_quality") == "low_content")
    failed    = sum(1 for r in records if r.get("extraction_quality") == "failed"
                   and r.get("source_status", "") not in _EXCLUDED_FROM_SCORE)
    unknown   = sum(1 for r in records if r.get("extraction_quality") == "unknown")
    needs_adp = sum(1 for r in records if r.get("requires_adapter", False)
                   and r.get("source_status", "") not in _EXCLUDED_FROM_SCORE)

    pts  = sum(_source_pts(r) for r in records)   # restricted return 0.0
    mx   = _max_pts(sc_enabled, sc_disabled)
    sc   = _score(pts, mx)
    lbl  = _coverage_level_label(_score_label(sc), restricted, total)

    return {
        "total":         total,
        "enabled":       enabled,
        "disabled":      disabled,
        "restricted":    restricted,
        "good":          good,
        "low_content":   low,
        "failed":        failed,
        "unknown":       unknown,
        "needs_adapter": needs_adp,
        "score":         sc,
        "score_label":   lbl,
    }


# ── Insight generators ────────────────────────────────────────────────────────

def _build_strengths(by_j: dict, by_c: dict) -> list[str]:
    strengths: list[str] = []

    for jur, m in sorted(by_j.items(), key=lambda x: -x[1]["score"]):
        name = _JURISDICTION_NAME.get(jur, jur)
        if m["score"] >= 70 and m["good"] >= 2:
            strengths.append(
                f"{name}: {m['good']} good-quality source(s) — score {m['score']} ({m['score_label']})."
            )
        if m["enabled"] > 0 and m["good"] >= m["enabled"]:
            strengths.append(
                f"{name}: all {m['enabled']} active source(s) extract successfully."
            )

    for cat, m in sorted(by_c.items(), key=lambda x: -x[1]["score"]):
        label = _CATEGORY_LABEL.get(cat, cat)
        if m["score"] >= 80 and m["enabled"] > 0 and m["failed"] == 0:
            strengths.append(
                f"{label}: no failures across {m['total']} source(s)."
            )

    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for s in strengths:
        if s not in seen:
            seen.add(s)
            out.append(s)

    return out[:6]


def _build_gaps(by_j: dict, by_c: dict) -> list[str]:
    gaps: list[str] = []

    for jur, m in sorted(by_j.items(), key=lambda x: x[1]["score"]):
        name = _JURISDICTION_NAME.get(jur, jur)
        rst  = m.get("restricted", 0)

        # Externally restricted — separate message (not "failed DNS/SSL")
        if rst >= 2:
            gaps.append(
                f"{name}: {rst} source(s) externally restricted "
                "(geo-block / JS SPA / protocol error) — documented, not adapter-fixable."
            )

        # Truly broken (non-restricted)
        if m["failed"] >= 2:
            gaps.append(
                f"{name}: {m['failed']} source(s) failed — likely DNS, SSL, or connectivity errors."
            )

        if m["enabled"] == 0 and m.get("restricted", 0) == 0 and m["total"] > 0:
            gaps.append(
                f"{name}: {m['total']} source(s) mapped but none actively monitored."
            )
        if m["score"] < 40 and m["total"] >= 3:
            gaps.append(
                f"{name}: overall score {m['score']} ({m['score_label']}) — significant coverage gap."
            )

    for cat, m in sorted(by_c.items(), key=lambda x: x[1]["score"]):
        label = _CATEGORY_LABEL.get(cat, cat)
        if m["needs_adapter"] >= 3:
            gaps.append(
                f"{label}: {m['needs_adapter']} source(s) need custom adapters."
            )

    seen: set[str] = set()
    out: list[str] = []
    for g in gaps:
        if g not in seen:
            seen.add(g)
            out.append(g)

    return out[:6]


def _build_recommendations(by_j: dict, by_c: dict, needs_adapter: int) -> list[str]:
    recs: list[str] = []

    weak_j = [j for j, m in by_j.items() if m["score"] < 50 and m["total"] >= 2]
    if weak_j:
        names = ", ".join(x for x in (_JURISDICTION_NAME.get(j, j) for j in weak_j[:3]) if x is not None)
        recs.append(
            f"Validate and fix failed sources in {names} — most likely DNS or SSL issues."
        )

    no_mon = [j for j, m in by_j.items() if m["enabled"] == 0 and m["total"] >= 2]
    if no_mon:
        names = ", ".join(x for x in (_JURISDICTION_NAME.get(j, j) for j in no_mon[:4]) if x is not None)
        recs.append(
            f"Consider activating vetted sources for: {names}."
        )

    if needs_adapter >= 5:
        recs.append(
            f"{needs_adapter} sources need custom adapters. "
            "Prioritise adapters for enabled HIGH-priority sources first."
        )

    high_q_disabled = sum(
        1 for m in by_j.values()
        if m["good"] > m["enabled"] and m["score"] >= 60
    )
    if high_q_disabled:
        recs.append(
            "Several jurisdictions have good-quality disabled sources. "
            "Run 'python run.py test-source <url>' to validate before enabling."
        )

    recs.append(
        "Run 'python run.py source-audit --json' regularly to refresh coverage data."
    )

    return recs[:5]


# ── Main report builder ───────────────────────────────────────────────────────

def generate_coverage_report(use_existing_audit: bool = True) -> dict:
    """
    Build a coverage report dict.

    When use_existing_audit=True, loads the latest source_audit_*.json from
    reports/.  If no file exists, falls back to sources.json metadata with
    extraction_quality marked 'unknown'.

    Never raises.  Never makes network calls.  Never modifies any file.

    Returns
    -------
    dict — see module docstring for full structure.
    """
    sources = load_sources()

    # ── Try to load latest audit JSON ─────────────────────────────────────────
    audit_data:   dict | None = None
    audit_path:   Path | None = None
    audit_date:   str  | None = None
    audit_source: str         = "metadata_only"

    if use_existing_audit:
        audit_data, audit_path = _load_latest_audit_json()
        if audit_data and audit_path:
            audit_source = audit_path.name
            # Try to extract date from header or filename
            audit_date = audit_data.get("generated") or audit_path.stem.replace(
                "source_audit_", ""
            )

    # ── Build per-source record list ──────────────────────────────────────────
    # Merge: audit records (keyed by url) take precedence over metadata.
    audit_by_url: dict[str, dict] = {}
    if audit_data:
        for r in audit_data.get("sources", []):
            url = r.get("url", "")
            if url:
                audit_by_url[url] = r

    records: list[dict] = []
    for src in sources:
        url = src.get("url", "")
        if url in audit_by_url:
            records.append(audit_by_url[url])
        else:
            # Metadata-only record
            records.append({
                "name":               src.get("name", url),
                "url":                url,
                "jurisdiction":       src.get("jurisdiction", ""),
                "category":           src.get("category", ""),
                "enabled":            src.get("enabled", False),
                "source_status":      src.get("status", ""),
                "extraction_quality": "unknown",
                "extracted_chars":    0,
                "requires_adapter":   False,
                "best_extractor":     "unknown",
                "error":              None,
            })

    # ── Global totals ─────────────────────────────────────────────────────────
    total      = len(records)
    restricted = sum(1 for r in records if r.get("source_status", "") in _EXCLUDED_FROM_SCORE)
    # Count only non-restricted (scoreable) sources as "enabled" so the three
    # buckets — restricted, enabled, disabled — partition `total` without
    # overlap. A source that is BOTH restricted-status and enabled=True would
    # otherwise be counted in both `enabled` and `restricted`, double-subtracted
    # here, and render a negative "Disabled / mapped" figure.
    enabled    = sum(1 for r in records if r.get("enabled") and _source_scores(r))
    disabled   = total - enabled - restricted
    good       = sum(1 for r in records if r.get("extraction_quality") == "good")
    low        = sum(1 for r in records if r.get("extraction_quality") == "low_content")
    failed     = sum(1 for r in records if r.get("extraction_quality") == "failed"
                    and r.get("source_status", "") not in _EXCLUDED_FROM_SCORE)
    unknown_q  = sum(1 for r in records if r.get("extraction_quality") == "unknown")
    needs_adp  = sum(1 for r in records if r.get("requires_adapter", False)
                    and r.get("source_status", "") not in _EXCLUDED_FROM_SCORE)

    # Adapter-resolved = good sources that report an adapter extractor
    adapter_resolved = sum(
        1 for r in records
        if r.get("extraction_quality") == "good"
        and str(r.get("best_extractor", "")).startswith("adapter:")
    )

    # Score excludes restricted sources from denominator
    sc_enabled  = sum(1 for r in records if r.get("enabled") and _source_scores(r))
    sc_disabled = sum(1 for r in records if not r.get("enabled") and _source_scores(r))
    all_pts  = sum(_source_pts(r) for r in records)
    all_max  = _max_pts(sc_enabled, sc_disabled)
    overall  = _score(all_pts, all_max)
    overall_label = _coverage_level_label(_score_label(overall), restricted, total)

    # ── By jurisdiction ───────────────────────────────────────────────────────
    by_j_raw: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_j_raw[r.get("jurisdiction", "?")].append(r)

    by_jurisdiction: dict[str, dict] = {}
    for jur, recs in sorted(by_j_raw.items()):
        m = _group_metrics(recs)
        m["name"]   = _JURISDICTION_NAME.get(jur, jur)
        m["region"] = _REGION.get(jur, "Other")
        by_jurisdiction[jur] = m

    # ── By category ───────────────────────────────────────────────────────────
    by_c_raw: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_c_raw[r.get("category", "other")].append(r)

    by_category: dict[str, dict] = {}
    for cat, recs in sorted(by_c_raw.items()):
        m = _group_metrics(recs)
        m["label"] = _CATEGORY_LABEL.get(cat, cat)
        by_category[cat] = m

    # ── By region ─────────────────────────────────────────────────────────────
    by_r_raw: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        reg = _REGION.get(r.get("jurisdiction", ""), "Other")
        by_r_raw[reg].append(r)

    by_region: dict[str, dict] = {
        reg: _group_metrics(recs)
        for reg, recs in sorted(by_r_raw.items())
    }

    # ── Insights ──────────────────────────────────────────────────────────────
    top_strengths   = _build_strengths(by_jurisdiction, by_category)
    top_gaps        = _build_gaps(by_jurisdiction, by_category)
    recommendations = _build_recommendations(by_jurisdiction, by_category, needs_adp)

    return {
        "generated_at":          date.today().isoformat(),
        "audit_source":          audit_source,
        "audit_date":            audit_date,
        "total_sources":         total,
        "enabled_sources":       enabled,
        "disabled_sources":      disabled,
        "restricted_sources":    restricted,
        "good_sources":          good,
        "low_content_sources":   low,
        "failed_sources":        failed,
        "unknown_quality":       unknown_q,
        "needs_adapter":         needs_adp,
        "adapter_resolved":      adapter_resolved,
        "coverage_score":        overall,
        "score_label":           overall_label,
        "by_jurisdiction":       by_jurisdiction,
        "by_category":           by_category,
        "by_region":             by_region,
        "top_strengths":         top_strengths,
        "top_gaps":              top_gaps,
        "recommendations":       recommendations,
        "scoring_note": (
            "Coverage score is an operational quality score based on extraction "
            "quality and source readiness. Externally restricted sources "
            "(geo-blocked / JS SPA zero-extraction / protocol errors) are excluded "
            "from the score denominator and shown in the 'Restricted' column."
        ),
    }


# ── Terminal printer ──────────────────────────────────────────────────────────

_SEP2 = "═" * 68

_R      = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_CYAN   = "\033[36m"

_SCORE_COLOR = {
    "strong":  _GREEN,
    "usable":  _CYAN,
    "limited": _YELLOW,
    "weak":    _RED,
}


def _score_str(score: int, label: str) -> str:
    col = _SCORE_COLOR.get(label, _DIM)
    return f"{col}{score:3d} — {label}{_R}"


def print_coverage_report(
    report: dict,
    jurisdiction: str | None = None,
    category: str | None = None,
) -> None:
    """Print the coverage report to stdout with ANSI colours."""

    print()
    print(_SEP2)
    print(f"  {_BOLD}StatuteProof — Coverage Report{_R}")
    print(_SEP2)

    audit_src = report.get("audit_source", "metadata_only")
    if audit_src == "metadata_only":
        print(
            f"  {_YELLOW}⚠  No source audit JSON found.{_R}\n"
            f"  Quality fields are unknown. Run:\n"
            f"    python run.py source-audit --json\n"
            f"  to refresh coverage data with live extraction quality.\n"
        )
    else:
        audit_date = report.get("audit_date", "?")
        print(f"  {_DIM}Audit source: {audit_src}  ({audit_date}){_R}")
    print(f"  {_DIM}Generated   : {report.get('generated_at', '?')}{_R}")
    print()

    # ── Global summary ────────────────────────────────────────────────────────
    print(f"  {_BOLD}Summary{_R}")
    print(f"  {'Total sources:':<26} {report['total_sources']}")
    print(f"  {'Enabled (monitored):':<26} {_GREEN}{report['enabled_sources']}{_R}")
    print(f"  {'Disabled / mapped:':<26} {report['disabled_sources']}")
    if report.get("restricted_sources", 0):
        print(f"  {'Externally restricted:':<26} {_DIM}{report['restricted_sources']}{_R}  (geo-block / JS SPA / protocol)")
    print(f"  {'Good (≥ 1 000 chars):':<26} {_GREEN}{report['good_sources']}{_R}")
    print(f"  {'Low content:':<26} {_YELLOW}{report['low_content_sources']}{_R}")
    print(f"  {'Failed:':<26} {_RED}{report['failed_sources']}{_R}")
    if report.get("unknown_quality", 0):
        print(f"  {'Quality unknown:':<26} {_DIM}{report['unknown_quality']}{_R}")
    print(f"  {'Needs adapter:':<26} {report['needs_adapter']}")
    print(f"  {'Adapter-resolved:':<26} {report.get('adapter_resolved', 0)}")

    overall = report["coverage_score"]
    label   = report["score_label"]
    col     = _SCORE_COLOR.get(label, _DIM)
    print()
    print(f"  {_BOLD}Overall Coverage Score:{_R}  {col}{_BOLD}{overall}{_R}  {col}{label}{_R}")
    print(f"  {_DIM}{report.get('scoring_note', '')}{_R}")
    print()

    # ── By jurisdiction ───────────────────────────────────────────────────────
    by_j = report.get("by_jurisdiction", {})
    filter_j = jurisdiction.upper() if jurisdiction else None

    if filter_j and filter_j not in by_j:
        print(f"  {_RED}No jurisdiction {filter_j!r} found.{_R}")
    else:
        items_j = (
            {filter_j: by_j[filter_j]}.items()
            if filter_j
            else by_j.items()
        )
        print(f"  {_BOLD}By Jurisdiction{_R}")
        print(f"  {_DIM}{'Code':<5} {'Score':>8}  {'Label':<8}  {'Total':>5}  {'Enb':>4}  {'Good':>4}  {'Low':>4}  {'Fail':>4}  {'Adp':>4}  {'Rst':>4}{_R}")
        print("  " + "·" * 68)
        for jur, m in items_j:
            mon_note = ""
            if m["enabled"] == 0 and m.get("restricted", 0) == 0:
                mon_note = f"  {_DIM}(not monitored){_R}"
            sc_str = _score_str(m["score"], m["score_label"])
            rst = m.get("restricted", 0)
            rst_str = f"{_DIM}{rst:>4}{_R}" if rst else f"{_DIM}   0{_R}"
            print(
                f"  {_BOLD}{jur:<5}{_R} "
                f"{sc_str:<30}  "
                f"{m['total']:>5}  {m['enabled']:>4}  {_GREEN}{m['good']:>4}{_R}  "
                f"{_YELLOW}{m['low_content']:>4}{_R}  {_RED}{m['failed']:>4}{_R}  "
                f"{m['needs_adapter']:>4}  {rst_str}"
                f"{mon_note}"
            )
        print()

    # ── By category ───────────────────────────────────────────────────────────
    by_c = report.get("by_category", {})
    filter_c = category.lower() if category else None

    if filter_c and filter_c not in by_c:
        print(f"  {_RED}No category {filter_c!r} found.{_R}")
    else:
        items_c = (
            {filter_c: by_c[filter_c]}.items()
            if filter_c
            else by_c.items()
        )
        print(f"  {_BOLD}By Category{_R}")
        print(f"  {_DIM}{'Category':<35} {'Score':>8}  {'Label':<8}  {'Total':>5}  {'Good':>4}  {'Fail':>4}{_R}")
        print("  " + "·" * 62)
        for cat, m in items_c:
            label_str = m.get("label", cat)[:33]
            sc_str    = _score_str(m["score"], m["score_label"])
            print(
                f"  {label_str:<35} "
                f"{sc_str:<30}  "
                f"{m['total']:>5}  {_GREEN}{m['good']:>4}{_R}  {_RED}{m['failed']:>4}{_R}"
            )
        print()

    # ── Insights ──────────────────────────────────────────────────────────────
    strengths = report.get("top_strengths", [])
    if strengths:
        print(f"  {_BOLD}{_GREEN}Top Strengths{_R}")
        for s in strengths:
            print(f"  {_GREEN}✓{_R} {s}")
        print()

    gaps = report.get("top_gaps", [])
    if gaps:
        print(f"  {_BOLD}{_YELLOW}Top Gaps{_R}")
        for g in gaps:
            print(f"  {_YELLOW}⚠{_R} {g}")
        print()

    recs = report.get("recommendations", [])
    if recs:
        print(f"  {_BOLD}Recommendations{_R}")
        for r in recs:
            print(f"  • {r}")
        print()

    print(_SEP2)
    print()


# ── JSON export ───────────────────────────────────────────────────────────────

def export_coverage_json(report: dict, reports_dir: Path | None = None) -> Path:
    """
    Write reports/coverage_YYYY-MM-DD.json.

    Returns the written path.  Never raises.
    """
    out_dir = reports_dir or _REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"coverage_{date.today().isoformat()}.json"

    # Strip internal _source keys if somehow present (shouldn't be)
    clean = {k: v for k, v in report.items() if k != "_source"}

    path.write_text(
        json.dumps(clean, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


# ── HTML builder ──────────────────────────────────────────────────────────────

_BADGE_COLOR: dict[str, str] = {
    "strong":  "#22c55e",
    "usable":  "#0ea5e9",
    "limited": "#f97316",
    "weak":    "#ef4444",
}


def _badge(label: str) -> str:
    color = _BADGE_COLOR.get(label, "#6b7280")
    return (
        f'<span style="background:{color};color:#fff;'
        f'padding:2px 8px;border-radius:4px;font-size:0.8em;'
        f'font-weight:600;letter-spacing:0.05em">{label.upper()}</span>'
    )


def _score_cell(score: int, label: str) -> str:
    color = _BADGE_COLOR.get(label, "#6b7280")
    return (
        f'<span style="font-weight:700;color:{color}">{score}</span> '
        f'{_badge(label)}'
    )


def build_coverage_html(report: dict) -> str:
    """Return a self-contained HTML coverage report string."""

    today     = report.get("generated_at", date.today().isoformat())
    audit_src = report.get("audit_source", "metadata_only")
    audit_lbl = (
        f"Source audit: {audit_src} ({report.get('audit_date', '?')})"
        if audit_src != "metadata_only"
        else "⚠ No source audit found — quality fields unknown"
    )
    overall   = report["coverage_score"]
    ovr_label = report["score_label"]
    ovr_color = _BADGE_COLOR.get(ovr_label, "#6b7280")

    def _row(*cells: str) -> str:
        tds = "".join(f"<td>{c}</td>" for c in cells)
        return f"<tr>{tds}</tr>"

    # ── jurisdiction table ────────────────────────────────────────────────────
    j_rows = ""
    for jur, m in report.get("by_jurisdiction", {}).items():
        mon = f"<span style='color:#6b7280;font-size:0.8em'>none</span>" if m["enabled"] == 0 else str(m["enabled"])
        rst = m.get("restricted", 0)
        rst_cell = (
            f"<span style='color:#6b7280;font-size:0.85em' title='externally restricted'>{rst}</span>"
            if rst else "—"
        )
        j_rows += _row(
            f"<strong>{jur}</strong> — {m.get('name', jur)}",
            m.get("region", ""),
            _score_cell(m["score"], m["score_label"]),
            str(m["total"]),
            mon,
            f"<span style='color:#22c55e'>{m['good']}</span>",
            f"<span style='color:#f97316'>{m['low_content']}</span>",
            f"<span style='color:#ef4444'>{m['failed']}</span>",
            str(m["needs_adapter"]),
            rst_cell,
        )

    # ── category table ────────────────────────────────────────────────────────
    c_rows = ""
    for cat, m in report.get("by_category", {}).items():
        c_rows += _row(
            m.get("label", cat),
            _score_cell(m["score"], m["score_label"]),
            str(m["total"]),
            str(m["enabled"]),
            f"<span style='color:#22c55e'>{m['good']}</span>",
            f"<span style='color:#f97316'>{m['low_content']}</span>",
            f"<span style='color:#ef4444'>{m['failed']}</span>",
            str(m["needs_adapter"]),
        )

    def _li_list(items: list[str], color: str = "#e8edf2") -> str:
        if not items:
            return "<li style='color:#6b7280'>None identified.</li>"
        return "".join(
            f"<li style='color:{color};margin-bottom:6px'>{item}</li>"
            for item in items
        )

    strengths_html = _li_list(report.get("top_strengths", []), "#4ade80")
    gaps_html      = _li_list(report.get("top_gaps", []), "#fbbf24")
    recs_html      = _li_list(report.get("recommendations", []), "#93c5fd")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>StatuteProof — Coverage Report — {today}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1b2a;color:#e8edf2;font-family:'Segoe UI',system-ui,sans-serif;
      line-height:1.6;padding:32px 24px;max-width:1100px;margin:0 auto}}
h1{{font-size:1.8rem;color:#00c8ff;margin-bottom:4px}}
h2{{font-size:1.1rem;color:#00c8ff;margin:32px 0 12px;border-bottom:1px solid #1e3a52;
    padding-bottom:6px}}
.meta{{color:#6b7280;font-size:0.85em;margin-bottom:32px}}
.card{{background:#1a2b3c;border-radius:10px;padding:24px;margin-bottom:24px}}
.score-big{{font-size:3.5rem;font-weight:800;color:{ovr_color};line-height:1}}
.score-label{{font-size:1rem;color:{ovr_color};margin-top:4px;font-weight:600;
              letter-spacing:0.1em;text-transform:uppercase}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;
       margin-bottom:16px}}
.stat{{background:#162435;border-radius:8px;padding:16px;text-align:center}}
.stat-n{{font-size:1.8rem;font-weight:700;color:#e8edf2}}
.stat-l{{font-size:0.78rem;color:#6b7280;margin-top:4px;text-transform:uppercase;
         letter-spacing:0.05em}}
.good{{color:#22c55e}}.low{{color:#f97316}}.fail{{color:#ef4444}}
.dim{{color:#6b7280}}
table{{width:100%;border-collapse:collapse;font-size:0.88em}}
th{{background:#1a2b3c;color:#00c8ff;text-align:left;padding:8px 12px;
    border-bottom:2px solid #00c8ff}}
td{{padding:8px 12px;border-bottom:1px solid #1e3a52;vertical-align:middle}}
tr:hover td{{background:#162435}}
ul{{list-style:none;padding:0}}
li{{padding:6px 0;border-bottom:1px solid #1e3a52}}
li:last-child{{border-bottom:none}}
.disclaimer{{background:#1a2b3c;border-left:4px solid #6b7280;padding:16px 20px;
             border-radius:4px;color:#6b7280;font-size:0.85em;margin-top:32px}}
</style>
</head>
<body>
<h1>StatuteProof — Coverage Report</h1>
<p class="meta">Generated: {today} &nbsp;·&nbsp; {audit_lbl}</p>

<h2>1. Executive Overview</h2>
<div class="grid">
  <div class="stat"><div class="stat-n">{report['total_sources']}</div>
    <div class="stat-l">Total Sources</div></div>
  <div class="stat"><div class="stat-n good">{report['enabled_sources']}</div>
    <div class="stat-l">Active Monitoring</div></div>
  <div class="stat"><div class="stat-n dim">{report['disabled_sources']}</div>
    <div class="stat-l">Disabled / Mapped</div></div>
  <div class="stat"><div class="stat-n good">{report['good_sources']}</div>
    <div class="stat-l">Good Quality</div></div>
  <div class="stat"><div class="stat-n low">{report['low_content_sources']}</div>
    <div class="stat-l">Low Content</div></div>
  <div class="stat"><div class="stat-n fail">{report['failed_sources']}</div>
    <div class="stat-l">Failed</div></div>
  <div class="stat"><div class="stat-n">{report['needs_adapter']}</div>
    <div class="stat-l">Needs Adapter</div></div>
  <div class="stat"><div class="stat-n good">{report.get('adapter_resolved', 0)}</div>
    <div class="stat-l">Adapters Built</div></div>
</div>

<h2>2. Coverage Score</h2>
<div class="card">
  <div class="score-big">{overall}</div>
  <div class="score-label">{ovr_label}</div>
  <p style="color:#9ca3af;font-size:0.85em;margin-top:16px">
    {report.get('scoring_note', '')}
  </p>
  <p style="color:#9ca3af;font-size:0.85em;margin-top:8px">
    <strong style="color:#e8edf2">Score scale:</strong>
    <span style="color:#22c55e">85–100 strong</span> ·
    <span style="color:#0ea5e9">65–84 usable</span> ·
    <span style="color:#f97316">40–64 limited</span> ·
    <span style="color:#ef4444">0–39 weak</span>
  </p>
</div>

<h2>3. Coverage by Jurisdiction</h2>
<table>
<tr>
  <th>Jurisdiction</th><th>Region</th><th>Score</th>
  <th>Total</th><th>Active</th>
  <th class="good">Good</th><th class="low">Low</th><th class="fail">Failed</th>
  <th>Needs Adapter</th><th title="Geo-blocked / JS SPA / protocol error">Restricted</th>
</tr>
{j_rows}
</table>

<h2>4. Coverage by Category</h2>
<table>
<tr>
  <th>Category</th><th>Score</th>
  <th>Total</th><th>Active</th>
  <th class="good">Good</th><th class="low">Low</th><th class="fail">Failed</th>
  <th>Needs Adapter</th>
</tr>
{c_rows}
</table>

<h2>5. Strengths</h2>
<ul>{strengths_html}</ul>

<h2>6. Gaps</h2>
<ul>{gaps_html}</ul>

<h2>7. Recommendations</h2>
<ul>{recs_html}</ul>

<div class="disclaimer">
  <strong>Disclaimer:</strong>
  This coverage report reflects technical monitoring readiness, not legal completeness.
  Coverage scores are based on automated extraction quality metrics.
  Regulatory obligation mapping requires separate legal analysis.
  Run <code>python run.py source-audit --json</code> to refresh with live data.
</div>
</body>
</html>"""

    return html


def export_coverage_html(report: dict, reports_dir: Path | None = None) -> Path:
    """
    Write reports/coverage_YYYY-MM-DD.html.

    Returns the written path.  Never raises.
    """
    out_dir = reports_dir or _REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"coverage_{date.today().isoformat()}.html"
    path.write_text(build_coverage_html(report), encoding="utf-8")
    return path
