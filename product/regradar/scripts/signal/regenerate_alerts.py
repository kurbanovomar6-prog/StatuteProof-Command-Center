"""Verification gate: regenerate 3 historical alerts through the full new
stack, before/after side by side.

Cases:
  A/B — the two 2026-07-05 DFSA title-flip runs (recorded HIGH, queued).
  C1  — closest real genuine-ish change: UAEFIU publications count 61→62
        (2026-06-11T22:33).
  C2  — SYNTHETIC genuine regulatory change (clearly labeled SAMPLE/FAKE):
        a real DFSA snapshot plus one invented circular paragraph, to prove
        the positive path end-to-end (severity + detected facts render).

Reads the real trail read-only. Writes docs/signal/ALERT_REGENERATION.md.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.alert_content import build_alert_content, render_markdown, render_telegram
from app.detected_facts import extract_detected_facts
from app.diff import get_diff
from app.risk import analyze_risk
from app.text_normalization import (
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

OUT: list[str] = []


def w(line: str = "") -> None:
    OUT.append(line)


def load_runs() -> list[dict]:
    return [
        json.loads(line)
        for line in open(REAL / "data/source_runs/source_runs.jsonl", encoding="utf-8")
        if line.strip()
    ]


def new_stack(old_text: str, new_text: str, source_name: str, url: str, checked: str) -> tuple[str, dict | None]:
    """Run the full new stack; return (outcome, alert_content or None)."""
    if looks_like_error_page(new_text) or looks_like_error_page(old_text):
        return "FAILED (error page rejected — no baseline, no alert)", None
    o, n = normalize_for_change_hash(old_text), normalize_for_change_hash(new_text)
    if stable_content_hash(o) == stable_content_hash(n):
        return "UNCHANGED (hashes equal after v2 normalization — heartbeat, NO customer alert)", None
    d = get_diff(o, n)
    if not d["has_changes"]:
        return "UNCHANGED (no diff blocks — NO customer alert)", None
    risk = analyze_risk(d)
    facts = extract_detected_facts(d["added"])
    payload = {
        "url": url,
        "source_name": source_name,
        "jurisdiction": "AE",
        "risk_level": risk["risk_level"],
        "risk_reason": risk["reason"],
        "risk_details": risk,
        "added": d["added"],
        "removed": d["removed"],
        "detected_facts": facts,
        "checked_at_utc": checked,
    }
    return f"{risk['risk_level']} (rule {risk.get('rule')})", build_alert_content(payload)


def main() -> None:
    runs = load_runs()
    by_source: dict[str, list[dict]] = {}
    for r in runs:
        by_source.setdefault(r["source_id"], []).append(r)
    for lst in by_source.values():
        lst.sort(key=lambda r: r["timestamp_utc"])

    w("# ALERT_REGENERATION — verification gate (signal-max)")
    w()

    # ── Cases A/B: title flips ────────────────────────────────────────────
    flips = [
        r
        for r in by_source["AE-dfsa-financial-crime-mlro-letters"]
        if r["timestamp_utc"].startswith("2026-07-05") and r.get("change_status") == "CHANGED"
    ]
    for i, r in enumerate(flips, start=1):
        prevs = [
            p
            for p in by_source[r["source_id"]]
            if p["timestamp_utc"] < r["timestamp_utc"] and p.get("snapshot_normalized_path")
        ]
        old = (REAL / prevs[-1]["snapshot_normalized_path"]).read_text(encoding="utf-8")
        new = (REAL / r["snapshot_normalized_path"]).read_text(encoding="utf-8")
        w(f"## Case {'AB'[i-1]} — DFSA title flip {r['timestamp_utc'][:16]} (run {r['run_id']})")
        w()
        w("**BEFORE (what the old stack actually did, from the real trail):**")
        w(f"- change_status=CHANGED, risk_level={r.get('risk_level')}")
        w(f"- risk_reason: {str(r.get('risk_reason'))[:200]}")
        w(f"- alert queued: data/alert_queue/…-{r['run_id']}-*.json (status PENDING_REVIEW)")
        w()
        outcome, content = new_stack(old, new, r.get("source_name",""), r.get("url") or r.get("official_url",""), r["timestamp_utc"])
        w(f"**AFTER (full new stack):** {outcome}")
        assert content is None, "title flip must not produce an alert"
        w()

    # ── Case C1: closest real genuine-ish change ─────────────────────────
    src = "AE-uae-financial-intelligence-unit-uaefiu"
    run = [
        r
        for r in by_source[src]
        if r["timestamp_utc"].startswith("2026-06-11") and r.get("change_status") == "CHANGED"
    ][0]
    prevs = [
        p
        for p in by_source[src]
        if p["timestamp_utc"] < run["timestamp_utc"] and p.get("snapshot_normalized_path")
    ]
    old = (REAL / prevs[-1]["snapshot_normalized_path"]).read_text(encoding="utf-8")
    new = (REAL / run["snapshot_normalized_path"]).read_text(encoding="utf-8")
    w(f"## Case C1 — UAEFIU publications count 61→62 ({run['timestamp_utc'][:16]})")
    w()
    w("The closest thing to a genuine change in the whole trail: the FIU")
    w("publications facet count incremented (a new publication). Honest")
    w("expectation: metadata-level, small delta.")
    w()
    w(f"**BEFORE:** change_status=CHANGED, risk_level={run.get('risk_level')} (none recorded at run time)")
    outcome, content = new_stack(old, new, run.get("source_name",""), run.get("url") or run.get("official_url",""), run["timestamp_utc"])
    w(f"**AFTER (full new stack):** {outcome}")
    if content:
        w()
        w("Rendered Telegram body:")
        w("```")
        w(render_telegram(content))
        w("```")
    w()

    # ── Case C2: synthetic genuine change on a real snapshot ─────────────
    w("## Case C2 — SYNTHETIC genuine regulatory change (SAMPLE / FAKE)")
    w()
    w("**SAMPLE / FAKE — the appended circular below is invented for the")
    w("verification gate; the base page is the real DFSA snapshot.** History")
    w("contains no unambiguous genuine regulatory change to replay (Phase-0")
    w("finding), so the positive path is proven on labeled synthetic content.")
    w()
    base = (REAL / flips[-1]["snapshot_normalized_path"]).read_text(encoding="utf-8")
    synthetic = (
        "Circular No. 12 of 2026 — Sanctions Screening Remediation.\n"
        "Licensed firms must complete sanctions screening remediation no later "
        "than 30 September 2026. A penalty of AED 250,000 applies under "
        "Federal Decree-Law No. (20) of 2018. Effective from 15 August 2026."
    )
    new_synth = base + "\n\n" + synthetic
    outcome, content = new_stack(base, new_synth, "DFSA Financial Crime Prevention Notices and MLRO Letters", (flips[-1].get("url") or flips[-1].get("official_url","")), "2026-07-06T12:00:00+00:00")
    w(f"**AFTER (full new stack):** {outcome}")
    assert content is not None
    w()
    w("Rendered Telegram body (SAMPLE / FAKE):")
    w("```")
    w(render_telegram(content))
    w("```")
    w()
    w("Rendered email/markdown body (SAMPLE / FAKE):")
    w("```")
    w(render_markdown(content))
    w("```")

    out = Path("docs/signal/ALERT_REGENERATION.md")
    out.write_text("\n".join(OUT) + "\n", encoding="utf-8")
    print("\n".join(OUT))


if __name__ == "__main__":
    main()
