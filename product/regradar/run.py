#!/usr/bin/env python3
"""
RegRadar v10 — CLI runner

Usage
-----
    python run.py <url>                          # single URL (backward-compat)
    python run.py url <url>                      # single URL (explicit)
    python run.py all                            # monitor all enabled sources once
    python run.py watch                          # watch mode: repeat every 60 min
    python run.py watch --interval <minutes>     # watch mode: custom interval
    python run.py sources                        # list sources table
    python run.py health                         # source health diagnostic
    python run.py demo                           # client demo (no DB writes)
    python run.py demo --send-telegram           # demo + Telegram demo alert
    python run.py test-source <url>              # test a URL without saving it
    python run.py add-source                     # interactively add a new source
    python run.py report                         # export compliance report (last 7 days)
    python run.py report --last <days>           # export report for last N days

Exit codes: 0 = success, 1 = error, 2 = bad arguments
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.pipeline import init_pipeline, run_pipeline

# ── logging (quiet by default; set LOG_LEVEL=DEBUG to see internals) ──────────

_log_level = logging.getLevelName(
    __import__("os").getenv("LOG_LEVEL", "WARNING").upper()
)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# ── colour palette ────────────────────────────────────────────────────────────

_R      = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_CYAN   = "\033[36m"
_BLUE   = "\033[34m"
_WHITE  = "\033[97m"
_BG_RED = "\033[41m"
_BG_YEL = "\033[43m"

_RISK_COLOR = {"HIGH": _RED, "MEDIUM": _YELLOW, "LOW": _GREEN}
_RISK_ICON  = {"HIGH": "🔴", "MEDIUM": "🟡",   "LOW": "🟢"}

_JURISDICTION_FLAG = {
    "AE": "🇦🇪", "SA": "🇸🇦", "SG": "🇸🇬", "HK": "🇭🇰",
    "QA": "🇶🇦", "BH": "🇧🇭", "MY": "🇲🇾", "TR": "🇹🇷",
    "RU": "🇷🇺", "KZ": "🇰🇿", "AZ": "🇦🇿",
    "BY": "🇧🇾", "UZ": "🇺🇿", "INT": "🌐",
    "GE": "🇬🇪", "AM": "🇦🇲",
}

WIDTH = 68


# ── output helpers ────────────────────────────────────────────────────────────

def _hr(char: str = "─") -> None:
    print(char * WIDTH)


def _label(key: str, value: str) -> None:
    print(f"   {_DIM}{key:<26}{_R}{value}")


def _print_header(url: str) -> None:
    _hr()
    print(f"  {_BOLD}RegRadar v4{_R} — regulatory change detection")
    print(f"  {_DIM}URL:{_R} {_CYAN}{url}{_R}")
    _hr()


def _print_risk_banner(risk: str) -> None:
    col  = _RISK_COLOR.get(risk, _R)
    if risk == "HIGH":
        print(
            f"\n{_BG_RED}{_WHITE}{_BOLD}"
            f"  ⚠  HIGH RISK — IMMEDIATE COMPLIANCE REVIEW REQUIRED  ⚠  "
            f"{_R}\n"
        )
    elif risk == "MEDIUM":
        print(
            f"\n{_BG_YEL}{_BOLD}"
            f"  ⚡ MEDIUM RISK — Compliance review recommended          "
            f"{_R}\n"
        )
    else:
        icon = _RISK_ICON.get(risk, "")
        print(f"\n  {col}{_BOLD}{icon} {risk} RISK{_R}\n")


def _print_no_change() -> None:
    print(f"\n{_GREEN}✓  No changes detected.{_R}")
    print(f"   Content hash matches the stored baseline.\n")


def _print_baseline(result: dict) -> None:
    risk = result.get("risk_level", "LOW")
    col  = _RISK_COLOR.get(risk, _R)
    icon = _RISK_ICON.get(risk, "")
    print(f"\n{_CYAN}★  First run — baseline stored.{_R}")
    _label("Extracted characters:", f"{result.get('chars', 0):,}")
    _label("Initial risk signal:", f"{col}{icon} {risk}{_R}")
    _label("Timestamp:", result.get("created_at", ""))
    print(f"\n   {_DIM}No Telegram alert sent for baseline runs.{_R}\n")


def _print_changed(result: dict) -> None:
    risk = result.get("risk_level", "LOW")
    col  = _RISK_COLOR.get(risk,   _R)
    icon = _RISK_ICON.get(risk,    "")

    print(f"\n{_YELLOW}⚡  Content changed!{_R}")
    _print_risk_banner(risk)

    ai_badge  = f"{_GREEN}✅ AI-enhanced (Claude){_R}"   if result.get("ai_used")       else f"{_DIM}📏 Rule-based{_R}"
    tg_badge  = f"{_GREEN}✅ Sent{_R}"                   if result.get("telegram_sent") else f"{_DIM}Not sent{_R}"

    _label("Risk level:",              f"{col}{_BOLD}{icon} {risk}{_R}")
    _label("Analysis method:",         ai_badge)
    _label("Telegram alert:",          tg_badge)

    # Multilingual fields (v9) — shown only when present
    src_lang = result.get("source_language", "")
    if src_lang:
        _label("Source language:",     src_lang.upper())
    out_lang = result.get("output_language", "")
    if out_lang:
        _label("Brief language:",      out_lang.upper())
    affected = result.get("affected_entities", [])
    if affected:
        _label("Affected entities:",   ", ".join(str(e) for e in affected[:4]))
    urgency = result.get("urgency", "")
    if urgency:
        _label("Urgency:",             urgency)
    dl = result.get("deadline")
    if dl:
        _label("Deadline:",            str(dl))

    # Confidence + review (v11 — from AI semantic analysis when available)
    confidence = result.get("confidence", "")
    if confidence:
        conf_col = _GREEN if confidence == "high" else (_YELLOW if confidence == "medium" else _DIM)
        _label("Analysis confidence:", f"{conf_col}{confidence}{_R}")
    rev_req = result.get("review_required", False)
    rev_rsn = result.get("review_reason", "")
    if confidence:
        _label("Review required:",     f"{_RED}Yes{_R}" if rev_req else f"{_GREEN}No{_R}")
        if rev_req and rev_rsn:
            _label("Review reason:",   rev_rsn)

    # Semantic findings table (v11 — only present when AI analysis succeeded)
    sf = result.get("semantic_findings", {})
    if sf:
        _hr("·")
        print(f"  {_BOLD}Semantic Analysis:{_R}")
        def _sem(lbl: str, val: object) -> None:
            if isinstance(val, bool):
                v_str = f"{_GREEN}Yes{_R}" if val else f"{_DIM}No{_R}"
            else:
                col = _RED if val in ("high", "critical") else (
                    _YELLOW if val in ("medium", "material") else _DIM
                )
                v_str = f"{col}{val}{_R}"
            print(f"   {_DIM}{lbl:<26}{_R}  {v_str}")
        _sem("New obligation:",        sf.get("new_obligation",       False))
        _sem("Deadline detected:",     sf.get("deadline_detected",    False))
        _sem("Reporting required:",    sf.get("reporting_required",   False))
        _sem("Licensing impact:",      sf.get("licensing_impact",     False))
        _sem("Enforcement exposure:",  sf.get("enforcement_exposure", False))
        _sem("Operational impact:",    sf.get("operational_impact",   "unknown"))
        _sem("Materiality:",           sf.get("materiality",          "unknown"))
        _hr("·")

    _label("Reason:",                  result.get("risk_reason", ""))
    _label("Timestamp:",               result.get("created_at", ""))
    _label("Characters extracted:",    f"{result.get('chars', 0):,}")
    _label("Added paragraphs:",        f"{col}{_BOLD}{result.get('added_count', 0)}{_R}")
    _label("Removed paragraphs:",      str(result.get("removed_count", 0)))
    _label("Modified sections:",       str(result.get("modified_count", 0)))

    summary = result.get("executive_summary", "")
    if summary:
        print(f"\n  {_BOLD}Executive Summary:{_R}")
        for line in _wrap(summary, WIDTH - 4):
            print(f"    {line}")

    action = result.get("business_action_required", "")
    if action:
        print(f"\n  {_BOLD}Required Business Action:{_R}")
        for line in _wrap(action, WIDTH - 4):
            print(f"    {_YELLOW}{line}{_R}")

    added   = result.get("added",   [])
    removed = result.get("removed", [])

    if added:
        _hr("·")
        print(f"  {_BOLD}Added content:{_R}")
        for i, block in enumerate(added[:5], 1):
            preview = block[:110] + ("…" if len(block) > 110 else "")
            print(f"  {_GREEN}+{_R} [{i}] {preview}")
        if len(added) > 5:
            print(f"       {_DIM}… and {len(added)-5} more{_R}")

    if removed:
        _hr("·")
        print(f"  {_BOLD}Removed content:{_R}")
        for i, block in enumerate(removed[:5], 1):
            preview = block[:110] + ("…" if len(block) > 110 else "")
            print(f"  {_RED}-{_R} [{i}] {preview}")
        if len(removed) > 5:
            print(f"       {_DIM}… and {len(removed)-5} more{_R}")

    _hr()
    print()


def _wrap(text: str, width: int) -> list[str]:
    words  = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = current + (" " if current else "") + word
    if current:
        lines.append(current)
    return lines or [""]


# ── deep source discovery helpers ────────────────────────────────────────────

def _suggest_next_step(verdict: str, mode: str, result: dict) -> str:
    if not result.get("safe_url"):
        return "Fix URL validation issue before testing"
    if verdict == "can_monitor":
        if mode == "html":
            return "Activate as HTML source — run add-source or set enabled=true in sources.json"
        if mode == "js_html":
            return "Activate as JS-rendered HTML source — Playwright JS mode works"
        if mode == "feed":
            return "Activate as feed source — RSS/Atom feed is available"
        if mode == "sitemap":
            return "Activate as sitemap source — sitemap has usable links"
        if mode == "documents":
            return "Activate as document source — install pypdf/python-docx if not done"
        return "Activate source (mode determined)"
    if verdict == "needs_adapter":
        return "Build a custom source adapter for this site's publication structure"
    # cannot_monitor
    if result.get("page", {}).get("status") == "ok":
        return "Source unavailable or blocked — manual review required"
    return "Find the correct official URL — this domain may be unreachable or moved"


def _readiness_bar(score: int) -> str:
    """ASCII progress bar for 0-100 readiness score."""
    filled = round(score / 100 * 20)
    bar    = "█" * filled + "░" * (20 - filled)
    if score >= 75:
        col = _GREEN
    elif score >= 50:
        col = _YELLOW
    else:
        col = _RED
    return f"{col}[{bar}]{_R}  {col}{score}/100{_R}"


def _cmd_test_source_deep(url: str) -> None:
    from app.source_discovery import discover_source_capabilities

    print(f"\n  Testing source {_DIM}(deep mode){_R}: {_CYAN}{url}{_R}")
    print(f"  {_DIM}Running 6-layer discovery — may take 60+ seconds…{_R}\n")

    result = discover_source_capabilities(url, deep=True)

    page = result["page"]
    caps = result["capabilities"]
    docs = result["documents"]
    feeds    = result["feeds"]
    sitemaps = result["sitemaps"]

    cv    = result.get("client_verdict",   "unavailable")
    title = result.get("client_title",     "Source unavailable")
    summ  = result.get("client_summary",   "")
    nxt   = result.get("client_next_step", "")
    score = result.get("readiness_score",  0)

    # ── Business verdict block (shown first) ─────────────────────────
    _hr("═")
    _CV_ICON = {
        "ready":          f"{_GREEN}✅  {_BOLD}",
        "limited":        f"{_YELLOW}⚡  {_BOLD}",
        "custom_adapter": f"{_YELLOW}🔧  {_BOLD}",
        "unavailable":    f"{_RED}✗   {_BOLD}",
    }
    print(f"  {_CV_ICON.get(cv, '')}{title}{_R}")
    print(f"  Readiness score:  {_readiness_bar(score)}")
    print()

    if not result["safe_url"]:
        print(f"  {_DIM}{result['reason']}{_R}")
        _hr("═")
        print()
        sys.exit(1)

    for line in _wrap(summ, WIDTH - 4):
        print(f"  {_DIM}{line}{_R}")
    print()
    _label("Suggested next step:", nxt)
    _hr("═")

    # ── Technical details ─────────────────────────────────────────────
    print(f"  {_BOLD}Technical Details{_R}")
    _hr("·")

    # Safety
    safe_str = f"{_GREEN}PASS{_R}" if result["safe_url"] else f"{_RED}FAIL{_R}"
    _label("Safety:", safe_str)

    # HTTP status
    hs = page.get("http_status")
    if hs is not None:
        hs_col = _GREEN if 200 <= hs < 300 else (_YELLOW if 300 <= hs < 400 else _RED)
        _label("HTTP status:", f"{hs_col}{hs}{_R}")
    else:
        _label("HTTP status:", f"{_DIM}unknown{_R}")

    _label("HTML chars:",       f"{page.get('html_chars', 0):,}")
    _label("Extracted chars:",  f"{page.get('extracted_chars', 0):,}")
    _label("Best extractor:",   page.get("best_extractor", "none"))

    q = page.get("quality", "failed")
    q_str = (
        f"{_GREEN}good{_R}"         if q == "good" else
        f"{_YELLOW}low_content{_R}" if q == "low_content" else
        f"{_RED}failed{_R}"
    )
    _label("Page quality:", q_str)
    if page.get("used_playwright"):
        _label("Rendering:", f"{_DIM}Playwright (JS-rendered){_R}")

    _hr("·")

    def _yn(val: bool) -> str:
        return f"{_GREEN}yes{_R}" if val else f"{_DIM}no{_R}"

    _label("HTML monitoring:",        _yn(caps["html_monitoring"]))
    _label("JS-rendered monitoring:", _yn(caps["js_html_monitoring"]))

    feed_str = _yn(caps["feed_monitoring"])
    if feeds:
        f0 = feeds[0]
        feed_str += f"  {_DIM}— {f0['url']}  ({f0.get('items_found', 0)} items){_R}"
    _label("Feed monitoring:", feed_str)

    sm_str = _yn(caps["sitemap_monitoring"])
    if sitemaps:
        best_sm = max(sitemaps, key=lambda s: s.get("links_found", 0))
        sm_str += f"  {_DIM}— {best_sm['url']}  ({best_sm.get('links_found', 0)} links){_R}"
    _label("Sitemap monitoring:", sm_str)

    doc_str = _yn(caps["document_monitoring"])
    total_docs = (
        docs["pdf_links_found"] + docs["docx_links_found"] + docs["xlsx_links_found"]
    )
    if total_docs > 0:
        doc_str += (
            f"  {_DIM}(PDF:{docs['pdf_links_found']} "
            f"DOCX:{docs['docx_links_found']} "
            f"XLSX:{docs['xlsx_links_found']}){_R}"
        )
    _label("Document monitoring:", doc_str)

    samples = docs.get("sample_documents_tested", [])
    if samples:
        _hr("·")
        print(f"  {_BOLD}Document samples:{_R}")
        for s in samples:
            c  = s.get("chars", 0)
            st = f"{_GREEN}{c:,}c{_R}" if c >= 100 else f"{_RED}0c{_R}"
            sv = f"{_GREEN}ok{_R}" if s.get("status") == "ok" else f"{_RED}failed{_R}"
            nm = s["url"].split("/")[-1][:40]
            print(f"    {_DIM}{nm}{_R}  {sv}  {st}")

    _hr("·")

    mode = result["recommended_mode"]
    mode_col = {
        "html": _GREEN, "js_html": _GREEN, "feed": _GREEN,
        "sitemap": _GREEN, "documents": _GREEN,
        "adapter": _YELLOW, "unavailable": _RED,
    }.get(mode, _DIM)
    _label("Recommended mode:", f"{mode_col}{_BOLD}{mode}{_R}")

    verdict = result["verdict"]
    if verdict == "can_monitor":
        v_str = f"{_GREEN}{_BOLD}can_monitor{_R}"
    elif verdict == "needs_adapter":
        v_str = f"{_YELLOW}needs_adapter{_R}"
    else:
        v_str = f"{_RED}cannot_monitor{_R}"
    _label("Verdict:", v_str)
    _label("Reason:",  result["reason"])

    _hr()
    print()
    sys.exit(0 if page["status"] == "ok" else 1)


# ── single-URL command ────────────────────────────────────────────────────────

def _run_single_url(url: str) -> None:
    if not url.startswith(("http://", "https://")):
        print(f"{_RED}Error:{_R} URL must start with http:// or https://", file=sys.stderr)
        sys.exit(2)

    _print_header(url)
    init_pipeline()

    try:
        result = run_pipeline(url)

    except KeyboardInterrupt:
        print(f"\n{_DIM}Interrupted.{_R}", file=sys.stderr)
        sys.exit(0)

    except TimeoutError as exc:
        print(f"\n{_RED}Timeout:{_R} {exc}", file=sys.stderr)
        sys.exit(1)

    except ValueError as exc:
        print(f"\n{_RED}Scrape error:{_R} {exc}", file=sys.stderr)
        sys.exit(1)

    except Exception as exc:
        print(f"\n{_RED}Unexpected error:{_R} {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not result["changed"]:
        _print_no_change()
        sys.exit(0)

    if result.get("is_new"):
        _print_baseline(result)
        sys.exit(0)

    _print_changed(result)
    sys.exit(0)


# ── sources command ────────────────────────────────────────────────────────────

def _cmd_sources() -> None:
    from app.sources import load_sources

    sources = load_sources()

    if not sources:
        print("  No sources found in sources.json.")
        sys.exit(0)

    _hr()
    print(f"  {_BOLD}RegRadar — configured sources{_R}")
    _hr()

    _STATUS_COL = {
        "active":   (_GREEN,  "active  "),
        "limited":  (_YELLOW, "limited "),
        "mapped":   (_BLUE,   "mapped  "),
        "disabled": (_DIM,    "disabled"),
    }

    col_w = {"#": 3, "En": 2, "St": 8, "Jur": 3, "Cat": 20, "Name": 34}
    header = (
        f"  {'#':<{col_w['#']}}  "
        f"{'En':<{col_w['En']}}  "
        f"{'Status':<{col_w['St']}}  "
        f"{'Jur':<{col_w['Jur']}}  "
        f"{'Category':<{col_w['Cat']}}  "
        f"Name"
    )
    print(f"{_BOLD}{header}{_R}")
    _hr("·")

    for i, src in enumerate(sources, 1):
        enabled  = f"{_GREEN}✓{_R}" if src["enabled"] else f"{_DIM}–{_R}"
        jur      = src.get("jurisdiction", "")
        flag     = _JURISDICTION_FLAG.get(jur, " ")
        cat      = src.get("category", "")[:col_w["Cat"]]
        name     = src.get("name", src["url"])[:col_w["Name"]]
        st_key   = src.get("status", "")
        st_col, st_lbl = _STATUS_COL.get(st_key, (_DIM, st_key[:8]))
        is_dim   = not src["enabled"]
        dim, rst = (_DIM, _R) if is_dim else ("", "")
        print(
            f"  {dim}{i:<{col_w['#']}}  "
            f"{enabled}  "
            f"{st_col}{st_lbl}{_R}  "
            f"{flag}{jur:<{col_w['Jur']}}  "
            f"{dim}{cat:<{col_w['Cat']}}  "
            f"{name}{rst}"
        )

    _hr("·")
    enabled_count = sum(1 for s in sources if s["enabled"])
    mapped_count  = sum(1 for s in sources if s.get("status") == "mapped")
    active_count  = sum(1 for s in sources if s.get("status") == "active")
    print(
        f"  {_BOLD}{enabled_count}{_R} enabled  ·  "
        f"{_GREEN}{active_count}{_R} active  ·  "
        f"{_BLUE}{mapped_count}{_R} mapped  ·  "
        f"{len(sources)} total"
    )
    if mapped_count:
        print(
            f"  {_DIM}Mapped sources are coverage inventory — "
            f"run test-source before enabling.{_R}"
        )
    print()


# ── all command ───────────────────────────────────────────────────────────────

def _cmd_all() -> None:
    from app.monitor import monitor_all_sources
    from app.config import AI_MAX_CALLS_PER_RUN, ENABLE_AI_ANALYSIS

    _hr()
    print(f"  {_BOLD}RegRadar v4{_R} — monitoring all enabled sources")
    _hr()

    try:
        results = monitor_all_sources(verbose=True)
    except KeyboardInterrupt:
        print(f"\n{_DIM}Interrupted.{_R}", file=sys.stderr)
        sys.exit(0)

    if not results:
        sys.exit(0)

    # ── summary table ──────────────────────────────────────────────────
    _hr()
    print(f"  {_BOLD}Summary{_R}")
    _hr("·")

    ok_count      = sum(1 for r in results if r.get("status") != "error")
    changed_count = sum(1 for r in results if r.get("changed") and not r.get("is_new"))
    new_count     = sum(1 for r in results if r.get("is_new"))
    error_count   = sum(1 for r in results if r.get("status") == "error")

    for r in results:
        name   = r.get("source_name", r.get("url", "?"))[:36]
        jur    = r.get("jurisdiction", "")
        flag   = _JURISDICTION_FLAG.get(jur, " ")

        if r.get("status") == "error":
            status_str = f"{_RED}✗  error{_R}"
        elif not r.get("changed"):
            status_str = f"{_GREEN}✓  unchanged{_R}"
        elif r.get("is_new"):
            status_str = f"{_CYAN}★  baseline{_R}"
        else:
            risk  = r.get("risk_level", "LOW")
            col   = _RISK_COLOR.get(risk, _R)
            icon  = _RISK_ICON.get(risk, "")
            added = r.get("added_count", 0)
            rem   = r.get("removed_count", 0)
            status_str = (
                f"{_YELLOW}⚡  changed{_R}  "
                f"{col}{icon} {risk}{_R}  "
                f"+{added} -{rem}"
            )

        quality = r.get("extraction_quality", "")
        chars   = r.get("extracted_chars")
        src_st  = r.get("source_status", "active")

        if quality == "good":
            qual_badge = f"{_GREEN}✓ good{_R}"
        elif quality == "low_content":
            qual_badge = f"{_YELLOW}⚠ low{_R}"
        elif quality == "failed":
            qual_badge = f"{_RED}✗ fail{_R}"
        else:
            qual_badge = ""

        chars_str   = f"{chars:>5,}c" if chars is not None else "      "
        limited_str = f"  {_DIM}[limited]{_R}" if src_st == "limited" else ""
        qual_col    = f"  {chars_str}  {qual_badge}" if qual_badge else ""

        print(f"  {flag} {name:<36}  {status_str}{qual_col}{limited_str}")

    _hr("·")
    print(
        f"  {_DIM}Total: {len(results)}  "
        f"ok: {ok_count}  "
        f"changed: {changed_count}  "
        f"new: {new_count}  "
        f"errors: {error_count}{_R}"
    )
    if ENABLE_AI_ANALYSIS:
        ai_used_total = max((r.get("ai_calls_used", 0) for r in results), default=0)
        ai_limit      = AI_MAX_CALLS_PER_RUN
        ai_col        = (
            _RED    if ai_used_total >= ai_limit and ai_limit > 0 else
            _YELLOW if ai_used_total > 0 else
            _DIM
        )
        print(
            f"  {_DIM}AI calls: {_R}{ai_col}{ai_used_total}{_R}"
            f"{_DIM} / {ai_limit} limit per run{_R}"
        )
    print()

    sys.exit(1 if error_count == len(results) else 0)


# ── health command ────────────────────────────────────────────────────────────

def _cmd_health() -> None:
    from app.health import run_source_health_check

    _hr()
    print(f"  {_BOLD}RegRadar v6{_R} — source health diagnostic")
    print(f"  {_DIM}Fetching all sources (enabled + disabled). May take several minutes.{_R}")
    _hr()

    results = run_source_health_check()

    if not results:
        print("  No sources found in sources.json.")
        sys.exit(0)

    # ── table header ───────────────────────────────────────────────────
    _hr()
    hdr_source  = f"{'Source':<33}"
    hdr_rest    = f"{'Jur':<3}  {'Status':<8}  En  {'Chars':>7}  {'Quality':<10}  Verdict"
    print(f"  {_BOLD}{hdr_source}  {hdr_rest}{_R}")
    _hr("·")

    counts = {"PASS": 0, "WARN": 0, "SKIP": 0, "FAIL": 0}

    for r in results:
        name       = r["name"][:33]
        jur        = r["jurisdiction"]
        flag       = _JURISDICTION_FLAG.get(jur, " ")
        status     = r["status"][:8]
        enabled    = r["enabled"]
        chars      = r["extracted_chars"]
        quality    = r["extraction_quality"]
        verdict    = r["verdict"]
        has_error  = bool(r.get("error"))

        en_str    = f"{_GREEN}✓{_R}" if enabled else f"{_DIM}–{_R}"
        chars_str = f"{chars:>6,}c" if chars else f"{'–':>7}"

        if quality == "good":
            qual_str = f"{_GREEN}✓ good{_R}"
        elif quality == "low_content":
            qual_str = f"{_YELLOW}⚠ low{_R}"
        elif has_error:
            qual_str = f"{_RED}error{_R}"
        else:
            qual_str = f"{_DIM}–{_R}"

        if verdict == "PASS":
            verd_str = f"{_GREEN}{_BOLD}PASS{_R}"
        elif verdict == "WARN":
            verd_str = f"{_YELLOW}WARN{_R}"
        elif verdict == "SKIP":
            verd_str = f"{_DIM}SKIP{_R}"
        else:
            verd_str = f"{_RED}FAIL{_R}"

        counts[verdict] = counts.get(verdict, 0) + 1

        dim = _DIM if not enabled else ""
        rst = _R   if not enabled else ""

        print(
            f"  {dim}{flag} {name:<33}  {jur:<3}  {status:<8}  "
            f"{en_str}  {chars_str}  {qual_str:<10}  {verd_str}{rst}"
        )

    _hr("·")
    p, w, s, f_ = counts["PASS"], counts["WARN"], counts["SKIP"], counts["FAIL"]
    print(
        f"  {_GREEN}PASS: {p}{_R}  "
        f"{_YELLOW}WARN: {w}{_R}  "
        f"{_DIM}SKIP: {s}{_R}  "
        f"{_RED}FAIL: {f_}{_R}"
    )
    print()

    # Exit 1 only if all enabled sources failed
    enabled_count = sum(1 for r in results if r["enabled"])
    fail_enabled  = sum(1 for r in results if r["enabled"] and r["verdict"] == "FAIL")
    sys.exit(1 if enabled_count > 0 and fail_enabled == enabled_count else 0)


# ── demo command ──────────────────────────────────────────────────────────────

def _cmd_demo(send_alert: bool = False) -> None:
    from app.demo import run_demo_change

    demo_sep = "═" * WIDTH

    # ── DEMO banner ───────────────────────────────────────────────────
    print(f"\n{_CYAN}{demo_sep}{_R}")
    print(f"  {_BOLD}{_YELLOW}⚡  RegRadar v7 — DEMO MODE{_R}")
    print(f"  {_DIM}Simulated regulatory change — for presentation purposes only.{_R}")
    print(f"  {_DIM}No production database writes. No real monitoring data.{_R}")
    print(f"{_CYAN}{demo_sep}{_R}")

    result = run_demo_change(send_alert=send_alert)

    # ── Source header ─────────────────────────────────────────────────
    _hr()
    print(f"  {_BOLD}URL:{_R}           {_CYAN}{result['url']}{_R}")
    _label("Source:",        result["source_name"])
    _label("Jurisdiction:",  result["jurisdiction"])
    _label("Category:",      result["category"])
    _label("Timestamp:",     result.get("created_at", ""))
    _hr()

    # ── Risk banner + metadata ────────────────────────────────────────
    _print_risk_banner("HIGH")

    _label("Risk reason:",       result["risk_reason"])
    _label("Added paragraphs:",  str(result["added_count"]))
    _label("Modified sections:", str(result["modified_count"]))
    _label("Chars extracted:",   f"{result['extracted_chars']:,}")
    _label("Quality:",           f"{_GREEN}✓ good{_R}")
    _label("Method:",            result["extraction_method"])
    _label("AI analysis:",       f"{_DIM}Not used (demo — no API key required){_R}")

    tg_sent = result.get("telegram_sent", False)
    _label(
        "Telegram alert:",
        f"{_GREEN}✅ Sent{_R}" if tg_sent else f"{_DIM}Not sent{_R}",
    )

    # Multilingual fields (v9)
    _label("Source language:",   result.get("source_language", "EN").upper())
    _label("Brief language:",    result.get("output_language", "EN").upper())
    affected_demo = result.get("affected_entities", [])
    if affected_demo:
        _label("Affected entities:", ", ".join(str(e) for e in affected_demo))
    urgency_demo = result.get("urgency", "")
    if urgency_demo:
        _label("Urgency:", urgency_demo)
    dl_demo = result.get("deadline")
    if dl_demo:
        _label("Deadline:", str(dl_demo))

    # Semantic findings (v11 — demo hardcoded, shows what AI detects)
    sf_demo = result.get("semantic_findings", {})
    if sf_demo:
        _hr(".")
        print(f"  {_BOLD}Semantic Analysis{_R} {_DIM}(simulated — no AI called){_R}")
        def _dsem(lbl: str, val: object) -> None:
            if isinstance(val, bool):
                v_str = f"{_GREEN}Yes{_R}" if val else f"{_DIM}No{_R}"
            else:
                col = _RED if val in ("high", "critical") else (
                    _YELLOW if val in ("medium", "material") else _DIM
                )
                v_str = f"{col}{val}{_R}"
            print(f"   {_DIM}{lbl:<26}{_R}  {v_str}")
        _dsem("New obligation:",       sf_demo.get("new_obligation",       False))
        _dsem("Deadline detected:",    sf_demo.get("deadline_detected",    False))
        _dsem("Reporting required:",   sf_demo.get("reporting_required",   False))
        _dsem("Licensing impact:",     sf_demo.get("licensing_impact",     False))
        _dsem("Enforcement exposure:", sf_demo.get("enforcement_exposure", False))
        _dsem("Operational impact:",   sf_demo.get("operational_impact",   "unknown"))
        _dsem("Materiality:",          sf_demo.get("materiality",          "unknown"))
        _hr(".")


    # ── Executive summary ─────────────────────────────────────────────
    print(f"\n  {_BOLD}Executive Summary:{_R}")
    for line in _wrap(result["executive_summary"], WIDTH - 4):
        print(f"    {line}")

    # ── Business action ───────────────────────────────────────────────
    print(f"\n  {_BOLD}Required Business Action:{_R}")
    for line in _wrap(result["business_action_required"], WIDTH - 4):
        print(f"    {_YELLOW}{line}{_R}")

    # ── Detected changes ──────────────────────────────────────────────
    added = result.get("added", [])
    if added:
        _hr("·")
        print(f"  {_BOLD}Detected regulatory changes ({len(added)} new paragraphs):{_R}")
        for i, block in enumerate(added, 1):
            preview = block[:120] + ("…" if len(block) > 120 else "")
            print(f"  {_GREEN}+{_R} [{i}] {preview}")

    # ── Demo footer ───────────────────────────────────────────────────
    _hr()
    print(f"\n{_CYAN}{demo_sep}{_R}")
    print(f"  {_BOLD}[DEMO]{_R} This simulation demonstrates RegRadar's capabilities:")
    print(f"  {_DIM}  • Real-time regulatory change detection across CIS + international sources{_R}")
    print(f"  {_DIM}  • Paragraph-level diff with added / removed / modified tracking{_R}")
    print(f"  {_DIM}  • Automated HIGH / MEDIUM / LOW risk classification{_R}")
    print(f"  {_DIM}  • AI-enhanced executive summaries and business action guidance{_R}")
    print(f"  {_DIM}  • Telegram compliance alerts for MEDIUM and HIGH risk changes{_R}")
    print(f"  {_DIM}  • Multi-source watch mode with configurable monitoring interval{_R}")
    print(f"{_CYAN}{demo_sep}{_R}\n")

    sys.exit(0)


# ── test-source command ───────────────────────────────────────────────────────

def _cmd_test_source(url: str, deep: bool = False) -> None:
    if deep:
        _cmd_test_source_deep(url)
        return

    from app.source_tester import test_source_url

    print(f"\n  Testing source: {_CYAN}{url}{_R}\n")

    result = test_source_url(url, include_documents=True)

    _hr()

    # Safety
    safe_str = f"{_GREEN}PASS{_R}" if result["safe_url"] else f"{_RED}FAIL{_R}"
    _label("Safety:", safe_str)

    if not result["safe_url"]:
        _label("Reason:", result["reason"])
        _hr()
        print()
        sys.exit(1)

    # Status
    status_col = _GREEN if result["status"] == "ok" else _RED
    _label("Status:", f"{status_col}{result['status']}{_R}")

    # HTTP status
    hs = result.get("http_status")
    if hs is not None:
        if 200 <= hs < 300:
            hs_col = _GREEN
        elif 300 <= hs < 400:
            hs_col = _YELLOW
        else:
            hs_col = _RED
        _label("HTTP status:", f"{hs_col}{hs}{_R}")
    else:
        _label("HTTP status:", f"{_DIM}unknown{_R}")

    # Content metrics
    _label("Extracted chars:", f"{result['extracted_chars']:,}")

    # Per-extractor breakdown (multi-strategy layer)
    method_detail = result.get("extraction_method_detail", "")
    if method_detail:
        _label("Best extractor:", method_detail)
    for c in result.get("extraction_candidates", []):
        cq = c.get("quality", "")
        cc = c.get("chars", 0)
        cm = c.get("method", "")
        if cq == "good":
            c_col = _GREEN
        elif cq == "low_content":
            c_col = _YELLOW
        else:
            c_col = _DIM
        marker = " ★" if cm == method_detail else "  "
        print(f"   {_DIM}{marker} {cm:<16}{_R}  {c_col}{cc:>7,}c  {cq}{_R}")

    _label("Links found:",     str(result["links_found"]))

    # Quality badge
    quality = result["extraction_quality"]
    if quality == "good":
        q_str = f"{_GREEN}GOOD{_R}"
    elif quality == "low_content":
        q_str = f"{_YELLOW}LOW_CONTENT{_R}"
    else:
        q_str = f"{_RED}FAILED{_R}"
    _label("Quality:", q_str)

    # Recommendations
    _label("Recommended status:",  result["recommended_status"])
    rec_en = result["recommended_enabled"]
    _label(
        "Recommended enabled:",
        f"{_GREEN}yes{_R}" if rec_en else f"{_YELLOW}no{_R}",
    )
    _label("Recommended method:", result["recommended_method"])

    # Verdict
    verdict = result["verdict"]
    if verdict == "can_monitor":
        v_str = f"{_GREEN}{_BOLD}can_monitor{_R}"
    elif verdict in ("needs_adapter", "limited"):
        v_str = f"{_YELLOW}needs_adapter{_R}"
    else:
        v_str = f"{_RED}cannot_monitor{_R}"
    _label("Verdict:", v_str)
    _label("Reason:",  result["reason"])

    # Document section
    doc_info = result.get("document_info")
    if doc_info and not doc_info.get("error"):
        _hr("·")
        print(f"  {_BOLD}Document Links:{_R}")
        _label("PDF links found:",    str(doc_info.get("documents_found", 0) - doc_info.get("doc_links", 0) - doc_info.get("docx_links", 0)))
        _label("DOC links found:",    str(doc_info.get("doc_links", 0)))
        _label("DOCX links found:",   str(doc_info.get("docx_links", 0)))
        pdf_proc = doc_info.get("pdf_processed", 0)
        _label("PDFs processed:",     str(pdf_proc))
        if pdf_proc > 0:
            _label("PDF extracted chars:", f"{doc_info.get('combined_chars', 0):,}")
            pdf_q = doc_info.get("quality", "failed")
            if pdf_q == "good":
                pq_str = f"{_GREEN}good{_R}"
            elif pdf_q == "low_content":
                pq_str = f"{_YELLOW}low_content{_R}"
            else:
                pq_str = f"{_DIM}failed{_R}"
            _label("PDF extraction quality:", pq_str)
            for item in doc_info.get("items", []):
                fn  = item["url"].split("/")[-1][:40]
                c   = item.get("chars", 0)
                m   = item.get("method", "none")
                err = item.get("error", "")
                if err:
                    print(f"    {_RED}✗{_R} {_DIM}{fn}{_R}  {_RED}{err[:60]}{_R}")
                else:
                    c_col = _GREEN if c >= 1000 else (_YELLOW if c >= 100 else _DIM)
                    print(f"    {_GREEN}✓{_R} {_DIM}{fn}{_R}  {c_col}{c:,}c{_R}  [{m}]")
    elif doc_info and doc_info.get("error"):
        _hr("·")
        _label("Document check:", f"{_DIM}error: {doc_info['error'][:60]}{_R}")

    _hr()
    print()
    sys.exit(0 if result["status"] == "ok" else 1)


# ── add-source command ────────────────────────────────────────────────────────

def _cmd_add_source() -> None:
    from app.source_discovery import discover_source_capabilities
    from app.source_tester import append_source_to_json, source_url_exists

    print(f"\n  {_BOLD}RegRadar — Add Source{_R}")
    print(f"  {_DIM}Interactive source registration wizard (deep discovery).{_R}\n")

    try:
        name         = input("  Source name: ").strip()
        url          = input("  URL: ").strip()
        jurisdiction = input("  Jurisdiction (e.g. RU, KZ, INT): ").strip().upper()
        category     = input("  Category (e.g. central_bank, finance_ministry): ").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {_DIM}Cancelled.{_R}\n")
        sys.exit(0)

    for field_name, field_val in (
        ("Source name",  name),
        ("URL",          url),
        ("Jurisdiction", jurisdiction),
        ("Category",     category),
    ):
        if not field_val:
            print(f"\n  {_RED}Error:{_R} {field_name} cannot be empty.", file=sys.stderr)
            sys.exit(2)

    print()

    if source_url_exists(url):
        print(f"  {_YELLOW}⚠  URL already exists in sources.json — duplicate not added.{_R}\n")
        sys.exit(0)

    print(f"  {_DIM}Running 6-layer deep discovery — may take 60+ seconds…{_R}\n")
    result = discover_source_capabilities(url, deep=True)

    if not result["safe_url"]:
        print(f"\n  {_RED}✗  URL rejected:{_R} {result['reason']}\n", file=sys.stderr)
        sys.exit(1)

    cv    = result.get("client_verdict",   "unavailable")
    title = result.get("client_title",     "Source unavailable")
    summ  = result.get("client_summary",   "")
    nxt   = result.get("client_next_step", "")
    score = result.get("readiness_score",  0)

    _hr("═")
    _CV_ICON = {
        "ready":          f"{_GREEN}✅  {_BOLD}",
        "limited":        f"{_YELLOW}⚡  {_BOLD}",
        "custom_adapter": f"{_YELLOW}🔧  {_BOLD}",
        "unavailable":    f"{_RED}✗   {_BOLD}",
    }
    print(f"  {_CV_ICON.get(cv, '')}{title}{_R}")
    print(f"  Readiness score:  {_readiness_bar(score)}")
    print()
    for line in _wrap(summ, WIDTH - 4):
        print(f"  {_DIM}{line}{_R}")
    print()
    _label("Recommended mode:", result.get("recommended_mode", "unavailable"))
    _label("Verdict:",          result.get("verdict", "cannot_monitor"))
    _label("Suggested action:", nxt)
    _hr("═")
    print()

    try:
        if cv == "ready":
            enable_raw = input("  Enable for active monitoring now? (yes/no) [yes]: ").strip().lower()
            answer        = "yes"
            final_status  = "active"
            final_enabled = enable_raw not in ("no", "n")

        elif cv == "limited":
            answer = input(
                "  Add as limited source (disabled, periodic review)? (yes/no) [yes]: "
            ).strip().lower()
            if answer in ("no", "n"):
                answer = "no"
            else:
                answer = "yes"
            final_status  = "limited"
            final_enabled = False

        elif cv == "custom_adapter":
            print(f"  {_DIM}This source requires a custom adapter before monitoring.{_R}")
            raw_choice = input(
                "  Add as mapped (inventory) for future adapter work? (yes/no) [yes]: "
            ).strip().lower()
            answer        = "no" if raw_choice in ("no", "n") else "yes"
            final_status  = "mapped"
            final_enabled = False

        else:  # unavailable
            print(
                f"  {_DIM}Source is currently unreachable. "
                f"You can add it as mapped inventory to revisit later.{_R}"
            )
            raw_choice = input(
                "  Add as mapped (inventory) or skip? (mapped/skip) [skip]: "
            ).strip().lower()
            if raw_choice in ("mapped", "m"):
                answer        = "yes"
                final_status  = "mapped"
                final_enabled = False
            else:
                answer        = "no"
                final_status  = "mapped"
                final_enabled = False

    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {_DIM}Cancelled — nothing added.{_R}\n")
        sys.exit(0)

    if answer not in ("yes", "y"):
        print(f"\n  {_DIM}Source not added.{_R}\n")
        sys.exit(0)

    new_source = {
        "name":         name,
        "url":          url,
        "jurisdiction": jurisdiction,
        "category":     category,
        "enabled":      final_enabled,
        "status":       final_status,
        "notes":        f"Added via add-source. Readiness: {score}/100. Verdict: {cv}.",
    }

    ok = append_source_to_json(new_source)
    if ok:
        en_label = f"{_GREEN}enabled{_R}" if final_enabled else f"{_DIM}disabled{_R}"
        print(
            f"\n  {_GREEN}✓{_R}  Source added to sources.json "
            f"({en_label}, status: {final_status}, readiness: {score}/100)\n"
        )
    else:
        print(f"\n  {_RED}✗{_R}  Failed to write to sources.json.\n", file=sys.stderr)
        sys.exit(1)


# ── report command ────────────────────────────────────────────────────────────

def _cmd_coverage(
    json_export: bool = False,
    html_export: bool = False,
    jurisdiction: str | None = None,
    category: str | None = None,
) -> None:
    """Coverage dashboard — uses latest source-audit JSON from reports/."""
    from app.coverage import (
        generate_coverage_report,
        print_coverage_report,
        export_coverage_json,
        export_coverage_html,
    )

    report = generate_coverage_report(use_existing_audit=True)
    print_coverage_report(report, jurisdiction=jurisdiction, category=category)

    if json_export:
        path = export_coverage_json(report)
        print(f"  {_GREEN}JSON exported →{_R} {path}\n")

    if html_export:
        path = export_coverage_html(report)
        print(f"  {_GREEN}HTML exported →{_R} {path}\n")


def _cmd_coverage_plan(
    json_export: bool = False,
    html_export: bool = False,
    jurisdiction: str | None = None,
    category: str | None = None,
) -> None:
    """Coverage improvement plan — reads latest coverage + audit JSONs."""
    from app.coverage_plan import (
        generate_coverage_plan,
        print_coverage_plan,
        export_coverage_plan_json,
        export_coverage_plan_html,
    )

    try:
        plan = generate_coverage_plan()
    except ValueError as exc:
        print(f"\n  {_RED}✗  {exc}{_R}\n", file=sys.stderr)
        sys.exit(1)

    # Apply simple jurisdiction/category filters to quick_wins and enable_candidates
    if jurisdiction:
        jur = jurisdiction.upper()
        plan["quick_wins"] = [
            w for w in plan["quick_wins"] if w["jurisdiction"] == jur
        ]
        plan["source_fix_tasks"] = [
            t for t in plan["source_fix_tasks"] if t["jurisdiction"] == jur
        ]
        plan["source_enable_candidates"] = [
            c for c in plan["source_enable_candidates"] if c["jurisdiction"] == jur
        ]
        plan["priority_jurisdictions"] = [
            j for j in plan["priority_jurisdictions"] if j["jurisdiction"] == jur
        ]
    if category:
        cat = category.lower()
        plan["quick_wins"] = [
            w for w in plan["quick_wins"] if w["category"] == cat
        ]
        plan["priority_categories"] = [
            c for c in plan["priority_categories"] if c["category"] == cat
        ]

    print_coverage_plan(plan)

    if json_export:
        path = export_coverage_plan_json(plan)
        print(f"  {_GREEN}JSON exported →{_R} {path}\n")

    if html_export:
        path = export_coverage_plan_html(plan)
        print(f"  {_GREEN}HTML exported →{_R} {path}\n")


def _cmd_test_mapped_deep(limit: int) -> None:
    """Deep batch discovery of mapped sources (no DB, no AI, no Telegram)."""
    from app.source_discovery import discover_source_capabilities
    from app.sources import load_sources

    all_sources = load_sources()
    mapped = [s for s in all_sources if s.get("status") == "mapped"]

    _hr()
    print(f"  {_BOLD}RegRadar — Deep Batch Discovery: Mapped Sources{_R}")
    print(f"  {_DIM}No DB writes · No AI · No Telegram · 6-layer analysis{_R}")
    _hr()

    if not mapped:
        print("  No mapped sources found in sources.json.")
        sys.exit(0)

    targets = mapped[:limit]
    print(
        f"  Running deep discovery on {len(targets)} of {len(mapped)} "
        f"mapped sources (limit={limit})\n"
        f"  {_DIM}This may take several minutes…{_R}\n"
    )

    _VERDICT_COL = {
        "can_monitor":    _GREEN,
        "needs_adapter":  _YELLOW,
        "cannot_monitor": _RED,
    }
    _MODE_COL = {
        "html": _GREEN, "js_html": _GREEN, "feed": _GREEN,
        "sitemap": _GREEN, "documents": _GREEN,
        "adapter": _YELLOW, "unavailable": _RED,
    }

    rows: list[tuple[dict, dict]] = []
    for i, src in enumerate(targets, 1):
        name = src["name"]
        jur  = src.get("jurisdiction", "")
        url  = src["url"]
        flag = _JURISDICTION_FLAG.get(jur, " ")
        print(f"  [{i}/{len(targets)}] {flag} {name[:44]} …", flush=True)
        try:
            r = discover_source_capabilities(url, deep=True)
        except Exception as exc:
            r = {
                "page":             {"extracted_chars": 0, "quality": "failed", "status": "failed"},
                "capabilities":     {"feed_monitoring": False, "sitemap_monitoring": False, "document_monitoring": False},
                "recommended_mode": "unavailable",
                "verdict":          "cannot_monitor",
                "reason":           str(exc),
                "feeds": [], "sitemaps": [], "documents": {"extractable_documents": 0},
            }
        rows.append((src, r))

        verdict = r.get("verdict", "cannot_monitor")
        mode    = r.get("recommended_mode", "unavailable")
        chars   = r.get("page", {}).get("extracted_chars", 0)
        vcol    = _VERDICT_COL.get(verdict, _DIM)
        mcol    = _MODE_COL.get(mode, _DIM)
        feed_y  = f"{_GREEN}✓{_R}" if r.get("capabilities", {}).get("feed_monitoring") else f"{_DIM}–{_R}"
        sm_y    = f"{_GREEN}✓{_R}" if r.get("capabilities", {}).get("sitemap_monitoring") else f"{_DIM}–{_R}"
        doc_y   = f"{_GREEN}✓{_R}" if r.get("capabilities", {}).get("document_monitoring") else f"{_DIM}–{_R}"
        print(
            f"       → {vcol}{verdict}{_R}  "
            f"mode:{mcol}{mode}{_R}  "
            f"{chars:>6,}c  "
            f"feed:{feed_y}  sm:{sm_y}  docs:{doc_y}"
        )

    _hr()
    print(
        f"  {_BOLD}{'Source':<34}  {'Jur':<3}  {'Chars':>6}  "
        f"{'Feed':<4}  {'SM':<4}  {'Doc':<4}  {'Mode':<12}  Verdict{_R}"
    )
    _hr("·")
    for src, r in rows:
        name    = src["name"][:34]
        jur     = src.get("jurisdiction", "")
        chars   = r.get("page", {}).get("extracted_chars", 0)
        verdict = r.get("verdict", "cannot_monitor")
        mode    = r.get("recommended_mode", "unavailable")
        caps    = r.get("capabilities", {})
        vcol    = _VERDICT_COL.get(verdict, _DIM)
        mcol    = _MODE_COL.get(mode, _DIM)
        feed_v  = f"{_GREEN}✓{_R}" if caps.get("feed_monitoring")    else f"{_DIM}–{_R}"
        sm_v    = f"{_GREEN}✓{_R}" if caps.get("sitemap_monitoring")  else f"{_DIM}–{_R}"
        doc_v   = f"{_GREEN}✓{_R}" if caps.get("document_monitoring") else f"{_DIM}–{_R}"
        print(
            f"  {name:<34}  {jur:<3}  {chars:>6,}c  "
            f"{feed_v}     {sm_v}     {doc_v}     "
            f"{mcol}{mode:<12}{_R}  {vcol}{verdict}{_R}"
        )

    _hr("·")
    can   = sum(1 for _, r in rows if r.get("verdict") == "can_monitor")
    needs = sum(1 for _, r in rows if r.get("verdict") == "needs_adapter")
    cant  = sum(1 for _, r in rows if r.get("verdict") == "cannot_monitor")
    feeds_found = sum(1 for _, r in rows if r.get("capabilities", {}).get("feed_monitoring"))
    sm_found    = sum(1 for _, r in rows if r.get("capabilities", {}).get("sitemap_monitoring"))
    doc_found   = sum(1 for _, r in rows if r.get("capabilities", {}).get("document_monitoring"))
    print(
        f"  {_GREEN}can_monitor: {can}{_R}  "
        f"{_YELLOW}needs_adapter: {needs}{_R}  "
        f"{_RED}cannot_monitor: {cant}{_R}"
    )
    print(
        f"  {_DIM}feeds found: {feeds_found}  sitemaps: {sm_found}  "
        f"extractable docs: {doc_found}{_R}"
    )
    print(
        f"\n  {_DIM}To activate: run 'add-source' or edit sources.json manually.{_R}\n"
    )


def _cmd_test_mapped(limit: int, deep: bool = False) -> None:
    """Batch-test mapped sources (no DB writes, no AI, no Telegram)."""
    if deep:
        _cmd_test_mapped_deep(limit)
        return

    from app.sources import load_sources
    from app.source_tester import test_source_url

    all_sources = load_sources()
    mapped = [s for s in all_sources if s.get("status") == "mapped"]

    _hr()
    print(f"  {_BOLD}RegRadar — Batch Test: Mapped Sources{_R}")
    print(
        f"  {_DIM}No DB writes · No AI · No Telegram · Safe anytime{_R}"
    )
    _hr()

    if not mapped:
        print("  No mapped sources found in sources.json.")
        sys.exit(0)

    targets = mapped[:limit]
    print(
        f"  Testing {len(targets)} of {len(mapped)} mapped sources "
        f"(limit={limit})\n"
    )

    _VERDICT_COL = {
        "can_monitor":    _GREEN,
        "needs_adapter":  _YELLOW,
        "cannot_monitor": _RED,
    }

    results = []
    for i, src in enumerate(targets, 1):
        name = src["name"]
        jur  = src.get("jurisdiction", "")
        url  = src["url"]
        flag = _JURISDICTION_FLAG.get(jur, " ")
        print(f"  [{i}/{len(targets)}] {flag} {name[:44]} …", flush=True)
        try:
            r = test_source_url(url)
        except Exception as exc:
            r = {
                "extracted_chars": 0,
                "extraction_quality": "failed",
                "extraction_method_detail": "error",
                "verdict": "cannot_monitor",
                "reason": str(exc),
            }
        results.append((src, r))
        verdict = r.get("verdict", "cannot_monitor")
        chars   = r.get("extracted_chars", 0)
        quality = r.get("extraction_quality", "failed")
        vcol    = _VERDICT_COL.get(verdict, _DIM)
        print(
            f"       → {vcol}{verdict}{_R}  "
            f"{chars:>6,}c  {quality}"
        )

    _hr()
    print(
        f"  {_BOLD}{'Source':<38}  {'Jur':<4}  "
        f"{'Chars':>6}  {'Quality':<12}  Verdict{_R}"
    )
    _hr("·")
    for src, r in results:
        name    = src["name"][:38]
        jur     = src.get("jurisdiction", "")
        chars   = r.get("extracted_chars", 0)
        quality = r.get("extraction_quality", "failed")
        verdict = r.get("verdict", "cannot_monitor")
        vcol    = _VERDICT_COL.get(verdict, _DIM)
        qcol    = _GREEN if quality == "good" else (_YELLOW if quality == "low_content" else _RED)
        print(
            f"  {name:<38}  {jur:<4}  "
            f"{chars:>6,}c  {qcol}{quality:<12}{_R}  "
            f"{vcol}{verdict}{_R}"
        )

    _hr("·")
    can   = sum(1 for _, r in results if r.get("verdict") == "can_monitor")
    needs = sum(1 for _, r in results if r.get("verdict") == "needs_adapter")
    cant  = sum(1 for _, r in results if r.get("verdict") == "cannot_monitor")
    print(
        f"  {_GREEN}can_monitor: {can}{_R}  "
        f"{_YELLOW}needs_adapter: {needs}{_R}  "
        f"{_RED}cannot_monitor: {cant}{_R}"
    )
    print(
        f"\n  {_DIM}To activate a source: run 'add-source' or edit sources.json manually.{_R}\n"
    )


def _cmd_report(days: int) -> None:
    from app.report import generate_report

    print(f"\n  {_BOLD}RegRadar v10 — Compliance Report Export{_R}")
    print(f"  {_DIM}Period: last {days} day{'s' if days != 1 else ''}{_R}\n")

    try:
        result = generate_report(days=days)
    except Exception as exc:
        print(f"  {_RED}Error generating report:{_R} {exc}", file=sys.stderr)
        sys.exit(1)

    _hr()
    _label("Markdown report:", result["markdown_path"])
    _label("HTML report:",     result["html_path"])
    _hr("·")
    _label("Total records:", str(result["total_records"]))
    _label("High risk:",     f"{_RED}{result['high_count']}{_R}")
    _label("Medium risk:",   f"{_YELLOW}{result['medium_count']}{_R}")
    _label("Low risk:",      f"{_GREEN}{result['low_count']}{_R}")
    _hr()

    if result["total_records"] == 0:
        print(
            f"  {_DIM}No monitoring records found for the last {days} "
            f"day{'s' if days != 1 else ''}. "
            f"Run 'python run.py all' first to populate the database.{_R}"
        )
    else:
        print(
            f"\n  {_GREEN}✓{_R}  Reports written to "
            f"{_CYAN}reports/{_R}\n"
        )

    sys.exit(0)


# ── ai-test command ───────────────────────────────────────────────────────────

def _cmd_ai_test() -> None:
    """
    Live AI semantic smoke test — no DB writes, no Telegram, safe anytime.

    Sends a synthetic regulatory diff to Claude and prints the full
    structured semantic result.  Exits 0 on success, 1 on failure.
    """
    from app.config import ANTHROPIC_API_KEY, ENABLE_AI_ANALYSIS

    _hr()
    print(f"  {_BOLD}RegRadar v11 — AI Semantic Smoke Test{_R}")
    print(f"  {_DIM}No DB writes. No Telegram. Safe to run anytime.{_R}")
    print(f"  {_DIM}Cost guard (AI_MAX_CALLS_PER_RUN) does not apply — single direct test.{_R}")
    _hr()

    if not ENABLE_AI_ANALYSIS:
        print(
            f"\n  {_YELLOW}⚠  AI analysis is disabled.{_R}\n"
            f"  Set ENABLE_AI_ANALYSIS=true in .env to activate.\n"
        )
        sys.exit(0)

    if not ANTHROPIC_API_KEY:
        print(
            f"\n  {_RED}✗  ANTHROPIC_API_KEY is not set.{_R}\n"
            f"  Add it to .env and set ENABLE_AI_ANALYSIS=true.\n"
        )
        sys.exit(1)

    from app.ai import analyze_change_with_ai

    url = "demo://ai-semantic-test"
    diff_result = {
        "added": [
            "Financial institutions shall submit updated internal control documentation "
            "to the regulator within 15 business days. Payment providers must also update "
            "transaction monitoring procedures and appoint a responsible compliance officer.",
            "Entities offering digital payment services must notify the supervisory authority "
            "before launching new customer-facing products.",
        ],
        "removed": [],
        "modified_count": 0,
    }
    rule_risk = {
        "risk_level": "MEDIUM",
        "reason": "Synthetic rule-based baseline for AI semantic smoke test.",
    }

    print(f"\n  {_DIM}Calling Claude — analysing synthetic regulatory diff…{_R}\n")

    result = analyze_change_with_ai(
        url             = url,
        diff_result     = diff_result,
        rule_based_risk = rule_risk,
        source_language = "en",
        output_language = "en",
    )

    if result is None:
        print(
            f"  {_RED}✗  AI analysis returned None.{_R}\n"
            f"  Check ANTHROPIC_API_KEY validity and account credits.\n"
            f"  Rule-based fallback would activate in real monitoring.\n"
        )
        sys.exit(1)

    risk = result.get("risk_level", "LOW")
    col  = _RISK_COLOR.get(risk, _R)
    icon = _RISK_ICON.get(risk, "")
    sf   = result.get("semantic_findings", {})
    conf = result.get("confidence", "")

    _print_risk_banner(risk)
    _label("Risk level:",    f"{col}{_BOLD}{icon} {risk}{_R}")
    _label("Reason:",        result.get("reason", ""))

    conf_col = _GREEN if conf == "high" else (_YELLOW if conf == "medium" else _DIM)
    _label("Confidence:",    f"{conf_col}{conf}{_R}")

    rev_req = result.get("review_required", False)
    rev_rsn = result.get("review_reason", "")
    _label("Review required:", f"{_RED}Yes{_R}" if rev_req else f"{_GREEN}No{_R}")
    if rev_req and rev_rsn:
        _label("Review reason:", rev_rsn)

    src_lang = result.get("source_language", "")
    out_lang = result.get("output_language", "")
    if src_lang:
        _label("Source language:", src_lang.upper())
    if out_lang:
        _label("Output language:", out_lang.upper())

    affected = result.get("affected_entities", [])
    _label("Affected entities:", ", ".join(str(e) for e in affected) if affected else f"{_DIM}none{_R}")

    urgency = result.get("urgency", "")
    _label("Urgency:",   urgency if urgency else f"{_DIM}none{_R}")

    deadline = result.get("deadline")
    _label("Deadline:",  str(deadline) if deadline else f"{_DIM}none detected{_R}")

    summary = result.get("executive_summary", "")
    if summary:
        print(f"\n  {_BOLD}Executive Summary:{_R}")
        for line in _wrap(summary, WIDTH - 4):
            print(f"    {line}")

    action = result.get("business_action_required", "")
    if action:
        print(f"\n  {_BOLD}Required Business Action:{_R}")
        for line in _wrap(action, WIDTH - 4):
            print(f"    {_YELLOW}{line}{_R}")

    if sf:
        _hr("·")
        print(f"  {_BOLD}Semantic Analysis:{_R}")
        def _sem(lbl: str, val: object) -> None:
            if isinstance(val, bool):
                v_str = f"{_GREEN}Yes{_R}" if val else f"{_DIM}No{_R}"
            else:
                c = _RED if val in ("high", "critical") else (
                    _YELLOW if val in ("medium", "material") else _DIM
                )
                v_str = f"{c}{val}{_R}"
            print(f"   {_DIM}{lbl:<26}{_R}  {v_str}")
        _sem("New obligation:",        sf.get("new_obligation",       False))
        _sem("Deadline detected:",     sf.get("deadline_detected",    False))
        _sem("Reporting required:",    sf.get("reporting_required",   False))
        _sem("Licensing impact:",      sf.get("licensing_impact",     False))
        _sem("Enforcement exposure:",  sf.get("enforcement_exposure", False))
        _sem("Operational impact:",    sf.get("operational_impact",   "unknown"))
        _sem("Materiality:",           sf.get("materiality",          "unknown"))

    _hr()
    print(f"\n  {_GREEN}✓  AI semantic analysis working correctly.{_R}\n")
    sys.exit(0)


# ── ai-health command ─────────────────────────────────────────────────────────

def _cmd_ai_health() -> None:
    """
    Check AI layer configuration and connectivity — no DB, no Telegram.

    Prints status of ENABLE_AI_ANALYSIS, API key presence, model name,
    brief language, and (when enabled) a lightweight connectivity test.
    Exits 0 if the layer is operational, 1 if not.
    """
    from app.config import (
        ANTHROPIC_API_KEY,
        ENABLE_AI_ANALYSIS,
        AI_OUTPUT_LANGUAGE,
        AI_BRIEF_LANGUAGE,
        AI_MIN_RISK_FOR_ANALYSIS,
        AI_MAX_CALLS_PER_RUN,
    )
    from app.ai_brief import _MODEL

    _hr()
    print(f"  {_BOLD}RegRadar — AI Layer Health Check{_R}")
    print(f"  {_DIM}No DB writes. No Telegram. Safe to run anytime.{_R}")
    _hr()

    ok = True

    def _check(label: str, value: str, good: bool) -> None:
        mark = f"{_GREEN}✓{_R}" if good else f"{_RED}✗{_R}"
        print(f"  {mark}  {_DIM}{label:<30}{_R}  {value}")

    _check("ENABLE_AI_ANALYSIS",
           f"{_GREEN}enabled{_R}" if ENABLE_AI_ANALYSIS else f"{_YELLOW}disabled{_R}",
           ENABLE_AI_ANALYSIS)

    key_present = bool(ANTHROPIC_API_KEY)
    _check("ANTHROPIC_API_KEY",
           f"{_GREEN}set ({len(ANTHROPIC_API_KEY)} chars){_R}" if key_present else f"{_RED}not set{_R}",
           key_present)

    _check("Model",          _MODEL,            True)
    _check("Output language", AI_OUTPUT_LANGUAGE, True)
    _check("Brief language",  AI_BRIEF_LANGUAGE,  True)
    _check("Min risk for AI", AI_MIN_RISK_FOR_ANALYSIS, True)
    _check("Max calls/run",   str(AI_MAX_CALLS_PER_RUN), True)

    if not ENABLE_AI_ANALYSIS:
        print(f"\n  {_YELLOW}AI analysis is disabled.{_R}")
        print(f"  Set {_DIM}ENABLE_AI_ANALYSIS=true{_R} in .env to activate.\n")
        sys.exit(0)

    if not key_present:
        print(f"\n  {_RED}ANTHROPIC_API_KEY is not set — AI unavailable.{_R}\n")
        ok = False
        sys.exit(1)

    # Lightweight connectivity test — one minimal message, not a real brief
    print(f"\n  {_DIM}Testing API connectivity…{_R}")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model      = _MODEL,
            max_tokens = 16,
            messages   = [{"role": "user", "content": "Reply with the word: ok"}],
        )
        reply = getattr(msg.content[0], "text", str(msg.content[0])).strip().lower()
        if "ok" in reply:
            print(f"  {_GREEN}✓  API connectivity OK — model responded correctly.{_R}")
        else:
            print(f"  {_YELLOW}⚠  API responded but output unexpected: {reply!r:.40}{_R}")
    except Exception as exc:
        print(f"  {_RED}✗  API connectivity failed: {exc}{_R}")
        ok = False

    _hr()
    if ok:
        print(f"\n  {_GREEN}✓  AI layer is healthy and ready.{_R}\n")
        sys.exit(0)
    else:
        print(f"\n  {_RED}✗  AI layer has errors — check configuration above.{_R}\n")
        sys.exit(1)


# ── ai-brief-test command ─────────────────────────────────────────────────────

def _cmd_ai_brief_test() -> None:
    """
    Smoke-test generate_ai_brief() with synthetic text — no DB, no Telegram.

    Uses a hardcoded HIGH-risk regulatory paragraph so the result is
    predictable regardless of network availability.  Prints a formatted
    compliance brief showing all standardised fields.
    Exits 0 always (fallback brief is a valid result).
    """
    from app.ai_brief import generate_ai_brief

    _hr()
    print(f"  {_BOLD}RegRadar — AI Compliance Brief Test{_R}")
    print(f"  {_DIM}No DB writes. No Telegram. Fallback brief is a valid result.{_R}")
    _hr()

    test_text = (
        "Article 7 — Mandatory VASP Licensing. With effect from 1 September 2026, "
        "any entity providing virtual asset exchange, custody, or transfer services "
        "must obtain a Type-II Financial Services Licence from the National Financial "
        "Monitoring Agency within 120 days. Continued operation without a valid licence "
        "constitutes a criminal offence and may result in a fine of up to USD 250,000 "
        "per day of non-compliance. Directors may be held personally liable under "
        "amended Section 38 of the Financial Crime Act."
    )
    test_meta = {
        "source_name":     "[TEST] Synthetic Regulatory Source",
        "url":             "demo://ai-brief-test",
        "jurisdiction":    "DEMO",
        "category":        "financial_regulator",
        "source_language": "en",
        "output_language": "en",
    }

    print(f"\n  {_DIM}Calling generate_ai_brief()…{_R}\n")
    brief = generate_ai_brief(test_text, test_meta)

    risk    = brief.get("risk_level", "LOW")
    col     = _RISK_COLOR.get(risk, _R)
    icon    = _RISK_ICON.get(risk, "")
    ai_used = brief.get("ai_used", False)
    fb_used = brief.get("fallback_used", False)

    _print_risk_banner(risk)
    _label("Risk level:",    f"{col}{_BOLD}{icon} {risk}{_R}")
    _label("AI used:",       f"{_GREEN}Yes{_R}" if ai_used else f"{_YELLOW}No (fallback){_R}")
    _label("Fallback used:", f"{_YELLOW}Yes{_R}" if fb_used else f"{_GREEN}No{_R}")
    _label("Model:",         brief.get("model") or f"{_DIM}none{_R}")
    if brief.get("error"):
        _label("Error:",     f"{_RED}{brief['error']}{_R}")

    conf = brief.get("confidence", "")
    conf_col = _GREEN if conf == "high" else (_YELLOW if conf == "medium" else _DIM)
    _label("Confidence:",    f"{conf_col}{conf}{_R}")

    _label("Urgency (std):",    f"{_BOLD}{brief.get('urgency', 'unclear')}{_R}")
    _label("Urgency (raw):",    brief.get("urgency_raw", ""))
    _label("Materiality (std):", f"{_BOLD}{brief.get('materiality', 'unclear')}{_R}")
    _label("Materiality (raw):", brief.get("materiality_raw", ""))

    dl = brief.get("deadline")
    _label("Deadline:",      str(dl) if dl else f"{_DIM}none detected{_R}")

    rev_req = brief.get("review_required", False)
    _label("Review required:", f"{_RED}Yes{_R}" if rev_req else f"{_GREEN}No{_R}")
    if rev_req and brief.get("review_reason"):
        _label("Review reason:",  brief["review_reason"])

    affected = brief.get("affected_entities", [])
    _label("Affected:",      ", ".join(str(e) for e in affected) if affected else f"{_DIM}none{_R}")

    summary = brief.get("executive_summary", "")
    if summary:
        print(f"\n  {_BOLD}Executive Summary:{_R}")
        for line in _wrap(summary, WIDTH - 4):
            print(f"    {line}")

    action = brief.get("business_action_required", "")
    if action:
        print(f"\n  {_BOLD}Required Business Action:{_R}")
        for line in _wrap(action, WIDTH - 4):
            print(f"    {_YELLOW}{line}{_R}")

    sf = brief.get("semantic_findings", {})
    if sf:
        _hr("·")
        print(f"  {_BOLD}Semantic Findings:{_R}")
        def _bsem(lbl: str, val: object) -> None:
            if isinstance(val, bool):
                v_str = f"{_GREEN}Yes{_R}" if val else f"{_DIM}No{_R}"
            else:
                c = _RED if val in ("high", "critical") else (
                    _YELLOW if val in ("medium", "material") else _DIM
                )
                v_str = f"{c}{val}{_R}"
            print(f"   {_DIM}{lbl:<26}{_R}  {v_str}")
        _bsem("New obligation:",        sf.get("new_obligation",       False))
        _bsem("Deadline detected:",     sf.get("deadline_detected",    False))
        _bsem("Reporting required:",    sf.get("reporting_required",   False))
        _bsem("Licensing impact:",      sf.get("licensing_impact",     False))
        _bsem("Enforcement exposure:",  sf.get("enforcement_exposure", False))
        _bsem("Operational impact:",    sf.get("operational_impact",   "none"))
        _bsem("Materiality (raw):",     sf.get("materiality",          "informational"))

    _hr()
    print(f"\n  {_GREEN}✓  generate_ai_brief() returned a valid brief.{_R}\n")
    sys.exit(0)


# ── watch command ─────────────────────────────────────────────────────────────

def _cmd_watch(extra_args: list[str]) -> None:
    """Parse optional --interval N and start the watch loop."""
    from app.scheduler import run_watch_loop

    interval: int | None = None
    i = 0
    while i < len(extra_args):
        if extra_args[i] == "--interval":
            if i + 1 >= len(extra_args):
                print(
                    "Error: --interval requires a positive integer value (minutes).",
                    file=sys.stderr,
                )
                sys.exit(2)
            raw = extra_args[i + 1]
            try:
                interval = int(raw)
                if interval < 1:
                    raise ValueError("must be >= 1")
            except ValueError:
                print(
                    f"Error: --interval must be a positive integer, got {raw!r}.",
                    file=sys.stderr,
                )
                sys.exit(2)
            i += 2
        else:
            print(
                f"Error: unknown option {extra_args[i]!r} for 'watch'.\n"
                f"  Usage: python run.py watch [--interval <minutes>]",
                file=sys.stderr,
            )
            sys.exit(2)

    run_watch_loop(interval)


def _cmd_discover_source(
    url: str,
    json_export: bool,
    jurisdiction: str,
    category: str,
    *,
    js: bool = False,
    network: bool = False,
    sitemap: bool = True,
    feeds: bool = True,
    documents: bool = True,
    max_links: int = 50,
    max_depth: int = 1,
) -> None:
    """Run structured no-save source discovery on one public URL."""
    import json as _json
    from app.source_discovery import discover_source

    print(f"\n  {_BOLD}StatuteProof — Source Discovery Engine{_R}", file=sys.stderr)
    print(f"  {_DIM}Discovering endpoints without evidence writes: {url}{_R}\n", file=sys.stderr)

    report = discover_source(
        url,
        use_js=js,
        include_network=network,
        include_sitemap=sitemap,
        include_feeds=feeds,
        include_documents=documents,
        max_links=max_links,
        max_depth=max_depth,
    )
    if jurisdiction:
        report["jurisdiction"] = jurisdiction
    if category:
        report["category"] = category

    if json_export:
        print(_json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
        return

    _hr("═")
    _label("Official domain:", report.get("official_domain", ""))
    _label("Final URL:", report.get("final_url", ""))
    _label("Sitemap URLs:", str(len(report.get("sitemap_urls", []))))
    _label("Feeds:", str(len(report.get("feed_urls", []))))
    _label("Documents:", str(len(report.get("document_links", []))))
    _label("Public JSON candidates:", str(len(report.get("public_json_candidates", []))))
    _label("Same-domain candidates:", str(len(report.get("same_domain_candidate_urls", []))))
    _label("Recommended paths:", str(len(report.get("recommended_activation_paths", []))))

    paths = report.get("recommended_activation_paths", [])
    if paths:
        _hr("·")
        print(f"  {_BOLD}Top Activation Path Candidates{_R}")
        for item in paths[:8]:
            print(
                f"  {_DIM}{int(item.get('confidence') or 0):>3}/100{_R}  "
                f"{item.get('adapter_family') or '-':<24}  "
                f"{item.get('candidate_url')}"
            )

    warnings = report.get("warnings", [])
    if warnings:
        _hr("·")
        print(f"  {_YELLOW}Warnings{_R}")
        for warning in warnings[:8]:
            print(f"  {_DIM}  • {warning}{_R}")

    _hr("═")
    print(f"  {_DIM}No evidence was saved. Run no-save Source Lab before any proof/baseline work.{_R}\n")


def _cmd_source_lab(
    url: str,
    *,
    source_id: str = "source-lab",
    name: str = "Source Lab URL",
    jurisdiction: str = "LAB",
    category: str = "custom",
    save: bool = False,
    json_export: bool = False,
    baseline_runs: int = 2,
    providers_report: bool = False,
    content_selector: str | None = None,
    wait_for_selector: str | None = None,
    js: bool = False,
    pdf: bool = False,
    adapter_family: str | None = None,
    adapter_name: str | None = None,
    adapter_config: dict | None = None,
) -> None:
    """Run one safe source-intake lab check. Never runs all sources."""
    import json
    from app.source_intake import run_source_intake, load_sources_json, build_source_lab_contract

    source = {
        "source_id": source_id,
        "name": name,
        "url": url,
        "jurisdiction": jurisdiction,
        "category": category,
        "enabled": False,
        "baseline_runs_required": baseline_runs,
    }
    if content_selector:
        source["content_selector"] = content_selector
    if wait_for_selector:
        source["wait_for_selector"] = wait_for_selector
    if js:
        source["fetch_method"] = "playwright"
    if pdf:
        source["source_type"] = "pdf"
    if adapter_family:
        source["adapter_family"] = adapter_family
    if adapter_name:
        source["adapter_name"] = adapter_name
    if adapter_config:
        source["adapter_config"] = adapter_config

    result = run_source_intake(source, all_sources=load_sources_json(), write_evidence=save)
    contract = build_source_lab_contract(result)
    payload = {
        "source_id": result.get("source_id"),
        "source_url": url,
        "canonical_url": url,
        "source_type": source.get("source_type") or "custom_public_source",
        "provider_used": result.get("provider_used"),
        "provider_candidates": result.get("provider_candidates", []),
        "adapter_used": result.get("adapter_used", False),
        "adapter_family": result.get("adapter_family", ""),
        "adapter_name": result.get("adapter_name", ""),
        "adapter_version": result.get("adapter_version", ""),
        "extraction_strategy": result.get("extraction_strategy", ""),
        "adapter_metadata": result.get("adapter_metadata", {}),
        "adapter_warnings": result.get("adapter_warnings", []),
        "dom_investigation": result.get("dom_investigation", {}),
        "normalized_length": result.get("chars_normalized"),
        "normalized_hash": result.get("normalized_hash"),
        "normalized_preview": result.get("normalized_preview"),
        "quality_score": result.get("quality_score"),
        "quality_label": (result.get("quality_breakdown") or {}).get("quality_label") or result.get("quality"),
        "evidence_level": result.get("evidence_level"),
        "certification_status": result.get("certification_status"),
        "readiness_status": result.get("status"),
        "activation_readiness": contract.get("activation_readiness"),
        "can_save_for_validation": contract.get("can_save_for_validation"),
        "can_save_evidence": result.get("can_save_evidence"),
        "can_activate_monitoring": contract.get("can_activate_monitoring"),
        "baseline_runs_completed": contract.get("baseline_runs_completed"),
        "baseline_runs_required": contract.get("baseline_runs_required"),
        "failure_reason": result.get("failure_reason"),
        "failure_code": result.get("failure_code"),
        "remediation_hint": result.get("remediation_hint"),
        "official_status": result.get("official_status"),
        "access_status": result.get("access_status"),
        "meaningful_content": result.get("meaningful_content"),
        "shallow_content": result.get("shallow_content"),
        "duplicate_hash": result.get("duplicate_hash"),
        "noise_risk": result.get("noise_risk"),
        "source_health_risk": result.get("source_health_risk"),
        "proof_path": result.get("proof_path"),
        "evidence_paths": result.get("evidence_paths"),
        "warnings": result.get("errors", []),
        "nav_shell_detected": result.get("nav_shell_detected"),
        "hash_collision": result.get("hash_collision"),
        "certification": result.get("certification"),
        "quality_breakdown": result.get("quality_breakdown"),
    }
    if providers_report:
        payload["provider_report"] = {
            "provider_used": result.get("provider_used"),
            "extraction_method": result.get("extraction_method"),
            "adapter_used": result.get("adapter_used"),
            "adapter_family": result.get("adapter_family"),
            "adapter_name": result.get("adapter_name"),
            "adapter_version": result.get("adapter_version"),
            "extraction_strategy": result.get("extraction_strategy"),
            "notes": result.get("notes"),
        }
    if json_export:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return

    print(f"\n{_BOLD}Source Lab{_R}")
    print(f"  URL: {url}")
    print(f"  Readiness: {payload['readiness_status']}")
    print(f"  Certification: {payload['certification_status']}")
    print(f"  Evidence level: {payload['evidence_level']}")
    print(f"  Quality: {payload['quality_score']}/100 ({payload['quality_label']})")
    print(f"  Provider: {payload['provider_used'] or '-'}")
    if payload.get("adapter_used"):
        print(f"  Adapter: {payload.get('adapter_name') or payload.get('adapter_family')} ({payload.get('adapter_version')})")
    if payload.get("failure_code"):
        print(f"  Failure code: {payload['failure_code']}")
    print(f"  Noise/source health: {payload.get('noise_risk') or '-'} / {payload.get('source_health_risk') or '-'}")
    print(f"  Normalized chars: {payload['normalized_length']}")
    print(f"  Normalized hash: {payload['normalized_hash'] or '-'}")
    if payload["failure_reason"]:
        print(f"  Failure: {payload['failure_reason']}")
    if payload["remediation_hint"]:
        print(f"  Remediation: {payload['remediation_hint']}")


def _cmd_investigate_source(
    url: str,
    *,
    json_export: bool = False,
    js: bool = False,
    content_selector: str | None = None,
    wait_for_selector: str | None = None,
) -> None:
    """Inspect one public URL's rendered/static DOM and recommend extraction strategy."""
    import json
    from app.scraper import fetch_page_with_config
    from app.dom_investigator import investigate_html
    from app.source_tester import validate_public_url

    safe, reason = validate_public_url(url)
    if not safe:
        payload = {
            "final_url": url,
            "detected_page_type": "blocked",
            "failure_reason": reason,
            "remediation_hint": "Use a public http(s) URL without credentials, private network, login, CAPTCHA, or paywall access.",
            "can_no_save_test": False,
            "can_save_evidence": False,
        }
    else:
        try:
            html = fetch_page_with_config(
                url,
                wait_for_selector=wait_for_selector,
                content_selector=content_selector,
                force_playwright=js,
            )
            payload = investigate_html(html, url=url)
            payload["raw_html_length"] = len(html or "")
            payload["fetch_method"] = "playwright" if js else "default"
        except Exception as exc:
            payload = {
                "final_url": url,
                "detected_page_type": "fetch_failed",
                "failure_reason": f"Fetch failed: {exc}",
                "remediation_hint": "Retry with --js or inspect the official page manually before adding it.",
                "can_no_save_test": False,
                "can_save_evidence": False,
                "warnings": [type(exc).__name__],
            }

    if json_export:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return

    print(f"\n{_BOLD}Source DOM Investigation{_R}")
    print(f"  URL: {url}")
    print(f"  Page type: {payload.get('detected_page_type')}")
    print(f"  Adapter: {payload.get('recommended_adapter_name') or payload.get('recommended_adapter_family') or '-'}")
    print(f"  Wait selector: {payload.get('wait_selector') or '-'}")
    print(f"  Content selector: {payload.get('content_selector') or '-'}")
    print(f"  Item selector: {payload.get('item_selector') or '-'}")
    print(f"  Selector confidence: {payload.get('selector_confidence', 0)}/100")
    print(f"  Nav/noise/health risk: {payload.get('nav_shell_risk')} / {payload.get('noise_risk')} / {payload.get('source_health_risk')}")
    if payload.get("failure_reason"):
        print(f"  Failure: {payload.get('failure_reason')}")
    if payload.get("remediation_hint"):
        print(f"  Remediation: {payload.get('remediation_hint')}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    if not args:
        print("Usage:", file=sys.stderr)
        print("  python run.py <url>                     single URL", file=sys.stderr)
        print("  python run.py url <url>                 single URL (explicit)", file=sys.stderr)
        print("  python run.py all                       monitor all sources once", file=sys.stderr)
        print("  python run.py watch                     watch mode (default 60 min)", file=sys.stderr)
        print("  python run.py watch --interval <min>    watch mode (custom interval)", file=sys.stderr)
        print("  python run.py sources                   list sources", file=sys.stderr)
        print("  python run.py health                    source health diagnostic", file=sys.stderr)
        print("  python run.py demo                      client demo (no DB writes)", file=sys.stderr)
        print("  python run.py demo --send-telegram      demo + Telegram demo alert", file=sys.stderr)
        print("  python run.py test-source <url>              test a URL without saving", file=sys.stderr)
        print("  python run.py test-source <url> --deep      6-layer deep source discovery", file=sys.stderr)
        print("  python run.py source-lab <url> --no-save --json  one-source parser/evidence lab", file=sys.stderr)
        print("  python run.py source-lab <url> --save --json     one-source lab with evidence write", file=sys.stderr)
        print("  python run.py source-lab <url> --js --content-selector main --wait-for-selector main", file=sys.stderr)
        print("  python run.py source-lab <url> --adapter-family listing --adapter-config-json '{\"container_selector\":\"main\"}'", file=sys.stderr)
        print("  python run.py source-lab <url> --source-id AE-example --save --json", file=sys.stderr)
        print("  python run.py investigate-source <url> --js --json  inspect DOM and suggest selectors", file=sys.stderr)
        print("  python run.py discover-source <url> --json --sitemap --feeds --documents  discover candidate endpoints without saving", file=sys.stderr)
        print("  python run.py source-discovery-lab <url> --js --network --json  discover endpoints + DOM remediation hints", file=sys.stderr)
        print("  python run.py mass-source-activate --queue product/regradar/config/mass_source_activation_queue.json --no-save-only --limit 10 --regulator SCA", file=sys.stderr)
        print("  python run.py add-source                     interactively add a source", file=sys.stderr)
        print("  python run.py coverage                       coverage dashboard (uses latest audit JSON)", file=sys.stderr)
        print("  python run.py coverage --json                export reports/coverage_YYYY-MM-DD.json", file=sys.stderr)
        print("  python run.py coverage --html                export reports/coverage_YYYY-MM-DD.html", file=sys.stderr)
        print("  python run.py coverage --jurisdiction AZ     filter dashboard to one jurisdiction", file=sys.stderr)
        print("  python run.py coverage --category central_bank  filter to one category", file=sys.stderr)
        print("  python run.py test-mapped                    batch test mapped sources (limit 10)", file=sys.stderr)
        print("  python run.py test-mapped --limit <n>        batch test N mapped sources", file=sys.stderr)
        print("  python run.py test-mapped --limit <n> --deep deep 6-layer batch discovery", file=sys.stderr)
        print("  python run.py report                    export report (last 7 days)", file=sys.stderr)
        print("  python run.py report --last <days>      export report for N days", file=sys.stderr)
        print("  python run.py ai-test                   live AI semantic smoke test", file=sys.stderr)
        print("  python run.py telegram-test             send test Telegram alert (reads .env or telegram_settings.json)", file=sys.stderr)
        print("  python run.py env-check                 print resolved .env path and key config values", file=sys.stderr)
        print("  python run.py adapter-research <query>  research one source to plan a custom adapter", file=sys.stderr)
        print("  python run.py source-audit              audit all sources for extraction quality and adapter needs", file=sys.stderr)
        print("  python run.py source-audit --json       same + export reports/source_audit_YYYY-MM-DD.json", file=sys.stderr)
        print("  python run.py source-readiness                          UAE source readiness check (default market)", file=sys.stderr)
        print("  python run.py source-readiness --market AE              source readiness for a specific market", file=sys.stderr)
        print("  python run.py source-readiness --market AE --html       same + export HTML report", file=sys.stderr)
        print("  python run.py source-readiness --market AE --record-run run diagnostics and append source history", file=sys.stderr)
        print("  python run.py source-history --market AE                inspect latest source run history", file=sys.stderr)
        print("  python run.py source-diff --market AE --latest-changed  inspect latest changed diff/proof", file=sys.stderr)
        print("  python run.py alert-draft --market AE --latest-changed  build DRAFT alert from latest changed run", file=sys.stderr)
        print("  python run.py alert-draft --market AE --latest-changed --profile uae_vasp_demo", file=sys.stderr)
        print("  python run.py relevance-test --market AE --profile uae_vasp_demo", file=sys.stderr)
        print("  python run.py alert-review list --market AE             list local alert drafts", file=sys.stderr)
        print("  python run.py weekly-brief --client uae_vasp_demo --market AE --days 7", file=sys.stderr)
        print("  python run.py adapter-queue             show sources that need custom adapters, sorted by priority", file=sys.stderr)
        print("  python run.py contact-queue             list queued contact requests (last 20)", file=sys.stderr)
        print("  python run.py contact-queue --limit <n> list last N queued contact requests", file=sys.stderr)
        print("  python run.py contact-queue --latest    show the most recent contact request in full", file=sys.stderr)
        print("  python run.py contact-queue --json      dump all queued requests as JSON array", file=sys.stderr)
        print("  python run.py coverage-plan             coverage improvement plan (uses latest JSONs)", file=sys.stderr)
        print("  python run.py coverage-plan --json      export reports/coverage_plan_YYYY-MM-DD.json", file=sys.stderr)
        print("  python run.py coverage-plan --html      export reports/coverage_plan_YYYY-MM-DD.html", file=sys.stderr)
        print("  python run.py coverage-plan --jurisdiction KZ  filter plan to one jurisdiction", file=sys.stderr)
        print("  python run.py document-test <url>       test PDF/document extraction for a URL", file=sys.stderr)
        print("  python run.py api                       start settings API server on 127.0.0.1:5001", file=sys.stderr)
        print("  python run.py api --port <n>            start API server on custom port", file=sys.stderr)
        print("  python run.py api --host 0.0.0.0        bind to all interfaces (production behind nginx)", file=sys.stderr)
        print("  python run.py discover-source <url>                      discover candidate endpoints without saving evidence", file=sys.stderr)
        print("  python run.py discover-source <url> --json               print structured source discovery JSON", file=sys.stderr)
        print("  python run.py discover-source <url> --jurisdiction CODE  tag with jurisdiction code (e.g. AE, SG, KZ)", file=sys.stderr)
        print("  python run.py discover-source <url> --category NAME      tag with category (e.g. tax, aml, cyber)", file=sys.stderr)
        print("  python run.py mass-source-activate --no-save-only --limit 10  safe queue batch; no evidence save by default", file=sys.stderr)
        sys.exit(2)

    cmd = args[0]

    if cmd == "coverage":
        extra     = args[1:]
        json_exp  = "--json"  in extra
        html_exp  = "--html"  in extra
        jur_filter: str | None = None
        cat_filter: str | None = None
        i_ = 0
        while i_ < len(extra):
            tok = extra[i_]
            if tok in ("--json", "--html"):
                i_ += 1
            elif tok == "--jurisdiction":
                if i_ + 1 >= len(extra):
                    print("Error: --jurisdiction requires a value.", file=sys.stderr)
                    sys.exit(2)
                jur_filter = extra[i_ + 1]
                i_ += 2
            elif tok == "--category":
                if i_ + 1 >= len(extra):
                    print("Error: --category requires a value.", file=sys.stderr)
                    sys.exit(2)
                cat_filter = extra[i_ + 1]
                i_ += 2
            else:
                print(
                    f"Error: unknown option {tok!r} for 'coverage'.\n"
                    "  Usage: python run.py coverage [--json] [--html] "
                    "[--jurisdiction CODE] [--category NAME]",
                    file=sys.stderr,
                )
                sys.exit(2)
        _cmd_coverage(
            json_export=json_exp,
            html_export=html_exp,
            jurisdiction=jur_filter,
            category=cat_filter,
        )

    elif cmd == "coverage-plan":
        extra    = args[1:]
        json_exp = "--json" in extra
        html_exp = "--html" in extra
        jur_filter_p: str | None = None
        cat_filter_p: str | None = None
        i_ = 0
        while i_ < len(extra):
            tok = extra[i_]
            if tok in ("--json", "--html"):
                i_ += 1
            elif tok == "--jurisdiction":
                if i_ + 1 >= len(extra):
                    print("Error: --jurisdiction requires a value.", file=sys.stderr)
                    sys.exit(2)
                jur_filter_p = extra[i_ + 1]
                i_ += 2
            elif tok == "--category":
                if i_ + 1 >= len(extra):
                    print("Error: --category requires a value.", file=sys.stderr)
                    sys.exit(2)
                cat_filter_p = extra[i_ + 1]
                i_ += 2
            else:
                print(
                    f"Error: unknown option {tok!r} for 'coverage-plan'.\n"
                    "  Usage: python run.py coverage-plan [--json] [--html] "
                    "[--jurisdiction CODE] [--category NAME]",
                    file=sys.stderr,
                )
                sys.exit(2)
        _cmd_coverage_plan(
            json_export=json_exp,
            html_export=html_exp,
            jurisdiction=jur_filter_p,
            category=cat_filter_p,
        )

    elif cmd == "sources":
        _cmd_sources()

    elif cmd == "all":
        _cmd_all()

    elif cmd == "health":
        _cmd_health()

    elif cmd == "demo":
        unknown = [a for a in args[1:] if a != "--send-telegram"]
        if unknown:
            print(
                f"Error: unknown option {unknown[0]!r} for 'demo'.\n"
                f"  Usage: python run.py demo [--send-telegram]",
                file=sys.stderr,
            )
            sys.exit(2)
        _cmd_demo(send_alert="--send-telegram" in args[1:])

    elif cmd == "test-source":
        extra   = args[1:]
        url_arg: str | None = None
        deep    = False
        for tok in extra:
            if tok == "--deep":
                deep = True
            elif url_arg is None:
                url_arg = tok
            else:
                print(
                    f"Error: unexpected argument {tok!r} for 'test-source'.\n"
                    "  Usage: python run.py test-source <url> [--deep]",
                    file=sys.stderr,
                )
                sys.exit(2)
        if url_arg is None:
            print(
                "Error: 'test-source' requires a URL argument.\n"
                "  Usage: python run.py test-source <url> [--deep]",
                file=sys.stderr,
            )
            sys.exit(2)
        _cmd_test_source(url_arg.strip(), deep=deep)

    elif cmd == "investigate-source":
        extra = args[1:]
        url_arg: str | None = None
        json_export = False
        js = False
        content_selector = None
        wait_for_selector = None
        i_ = 0
        while i_ < len(extra):
            tok = extra[i_]
            if tok == "--json":
                json_export = True
                i_ += 1
            elif tok == "--js":
                js = True
                i_ += 1
            elif tok == "--content-selector":
                if i_ + 1 >= len(extra):
                    print("Error: --content-selector requires a CSS selector.", file=sys.stderr)
                    sys.exit(2)
                content_selector = extra[i_ + 1]
                i_ += 2
            elif tok == "--wait-for-selector":
                if i_ + 1 >= len(extra):
                    print("Error: --wait-for-selector requires a CSS selector.", file=sys.stderr)
                    sys.exit(2)
                wait_for_selector = extra[i_ + 1]
                i_ += 2
            elif url_arg is None:
                url_arg = tok
                i_ += 1
            else:
                print(f"Error: unexpected argument {tok!r} for 'investigate-source'.", file=sys.stderr)
                sys.exit(2)
        if not url_arg:
            print("Error: 'investigate-source' requires a URL.", file=sys.stderr)
            sys.exit(2)
        _cmd_investigate_source(
            url_arg.strip(),
            json_export=json_export,
            js=js,
            content_selector=content_selector,
            wait_for_selector=wait_for_selector,
        )

    elif cmd == "source-lab":
        extra = args[1:]
        url_arg: str | None = None
        save = False
        json_export = False
        providers_report = False
        js = False
        pdf = False
        baseline_runs = 2
        source_id = "source-lab"
        source_name = "Source Lab URL"
        jurisdiction = "LAB"
        category = "custom"
        content_selector = None
        wait_for_selector = None
        adapter_family = None
        adapter_name = None
        adapter_config = None
        i_ = 0
        while i_ < len(extra):
            tok = extra[i_]
            if tok == "--json":
                json_export = True
                i_ += 1
            elif tok == "--save":
                save = True
                i_ += 1
            elif tok == "--no-save":
                save = False
                i_ += 1
            elif tok == "--providers-report":
                providers_report = True
                i_ += 1
            elif tok == "--js":
                js = True
                i_ += 1
            elif tok == "--pdf":
                pdf = True
                i_ += 1
            elif tok == "--certify":
                i_ += 1
            elif tok == "--baseline-runs":
                if i_ + 1 >= len(extra):
                    print("Error: --baseline-runs requires an integer.", file=sys.stderr)
                    sys.exit(2)
                baseline_runs = int(extra[i_ + 1])
                i_ += 2
            elif tok == "--source-id":
                if i_ + 1 >= len(extra):
                    print("Error: --source-id requires a value.", file=sys.stderr)
                    sys.exit(2)
                source_id = extra[i_ + 1].strip() or "source-lab"
                i_ += 2
            elif tok == "--name":
                if i_ + 1 >= len(extra):
                    print("Error: --name requires a value.", file=sys.stderr)
                    sys.exit(2)
                source_name = extra[i_ + 1].strip() or "Source Lab URL"
                i_ += 2
            elif tok == "--jurisdiction":
                if i_ + 1 >= len(extra):
                    print("Error: --jurisdiction requires a value.", file=sys.stderr)
                    sys.exit(2)
                jurisdiction = extra[i_ + 1].strip() or "LAB"
                i_ += 2
            elif tok == "--category":
                if i_ + 1 >= len(extra):
                    print("Error: --category requires a value.", file=sys.stderr)
                    sys.exit(2)
                category = extra[i_ + 1].strip() or "custom"
                i_ += 2
            elif tok == "--content-selector":
                if i_ + 1 >= len(extra):
                    print("Error: --content-selector requires a CSS selector.", file=sys.stderr)
                    sys.exit(2)
                content_selector = extra[i_ + 1]
                i_ += 2
            elif tok == "--wait-for-selector":
                if i_ + 1 >= len(extra):
                    print("Error: --wait-for-selector requires a CSS selector.", file=sys.stderr)
                    sys.exit(2)
                wait_for_selector = extra[i_ + 1]
                i_ += 2
            elif tok == "--adapter-family":
                if i_ + 1 >= len(extra):
                    print("Error: --adapter-family requires a value.", file=sys.stderr)
                    sys.exit(2)
                adapter_family = extra[i_ + 1].strip() or None
                i_ += 2
            elif tok == "--adapter-name":
                if i_ + 1 >= len(extra):
                    print("Error: --adapter-name requires a value.", file=sys.stderr)
                    sys.exit(2)
                adapter_name = extra[i_ + 1].strip() or None
                i_ += 2
            elif tok == "--adapter-config-json":
                if i_ + 1 >= len(extra):
                    print("Error: --adapter-config-json requires a JSON object.", file=sys.stderr)
                    sys.exit(2)
                try:
                    import json as _json
                    parsed_config = _json.loads(extra[i_ + 1])
                except Exception as exc:
                    print(f"Error: --adapter-config-json is invalid JSON: {exc}", file=sys.stderr)
                    sys.exit(2)
                if not isinstance(parsed_config, dict):
                    print("Error: --adapter-config-json must decode to an object.", file=sys.stderr)
                    sys.exit(2)
                adapter_config = parsed_config
                i_ += 2
            elif url_arg is None:
                url_arg = tok
                i_ += 1
            else:
                print(f"Error: unexpected argument {tok!r} for 'source-lab'.", file=sys.stderr)
                sys.exit(2)
        if not url_arg:
            print("Error: 'source-lab' requires a URL.", file=sys.stderr)
            sys.exit(2)
        _cmd_source_lab(
            url_arg.strip(),
            source_id=source_id,
            name=source_name,
            jurisdiction=jurisdiction,
            category=category,
            save=save,
            json_export=json_export,
            baseline_runs=baseline_runs,
            providers_report=providers_report,
            content_selector=content_selector,
            wait_for_selector=wait_for_selector,
            js=js,
            pdf=pdf,
            adapter_family=adapter_family,
            adapter_name=adapter_name,
            adapter_config=adapter_config,
        )

    elif cmd == "test-mapped":
        raw_limit = 10
        deep      = False
        extra     = args[1:]
        i_        = 0
        while i_ < len(extra):
            tok = extra[i_]
            if tok == "--limit":
                if i_ + 1 >= len(extra):
                    print("Error: --limit requires a positive integer.", file=sys.stderr)
                    sys.exit(2)
                try:
                    raw_limit = int(extra[i_ + 1])
                    if raw_limit < 1:
                        raise ValueError
                except ValueError:
                    print(
                        f"Error: --limit must be a positive integer, got {extra[i_+1]!r}.",
                        file=sys.stderr,
                    )
                    sys.exit(2)
                i_ += 2
            elif tok == "--deep":
                deep = True
                i_ += 1
            else:
                print(
                    f"Error: unknown option {tok!r} for 'test-mapped'.\n"
                    "  Usage: python run.py test-mapped [--limit <n>] [--deep]",
                    file=sys.stderr,
                )
                sys.exit(2)
        _cmd_test_mapped(raw_limit, deep=deep)

    elif cmd == "add-source":
        if len(args) > 1:
            print(
                "Error: 'add-source' takes no arguments (interactive mode).\n"
                "  Usage: python run.py add-source",
                file=sys.stderr,
            )
            sys.exit(2)
        _cmd_add_source()

    elif cmd == "report":
        # Parse optional --last N
        report_days = 7
        extra = args[1:]
        if extra:
            if extra[0] != "--last":
                print(
                    f"Error: unknown option {extra[0]!r} for 'report'.\n"
                    "  Usage: python run.py report [--last <days>]",
                    file=sys.stderr,
                )
                sys.exit(2)
            if len(extra) < 2:
                print(
                    "Error: --last requires a positive integer value (days).",
                    file=sys.stderr,
                )
                sys.exit(2)
            if len(extra) > 2:
                print(
                    "Error: 'report' accepts at most one option: --last <days>.",
                    file=sys.stderr,
                )
                sys.exit(2)
            raw_days = extra[1]
            try:
                report_days = int(raw_days)
                if report_days < 1:
                    raise ValueError("must be >= 1")
            except ValueError:
                print(
                    f"Error: --last must be a positive integer, got {raw_days!r}.",
                    file=sys.stderr,
                )
                sys.exit(2)
        _cmd_report(report_days)

    elif cmd == "ai-test":
        if len(args) > 1:
            print("Error: 'ai-test' takes no arguments.", file=sys.stderr)
            sys.exit(2)
        _cmd_ai_test()

    elif cmd == "ai-health":
        if len(args) > 1:
            print("Error: 'ai-health' takes no arguments.", file=sys.stderr)
            sys.exit(2)
        _cmd_ai_health()

    elif cmd == "ai-brief-test":
        if len(args) > 1:
            print("Error: 'ai-brief-test' takes no arguments.", file=sys.stderr)
            sys.exit(2)
        _cmd_ai_brief_test()

    elif cmd == "telegram-test":
        if len(args) > 1:
            print("Error: 'telegram-test' takes no arguments.", file=sys.stderr)
            sys.exit(2)
        _cmd_telegram_test()

    elif cmd == "telegram-updates":
        if len(args) > 1:
            print("Error: 'telegram-updates' takes no arguments.", file=sys.stderr)
            sys.exit(2)
        _cmd_telegram_updates()

    elif cmd == "telegram-listen":
        if len(args) > 1:
            print("Error: 'telegram-listen' takes no arguments.", file=sys.stderr)
            sys.exit(2)
        _cmd_telegram_listen()

    elif cmd == "telegram-clients":
        if len(args) > 1:
            print("Error: 'telegram-clients' takes no arguments.", file=sys.stderr)
            sys.exit(2)
        _cmd_telegram_clients()

    elif cmd == "telegram-client-set":
        if len(args) < 3:
            print(
                "Error: 'telegram-client-set' requires client_id and chat_id.\n"
                "  Usage: python run.py telegram-client-set <client_id> <chat_id> [name]",
                file=sys.stderr,
            )
            sys.exit(2)
        _cmd_telegram_client_set(
            client_id=args[1].strip(),
            chat_id=args[2].strip(),
            name=" ".join(args[3:]).strip() if len(args) > 3 else "",
        )

    elif cmd == "telegram-client-test":
        if len(args) != 2:
            print(
                "Error: 'telegram-client-test' requires exactly one argument.\n"
                "  Usage: python run.py telegram-client-test <client_id>",
                file=sys.stderr,
            )
            sys.exit(2)
        _cmd_telegram_client_test(args[1].strip())

    elif cmd == "telegram-client-disable":
        if len(args) != 2:
            print(
                "Error: 'telegram-client-disable' requires exactly one argument.\n"
                "  Usage: python run.py telegram-client-disable <client_id>",
                file=sys.stderr,
            )
            sys.exit(2)
        _cmd_telegram_client_disable(args[1].strip())

    elif cmd == "env-check":
        if len(args) > 1:
            print("Error: 'env-check' takes no arguments.", file=sys.stderr)
            sys.exit(2)
        _cmd_env_check()

    elif cmd == "adapter-research":
        if len(args) < 2:
            print(
                "Error: 'adapter-research' requires a source query.\n"
                "  Usage: python run.py adapter-research <name|url|category>",
                file=sys.stderr,
            )
            sys.exit(2)
        if len(args) > 2:
            print(
                "Error: 'adapter-research' takes exactly one argument (quote multi-word queries).\n"
                "  Usage: python run.py adapter-research 'central bank russia'",
                file=sys.stderr,
            )
            sys.exit(2)
        _cmd_adapter_research(args[1].strip())

    elif cmd == "source-audit":
        unknown = [a for a in args[1:] if a != "--json"]
        if unknown:
            print(
                f"Error: unknown option {unknown[0]!r} for 'source-audit'.\n"
                "  Usage: python run.py source-audit [--json]",
                file=sys.stderr,
            )
            sys.exit(2)
        _cmd_source_audit(json_export="--json" in args[1:])

    elif cmd == "source-readiness":
        market   = "AE"
        profile  = "fintech"
        html_exp = "--html" in args[1:]
        record_run = False
        i_       = 1
        while i_ < len(args):
            if args[i_] == "--market" and i_ + 1 < len(args):
                market = args[i_ + 1].upper()
                i_ += 2
            elif args[i_] == "--profile" and i_ + 1 < len(args):
                profile = args[i_ + 1].lower()
                i_ += 2
            elif args[i_] == "--html":
                i_ += 1
            elif args[i_] == "--record-run":
                record_run = True
                i_ += 1
            elif args[i_] == "--no-record-run":
                record_run = False
                i_ += 1
            else:
                print(
                    f"Error: unknown option {args[i_]!r} for 'source-readiness'.",
                    file=sys.stderr,
                )
                sys.exit(2)
        _cmd_source_readiness(market=market, profile=profile, html_export=html_exp, record_run=record_run)

    elif cmd == "source-history":
        market = "AE"
        source = None
        limit = 20
        i_ = 1
        while i_ < len(args):
            if args[i_] == "--market" and i_ + 1 < len(args):
                market = args[i_ + 1].upper()
                i_ += 2
            elif args[i_] == "--source" and i_ + 1 < len(args):
                source = args[i_ + 1]
                i_ += 2
            elif args[i_] == "--limit" and i_ + 1 < len(args):
                try:
                    limit = max(1, int(args[i_ + 1]))
                except ValueError:
                    print("Error: --limit must be an integer.", file=sys.stderr)
                    sys.exit(2)
                i_ += 2
            else:
                print(
                    f"Error: unknown option {args[i_]!r} for 'source-history'.",
                    file=sys.stderr,
                )
                sys.exit(2)
        _cmd_source_history(market=market, source=source, limit=limit)

    elif cmd == "backfill-artifacts":
        dry_run = "--dry-run" in args
        from app.source_runs import backfill_run_artifacts
        print(f"\nBackfilling proof.json + diff.json for CHANGED runs{' (dry-run)' if dry_run else ''}…\n")
        results = backfill_run_artifacts(dry_run=dry_run)
        backfilled = [r for r in results if r["action"] == "backfilled"]
        skipped = [r for r in results if r["action"] == "skipped"]
        no_snap = [r for r in results if r["action"] == "no_snapshot"]
        dry = [r for r in results if r["action"] == "dry_run"]
        for r in results:
            icon = {"backfilled": "✓", "skipped": "·", "no_snapshot": "✗", "dry_run": "?"}.get(r["action"], "?")
            print(f"  {icon} {r['action']:<12} {r['source_id']} / {r['run_id']}  — {r['detail']}")
        print(f"\nBackfilled: {len(backfilled)}  Skipped: {len(skipped)}  No-snapshot: {len(no_snap)}{f'  Dry-run: {len(dry)}' if dry_run else ''}")
        if backfilled and not dry_run:
            print("source_runs.jsonl updated with new artifact paths.")
        sys.exit(0)

    elif cmd == "alert-queue":
        # List pending alerts awaiting human review
        from app.source_runs import list_alert_queue
        status_filter = args[1] if len(args) > 1 else "PENDING_REVIEW"
        alerts = list_alert_queue(status=status_filter if status_filter != "all" else None)
        if not alerts:
            print(f"No alerts found (status={status_filter})")
        else:
            print(f"Alert queue ({len(alerts)} items, status={status_filter}):")
            for a in alerts:
                print(f"  {a['_filename']}: {a.get('source_id')} @ {a.get('run_at')} [{a.get('status')}]")

    elif cmd == "weekly-status":
        # Build a weekly summary of all monitoring activity
        from app.source_runs import build_weekly_status_summary
        days = int(args[1]) if len(args) > 1 else 7
        summary = build_weekly_status_summary(days=days)
        import json as _json
        print(_json.dumps(summary, indent=2))

    elif cmd == "source-diff":
        market = "AE"
        source = None
        latest_changed = False
        i_ = 1
        while i_ < len(args):
            if args[i_] == "--market" and i_ + 1 < len(args):
                market = args[i_ + 1].upper()
                i_ += 2
            elif args[i_] == "--source" and i_ + 1 < len(args):
                source = args[i_ + 1]
                i_ += 2
            elif args[i_] == "--latest-changed":
                latest_changed = True
                i_ += 1
            else:
                print(
                    f"Error: unknown option {args[i_]!r} for 'source-diff'.",
                    file=sys.stderr,
                )
                sys.exit(2)
        _cmd_source_diff(market=market, source=source, latest_changed=latest_changed)

    elif cmd == "alert-draft":
        market = "AE"
        source = None
        latest_changed = False
        profile = None
        i_ = 1
        while i_ < len(args):
            if args[i_] == "--market" and i_ + 1 < len(args):
                market = args[i_ + 1].upper()
                i_ += 2
            elif args[i_] == "--source" and i_ + 1 < len(args):
                source = args[i_ + 1]
                i_ += 2
            elif args[i_] == "--latest-changed":
                latest_changed = True
                i_ += 1
            elif args[i_] == "--profile" and i_ + 1 < len(args):
                profile = args[i_ + 1]
                i_ += 2
            else:
                print(
                    f"Error: unknown option {args[i_]!r} for 'alert-draft'.",
                    file=sys.stderr,
                )
                sys.exit(2)
        _cmd_alert_draft(market=market, source=source, latest_changed=latest_changed, profile_id=profile)

    elif cmd == "relevance-test":
        market = "AE"
        profile = None
        i_ = 1
        while i_ < len(args):
            if args[i_] == "--market" and i_ + 1 < len(args):
                market = args[i_ + 1].upper()
                i_ += 2
            elif args[i_] == "--profile" and i_ + 1 < len(args):
                profile = args[i_ + 1]
                i_ += 2
            else:
                print(
                    f"Error: unknown option {args[i_]!r} for 'relevance-test'.",
                    file=sys.stderr,
                )
                sys.exit(2)
        if not profile:
            print("Error: 'relevance-test' requires --profile <client_id>.", file=sys.stderr)
            sys.exit(2)
        _cmd_relevance_test(market=market, profile_id=profile)

    elif cmd == "alert-review":
        if len(args) < 2:
            print("Error: 'alert-review' requires a subcommand: list | show | approve | reject | needs-adapter.", file=sys.stderr)
            sys.exit(2)
        subcmd = args[1]
        extra = args[2:]
        if subcmd == "list":
            market = "AE"
            i_ = 0
            while i_ < len(extra):
                if extra[i_] == "--market" and i_ + 1 < len(extra):
                    market = extra[i_ + 1].upper()
                    i_ += 2
                else:
                    print(f"Error: unknown option {extra[i_]!r} for 'alert-review list'.", file=sys.stderr)
                    sys.exit(2)
            _cmd_alert_review_list(market=market)
        elif subcmd == "show":
            opts = _parse_alert_review_options(extra, require_alert=True, require_reviewer=False)
            _cmd_alert_review_show(alert_id=opts["alert_id"])
        elif subcmd == "approve":
            opts = _parse_alert_review_options(extra, require_alert=True, require_reviewer=True)
            if opts["weekly"] == opts["urgent"]:
                print("Error: approve requires exactly one of --weekly or --urgent.", file=sys.stderr)
                sys.exit(2)
            action = "approve_urgent" if opts["urgent"] else "approve_weekly"
            _cmd_alert_review_action(
                alert_id=opts["alert_id"],
                action=action,
                reviewer=opts["reviewer"],
                note=opts["note"],
                force=opts["force"],
            )
        elif subcmd in ("reject", "needs-adapter"):
            opts = _parse_alert_review_options(extra, require_alert=True, require_reviewer=True)
            action = "needs_adapter" if subcmd == "needs-adapter" else "reject"
            _cmd_alert_review_action(
                alert_id=opts["alert_id"],
                action=action,
                reviewer=opts["reviewer"],
                note=opts["note"],
                force=opts["force"],
            )
        else:
            print(f"Error: unknown alert-review subcommand {subcmd!r}.", file=sys.stderr)
            sys.exit(2)

    elif cmd == "weekly-brief":
        client = None
        market = "AE"
        days = 7
        date_from = None
        date_to = None
        formats = {"md", "html"}
        demo_fixture = False
        i_ = 1
        while i_ < len(args):
            tok = args[i_]
            if tok == "--client" and i_ + 1 < len(args):
                client = args[i_ + 1]
                i_ += 2
            elif tok == "--market" and i_ + 1 < len(args):
                market = args[i_ + 1].upper()
                i_ += 2
            elif tok == "--days" and i_ + 1 < len(args):
                try:
                    days = max(1, int(args[i_ + 1]))
                except ValueError:
                    print("Error: --days must be an integer.", file=sys.stderr)
                    sys.exit(2)
                i_ += 2
            elif tok == "--from" and i_ + 1 < len(args):
                date_from = args[i_ + 1]
                i_ += 2
            elif tok == "--to" and i_ + 1 < len(args):
                date_to = args[i_ + 1]
                i_ += 2
            elif tok == "--format" and i_ + 1 < len(args):
                fmt = args[i_ + 1].lower()
                if fmt not in {"md", "html", "both"}:
                    print("Error: --format must be md, html, or both.", file=sys.stderr)
                    sys.exit(2)
                formats = {"md", "html"} if fmt == "both" else {fmt}
                i_ += 2
            elif tok == "--demo-fixture":
                demo_fixture = True
                i_ += 1
            else:
                print(f"Error: unknown option {tok!r} for 'weekly-brief'.", file=sys.stderr)
                sys.exit(2)
        if not client:
            print("Error: 'weekly-brief' requires --client <client_id>.", file=sys.stderr)
            sys.exit(2)
        _cmd_weekly_brief(
            client_id=client,
            market=market,
            days=days,
            date_from=date_from,
            date_to=date_to,
            formats=formats,
            demo_fixture=demo_fixture,
        )

    elif cmd == "adapter-queue":
        if len(args) > 1:
            print("Error: 'adapter-queue' takes no arguments.", file=sys.stderr)
            sys.exit(2)
        _cmd_adapter_queue()

    elif cmd == "contact-queue":
        _cq_limit   = 20
        _cq_latest  = False
        _cq_json    = False
        _cq_extra   = args[1:]
        _i = 0
        while _i < len(_cq_extra):
            tok = _cq_extra[_i]
            if tok == "--limit":
                if _i + 1 >= len(_cq_extra):
                    print("Error: --limit requires an integer.", file=sys.stderr)
                    sys.exit(2)
                try:
                    _cq_limit = int(_cq_extra[_i + 1])
                except ValueError:
                    print(f"Error: --limit value must be an integer, got {_cq_extra[_i+1]!r}.", file=sys.stderr)
                    sys.exit(2)
                _i += 2
            elif tok == "--latest":
                _cq_latest = True
                _i += 1
            elif tok == "--json":
                _cq_json = True
                _i += 1
            else:
                print(f"Error: unknown argument {tok!r} for 'contact-queue'.", file=sys.stderr)
                sys.exit(2)
        _cmd_contact_queue(limit=_cq_limit, latest=_cq_latest, json_export=_cq_json)

    elif cmd == "document-test":
        if len(args) < 2:
            print(
                "Error: 'document-test' requires a URL argument.\n"
                "  Usage: python run.py document-test <url>",
                file=sys.stderr,
            )
            sys.exit(2)
        if len(args) > 2:
            print(
                f"Error: unexpected argument {args[2]!r} for 'document-test'.\n"
                "  Usage: python run.py document-test <url>",
                file=sys.stderr,
            )
            sys.exit(2)
        _cmd_document_test(args[1].strip())

    elif cmd == "api":
        api_port = 5001
        api_host = "127.0.0.1"
        extra = args[1:]
        i_ = 0
        while i_ < len(extra):
            tok = extra[i_]
            if tok == "--port":
                if i_ + 1 >= len(extra):
                    print("Error: --port requires an integer.", file=sys.stderr)
                    sys.exit(2)
                try:
                    api_port = int(extra[i_ + 1])
                except ValueError:
                    print(f"Error: --port must be an integer, got {extra[i_+1]!r}.", file=sys.stderr)
                    sys.exit(2)
                i_ += 2
            elif tok == "--host":
                if i_ + 1 >= len(extra):
                    print("Error: --host requires a value.", file=sys.stderr)
                    sys.exit(2)
                api_host = extra[i_ + 1]
                i_ += 2
            else:
                print(f"Error: unknown option {tok!r} for 'api'.", file=sys.stderr)
                sys.exit(2)
        _cmd_api(port=api_port, host=api_host)

    elif cmd == "watch":
        _cmd_watch(args[1:])

    elif cmd == "url":
        if len(args) < 2:
            print("Error: 'url' command requires a URL argument.", file=sys.stderr)
            sys.exit(2)
        _run_single_url(args[1].strip())

    elif cmd == "mass-source-activate":
        import json as _json
        from app.mass_source_activation_runner import DEFAULT_QUEUE_PATH, run_mass_source_activation_batch

        extra = args[1:]
        queue_path = DEFAULT_QUEUE_PATH
        regulator = None
        source_id = None
        status = None
        limit = None
        mode = "no-save-only"
        repeat_baseline = 0
        json_export = False
        i_ = 0
        while i_ < len(extra):
            tok = extra[i_]
            if tok == "--json":
                json_export = True
                i_ += 1
            elif tok == "--queue":
                if i_ + 1 >= len(extra):
                    print("Error: --queue requires a path.", file=sys.stderr)
                    sys.exit(2)
                queue_path = Path(extra[i_ + 1])
                i_ += 2
            elif tok == "--regulator":
                if i_ + 1 >= len(extra):
                    print("Error: --regulator requires a value.", file=sys.stderr)
                    sys.exit(2)
                regulator = extra[i_ + 1]
                i_ += 2
            elif tok == "--source-id":
                if i_ + 1 >= len(extra):
                    print("Error: --source-id requires a value.", file=sys.stderr)
                    sys.exit(2)
                source_id = extra[i_ + 1]
                i_ += 2
            elif tok == "--status":
                if i_ + 1 >= len(extra):
                    print("Error: --status requires a value.", file=sys.stderr)
                    sys.exit(2)
                status = extra[i_ + 1]
                i_ += 2
            elif tok == "--limit":
                if i_ + 1 >= len(extra):
                    print("Error: --limit requires an integer.", file=sys.stderr)
                    sys.exit(2)
                try:
                    limit = max(1, int(extra[i_ + 1]))
                except ValueError:
                    print(f"Error: --limit must be an integer, got {extra[i_+1]!r}.", file=sys.stderr)
                    sys.exit(2)
                i_ += 2
            elif tok == "--discover-only":
                mode = "discover-only"
                i_ += 1
            elif tok == "--no-save-only":
                mode = "no-save-only"
                i_ += 1
            elif tok == "--save-passing":
                mode = "save-passing"
                i_ += 1
            elif tok == "--repeat-baseline":
                if i_ + 1 >= len(extra):
                    print("Error: --repeat-baseline requires an integer.", file=sys.stderr)
                    sys.exit(2)
                try:
                    repeat_baseline = max(0, int(extra[i_ + 1]))
                except ValueError:
                    print(f"Error: --repeat-baseline must be an integer, got {extra[i_+1]!r}.", file=sys.stderr)
                    sys.exit(2)
                i_ += 2
            else:
                print(f"Error: unknown option {tok!r} for 'mass-source-activate'.", file=sys.stderr)
                sys.exit(2)
        summary = run_mass_source_activation_batch(
            queue_path=queue_path,
            regulator=regulator,
            source_id=source_id,
            status=status,
            limit=limit,
            mode=mode,
            repeat_baseline=repeat_baseline,
        )
        if json_export:
            print(_json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(f"\n  {_BOLD}StatuteProof — Mass Source Activation Runner{_R}")
            print(f"  {_DIM}Mode: {summary['mode']} · no sources.json update · no customer delivery{_R}")
            _hr()
            _label("Processed", str(summary["processed_count"]))
            _label("No-save passed", str(summary["no_save_passed_count"]))
            _label("Saved evidence", str(summary["saved_evidence_count"]))
            _label("Activation-ready", str(summary["activation_ready_count"]))
            for warning in summary.get("warnings") or []:
                print(f"  {_YELLOW}Warning:{_R} {warning}")

    elif cmd in {"discover-source", "source-discovery-lab"}:
        extra = args[1:]
        if not extra or extra[0].startswith("-"):
            print(f"Error: '{cmd}' requires a URL argument.", file=sys.stderr)
            print(
                f"  Usage: python run.py {cmd} <url> [--json] [--js] [--network] [--sitemap] [--feeds] [--documents] [--max-links N] [--max-depth N]",
                file=sys.stderr,
            )
            sys.exit(2)
        ds_url = extra[0]
        ds_json = "--json" in extra
        ds_jur = ""
        ds_cat = ""
        ds_js = cmd == "source-discovery-lab"
        ds_network = False
        ds_sitemap = True
        ds_feeds = True
        ds_documents = True
        ds_max_links = 50
        ds_max_depth = 1
        i_ = 1
        while i_ < len(extra):
            tok = extra[i_]
            if tok == "--json":
                i_ += 1
            elif tok == "--js":
                ds_js = True
                i_ += 1
            elif tok == "--network":
                ds_network = True
                i_ += 1
            elif tok == "--sitemap":
                ds_sitemap = True
                i_ += 1
            elif tok == "--no-sitemap":
                ds_sitemap = False
                i_ += 1
            elif tok == "--feeds":
                ds_feeds = True
                i_ += 1
            elif tok == "--no-feeds":
                ds_feeds = False
                i_ += 1
            elif tok == "--documents":
                ds_documents = True
                i_ += 1
            elif tok == "--no-documents":
                ds_documents = False
                i_ += 1
            elif tok == "--max-links":
                if i_ + 1 >= len(extra):
                    print("Error: --max-links requires an integer.", file=sys.stderr)
                    sys.exit(2)
                try:
                    ds_max_links = max(1, min(250, int(extra[i_ + 1])))
                except ValueError:
                    print(f"Error: --max-links must be an integer, got {extra[i_+1]!r}.", file=sys.stderr)
                    sys.exit(2)
                i_ += 2
            elif tok == "--max-depth":
                if i_ + 1 >= len(extra):
                    print("Error: --max-depth requires an integer.", file=sys.stderr)
                    sys.exit(2)
                try:
                    ds_max_depth = max(0, min(2, int(extra[i_ + 1])))
                except ValueError:
                    print(f"Error: --max-depth must be an integer, got {extra[i_+1]!r}.", file=sys.stderr)
                    sys.exit(2)
                i_ += 2
            elif tok == "--jurisdiction":
                if i_ + 1 >= len(extra):
                    print("Error: --jurisdiction requires a value.", file=sys.stderr)
                    sys.exit(2)
                ds_jur = extra[i_ + 1]
                i_ += 2
            elif tok == "--category":
                if i_ + 1 >= len(extra):
                    print("Error: --category requires a value.", file=sys.stderr)
                    sys.exit(2)
                ds_cat = extra[i_ + 1]
                i_ += 2
            else:
                print(f"Error: unknown option {tok!r} for '{cmd}'.", file=sys.stderr)
                sys.exit(2)
        _cmd_discover_source(
            ds_url,
            json_export=ds_json,
            jurisdiction=ds_jur,
            category=ds_cat,
            js=ds_js,
            network=ds_network,
            sitemap=ds_sitemap,
            feeds=ds_feeds,
            documents=ds_documents,
            max_links=ds_max_links,
            max_depth=ds_max_depth,
        )

    elif cmd.startswith(("http://", "https://")):
        # backward-compatible bare URL
        _run_single_url(cmd)

    else:
        print(
            f"Error: unknown command '{cmd}'. "
            "Use: url | all | watch | sources | coverage | coverage-plan | health | demo | test-source | source-lab | investigate-source | source-discovery-lab | mass-source-activate | test-mapped | add-source | report | ai-test | ai-health | ai-brief-test | telegram-test | telegram-updates | telegram-listen | telegram-clients | telegram-client-set | telegram-client-test | telegram-client-disable | env-check | adapter-research | source-audit | source-readiness | source-history | backfill-artifacts | alert-queue | weekly-status | source-diff | alert-draft | relevance-test | alert-review | weekly-brief | adapter-queue | document-test | api | discover-source",
            file=sys.stderr,
        )
        sys.exit(2)


def _cmd_document_test(url: str) -> None:
    """
    Test document extraction for a URL.

    If the URL ends in .pdf — fetch and extract directly.
    Otherwise — fetch the page, find document links, process up to 3 PDFs.
    No AI. No Telegram. No DB writes.
    """
    from app.source_tester import validate_public_url
    from app.scraper import fetch_page
    from app.document_extractor import (
        fetch_document, extract_pdf_text,
        find_document_links, extract_documents_from_page,
    )

    print(f"\n  {_BOLD}RegRadar — Document Test{_R}")
    print(f"  {_DIM}No AI · No Telegram · No DB writes{_R}")
    _hr()

    safe, msg = validate_public_url(url)
    if not safe:
        print(f"  {_RED}✗  URL rejected:{_R} {msg}\n", file=sys.stderr)
        sys.exit(1)

    import requests as _req
    from urllib.parse import urlparse

    parsed = urlparse(url)
    path_lower = parsed.path.lower()
    is_pdf = path_lower.endswith(".pdf")

    if is_pdf:
        # ── Direct PDF ───────────────────────────────────────────────────
        print(f"  {_DIM}Detected PDF URL — fetching directly …{_R}\n")
        fetch = fetch_document(url)
        _label("URL:",          url)
        _label("HTTP status:",  str(fetch.get("http_status") or "—"))
        _label("Content type:", fetch.get("content_type", ""))
        _label("Downloaded:",   f"{fetch.get('bytes', 0):,} bytes")

        if fetch["status"] != "ok":
            _label("Error:", fetch.get("error", "unknown"))
            _hr()
            sys.exit(1)

        extr = extract_pdf_text(fetch["data"])
        _label("Method:",       extr.get("method", "none"))
        _label("Extracted:",    f"{extr.get('chars', 0):,} chars")
        q = extr.get("quality", "failed")
        q_str = (
            f"{_GREEN}good{_R}"         if q == "good" else
            f"{_YELLOW}low_content{_R}" if q == "low_content" else
            f"{_RED}failed{_R}"
        )
        _label("Quality:", q_str)
        if extr.get("error"):
            _label("Error:", extr["error"][:80])
        if extr.get("text"):
            _hr("·")
            print(f"  {_BOLD}Text sample (first 400 chars):{_R}")
            print(f"  {_DIM}{extr['text'][:400]}{_R}")
        _hr()
        print()
        sys.exit(0)

    # ── HTML page → discover + process document links ────────────────────
    print(f"  {_DIM}Fetching page to discover document links …{_R}\n")
    try:
        resp = _req.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"},
            timeout=15,
            allow_redirects=True,
        )
        html = resp.text if resp.ok else ""
        _label("HTTP status:", str(resp.status_code))
        _label("HTML length:",  f"{len(html):,} chars")
    except Exception as exc:
        print(f"  {_RED}✗  Fetch failed:{_R} {exc}\n", file=sys.stderr)
        sys.exit(1)

    used_fallback = False
    if len(html) < 500:
        print(f"  {_YELLOW}Requests returned too little HTML — trying scraper fallback …{_R}")
        try:
            html = fetch_page(url)
            used_fallback = True
            _label("Fallback HTML length:", f"{len(html):,} chars")
        except Exception as exc:
            print(f"  {_YELLOW}Fallback fetch failed:{_R} {type(exc).__name__}: {exc}")

    lnk = find_document_links(html, url)
    if not lnk["all_document_links"] and not used_fallback:
        print(f"  {_YELLOW}No document links in requests HTML — trying scraper fallback …{_R}")
        try:
            html = fetch_page(url)
            used_fallback = True
            _label("Fallback HTML length:", f"{len(html):,} chars")
            lnk = find_document_links(html, url)
        except Exception as exc:
            print(f"  {_YELLOW}Fallback fetch failed:{_R} {type(exc).__name__}: {exc}")
    _label("PDF links found:",  str(len(lnk["pdf_links"])))
    _label("DOC links found:",  str(len(lnk["doc_links"])))
    _label("DOCX links found:", str(len(lnk["docx_links"])))

    if lnk["pdf_links"]:
        print()
        print(f"  {_DIM}PDF links:{_R}")
        for p in lnk["pdf_links"][:5]:
            print(f"    • {p}")
        if len(lnk["pdf_links"]) > 5:
            print(f"    {_DIM}… and {len(lnk['pdf_links'])-5} more{_R}")

    if not lnk["all_document_links"]:
        _hr()
        print(f"  {_DIM}No document links found on this page.{_R}\n")
        sys.exit(0)

    print(f"\n  {_DIM}Processing up to 3 PDFs …{_R}\n")
    doc_result = extract_documents_from_page(html, url, max_docs=3)

    _hr("·")
    print(f"  {_BOLD}Document Extraction Results{_R}")
    _label("PDFs processed:",     str(doc_result.get("pdf_processed", 0)))
    _label("Combined chars:",     f"{doc_result.get('combined_chars', 0):,}")
    q = doc_result.get("quality", "failed")
    q_str = (
        f"{_GREEN}good{_R}"         if q == "good" else
        f"{_YELLOW}low_content{_R}" if q == "low_content" else
        f"{_RED}failed{_R}"
    )
    _label("Quality:", q_str)

    for item in doc_result.get("items", []):
        fn  = item["url"].split("/")[-1][:44]
        c   = item.get("chars", 0)
        m   = item.get("method", "none")
        err = item.get("error", "")
        if err:
            print(f"    {_RED}✗{_R} {_DIM}{fn}{_R}  {_RED}{err[:60]}{_R}")
        else:
            c_col = _GREEN if c >= 1000 else (_YELLOW if c >= 100 else _DIM)
            print(f"    {_GREEN}✓{_R} {_DIM}{fn}{_R}  {c_col}{c:,}c{_R}  [{m}]")

    _hr()
    print()
    sys.exit(0)


def _cmd_adapter_research(query: str) -> None:
    """Investigate one source to plan a custom adapter."""
    from app.adapter_research import run_adapter_research, print_research_report

    result = run_adapter_research(query)
    if result is not None:
        print_research_report(result)


def _cmd_source_audit(json_export: bool = False) -> None:
    """Audit all sources for extraction quality and adapter needs."""
    from app.source_audit import run_audit, print_audit_report, export_audit_json

    print("  Running source audit — this may take several minutes …\n")
    records = run_audit(verbose=True)
    print_audit_report(records)

    if json_export:
        path = export_audit_json(records)
        print(f"  JSON exported → {path}\n")


def _cmd_source_readiness(
    market: str = "AE",
    profile: str = "fintech",
    html_export: bool = False,
    record_run: bool = False,
) -> None:
    """Show source readiness report for a market and optionally export HTML."""
    from app.source_readiness import (
        build_readiness_report,
        render_readiness_terminal,
        export_readiness_html,
    )

    flag = _JURISDICTION_FLAG.get(market, "")
    print(f"  {_CYAN}{_BOLD}RegRadar — Source Readiness{_R}  {flag} {market} / {profile}\n")

    report = build_readiness_report(market, profile, record_run=record_run)
    render_readiness_terminal(report)

    if html_export:
        path = export_readiness_html(report)
        print(f"  {_GREEN}HTML report exported →{_R} {path}\n")

    if record_run:
        print(f"  {_GREEN}Source run history recorded.{_R}\n")

    verdict = report["pilot_verdict"]
    vcolor  = _GREEN if verdict == "FREE_CHECK_READY" else (_YELLOW if verdict == "PILOT_READY" else _RED)
    print(f"  Summary: {vcolor}{_BOLD}{verdict}{_R}"
          f"  |  active={report['sources_active']}"
          f"  blocked={report['sources_blocked']}"
          f"  p0={len(report['p0_sources'])} p1={len(report['p1_sources'])}\n")


def _cmd_source_history(market: str = "AE", source: str | None = None, limit: int = 20) -> None:
    """Show latest source run history records."""
    from app.source_runs import render_history_terminal, source_run_path

    render_history_terminal(market=market, source_filter=source, limit=limit)
    print(f"\n  Source run history file: {source_run_path()}\n")


def _cmd_source_diff(market: str = "AE", source: str | None = None, latest_changed: bool = False) -> None:
    """Inspect latest changed source diff/proof artifacts."""
    import json as _json
    from pathlib import Path as _Path

    from app.source_runs import changed_runs

    limit = 1 if latest_changed else 5
    rows = changed_runs(market=market, source_filter=source, limit=limit)
    if not rows:
        print(f"\nRegRadar — Source Diff  {market.upper()}")
        print("No CHANGED source run records found for this filter.\n")
        return

    base_dir = _Path(__file__).parent

    def _load(path_value: str | None) -> dict:
        if not path_value:
            return {}
        path = _Path(path_value)
        if not path.is_absolute():
            path = base_dir / path
        if not path.exists():
            return {}
        try:
            return _json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    print(f"\nRegRadar — Source Diff  {market.upper()}")
    print("─" * 96)
    for rec in rows:
        diff = _load(rec.get("diff_json_path"))
        proof = _load(rec.get("proof_block_path"))
        norm_hash = str(rec.get("normalized_hash") or "")[:12] or "—"
        print(f"{rec.get('source_name') or rec.get('source_id')}")
        print(f"  checked: {rec.get('timestamp_utc') or 'unknown'}")
        print(
            f"  status: {rec.get('change_status') or 'UNKNOWN'}"
            f"  quality: {rec.get('extraction_quality') or 'UNKNOWN'}"
            f"  normalized_hash: {norm_hash}"
        )
        print(f"  diff: {diff.get('diff_summary') or 'diff artifact unavailable'}")
        print(
            f"  counts: +{diff.get('added_count', 0)}"
            f" -{diff.get('removed_count', 0)}"
            f" changed={diff.get('changed_count', 0)}"
        )
        print(f"  meaningful_change_detected: {diff.get('meaningful_change_detected')}")
        print(f"  proof_quality: {proof.get('proof_quality') or 'UNKNOWN'}")
        print(f"  diff_json_path: {rec.get('diff_json_path') or '—'}")
        print(f"  diff_md_path: {rec.get('diff_md_path') or '—'}")
        print(f"  proof_block_path: {rec.get('proof_block_path') or '—'}")
        print("")


def _cmd_alert_draft(
    market: str = "AE",
    source: str | None = None,
    latest_changed: bool = False,
    profile_id: str | None = None,
) -> None:
    """Build a draft-only alert artifact from changed source proof."""
    import json as _json
    from pathlib import Path as _Path

    from app.alert_drafts import (
        build_alert_draft,
        load_json_artifact,
        snapshot_dir_from_proof,
        write_alert_artifacts,
    )
    from app.client_profiles import (
        load_client_profile,
        score_alert_relevance,
        source_metadata_for_alert,
    )
    from app.source_runs import changed_runs

    limit = 1 if latest_changed else 5
    rows = changed_runs(market=market, source_filter=source, limit=limit)
    if not rows:
        print(f"\nRegRadar — Alert Draft  {market.upper()}")
        print("No CHANGED source run records found for this filter.\n")
        return

    base_dir = _Path(__file__).parent
    print(f"\nRegRadar — Alert Draft  {market.upper()}")
    print("─" * 96)
    client_profile = load_client_profile(profile_id) if profile_id else None
    for rec in rows:
        diff = load_json_artifact(rec.get("diff_json_path"), base_dir)
        proof = load_json_artifact(rec.get("proof_block_path"), base_dir)
        if not diff:
            diff = {
                "diff_quality": "INCOMPLETE",
                "meaningful_change_detected": False,
                "diff_summary": "Diff artifact unavailable; human review required.",
                "limitations": ["Diff artifact unavailable; human review required."],
            }
        if not proof:
            proof = {
                "proof_quality": "INCOMPLETE",
                "official_url": rec.get("official_url"),
                "normalized_hash": rec.get("normalized_hash"),
                "limitations_notes": "Proof artifact unavailable; human review required.",
            }

        alert = build_alert_draft(rec, diff, proof)
        snapshot_dir = snapshot_dir_from_proof(proof, base_dir)
        paths = {}
        if snapshot_dir is not None:
            paths = write_alert_artifacts(alert, snapshot_dir)
        relevance = None
        relevance_path = None
        if client_profile is not None:
            metadata = source_metadata_for_alert(alert)
            relevance = score_alert_relevance(alert, client_profile, metadata)
            if snapshot_dir is not None:
                relevance_path = snapshot_dir / "relevance.json"
                payload = {
                    "client_id": client_profile.get("client_id"),
                    "alert_id": alert.get("alert_id"),
                    "source_id": alert.get("source_id"),
                    "source_name": alert.get("source_name"),
                    "source_metadata": metadata,
                    **relevance,
                }
                relevance_path.write_text(
                    _json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
                alert["relevance"] = payload
                write_alert_artifacts(alert, snapshot_dir)

        print(f"{alert.get('source_name') or alert.get('source_id')}")
        print(f"  change_type: {alert.get('change_type')}")
        print(f"  risk_level: {alert.get('risk_level')}")
        print(f"  review_status: {alert.get('review_status')}")
        print(f"  send_decision: {alert.get('send_decision')}")
        print(f"  confidence: {alert.get('confidence')}")
        print(f"  alert_draft_json_path: {paths.get('alert_draft_json_path') or 'not written'}")
        print(f"  alert_draft_md_path: {paths.get('alert_draft_md_path') or 'not written'}")
        if relevance is not None:
            print(f"  profile: {client_profile.get('client_id')}")
            print(f"  relevance_score: {relevance.get('relevance_score')}")
            print(f"  delivery_decision: {relevance.get('delivery_decision')}")
            print(f"  matched_topics: {', '.join(relevance.get('matched_topics') or []) or 'none'}")
            print(f"  relevance_reason: {relevance.get('reason')}")
            print(f"  relevance_path: {_rel_to_cwd(relevance_path) if relevance_path else 'not written'}")
        print("")


def _cmd_relevance_test(market: str = "AE", profile_id: str = "") -> None:
    """Score the latest alert draft or a synthetic fixture against a profile."""
    from pathlib import Path as _Path

    from app.alert_drafts import build_alert_draft, load_json_artifact, snapshot_dir_from_proof
    from app.client_profiles import (
        load_client_profile,
        score_alert_relevance,
        source_metadata_for_alert,
    )
    from app.source_runs import changed_runs

    base_dir = _Path(__file__).parent
    profile = load_client_profile(profile_id)
    rows = changed_runs(market=market, limit=1)
    alert = None
    if rows:
        rec = rows[0]
        diff = load_json_artifact(rec.get("diff_json_path"), base_dir)
        proof = load_json_artifact(rec.get("proof_block_path"), base_dir)
        snapshot_dir = snapshot_dir_from_proof(proof, base_dir)
        draft_path = snapshot_dir / "alert_draft.json" if snapshot_dir is not None else None
        if draft_path is not None and draft_path.exists():
            alert = load_json_artifact(str(draft_path), base_dir)
        elif diff and proof:
            alert = build_alert_draft(rec, diff, proof)
    if alert is None:
        alert = _synthetic_relevance_alert(market)

    metadata = source_metadata_for_alert(alert)
    relevance = score_alert_relevance(alert, profile, metadata)

    print(f"\nRegRadar — Relevance Test  {market.upper()}")
    print("─" * 96)
    print(f"profile: {profile.get('client_id')} ({profile.get('company_name')})")
    print(f"source: {alert.get('source_name')}")
    print(f"change_type: {alert.get('change_type')}")
    print(f"risk_level: {alert.get('risk_level')}")
    print(f"relevance_score: {relevance.get('relevance_score')}")
    print(f"delivery_decision: {relevance.get('delivery_decision')}")
    print(f"matched_topics: {', '.join(relevance.get('matched_topics') or []) or 'none'}")
    print(f"matched_sources: {', '.join(relevance.get('matched_sources') or []) or 'none'}")
    print(f"matched_jurisdictions: {', '.join(relevance.get('matched_jurisdictions') or []) or 'none'}")
    print(f"reason: {relevance.get('reason')}\n")


def _parse_alert_review_options(
    args: list[str],
    *,
    require_alert: bool,
    require_reviewer: bool,
) -> dict:
    opts = {
        "alert_id": None,
        "reviewer": "",
        "note": "",
        "weekly": False,
        "urgent": False,
        "force": False,
    }
    i_ = 0
    while i_ < len(args):
        tok = args[i_]
        if tok == "--alert-id" and i_ + 1 < len(args):
            opts["alert_id"] = args[i_ + 1]
            i_ += 2
        elif tok == "--reviewer" and i_ + 1 < len(args):
            opts["reviewer"] = args[i_ + 1]
            i_ += 2
        elif tok == "--note" and i_ + 1 < len(args):
            opts["note"] = args[i_ + 1]
            i_ += 2
        elif tok == "--weekly":
            opts["weekly"] = True
            i_ += 1
        elif tok == "--urgent":
            opts["urgent"] = True
            i_ += 1
        elif tok == "--force":
            opts["force"] = True
            i_ += 1
        else:
            print(f"Error: unknown alert-review option {tok!r}.", file=sys.stderr)
            sys.exit(2)
    if require_alert and not opts["alert_id"]:
        print("Error: --alert-id is required.", file=sys.stderr)
        sys.exit(2)
    if require_reviewer and not opts["reviewer"]:
        print("Error: --reviewer is required.", file=sys.stderr)
        sys.exit(2)
    if require_reviewer and not opts["note"]:
        print("Error: --note is required for review actions.", file=sys.stderr)
        sys.exit(2)
    return opts


def _cmd_alert_review_list(market: str = "AE") -> None:
    from app.alert_review import list_alert_drafts, latest_review_for, review_store_path

    rows = list_alert_drafts(market=market)[:20]
    print(f"\nRegRadar — Alert Review Queue  {market.upper()}")
    print("─" * 96)
    if not rows:
        print("No alert drafts found.\n")
        return
    for alert in rows:
        latest = latest_review_for(alert.get("alert_id"))
        status = (latest or {}).get("new_status") or alert.get("review_status") or "DRAFT"
        decision = (latest or {}).get("new_send_decision") or alert.get("send_decision") or "HOLD_FOR_REVIEW"
        print(f"{alert.get('checked_at_utc') or 'unknown'}  {status:<22} {decision:<26} {alert.get('source_name')}")
        print(f"  - alert_id: {alert.get('alert_id')}")
        print(f"  - risk={alert.get('risk_level')} confidence={alert.get('confidence')} change_type={alert.get('change_type')}")
    print(f"\n  Review store: {review_store_path()}\n")


def _cmd_alert_review_show(alert_id: str) -> None:
    from app.alert_review import approval_safety_issues, find_alert_draft, latest_review_for

    try:
        alert, path = find_alert_draft(alert_id)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    latest = latest_review_for(alert_id)
    proof = alert.get("proof_block") or {}
    relevance = alert.get("relevance") or {}
    status = (latest or {}).get("new_status") or alert.get("review_status")
    decision = (latest or {}).get("new_send_decision") or alert.get("send_decision")

    print(f"\nRegRadar — Alert Review Detail")
    print("─" * 96)
    print(f"alert_id: {alert.get('alert_id')}")
    print(f"source: {alert.get('source_name')}")
    print(f"checked: {alert.get('checked_at_utc')}")
    print(f"change_type: {alert.get('change_type')}  risk: {alert.get('risk_level')}  confidence: {alert.get('confidence')}")
    print(f"review_status: {status}")
    print(f"send_decision: {decision}")
    if relevance:
        print(f"relevance: {relevance.get('delivery_decision')} score={relevance.get('relevance_score')} profile={relevance.get('client_id')}")
    print(f"alert_draft_path: {_rel_to_cwd(path)}")
    print(f"proof_path: {proof.get('proof_block_path') or str(path.parent / 'proof.json')}")
    print(f"diff_path: {proof.get('diff_json_path') or str(path.parent / 'diff.json')}")
    issues = approval_safety_issues(alert)
    print(f"safety_issues: {', '.join(issues) if issues else 'none'}")
    if latest:
        print(f"latest_review: {latest.get('new_status')} by {latest.get('reviewer')} at {latest.get('reviewed_at_utc')}")
    print("")


def _cmd_alert_review_action(
    *,
    alert_id: str,
    action: str,
    reviewer: str,
    note: str,
    force: bool = False,
) -> None:
    from app.alert_review import review_alert, review_store_path

    try:
        record = review_alert(
            alert_id=alert_id,
            action=action,
            reviewer=reviewer,
            note=note,
            force=force,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\nRegRadar — Alert Review Recorded")
    print("─" * 96)
    print(f"review_id: {record.get('review_id')}")
    print(f"alert_id: {record.get('alert_id')}")
    print(f"source: {record.get('source_name')}")
    print(f"new_status: {record.get('new_status')}")
    print(f"new_send_decision: {record.get('new_send_decision')}")
    print(f"reviewer: {record.get('reviewer')}")
    print(f"review_store: {review_store_path()}\n")


def _cmd_weekly_brief(
    *,
    client_id: str,
    market: str = "AE",
    days: int = 7,
    date_from: str | None = None,
    date_to: str | None = None,
    formats: set[str] | None = None,
    demo_fixture: bool = False,
) -> None:
    from app.weekly_brief import generate_weekly_brief

    try:
        result = generate_weekly_brief(
            client_id=client_id,
            market=market,
            days=days,
            date_from=date_from,
            date_to=date_to,
            demo_fixture=demo_fixture,
            formats=formats,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    brief = result["brief"]
    print(f"\nRegRadar — Weekly Brief  {market.upper()}")
    print("─" * 96)
    print(f"client: {brief.get('client_name')} ({brief.get('client_id')})")
    print(f"period: {brief.get('period_start')} to {brief.get('period_end')}")
    print(f"included_alerts: {result.get('included_alerts')}")
    print(f"urgent_ready_items: {brief.get('summary', {}).get('urgent_ready_items')}")
    print(f"weekly_only_items: {brief.get('summary', {}).get('weekly_only_items')}")
    print(f"demo_fixture: {result.get('demo_fixture')}")
    for kind, path in result["paths"].items():
        print(f"{kind}_path: {path}")
    print("")


def _synthetic_relevance_alert(market: str) -> dict:
    return {
        "alert_id": "synthetic-vara-custody",
        "review_status": "DRAFT",
        "send_decision": "HOLD_FOR_REVIEW",
        "market": market,
        "source_id": "AE-dubai-virtual-assets-regulatory-authority-vara",
        "source_name": "Dubai Virtual Assets Regulatory Authority (VARA)",
        "source_url": "https://www.vara.ae/",
        "checked_at_utc": "synthetic",
        "change_status": "CHANGED",
        "change_type": "LICENSING",
        "risk_level": "MEDIUM",
        "confidence": "MEDIUM",
        "what_changed": "Synthetic VARA custody/licensing fixture.",
        "added_chunks": ["Licensed VASPs must maintain custody controls."],
        "removed_chunks": [],
        "changed_chunks": [],
        "affected_entities": "Licensed VASPs, crypto exchanges, custody providers, compliance teams.",
        "recommended_action": "Review changed sections against licensing and custody controls.",
        "limitations": [],
        "proof_block": {"proof_quality": "GOOD"},
    }


def _rel_to_cwd(path: object) -> str:
    if path is None:
        return ""
    from pathlib import Path as _Path

    p = _Path(path)
    try:
        return str(p.resolve().relative_to(_Path.cwd().resolve()))
    except ValueError:
        return str(p)


def _cmd_adapter_queue() -> None:
    """Show sources that need custom adapters, sorted by priority."""
    from app.source_audit import run_audit, print_adapter_queue

    print("  Building adapter queue — running full source audit …\n")
    records = run_audit(verbose=True)
    print_adapter_queue(records)


def _cmd_contact_queue(limit: int = 20, latest: bool = False, json_export: bool = False) -> None:
    """List queued contact requests from data/contact_requests.jsonl."""
    import json as _json
    from app.config import BASE_DIR

    queue_file = BASE_DIR / "data" / "contact_requests.jsonl"

    if not queue_file.exists():
        if json_export:
            print("[]")
            return
        print("No contact requests queued yet.  (data/contact_requests.jsonl not found)")
        print("The file is created automatically when the first form submission arrives.")
        return

    entries = []
    with queue_file.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(_json.loads(line))
            except _json.JSONDecodeError:
                continue

    total = len(entries)
    if total == 0:
        if json_export:
            print("[]")
            return
        print("Contact queue file exists but contains no valid entries.")
        return

    if latest:
        shown = entries[-1:]
    elif limit > 0:
        shown = entries[-limit:]
    else:
        shown = entries

    if json_export:
        print(_json.dumps(shown, ensure_ascii=False, indent=2))
        return

    label = "most recent" if latest else f"last {len(shown)}"
    print(f"  Contact queue — {label} of {total} total entr{'y' if total == 1 else 'ies'}\n")
    for idx, entry in enumerate(shown, 1):
        received = entry.get("received_at", "?")
        body     = entry.get("body", {})
        name     = body.get("name",    "(no name)")
        email    = body.get("email",   "(no email)")
        company  = body.get("company",  "")
        industry = body.get("industry", "")
        markets  = body.get("markets",  "")
        watchlist = body.get("watchlistContext")

        print(f"  [{idx}] {received}")
        print(f"        Name:    {name}")
        print(f"        Email:   {email}")
        if company:
            print(f"        Company: {company}")
        if industry:
            print(f"        Industry: {industry}")
        if markets:
            print(f"        Markets: {markets}")
        if isinstance(watchlist, dict):
            wl_parts = []
            for key in ("companyType", "markets", "topics", "delivery"):
                val = watchlist.get(key)
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val if v)
                if val:
                    wl_parts.append(f"{key}={val}")
            if wl_parts:
                print(f"        Watchlist: {' | '.join(wl_parts)}")
        print()

    if total > len(shown) and not latest:
        print(f"  (showing last {len(shown)} of {total}; use --limit or --json to see more)")


def _cmd_telegram_test() -> None:
    """
    Send a test Telegram alert.

    Credentials are resolved in priority order:
      1. telegram_settings.json  (written by the web settings UI)
      2. .env  (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)
    The token is never printed.
    """
    from app import telegram_settings as _ts
    import requests as _req

    token    = _ts.get_token()
    settings = _ts.load()
    chat_id  = settings["chat_id"]

    if not token or not chat_id:
        print(
            "Error: Bot token or Chat ID not configured.\n"
            "  Option A — set in .env:\n"
            "    TELEGRAM_BOT_TOKEN=<token>\n"
            "    TELEGRAM_CHAT_ID=<chat_id>\n"
            "  Option B — save via web UI and run the API server first:\n"
            "    python run.py api",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Sending test message to chat {chat_id!r} …")
    try:
        resp = _req.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id":    chat_id,
                "text":       "✅ *RegRadar* — test connection is working. Alerts will be delivered here.",
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            print("✅  Test message sent successfully.")
        else:
            print(f"❌  Telegram API error: {data.get('description', 'unknown')}", file=sys.stderr)
            sys.exit(1)
    except _req.Timeout:
        print("❌  Request timed out after 10 s.", file=sys.stderr)
        sys.exit(1)
    except _req.HTTPError as exc:
        print(f"❌  HTTP error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"❌  {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


# ── telegram-updates command ──────────────────────────────────────────────────

def _cmd_telegram_updates() -> None:
    """
    Fetch the latest Telegram updates once and print chat info.

    Does NOT start a listener. Useful for discovering chat IDs during
    client setup without a running bot server.
    Exits 0 always.
    """
    from app.telegram_settings import get_token
    from app.telegram_onboarding import fetch_updates

    token = get_token()
    if not token:
        print(
            "Error: TELEGRAM_BOT_TOKEN not configured.\n"
            "  Set it in .env or via: python run.py api",
            file=sys.stderr,
        )
        sys.exit(1)

    _hr()
    print(f"  {_BOLD}RegRadar — Telegram Updates (one-shot){_R}")
    print(f"  {_DIM}Fetches pending updates. Use /start or /id in Telegram first.{_R}")
    _hr()

    updates = fetch_updates(token, offset=0, timeout=0)

    if not updates:
        print(f"\n  {_YELLOW}No pending updates found.{_R}")
        print(f"  Open @regradar_alerts_bot in Telegram and send /start or /id.")
        print(f"  Then run this command again.\n")
        sys.exit(0)

    seen: set[str] = set()
    print(f"\n  Found {len(updates)} update(s):\n")
    for upd in updates:
        msg = upd.get("message") or upd.get("channel_post")
        if not msg:
            continue
        chat     = msg.get("chat", {})
        chat_id  = str(chat.get("id", "?"))
        chat_type = chat.get("type", "?")
        username = chat.get("username") or chat.get("title") or ""
        text     = (msg.get("text") or "")[:60]
        key      = chat_id
        if key in seen:
            continue
        seen.add(key)
        uname_str = f"  @{username}" if username else ""
        print(f"  {_BOLD}Chat ID:{_R} {_CYAN}{chat_id}{_R}   {_DIM}({chat_type}){uname_str}{_R}")
        if text:
            print(f"  {_DIM}Last message: {text!r}{_R}")
        print()

    print(f"  {_DIM}Copy a Chat ID and paste it into RegRadar → Settings → Telegram.{_R}\n")
    sys.exit(0)


# ── telegram-listen command ───────────────────────────────────────────────────

def _cmd_telegram_listen() -> None:
    """
    Start Telegram long-polling listener. Responds to /start, /id, /connect.

    Runs until Ctrl-C. No DB writes. No monitoring alerts.
    """
    from app.telegram_settings import get_token
    from app.telegram_onboarding import run_listen_loop
    import requests as _req

    token = get_token()
    if not token:
        print(
            "Error: TELEGRAM_BOT_TOKEN not configured.\n"
            "  Set it in .env or via: python run.py api",
            file=sys.stderr,
        )
        sys.exit(1)

    # Resolve bot username for display
    bot_username = ""
    try:
        resp = _req.get(
            f"https://api.telegram.org/bot{token}/getMe", timeout=10
        )
        data = resp.json()
        if data.get("ok"):
            bot_username = data["result"].get("username", "")
    except Exception:
        pass

    run_listen_loop(token, bot_username=bot_username)
    sys.exit(0)


# ── telegram-clients command ──────────────────────────────────────────────────

def _cmd_telegram_clients() -> None:
    """List all registered Telegram client configurations."""
    from app.telegram_clients import list_telegram_clients

    clients = list_telegram_clients()

    _hr()
    print(f"  {_BOLD}RegRadar Telegram Clients{_R}")
    _hr()

    if not clients:
        print(f"\n  {_DIM}No clients configured yet.{_R}")
        print(f"  Add one: python run.py telegram-client-set <id> <chat_id> [name]\n")
        sys.exit(0)

    for c in clients:
        cid      = c.get("client_id", "?")
        name     = c.get("name", cid)
        chat_id  = c.get("telegram_chat_id", "?")
        enabled  = c.get("telegram_enabled", True)
        lang     = c.get("alert_language", "en")
        # Partially mask chat ID for display
        masked   = chat_id[:4] + "***" + chat_id[-4:] if len(chat_id) > 8 else chat_id
        status   = f"{_GREEN}enabled{_R}" if enabled else f"{_YELLOW}disabled{_R}"
        print(f"  {_BOLD}{cid}{_R}  |  {status}  |  chat_id: {masked}  |  language: {lang}  |  {_DIM}{name}{_R}")

    print()
    sys.exit(0)


# ── telegram-client-set command ───────────────────────────────────────────────

def _cmd_telegram_client_set(client_id: str, chat_id: str, name: str = "") -> None:
    """Add or update a Telegram client record."""
    from app.telegram_clients import upsert_telegram_client

    record = upsert_telegram_client(
        client_id=client_id,
        chat_id=chat_id,
        name=name or client_id,
        enabled=True,
        language="en",
    )
    masked = chat_id[:4] + "***" + chat_id[-4:] if len(chat_id) > 8 else chat_id
    print(
        f"✅  Client saved.\n"
        f"   client_id : {record['client_id']}\n"
        f"   name      : {record['name']}\n"
        f"   chat_id   : {masked}\n"
        f"   enabled   : {record['telegram_enabled']}\n"
        f"   language  : {record['alert_language']}"
    )
    sys.exit(0)


# ── telegram-client-test command ─────────────────────────────────────────────

def _cmd_telegram_client_test(client_id: str) -> None:
    """Send a test alert to a registered client's Telegram chat."""
    from app.telegram_clients import get_telegram_client, send_client_test_alert

    client = get_telegram_client(client_id)
    if not client:
        print(
            f"Error: client_id {client_id!r} not found.\n"
            f"  Add it first: python run.py telegram-client-set {client_id} <chat_id> [name]",
            file=sys.stderr,
        )
        sys.exit(1)

    chat_id = client.get("telegram_chat_id", "?")
    masked  = chat_id[:4] + "***" + chat_id[-4:] if len(chat_id) > 8 else chat_id
    print(f"Sending test alert to {client.get('name', client_id)} (chat {masked}) …")

    ok = send_client_test_alert(client_id)
    if ok:
        print("✅  Test alert sent successfully.")
        sys.exit(0)
    else:
        print(
            "❌  Test alert failed.\n"
            "  Check:\n"
            "  1. TELEGRAM_BOT_TOKEN is set in .env\n"
            "  2. The chat ID is correct\n"
            "  3. The bot has been started or added to the group/channel\n"
            "  4. For channels: bot must be admin with post permission",
            file=sys.stderr,
        )
        sys.exit(1)


# ── telegram-client-disable command ──────────────────────────────────────────

def _cmd_telegram_client_disable(client_id: str) -> None:
    """Disable Telegram alerts for a registered client."""
    from app.telegram_clients import disable_telegram_client

    ok = disable_telegram_client(client_id)
    if ok:
        print(f"✅  Client {client_id!r} disabled.")
        sys.exit(0)
    else:
        print(
            f"Error: client_id {client_id!r} not found.",
            file=sys.stderr,
        )
        sys.exit(1)


# ── api command ───────────────────────────────────────────────────────────────

def _cmd_api(port: int = 5001, host: str = "127.0.0.1") -> None:
    """Start the RegRadar settings API server (blocks until Ctrl-C)."""
    from app.api import run_server
    run_server(host=host, port=port)


def _cmd_env_check() -> None:
    """
    Print resolved .env path and key configuration values.
    Tokens are never printed in full — only present: true/false.
    """
    import requests as _req

    # Import after dotenv has already loaded (config module loads it on import)
    from app.config import (
        _DOTENV_PATH,
        ENABLE_AI_ANALYSIS,
        ANTHROPIC_API_KEY,
        ENABLE_TELEGRAM_ALERTS,
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
    )

    SEP = "─" * 60
    print(SEP)
    print("  RegRadar — environment check")
    print(SEP)
    print(f"  .env path         : {_DOTENV_PATH}")
    print(f"  .env exists       : {_DOTENV_PATH.exists()}")
    print()
    print(f"  ENABLE_AI_ANALYSIS       : {ENABLE_AI_ANALYSIS}")
    print(f"  ANTHROPIC_API_KEY present: {bool(ANTHROPIC_API_KEY)}")
    print()
    print(f"  ENABLE_TELEGRAM_ALERTS   : {ENABLE_TELEGRAM_ALERTS}")
    print(f"  TELEGRAM_CHAT_ID         : {TELEGRAM_CHAT_ID!r}")
    print(f"  TELEGRAM_BOT_TOKEN present: {bool(TELEGRAM_BOT_TOKEN)}")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print()
        print("  ⚠  Telegram not configured — skipping getMe call.")
        print(SEP)
        return

    print()
    print("  Calling Telegram getMe …")
    try:
        resp = _req.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe",
            timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            bot = data["result"]
            print(f"  bot username  : @{bot.get('username', 'unknown')}")
            print(f"  bot first_name: {bot.get('first_name', 'unknown')}")
            print("  getMe         : ✅  OK")
        else:
            print(f"  getMe         : ❌  {data.get('description', 'error')}")
    except _req.Timeout:
        print("  getMe         : ❌  timeout")
    except Exception as exc:
        print(f"  getMe         : ❌  {type(exc).__name__}: {exc}")

    print(SEP)


if __name__ == "__main__":
    main()
