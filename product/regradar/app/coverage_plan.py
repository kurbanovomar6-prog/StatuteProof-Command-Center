"""
RegRadar — Coverage Improvement Plan.

Reads the latest coverage JSON and source-audit JSON from reports/,
then produces a prioritised action plan for improving coverage.

No AI.  No Telegram.  No DB writes.  No network calls.
No sources.json modification.  One bad file never crashes the command.

Public API
----------
generate_coverage_plan()         → dict
print_coverage_plan(plan)        → None
export_coverage_plan_json(plan)  → Path
build_coverage_plan_html(plan)   → str
export_coverage_plan_html(plan)  → Path
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

_REPORTS_DIR = Path(__file__).parent.parent / "reports"

# ── Metadata ──────────────────────────────────────────────────────────────────

_JURISDICTION_NAME: dict[str, str] = {
    "RU":  "Russia",
    "KZ":  "Kazakhstan",
    "AZ":  "Azerbaijan",
    "BY":  "Belarus",
    "UZ":  "Uzbekistan",
    "GE":  "Georgia",
    "AM":  "Armenia",
    "INT": "International",
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
}

# Categories considered high-importance for regulatory monitoring
_IMPORTANT_CATS: frozenset[str] = frozenset({
    "central_bank",
    "aml",
    "financial_regulator",
    "finance_ministry",
    "ministry_finance",
    "tax",
    "legal_acts",
    "international",
    "international_standard_setter",
})

# ── File loaders ──────────────────────────────────────────────────────────────

def _latest_json(
    pattern: str,
    exclude: str | None = None,
) -> tuple[dict | None, Path | None]:
    """Return (data, path) for the most-recent file matching glob pattern."""
    candidates = sorted(
        (
            p for p in _REPORTS_DIR.glob(pattern)
            if exclude is None or exclude not in p.name
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None, None
    path = candidates[0]
    try:
        return json.loads(path.read_text(encoding="utf-8")), path
    except Exception as exc:
        logger.warning("coverage_plan: could not load %s: %s", path, exc)
        return None, None


# ── Error classifier ──────────────────────────────────────────────────────────

def _error_type(error: str | None) -> str:
    if not error:
        return "unknown"
    e = error.lower()
    if any(k in e for k in ("name_not_resolved", "nameresolution", "gaierror", "err_name")):
        return "dns"
    if any(k in e for k in ("cert_authority_invalid", "cert_common_name", "ssl", "certificate")):
        return "ssl"
    if "timeout" in e:
        return "timeout"
    if any(k in e for k in ("unable to retrieve", "page is navigating", "changing the cont")):
        return "navigation_timeout"
    if any(k in e for k in ("404", "not found")):
        return "not_found"
    return "other"


_ERROR_LABEL: dict[str, str] = {
    "dns":               "DNS — domain not resolved",
    "ssl":               "SSL — certificate error",
    "timeout":           "Timeout — site too slow or unreachable",
    "navigation_timeout":"Navigation timeout — JS-heavy or bot-protected",
    "not_found":         "HTTP 404 — URL not found",
    "other":             "Unknown error",
    "unknown":           "Unknown error",
}

_ERROR_FIX: dict[str, str] = {
    "dns":               "Find the correct official domain; the current URL is wrong or the domain has changed.",
    "ssl":               "Try the http:// variant or find the alternate official domain with a valid cert.",
    "timeout":           "Test manually; consider adding a retry adapter or a different entry URL.",
    "navigation_timeout":"Site is JS-heavy or bot-protected; test in browser and consider Playwright adapter.",
    "not_found":         "Check for updated URL path on the official website.",
    "other":             "Investigate manually; test URL in browser before rebuilding adapter.",
    "unknown":           "Investigate error; test URL manually.",
}


# ── Scoring helpers (mirrors app/coverage.py without importing it) ────────────

_LABEL_PRIORITY: dict[str, int] = {"weak": 0, "limited": 1, "usable": 2, "strong": 3}

def _score_label(s: int) -> str:
    if s >= 85: return "strong"
    if s >= 65: return "usable"
    if s >= 40: return "limited"
    return "weak"


# ── Plan builders ─────────────────────────────────────────────────────────────

def _build_priority_jurisdictions(cov_j: dict) -> list[dict]:
    """Return jurisdictions sorted from weakest to strongest, with recommended actions."""
    items = []
    for jur, m in cov_j.items():
        label  = m.get("score_label", _score_label(m.get("score", 0)))
        score  = m.get("score", 0)
        prio   = _LABEL_PRIORITY.get(label, 2)
        name   = _JURISDICTION_NAME.get(jur, jur)

        if label in ("weak", "limited"):
            urgency = "HIGH"
        elif m.get("enabled", 0) == 0 and m.get("total", 0) > 0:
            urgency = "MEDIUM"
        elif label == "usable":
            urgency = "LOW"
        else:
            urgency = "NONE"

        # Build concise action list
        actions: list[str] = []
        if m.get("failed", 0) > 0:
            actions.append(
                f"Fix {m['failed']} failed source(s) (DNS/SSL/URL errors)."
            )
        if m.get("enabled", 0) == 0 and m.get("good", 0) > 0:
            actions.append(
                f"Consider enabling {m['good']} good-quality disabled source(s)."
            )
        if m.get("needs_adapter", 0) > 0 and m.get("failed", 0) > 0:
            actions.append(
                f"Build adapter for {m['needs_adapter'] - m.get('failed',0)} low-content source(s)."
            )
        if not actions:
            actions.append("Maintain current quality; expand source count if client requests.")

        items.append({
            "jurisdiction": jur,
            "name":         name,
            "score":        score,
            "score_label":  label,
            "urgency":      urgency,
            "enabled":      m.get("enabled", 0),
            "total":        m.get("total", 0),
            "good":         m.get("good", 0),
            "failed":       m.get("failed", 0),
            "actions":      actions,
        })

    items.sort(key=lambda x: (_LABEL_PRIORITY.get(x["score_label"], 2), x["score"]))
    return items


def _build_priority_categories(cov_c: dict) -> list[dict]:
    """Return important categories sorted by score, lowest first."""
    items = []
    for cat, m in cov_c.items():
        if cat not in _IMPORTANT_CATS:
            continue
        label = m.get("score_label", _score_label(m.get("score", 0)))
        if label in ("strong",) and m.get("enabled", 0) >= 1:
            continue  # skip well-covered categories
        score = m.get("score", 0)
        items.append({
            "category":      cat,
            "label":         m.get("label", _CATEGORY_LABEL.get(cat, cat)),
            "score":         score,
            "score_label":   label,
            "total":         m.get("total", 0),
            "enabled":       m.get("enabled", 0),
            "good":          m.get("good", 0),
            "failed":        m.get("failed", 0),
            "needs_adapter": m.get("needs_adapter", 0),
        })

    items.sort(key=lambda x: x["score"])
    return items


def _build_quick_wins(sources: list[dict]) -> list[dict]:
    """
    Disabled sources with good extraction quality in important categories.

    These can be enabled without building a new adapter — highest ROI.
    Sorted: important category first, then by chars descending.
    """
    items = []
    for s in sources:
        if s.get("enabled"):
            continue
        if s.get("extraction_quality") != "good":
            continue
        cat = s.get("category", "")
        if cat not in _IMPORTANT_CATS:
            continue
        items.append({
            "name":         s.get("name", ""),
            "url":          s.get("url", ""),
            "jurisdiction": s.get("jurisdiction", ""),
            "category":     cat,
            "category_label": _CATEGORY_LABEL.get(cat, cat),
            "chars":        s.get("extracted_chars", 0),
            "extractor":    s.get("best_extractor", ""),
            "reason": (
                f"Good extraction ({s.get('extracted_chars',0):,} chars via "
                f"{s.get('best_extractor','?')}) — ready to enable without adapter."
            ),
        })

    # Sort: important cats first, then chars descending
    cat_rank = {
        "central_bank": 0, "aml": 1, "financial_regulator": 2,
        "finance_ministry": 3, "ministry_finance": 3,
        "tax": 4, "legal_acts": 5,
        "international": 6, "international_standard_setter": 7,
    }
    items.sort(key=lambda x: (cat_rank.get(x["category"], 9), -x["chars"]))
    return items[:15]


def _build_adapter_tasks(sources: list[dict]) -> list[dict]:
    """
    Sources with low_content or failed extraction that need a custom adapter.
    Prioritises: enabled > important category > higher chars (closer to threshold).
    """
    items = []
    for s in sources:
        if not s.get("requires_adapter", False):
            continue
        q = s.get("extraction_quality", "failed")
        if q == "good":
            continue  # already resolved
        cat = s.get("category", "")
        enabled = bool(s.get("enabled", False))

        if q == "failed":
            # Only include failed sources where the URL appears valid (not pure DNS)
            err_t = _error_type(s.get("error"))
            if err_t in ("dns", "not_found"):
                continue  # URL fix first, adapter second
        else:
            err_t = "low_content"

        if not enabled and cat not in _IMPORTANT_CATS:
            continue  # skip unimportant disabled low-quality sources

        prio = "HIGH" if enabled else ("MEDIUM" if cat in _IMPORTANT_CATS else "LOW")

        items.append({
            "name":           s.get("name", ""),
            "url":            s.get("url", ""),
            "jurisdiction":   s.get("jurisdiction", ""),
            "category":       cat,
            "category_label": _CATEGORY_LABEL.get(cat, cat),
            "quality":        q,
            "chars":          s.get("extracted_chars", 0),
            "error_type":     err_t,
            "enabled":        enabled,
            "priority":       prio,
            "next_step":      s.get("suggested_next_step", ""),
        })

    rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    items.sort(key=lambda x: (rank.get(x["priority"], 9), -x["chars"]))
    return items


def _build_source_fix_tasks(sources: list[dict]) -> list[dict]:
    """
    Failed sources grouped by error type with a concrete fix suggestion.
    Excludes sources whose fix is 'needs adapter' (those go to adapter_tasks).
    """
    items = []
    for s in sources:
        if s.get("extraction_quality") != "failed":
            continue
        err_t = _error_type(s.get("error"))
        items.append({
            "name":           s.get("name", ""),
            "url":            s.get("url", ""),
            "jurisdiction":   s.get("jurisdiction", ""),
            "category":       s.get("category", ""),
            "category_label": _CATEGORY_LABEL.get(s.get("category", ""), s.get("category", "")),
            "error_type":     err_t,
            "error_label":    _ERROR_LABEL.get(err_t, err_t),
            "suggested_fix":  _ERROR_FIX.get(err_t, "Investigate manually."),
            "enabled":        bool(s.get("enabled", False)),
        })

    # Enabled first, then by error type (dns first — easiest to fix)
    err_rank = {"dns": 0, "ssl": 1, "not_found": 2, "navigation_timeout": 3, "timeout": 4, "other": 5}
    items.sort(key=lambda x: (0 if x["enabled"] else 1, err_rank.get(x["error_type"], 9)))
    return items


def _build_enable_candidates(sources: list[dict], cov_j: dict) -> list[dict]:
    """
    Good disabled sources in jurisdictions that would most benefit from activation.
    Groups them by jurisdiction and includes a note on coverage impact.
    """
    # Weak/limited jurisdictions benefit most
    priority_j = {
        j for j, m in cov_j.items()
        if m.get("score_label") in ("weak", "limited")
        or (m.get("enabled", 0) == 0 and m.get("good", 0) > 0)
    }

    items = []
    for s in sources:
        if s.get("enabled"):
            continue
        if s.get("extraction_quality") != "good":
            continue
        jur = s.get("jurisdiction", "")
        benefit = "high" if jur in priority_j else "medium"
        items.append({
            "name":           s.get("name", ""),
            "url":            s.get("url", ""),
            "jurisdiction":   jur,
            "jurisdiction_name": _JURISDICTION_NAME.get(jur, jur),
            "category":       s.get("category", ""),
            "category_label": _CATEGORY_LABEL.get(s.get("category",""), s.get("category","")),
            "chars":          s.get("extracted_chars", 0),
            "coverage_benefit": benefit,
        })

    items.sort(key=lambda x: (0 if x["coverage_benefit"] == "high" else 1, -x["chars"]))
    return items


def _build_expansion_suggestions(
    cov_j: dict,
    cov_c: dict,
    sources: list[dict],
) -> list[str]:
    """
    Suggest new source types to add for weak/limited jurisdictions
    where important categories are missing or failed.
    """
    # Map existing (jurisdiction, category) pairs
    existing: set[tuple[str, str]] = set()
    for s in sources:
        existing.add((s.get("jurisdiction", ""), s.get("category", "")))

    suggestions: list[str] = []

    for jur, m in sorted(cov_j.items(), key=lambda x: x[1].get("score", 100)):
        if m.get("score_label") not in ("weak", "limited"):
            continue
        name = _JURISDICTION_NAME.get(jur, jur)

        for cat in ("central_bank", "aml", "financial_regulator", "tax", "legal_acts"):
            key = (jur, cat)
            label = _CATEGORY_LABEL.get(cat, cat)

            if key not in existing:
                suggestions.append(
                    f"{name}: add missing {label} source — "
                    f"search for official {jur} {label.lower()} website."
                )
            else:
                # Check if all existing ones are failed
                cat_srcs = [s for s in sources if s.get("jurisdiction") == jur and s.get("category") == cat]
                all_failed = all(s.get("extraction_quality") == "failed" for s in cat_srcs)
                if all_failed:
                    suggestions.append(
                        f"{name}: {label} source URL invalid — "
                        f"find the current official domain and update."
                    )

    # Dedup and cap
    seen: set[str] = set()
    out: list[str] = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            out.append(s)

    return out[:12]


def _build_roadmap(
    current_score: int,
    quick_wins: list[dict],
    fix_tasks: list[dict],
    enable_candidates: list[dict],
    adapter_tasks: list[dict],
    cov_j: dict,
) -> dict[str, list[str]]:
    """Generate a 7 / 30 / 90-day roadmap based on the plan data."""

    dns_fixes   = [t for t in fix_tasks if t["error_type"] == "dns"]
    ssl_fixes   = [t for t in fix_tasks if t["error_type"] == "ssl"]
    nav_fixes   = [t for t in fix_tasks if t["error_type"] == "navigation_timeout"]
    high_value  = [c for c in enable_candidates if c["coverage_benefit"] == "high"]
    weak_j      = [j for j, m in cov_j.items() if m.get("score_label") == "weak"]
    limited_j   = [j for j, m in cov_j.items() if m.get("score_label") == "limited"]

    next_7: list[str] = []
    next_30: list[str] = []
    next_90: list[str] = []

    # ── 7 days ────────────────────────────────────────────────────────────────
    if dns_fixes:
        names = ", ".join(t["name"][:30] for t in dns_fixes[:3])
        next_7.append(
            f"Fix {len(dns_fixes)} DNS failure(s) by verifying official domains: {names}."
        )
    if ssl_fixes:
        next_7.append(
            f"Fix {len(ssl_fixes)} SSL certificate error(s): try http:// variant or alternate domains."
        )
    if nav_fixes:
        next_7.append(
            f"Investigate {len(nav_fixes)} navigation-timeout source(s) manually in a browser."
        )
    if high_value:
        jurs = sorted(set(c["jurisdiction_name"] for c in high_value[:4]))
        next_7.append(
            f"Enable {len(high_value)} good-quality disabled source(s) for: {', '.join(jurs)}."
        )
    next_7.append("Run 'python run.py source-audit --json' to refresh coverage data.")
    next_7.append("Run 'python run.py coverage' to measure improvement.")

    # ── 30 days ───────────────────────────────────────────────────────────────
    if weak_j:
        names = ", ".join(_JURISDICTION_NAME.get(j, j) for j in weak_j)
        next_30.append(
            f"Add 5–10 quality-checked sources for weak jurisdiction(s): {names}."
        )
    if limited_j:
        names = ", ".join(_JURISDICTION_NAME.get(j, j) for j in limited_j)
        next_30.append(
            f"Expand source count for limited jurisdiction(s): {names}."
        )
    next_30.append(
        "Enable Georgia country pack (4 good sources: central bank, tax, legal acts, finance ministry)."
    )
    next_30.append(
        "Enable Belarus country pack (3 good sources: central bank, finance ministry, legal portal)."
    )
    if adapter_tasks:
        next_30.append(
            f"Build adapters for {min(len(adapter_tasks), 3)} low-content important source(s) "
            f"(e.g. {adapter_tasks[0]['name'][:40]})."
        )
    next_30.append(
        "Validate AML sources for AZ, KZ, AM — find correct official FIU/AML authority URLs."
    )
    next_30.append("Run 'python run.py coverage --html' to refresh client-facing report.")

    # ── 90 days ───────────────────────────────────────────────────────────────
    target = min(current_score + 20, 88)
    next_90.append(
        f"Target coverage score: {target} ({_score_label(target)}) across all jurisdictions."
    )
    next_90.append(
        "Build country packs for AZ, KZ, UZ, AM: 5–8 sources per jurisdiction "
        "(central bank, AML, tax, legal acts, finance ministry)."
    )
    next_90.append(
        "Expand International Standard Setter coverage: "
        "fix IOSCO, EBA, ESMA sources (currently < 150 chars — adapters needed)."
    )
    next_90.append(
        "Add 30–50 new quality-checked sources overall to reach 80–100 total sources."
    )
    next_90.append(
        "Build client-specific source profiles for each active client jurisdiction."
    )
    next_90.append(
        "Expand PDF/document extraction to legal database sources for richer signal."
    )

    return {
        "next_7_days":  next_7,
        "next_30_days": next_30,
        "next_90_days": next_90,
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_coverage_plan() -> dict:
    """
    Build a coverage improvement plan from the latest report files.

    Returns a dict with the full plan, or raises ValueError with a clear
    user-facing message when required inputs are missing.

    No network calls.  No DB writes.  No file modifications.
    """
    if not _REPORTS_DIR.exists():
        raise ValueError(
            "reports/ directory not found.\n"
            "Run: python run.py source-audit --json\n"
            "     python run.py coverage --json"
        )

    # ── Load coverage JSON (exclude coverage_plan_*.json) ────────────────────
    cov_data, cov_path = _latest_json("coverage_*.json", exclude="plan")
    if cov_data is None:
        raise ValueError(
            "No coverage JSON found in reports/.\n"
            "Run: python run.py coverage --json"
        )

    # ── Load audit JSON ───────────────────────────────────────────────────────
    aud_data, aud_path = _latest_json("source_audit_*.json")
    if aud_data is None:
        raise ValueError(
            "No source-audit JSON found in reports/.\n"
            "Run: python run.py source-audit --json"
        )

    sources       = aud_data.get("sources", [])
    cov_j         = cov_data.get("by_jurisdiction", {})
    cov_c         = cov_data.get("by_category", {})
    current_score = cov_data.get("coverage_score", 0)
    current_label = cov_data.get("score_label", "unknown")
    target_score  = min(current_score + 15, 85)

    # ── Build plan components ─────────────────────────────────────────────────
    priority_j   = _build_priority_jurisdictions(cov_j)
    priority_c   = _build_priority_categories(cov_c)
    quick_wins   = _build_quick_wins(sources)
    adapter_t    = _build_adapter_tasks(sources)
    fix_tasks    = _build_source_fix_tasks(sources)
    enable_cands = _build_enable_candidates(sources, cov_j)
    expansions   = _build_expansion_suggestions(cov_j, cov_c, sources)
    roadmap      = _build_roadmap(
        current_score, quick_wins, fix_tasks, enable_cands, adapter_t, cov_j
    )

    return {
        "generated_at":               date.today().isoformat(),
        "coverage_json":              cov_path.name if cov_path else "?",
        "audit_json":                 aud_path.name if aud_path else "?",
        "overall_score":              current_score,
        "overall_label":              current_label,
        "target_score":               target_score,
        "target_label":               _score_label(target_score),
        "total_sources":              cov_data.get("total_sources", 0),
        "enabled_sources":            cov_data.get("enabled_sources", 0),
        "good_sources":               cov_data.get("good_sources", 0),
        "failed_sources":             cov_data.get("failed_sources", 0),
        "priority_jurisdictions":     priority_j,
        "priority_categories":        priority_c,
        "quick_wins":                 quick_wins,
        "adapter_tasks":              adapter_t,
        "source_fix_tasks":           fix_tasks,
        "source_enable_candidates":   enable_cands,
        "source_expansion_suggestions": expansions,
        "roadmap":                    roadmap,
        "disclaimer": (
            "This plan is based on technical monitoring readiness and source "
            "quality, not a guarantee of legal completeness."
        ),
    }


# ── Terminal printer ──────────────────────────────────────────────────────────

_SEP2 = "═" * 68
_SEP  = "─" * 68
_R    = "\033[0m"
_BOLD = "\033[1m"
_DIM  = "\033[2m"
_G    = "\033[32m"
_Y    = "\033[33m"
_R_   = "\033[31m"
_C    = "\033[36m"
_B    = "\033[34m"

_SCORE_COL = {"strong": _G, "usable": _C, "limited": _Y, "weak": _R_}
_PRIO_COL  = {"HIGH": _R_, "MEDIUM": _Y, "LOW": _DIM, "NONE": _DIM}


def _score_badge(score: int, label: str) -> str:
    col = _SCORE_COL.get(label, _DIM)
    return f"{col}{score} — {label}{_R}"


def print_coverage_plan(plan: dict) -> None:
    print()
    print(_SEP2)
    print(f"  {_BOLD}StatuteProof — Coverage Improvement Plan{_R}")
    print(_SEP2)
    print(f"  {_DIM}Coverage JSON: {plan.get('coverage_json','?')}{_R}")
    print(f"  {_DIM}Audit JSON   : {plan.get('audit_json','?')}{_R}")
    print(f"  {_DIM}Generated    : {plan.get('generated_at','?')}{_R}")
    print()

    cur   = plan["overall_score"]
    cur_l = plan["overall_label"]
    tgt   = plan["target_score"]
    tgt_l = plan["target_label"]
    print(
        f"  {_BOLD}Current score:{_R} {_score_badge(cur, cur_l)}    "
        f"{_BOLD}Target score:{_R} {_score_badge(tgt, tgt_l)}"
    )
    print(
        f"  {_DIM}Sources: {plan['total_sources']} total · "
        f"{plan['enabled_sources']} enabled · "
        f"{plan['good_sources']} good · "
        f"{plan['failed_sources']} failed{_R}"
    )
    print()

    # ── Priority jurisdictions ─────────────────────────────────────────────
    pj = plan.get("priority_jurisdictions", [])
    actionable = [j for j in pj if j["urgency"] in ("HIGH", "MEDIUM")]
    if actionable:
        print(f"  {_BOLD}Priority Jurisdictions{_R}")
        for j in actionable:
            col = _PRIO_COL.get(j["urgency"], _DIM)
            sc  = _score_badge(j["score"], j["score_label"])
            print(
                f"  {col}[{j['urgency']:<6}]{_R}  "
                f"{_BOLD}{j['jurisdiction']}{_R} {j['name']:<14}  "
                f"{sc:<30}  "
                f"{j['total']} src / {j['enabled']} enabled / {j['failed']} failed"
            )
            for act in j["actions"]:
                print(f"             {_DIM}→ {act}{_R}")
        print()

    # ── Priority categories ────────────────────────────────────────────────
    pc = plan.get("priority_categories", [])
    if pc:
        print(f"  {_BOLD}Priority Categories{_R}")
        for c in pc[:6]:
            sc = _score_badge(c["score"], c["score_label"])
            print(
                f"  {c['label']:<38}  {sc:<30}  "
                f"{c['total']} src / {c['enabled']} enabled"
            )
        print()

    # ── Quick wins ─────────────────────────────────────────────────────────
    qw = plan.get("quick_wins", [])
    if qw:
        print(f"  {_BOLD}{_G}Quick Wins — Enable without adapter{_R}")
        for i, w in enumerate(qw[:8], 1):
            print(
                f"  {_G}{i}.{_R} {w['name'][:52]}\n"
                f"     {_DIM}{w['jurisdiction']} · {w['category_label']} · "
                f"{w['chars']:,} chars{_R}"
            )
        if len(qw) > 8:
            print(f"     {_DIM}… and {len(qw)-8} more{_R}")
        print()

    # ── Source fix tasks ───────────────────────────────────────────────────
    ft = plan.get("source_fix_tasks", [])
    if ft:
        print(f"  {_BOLD}{_Y}Source Fix Tasks — URL / Domain errors{_R}")
        for i, t in enumerate(ft, 1):
            col = _R_ if t["enabled"] else _Y
            en  = "enabled" if t["enabled"] else "disabled"
            print(
                f"  {col}{i}.{_R} {t['name'][:52]}\n"
                f"     {_DIM}{t['jurisdiction']} · {t['category_label']} · "
                f"{en} · {t['error_label']}\n"
                f"     Fix: {t['suggested_fix']}{_R}"
            )
        print()

    # ── Adapter tasks ──────────────────────────────────────────────────────
    at = plan.get("adapter_tasks", [])
    if at:
        print(f"  {_BOLD}Adapter Tasks — Low-content sources{_R}")
        for i, t in enumerate(at[:6], 1):
            col = _PRIO_COL.get(t["priority"], _DIM)
            print(
                f"  {col}[{t['priority']}]{_R} {i}. {t['name'][:50]}\n"
                f"     {_DIM}{t['jurisdiction']} · {t['category_label']} · "
                f"{t['quality']} · {t['chars']:,} chars\n"
                f"     {t['next_step'][:80]}{_R}"
            )
        if len(at) > 6:
            print(f"     {_DIM}… and {len(at)-6} more{_R}")
        print()

    # ── Expansion suggestions ──────────────────────────────────────────────
    exp = plan.get("source_expansion_suggestions", [])
    if exp:
        print(f"  {_BOLD}Source Expansion Suggestions{_R}")
        for i, s in enumerate(exp[:8], 1):
            print(f"  {i}. {s}")
        if len(exp) > 8:
            print(f"     {_DIM}… and {len(exp)-8} more{_R}")
        print()

    # ── Roadmap ────────────────────────────────────────────────────────────
    rm = plan.get("roadmap", {})
    print(f"  {_BOLD}Roadmap{_R}")
    for key, header in [
        ("next_7_days",  "Next 7 days"),
        ("next_30_days", "Next 30 days"),
        ("next_90_days", "Next 90 days"),
    ]:
        items = rm.get(key, [])
        if items:
            print(f"\n  {_BOLD}{_C}{header}{_R}")
            for item in items:
                print(f"  • {item}")

    print()
    print(f"  {_DIM}{plan.get('disclaimer', '')}{_R}")
    print()
    print(_SEP2)
    print()


# ── JSON export ───────────────────────────────────────────────────────────────

def export_coverage_plan_json(plan: dict, reports_dir: Path | None = None) -> Path:
    out_dir = reports_dir or _REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"coverage_plan_{date.today().isoformat()}.json"
    path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


# ── HTML builder ──────────────────────────────────────────────────────────────

_BADGE_CSS: dict[str, str] = {
    "strong":  "#22c55e",
    "usable":  "#0ea5e9",
    "limited": "#f97316",
    "weak":    "#ef4444",
    "HIGH":    "#ef4444",
    "MEDIUM":  "#f59e0b",
    "LOW":     "#6b7280",
}


def _html_badge(text: str, color: str = "#6b7280") -> str:
    return (
        f'<span style="background:{color};color:#fff;'
        f'padding:2px 8px;border-radius:4px;font-size:0.78em;'
        f'font-weight:700;letter-spacing:0.04em">{text.upper()}</span>'
    )


def _score_html(score: int, label: str) -> str:
    col = _BADGE_CSS.get(label, "#6b7280")
    return (
        f'<span style="font-weight:800;color:{col};font-size:1.1em">{score}</span> '
        f'{_html_badge(label, col)}'
    )


def build_coverage_plan_html(plan: dict) -> str:
    today     = plan.get("generated_at", date.today().isoformat())
    cur_score = plan["overall_score"]
    cur_label = plan["overall_label"]
    tgt_score = plan["target_score"]
    tgt_label = plan["target_label"]

    def _li(items: list[str], color: str = "#e8edf2") -> str:
        if not items:
            return "<li style='color:#6b7280'>None identified.</li>"
        return "".join(
            f"<li style='color:{color};padding:5px 0;border-bottom:1px solid #1e3a52'>"
            f"{item}</li>"
            for item in items
        )

    # ── Priority jurisdictions table ──────────────────────────────────────────
    j_rows = ""
    for j in plan.get("priority_jurisdictions", []):
        if j["urgency"] == "NONE":
            continue
        badge_col = _BADGE_CSS.get(j["urgency"], "#6b7280")
        sc_col    = _BADGE_CSS.get(j["score_label"], "#6b7280")
        actions   = "; ".join(j["actions"])
        j_rows += (
            f"<tr>"
            f"<td>{_html_badge(j['urgency'], badge_col)}</td>"
            f"<td><strong>{j['jurisdiction']}</strong> — {j['name']}</td>"
            f"<td><span style='color:{sc_col};font-weight:700'>{j['score']}</span> "
            f"{_html_badge(j['score_label'], sc_col)}</td>"
            f"<td>{j['total']}</td><td>{j['enabled']}</td><td>{j['failed']}</td>"
            f"<td style='font-size:0.85em;color:#9ca3af'>{actions}</td>"
            f"</tr>"
        )

    # ── Quick wins table ──────────────────────────────────────────────────────
    qw_rows = ""
    for w in plan.get("quick_wins", [])[:10]:
        qw_rows += (
            f"<tr>"
            f"<td>{w['name']}</td>"
            f"<td>{w['jurisdiction']}</td>"
            f"<td>{w['category_label']}</td>"
            f"<td style='color:#22c55e'>{w['chars']:,}</td>"
            f"<td style='font-size:0.85em;color:#9ca3af'>{w['extractor']}</td>"
            f"</tr>"
        )

    # ── Source fix table ──────────────────────────────────────────────────────
    fix_rows = ""
    for t in plan.get("source_fix_tasks", []):
        err_col = "#ef4444" if t["enabled"] else "#f59e0b"
        fix_rows += (
            f"<tr>"
            f"<td>{t['name']}</td>"
            f"<td>{t['jurisdiction']}</td>"
            f"<td style='color:{err_col}'>{t['error_label']}</td>"
            f"<td style='font-size:0.85em;color:#9ca3af'>{t['suggested_fix']}</td>"
            f"</tr>"
        )

    # ── Roadmap ───────────────────────────────────────────────────────────────
    def _roadmap_section(title: str, items: list[str], color: str) -> str:
        lis = "".join(
            f"<li style='padding:6px 0;border-bottom:1px solid #1e3a52'>{item}</li>"
            for item in items
        )
        return (
            f"<div style='margin-bottom:24px'>"
            f"<h3 style='color:{color};margin-bottom:10px'>{title}</h3>"
            f"<ul style='list-style:none;padding:0'>{lis}</ul>"
            f"</div>"
        )

    rm = plan.get("roadmap", {})
    roadmap_html = (
        _roadmap_section("Next 7 Days",  rm.get("next_7_days",  []), "#22c55e") +
        _roadmap_section("Next 30 Days", rm.get("next_30_days", []), "#0ea5e9") +
        _roadmap_section("Next 90 Days", rm.get("next_90_days", []), "#a78bfa")
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>StatuteProof — Coverage Improvement Plan — {today}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1b2a;color:#e8edf2;font-family:'Segoe UI',system-ui,sans-serif;
      line-height:1.6;padding:32px 24px;max-width:1100px;margin:0 auto}}
h1{{font-size:1.8rem;color:#00c8ff;margin-bottom:4px}}
h2{{font-size:1.05rem;color:#00c8ff;margin:32px 0 12px;border-bottom:1px solid #1e3a52;
    padding-bottom:6px;text-transform:uppercase;letter-spacing:0.08em}}
.meta{{color:#6b7280;font-size:0.85em;margin-bottom:28px}}
.score-row{{display:flex;gap:32px;flex-wrap:wrap;margin-bottom:28px;
            background:#1a2b3c;border-radius:10px;padding:24px}}
.score-box{{text-align:center}}
.score-n{{font-size:2.8rem;font-weight:800;line-height:1}}
.score-l{{font-size:0.8rem;color:#6b7280;text-transform:uppercase;
          letter-spacing:0.08em;margin-top:4px}}
.arrow{{font-size:2rem;color:#374151;display:flex;align-items:center}}
.stats{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px}}
.stat{{background:#1a2b3c;border-radius:8px;padding:14px 20px;text-align:center;min-width:110px}}
.stat-n{{font-size:1.6rem;font-weight:700}}
.stat-l{{font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:0.88em;margin-bottom:8px}}
th{{background:#1a2b3c;color:#00c8ff;text-align:left;padding:9px 12px;
    border-bottom:2px solid #00c8ff;font-size:0.82em;letter-spacing:0.04em}}
td{{padding:9px 12px;border-bottom:1px solid #1e3a52;vertical-align:top}}
tr:hover td{{background:#162435}}
ul{{list-style:none;padding:0}}
.card{{background:#1a2b3c;border-radius:10px;padding:24px;margin-bottom:24px}}
.disclaimer{{background:#1a2b3c;border-left:4px solid #6b7280;padding:16px 20px;
             border-radius:4px;color:#6b7280;font-size:0.85em;margin-top:32px}}
</style>
</head>
<body>

<h1>StatuteProof — Coverage Improvement Plan</h1>
<p class="meta">
  Generated: {today} &nbsp;·&nbsp;
  Coverage: {plan.get('coverage_json','?')} &nbsp;·&nbsp;
  Audit: {plan.get('audit_json','?')}
</p>

<h2>1. Current vs Target</h2>
<div class="score-row">
  <div class="score-box">
    <div class="score-n" style="color:{_BADGE_CSS.get(cur_label,'#fff')}">{cur_score}</div>
    <div class="score-l">Current Score — {cur_label}</div>
  </div>
  <div class="arrow">→</div>
  <div class="score-box">
    <div class="score-n" style="color:{_BADGE_CSS.get(tgt_label,'#fff')}">{tgt_score}</div>
    <div class="score-l">Target Score — {tgt_label}</div>
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-n">{plan['total_sources']}</div>
    <div class="stat-l">Total Sources</div></div>
  <div class="stat"><div class="stat-n" style="color:#22c55e">{plan['enabled_sources']}</div>
    <div class="stat-l">Active</div></div>
  <div class="stat"><div class="stat-n" style="color:#22c55e">{plan['good_sources']}</div>
    <div class="stat-l">Good Quality</div></div>
  <div class="stat"><div class="stat-n" style="color:#ef4444">{plan['failed_sources']}</div>
    <div class="stat-l">Failed</div></div>
  <div class="stat"><div class="stat-n" style="color:#f59e0b">{len(plan.get('quick_wins',[]))}</div>
    <div class="stat-l">Quick Wins</div></div>
  <div class="stat"><div class="stat-n" style="color:#f97316">{len(plan.get('source_fix_tasks',[]))}</div>
    <div class="stat-l">URL Fixes Needed</div></div>
</div>

<h2>2. Priority Jurisdictions</h2>
<table>
<tr><th>Urgency</th><th>Jurisdiction</th><th>Score</th>
    <th>Total</th><th>Active</th><th>Failed</th><th>Recommended Actions</th></tr>
{j_rows if j_rows else '<tr><td colspan="7" style="color:#6b7280">All jurisdictions at acceptable level.</td></tr>'}
</table>

<h2>3. Quick Wins — Enable Without Adapter</h2>
<p style="color:#9ca3af;font-size:0.85em;margin-bottom:12px">
  These sources already extract well — enabling them improves coverage immediately.
</p>
<table>
<tr><th>Source Name</th><th>Jurisdiction</th><th>Category</th>
    <th style="color:#22c55e">Chars</th><th>Extractor</th></tr>
{qw_rows if qw_rows else '<tr><td colspan="5" style="color:#6b7280">No quick wins identified.</td></tr>'}
</table>

<h2>4. Source URL Fixes Required</h2>
<p style="color:#9ca3af;font-size:0.85em;margin-bottom:12px">
  These sources fail due to DNS, SSL, or URL errors — no adapter needed, fix the URL.
</p>
<table>
<tr><th>Source Name</th><th>Jurisdiction</th><th>Error Type</th><th>Suggested Fix</th></tr>
{fix_rows if fix_rows else '<tr><td colspan="4" style="color:#6b7280">No URL fix tasks identified.</td></tr>'}
</table>

<h2>5. Source Expansion Suggestions</h2>
<ul>
{_li(plan.get('source_expansion_suggestions', []), '#93c5fd')}
</ul>

<h2>6. Roadmap</h2>
<div class="card">{roadmap_html}</div>

<div class="disclaimer">
  <strong>Disclaimer:</strong> {plan.get('disclaimer', '')}
</div>

</body>
</html>"""

    return html


def export_coverage_plan_html(plan: dict, reports_dir: Path | None = None) -> Path:
    out_dir = reports_dir or _REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"coverage_plan_{date.today().isoformat()}.html"
    path.write_text(build_coverage_plan_html(plan), encoding="utf-8")
    return path
