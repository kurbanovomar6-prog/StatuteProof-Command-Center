"""Phase 0-A: emit the per-run human-judgment table as markdown.

The CLASS mapping below is the reviewer's manual classification of every
replayable CHANGED run, made by reading the actual delta text
(docs/signal/replay_severity.jsonl). Keys: (source_id, ts-prefix).
Classes:
  TITLE_FLIP        site <title>/tagline toggles between two variants
  COUNTER           visitor/rating counter increments
  LANG_FLAP         same URL served AR vs EN between runs
  ERROR_PAGE        404/502 error page hashed as baseline or its recovery
  ADAPTER_FORMAT    extraction adapter output format switched/enriched
  PDF_REFLOW        PDF extractor version change re-flowed identical document
  WRONG_PAGE        fetch landed on homepage/redirect instead of target
  CHROME_SHUFFLE    nav/carousel/banner rotation, service-list reshuffle
  COUNT_CHANGE      listing/category count changed (possible genuine signal)
  REBRAND           real-world rename visible in chrome (weak genuine)
"""
from __future__ import annotations

import json

CLASS: dict[tuple[str, str], str] = {
    ("AE-uae-ministry-of-economy", "2026-05-30T12:05"): "CHROME_SHUFFLE",
    ("AE-central-bank-of-the-uae", "2026-05-30T12:06"): "COUNTER",
    ("AE-dubai-virtual-assets-regulatory-authority-vara", "2026-05-30T12:06"): "CHROME_SHUFFLE",
    ("AE-dubai-financial-services-authority-dfsa", "2026-05-30T12:06"): "CHROME_SHUFFLE",
    ("AE-uae-ministry-of-finance", "2026-05-30T12:09"): "CHROME_SHUFFLE",
    ("AE-uae-legislation-portal", "2026-05-30T12:10"): "CHROME_SHUFFLE",
    ("AE-uae-financial-intelligence-unit-uaefiu", "2026-05-30T12:10"): "COUNTER",
    ("AE-difc-laws-and-regulations", "2026-05-30T12:10"): "CHROME_SHUFFLE",
    ("AE-uae-ministry-of-economy", "2026-05-30T12:10"): "CHROME_SHUFFLE",
    ("AE-uae-legislation-portal", "2026-05-30T12:14"): "CHROME_SHUFFLE",
    ("AE-uae-legislation-portal", "2026-05-30T12:19"): "CHROME_SHUFFLE",
    ("AE-uae-legislation-portal", "2026-05-30T12:24"): "COUNT_CHANGE",
    ("AE-uae-legislation-portal", "2026-05-30T16:09"): "COUNT_CHANGE",
    ("AE-central-bank-of-the-uae", "2026-06-11T22:28"): "COUNTER",
    ("AE-dubai-financial-services-authority-dfsa", "2026-06-11T22:29"): "CHROME_SHUFFLE",
    ("AE-uae-ministry-of-finance", "2026-06-11T22:32"): "CHROME_SHUFFLE",
    ("AE-uae-financial-intelligence-unit-uaefiu", "2026-06-11T22:33"): "COUNT_CHANGE",
    ("AE-uae-ministry-of-economy", "2026-06-11T22:33"): "LANG_FLAP",
    ("AE-dubai-virtual-assets-regulatory-authority-vara", "2026-06-11T22:44"): "ERROR_PAGE",
    ("AE-uae-legislation-portal", "2026-06-11T22:48"): "ERROR_PAGE",
    ("AE-uae-ministry-of-economy", "2026-06-11T22:49"): "CHROME_SHUFFLE",
    ("AE-central-bank-of-the-uae", "2026-06-12T12:54"): "COUNTER",
    ("AE-dubai-virtual-assets-regulatory-authority-vara", "2026-06-12T12:54"): "CHROME_SHUFFLE",
    ("AE-uae-ministry-of-economy", "2026-06-12T13:14"): "REBRAND",
    ("AE-cbuae-regulations", "2026-06-12T13:14"): "COUNTER",
    ("AE-cbuae-circulars", "2026-06-12T13:15"): "COUNTER",
    ("AE-adgm-fsra-financial-crime-prevention", "2026-06-15T12:56"): "WRONG_PAGE",
    ("AE-adgm-fsra-rulebooks", "2026-06-15T13:07"): "WRONG_PAGE",
    ("AE-dfsa-aml-rulebook-module", "2026-06-15T13:22"): "CHROME_SHUFFLE",
    ("AE-uaefiu-typology-reports", "2026-06-15T17:37"): "ADAPTER_FORMAT",
    ("AE-dubai-financial-services-authority-dfsa", "2026-06-18T20:16"): "ADAPTER_FORMAT",
    ("AE-sca-aml-cft", "2026-06-19T14:29"): "ADAPTER_FORMAT",
    ("AE-sca-aml-cft", "2026-06-19T14:30"): "ADAPTER_FORMAT",
    ("AE-cbuae-retail-payment-services-rulebook", "2026-06-19T14:55"): "ADAPTER_FORMAT",
    ("AE-cbuae-exchange-business-regulation-doclist", "2026-06-19T14:57"): "ADAPTER_FORMAT",
    ("AE-cbuae-model-management-standards-doclist", "2026-06-19T14:57"): "ADAPTER_FORMAT",
    ("AE-cbuae-tbml-transshipment-guidance-doclist", "2026-06-19T14:58"): "ADAPTER_FORMAT",
    ("AE-eocn-laws-regulations-en", "2026-06-19T15:00"): "ADAPTER_FORMAT",
    ("AE-uaefiu-typology-reports", "2026-06-19T15:02"): "ADAPTER_FORMAT",
    ("AE-uaefiu-publications-hub", "2026-06-19T15:02"): "ADAPTER_FORMAT",
    ("AE-sca-circulars-rules-procedures", "2026-06-19T15:05"): "ADAPTER_FORMAT",
    ("AE-vara-compliance-risk-rulebook-pdf", "2026-06-19T15:07"): "PDF_REFLOW",
    ("AE-vara-technology-information-rulebook-pdf", "2026-06-19T15:07"): "PDF_REFLOW",
    ("AE-vara-va-issuance-rulebook-pdf", "2026-06-19T15:08"): "PDF_REFLOW",
    ("AE-vara-broker-dealer-rulebook-pdf", "2026-06-19T15:08"): "PDF_REFLOW",
    ("AE-vara-lending-borrowing-rulebook-pdf", "2026-06-19T15:08"): "PDF_REFLOW",
    ("AE-vara-va-regulations-2023-pdf", "2026-06-19T15:08"): "PDF_REFLOW",
    ("AE-adgm-fsra-guidance-policy", "2026-06-19T15:09"): "WRONG_PAGE",
    ("AE-adgm-ra-circulars", "2026-06-19T15:09"): "WRONG_PAGE",
    ("AE-adgm-listing-rules", "2026-06-19T15:09"): "ADAPTER_FORMAT",
    ("AE-dfsa-financial-crime-mlro-letters", "2026-06-19T15:11"): "ADAPTER_FORMAT",
    ("AE-dfsa-aml-rulebook-module", "2026-06-19T15:11"): "CHROME_SHUFFLE",
    ("AE-dfsa-consultation-current", "2026-06-19T15:11"): "ADAPTER_FORMAT",
    ("AE-dfsa-consultation-paper-165", "2026-06-19T15:12"): "ADAPTER_FORMAT",
    ("AE-difc-data-protection-regulation-10", "2026-06-19T15:17"): "ADAPTER_FORMAT",
    ("AE-dfsa-guidance-notes", "2026-06-19T16:39"): "ADAPTER_FORMAT",
    ("AE-dfsa-what-we-do-enforcement-1a837c50", "2026-06-19T16:40"): "ADAPTER_FORMAT",
    ("AE-difc-legal-database", "2026-06-21T21:40"): "ADAPTER_FORMAT",
    ("AE-sca-regulations-listing", "2026-06-21T21:41"): "ADAPTER_FORMAT",
    ("AE-adgm-fsra-guidance-policy", "2026-06-21T21:44"): "WRONG_PAGE",
    ("AE-difc-legal-database", "2026-06-21T21:45"): "ADAPTER_FORMAT",
    ("AE-dfsa-financial-crime-mlro-letters", "2026-07-05T12:54"): "TITLE_FLIP",
    ("AE-dfsa-financial-crime-mlro-letters", "2026-07-05T13:28"): "TITLE_FLIP",
}

GENUINE = {"COUNT_CHANGE": "possible-genuine", "REBRAND": "weak-genuine"}


def main() -> None:
    rows = [
        json.loads(line)
        for line in open("docs/signal/replay_severity.jsonl", encoding="utf-8")
    ]
    from collections import Counter

    counts: Counter[str] = Counter()
    lines = [
        "| # | source | ts | recorded | replayed | rule | judgment class | genuine? |",
        "|---|--------|----|----------|----------|------|----------------|----------|",
    ]
    n = 0
    for r in rows:
        if r.get("replay") != "OK":
            continue
        n += 1
        key = (r["source_id"], r["ts"][:16])
        cls = CLASS.get(key, "UNCLASSIFIED")
        counts[cls] += 1
        lines.append(
            f"| {n} | {r['source_id']} | {r['ts']} | {r['recorded_risk']} | "
            f"{r['replayed_risk']} | {r.get('rule')} | {cls} | {GENUINE.get(cls, 'no')} |"
        )
    print("\n".join(lines))
    print()
    print("Class totals:", dict(counts.most_common()))
    assert counts.get("UNCLASSIFIED", 0) == 0, "unclassified rows remain"


if __name__ == "__main__":
    main()
