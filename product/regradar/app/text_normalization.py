"""
Stable text normalization for source change detection.

The goal is not to create a perfect legal parser.  It is to remove common
website noise while preserving the regulatory text that a human would verify:
headings, publication titles, dates, circular wording, tables already rendered
as text, and document links.
"""

from __future__ import annotations

import hashlib
import html
import re


_SPACE_RE = re.compile(r"[ \t\r\f\v]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")

_BOILERPLATE_EXACT = {
    "accept",
    "accept all",
    "accept cookies",
    "all rights reserved",
    "back to top",
    "close",
    "cookie settings",
    "copyright",
    "english",
    "home",
    "menu",
    "privacy policy",
    "read more",
    "search",
    "skip to content",
    "submit",
    "terms and conditions",
    "عربي",
}

_BOILERPLATE_PHRASES = (
    "enable javascript",
    "follow us on",
    "powered by curator.io",
    "share this page",
    "subscribe to our newsletter",
    "this site uses cookies",
    "we use cookies",
    "your browser does not support",
)

_VOLATILE_LINE_RE = re.compile(
    r"""
    ^\s*(
        generated\s+(at|on)|
        page\s+generated|
        print(ed)?\s+(at|on)|
        retrieved\s+(at|on)|
        session\s+id|
        current\s+(date|time)|
        local\s+time|
        server\s+time|
        last\s+run
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_VOLATILE_FRAGMENT_RE = re.compile(
    r"""
    (
        عدد\s+الزوار\s*:\s*[\d\s,]+|
        آخر\s+تحديث\s+للمحتوى\s+بتاريخ\s*:\s*
            \d{1,2}\s+[^\n]{1,30}?\s+\d{4}\s+
            \d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?|
        last\s+content\s+update\s*:\s*
            \d{1,2}\s+[A-Za-z]+\s+\d{4}\s+
            \d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

_TIME_ONLY_RE = re.compile(r"^\s*\d{1,2}:\d{2}(:\d{2})?\s*(am|pm)?\s*$", re.IGNORECASE)
_DATE_WORD_RE = re.compile(
    r"\b(published|publication|issued|effective|dated|date|circular|law|decree|resolution)\b",
    re.IGNORECASE,
)

_ARABIC_RE = re.compile(r"[؀-ۿ]")


def _is_arabic_line(line: str) -> bool:
    """Return True if more than 20% of the line's characters are Arabic-script."""
    if not line:
        return False
    arabic_chars = len(_ARABIC_RE.findall(line))
    return arabic_chars > 0.2 * len(line)


def _clean_line(line: str) -> str:
    line = line.replace("\u00a0", " ")
    line = _VOLATILE_FRAGMENT_RE.sub("", line)
    line = _SPACE_RE.sub(" ", line).strip()
    return line


def _is_volatile_line(line: str) -> bool:
    """Remove timestamps that describe the page/render run, not publication dates."""
    if not line:
        return True
    if _DATE_WORD_RE.search(line):
        return False
    if _VOLATILE_LINE_RE.search(line):
        return True
    if _TIME_ONLY_RE.match(line):
        return True
    return False


def _is_boilerplate_line(line: str) -> bool:
    lower = line.lower().strip(" .:-|")
    if line.startswith("حساب حكومة الإمارات"):
        return True
    if "الجريدة الرسمية المحلية حكومة أبوظبي حكومة دبي" in line:
        return True
    if lower in _BOILERPLATE_EXACT:
        return True
    if len(lower) <= 3 and not lower.isdigit():
        return True
    if len(lower) <= 24 and any(phrase in lower for phrase in _BOILERPLATE_PHRASES):
        return True
    return False


def normalize_for_change_hash(text: str) -> str:
    """
    Return a stable text representation for regulatory change hashing.

    Conservative cleanup only:
    - normalize whitespace
    - remove empty lines
    - remove obvious UI/cookie/navigation fragments
    - remove duplicate repeated lines
    - remove render-time timestamp lines when clearly not publication dates
    """
    if not text:
        return ""

    text = html.unescape(text)
    raw_lines = str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines: list[str] = []
    seen: dict[str, int] = {}

    for raw in raw_lines:
        line = _clean_line(raw)
        if not line:
            continue
        if _is_volatile_line(line):
            continue

        key = line.casefold()
        seen_count = seen.get(key, 0)
        if _is_boilerplate_line(line):
            seen[key] = seen_count + 1
            continue
        if seen_count > 0:
            seen[key] = seen_count + 1
            continue
        if len(line) > 40 and any(line in previous for previous in lines[-5:]):
            seen[key] = 1
            continue

        seen[key] = 1
        lines.append(line)

    normalized = "\n".join(_merge_wrapped_lines(lines))
    normalized = _MULTI_NEWLINE_RE.sub("\n\n", normalized)
    return normalized.strip()


def _merge_wrapped_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        if not merged or not merged[-1]:
            merged.append(line)
            continue
        prev = merged[-1]
        if _is_arabic_line(prev) or _is_arabic_line(line):
            # For Arabic lines, only merge if the previous line ends with a
            # comma (Arabic or ASCII) — never rely on the lowercase-initial
            # check because Arabic script has no case distinction.
            if prev.endswith("،") or prev.endswith(","):
                merged[-1] = f"{prev} {line}"
            else:
                merged.append(line)
        else:
            # English / Latin merge heuristic: previous line does not end in
            # sentence-closing punctuation and current line starts lowercase.
            if (
                not prev.endswith((".", ":", ";", "!", "?", ")", "]"))
                and line[:1].islower()
            ):
                merged[-1] = f"{prev} {line}"
            else:
                merged.append(line)
    return merged


def stable_content_hash(text: str) -> str | None:
    """
    Return SHA-256 of whitespace-normalised text for change detection.

    Uses minimal normalisation (collapse whitespace only) so the hash is
    stable across minor formatting changes while remaining sensitive to any
    actual text change.  Returns None for empty/blank input.

    This is the canonical hash used by both pipeline.py (comparison) and
    db.save_document() (storage) — they must always call the same function.
    """
    if not text:
        return None
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def stable_normalized_hash(text: str) -> str:
    """Return SHA-256 of normalized text, or an empty string for empty input."""
    normalized = normalize_for_change_hash(text)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
