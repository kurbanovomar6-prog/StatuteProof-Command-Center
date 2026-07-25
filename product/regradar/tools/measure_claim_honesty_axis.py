"""Reproducible measurement for the CLAIM HONESTY axis.

    python3 tools/measure_claim_honesty_axis.py
    python3 tools/measure_claim_honesty_axis.py --json

Every published number is recomputed HERE from sources.json and compared with
what the site actually says. The axis exists because planCapabilities.js once
claimed 246 enabled / 180 fresh-alert against a real 140 / 40, and LegalPage.jsx
named Stripe (no live payment path) and Railway (the box is DigitalOcean
Frankfurt). Those are not typos; they are the difference between a monitoring
product and a false claim to a regulated buyer.

Three independent checks, because they fail in different ways:

1. **Numbers** — recomputed from the registry, never read from a constant that
   claims to have been recomputed.
2. **Infrastructure claims** — the legal pages must name the processor and host
   that actually serve the product.
3. **Forbidden claims** — CLAUDE.md lists phrases that must never appear in
   customer-facing text ("guarantee compliance", "never miss an update", …).
   This scans the shipped frontend for them, because a single one of these in a
   footer is a bigger problem than any score on this axis.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
REPO = ROOT.parent.parent

# From CLAUDE.md "Forbidden Claims (Never Write These)". Matched
# case-insensitively as substrings of visible copy.
FORBIDDEN = (
    "ai lawyer",
    "guarantee compliance",
    "prevent fines",
    "replace lawyers",
    "automatic legal advice",
    "official partner of",
    "certified by",
    "100% accurate",
    "never miss an update",
    "stay compliant automatically",
    "we handle compliance for you",
    "automated compliance decisions",
    "avoid all penalties",
)

# What actually runs the product. A legal page naming anything else is a false
# statement to a buyer who is relying on it for their own vendor due diligence.
REAL_HOST_HINTS = ("digitalocean", "frankfurt")
STALE_INFRA_CLAIMS = ("railway",)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _recompute_from_registry() -> dict:
    raw = json.loads(_read(ROOT / "sources.json") or "{}")
    rows = raw if isinstance(raw, list) else raw.get("sources", [])
    enabled = [r for r in rows if r.get("enabled") is True]
    fresh = [
        r for r in enabled
        if r.get("monitoring_mode") == "fresh_alert" and r.get("alert_eligible") is True
    ]
    candidate = [r for r in enabled if r.get("monitoring_mode") == "candidate"]
    return {
        "total_rows": len(rows),
        "enabled": len(enabled),
        "fresh_alert": len(fresh),
        "candidate": len(candidate),
    }


def _published_numbers() -> dict:
    """The numbers the site actually ships, parsed out of the source of truth file."""
    text = _read(WEB / "data" / "sourceCounts.js")
    out: dict = {}
    for field in ("enabled", "readinessSupported", "candidate"):
        match = re.search(rf"\b{field}\s*:\s*(\d+)", text)
        if match:
            out[field] = int(match.group(1))
    return out


def _infra_claims() -> dict:
    legal = ""
    for name in ("LegalPage.jsx", "PrivacyPage.jsx", "TermsPage.jsx"):
        for path in WEB.rglob(name):
            legal += _read(path)
    low = legal.lower()
    return {
        "legal_text_found": bool(legal),
        "names_the_real_host": any(h in low for h in REAL_HOST_HINTS),
        "names_a_stale_host": [c for c in STALE_INFRA_CLAIMS if c in low],
        "mentions_stripe": "stripe" in low,
        "mentions_pdpl": "pdpl" in low,
        "mentions_gdpr": "gdpr" in low,
    }


# A forbidden phrase is only a violation when it is ASSERTED. The mandatory
# disclaimer in CLAUDE.md is built out of these very phrases under negation —
# "StatuteProof does not determine compliance outcomes, prevent fines, or ..." —
# so a scanner that matches the bare substring flags the required legal text as
# a legal violation. The first version of this file did exactly that and
# reported six shipped violations, all of them the disclaimer.
_NEGATORS = (
    "does not", "do not", "doesn't", "don't", "cannot", "can not", "can't",
    "never ", "no ", "not ", "without ", "nor ",
)
_NEGATION_WINDOW = 120


def _is_negated(text_low: str, idx: int) -> bool:
    window = text_low[max(0, idx - _NEGATION_WINDOW): idx]
    return any(neg in window for neg in _NEGATORS)


def _forbidden_hits() -> list[dict]:
    """Forbidden phrases ASSERTED in shipped customer-facing text.

    Skips test files: a guard test necessarily enumerates the banned list, and
    flagging the guard would bury a real hit in noise.
    """
    hits: list[dict] = []
    for path in list(WEB.rglob("*.jsx")) + list(WEB.rglob("*.js")):
        name = str(path)
        if "node_modules" in name or "/test/" in name or ".test." in name:
            continue
        text = _read(path)
        low = text.lower()
        for phrase in FORBIDDEN:
            start = 0
            while True:
                idx = low.find(phrase, start)
                if idx == -1:
                    break
                start = idx + len(phrase)
                if _is_negated(low, idx):
                    continue
                hits.append({
                    "file": str(path.relative_to(REPO)),
                    "line": text[:idx].count("\n") + 1,
                    "phrase": phrase,
                    "excerpt": text[max(0, idx - 60): idx + 80].replace("\n", " "),
                })
    return hits


def measure() -> dict:
    real = _recompute_from_registry()
    published = _published_numbers()
    drift = {}
    pairs = (("enabled", "enabled"), ("readinessSupported", "fresh_alert"),
             ("candidate", "candidate"))
    for pub_key, real_key in pairs:
        if pub_key in published:
            drift[pub_key] = {
                "published": published[pub_key],
                "recomputed": real[real_key],
                "matches": published[pub_key] == real[real_key],
            }

    forbidden = _forbidden_hits()
    infra = _infra_claims()
    return {
        "recomputed_from_registry": real,
        "published": published,
        "drift": drift,
        "all_numbers_match": bool(drift) and all(d["matches"] for d in drift.values()),
        "infrastructure_claims": infra,
        "forbidden_claim_hits": forbidden,
        "forbidden_claims_clean": not forbidden,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = measure()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print("published numbers vs the registry")
    for key, d in report["drift"].items():
        mark = "+" if d["matches"] else "-"
        print(f"  {mark} {key:22} published {d['published']:>5}  recomputed {d['recomputed']:>5}")
    if not report["drift"]:
        print("  (no published numbers found to compare)")

    infra = report["infrastructure_claims"]
    print("\ninfrastructure claims in the legal pages")
    print(f"  names the real host                {infra['names_the_real_host']}")
    print(f"  names a stale host                 {infra['names_a_stale_host'] or 'none'}")
    print(f"  mentions Stripe                    {infra['mentions_stripe']}")
    print(f"  mentions PDPL / GDPR               {infra['mentions_pdpl']} / {infra['mentions_gdpr']}")

    print("\nforbidden claims in shipped frontend copy")
    if report["forbidden_claims_clean"]:
        print("  + none")
    else:
        for hit in report["forbidden_claim_hits"]:
            print(f"  - {hit['file']}:{hit['line']}  \"{hit['phrase']}\"")

    print(f"\n>> ALL PUBLISHED NUMBERS MATCH THE REGISTRY: {report['all_numbers_match']}")
    print(f">> NO FORBIDDEN CLAIMS SHIPPED:              {report['forbidden_claims_clean']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
