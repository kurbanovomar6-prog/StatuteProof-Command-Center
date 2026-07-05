"""Phase 0-C: per-source nav/chrome contamination of normalized snapshots.

For every source's latest normalized snapshot, measure:
  - chrome_marker_lines: lines matching known page-chrome markers observed in
    the real trail (nav labels, theme/rating widgets, cookie banners,
    carousel counters, language switch, visitor counters)
  - navlike_lines: short link-label lines (<= 40 chars, no sentence
    punctuation, not numeric data)
  - volatile_counter_lines: lines with visitor/rating counters

Chrome fraction = (chrome_marker + volatile) lines / total lines.
Sources with any chrome/volatile hit will flip their baseline hash when
extraction is cleaned — that sizes the future coordinated reset.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

REAL = Path(
    os.environ.get(
        "REGRADAR_REAL_DIR",
        "/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar",
    )
)

# Every marker below was observed verbatim in the real 63-delta judgment pass.
CHROME_MARKERS = [
    r"^(about us|go back|who we are|what we do|our structure|careers?|overview)$",
    r"^(jurisdiction|authorities|initiatives|dispute resolution)$",
    r"theme color #|color blind mode|night reading mode",
    r"default switch checkbox input",
    r"rate this page|rated by [\d,]+ people|thanks for rating",
    r"قُ?يّ?مت الصفحة من قبل|شكراً على التقيّم|قيّم هذه الصفحة",
    r"^skip to (main )?content",
    r"we use cookies|this site uses cookies|cookie",
    r"^(read more|اقرأ المزيد)$",
    r"^\d+/\d+$",  # carousel position
    r"popular search|advanced search|search in the website",
    r"^(english|عربي|عربى)$|^a a a ",
    r"breadcrumb|مسار التنقل",
    r"^(latest news|أخبار)$",
    r"follow us|social media|linkedin|twitter|youtube|instagram",
    r"^(home|الصفحة الرئيسية|الرئيسية)\b",
    r"your ip:|cloudflare ray id|performance & security by cloudflare",
    r"sorry .*we couldn.t find|bad gateway|page not found|404",
    r"عدد الزوار|اخر تعديل للموقع",
    r"^(login|sign in|register)$",
]
CHROME_RE = re.compile("|".join(CHROME_MARKERS), re.IGNORECASE)

COUNTER_RE = re.compile(
    r"rated by\s*[\d,]+|من قبلِ?\s*[\d,]+\s*مستخدم|عدد الزوار\s*:?\s*[\d,]+", re.I
)

SENTENCE_PUNCT = re.compile(r"[.:;!?،۔]|\d")


def navlike(line: str) -> bool:
    s = line.strip()
    return 0 < len(s) <= 40 and not SENTENCE_PUNCT.search(s)


def main() -> None:
    runs = []
    with open(REAL / "data/source_runs/source_runs.jsonl", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                runs.append(json.loads(line))
    latest: dict[str, str] = {}
    for r in runs:
        p = r.get("snapshot_normalized_path")
        if p:
            latest[r["source_id"]] = p

    rows = []
    for sid, p in sorted(latest.items()):
        f = REAL / p
        if not f.is_file():
            continue
        lines = [ln for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if not lines:
            continue
        chrome = sum(1 for ln in lines if CHROME_RE.search(ln))
        counters = sum(1 for ln in lines if COUNTER_RE.search(ln))
        nav = sum(1 for ln in lines if navlike(ln))
        frac = (chrome + counters) / len(lines)
        rows.append(
            {
                "source_id": sid,
                "lines": len(lines),
                "chrome_lines": chrome,
                "counter_lines": counters,
                "navlike_lines": nav,
                "chrome_frac": round(frac, 3),
                "will_flip_on_clean": chrome + counters > 0,
            }
        )

    rows.sort(key=lambda r: -r["chrome_frac"])
    flip = sum(1 for r in rows if r["will_flip_on_clean"])
    print(f"sources with latest snapshot: {len(rows)}")
    print(f"sources with >=1 chrome/counter line (baseline flips on clean): {flip}")
    print(f"{'source_id':58} {'lines':>5} {'chrome':>6} {'cntr':>4} {'nav':>5} {'frac':>6}")
    for r in rows[:40]:
        print(
            f"{r['source_id'][:58]:58} {r['lines']:>5} {r['chrome_lines']:>6} "
            f"{r['counter_lines']:>4} {r['navlike_lines']:>5} {r['chrome_frac']:>6}"
        )
    Path("docs/signal/noise_anatomy.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
