"""Phase 0-D: portfolio tiering over all sources in sources.json.

Tiers (rules applied mechanically; every row carries its evidence):
  A            enabled + fresh_alert + alert_eligible, GOOD extraction seen,
               no restricted/failed access in last 5 runs
  B            enabled + eligible but only MEDIUM/low extraction, or PDF-only,
               or chrome contamination observed
  C            enabled but monitoring_mode in {candidate, evidence_library, None}
  REMEDIATION  enabled with recent FAILED/restricted runs, or status in
               {limited, remediation, disabled_path_moved}
  EXCLUDE-REV  disabled: non-UAE / duplicate / covered_by_hub / navigation_only
               / replaced — review before ever activating
  INACTIVE     remaining disabled sources (static pdf/doc, geo_blocked,
               needs_playwright, mapped, disabled) — activation candidates pool

Outputs docs/signal/portfolio.jsonl + summary counts.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

REAL = Path(
    os.environ.get(
        "REGRADAR_REAL_DIR",
        "/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar",
    )
)


def main() -> None:
    payload = json.loads((REAL / "sources.json").read_text(encoding="utf-8"))
    items = payload.get("sources", payload) if isinstance(payload, dict) else payload

    runs = []
    with open(REAL / "data/source_runs/source_runs.jsonl", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                runs.append(json.loads(line))
    hist: dict[str, list[dict]] = {}
    for r in runs:
        hist.setdefault(str(r.get("source_id")), []).append(r)
    for lst in hist.values():
        lst.sort(key=lambda r: str(r.get("timestamp_utc")))

    noise = {}
    na = Path("docs/signal/noise_anatomy.jsonl")
    if na.is_file():
        for line in na.read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            noise[d["source_id"]] = d

    rows = []
    for s in items:
        sid = s.get("source_id") or s.get("name")
        h = hist.get(str(sid), [])
        last5 = h[-5:]
        qual = Counter(str(r.get("extraction_quality")).upper() for r in h)
        acc = Counter(str(r.get("access_status")) for r in last5)
        ch = Counter(str(r.get("change_status")) for r in h)
        good_seen = qual.get("GOOD", 0) > 0
        recent_bad = acc.get("failed", 0) + acc.get("restricted", 0) > 0 or any(
            str(r.get("change_status")) == "FAILED" for r in last5
        )
        nz = noise.get(str(sid), {})
        status = str(s.get("status") or "")
        mode = str(s.get("monitoring_mode") or "None")
        eligible = mode == "fresh_alert" and s.get("alert_eligible") is True
        is_pdf = "pdf" in str(s.get("url", "")).lower() or "-pdf" in str(sid)

        if s.get("enabled"):
            if recent_bad or status in ("limited", "remediation"):
                tier = "REMEDIATION"
            elif not eligible:
                tier = "C"
            elif good_seen and not is_pdf and not nz.get("will_flip_on_clean"):
                tier = "A"
            else:
                tier = "B"
        else:
            if status in (
                "disabled_non_uae",
                "disabled_duplicate",
                "duplicate_url",
                "disabled_covered_by_hub",
                "disabled_navigation_only",
                "replaced",
            ):
                tier = "EXCLUDE-REVIEW"
            elif status in ("limited", "remediation", "disabled_path_moved"):
                tier = "REMEDIATION"
            else:
                tier = "INACTIVE-POOL"

        evidence_bits = []
        if h:
            evidence_bits.append(
                f"{len(h)} runs (CHANGED {ch.get('CHANGED',0)}, FAILED {ch.get('FAILED',0)}, QD {ch.get('QUALITY_DROP',0)})"
            )
            evidence_bits.append(f"qual GOOD:{qual.get('GOOD',0)}/MED:{qual.get('MEDIUM',0)}")
        else:
            evidence_bits.append("no runs recorded")
        if nz:
            evidence_bits.append(
                f"chrome {nz['chrome_lines']}+{nz['counter_lines']}cntr/{nz['lines']} lines"
            )
        if recent_bad:
            evidence_bits.append(f"recent access {dict(acc)}")

        rows.append(
            {
                "source_id": sid,
                "tier": tier,
                "enabled": bool(s.get("enabled")),
                "status": status,
                "monitoring_mode": mode,
                "alert_eligible": s.get("alert_eligible"),
                "category": s.get("category"),
                "is_pdf": is_pdf,
                "reason_fields": (
                    str(s.get("fresh_signal_reason") or s.get("notes") or "")[:160]
                ),
                "evidence": "; ".join(evidence_bits),
            }
        )

    Path("docs/signal/portfolio.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    print("total sources:", len(rows))
    print("tiers:", dict(Counter(r["tier"] for r in rows)))
    print("\n-- enabled-but-not-eligible (tier C), exact reasons --")
    for r in rows:
        if r["tier"] == "C":
            print(
                f"  {r['source_id'][:52]:52} mode={r['monitoring_mode']:<16} "
                f"elig={str(r['alert_eligible']):<5} | {r['reason_fields'][:80] or '(no reason field recorded)'}"
            )


if __name__ == "__main__":
    main()
