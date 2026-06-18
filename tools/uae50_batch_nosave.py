#!/usr/bin/env python3
"""Honest batch no-save harness for the UAE 50-source activation sprint.

For each candidate it runs the real source-intake pipeline twice:
  1. probe pass (Playwright render, no adapter) to obtain the Auto DOM
     Investigator's recommended adapter family/name and selectors;
  2. apply pass with that recommended adapter, recording the genuine no-save
     outcome (quality, nav-shell, can_save_evidence, failure code, etc.).

It never writes evidence (write_evidence=False), never sends alerts, never
mutates sources.json, and tests one source at a time. Output is a JSON report.

Usage:
  python3 tools/uae50_batch_nosave.py --from-work-queue --states candidate,remediation,baseline_pending --limit 20
  python3 tools/uae50_batch_nosave.py --url https://... --source-id AE-x --regulator SCA
"""
from __future__ import annotations

import argparse
import json
import sys
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

WORK_QUEUE = PRODUCT / "config" / "uae_source_work_queue.json"

# DOM-recommended family/name -> (adapter_family, adapter_name)
RECO_MAP = {
    "listing": ("listing", "listing"),
    "table": ("table", "table"),
    "register": ("register", "register"),
    "rulebook": ("rulebook", "dfsa_rulebook"),
    "dfsa_rulebook": ("rulebook", "dfsa_rulebook"),
    "document_listing": ("document_listing", "cbuae_document_listing"),
    "pdf_listing": ("pdf_listing", "pdf_listing"),
    "pdf_document": ("pdf_document", "pdf_document"),
    "custom_element": ("custom_element", "custom_element"),
    "static_html": ("static_html", "static_html"),
    "sitemap_feed": ("sitemap_feed", "sitemap_feed"),
    "public_json_api": ("public_json_api", "public_json_api"),
    "fta_tax_listing": ("fta_tax_listing", "fta_tax_listing"),
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
        "hash_collision": bool(result.get("hash_collision")),
        "noise_risk": result.get("noise_risk"),
        "source_health_risk": result.get("source_health_risk"),
        "can_save_evidence": bool(result.get("can_save_evidence")),
        "adapter_used": bool(result.get("adapter_used")),
        "adapter_name": result.get("adapter_name") or "",
        "adapter_family": result.get("adapter_family") or "",
        "failure_code": classify_failure_code(result) if status != "CONFIRMED_ACCESSIBLE" else "",
        "strong_pass": strong,
    }


def test_candidate(source_id: str, url: str, regulator: str, all_sources: list) -> dict:
    base = {
        "source_id": source_id,
        "name": source_id,
        "url": url,
        "jurisdiction": "AE",
        "category": "regulatory",
        "enabled": False,
        "baseline_runs_required": 2,
        "fetch_method": "playwright",
    }
    # Pass 1 — probe (no adapter) to read DOM investigator recommendation.
    try:
        probe = run_source_intake(dict(base), all_sources=all_sources, write_evidence=False)
    except Exception as exc:  # network/render failure is a real, recorded outcome
        return {
            "source_id": source_id, "url": url, "regulator": regulator,
            "error": f"probe_failed: {type(exc).__name__}: {exc}"[:300],
            "recommended": "", "applied": _empty(), "best": _empty(),
        }
    dom = probe.get("dom_investigation") or {}
    reco = str(dom.get("recommended_adapter_name") or dom.get("recommended_adapter_family") or "")
    fam_name = RECO_MAP.get(reco)
    probe_summary = _summary_fields(probe)

    applied_summary = None
    if fam_name:
        fam, name = fam_name
        cfg = {}
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
        try:
            applied = run_source_intake(src, all_sources=all_sources, write_evidence=False)
            applied_summary = _summary_fields(applied)
            applied_summary["adapter_config"] = cfg
            applied_summary["wait_for_selector"] = dom.get("wait_selector") or ""
        except Exception as exc:
            applied_summary = _empty()
            applied_summary["error"] = f"apply_failed: {type(exc).__name__}: {exc}"[:300]

    # Best = applied if it is a strong pass, else probe.
    best = applied_summary if (applied_summary and applied_summary.get("strong_pass")) else probe_summary
    return {
        "source_id": source_id,
        "url": url,
        "regulator": regulator,
        "recommended_adapter": reco,
        "detected_page_type": dom.get("detected_page_type"),
        "selector_confidence": dom.get("selector_confidence"),
        "probe": probe_summary,
        "applied": applied_summary,
        "best": best,
    }


def _empty() -> dict:
    return {"status": "", "strong_pass": False, "can_save_evidence": False}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-work-queue", action="store_true")
    ap.add_argument("--states", default="candidate,remediation,baseline_pending")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--regulator", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--source-id", default="source-lab")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    all_sources = load_sources_json()
    targets: list[tuple[str, str, str]] = []

    if args.url:
        targets.append((args.source_id, args.url, args.regulator or "manual"))
    elif args.from_work_queue:
        data = json.loads(WORK_QUEUE.read_text(encoding="utf-8"))
        states = {s.strip() for s in args.states.split(",") if s.strip()}
        seen_urls = set()
        for s in data.get("sources", []):
            if s.get("activation_decision") not in states:
                continue
            reg = str(s.get("regulator") or "")
            if args.regulator and args.regulator.lower() not in reg.lower():
                continue
            url = str(s.get("url") or "")
            if not url.startswith("https://") or url in seen_urls:
                continue
            seen_urls.add(url)
            targets.append((str(s.get("source_id")), url, reg))
    else:
        ap.error("Provide --url or --from-work-queue")

    targets = targets[: args.limit]
    results = []
    strong = []
    for i, (sid, url, reg) in enumerate(targets, start=1):
        print(f"[{i}/{len(targets)}] {sid} :: {url}", file=sys.stderr)
        r = test_candidate(sid, url, reg, all_sources)
        results.append(r)
        if r.get("best", {}).get("strong_pass"):
            strong.append(sid)
            print(f"    STRONG PASS via {r['best'].get('adapter_name') or 'generic'} q={r['best'].get('quality_score')}", file=sys.stderr)
        else:
            fc = r.get("best", {}).get("failure_code") or r.get("error", "")
            print(f"    no pass ({fc})", file=sys.stderr)

    report = {
        "tested_count": len(results),
        "strong_pass_count": len(strong),
        "strong_pass_ids": strong,
        "results": results,
    }
    out = json.dumps(report, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(out)
    print(f"\nSUMMARY: {len(strong)}/{len(results)} strong no-save passes: {strong}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
