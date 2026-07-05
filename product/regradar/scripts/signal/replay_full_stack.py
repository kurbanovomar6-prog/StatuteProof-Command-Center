"""Full-stack replay: error-page gate → v2 normalization → diff → risk.

This is what production computes after F1+F3(+F4). Run over every
historical CHANGED run; used as the severity regression harness: verdict
shifts must be justified by the judgment class
(scripts/signal/judgment_table.py), never silent.

Usage: python3 scripts/signal/replay_full_stack.py [out.jsonl]
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.diff import get_diff  # noqa: E402
from app.risk import analyze_risk  # noqa: E402
from app.text_normalization import (  # noqa: E402
    looks_like_error_page,
    normalize_for_change_hash,
    stable_content_hash,
)

REAL = Path(
    os.environ.get(
        "REGRADAR_REAL_DIR",
        "/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar",
    )
)


def main() -> None:
    runs = [
        json.loads(line)
        for line in open(REAL / "data/source_runs/source_runs.jsonl", encoding="utf-8")
        if line.strip()
    ]
    by_source: dict[str, list[dict]] = {}
    for r in runs:
        by_source.setdefault(r["source_id"], []).append(r)
    for lst in by_source.values():
        lst.sort(key=lambda r: r["timestamp_utc"])

    rows = []
    for r in runs:
        if r.get("change_status") != "CHANGED" or not r.get("snapshot_normalized_path"):
            continue
        prevs = [
            p
            for p in by_source[r["source_id"]]
            if p["timestamp_utc"] < r["timestamp_utc"]
            and p.get("snapshot_normalized_path")
        ]
        if not prevs:
            continue
        old_f = REAL / prevs[-1]["snapshot_normalized_path"]
        new_f = REAL / r["snapshot_normalized_path"]
        if not (old_f.is_file() and new_f.is_file()):
            continue
        old_raw, new_raw = old_f.read_text(encoding="utf-8"), new_f.read_text(encoding="utf-8")
        row = {"source_id": r["source_id"], "ts": r["timestamp_utc"][:19]}
        if looks_like_error_page(new_raw) or looks_like_error_page(old_raw):
            row["outcome"] = "ERROR_PAGE_FILTERED"
            rows.append(row)
            continue
        old, new = normalize_for_change_hash(old_raw), normalize_for_change_hash(new_raw)
        if stable_content_hash(old) == stable_content_hash(new):
            row["outcome"] = "NO_DIFF"
            rows.append(row)
            continue
        d = get_diff(old, new)
        if not d["has_changes"]:
            row["outcome"] = "NO_DIFF"
            rows.append(row)
            continue
        risk = analyze_risk(d)
        row.update(
            {
                "outcome": risk["risk_level"],
                "rule": risk.get("rule"),
                "matched": risk.get("matched_keywords"),
                "delta_added": " || ".join(d["added"])[:600],
            }
        )
        rows.append(row)

    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(
            "\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n",
            encoding="utf-8",
        )
    print("full-stack outcomes:", dict(Counter(x["outcome"] for x in rows).most_common()))
    for x in rows:
        if x["outcome"] == "HIGH":
            print(f"HIGH {x['source_id'][:50]:50} {x['ts'][:16]} matched={x['matched']}")


if __name__ == "__main__":
    main()
