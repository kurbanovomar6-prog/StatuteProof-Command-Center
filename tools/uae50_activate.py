#!/usr/bin/env python3
"""Save evidence + repeat baseline for a single strong-pass UAE source.

Runs the real source-intake pipeline with write_evidence=True twice (or until the
required baseline run count is reached), persisting proof artifacts to
source_runs.jsonl. Then reports the certification status, proof_path, completed
baseline count, and hash stability. It does NOT touch sources.json and does NOT
send alerts. Activation into sources.json is a separate, gated step.

Usage:
  python3 tools/uae50_activate.py --source-id AE-x --url https://... \
      --name "..." --adapter-family listing --adapter-name listing \
      --adapter-config-json '{"container_selector":"main","item_selector":"..."}' \
      --wait-for-selector main --runs 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "product" / "regradar"
sys.path.insert(0, str(PRODUCT))

from app.source_intake import run_source_intake, load_sources_json  # noqa: E402
from app.source_certification import build_certification_from_runs  # noqa: E402
from app.source_runs import _read_runs  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--jurisdiction", default="AE")
    ap.add_argument("--category", default="regulatory")
    ap.add_argument("--adapter-family", default="")
    ap.add_argument("--adapter-name", default="")
    ap.add_argument("--adapter-config-json", default="{}")
    ap.add_argument("--wait-for-selector", default="")
    ap.add_argument("--content-selector", default="")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--baseline-required", type=int, default=2)
    args = ap.parse_args()

    cfg = json.loads(args.adapter_config_json) if args.adapter_config_json else {}
    source = {
        "source_id": args.source_id,
        "name": args.name or args.source_id,
        "url": args.url,
        "jurisdiction": args.jurisdiction,
        "category": args.category,
        "enabled": False,
        "fetch_method": "playwright",
        "baseline_runs_required": args.baseline_required,
    }
    if args.adapter_family:
        source["adapter_family"] = args.adapter_family
    if args.adapter_name:
        source["adapter_name"] = args.adapter_name
    if cfg:
        source["adapter_config"] = cfg
    if args.wait_for_selector:
        source["wait_for_selector"] = args.wait_for_selector
    if args.content_selector:
        source["content_selector"] = args.content_selector

    all_sources = load_sources_json()
    run_results = []
    for n in range(1, args.runs + 1):
        print(f"[run {n}/{args.runs}] saving evidence for {args.source_id}", file=sys.stderr)
        res = run_source_intake(dict(source), all_sources=all_sources, write_evidence=True)
        run_results.append({
            "status": res.get("status"),
            "quality_score": res.get("quality_score"),
            "normalized_hash": res.get("normalized_hash"),
            "normalized_length": res.get("chars_normalized"),
            "evidence_written": res.get("evidence_written"),
            "proof_path": res.get("proof_path"),
            "can_save_evidence": res.get("can_save_evidence"),
            "adapter_used": res.get("adapter_used"),
            "noise_risk": res.get("noise_risk"),
            "source_health_risk": res.get("source_health_risk"),
        })

    runs = _read_runs()
    cert = build_certification_from_runs(
        source_id=args.source_id,
        source_url=args.url,
        runs=runs,
        baseline_runs_required=args.baseline_required,
        quality_score=int(run_results[-1].get("quality_score") or 0),
    )
    hashes = cert.get("hash_history", [])
    stable = len(set(hashes)) == 1 if hashes else False
    out = {
        "source_id": args.source_id,
        "url": args.url,
        "run_results": run_results,
        "certification_status": cert.get("certification_status"),
        "baseline_runs_completed": cert.get("baseline_runs_completed"),
        "baseline_runs_required": cert.get("baseline_runs_required"),
        "proof_paths": cert.get("proof_paths", []),
        "proof_path": (cert.get("proof_paths") or [None])[0],
        "hash_history": hashes,
        "hash_stable": stable,
        "evidence_level": cert.get("evidence_level"),
        "certification_score": cert.get("certification_score"),
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
