"""F6 — one-shot activation probe for top-10 candidates.

For each candidate: ONE real fetch → extraction → v2 normalization →
hashing, with honest labelling. Nothing is written to any trail; sources
stay exactly as configured (enabling is Phase 2, operator-gated).

Run with STATUTEPROOF_BASE_DIR pointing at an isolated dir.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.scraper import fetch_page  # noqa: E402
from app.extractors import extract_best_text  # noqa: E402
from app.text_normalization import (  # noqa: E402
    looks_like_error_page,
    normalize_for_change_hash,
    stable_content_hash,
)
from app.arabic_text import arabic_share  # noqa: E402

CANDIDATES = [
    ("AE-adgm-fsra-waivers", "https://www.adgm.com/financial-services-regulatory-authority/waivers-and-modifications"),
    ("AE-adgm-ra-circulars", "https://www.adgm.com/registration-authority/circulars"),
    ("AE-fta-tax-legislation-listing", "https://tax.gov.ae/en/legislation.aspx"),
    ("AE-fta-vat-guides-references", "https://tax.gov.ae/en/taxes/vat/guides.references.aspx"),
    ("AE-fta-corporate-tax-guides-references", "https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx"),
    ("AE-fta-media-centre", "https://tax.gov.ae/en/media.centre.aspx"),
    ("AE-fta-corporate-tax-legislation", "https://tax.gov.ae/en/legislation/corporate-tax.aspx"),
    ("AE-uae-financial-intelligence-unit-uaefiu", "https://www.uaefiu.gov.ae/"),
    ("AE-uaefiu-circulars", "https://www.uaefiu.gov.ae/en/Publications/"),
    ("AE-uaefiu-typology-reports", "https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/"),
]


def probe(source_id: str, url: str) -> dict:
    row: dict = {"source_id": source_id, "url": url}
    t0 = time.time()
    try:
        html = fetch_page(url)
    except Exception as exc:
        row.update(
            {
                "fetch": "FAILED",
                "error": f"{type(exc).__name__}: {exc}"[:200],
                "label": "BLOCKED — fetch failed from this network",
                "seconds": round(time.time() - t0, 1),
            }
        )
        return row
    extr = extract_best_text(html, url)
    text = extr["text"] or ""
    normalized = normalize_for_change_hash(text)
    row.update(
        {
            "fetch": "OK",
            "seconds": round(time.time() - t0, 1),
            "raw_html_chars": len(html or ""),
            "extracted_chars": len(text),
            "extraction_method": extr.get("method"),
            "extraction_quality": extr.get("quality"),
            "normalized_chars": len(normalized),
            "normalized_hash": stable_content_hash(normalized),
            "error_page": looks_like_error_page(text),
            "arabic_share": round(arabic_share(normalized), 2),
            "normalized_head": normalized[:220].replace("\n", " ¶ "),
        }
    )
    if row["error_page"]:
        row["label"] = "BLOCKED — error/challenge page served"
    elif len(normalized) < 300:
        row["label"] = "NAV-SHELL / THIN — not fresh-alert eligible without adapter"
    elif len(normalized) >= 1000:
        row["label"] = "fresh-alert candidate — extraction+normalization+hash proven"
    else:
        row["label"] = "evidence-library-only — thin but stable content captured"
    return row


def main() -> None:
    rows = [probe(sid, url) for sid, url in CANDIDATES]
    out = Path("docs/signal/activation_probe_results.jsonl")
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    for r in rows:
        print(
            f"{r['source_id'][:44]:44} fetch={r['fetch']:6} "
            f"chars={r.get('normalized_chars', 0):>7} q={str(r.get('extraction_quality'))[:11]:11} "
            f"err_pg={str(r.get('error_page'))[:5]:5} | {r['label']}"
        )


if __name__ == "__main__":
    main()
