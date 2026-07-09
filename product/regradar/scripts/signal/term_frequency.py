"""Phase 0-B: term-frequency reality over the real trail.

Two corpora, EN and AR separated by script:
  1. DELTAS  — added+removed text of every replayable CHANGED run
              (docs/signal/replay_severity.jsonl, produced by replay_severity.py)
  2. DOCS    — the latest normalized snapshot of every source that has one

Outputs real counts: top tokens per corpus/language, plus hit counts for
regulatory fact patterns (dates, deadlines, amounts, law references,
licence categories) so detection-term candidates are grounded in data,
not invented.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

REAL = Path(
    os.environ.get(
        "REGRADAR_REAL_DIR",
        "/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar",
    )
)

ARABIC_RE = re.compile(r"[؀-ۿ]")
EN_TOKEN = re.compile(r"[a-z]{3,}")
AR_TOKEN = re.compile(r"[؀-ۿ]{2,}")

EN_STOP = set(
    """the and for with that this from are was were has have had not you your our
    their its will shall may can all any each other more most such than then when
    where which while who whom whose why how what been being into onto upon out
    off over under above below between among through during before after about
    against also only just even now new use used using per via etc www http https
    com gov page home back site menu search read click here link view download
    open close login item items title url row hash category context date listing
    source document english available additional information please contact
    center centre""".split()
)

# Regulatory fact patterns — counted, not assumed.
EN_PATTERNS = {
    "law_ref (Decree-Law/Cabinet Decision/Federal Law No.)": re.compile(
        r"(federal\s+)?(decree[-\s]?law|cabinet\s+(decision|resolution)|federal\s+law|administrative\s+decision|circular)\s+no\.?\s*\(?\d+", re.I
    ),
    "article_ref (Article (n))": re.compile(r"\barticle\s*\(?\d+", re.I),
    "effective_date": re.compile(r"\beffective\s+(from|date|on|as\s+of)\b", re.I),
    "deadline_phrases": re.compile(
        r"\b(no\s+later\s+than|deadline|within\s+\d+\s+(days|months)|by\s+\d{1,2}[\/\s])", re.I
    ),
    "amount_AED": re.compile(r"\b(aed|dirham|dhs?\.?)\s*[\d,]+|\b[\d,]+\s*(aed|dirhams?)\b", re.I),
    "percentage": re.compile(r"\b\d+(\.\d+)?\s*(%|percent)", re.I),
    "penalty_fine": re.compile(r"\b(penalt(y|ies)|fine[sd]?\b|sanction)", re.I),
    "licence_category": re.compile(r"\b(licen[cs]e[d]?|licen[cs]ing)\b.{0,40}\b(categor|class|type)", re.I),
    "must_shall": re.compile(r"\b(must|shall|required\s+to|obliged\s+to)\b", re.I),
    "date_dmy": re.compile(r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b"),
    "date_month": re.compile(
        r"\b\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}", re.I
    ),
    "in_force_status": re.compile(r"\b(in[-\s]force|status:\s*in[-\s]?force|repealed|superseded)\b", re.I),
    "consultation": re.compile(r"\bconsultation\s+(paper|period|closes?)\b", re.I),
}

AR_PATTERNS = {
    "قانون اتحادي (federal law)": re.compile(r"قانون\s+اتحادي"),
    "مرسوم بقانون (decree-law)": re.compile(r"مرسوم\s+بقانون"),
    "قرار (decision/resolution)": re.compile(r"\bقرار\b"),
    "تعميم (circular)": re.compile(r"تعميم"),
    "لائحة (regulation)": re.compile(r"لائحة"),
    "مادة (article)": re.compile(r"مادة\s*\(?\d+|المادة"),
    "غرامة (fine)": re.compile(r"غرامة|غرامات"),
    "عقوبة/جزاء (penalty)": re.compile(r"عقوبة|عقوبات|جزاء|جزاءات"),
    "ترخيص (licence)": re.compile(r"ترخيص|رخصة|مرخص"),
    "التزام/يجب (obligation/must)": re.compile(r"التزام|يجب|يتعين|ملزم"),
    "موعد نهائي/مهلة (deadline)": re.compile(r"موعد\s+نهائي|مهلة|أقصاه"),
    "نافذ/ساري (in force)": re.compile(r"نافذ|ساري\s+المفعول|يعمل\s+به"),
    "درهم (dirham amount)": re.compile(r"درهم"),
    "غسل الأموال (AML)": re.compile(r"غسل\s+الأموال"),
    "تمويل الإرهاب (CFT)": re.compile(r"تمويل\s+الإرهاب"),
    "الأصول الافتراضية (virtual assets)": re.compile(r"الأصول\s+الافتراضية"),
}


def split_langs(text: str) -> tuple[str, str]:
    en_lines, ar_lines = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        ar_chars = len(ARABIC_RE.findall(line))
        if ar_chars > 0.2 * len(line):
            ar_lines.append(line)
        else:
            en_lines.append(line)
    return "\n".join(en_lines), "\n".join(ar_lines)


def corpus_deltas() -> str:
    """Full (untruncated) added+removed text of every replayable CHANGED run."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from app.diff import get_diff

    runs = []
    with open(REAL / "data/source_runs/source_runs.jsonl", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                runs.append(json.loads(line))
    by_source: dict[str, list[dict]] = {}
    for r in runs:
        by_source.setdefault(r["source_id"], []).append(r)
    for lst in by_source.values():
        lst.sort(key=lambda r: r["timestamp_utc"])

    parts = []
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
        d = get_diff(
            old_f.read_text(encoding="utf-8"), new_f.read_text(encoding="utf-8")
        )
        parts.extend(d["added"])
        parts.extend(d["removed"])
    return "\n".join(parts)


def corpus_docs() -> tuple[str, int]:
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
    texts = []
    n = 0
    for _sid, p in sorted(latest.items()):
        f = REAL / p
        if f.is_file():
            texts.append(f.read_text(encoding="utf-8"))
            n += 1
    return "\n".join(texts), n


def report(name: str, text: str) -> None:
    en, ar = split_langs(text)
    print(f"\n===== {name}: {len(text):,} chars (EN {len(en):,} / AR {len(ar):,}) =====")
    en_tokens = [t for t in EN_TOKEN.findall(en.lower()) if t not in EN_STOP]
    ar_tokens = AR_TOKEN.findall(ar)
    print(f"-- top 35 EN tokens ({len(en_tokens):,} total) --")
    print(", ".join(f"{w}:{c}" for w, c in Counter(en_tokens).most_common(35)))
    print(f"-- top 35 AR tokens ({len(ar_tokens):,} total) --")
    print(", ".join(f"{w}:{c}" for w, c in Counter(ar_tokens).most_common(35)))
    print("-- EN fact patterns --")
    for label, pat in EN_PATTERNS.items():
        print(f"  {label}: {len(pat.findall(text))}")
    print("-- AR fact patterns --")
    for label, pat in AR_PATTERNS.items():
        print(f"  {label}: {len(pat.findall(text))}")


def main() -> None:
    deltas = corpus_deltas()
    docs, n_docs = corpus_docs()
    report("DELTA CORPUS (63 replayed CHANGED runs, added+removed)", deltas)
    report(f"DOCUMENT CORPUS (latest normalized snapshot x {n_docs} sources)", docs)


if __name__ == "__main__":
    main()
