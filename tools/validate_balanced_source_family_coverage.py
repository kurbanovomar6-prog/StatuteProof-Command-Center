#!/usr/bin/env python3
"""Validate UAE source family scorecard and balanced coverage honesty."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "product/regradar/config/uae_1000_source_universe_candidates.json"
TOP250 = ROOT / "product/regradar/config/uae_top_250_activation_queue.json"
SCORECARD = ROOT / "docs/uae-source-family-scorecard.md"
FINAL_REPORT = ROOT / "docs/uae-1000-source-expansion-final-report.md"

EXPECTED_FAMILIES = {
    "CBUAE",
    "DFSA",
    "DIFC",
    "ADGM/FSRA",
    "VARA",
    "SCA",
    "UAE FIU",
    "EOCN / sanctions / TFS",
    "FTA / Tax",
    "Ministry of Economy / DNFBP AML",
    "Ministry of Justice / UAE Legislation / Gazette",
    "UAE Data Office / PDPL / privacy",
    "Ministry of Finance",
    "Cabinet / Federal decrees",
    "DFM",
    "ADX",
    "Nasdaq Dubai",
    "DMCC",
    "Dubai Economy / DET",
    "Abu Dhabi DED",
    "Customs / FCA / Dubai Customs",
    "UAE courts / DIFC Courts / ADGM Courts",
    "Insurance / health insurance / pensions",
    "Cyber/security official advisories",
    "Other UAE free zones with regulatory relevance",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    errors: list[str] = []
    if not UNIVERSE.exists():
        errors.append("Missing UAE 1000-source universe file")
    if not TOP250.exists():
        errors.append("Missing top-250 queue")
    if not SCORECARD.exists():
        errors.append("Missing source-family scorecard")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    universe = load_json(UNIVERSE)
    top = load_json(TOP250)
    candidates = universe.get("candidates") or []
    rejected = universe.get("rejected") or []
    top_queue = top.get("top_250_activation_queue") or []
    score_text = SCORECARD.read_text(encoding="utf-8", errors="ignore")
    final_text = FINAL_REPORT.read_text(encoding="utf-8", errors="ignore") if FINAL_REPORT.exists() else ""

    families_seen = {row.get("source_family") for row in candidates if isinstance(row, dict)}
    families_seen |= {row.get("source_family") for row in rejected if isinstance(row, dict)}
    missing = sorted(EXPECTED_FAMILIES - families_seen)
    if missing:
        errors.append("Universe missing expected families: " + ", ".join(missing))

    top_families = {row.get("source_family") for row in top_queue if isinstance(row, dict)}
    weak_targets = {"FTA / Tax", "SCA", "UAE FIU", "EOCN / sanctions / TFS", "Ministry of Economy / DNFBP AML"}
    absent_weak = sorted(weak_targets - top_families)
    if absent_weak:
        errors.append("Top-250 queue missing weak-family targets: " + ", ".join(absent_weak))

    for family in EXPECTED_FAMILIES:
        if family not in score_text:
            errors.append(f"Scorecard missing family row: {family}")

    strong_rows = [
        line for line in score_text.splitlines()
        if "| Strong |" in line and not re.search(r"\|\s*(2[0-9]|[3-9][0-9])\s*\|", line)
    ]
    if strong_rows:
        errors.append("Scorecard may label a family Strong without 20+ active endpoints.")

    lower_final = final_text.lower()
    for forbidden in ("complete uae coverage", "guaranteed compliance", "perfect parsing", "never miss updates"):
        if forbidden in lower_final:
            errors.append(f"Final universe report contains forbidden phrase: {forbidden}")

    if "sources activated in this mapping phase: 0" not in lower_final:
        errors.append("Final universe report must state that zero sources were activated in mapping phase.")
    if "fta" in lower_final and "25 proof-backed fta" not in lower_final:
        errors.append("Final universe report should disclose the later 25 proof-backed FTA activation.")

    if errors:
        for error in errors[:80]:
            print(f"ERROR: {error}")
        if len(errors) > 80:
            print(f"ERROR: {len(errors) - 80} additional errors omitted")
        return 1

    print("Balanced source family coverage validation PASSED")
    print(f"- Families represented: {len(families_seen)}")
    print(f"- Top-250 families represented: {len(top_families)}")
    print("- Scorecard and final report preserve candidate-vs-active distinction")
    return 0


if __name__ == "__main__":
    sys.exit(main())
