"""Phase 0-A: replay the current risk rubric over all historical CHANGED runs.

Reads the REAL evidence trail read-only (path via REGRADAR_REAL_DIR, default
the primary checkout) and replays: prev normalized snapshot vs new normalized
snapshot -> get_diff -> analyze_risk. Compares the replayed verdict with the
risk_level recorded at run time, and dumps the actual delta text per run so a
human can judge every disagreement.

Output: JSON lines to stdout (one per CHANGED run) + a summary table.
Never writes to the real trail.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.diff import get_diff  # noqa: E402
from app.risk import analyze_risk  # noqa: E402

REAL = Path(
    os.environ.get(
        "REGRADAR_REAL_DIR",
        "/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar",
    )
)


def load_runs() -> list[dict]:
    runs = []
    with open(REAL / "data/source_runs/source_runs.jsonl", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                runs.append(json.loads(line))
    return runs


def main() -> None:
    runs = load_runs()
    by_source: dict[str, list[dict]] = {}
    for r in runs:
        by_source.setdefault(r["source_id"], []).append(r)
    for lst in by_source.values():
        lst.sort(key=lambda r: r["timestamp_utc"])

    changed = [r for r in runs if r.get("change_status") == "CHANGED"]
    changed.sort(key=lambda r: r["timestamp_utc"])

    rows = []
    for r in changed:
        prevs = [
            p
            for p in by_source[r["source_id"]]
            if p["timestamp_utc"] < r["timestamp_utc"]
            and p.get("snapshot_normalized_path")
        ]
        row: dict = {
            "source_id": r["source_id"],
            "ts": r["timestamp_utc"][:19],
            "run_id": r.get("run_id"),
            "recorded_risk": r.get("risk_level"),
            "recorded_reason": (r.get("risk_reason") or "")[:120],
        }
        new_p = r.get("snapshot_normalized_path")
        if not prevs or not new_p:
            row["replay"] = "NOT_REPLAYABLE"
            rows.append(row)
            continue
        old_f = REAL / prevs[-1]["snapshot_normalized_path"]
        new_f = REAL / new_p
        if not old_f.is_file() or not new_f.is_file():
            row["replay"] = "SNAPSHOT_MISSING"
            rows.append(row)
            continue
        old_text = old_f.read_text(encoding="utf-8")
        new_text = new_f.read_text(encoding="utf-8")
        d = get_diff(old_text, new_text)
        risk = analyze_risk(d)
        row.update(
            {
                "replay": "OK",
                "prev_run_id": prevs[-1].get("run_id"),
                "replayed_risk": risk["risk_level"],
                "rule": risk.get("rule"),
                "matched": risk.get("matched_keywords"),
                "added_n": len(d["added"]),
                "removed_n": len(d["removed"]),
                "added_chars": sum(len(a) for a in d["added"]),
                "removed_chars": sum(len(x) for x in d["removed"]),
                "added_text": " || ".join(d["added"])[:1500],
                "removed_text": " || ".join(d["removed"])[:1500],
            }
        )
        rows.append(row)

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    if out:
        out.write_text(payload + "\n", encoding="utf-8")

    # summary
    ok = [r for r in rows if r.get("replay") == "OK"]
    agree = sum(1 for r in ok if r["replayed_risk"] == r["recorded_risk"])
    print(f"CHANGED runs: {len(rows)}; replayed: {len(ok)}; verdict-identical: {agree}")
    from collections import Counter

    print("recorded :", dict(Counter(r["recorded_risk"] for r in rows)))
    print("replayed :", dict(Counter(r.get("replayed_risk") for r in ok)))
    dis = [r for r in ok if r["replayed_risk"] != r["recorded_risk"]]
    for r in dis:
        print(
            f"DISAGREE {r['source_id']} {r['ts']} recorded={r['recorded_risk']} "
            f"replayed={r['replayed_risk']} rule={r.get('rule')}"
        )


if __name__ == "__main__":
    main()
