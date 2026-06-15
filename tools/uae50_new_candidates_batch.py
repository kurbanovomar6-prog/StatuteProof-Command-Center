#!/usr/bin/env python3
"""No-save batch test for newly discovered UAE official endpoints.

Runs the two-pass (probe + adapter) no-save pipeline for each new candidate URL
discovered in the June 2026 endpoint discovery sprint. Does not write evidence,
does not mutate sources.json, does not send alerts.

Usage:
  python3 tools/uae50_new_candidates_batch.py --out /tmp/uae50_new.json
  python3 tools/uae50_new_candidates_batch.py --tier 1    # run only tier-1 high-confidence
  python3 tools/uae50_new_candidates_batch.py --tier 1,2  # run tiers 1 and 2
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "product" / "regradar"
sys.path.insert(0, str(PRODUCT))

from app.source_intake import (  # noqa: E402
    run_source_intake,
    load_sources_json,
    build_source_lab_contract,
    classify_failure_code,
)

# New candidates discovered in the June 2026 endpoint discovery sprint.
# Tier 1 = confirmed accessible via WebFetch + strong regulatory content
# Tier 2 = URL pattern known, regulatory content expected, may need Playwright
# Tier 3 = speculative / lower-priority
NEW_CANDIDATES: list[dict] = [
    # ── Tier 1: UAE FIU new knowledge centre URLs ──────────────────────────
    {"tier": 1, "source_id": "AE-uaefiu-typology-reports", "regulator": "UAE FIU",
     "url": "https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/",
     "title": "UAE FIU Trends and Typology Reports", "adapter_hint": "listing"},
    {"tier": 1, "source_id": "AE-uaefiu-aml-cft-laws", "regulator": "UAE FIU",
     "url": "https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/",
     "title": "UAE FIU AML/CFT Laws and Related Decisions", "adapter_hint": "listing"},
    {"tier": 1, "source_id": "AE-uaefiu-publications-hub", "regulator": "UAE FIU",
     "url": "https://uaefiu.gov.ae/en/more/knowledge-centre/publications/",
     "title": "UAE FIU Publications Hub", "adapter_hint": "listing"},
    {"tier": 1, "source_id": "AE-uaefiu-annual-reports", "regulator": "UAE FIU",
     "url": "https://uaefiu.gov.ae/en/more/knowledge-centre/publications/annual-report/",
     "title": "UAE FIU Annual Reports", "adapter_hint": "listing"},
    {"tier": 1, "source_id": "AE-uaefiu-nra-2024", "regulator": "UAE FIU",
     "url": "https://uaefiu.gov.ae/en/more/knowledge-centre/publications/national-risk-assessment-report-2024/",
     "title": "UAE National Risk Assessment 2024", "adapter_hint": "static_html"},
    {"tier": 1, "source_id": "AE-uaefiu-press-releases", "regulator": "UAE FIU",
     "url": "https://uaefiu.gov.ae/en/more/media/press-releases/",
     "title": "UAE FIU Press Releases", "adapter_hint": "listing"},
    # ── Tier 1: EOCN English URLs ───────────────────────────────────────────
    {"tier": 1, "source_id": "AE-eocn-laws-regulations-en", "regulator": "EOCN",
     "url": "https://www.eocn.gov.ae/en-us/laws-regulations-listing",
     "title": "EOCN AML/CFT Laws and Regulations (English)", "adapter_hint": "listing"},
    {"tier": 1, "source_id": "AE-eocn-news-en", "regulator": "EOCN",
     "url": "https://www.eocn.gov.ae/en-us/news",
     "title": "EOCN Regulatory News and Announcements (English)", "adapter_hint": "listing"},
    # ── Tier 1: ADGM confirmed accessible new pages ─────────────────────────
    {"tier": 1, "source_id": "AE-adgm-media-announcements", "regulator": "ADGM",
     "url": "https://www.adgm.com/media/announcements",
     "title": "ADGM FSRA Media and Regulatory Announcements", "adapter_hint": "custom_element"},
    {"tier": 1, "source_id": "AE-adgm-dp-regulatory-actions", "regulator": "ADGM",
     "url": "https://www.adgm.com/operating-in-adgm/office-of-data-protection/regulatory-actions",
     "title": "ADGM Data Protection Regulatory Actions", "adapter_hint": "custom_element"},
    {"tier": 1, "source_id": "AE-adgm-fsra-waivers", "regulator": "ADGM/FSRA",
     "url": "https://www.adgm.com/financial-services-regulatory-authority/waivers-and-modifications",
     "title": "ADGM FSRA Waivers and Modifications Register", "adapter_hint": "custom_element"},
    {"tier": 1, "source_id": "AE-adgm-dp-guidance", "regulator": "ADGM",
     "url": "https://www.adgm.com/operating-in-adgm/office-of-data-protection/guidance",
     "title": "ADGM Data Protection Guidance", "adapter_hint": "custom_element"},
    # ── Tier 2: ADGM Registration Authority ─────────────────────────────────
    {"tier": 2, "source_id": "AE-adgm-ra-circulars", "regulator": "ADGM RA",
     "url": "https://www.adgm.com/registration-authority/circulars",
     "title": "ADGM Registration Authority Circulars", "adapter_hint": "custom_element"},
    {"tier": 2, "source_id": "AE-adgm-ra-notices", "regulator": "ADGM RA",
     "url": "https://www.adgm.com/registration-authority/notices",
     "title": "ADGM Registration Authority Notices", "adapter_hint": "custom_element"},
    {"tier": 2, "source_id": "AE-adgm-ra-aml-guides", "regulator": "ADGM RA",
     "url": "https://www.adgm.com/registration-authority/aml-cft-quick-guides",
     "title": "ADGM RA AML/CFT Quick Guides", "adapter_hint": "custom_element"},
    {"tier": 2, "source_id": "AE-adgm-listing-announcements", "regulator": "ADGM/FSRA",
     "url": "https://www.adgm.com/financial-services-regulatory-authority/listing-authority/listing-authority-announcements",
     "title": "ADGM FSRA Listing Authority Announcements", "adapter_hint": "custom_element"},
    {"tier": 2, "source_id": "AE-adgm-listing-rules", "regulator": "ADGM/FSRA",
     "url": "https://www.adgm.com/financial-services-regulatory-authority/listing-authority/rules-and-guidance",
     "title": "ADGM FSRA Listing Authority Rules and Guidance", "adapter_hint": "custom_element"},
    # ── Tier 2: SCA new subpages ─────────────────────────────────────────────
    {"tier": 2, "source_id": "AE-sca-regulations-listing", "regulator": "SCA",
     "url": "https://www.sca.gov.ae/en/regulations/regulations-listing",
     "title": "SCA Regulations Listing", "adapter_hint": "sca_listing"},
    {"tier": 2, "source_id": "AE-sca-regulations-amendments", "regulator": "SCA",
     "url": "https://www.sca.gov.ae/en/regulations/regulations-listing/amendments",
     "title": "SCA Regulation Amendments", "adapter_hint": "sca_listing"},
    {"tier": 2, "source_id": "AE-sca-fatca-crs", "regulator": "SCA",
     "url": "https://www.sca.gov.ae/en/regulations/automatic-exchange-of-information-fatca-and-crs",
     "title": "SCA FATCA and CRS (AEOI) Guidance", "adapter_hint": "sca_listing"},
    {"tier": 2, "source_id": "AE-sca-corporate-governance", "regulator": "SCA",
     "url": "https://www.sca.gov.ae/en/regulations/corporate-governance",
     "title": "SCA Corporate Governance Regulations", "adapter_hint": "sca_listing"},
    {"tier": 2, "source_id": "AE-sca-market-rules", "regulator": "SCA",
     "url": "https://www.sca.gov.ae/en/regulations/market-rules-approved-by-sca",
     "title": "SCA Market Rules Approved by SCA", "adapter_hint": "sca_listing"},
    {"tier": 2, "source_id": "AE-sca-violations", "regulator": "SCA",
     "url": "https://www.sca.gov.ae/en/open-data/violations-and-violators",
     "title": "SCA Violations and Violators", "adapter_hint": "table"},
    # ── Tier 2: ADGM FSRA additional ─────────────────────────────────────────
    {"tier": 2, "source_id": "AE-adgm-federal-legislation", "regulator": "ADGM",
     "url": "https://www.adgm.com/legal-framework/federal-legislation",
     "title": "ADGM Federal Legislation", "adapter_hint": "custom_element"},
    {"tier": 2, "source_id": "AE-adgm-abu-dhabi-legislation", "regulator": "ADGM",
     "url": "https://www.adgm.com/legal-framework/abu-dhabi-legislation",
     "title": "ADGM Abu Dhabi Legislation", "adapter_hint": "custom_element"},
    # ── Tier 2: UAE FIU additional sitemap pages ──────────────────────────────
    {"tier": 2, "source_id": "AE-uaefiu-strategic-analysis", "regulator": "UAE FIU",
     "url": "https://uaefiu.gov.ae/en/more/knowledge-centre/publications/strategic-analysis-guidelines/",
     "title": "UAE FIU Strategic Analysis Guidelines", "adapter_hint": "listing"},
    {"tier": 2, "source_id": "AE-uaefiu-mutual-evaluation", "regulator": "UAE FIU",
     "url": "https://uaefiu.gov.ae/en/more/knowledge-centre/publications/uae-mutual-evaluation-report/",
     "title": "UAE FIU Mutual Evaluation Reports", "adapter_hint": "listing"},
    # ── Tier 3: Ministry of Economy new URL pattern ───────────────────────────
    {"tier": 3, "source_id": "AE-moec-aml-dnfbp", "regulator": "Ministry of Economy",
     "url": "https://www.moet.gov.ae/en/anti-money-laundering",
     "title": "UAE Ministry of Economy AML/DNFBP", "adapter_hint": "custom_element"},
    # ── Tier 3: ADGM data protection hub ─────────────────────────────────────
    {"tier": 3, "source_id": "AE-adgm-dp-hub", "regulator": "ADGM",
     "url": "https://www.adgm.com/operating-in-adgm/office-of-data-protection",
     "title": "ADGM Office of Data Protection Hub", "adapter_hint": "custom_element"},
    # ── Tier 3: DFSA new URL attempts ─────────────────────────────────────────
    {"tier": 3, "source_id": "AE-dfsa-published-decisions", "regulator": "DFSA",
     "url": "https://www.dfsa.ae/what-we-do/enforcement/published-decisions",
     "title": "DFSA Published Enforcement Decisions", "adapter_hint": "listing"},
]

RECO_MAP = {
    "listing": ("listing", "listing"),
    "table": ("table", "table"),
    "register": ("register", "register"),
    "rulebook": ("rulebook", "dfsa_rulebook"),
    "dfsa_rulebook": ("rulebook", "dfsa_rulebook"),
    "sca_listing": ("sca_listing", "sca_listing"),
    "document_listing": ("document_listing", "cbuae_document_listing"),
    "pdf_listing": ("pdf_listing", "pdf_listing"),
    "pdf_document": ("pdf_document", "pdf_document"),
    "custom_element": ("custom_element", "custom_element"),
    "static_html": ("static_html", "static_html"),
    "sitemap_feed": ("sitemap_feed", "sitemap_feed"),
    "public_json_api": ("public_json_api", "public_json_api"),
}


def _summary_fields(result: dict) -> dict:
    contract = build_source_lab_contract(result)
    status = str(result.get("status") or "")
    nav_shell = bool(result.get("nav_shell_detected")) or status == "NAV_SHELL_ONLY"
    chars = int(result.get("chars_normalized") or 0)
    strong = (
        status == "CONFIRMED_ACCESSIBLE"
        and bool(result.get("can_save_evidence"))
        and not nav_shell
        and int(result.get("quality_score") or 0) >= 60
        and not result.get("hash_collision")
    )
    return {
        "status": status,
        "activation_readiness": contract.get("activation_readiness"),
        "quality_score": result.get("quality_score"),
        "normalized_length": chars,
        "normalized_hash": result.get("normalized_hash"),
        "nav_shell": nav_shell,
        "can_save_evidence": bool(result.get("can_save_evidence")),
        "adapter_used": bool(result.get("adapter_used")),
        "adapter_name": result.get("adapter_name") or "",
        "adapter_family": result.get("adapter_family") or "",
        "failure_code": classify_failure_code(result) if status != "CONFIRMED_ACCESSIBLE" else "",
        "strong_pass": strong,
    }


def _empty() -> dict:
    return {"status": "", "strong_pass": False, "can_save_evidence": False,
            "quality_score": 0, "nav_shell": True}


def test_candidate(cand: dict, all_sources: list) -> dict:
    source_id = cand["source_id"]
    url = cand["url"]
    regulator = cand["regulator"]
    adapter_hint = cand.get("adapter_hint", "")
    base = {
        "source_id": source_id,
        "name": cand.get("title", source_id),
        "url": url,
        "jurisdiction": "AE",
        "category": "regulatory",
        "enabled": False,
        "baseline_runs_required": 2,
        "fetch_method": "playwright",
    }
    print(f"  [probe] {source_id} ...", flush=True)
    try:
        probe = run_source_intake(dict(base), all_sources=all_sources, write_evidence=False)
    except Exception as exc:
        print(f"  [PROBE ERROR] {exc}", flush=True)
        return {
            "source_id": source_id, "url": url, "regulator": regulator, "tier": cand["tier"],
            "title": cand.get("title", ""), "error": f"{type(exc).__name__}: {exc}"[:300],
            "probe": _empty(), "applied": None, "best": _empty(),
        }
    dom = probe.get("dom_investigation") or {}
    reco = str(dom.get("recommended_adapter_name") or dom.get("recommended_adapter_family") or "")
    # Use adapter_hint if DOM investigator gives no recommendation or gives generic
    effective_reco = reco if reco else adapter_hint
    fam_name = RECO_MAP.get(effective_reco)
    probe_summary = _summary_fields(probe)
    print(f"  [probe done] status={probe_summary['status']} q={probe_summary['quality_score']} reco={reco or 'none'}", flush=True)

    applied_summary = None
    if fam_name and not probe_summary["strong_pass"]:
        fam, name = fam_name
        cfg: dict = {}
        if dom.get("content_selector"):
            cfg["container_selector"] = dom.get("content_selector")
            cfg["content_selector"] = dom.get("content_selector")
        if dom.get("item_selector"):
            cfg["item_selector"] = dom.get("item_selector")
        src = dict(base)
        src["adapter_family"] = fam
        src["adapter_name"] = name
        src["adapter_config"] = cfg
        if dom.get("wait_selector"):
            src["wait_for_selector"] = dom.get("wait_selector")
        print(f"  [apply] {source_id} with adapter={name} ...", flush=True)
        try:
            applied = run_source_intake(src, all_sources=all_sources, write_evidence=False)
            applied_summary = _summary_fields(applied)
            applied_summary["adapter_config"] = cfg
            applied_summary["wait_for_selector"] = dom.get("wait_selector") or ""
            print(f"  [apply done] status={applied_summary['status']} q={applied_summary['quality_score']}", flush=True)
        except Exception as exc:
            applied_summary = _empty()
            applied_summary["error"] = f"apply_failed: {type(exc).__name__}: {exc}"[:300]
            print(f"  [APPLY ERROR] {exc}", flush=True)
    elif probe_summary["strong_pass"]:
        print(f"  [skip apply] probe already strong pass", flush=True)

    best = applied_summary if (applied_summary and applied_summary.get("strong_pass")) else probe_summary
    return {
        "source_id": source_id, "url": url, "regulator": regulator, "tier": cand["tier"],
        "title": cand.get("title", ""),
        "recommended_adapter": reco,
        "adapter_hint": adapter_hint,
        "probe": probe_summary,
        "applied": applied_summary,
        "best": best,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="1,2,3", help="Comma-separated tier numbers to run (1=high, 2=med, 3=low)")
    ap.add_argument("--out", default="/tmp/uae50_new_candidates.json")
    ap.add_argument("--delay", type=float, default=3.0, help="Seconds between tests")
    args = ap.parse_args()

    tiers = {int(t.strip()) for t in args.tier.split(",") if t.strip()}
    targets = [c for c in NEW_CANDIDATES if c["tier"] in tiers]
    print(f"UAE 50 new-candidate batch: {len(targets)} targets (tiers {sorted(tiers)})", flush=True)

    all_sources = load_sources_json()
    results = []
    strong_passes = []

    for i, cand in enumerate(targets, 1):
        print(f"\n[{i}/{len(targets)}] {cand['source_id']} tier={cand['tier']}", flush=True)
        result = test_candidate(cand, all_sources)
        results.append(result)
        if result.get("best", {}).get("strong_pass"):
            strong_passes.append(result)
            print(f"  *** STRONG PASS *** q={result['best']['quality_score']}", flush=True)
        if i < len(targets):
            time.sleep(args.delay)

    # Summary
    total = len(results)
    n_strong = len(strong_passes)
    n_nav_shell = sum(1 for r in results if r.get("best", {}).get("nav_shell") and not r.get("best", {}).get("strong_pass"))
    n_blocked = sum(1 for r in results if r.get("best", {}).get("status") in ("ACCESS_BLOCKED", "FETCH_FAILED"))
    n_error = sum(1 for r in results if "error" in r)

    summary = {
        "total_tested": total,
        "strong_passes": n_strong,
        "nav_shell_only": n_nav_shell,
        "blocked": n_blocked,
        "errors": n_error,
        "other_failures": total - n_strong - n_nav_shell - n_blocked - n_error,
        "strong_pass_ids": [r["source_id"] for r in strong_passes],
    }

    report = {"summary": summary, "strong_passes": strong_passes, "all_results": results}
    out_path = Path(args.out)
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\n=== BATCH COMPLETE ===")
    print(f"Tested: {total} | Strong: {n_strong} | NAV_SHELL: {n_nav_shell} | Blocked: {n_blocked} | Errors: {n_error}")
    print(f"Strong passes: {[r['source_id'] for r in strong_passes]}")
    print(f"Report: {out_path}")
    return 0 if True else 1


if __name__ == "__main__":
    sys.exit(main())
